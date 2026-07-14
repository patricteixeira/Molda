"""Construtor sem dependências para o contrato público Brand Package 0.1."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal, Self

SCHEMA_VERSION = "0.1.0"
MANIFEST_FILENAME = "brand-package.json"
_ADAPTER_ID = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)+$")
_SOURCE_KIND = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
_SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
_MAX_FILE_BYTES = 200 * 2**20
_WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "CONIN$",
    "CONOUT$",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
_Role = Literal["guideline", "logo", "font", "tokens", "reference"]


class AdapterBuildError(ValueError):
    """Entrada insegura ou incompatível com Brand Package 0.1."""


@dataclass(frozen=True)
class AdapterIdentity:
    """Identidade pública e versionada do adapter."""

    id: str
    name: str
    version: str

    def __post_init__(self) -> None:
        """Valida namespace, nome visível e SemVer sem dependências externas."""
        if not _ADAPTER_ID.fullmatch(self.id) or len(self.id) > 128:
            raise AdapterBuildError("O id do adapter precisa usar um namespace estável.")
        if not self.name.strip() or len(self.name) > 100:
            raise AdapterBuildError("O nome do adapter precisa ter entre 1 e 100 caracteres.")
        if not _SEMVER.fullmatch(self.version):
            raise AdapterBuildError("A versão do adapter precisa seguir SemVer.")


@dataclass(frozen=True)
class SourceIdentity:
    """Origem não sensível lida pelo adapter."""

    kind: str
    label: str | None = None

    def __post_init__(self) -> None:
        """Recusa kinds instáveis e labels vazios ou excessivos."""
        if not _SOURCE_KIND.fullmatch(self.kind):
            raise AdapterBuildError("O kind da origem não é válido.")
        if self.label is not None and (not self.label.strip() or len(self.label) > 160):
            raise AdapterBuildError("O label da origem precisa ter entre 1 e 160 caracteres.")


@dataclass(frozen=True)
class BuiltPackage:
    """Resultado publicado e sua identidade determinística."""

    package_dir: Path
    manifest_path: Path
    file_count: int
    total_bytes: int
    package_sha256: str


@dataclass(frozen=True)
class _PendingFile:
    source: Path
    path: str
    role: _Role
    media_type: str


def _portable_path(value: str) -> str:
    if (
        not value
        or len(value) > 240
        or value != unicodedata.normalize("NFC", value)
        or "\\" in value
    ):
        raise AdapterBuildError("O path de destino precisa ser POSIX e NFC.")
    candidate = PurePosixPath(value)
    parts = value.split("/")
    if candidate.is_absolute() or any(
        part in {"", ".", ".."}
        or ":" in part
        or part.endswith((".", " "))
        or part.split(".", maxsplit=1)[0].upper() in _WINDOWS_RESERVED
        for part in parts
    ):
        raise AdapterBuildError("O path de destino não é portável.")
    if candidate.suffix != candidate.suffix.casefold():
        raise AdapterBuildError("A extensão do destino precisa usar letras minúsculas.")
    if value == MANIFEST_FILENAME:
        raise AdapterBuildError("O manifesto é reservado ao SDK.")
    return value


def _validate_role(path: str, role: _Role, media_type: str) -> None:
    suffix = PurePosixPath(path).suffix
    if role == "logo" and not (
        path.startswith("assets/logos/")
        and {".svg": "image/svg+xml", ".png": "image/png"}.get(suffix) == media_type
    ):
        raise AdapterBuildError("Logos devem usar assets/logos/ e SVG ou PNG.")
    if role == "font" and not (
        path.startswith("fonts/")
        and {".ttf": "font/ttf", ".otf": "font/otf"}.get(suffix) == media_type
    ):
        raise AdapterBuildError("Fontes devem usar fonts/ e TTF ou OTF.")
    if role == "tokens" and not (
        "/" not in path
        and (path == "tokens.json" or path.endswith(".tokens.json"))
        and media_type == "application/json"
    ):
        raise AdapterBuildError("Tokens devem usar tokens.json ou *.tokens.json na raiz.")
    if role == "guideline" and not (
        "/" not in path and path.endswith(".pdf") and media_type == "application/pdf"
    ):
        raise AdapterBuildError("Diretrizes devem ser PDFs na raiz.")
    if role == "reference" and not (
        path.startswith("references/") and path.endswith(".pdf") and media_type == "application/pdf"
    ):
        raise AdapterBuildError("Referências devem ser PDFs em references/.")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _write_manifest(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


class BrandPackageBuilder:
    """Materializa um Brand Package completo e atômico."""

    def __init__(self, adapter: AdapterIdentity, source: SourceIdentity) -> None:
        """Inicia um pacote vazio ligado à identidade e à origem informadas."""
        self.adapter = adapter
        self.source = source
        self._files: list[_PendingFile] = []
        self._paths: set[str] = set()

    def add_file(
        self,
        source: Path,
        path: str,
        *,
        role: _Role,
        media_type: str,
    ) -> Self:
        """Declara uma cópia futura depois de validar fonte, destino e papel."""
        source = Path(source)
        try:
            if source.is_symlink() or not source.is_file():
                raise AdapterBuildError("O arquivo-fonte precisa ser regular e legível.")
            if source.stat().st_size > _MAX_FILE_BYTES:
                raise AdapterBuildError("O arquivo-fonte excede 200 MiB.")
        except AdapterBuildError:
            raise
        except OSError as exc:
            raise AdapterBuildError("O arquivo-fonte precisa ser regular e legível.") from exc
        path = _portable_path(path)
        _validate_role(path, role, media_type)
        key = path.casefold()
        if key in self._paths:
            raise AdapterBuildError("O pacote não pode declarar destinos colidentes.")
        if len(self._files) >= 200:
            raise AdapterBuildError("O pacote não pode exceder 200 arquivos.")
        self._paths.add(key)
        self._files.append(_PendingFile(source, path, role, media_type))
        return self

    def build(self, out_dir: Path) -> BuiltPackage:
        """Publica a árvore por staging e recusa substituir um destino existente."""
        if not self._files:
            raise AdapterBuildError("O Brand Package precisa declarar ao menos um arquivo.")
        out_dir = Path(out_dir)
        if out_dir.exists() or out_dir.is_symlink():
            raise AdapterBuildError("O diretório de saída já existe.")
        out_dir.parent.mkdir(parents=True, exist_ok=True)
        parent = out_dir.parent.resolve(strict=True)
        stage = Path(tempfile.mkdtemp(prefix=f".{out_dir.name}.stage-", dir=parent))
        published = False
        try:
            records: list[dict[str, object]] = []
            identity = hashlib.sha256()
            total_bytes = 0
            for item in sorted(self._files, key=lambda value: value.path.casefold()):
                if item.source.is_symlink() or not item.source.is_file():
                    raise AdapterBuildError(
                        "O arquivo-fonte deixou de ser um arquivo regular antes da cópia."
                    )
                target = stage.joinpath(*item.path.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(item.source, target, follow_symlinks=False)
                if target.is_symlink() or not target.is_file():
                    raise AdapterBuildError("A cópia não produziu um arquivo regular.")
                size = target.stat().st_size
                digest = _sha256(target)
                total_bytes += size
                if total_bytes > _MAX_FILE_BYTES:
                    raise AdapterBuildError("O pacote não pode exceder 200 MiB.")
                records.append(
                    {
                        "path": item.path,
                        "role": item.role,
                        "mediaType": item.media_type,
                        "size": size,
                        "sha256": digest,
                    }
                )
                identity.update(item.path.encode("utf-8"))
                identity.update(b"\0")
                identity.update(digest.encode("ascii"))
                identity.update(b"\0")
                identity.update(str(size).encode("ascii"))
                identity.update(b"\n")
            source_payload: dict[str, str] = {"kind": self.source.kind}
            if self.source.label is not None:
                source_payload["label"] = self.source.label
            manifest: dict[str, object] = {
                "schemaVersion": SCHEMA_VERSION,
                "adapter": {
                    "id": self.adapter.id,
                    "name": self.adapter.name,
                    "version": self.adapter.version,
                },
                "source": source_payload,
                "files": records,
            }
            _write_manifest(stage / MANIFEST_FILENAME, manifest)
            os.replace(stage, out_dir)
            published = True
            return BuiltPackage(
                package_dir=out_dir,
                manifest_path=out_dir / MANIFEST_FILENAME,
                file_count=len(records),
                total_bytes=total_bytes,
                package_sha256=identity.hexdigest(),
            )
        except AdapterBuildError:
            raise
        except OSError as exc:
            raise AdapterBuildError("Não foi possível publicar o Brand Package.") from exc
        finally:
            if not published:
                shutil.rmtree(stage, ignore_errors=True)
