"""Brand Package 0.1: fronteira de arquivo para adapters comunitários.

Um adapter roda fora do core e materializa a convenção de intake existente.
O manifesto declara todos os bytes do pacote para que a mesma saída possa ser
verificada localmente, na API ou em CI sem executar o adapter novamente.
"""

from __future__ import annotations

import hashlib
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import ConfigDict, Field, ValidationError, field_validator, model_validator

from brand_runtime.ir.models import CamelModel

MANIFEST_FILENAME = "brand-package.json"
PACKAGE_SCHEMA_VERSION = "0.1.0"
_HASH_PATTERN = r"^[0-9a-f]{64}$"
_ADAPTER_ID_PATTERN = r"^[a-z0-9]+(?:[.-][a-z0-9]+)+$"
_SOURCE_KIND_PATTERN = r"^[a-z][a-z0-9-]{1,63}$"
_SEMVER_PATTERN = (
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
_CHUNK_SIZE = 64 * 1024
_MAX_MANIFEST_BYTES = 1024 * 1024
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
_MEDIA_BY_SUFFIX = {
    ".pdf": "application/pdf",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".json": "application/json",
}


class PackageValidationError(ValueError):
    """Falha de contrato ou integridade em um Brand Package declarado."""

    def __init__(self, code: str, message: str, *, path: str | None = None) -> None:
        """Preserva código estável e path seguro para diagnóstico por adapter."""
        super().__init__(message)
        self.code = code
        self.path = path


def _portable_path(value: str) -> str:
    """Exige path POSIX relativo, NFC e portável também em Windows."""
    if not value or value != unicodedata.normalize("NFC", value) or "\\" in value:
        raise ValueError("O path precisa ser relativo, POSIX e normalizado em NFC.")
    candidate = PurePosixPath(value)
    parts = value.split("/")
    if candidate.is_absolute() or any(
        part in {"", ".", ".."}
        or ":" in part
        or part.endswith((".", " "))
        or part.split(".", maxsplit=1)[0].upper() in _WINDOWS_RESERVED
        for part in parts
    ):
        raise ValueError("O path não é portável ou pode escapar do pacote.")
    return value


class AdapterIdentity(CamelModel):
    """Identidade versionada de quem produziu o pacote."""

    id: str = Field(min_length=3, max_length=128, pattern=_ADAPTER_ID_PATTERN)
    name: str = Field(min_length=1, max_length=100)
    version: str = Field(pattern=_SEMVER_PATTERN)


class BrandPackageSource(CamelModel):
    """Origem externa, sem exigir URL, token ou identificador sensível."""

    kind: str = Field(pattern=_SOURCE_KIND_PATTERN)
    label: str | None = Field(default=None, min_length=1, max_length=160)


class BrandPackageFile(CamelModel):
    """Arquivo declarado pelo adapter e consumível pelo intake atual."""

    model_config = ConfigDict(
        json_schema_extra={
            "allOf": [
                {
                    "if": {"properties": {"role": {"const": "logo"}}, "required": ["role"]},
                    "then": {
                        "properties": {
                            "path": {"pattern": "^assets/logos/.+\\.(?:svg|png)$"},
                            "mediaType": {"enum": ["image/svg+xml", "image/png"]},
                        }
                    },
                },
                {
                    "if": {"properties": {"role": {"const": "font"}}, "required": ["role"]},
                    "then": {
                        "properties": {
                            "path": {"pattern": "^fonts/.+\\.(?:ttf|otf)$"},
                            "mediaType": {"enum": ["font/ttf", "font/otf"]},
                        }
                    },
                },
                {
                    "if": {"properties": {"role": {"const": "tokens"}}, "required": ["role"]},
                    "then": {
                        "properties": {
                            "path": {"pattern": "^(?:tokens|[^/]+\\.tokens)\\.json$"},
                            "mediaType": {"const": "application/json"},
                        }
                    },
                },
                {
                    "if": {
                        "properties": {"role": {"const": "guideline"}},
                        "required": ["role"],
                    },
                    "then": {
                        "properties": {
                            "path": {"pattern": "^[^/]+\\.pdf$"},
                            "mediaType": {"const": "application/pdf"},
                        }
                    },
                },
                {
                    "if": {
                        "properties": {"role": {"const": "reference"}},
                        "required": ["role"],
                    },
                    "then": {
                        "properties": {
                            "path": {"pattern": "^references/.+\\.pdf$"},
                            "mediaType": {"const": "application/pdf"},
                        }
                    },
                },
            ]
        }
    )

    path: str = Field(
        min_length=1,
        max_length=240,
        json_schema_extra={
            "pattern": r"^(?!/)(?!.*\\)(?!.*(?:^|/)\.{1,2}(?:/|$))(?!.*:)(?!.*//).+$"
        },
    )
    role: Literal["guideline", "logo", "font", "tokens", "reference"]
    media_type: Literal[
        "application/pdf",
        "image/svg+xml",
        "image/png",
        "font/ttf",
        "font/otf",
        "application/json",
    ]
    size: int = Field(ge=0, le=200 * 2**20)
    sha256: Annotated[str, Field(pattern=_HASH_PATTERN)]

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        return _portable_path(value)

    @model_validator(mode="after")
    def _matches_intake_convention(self) -> Self:
        path = PurePosixPath(self.path)
        expected_media = _MEDIA_BY_SUFFIX.get(path.suffix.casefold())
        if expected_media != self.media_type:
            raise ValueError("O mediaType não corresponde à extensão do arquivo.")
        if path.suffix != path.suffix.casefold():
            raise ValueError("A extensão do arquivo precisa usar letras minúsculas.")
        if self.path == MANIFEST_FILENAME:
            raise ValueError("O manifesto não pode declarar a si próprio.")
        if self.role == "logo" and not (
            self.path.startswith("assets/logos/")
            and self.media_type in {"image/svg+xml", "image/png"}
        ):
            raise ValueError("Logos devem usar assets/logos/ e SVG ou PNG.")
        if self.role == "font" and not (
            self.path.startswith("fonts/") and self.media_type in {"font/ttf", "font/otf"}
        ):
            raise ValueError("Fontes devem usar fonts/ e TTF ou OTF.")
        if self.role == "tokens" and not (
            "/" not in self.path
            and self.media_type == "application/json"
            and (self.path == "tokens.json" or self.path.endswith(".tokens.json"))
        ):
            raise ValueError("Tokens devem usar tokens.json ou *.tokens.json na raiz.")
        if self.role == "guideline" and not (
            "/" not in self.path and self.media_type == "application/pdf"
        ):
            raise ValueError("Diretrizes devem ser PDFs na raiz do pacote.")
        if self.role == "reference" and not (
            self.path.startswith("references/") and self.media_type == "application/pdf"
        ):
            raise ValueError("Referências devem ser PDFs em references/.")
        return self


class BrandPackageManifest(CamelModel):
    """Manifesto completo e determinístico produzido por um adapter."""

    schema_version: Literal["0.1.0"]
    adapter: AdapterIdentity
    source: BrandPackageSource
    files: list[BrandPackageFile] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def _unique_paths(self) -> Self:
        keys = [unicodedata.normalize("NFC", item.path).casefold() for item in self.files]
        if len(keys) != len(set(keys)):
            raise ValueError("Os paths declarados precisam ser únicos sem distinguir maiúsculas.")
        return self


class PackageValidationReport(CamelModel):
    """Recibo determinístico emitido pelo validador de conformidade."""

    schema_version: Literal["0.1.0"] = PACKAGE_SCHEMA_VERSION
    status: Literal["pass"] = "pass"
    adapter: AdapterIdentity
    source: BrandPackageSource
    file_count: int = Field(ge=1, le=200)
    total_bytes: int = Field(ge=0)
    package_sha256: Annotated[str, Field(pattern=_HASH_PATTERN)]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest(path: Path) -> BrandPackageManifest:
    try:
        if path.is_symlink() or not path.is_file():
            raise PackageValidationError(
                "MANIFEST_MISSING",
                f"O pacote declarado precisa conter {MANIFEST_FILENAME}.",
                path=MANIFEST_FILENAME,
            )
        if path.stat().st_size > _MAX_MANIFEST_BYTES:
            raise PackageValidationError(
                "MANIFEST_TOO_LARGE",
                "O manifesto excede o limite de 1 MiB.",
                path=MANIFEST_FILENAME,
            )
        return BrandPackageManifest.model_validate_json(path.read_text(encoding="utf-8"))
    except PackageValidationError:
        raise
    except (OSError, UnicodeError, ValidationError) as exc:
        raise PackageValidationError(
            "MANIFEST_INVALID",
            "O manifesto do Brand Package não corresponde ao contrato 0.1.0.",
            path=MANIFEST_FILENAME,
        ) from exc


def _inventory(base: Path) -> dict[str, Path]:
    inventory: dict[str, Path] = {}
    folded: set[str] = set()
    try:
        entries = sorted(base.rglob("*"), key=lambda item: item.as_posix().casefold())
    except OSError as exc:
        raise PackageValidationError(
            "PACKAGE_UNREADABLE", "Não foi possível ler o pacote."
        ) from exc
    for entry in entries:
        relative = entry.relative_to(base).as_posix()
        if entry.is_symlink():
            raise PackageValidationError(
                "SYMLINK_FORBIDDEN",
                "Brand Packages declarados não podem conter links simbólicos.",
                path=relative,
            )
        if not entry.is_file():
            continue
        key = unicodedata.normalize("NFC", relative).casefold()
        if key in folded:
            raise PackageValidationError(
                "PATH_COLLISION",
                "O pacote contém paths que colidem sem distinguir maiúsculas.",
                path=relative,
            )
        folded.add(key)
        inventory[relative] = entry
    return inventory


def validate_brand_package(
    package_dir: Path,
    *,
    max_files: int = 200,
    max_total_bytes: int = 200 * 2**20,
) -> PackageValidationReport:
    """Valida manifesto, inventário, tamanhos e hashes sem alterar o pacote."""
    try:
        base = Path(package_dir).resolve(strict=True)
    except OSError as exc:
        raise PackageValidationError(
            "PACKAGE_MISSING", "O Brand Package informado não é um diretório legível."
        ) from exc
    if not base.is_dir():
        raise PackageValidationError(
            "PACKAGE_MISSING", "O Brand Package informado não é um diretório legível."
        )
    manifest = _manifest(base / MANIFEST_FILENAME)
    if len(manifest.files) > max_files:
        raise PackageValidationError("TOO_MANY_FILES", "O pacote contém arquivos demais.")

    inventory = _inventory(base)
    declared = {item.path: item for item in manifest.files}
    actual_paths = set(inventory).difference({MANIFEST_FILENAME})
    declared_paths = set(declared)
    missing = sorted(declared_paths - actual_paths)
    unexpected = sorted(actual_paths - declared_paths)
    if missing:
        raise PackageValidationError(
            "FILE_MISSING",
            "O pacote não contém todos os arquivos declarados.",
            path=missing[0],
        )
    if unexpected:
        raise PackageValidationError(
            "FILE_UNDECLARED",
            "O pacote contém arquivo não declarado no manifesto.",
            path=unexpected[0],
        )

    total_bytes = 0
    identity = hashlib.sha256()
    for relative in sorted(declared, key=str.casefold):
        item = declared[relative]
        target = inventory[relative]
        try:
            size = target.stat().st_size
        except OSError as exc:
            raise PackageValidationError(
                "FILE_UNREADABLE",
                "Não foi possível ler um arquivo declarado.",
                path=relative,
            ) from exc
        total_bytes += size
        if total_bytes > max_total_bytes:
            raise PackageValidationError(
                "PACKAGE_TOO_LARGE", "O pacote excede o tamanho máximo permitido."
            )
        if size != item.size:
            raise PackageValidationError(
                "SIZE_MISMATCH",
                "O tamanho do arquivo não corresponde ao manifesto.",
                path=relative,
            )
        try:
            digest = _sha256(target)
        except OSError as exc:
            raise PackageValidationError(
                "FILE_UNREADABLE",
                "Não foi possível ler um arquivo declarado.",
                path=relative,
            ) from exc
        if digest != item.sha256:
            raise PackageValidationError(
                "HASH_MISMATCH",
                "O SHA-256 do arquivo não corresponde ao manifesto.",
                path=relative,
            )
        identity.update(relative.encode("utf-8"))
        identity.update(b"\0")
        identity.update(digest.encode("ascii"))
        identity.update(b"\0")
        identity.update(str(size).encode("ascii"))
        identity.update(b"\n")

    return PackageValidationReport(
        adapter=manifest.adapter,
        source=manifest.source,
        file_count=len(manifest.files),
        total_bytes=total_bytes,
        package_sha256=identity.hexdigest(),
    )
