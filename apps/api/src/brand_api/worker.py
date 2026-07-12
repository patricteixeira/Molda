"""Worker transacional da fila de exports persistida no Postgres."""

from __future__ import annotations

import os
import re
import shutil
import stat
import time
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath

from sqlalchemy import select

from brand_api.config import Settings
from brand_api.db import make_engine, make_session_factory
from brand_api.exporters import (
    Exporter,
    ExportOutcome,
    ExportRejected,
    FakeExporter,
    PlaywrightExporter,
)
from brand_api.models import BrandRevision, Document, Job
from brand_api.storage import Storage
from brand_runtime import BrandIR, ContentSpec, GuardCheck, LayoutSpec
from brand_runtime.kit.models import ImageValue

_JOB_ID_RE = re.compile(r"^job_[0-9a-f]{12}$")
_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def _is_link(path: Path) -> bool:
    """Detecta links simbólicos e junctions sem seguir seus destinos."""
    is_junction = getattr(os.path, "isjunction", None)
    return path.is_symlink() or bool(is_junction and is_junction(path))


def _validate_existing_ancestors(path: Path) -> None:
    """Recusa qualquer link na cadeia já existente de um diretório de trabalho."""
    for component in (path, *path.parents):
        if component.exists() and _is_link(component):
            raise ValueError("O diretório de trabalho não pode conter links.")


def _ensure_regular_directory(path: Path) -> None:
    """Cria uma árvore e confirma que cada componente é diretório real."""
    _validate_existing_ancestors(path)
    path.mkdir(parents=True, exist_ok=True)
    current = path
    while True:
        if _is_link(current) or not current.is_dir():
            raise ValueError("O diretório de trabalho precisa ser uma pasta regular.")
        if current == current.parent:
            break
        current = current.parent


def _safe_relative_path(raw_path: str) -> Path:
    """Converte um path POSIX relativo sem aceitar escapes ou ambiguidades Windows."""
    if not isinstance(raw_path, str) or not raw_path or "\x00" in raw_path:
        raise ValueError("O path do manifest é inválido.")
    if "\\" in raw_path or PureWindowsPath(raw_path).drive:
        raise ValueError("O path do manifest precisa ser relativo e usar '/'.")
    raw_parts = raw_path.split("/")
    if any(
        part in {"", ".", ".."}
        or part.endswith((".", " "))
        or any(ord(character) < 32 or character in '<>:"|?*' for character in part)
        or part.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES
        for part in raw_parts
    ):
        raise ValueError("O path do manifest contém um segmento não permitido.")
    candidate = PurePosixPath(raw_path)
    if candidate.is_absolute():
        raise ValueError("O path do manifest não pode escapar do diretório de trabalho.")
    return Path(*candidate.parts)


def _materialization_plan(
    manifest: dict[str, str],
    ir: BrandIR,
    content: ContentSpec,
) -> dict[Path, str]:
    """Une as raízes de asset e falha em colisões ambíguas."""
    planned: dict[Path, str] = {}
    casefolded: dict[str, Path] = {}

    def add(relative: Path, sha256: str) -> None:
        key = relative.as_posix().casefold()
        previous_path = casefolded.get(key)
        if previous_path is not None:
            if previous_path != relative or planned[previous_path] != sha256:
                raise ValueError("O workdir contém paths de asset em colisão.")
            return
        casefolded[key] = relative
        planned[relative] = sha256

    for raw_path, sha256 in manifest.items():
        add(_safe_relative_path(raw_path), sha256)

    for font in ir.fonts.values():
        if font.file_sha256 is not None:
            add(Path("fonts", font.file_sha256), font.file_sha256)

    for value in content.values.values():
        if isinstance(value, ImageValue):
            if value.sha256 is None:
                raise ValueError("Uma imagem do documento não possui SHA-256.")
            add(
                Path("sha256", value.sha256[:2], value.sha256[2:4], value.sha256),
                value.sha256,
            )
    return planned


def _write_blob_safely(dest: Path, relative: Path, data: bytes) -> None:
    """Publica um blob novo recusando parents ou destinos que sejam links."""
    target = dest / relative
    current = dest
    for part in relative.parent.parts:
        current /= part
        current.mkdir(exist_ok=True)
        if _is_link(current) or not current.is_dir():
            raise ValueError("O workdir contém um link não permitido.")
    if target.exists() or _is_link(target):
        raise ValueError("O workdir já contém um arquivo no destino do asset.")
    with target.open("xb") as handle:
        handle.write(data)


