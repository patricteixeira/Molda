"""Contratos do laboratório isolado de referências de templates."""

from __future__ import annotations

import unicodedata
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator

from brand_runtime.ir.models import CamelModel
from brand_runtime.kit.models import Profile

CORPUS_SCHEMA_VERSION = "0.1.0"
CORPUS_MANIFEST_FILENAME = "template-corpus.json"
REFERENCE_MANIFEST_FILENAME = "template-reference.json"

Slug = Annotated[
    str,
    Field(min_length=2, max_length=96, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
NonBlank = Annotated[str, Field(min_length=1, max_length=500, pattern=r".*\S.*")]
Composition = Literal["contemplative", "asymmetric", "modular", "expansive", "layered"]
Surface = Literal[
    "none",
    "paper-grain",
    "linear-rhythm",
    "technical-grid",
    "point-field",
    "concentric-rings",
]
Disposition = Literal[
    "needs-annotation",
    "negative-control",
    "redundant",
    "family-variant",
    "new-composition",
    "family-gap",
]

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
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".pdf": "application/pdf",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".json": "application/json",
    ".html": "text/html",
    ".css": "text/css",
    ".md": "text/markdown",
    ".txt": "text/plain",
}
_PREVIEW_MEDIA = {"image/png", "image/jpeg", "image/webp"}
_LICENSE_MEDIA = {"application/pdf", "text/markdown", "text/plain"}


def portable_path(value: str) -> str:
    """Exige path relativo, POSIX, NFC e portável também em Windows."""
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
        raise ValueError("O path não é portável ou pode escapar do corpus.")
    return value


class TemplateCorpusProvenance(CamelModel):
    """Autoria e permissão de uso de uma referência."""

    author: NonBlank
    ownership: Literal["authored", "licensed", "public-reference", "unknown"]
    usage_policy: Literal["project-internal", "derivative-authoring", "analysis-only"]
    license_id: Annotated[str, Field(min_length=1, max_length=160)] | None = None
    source_url: (
        Annotated[
            str,
            Field(max_length=2048, pattern=r"^https?://[^\s]+$"),
        ]
        | None
    ) = None
    notes_pt: Annotated[str, Field(max_length=2000)] | None = None

    @model_validator(mode="after")
    def _coherent_permission(self) -> Self:
        if self.ownership in {"public-reference", "unknown"} and (
            self.usage_policy != "analysis-only"
        ):
            raise ValueError(
                "Referências públicas ou sem autoria só podem ser usadas para análise."
            )
        if self.ownership == "licensed" and self.license_id is None:
            raise ValueError("Uma referência licenciada precisa identificar a licença.")
        return self


class TemplateReferenceFile(CamelModel):
    """Arquivo declarado, sem permissão implícita para execução."""

    path: Annotated[str, Field(min_length=1, max_length=240)]
    role: Literal["preview", "source", "license"]
    media_type: Literal[
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/svg+xml",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/json",
        "text/html",
        "text/css",
        "text/markdown",
        "text/plain",
    ]
    size: int = Field(ge=0, le=200 * 2**20)
    sha256: Sha256

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        return portable_path(value)

    @model_validator(mode="after")
    def _matches_declared_role(self) -> Self:
        path = PurePosixPath(self.path)
        if path.suffix != path.suffix.casefold():
            raise ValueError("A extensão do arquivo precisa usar letras minúsculas.")
        if _MEDIA_BY_SUFFIX.get(path.suffix) != self.media_type:
            raise ValueError("O mediaType não corresponde à extensão do arquivo.")
        if self.path == REFERENCE_MANIFEST_FILENAME:
            raise ValueError("O manifesto não pode declarar a si próprio.")
        if self.role == "preview" and self.media_type not in _PREVIEW_MEDIA:
            raise ValueError("A prévia precisa ser PNG, JPEG ou WebP.")
        if self.role == "license" and self.media_type not in _LICENSE_MEDIA:
            raise ValueError("A licença precisa ser PDF, Markdown ou texto simples.")
        return self


class TemplateGrammarAxes(CamelModel):
    """Seis eixos contínuos compartilhados com a direção criativa."""

    energy: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)
    geometry: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)
    density: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)
    formality: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)
    materiality: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)
    contrast: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)

    def values(self) -> tuple[float, float, float, float, float, float]:
        """Retorna a ordem canônica usada pelo classificador."""
        return (
            self.energy,
            self.geometry,
            self.density,
            self.formality,
            self.materiality,
            self.contrast,
        )


