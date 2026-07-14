"""Document Graph mínimo e versionado do M3."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from brand_runtime.ir.models import CamelModel


class BoundsPt(CamelModel):
    """Caixa do objeto em pontos, independente da unidade OOXML interna."""

    x: float = Field(allow_inf_nan=False)
    y: float = Field(allow_inf_nan=False)
    width: float = Field(gt=0, allow_inf_nan=False)
    height: float = Field(gt=0, allow_inf_nan=False)


class DocumentDiagnostic(CamelModel):
    """Finding estrutural encontrado antes da leitura semântica."""

    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    part: str | None = None


class DocumentNode(CamelModel):
    """Objeto editável reencontrado no arquivo externo."""

    id: str
    slide_index: int = Field(ge=1)
    shape_id: int = Field(ge=1)
    kind: Literal["text", "picture"]
    name: str
    role: str
    slot_id: str | None = None
    brand_revision_id: str | None = None
    semantic_source: Literal["name", "description", "placeholder"]
    text: str | None = None
    font_family: str | None = None
    font_size_pt: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    color: str | None = None
    bounds_pt: BoundsPt


class DocumentSource(CamelModel):
    """Identidade imutável do arquivo analisado."""

    format: Literal["pptx"] = "pptx"
    filename: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0)
    slide_count: int = Field(ge=1)


class DocumentGraph(CamelModel):
    """Representação semântica consumida pelos futuros linter e fixer."""

    schema_version: Literal["0.1.0"] = "0.1.0"
    source: DocumentSource
    nodes: list[DocumentNode]
    diagnostics: list[DocumentDiagnostic]