def build_export_workdir(
    manifest: dict[str, str],
    ir: BrandIR,
    content: ContentSpec,
    storage: Storage,
    dest: Path,
) -> Path:
    """Materializa pacote, fontes e imagens em uma raiz efêmera segura."""
    _validate_existing_ancestors(dest)
    if dest.exists():
        if _is_link(dest) or not dest.is_dir() or any(dest.iterdir()):
            raise ValueError("O diretório de trabalho precisa estar vazio e sem links.")
    else:
        _ensure_regular_directory(dest)

    identity = dest.resolve(strict=True)
    try:
        for relative, sha256 in _materialization_plan(manifest, ir, content).items():
            # Storage.get valida tanto o endereço quanto a integridade do conteúdo.
            _write_blob_safely(dest, relative, storage.get(sha256))
    except Exception:
        # Se a materialização falhar no meio, não deixa uma árvore parcial para trás.
        with suppress(OSError, ValueError):
            _validate_existing_ancestors(dest)
            if dest.exists() and not _is_link(dest) and dest.resolve(strict=True) == identity:
                shutil.rmtree(dest)
        raise
    return dest


def _serialize_checks(checks: list[GuardCheck]) -> list[dict]:
    """Valida e serializa checks do exporter sem perder campos medidos."""
    return [
        GuardCheck.model_validate(check).model_dump(mode="json", by_alias=True) for check in checks
    ]


