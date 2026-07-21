"""Priorização explicável do catálogo pela linguagem confirmada da marca."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from brand_runtime.ir.models import BrandIR, CreativeDirection
from brand_runtime.kit.models import LayoutSpec


@dataclass(frozen=True)
class _FamilyProfile:
    axes: tuple[float, float, float, float, float, float]
    compositions: frozenset[str]
    surfaces: frozenset[str]
    promise_pt: str


@dataclass(frozen=True)
class TemplateRecommendation:
    """Recomendação serializável sem alterar o contrato imutável do layout."""

    layout_id: str
    rank: int
    reason_pt: str
    basis: Literal["brand", "exploratory"]


_FAMILY_PROFILES: dict[str, _FamilyProfile] = {
    "typographic-editorial": _FamilyProfile(
        (0.10, 0.10, -0.20, 0.35, -0.10, 0.35),
        frozenset({"asymmetric", "contemplative", "expansive"}),
        frozenset({"none", "paper-grain"}),
        "Cria hierarquia forte só com tipografia e respiro.",
    ),
    "typographic-brutalist": _FamilyProfile(
        (0.90, 0.50, 0.50, 0.10, 0.20, 1.00),
        frozenset({"expansive", "layered"}),
        frozenset({"linear-rhythm", "technical-grid"}),
        "Dá impacto direto à mensagem com escala e contraste assumidos.",
    ),
    "swiss-system": _FamilyProfile(
        (-0.10, 0.90, -0.50, 0.80, 0.20, 0.35),
        frozenset({"modular", "contemplative"}),
        frozenset({"technical-grid", "none"}),
        "Organiza a informação com precisão, ritmo e bastante legibilidade.",
    ),
    "geometric-modernism": _FamilyProfile(
        (0.45, 0.95, 0.10, 0.45, 0.10, 0.65),
        frozenset({"modular", "expansive"}),
        frozenset({"technical-grid", "concentric-rings"}),
        "Transforma geometria e cor em sinais claros da identidade.",
    ),
    "kinetic-typography": _FamilyProfile(
        (1.00, 0.30, 0.55, -0.20, 0.20, 0.90),
        frozenset({"expansive", "layered"}),
        frozenset({"linear-rhythm", "point-field"}),
        "Constrói sensação de movimento sem sacrificar a leitura.",
    ),
    "constructivist-dynamics": _FamilyProfile(
        (0.85, 0.85, 0.55, 0.20, -0.10, 1.00),
        frozenset({"expansive", "layered"}),
        frozenset({"linear-rhythm", "technical-grid"}),
        "Usa tensão, diagonais e blocos para tornar a mensagem enfática.",
    ),
    "fashion-editorial": _FamilyProfile(
        (0.20, 0.10, -0.15, 0.85, -0.30, 0.55),
        frozenset({"asymmetric", "contemplative"}),
        frozenset({"paper-grain", "none"}),
        "Equilibra sofisticação, imagem e tipografia com ritmo editorial.",
    ),
    "minimal-luxury": _FamilyProfile(
        (-0.55, 0.20, -0.90, 0.90, -0.35, 0.20),
        frozenset({"contemplative", "asymmetric"}),
        frozenset({"none", "paper-grain"}),
        "Preserva silêncio visual, proporção e uma presença mais refinada.",
    ),
    "editorial-collage": _FamilyProfile(
        (0.65, -0.65, 0.90, -0.30, -1.00, 0.80),
        frozenset({"layered", "asymmetric"}),
        frozenset({"paper-grain", "point-field"}),
        "Combina camadas e materialidade para uma expressão mais humana.",
    ),
    "technical-diagram": _FamilyProfile(
        (0.05, 1.00, 0.20, 1.00, 0.60, 0.40),
        frozenset({"modular", "layered"}),
        frozenset({"technical-grid", "point-field"}),
        "Explica sistemas complexos com estrutura, precisão e rastreabilidade.",
    ),
    "product-campaign": _FamilyProfile(
        (0.45, 0.40, 0.10, 0.50, 0.10, 0.55),
        frozenset({"asymmetric", "expansive", "modular"}),
        frozenset({"none", "linear-rhythm"}),
        "Abre espaço para produto, benefício e chamada sem perder identidade.",
    ),
    "data-evidence": _FamilyProfile(
        (0.10, 0.85, 0.25, 0.95, 0.65, 0.35),
        frozenset({"modular", "layered"}),
        frozenset({"technical-grid", "point-field"}),
        "Transforma números e evidências em uma narrativa visual confiável.",
    ),
    "device-mockup": _FamilyProfile(
        (0.25, 0.75, -0.05, 0.65, 1.00, 0.30),
        frozenset({"modular", "asymmetric"}),
        frozenset({"technical-grid", "none"}),
        "Mostra interfaces e experiências digitais dentro do contexto da marca.",
    ),
}

_AXIS_LABELS = (
    ("contida", "expansiva"),
    ("orgânica", "geométrica"),
    ("essencial", "rica em camadas"),
    ("próxima", "institucional"),
    ("tátil", "digital"),
    ("sutil", "enfática"),
)


def _package_id(layout: LayoutSpec) -> str:
    return layout.template_ref.package_id if layout.template_ref is not None else "essential"


def _axis_values(direction: CreativeDirection) -> tuple[float, float, float, float, float, float]:
    return (
        direction.energy.value,
        direction.geometry.value,
        direction.density.value,
        direction.formality.value,
        direction.materiality.value,
        direction.contrast.value,
    )


def _axis_confidences(
    direction: CreativeDirection,
) -> tuple[float, float, float, float, float, float]:
    return (
        direction.energy.confidence,
        direction.geometry.confidence,
        direction.density.confidence,
        direction.formality.confidence,
        direction.materiality.confidence,
        direction.contrast.confidence,
    )


def _score(direction: CreativeDirection, profile: _FamilyProfile) -> float:
    values = _axis_values(direction)
    confidences = _axis_confidences(direction)
    evidence_weight = sum(confidences)
    axis_score = (
        sum(
            (1.0 - abs(value - target) / 2.0) * confidence
            for value, target, confidence in zip(values, profile.axes, confidences, strict=True)
        )
        / evidence_weight
        if evidence_weight > 0
        else 0.5
    )
    composition_bonus = 0.22 if direction.composition in profile.compositions else 0.0
    surface_bonus = 0.10 if direction.surface in profile.surfaces else 0.0
    return axis_score + composition_bonus + surface_bonus


def _reason(direction: CreativeDirection, profile: _FamilyProfile) -> str:
    values = _axis_values(direction)
    confidences = _axis_confidences(direction)
    strongest = sorted(
        range(len(values)),
        key=lambda index: (confidences[index], abs(values[index])),
        reverse=True,
    )
    descriptors = [
        _AXIS_LABELS[index][1 if values[index] >= 0 else 0]
        for index in strongest
        if confidences[index] > 0
    ][:2]
    if not descriptors:
        return profile.promise_pt
    return (
        f"{profile.promise_pt} A leitura do manual aponta para uma expressão "
        f"{' e '.join(descriptors)}."
    )


def _family_order(layouts: list[LayoutSpec], direction: CreativeDirection | None) -> list[str]:
    present = list(dict.fromkeys(_package_id(layout) for layout in layouts))
    if direction is None:
        return present
    order = {package_id: index for index, package_id in enumerate(present)}
    return sorted(
        present,
        key=lambda package_id: (
            -_score(direction, _FAMILY_PROFILES[package_id])
            if package_id in _FAMILY_PROFILES
            else 0.0,
            order[package_id],
        ),
    )


def recommend_template_layouts(
    ir: BrandIR,
    layouts: Iterable[LayoutSpec],
    *,
    limit: int = 8,
) -> list[TemplateRecommendation]:
    """Escolhe poucas composições diversas e explica o vínculo com a marca.

    A seleção prioriza quatro famílias e oferece a superfície principal e sua
    alternativa quando ambas existem. Sem direção confirmada, entrega uma
    amostra editorial diversa e a identifica honestamente como exploratória.
    """
    available = list(layouts)
    if limit <= 0 or not available:
        return []

    direction = ir.creative_direction
    basis: Literal["brand", "exploratory"] = "brand" if direction is not None else "exploratory"
    family_order = _family_order(available, direction)
    selected: list[LayoutSpec] = []

    for package_id in family_order[: max(1, min(4, limit))]:
        family = [layout for layout in available if _package_id(layout) == package_id]
        bases = [layout for layout in family if not layout.id.endswith("-alternative")]
        principal = bases[0] if bases else family[0]
        selected.append(principal)
        alternate = next(
            (layout for layout in family if layout.id == f"{principal.id}-alternative"),
            None,
        )
        if alternate is not None and len(selected) < limit:
            selected.append(alternate)
        if len(selected) >= limit:
            break

    if len(selected) < limit:
        selected_ids = {layout.id for layout in selected}
        for package_id in family_order:
            for layout in available:
                if _package_id(layout) != package_id or layout.id in selected_ids:
                    continue
                selected.append(layout)
                selected_ids.add(layout.id)
                if len(selected) >= limit:
                    break
            if len(selected) >= limit:
                break

    recommendations: list[TemplateRecommendation] = []
    for rank, layout in enumerate(selected[:limit], start=1):
        profile = _FAMILY_PROFILES.get(_package_id(layout))
        reason = (
            _reason(direction, profile)
            if direction is not None and profile is not None
            else "Ponto de partida variado para descobrir a expressão que melhor representa a marca."
        )
        recommendations.append(
            TemplateRecommendation(layout_id=layout.id, rank=rank, reason_pt=reason, basis=basis)
        )
    return recommendations
