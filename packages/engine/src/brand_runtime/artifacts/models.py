"""Instância reabrível de um template, sem depender do estado futuro do registry."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from brand_runtime.ir.models import CamelModel
from brand_runtime.kit.models import (
    ContentSpec,
    ImageValue,
    LayerOverride,
    LayoutSpec,
    NonBlankString,
    ShapeLayer,
    Slot,
    SurfaceStyle,
    TemplateRef,
    TextValue,
)

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
TruthStatus = Literal["confirmed", "derived", "placeholder", "missing"]


class ArtifactValue(CamelModel):
    """Valor acompanhado de seu estado de verdade e proveniência legível."""

    status: TruthStatus
    value: TextValue | ImageValue | None = None
    source_pt: str | None = None

    @model_validator(mode="after")
    def _missing_has_no_value(self) -> Self:
        if self.status == "missing" and self.value is not None:
            raise ValueError("Conteúdo missing não pode carregar um valor.")
        if self.status != "missing" and self.value is None:
            raise ValueError("Conteúdo presente precisa carregar um valor.")
        return self


class ArtifactInstance(CamelModel):
    """Snapshot autocontido e reabrível de uma composição publicada."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    id: NonBlankString
    template_ref: TemplateRef
    brand_revision_id: NonBlankString
    scene_snapshot: LayoutSpec
    scene_hash: Sha256
    values: dict[NonBlankString, ArtifactValue]
    background_color_token: NonBlankString | None = None
    overrides: dict[NonBlankString, LayerOverride] = Field(default_factory=dict)
    asset_bindings: dict[NonBlankString, NonBlankString] = Field(default_factory=dict)
    locale: Literal["pt-BR", "en", "unknown"] = "pt-BR"
    surface: SurfaceStyle | None = None
    added_slots: list[Slot] = Field(default_factory=list)
    added_layers: list[ShapeLayer] = Field(default_factory=list)

    @model_validator(mode="after")
    def _snapshot_matches_reference(self) -> Self:
        if self.scene_snapshot.id != self.template_ref.composition_id and (
            self.scene_snapshot.template_ref is None
            or self.scene_snapshot.template_ref != self.template_ref
        ):
            raise ValueError("O snapshot não corresponde à referência de template fixada.")
        if self.scene_snapshot.template_ref is not None and (
            self.scene_snapshot.template_ref != self.template_ref
        ):
            raise ValueError("templateRef e sceneSnapshot.templateRef divergem.")
        slots = {slot.id: slot for slot in [*self.scene_snapshot.slots, *self.added_slots]}
        invalid_bindings = [
            slot_id
            for slot_id in self.asset_bindings
            if slot_id not in slots or slots[slot_id].kind != "logo"
        ]
        if invalid_bindings:
            raise ValueError(
                "assetBindings só pode referenciar slots de logo conhecidos: "
                + ", ".join(sorted(invalid_bindings))
                + "."
            )
        return self


LegacyContentSpec = ContentSpec
