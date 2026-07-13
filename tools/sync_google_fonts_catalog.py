"""Gera o catálogo versionado do Google Fonts usado pelo intake.

O script lê um checkout local de ``google/fonts`` já fixado em um commit.
Ele não consulta APIs em runtime e não inclui os binários das fontes no
repositório do brand-runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path

from gfmetadata import FamilyProto, text_format

_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_GIT_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9_.+,[\]() -]+\.ttf$")
_LICENSES = {
    "OFL": ("OFL-1.1", ("OFL.txt",)),
    "APACHE2": ("Apache-2.0", ("LICENSE.txt",)),
    "UFL": ("Ubuntu-font-1.0", ("UFL.txt", "LICENCE.txt")),
}


def _family_key(value: str) -> str:
    """Normaliza família para lookup exato sem depender de pontuação."""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


class _GitBlobReader:
    """Lê muitos blobs por um único processo ``git cat-file --batch``."""

    def __init__(self, checkout: Path, revision: str) -> None:
        self.checkout = checkout
        self.revision = revision
        self.process: subprocess.Popen[bytes] | None = None

    def __enter__(self) -> _GitBlobReader:
        self.process = subprocess.Popen(
            ["git", "-C", str(self.checkout), "cat-file", "--batch"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        return self

    def read(self, path: Path) -> bytes:
        """Lê bytes canônicos sem conversão de fim de linha do checkout."""
        if (
            self.process is None
            or self.process.stdin is None
            or self.process.stdout is None
        ):
            raise RuntimeError("O leitor de blobs não foi iniciado.")
        relative = path.relative_to(self.checkout).as_posix()
        self.process.stdin.write(f"{self.revision}:{relative}\n".encode("utf-8"))
        self.process.stdin.flush()
        header = self.process.stdout.readline().decode("ascii").strip().split()
        if len(header) != 3 or header[1] != "blob":
            raise ValueError(f"Blob Git ausente ou inválido: {relative}.")
        size = int(header[2])
        data = self.process.stdout.read(size)
        if len(data) != size or self.process.stdout.read(1) != b"\n":
            raise ValueError(f"Blob Git truncado: {relative}.")
        return data

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.process is None:
            return
        if self.process.stdin is not None:
            self.process.stdin.close()
        if exc_type is None:
            if self.process.wait(timeout=10) != 0:
                raise RuntimeError("git cat-file encerrou com erro.")
        else:
            self.process.terminate()
            self.process.wait(timeout=10)


def _checkout_revision(checkout: Path) -> str:
    """Lê o commit do checkout sem aceitar uma árvore sem identidade Git."""
    result = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip().casefold()


def _git_blob_oids(checkout: Path, revision: str) -> dict[str, str]:
    """Indexa OIDs da árvore sem baixar os blobs prometidos do partial clone."""
    result = subprocess.run(
        [
            "git",
            "-C",
            str(checkout),
            "ls-tree",
            "-r",
            "-z",
            "--full-tree",
            revision,
            "--",
            "ofl",
            "apache",
            "ufl",
        ],
        check=True,
        capture_output=True,
    )
    indexed: dict[str, str] = {}
    for entry in result.stdout.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        _mode, object_type, raw_oid = metadata.split()
        if object_type != b"blob":
            continue
        path = raw_path.decode("utf-8")
        oid = raw_oid.decode("ascii")
        if not _GIT_OID_RE.fullmatch(oid):
            raise ValueError(f"OID Git inválido em {path!r}.")
        indexed[path] = oid
    return indexed


def _license(metadata, directory: Path, blobs: _GitBlobReader) -> dict[str, str] | None:
    """Resolve a licença declarada; família sem texto não entra no catálogo."""
    try:
        license_id, filenames = _LICENSES[metadata.license]
    except KeyError as exc:
        raise ValueError(
            f"Licença Google Fonts não reconhecida em {directory}: {metadata.license!r}."
        ) from exc
    license_path = next(
        (directory / name for name in filenames if (directory / name).is_file()), None
    )
    if license_path is None:
        return None
    return {
        "id": license_id,
        "filename": license_path.name,
        "sha256": hashlib.sha256(blobs.read(license_path)).hexdigest(),
    }


def _variant(font, *, directory: str, blob_oids: dict[str, str]) -> dict[str, object]:
    """Converte uma variante do textproto em dados estritos de runtime."""
    filename = font.filename
    if (
        not _SAFE_FILENAME_RE.fullmatch(filename)
        or Path(filename).name != filename
        or font.style not in {"normal", "italic"}
        or not 100 <= font.weight <= 900
    ):
        raise ValueError(f"Variante Google Fonts inválida: {filename!r}.")
    path = f"{directory}/{filename}"
    try:
        git_blob_oid = blob_oids[path]
    except KeyError as exc:
        raise ValueError(f"Blob de fonte ausente na árvore Git: {path!r}.") from exc
    return {
        "filename": filename,
        "style": font.style,
        "weight": font.weight,
        "variable": "[" in filename and "]" in filename,
        "gitBlobOid": git_blob_oid,
    }


def build_catalog(checkout: Path, revision: str) -> dict[str, object]:
    """Monta o catálogo determinístico a partir de METADATA.pb e licenças."""
    families: dict[str, dict[str, object]] = {}
    excluded: list[dict[str, str]] = []
    blob_oids = _git_blob_oids(checkout, revision)
    with _GitBlobReader(checkout, revision) as blobs:
        for metadata_path in sorted(checkout.glob("*/*/METADATA.pb")):
            directory = metadata_path.parent
            if directory.name.endswith("_todelist"):
                continue
            relative_directory = directory.relative_to(checkout).as_posix()
            if relative_directory.split("/", 1)[0] not in {"ofl", "apache", "ufl"}:
                continue

            metadata = FamilyProto()
            # O schema público do repositório pode ganhar campos que não afetam o
            # resolvedor. Os campos essenciais abaixo continuam validados de forma
            # fechada antes de o catálogo ser publicado.
            metadata_bytes = blobs.read(metadata_path)
            text_format.Parse(
                metadata_bytes.decode("utf-8"),
                metadata,
                allow_unknown_field=True,
            )
            license_info = _license(metadata, directory, blobs)
            if license_info is None:
                excluded.append(
                    {"directory": relative_directory, "reason": "license-text-missing"}
                )
                continue
            key = _family_key(metadata.name)
            if not key or len(key) > 128:
                raise ValueError(f"Nome de família inválido em {metadata_path}.")
            if key in families:
                raise ValueError(f"Família duplicada no catálogo: {metadata.name!r}.")
            variants = sorted(
                (
                    _variant(
                        font,
                        directory=relative_directory,
                        blob_oids=blob_oids,
                    )
                    for font in metadata.fonts
                ),
                key=lambda item: (
                    str(item["style"]),
                    int(item["weight"]),
                    str(item["filename"]),
                ),
            )
            if not variants:
                raise ValueError(f"Família sem variantes em {metadata_path}.")
            axes = sorted(
                (
                    {
                        "tag": axis.tag,
                        "minimum": axis.min_value,
                        "maximum": axis.max_value,
                    }
                    for axis in metadata.axes
                ),
                key=lambda item: str(item["tag"]),
            )
            families[key] = {
                "name": metadata.name,
                "directory": relative_directory,
                "subsets": sorted(set(metadata.subsets)),
                "axes": axes,
                "variants": variants,
                "license": license_info,
                "metadataSha256": hashlib.sha256(metadata_bytes).hexdigest(),
            }

    if len(families) < 1_000:
        raise ValueError("O checkout não contém um catálogo Google Fonts completo.")
    return {
        "schemaVersion": "1.0.0",
        "provider": "google-fonts",
        "revision": revision,
        "families": dict(sorted(families.items())),
        "excluded": excluded,
    }


def _write_catalog(output: Path, catalog: dict[str, object]) -> None:
    """Publica o JSON de forma atômica e com serialização determinística."""
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, raw_temporary = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    """Executa a geração a partir dos argumentos de linha de comando."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    checkout = args.checkout.resolve(strict=True)
    revision = args.revision.casefold()
    if not _REVISION_RE.fullmatch(revision):
        raise SystemExit("--revision precisa ser um SHA Git completo em minúsculas.")
    if _checkout_revision(checkout) != revision:
        raise SystemExit("O checkout não está no commit informado em --revision.")
    catalog = build_catalog(checkout, revision)
    _write_catalog(args.output, catalog)
    print(
        f"{len(catalog['families'])} famílias publicadas; "
        f"{len(catalog['excluded'])} excluídas; destino: {args.output}"
    )


if __name__ == "__main__":
    main()
