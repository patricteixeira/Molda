"""Sistema visual derivado e versionado, separado dos fatos do Brand IR."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from brand_runtime.ir.models import CamelModel
from brand_runtime.kit.models import Profile

NonBlankString = Annotated[str, Field(min_length=1, pattern=r".*\S.*")]
NonNegative = Annotated[float, Field(ge=0.0, allow_inf_nan=False)]
Opacity = Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)]


class TypeStyle(CamelModel):
    """Papel tipográfico resolvido para uso em componentes e templates."""

    role: NonBlankString
    font_token: NonBlankString
    color_token: NonBlankString
    min_size_px: Annotated[float, Field(gt=0.0, allow_inf_nan=False)]
    max_size_px: Annotated[float, Field(gt=0.0, allow_inf_nan=False)]
    line_height: Annotated[float, Field(ge=0.5, le=3.0, allow_inf_nan=False)]
    letter_spacing_em: Annotated[float, Field(ge=-0.25, le=1.0, allow_inf_nan=False)] = 0

    @model_validator(mode="after")
    def _ordered_sizes(self) -> TypeStyle:
        if self.min_size_px > self.max_size_px:
            raise ValueError("O tamanho mínimo não pode superar o máximo.")
        return self


class StrokeStyle(CamelModel):
    """Traço semântico fechado por token de cor."""

    width_px: NonNegative
    color_token: NonBlankString
    opacity: Opacity = 1


class ShadowStyle(CamelModel):
    """Elevação determinística; opacidade zero representa ausência real."""

    offset_x_px: float = 0
    offset_y_px: float = 0
    blur_px: NonNegative = 0
    spread_px: float = 0
    color_token: NonBlankString
    opacity: Opacity = 0


class GridStyle(CamelModel):
    """Grade responsiva resolvida para um perfil canônico."""

    profile: Profile
    columns: Annotated[int, Field(ge=1, le=24)]
    margin_px: NonNegative
    gutter_px: NonNegative


class ImageTreatment(CamelModel):
    """Tratamento de imagem sem filtros ou CSS arbitrários."""

    fit: Literal["contain", "cover"] = "cover"
    crop_bias: Literal["center", "top", "bottom", "left", "right"] = "center"
    radius_token: NonBlankString = "none"
    contrast: Annotated[float, Field(ge=0.5, le=1.5, allow_inf_nan=False)] = 1
    saturation: Annotated[float, Field(ge=0.0, le=1.5, allow_inf_nan=False)] = 1


class MotionStyle(CamelModel):
    """Ritmo de interação com alternativa explícita para movimento reduzido."""

    pace: Literal["calm", "measured", "direct"]
    duration_fast_ms: Annotated[int, Field(ge=0, le=2000)]
    duration_standard_ms: Annotated[int, Field(ge=0, le=4000)]
    easing: Literal["linear", "ease-out", "ease-in-out"]
    reduced_motion: Literal["remove", "shorten"] = "remove"


class ComponentStateStyle(CamelModel):
    """Aparência semântica compartilhada por estados de componentes."""

    opacity: Opacity = 1
    scale: Annotated[float, Field(ge=0.5, le=1.5, allow_inf_nan=False)] = 1
    stroke_token: NonBlankString = "hairline"


class StyleSystemIR(CamelModel):
    """Decisões de sistema calculadas sem se passarem por fatos do manual."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    brand_revision_id: NonBlankString
    derivation_status: Literal["derived"] = "derived"
    spacing: dict[NonBlankString, NonNegative]
    radii: dict[NonBlankString, NonNegative]
    typography: dict[NonBlankString, TypeStyle]
    strokes: dict[NonBlankString, StrokeStyle]
    shadows: dict[NonBlankString, ShadowStyle]
    grids: dict[Profile, GridStyle]
    image_treatment: ImageTreatment
    motion: MotionStyle
    component_states: dict[NonBlankString, ComponentStateStyle]
    rationale_pt: list[NonBlankString] = Field(min_length=1, max_length=8)