class TemplateGrammar(CamelModel):
    """Leitura humana da gramática; o auditor apenas compara o declarado."""

    axes: TemplateGrammarAxes
    compositions: list[Composition] = Field(min_length=1, max_length=5)
    surfaces: list[Surface] = Field(min_length=1, max_length=6)
    hierarchy: Literal["type-led", "image-led", "balanced", "data-led", "device-led"]
    alignment: Literal["grid", "axial", "free", "layered"]
    slot_roles: list[NonBlank] = Field(min_length=1, max_length=24)
    negative_space: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)

    @model_validator(mode="after")
    def _unique_vocabulary(self) -> Self:
        for values, label in (
            (self.compositions, "compositions"),
            (self.surfaces, "surfaces"),
            (self.slot_roles, "slotRoles"),
        ):
            keys = [value.casefold() for value in values]
            if len(keys) != len(set(keys)):
                raise ValueError(f"{label} não pode conter valores repetidos.")
        return self


class TemplateReferenceManifest(CamelModel):
    """Manifesto autocontido de uma referência em quarentena."""

    schema_version: Literal["0.1.0"]
    id: Slug
    title_pt: NonBlank
    intent: Literal["reference", "holdout", "negative-control"] = "reference"
    provenance: TemplateCorpusProvenance
    purposes: list[NonBlank] = Field(min_length=1, max_length=12)
    profiles: list[Profile] = Field(min_length=1, max_length=4)
    files: list[TemplateReferenceFile] = Field(min_length=1, max_length=50)
    grammar: TemplateGrammar | None = None

    @model_validator(mode="after")
    def _complete_reference(self) -> Self:
        paths = [unicodedata.normalize("NFC", item.path).casefold() for item in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("Os paths declarados precisam ser únicos sem distinguir maiúsculas.")
        if sum(item.role == "preview" for item in self.files) != 1:
            raise ValueError("Cada referência precisa declarar exatamente uma prévia.")
        purpose_keys = [value.casefold() for value in self.purposes]
        if len(purpose_keys) != len(set(purpose_keys)):
            raise ValueError("purposes não pode conter valores repetidos.")
        if len(self.profiles) != len(set(self.profiles)):
            raise ValueError("profiles não pode conter valores repetidos.")
        return self


class TemplateCorpusManifest(CamelModel):
    """Índice mínimo do corpus; cada item conserva seu próprio contrato."""

    schema_version: Literal["0.1.0"]
    id: Slug
    title_pt: NonBlank
    owner: NonBlank
    references: list[Annotated[str, Field(min_length=1, max_length=240)]] = Field(
        min_length=1,
        max_length=200,
    )

    @field_validator("references")
    @classmethod
    def _validate_references(cls, values: list[str]) -> list[str]:
        for value in values:
            portable_path(value)
            parts = value.split("/")
            if (
                len(parts) != 3
                or parts[0] != "references"
                or parts[2] != REFERENCE_MANIFEST_FILENAME
            ):
                raise ValueError(
                    "Cada referência deve usar references/<id>/template-reference.json."
                )
        keys = [unicodedata.normalize("NFC", value).casefold() for value in values]
        if len(keys) != len(set(keys)):
            raise ValueError("As referências precisam ser únicas sem distinguir maiúsculas.")
        return values


class TemplatePreviewEvidence(CamelModel):
    """Evidência raster determinística usada na comparação estrutural."""

    path: str
    media_type: Literal["image/png", "image/jpeg", "image/webp"]
    width_px: int = Field(gt=0)
    height_px: int = Field(gt=0)
    aspect_ratio: float = Field(gt=0.0, allow_inf_nan=False)
    sha256: Sha256
    difference_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{16}$")]


class TemplateFamilyMatch(CamelModel):
    """Família vizinha e componentes explicáveis da pontuação."""

    family_id: Slug
    score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    axis_similarity: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    composition_overlap: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    surface_overlap: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)


class TemplateReferenceAssessment(CamelModel):
    """Classificação de triagem, nunca autorização de promoção."""

    reference_id: Slug
    title_pt: NonBlank
    intent: Literal["reference", "holdout", "negative-control"]
    preview: TemplatePreviewEvidence
    disposition: Disposition
    nearest_family: TemplateFamilyMatch | None = None
    duplicate_of: Slug | None = None
    findings_pt: list[NonBlank] = Field(min_length=1, max_length=8)


class TemplateSimilarityPair(CamelModel):
    """Relação visual suspeita entre duas referências."""

    left_reference_id: Slug
    right_reference_id: Slug
    kind: Literal["exact-duplicate", "structural-near-duplicate"]
    structural_similarity: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)


class TemplateCorpusReport(CamelModel):
    """Recibo determinístico e exclusivamente orientado à revisão humana."""

    schema_version: Literal["0.1.0"] = CORPUS_SCHEMA_VERSION
    status: Literal["ready-for-review"] = "ready-for-review"
    promotion_policy: Literal["manual-review-required"] = "manual-review-required"
    corpus_id: Slug
    title_pt: NonBlank
    reference_count: int = Field(ge=1, le=200)
    total_bytes: int = Field(ge=0)
    corpus_sha256: Sha256
    assessments: list[TemplateReferenceAssessment] = Field(min_length=1, max_length=200)
    similarity_pairs: list[TemplateSimilarityPair] = Field(default_factory=list)
