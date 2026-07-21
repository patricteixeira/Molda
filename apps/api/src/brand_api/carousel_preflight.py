"""Preflight geométrico de candidatos antes da composição automática."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from brand_api.carousel_composition import CarouselCandidateAssessment
from brand_runtime import BrandIR, ContentSpec, LayoutSpec, materialize_content_layout
from brand_runtime.colors import wcag_contrast
from brand_runtime.guard.static_checks import run_static_checks
from brand_runtime.kit.models import LayerOverride, ShapeLayer, Slot, TextValue

_COLLISION_EXEMPT_IDS = {"echo-near", "echo-far"}
_COLLISION_EXEMPT_LAYOUT_TERMS = ("collision", "overlap")
_MIN_CONTRAST_NORMAL = 4.5
_MIN_CONTRAST_LARGE = 3.0


@dataclass(frozen=True)
class _TextGeometry:
    """Medição aproximada de uma camada textual ativa."""

    slot_id: str
    area: tuple[float, float, float, float]
    ink: tuple[float, float, float, float]
    font_size_px: float
    overflow: bool


def _effective_area(slot: Slot, override: LayerOverride | None) -> tuple[float, ...]:
    return override.area if override is not None and override.area is not None else slot.area


def _effective_line_height(
    ir: BrandIR,
    slot: Slot,
    override: LayerOverride | None,
) -> float:
    if override is not None and override.line_height is not None:
        return override.line_height
    if slot.line_height is not None:
        return slot.line_height
    role = ir.roles.get(slot.role or "")
    return role.line_height if role is not None else 1.2


def _effective_letter_spacing(slot: Slot, override: LayerOverride | None) -> float:
    if override is not None and override.letter_spacing_em is not None:
        return override.letter_spacing_em
    return slot.letter_spacing_em


def _effective_transform(slot: Slot, override: LayerOverride | None) -> str:
    if override is not None and override.text_transform is not None:
        return override.text_transform
    return slot.text_transform


def _glyph_units(character: str) -> float:
    if character.isspace():
        return 0.32
    if character in "ilI|!.,:;'`´":
        return 0.28
    if character in "mwMW@%&QO":
        return 0.88
    if character.isupper():
        return 0.64
    if character.isdigit():
        return 0.56
    return 0.52


def _line_units(text: str, letter_spacing_em: float) -> float:
    if not text:
        return 0.0
    return sum(_glyph_units(character) for character in text) + max(0, len(text) - 1) * max(
        -0.2,
        letter_spacing_em,
    )


def _wrapped_line_units(text: str, capacity: float, letter_spacing_em: float) -> list[float]:
    """Simula `pre-wrap` com `overflow-wrap: break-word` em unidades de fonte."""
    lines: list[float] = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        current = 0.0
        for word in words:
            word_units = _line_units(word, letter_spacing_em)
            separator = _glyph_units(" ") if current else 0.0
            if current + separator + word_units <= capacity:
                current += separator + word_units
                continue
            if current:
                lines.append(current)
                current = 0.0
            while word_units > capacity and capacity > 0:
                lines.append(capacity)
                word_units -= capacity
            current = word_units
        lines.append(current)
    return lines or [0.0]


def _geometry_at_size(
    slot: Slot,
    override: LayerOverride | None,
    text: str,
    font_size_px: float,
    line_height: float,
    letter_spacing_em: float,
) -> _TextGeometry:
    x, y, width, height = _effective_area(slot, override)
    transformed = text.upper() if _effective_transform(slot, override) == "uppercase" else text
    capacity = max(1.0, width / font_size_px)
    line_units = _wrapped_line_units(transformed, capacity, letter_spacing_em)
    ink_width = min(width, max(line_units, default=0.0) * font_size_px)
    ink_height = len(line_units) * font_size_px * line_height
    align = (
        override.text_align
        if override is not None and override.text_align is not None
        else slot.text_align
    )
    ink_x = (
        x
        if align == "left"
        else x + width - ink_width
        if align == "right"
        else x + (width - ink_width) / 2
    )
    return _TextGeometry(
        slot_id=slot.id,
        area=(x, y, width, height),
        ink=(ink_x, y, ink_width, min(ink_height, height)),
        font_size_px=font_size_px,
        overflow=ink_height > height + 1.0,
    )


def _measure_text(
    ir: BrandIR,
    slot: Slot,
    override: LayerOverride | None,
    text: str,
) -> _TextGeometry:
    role = ir.roles.get(slot.role or "")
    minimum = float(role.min_size_px if role is not None else 12)
    maximum = float(role.max_size_px if role is not None else minimum)
    explicit = (
        override.font_size_px
        if override is not None and override.font_size_px is not None
        else slot.font_size_px
    )
    line_height = _effective_line_height(ir, slot, override)
    letter_spacing = _effective_letter_spacing(slot, override)
    if explicit is not None:
        return _geometry_at_size(
            slot,
            override,
            text,
            float(explicit),
            line_height,
            letter_spacing,
        )
    if slot.fit == "fixed":
        return _geometry_at_size(
            slot,
            override,
            text,
            maximum,
            line_height,
            letter_spacing,
        )
    for size in range(math.floor(maximum), math.ceil(minimum) - 1, -1):
        geometry = _geometry_at_size(
            slot,
            override,
            text,
            float(size),
            line_height,
            letter_spacing,
        )
        if not geometry.overflow:
            return geometry
    return _geometry_at_size(
        slot,
        override,
        text,
        minimum,
        line_height,
        letter_spacing,
    )


def _intersection_ratio(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[0] + first[2], second[0] + second[2])
    bottom = min(first[1] + first[3], second[1] + second[3])
    if right <= left or bottom <= top:
        return 0.0
    intersection = (right - left) * (bottom - top)
    smaller = min(first[2] * first[3], second[2] * second[3])
    return intersection / smaller if smaller else 0.0


def _coverage_ratio(
    covering: tuple[float, float, float, float],
    target: tuple[float, float, float, float],
) -> float:
    left = max(covering[0], target[0])
    top = max(covering[1], target[1])
    right = min(covering[0] + covering[2], target[0] + target[2])
    bottom = min(covering[1] + covering[3], target[1] + target[3])
    if right <= left or bottom <= top:
        return 0.0
    target_area = target[2] * target[3]
    return ((right - left) * (bottom - top)) / target_area if target_area else 0.0


def _covers(
    layer: ShapeLayer,
    area: tuple[float, float, float, float],
) -> bool:
    return layer.opacity >= 0.9 and _coverage_ratio(layer.area, area) >= 0.82


def _effective_opacity(slot: Slot, override: LayerOverride | None) -> float:
    if override is not None and override.opacity is not None:
        return override.opacity
    return slot.opacity


def _effective_fill_mode(slot: Slot, override: LayerOverride | None) -> str:
    if override is not None and override.fill_mode is not None:
        return override.fill_mode
    return slot.fill_mode


def _background_token(
    layout: LayoutSpec,
    content: ContentSpec,
    geometry: _TextGeometry,
    slot: Slot,
) -> str | None:
    slot_z = slot.z_index or 0
    local_layers = sorted(
        (
            layer
            for layer in layout.locked_layers
            if isinstance(layer, ShapeLayer)
            and layer.z_index < slot_z
            and _covers(layer, geometry.area)
        ),
        key=lambda layer: layer.z_index,
        reverse=True,
    )
    if local_layers:
        return local_layers[0].color_token
    if content.background_color_token is not None:
        return content.background_color_token
    return layout.background.color_token if layout.background.kind == "color" else None


def _foreground_token(
    ir: BrandIR,
    slot: Slot,
    override: LayerOverride | None,
) -> str | None:
    if override is not None and override.color_token is not None:
        return override.color_token
    if slot.color_token is not None:
        return slot.color_token
    role = ir.roles.get(slot.role or "")
    return role.color if role is not None else None


def assess_carousel_candidate(
    ir: BrandIR,
    layout: LayoutSpec,
    content: ContentSpec,
    assets_dir: Path,
) -> CarouselCandidateAssessment:
    """Rejeita candidatos automáticos que não acomodam o conteúdo materializado."""
    issues = [
        f"{check.id}:{check.slot_id or '-'}"
        for check in run_static_checks(ir, layout, content, assets_dir)
        if check.status == "blocked"
        or (check.id in {"required-slot", "text-length"} and check.status == "warning")
    ]
    active_layout = materialize_content_layout(layout, content)
    geometries: list[tuple[Slot, LayerOverride | None, _TextGeometry]] = []
    for slot in active_layout.slots:
        value = content.values.get(slot.id)
        override = content.overrides.get(slot.id)
        if (
            slot.kind != "text"
            or not isinstance(value, TextValue)
            or not value.text.strip()
            or (override is not None and override.hidden)
        ):
            continue
        geometry = _measure_text(ir, slot, override, value.text)
        geometries.append((slot, override, geometry))
        if geometry.overflow:
            issues.append(f"text-overflow:{slot.id}")

        foreground_ref = _foreground_token(ir, slot, override)
        background_ref = _background_token(active_layout, content, geometry, slot)
        foreground = ir.colors.get(foreground_ref) if foreground_ref is not None else None
        background = ir.colors.get(background_ref) if background_ref is not None else None
        if foreground is not None and background is not None:
            threshold = _MIN_CONTRAST_LARGE if geometry.font_size_px >= 24 else _MIN_CONTRAST_NORMAL
            if wcag_contrast(foreground.value, background.value) < threshold:
                issues.append(f"contrast:{slot.id}")

    layout_allows_overlap = any(term in layout.id for term in _COLLISION_EXEMPT_LAYOUT_TERMS)
    if not layout_allows_overlap:
        for index, (slot, override, geometry) in enumerate(geometries):
            if (
                slot.id in _COLLISION_EXEMPT_IDS
                or _effective_opacity(slot, override) <= 0.2
                or _effective_fill_mode(slot, override) == "stroke"
            ):
                continue
            for other_slot, other_override, other_geometry in geometries[index + 1 :]:
                if (
                    other_slot.id in _COLLISION_EXEMPT_IDS
                    or _effective_opacity(other_slot, other_override) <= 0.2
                    or _effective_fill_mode(other_slot, other_override) == "stroke"
                ):
                    continue
                if _intersection_ratio(geometry.ink, other_geometry.ink) >= 0.12:
                    issues.append(f"text-collision:{slot.id}:{other_slot.id}")

    unique_issues = tuple(dict.fromkeys(issues))
    return CarouselCandidateAssessment(viable=not unique_issues, issues=unique_issues)
