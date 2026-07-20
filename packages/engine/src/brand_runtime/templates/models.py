"""Contratos versionados para famílias de templates visuais."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from brand_runtime.ir.models import CamelModel
from brand_runtime.kit.models import LayoutSpec, NonBlankString, Profile

SemVer = Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+$")]


class ExportSupport(CamelModel):
    """Capacidade declarada por composição, sem prometer paridade inexistente."""

    preview: Literal["native"] = "native"
    png: Literal["native"] = "native"
    pdf: Literal["native"] = "native"
    pptx: Literal["native", "hybrid", "unsupported"] = "hybrid"


class TemplateEvaluation(CamelModel):
    """Gate determinístico aplicado antes de publicar um pacote."""

    kind: Literal[
        "no-overflow",
        "safe-area",
        "contrast",
        "type-hierarchy",
        "negative-space",
        "structural-distance",
    ]
    stage: Literal["portable", "guard", "renderer"] = "portable"
    severity: Literal["error", "warning"] = "error"
    minimum: float | None = None
    maximum: float | None = None

    @model_validator(mode="after")
    def _stage_matches_measurement(self) -> Self:
        required_stage = {
            "no-overflow": "renderer",
            "contrast": "guard",
        }.get(self.kind, "portable")
        if self.stage != required_stage:
            raise ValueError(
                f"A avaliação {self.kind} precisa executar no estágio {required_stage}."
            )
        return self


class TemplateComposition(CamelModel):
    """Composição individual compilada e seu conteúdo demonstrativo."""

    id: NonBlankString
    name_pt: NonBlankString
    intent_pt: NonBlankString
    layout: LayoutSpec
    sample_content_pt: dict[NonBlankString, str]
    critical_nodes: list[NonBlankString] = Field(default_factory=list)
    allowed_overlaps: list[tuple[NonBlankString, NonBlankString]] = Field(default_factory=list)
    export_support: ExportSupport = Field(default_factory=ExportSupport)

    @model_validator(mode="after")
    def _references_belong_to_layout(self) -> Self:
        if self.layout.template_ref is None or self.layout.template_ref.composition_id != self.id:
            raise ValueError("A composição precisa apontar para o mesmo id em layout.templateRef.")
        element_ids = {
            *(slot.id for slot in self.layout.slots),
            *(layer.id for layer in self.layout.locked_layers),
        }
        unknown_samples = set(self.sample_content_pt) - {
            slot.id for slot in self.layout.slots if slot.kind != "logo"
        }
        if unknown_samples:
            raise ValueError(
                "sampleContentPt referencia slots desconhecidos: "
                + ", ".join(sorted(unknown_samples))
            )
        unknown_critical = set(self.critical_nodes) - element_ids
        if unknown_critical:
            raise ValueError(
                "criticalNodes referencia elementos desconhecidos: "
                + ", ".join(sorted(unknown_critical))
            )
        return self


class TemplatePackage(CamelModel):
    """Pacote seguro: dados declarativos, sem CSS, HTML ou código executável."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    id: NonBlankString
    version: SemVer
    family: NonBlankString
    title_pt: NonBlankString
    description_pt: NonBlankString
    scene_schema_version: Literal["2.0.0"] = "2.0.0"
    profiles: list[Profile] = Field(min_length=1)
    required_roles: list[NonBlankString] = Field(min_length=1)
    required_color_tokens: list[NonBlankString] = Field(min_length=1)
    compositions: list[TemplateComposition] = Field(min_length=1)
    evaluations: list[TemplateEvaluation] = Field(min_length=1)
    license: Literal["project-internal"] = "project-internal"

    @model_validator(mode="after")
    def _package_is_coherent(self) -> Self:
        ids = [composition.id for composition in self.compositions]
        if len(ids) != len(set(ids)):
            raise ValueError("Os ids das composições precisam ser únicos no pacote.")
        if len(self.profiles) != len(set(self.profiles)):
            raise ValueError("Os perfis do pacote não podem se repetir.")
        evaluation_kinds = [evaluation.kind for evaluation in self.evaluations]
        required_evaluations = {
            "no-overflow",
            "safe-area",
            "contrast",
            "type-hierarchy",
            "negative-space",
            "structural-distance",
        }
        if set(evaluation_kinds) != required_evaluations or len(evaluation_kinds) != len(
            required_evaluations
        ):
            raise ValueError("O pacote precisa declarar uma vez cada gate de publicação.")
        for composition in self.compositions:
            reference = composition.layout.template_ref
            if reference is None or (reference.package_id, reference.version) != (
                self.id,
                self.version,
            ):
                raise ValueError("Toda composição precisa apontar para id e versão do pacote.")
            if composition.layout.profile not in self.profiles:
                raise ValueError("Uma composição usa perfil não publicado pelo pacote.")
        return self
