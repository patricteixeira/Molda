"""Derivação pura do StyleSystemIR a partir da revisão confirmada da marca."""

from __future__ import annotations

from brand_runtime.ir.models import BrandIR
from brand_runtime.kit.models import PROFILES
from brand_runtime.style.models import (
    ComponentStateStyle,
    GridStyle,
    ImageTreatment,
    MotionStyle,
    ShadowStyle,
    StrokeStyle,
    StyleSystemIR,
    TypeStyle,
)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _token(ir: BrandIR, *candidates: str) -> str:
    return next((token for token in candidates if token in ir.colors), next(iter(ir.colors)))


def derive_style_system(ir: BrandIR) -> StyleSystemIR:
    """Calcula escalas explícitas; ausência de direção produz um baseline neutro."""
    direction = ir.creative_direction
    density = direction.density.value if direction is not None else 0
    geometry = direction.geometry.value if direction is not None else 0
    materiality = direction.materiality.value if direction is not None else 0
    energy = direction.energy.value if direction is not None else 0
    negative_space = direction.negative_space if direction is not None else 0.5

    spacing_factor = _clamp(1 - density * 0.18, 0.82, 1.18)
    spacing = {
        "none": 0,
        "2xs": round(4 * spacing_factor, 2),
        "xs": round(8 * spacing_factor, 2),
        "sm": round(16 * spacing_factor, 2),
        "md": round(32 * spacing_factor, 2),
        "lg": round(64 * spacing_factor, 2),
        "xl": round(96 * spacing_factor, 2),
        "2xl": round(144 * spacing_factor, 2),
    }

    if geometry >= 0.15:
        radii = {"none": 0, "sm": 0, "md": 0, "lg": 0, "full": 9999}
    else:
        softness = _clamp((0.15 - geometry) / 1.15, 0, 1)
        radii = {
            "none": 0,
            "sm": round(6 * softness, 2),
            "md": round(14 * softness, 2),
            "lg": round(28 * softness, 2),
            "full": 9999,
        }

    foreground = _token(ir, "color.text", "color.primary")
    accent = _token(ir, "color.secondary", "color.primary", foreground)
    typography = {
        role_name: TypeStyle(
            role=role_name,
            font_token=role.font,
            color_token=role.color,
            min_size_px=role.min_size_px,
            max_size_px=role.max_size_px,
            line_height=role.line_height,
        )
        for role_name, role in ir.roles.items()
    }

    shadow_strength = _clamp((materiality - 0.1) * 0.18, 0, 0.18)
    grids = {}
    for profile, (width, _height, safe) in PROFILES.items():
        margin = round(_clamp(safe + negative_space * width * 0.055, safe, width * 0.14), 2)
        grids[profile] = GridStyle(
            profile=profile,
            columns=8 if profile == "doc-a4" else 12,
            margin_px=margin,
            gutter_px=round(_clamp(18 + negative_space * 22, 18, 40), 2),
        )

    if energy < -0.25:
        pace, fast, standard, easing = "calm", 240, 520, "ease-in-out"
    elif energy > 0.35:
        pace, fast, standard, easing = "direct", 110, 240, "ease-out"
    else:
        pace, fast, standard, easing = "measured", 170, 360, "ease-out"

    rationale = [
        "Escalas derivadas dos tokens confirmados sem alterar o Brand IR.",
        "O valor zero permanece explícito para raios, sombras e espaçamentos ausentes.",
    ]
    if direction is not None:
        rationale.extend(direction.rationale_pt[:4])

    return StyleSystemIR(
        brand_revision_id=ir.revision.id,
        spacing=spacing,
        radii=radii,
        typography=typography,
        strokes={
            "hairline": StrokeStyle(width_px=1, color_token=foreground, opacity=0.22),
            "rule": StrokeStyle(width_px=2, color_token=foreground, opacity=0.72),
            "accent": StrokeStyle(width_px=4, color_token=accent, opacity=1),
        },
        shadows={
            "none": ShadowStyle(color_token=foreground),
            "soft": ShadowStyle(
                offset_y_px=12,
                blur_px=32,
                spread_px=-8,
                color_token=foreground,
                opacity=round(shadow_strength, 3),
            ),
        },
        grids=grids,
        image_treatment=ImageTreatment(
            radius_token="none" if geometry >= 0.15 else "sm",
            contrast=round(
                _clamp(1 + (direction.contrast.value if direction else 0) * 0.08, 0.92, 1.08), 2
            ),
            saturation=round(_clamp(1 + materiality * 0.1, 0.9, 1.1), 2),
        ),
        motion=MotionStyle(
            pace=pace,
            duration_fast_ms=fast,
            duration_standard_ms=standard,
            easing=easing,
        ),
        component_states={
            "default": ComponentStateStyle(stroke_token="hairline"),
            "hover": ComponentStateStyle(opacity=1, scale=1.01, stroke_token="accent"),
            "disabled": ComponentStateStyle(opacity=0.42, stroke_token="hairline"),
        },
        rationale_pt=rationale,
    )
