"""Avaliações geométricas determinísticas para publicação de templates."""

from __future__ import annotations

import hashlib
import json
from itertools import combinations
from typing import Annotated, Literal

from pydantic import Field

from brand_runtime.ir.models import CamelModel
from brand_runtime.kit.models import LayoutSpec, NonBlankString
from brand_runtime.templates.models import TemplatePackage

Ratio = Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)]


class TemplateQualityFinding(CamelModel):
    """Resultado de um gate de publicação ligado a uma composição."""

    check: NonBlankString
    composition_id: NonBlankString
    status: Literal["pass", "fail"]
    detail_pt: NonBlankString


class TemplateQualityReport(CamelModel):
    """Relatório fechado usado pelo registry antes de expor uma família."""

    passed: bool
    findings: list[TemplateQualityFinding]
    structural_signatures: dict[NonBlankString, NonBlankString]
    pair_distances: dict[NonBlankString, Ratio]
    delegated_checks: dict[NonBlankString, Literal["guard", "renderer"]]


def _normalized_area(layout: LayoutSpec, area: tuple[int, int, int, int]) -> tuple[float, ...]:
    width = layout.canvas.width_px
    height = layout.canvas.height_px
    x, y, item_width, item_height = area
    return tuple(
        round(value, 4)
        for value in (x / width, y / height, item_width / width, item_height / height)
    )


def structural_signature(layout: LayoutSpec) -> str:
    """Resume esqueleto e hierarquia sem depender de cor, fonte ou texto demonstrativo."""
    payload = {
        "profile": layout.profile,
        "slots": sorted(
            (
                slot.id,
                slot.kind,
                slot.role,
                _normalized_area(layout, slot.area),
                slot.text_align,
            )
            for slot in layout.slots
        ),
        "layers": sorted(
            (layer.kind, getattr(layer, "shape", None), _normalized_area(layout, layer.area))
            for layer in layout.locked_layers
        ),
        "groups": sorted(
            (
                group.kind,
                _normalized_area(layout, group.area),
                len(group.children),
                group.direction,
                group.columns,
            )
            for group in (layout.scene_graph.groups if layout.scene_graph else [])
        ),
    }
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _structural_distance(left: LayoutSpec, right: LayoutSpec) -> float:
    left_slots = {slot.id: _normalized_area(left, slot.area) for slot in left.slots}
    right_slots = {slot.id: _normalized_area(right, slot.area) for slot in right.slots}
    shared = sorted(set(left_slots) & set(right_slots))
    geometry = 1.0
    if shared:
        geometry = sum(
            sum(abs(a - b) for a, b in zip(left_slots[item], right_slots[item], strict=True)) / 4
            for item in shared
        ) / len(shared)

    left_groups = {group.kind for group in (left.scene_graph.groups if left.scene_graph else [])}
    right_groups = {group.kind for group in (right.scene_graph.groups if right.scene_graph else [])}
    union = left_groups | right_groups
    group_distance = 1 - len(left_groups & right_groups) / len(union) if union else 0

    left_layers = {(layer.kind, getattr(layer, "shape", None)) for layer in left.locked_layers}
    right_layers = {(layer.kind, getattr(layer, "shape", None)) for layer in right.locked_layers}
    layer_union = left_layers | right_layers
    layer_distance = 1 - len(left_layers & right_layers) / len(layer_union) if layer_union else 0
    return round(min(1.0, geometry * 1.8 + group_distance * 0.45 + layer_distance * 0.15), 4)


def _negative_space(layout: LayoutSpec) -> float:
    columns, rows = 54, 68
    occupied: set[tuple[int, int]] = set()
    for slot in layout.slots:
        x, y, width, height = _normalized_area(layout, slot.area)
        left = max(0, int(x * columns))
        top = max(0, int(y * rows))
        right = min(columns, max(left + 1, int((x + width) * columns + 0.999)))
        bottom = min(rows, max(top + 1, int((y + height) * rows + 0.999)))
        occupied.update(
            (column, row) for column in range(left, right) for row in range(top, bottom)
        )
    return round(1 - len(occupied) / (columns * rows), 4)


def evaluate_template_package(package: TemplatePackage) -> TemplateQualityReport:
    """Executa gates portáteis antes das provas medidas do renderer."""
    findings: list[TemplateQualityFinding] = []
    evaluations = {evaluation.kind: evaluation for evaluation in package.evaluations}
    delegated_checks = {
        evaluation.kind: evaluation.stage
        for evaluation in package.evaluations
        if evaluation.stage != "portable"
    }
    signatures = {
        composition.id: structural_signature(composition.layout)
        for composition in package.compositions
    }

    for composition in package.compositions:
        layout = composition.layout
        safe = layout.canvas.safe_area_px
        width = layout.canvas.width_px
        height = layout.canvas.height_px
        elements = {
            **{slot.id: slot for slot in layout.slots},
            **{layer.id: layer for layer in layout.locked_layers},
        }
        safe_critical = all(
            safe <= elements[item].area[0]
            and safe <= elements[item].area[1]
            and elements[item].area[0] + elements[item].area[2] <= width - safe
            and elements[item].area[1] + elements[item].area[3] <= height - safe
            for item in composition.critical_nodes
        )
        findings.append(
            TemplateQualityFinding(
                check="safe-area",
                composition_id=composition.id,
                status="pass" if safe_critical else "fail",
                detail_pt=(
                    "Nós críticos permanecem na área segura."
                    if safe_critical
                    else "Um nó crítico ultrapassa a área segura."
                ),
            )
        )

        sizes = [
            slot.font_size_px for slot in layout.slots if slot.kind == "text" and slot.font_size_px
        ]
        hierarchy = max(sizes) / min(sizes) if sizes else 1
        hierarchy_minimum = evaluations["type-hierarchy"].minimum or 2.5
        findings.append(
            TemplateQualityFinding(
                check="type-hierarchy",
                composition_id=composition.id,
                status="pass" if hierarchy >= hierarchy_minimum else "fail",
                detail_pt=f"Razão tipográfica medida: {hierarchy:.2f}.",
            )
        )

        negative_space = _negative_space(layout)
        negative_rule = evaluations["negative-space"]
        negative_minimum = negative_rule.minimum if negative_rule.minimum is not None else 0.12
        negative_maximum = negative_rule.maximum if negative_rule.maximum is not None else 0.72
        findings.append(
            TemplateQualityFinding(
                check="negative-space",
                composition_id=composition.id,
                status=(
                    "pass" if negative_minimum <= negative_space <= negative_maximum else "fail"
                ),
                detail_pt=f"Espaço negativo estimado: {negative_space:.2%}.",
            )
        )

    pair_distances: dict[str, float] = {}
    distance_minimum = evaluations["structural-distance"].minimum or 0.35
    for left, right in combinations(package.compositions, 2):
        pair = f"{left.id}::{right.id}"
        distance = _structural_distance(left.layout, right.layout)
        pair_distances[pair] = distance
        findings.append(
            TemplateQualityFinding(
                check="structural-distance",
                composition_id=pair,
                status="pass" if distance >= distance_minimum else "fail",
                detail_pt=f"Distância estrutural medida: {distance:.2f}.",
            )
        )

    return TemplateQualityReport(
        passed=all(finding.status == "pass" for finding in findings),
        findings=findings,
        structural_signatures=signatures,
        pair_distances=pair_distances,
        delegated_checks=delegated_checks,
    )