def _claim_next_job(session_factory) -> str | None:
    """Reivindica atomicamente o próximo job e libera o lock antes do render."""
    with session_factory() as session:
        job = session.scalars(
            select(Job)
            .where(Job.status == "queued")
            .order_by(Job.created_at, Job.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        ).first()
        if job is None:
            return None
        job.status = "running"
        job.started_at = datetime.now(UTC)
        job.error = None
        job.result = None
        job_id = job.id
        session.commit()
        return job_id


def _load_export_contract(session_factory, job_id: str):
    """Carrega e valida o snapshot persistido necessário ao export."""
    with session_factory() as session:
        job = session.get(Job, job_id)
        if job is None or job.status != "running" or job.kind != "export":
            raise RuntimeError("O job reivindicado não está disponível para export.")
        document = session.get(Document, job.document_id)
        if document is None:
            raise RuntimeError("O documento do job não foi encontrado.")
        revision = session.get(BrandRevision, document.brand_revision_id)
        if revision is None:
            raise RuntimeError("A revisão de marca do documento não foi encontrada.")
        fmt = job.params.get("format") if isinstance(job.params, dict) else None
        if fmt not in {"png", "pdf"}:
            raise RuntimeError("O formato persistido no job é inválido.")
        ir = BrandIR.model_validate(revision.ir)
        content = ContentSpec.model_validate(document.content)
        raw_layout = next(
            (
                item
                for item in revision.kit
                if isinstance(item, dict) and item.get("id") == document.layout_id
            ),
            None,
        )
        if raw_layout is None:
            raise RuntimeError("O layout do documento não existe na revisão.")
        return (
            document.id,
            ir,
            LayoutSpec.model_validate(raw_layout),
            content,
            dict(revision.manifest),
            fmt,
        )


def _safe_job_workdir(work_root: Path, job_id: str) -> Path:
    """Deriva uma pasta de job estritamente contida na raiz configurada."""
    if not _JOB_ID_RE.fullmatch(job_id):
        raise ValueError("O identificador do job não é seguro para o workdir.")
    _ensure_regular_directory(work_root)
    destination = work_root / job_id
    if destination.exists() or _is_link(destination):
        raise ValueError("O diretório de trabalho do job já existe.")
    if destination.parent.resolve(strict=True) != work_root.resolve(strict=True):
        raise ValueError("O workdir do job escapou da raiz configurada.")
    return destination


def _read_exact_output(out_path: Path, workdir: Path, workdir_identity: Path) -> bytes:
    """Lê somente ``out.<fmt>`` regular e contido, ignorando o path do adapter."""
    _validate_existing_ancestors(out_path)
    if _is_link(out_path) or _is_link(workdir) or not workdir.is_dir():
        raise RuntimeError("O exporter produziu um link em vez de um arquivo regular.")
    try:
        mode = out_path.stat(follow_symlinks=False).st_mode
        resolved = out_path.resolve(strict=True)
        root = workdir.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("O exporter não produziu o arquivo esperado.") from exc
    if root != workdir_identity or not stat.S_ISREG(mode) or not resolved.is_relative_to(root):
        raise RuntimeError("O arquivo exportado não está contido no workdir.")
    return out_path.read_bytes()


def _finish_success(
    session_factory,
    job_id: str,
    document_id: str,
    checks: list[dict],
    sha256: str,
) -> None:
    """Persiste o resultado publicado e o verdict completo em uma transação."""
    with session_factory() as session:
        job = session.get(Job, job_id)
        document = session.get(Document, document_id)
        if job is None or job.status != "running" or document is None:
            raise RuntimeError("O job mudou de estado antes de concluir o export.")
        job.checks = checks
        document.checks = checks
        job.status = "succeeded"
        job.result = {"sha256": sha256, "url": f"/v1/assets/{sha256}"}
        job.error = None
        job.finished_at = datetime.now(UTC)
        session.commit()


def _finish_failure(
    session_factory,
    job_id: str,
    *,
    error: str,
    checks: list[dict] | None = None,
    document_id: str | None = None,
) -> None:
    """Fecha o job como falha, sem jamais associar um blob de resultado."""
    with session_factory() as session:
        job = session.get(Job, job_id)
        if job is None:
            return
        job.status = "failed"
        job.result = None
        job.error = error
        job.finished_at = datetime.now(UTC)
        if checks is not None:
            job.checks = checks
            if document_id is not None:
                document = session.get(Document, document_id)
                if document is not None:
                    document.checks = checks
        session.commit()


def run_next_job(
    session_factory,
    *,
    storage: Storage,
    exporter: Exporter,
    settings: Settings,
) -> bool:
    """Processa no máximo um job, persistindo sucesso ou falha e limpando o workdir."""
    job_id = _claim_next_job(session_factory)
    if job_id is None:
        return False

    workdir: Path | None = None
    workdir_identity: Path | None = None
    document_id: str | None = None
    try:
        document_id, ir, layout, content, manifest, fmt = _load_export_contract(
            session_factory, job_id
        )
        workdir = _safe_job_workdir(settings.work_dir, job_id)
        build_export_workdir(manifest, ir, content, storage, workdir)
        workdir_identity = workdir.resolve(strict=True)
        out_path = workdir / f"out.{fmt}"
        outcome: ExportOutcome = exporter.export(
            ir=ir,
            layout=layout,
            content=content,
            assets_dir=workdir,
            fmt=fmt,
            out_path=out_path,
        )
        checks = _serialize_checks(outcome.checks)
        if any(check["status"] == "blocked" for check in checks):
            raise ExportRejected([GuardCheck.model_validate(check) for check in checks])
        # Deliberadamente ignora outcome.path: só o destino pré-acordado pode ser publicado.
        sha256 = storage.put(_read_exact_output(out_path, workdir, workdir_identity))
        _finish_success(session_factory, job_id, document_id, checks, sha256)
    except ExportRejected as exc:
        checks = _serialize_checks(exc.checks)
        _finish_failure(
            session_factory,
            job_id,
            error="O render encontrou pendências — corrija antes de exportar.",
            checks=checks,
            document_id=document_id,
        )
    except Exception as exc:
        _finish_failure(
            session_factory,
            job_id,
            error=f"Falha no export: {exc}",
        )
    finally:
        if workdir is not None and workdir_identity is not None:
            with suppress(OSError, ValueError):
                _validate_existing_ancestors(workdir)
                if (
                    workdir.exists()
                    and not _is_link(workdir)
                    and workdir.resolve(strict=True) == workdir_identity
                ):
                    shutil.rmtree(workdir)
    return True


def run_worker(
    settings: Settings,
    *,
    poll_seconds: float = 1.0,
    once: bool = False,
) -> None:
    """Inicializa dependências do processo worker e executa seu loop de polling."""
    if poll_seconds < 0:
        raise ValueError("O intervalo de polling não pode ser negativo.")
    exporter: Exporter
    if settings.fake_exporter:
        exporter = FakeExporter()
    else:
        if settings.render_dist is None:
            raise RuntimeError("Defina BRANDRT_RENDER_DIST para iniciar o worker de export real.")
        exporter = PlaywrightExporter(settings.render_dist)

    storage = Storage(settings.storage_dir)
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)
    try:
        if once:
            run_next_job(
                session_factory,
                storage=storage,
                exporter=exporter,
                settings=settings,
            )
            return
        while True:
            processed = run_next_job(
                session_factory,
                storage=storage,
                exporter=exporter,
                settings=settings,
            )
            if not processed:
                time.sleep(poll_seconds)
    finally:
        engine.dispose()
