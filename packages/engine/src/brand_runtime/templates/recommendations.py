"""Priorização explicável do catálogo pela linguagem confirmada da marca."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from brand_runtime.ir.models import BrandIR, CreativeDirection
from brand_runtime.kit.models import LayoutSpec


@dataclass(frozen=True)
class FamilyProfile:
    """Assinatura estrutural publicada de uma família do catálogo."""

    axes: tuple[float, float, float, float, float, float]
    compositions: frozenset[str]
    surfaces: frozenset[str]
    promise_pt: str
    required_axes: frozenset[int] = frozenset()


@dataclass(frozen=True)
class TemplateRecommendation:
    """Recomendação serializável sem alterar o contrato imutável do layout."""

    layout_id: str
    rank: int
    reason_pt: str
    basis: Literal["brand", "exploratory"]


_FAMILY_PROFILES: dict[str, FamilyProfile] = {
    "typographic-editorial": FamilyProfile(
        (0.10, 0.10, -0.20, 0.35, -0.10, 0.35),
        frozenset({"asymmetric", "contemplative", "expansive"}),
        frozenset({"none", "paper-grain"}),
        "Cria hierarquia forte só com tipografia e respiro.",
    ),
    "typographic-brutalist": FamilyProfile(
        (0.90, 0.50, 0.50, 0.10, 0.20, 1.00),
        frozenset({"expansive", "layered"}),
        frozenset({"linear-rhythm", "technical-grid"}),
        "Dá impacto direto à mensagem com escala e contraste assumidos.",
        frozenset({0, 5}),
    ),
    "swiss-system": FamilyProfile(
        (-0.10, 0.90, -0.50, 0.80, 0.20, 0.35),
        frozenset({"modular", "contemplative"}),
        frozenset({"technical-grid", "none"}),
        "Organiza a informação com precisão, ritmo e bastante legibilidade.",
        frozenset({1, 3}),
    ),
    "geometric-modernism": FamilyProfile(
        (0.45, 0.95, 0.10, 0.45, 0.10, 0.65),
        frozenset({"modular", "expansive"}),
        frozenset({"technical-grid", "concentric-rings"}),
        "Transforma geometria e cor em sinais claros da identidade.",
        frozenset({1}),
    ),
    "kinetic-typography": FamilyProfile(
        (1.00, 0.30, 0.55, -0.20, 0.20, 0.90),
        frozenset({"expansive", "layered"}),
        frozenset({"linear-rhythm", "point-field"}),
        "Constrói sensação de movimento sem sacrificar a leitura.",
        frozenset({0, 5}),
    ),
    "constructivist-dynamics": FamilyProfile(
        (0.85, 0.85, 0.55, 0.20, -0.10, 1.00),
        frozenset({"expansive", "layered"}),
        frozenset({"linear-rhythm", "technical-grid"}),
        "Usa tensão, diagonais e blocos para tornar a mensagem enfática.",
        frozenset({0, 1, 5}),
    ),
    "fashion-editorial": FamilyProfile(
        (0.20, 0.10, -0.15, 0.85, -0.30, 0.45),
        frozenset({"asymmetric", "contemplative"}),
        frozenset({"paper-grain", "none"}),
        "Equilibra sofisticação, imagem e tipografia com ritmo editorial.",
        frozenset({3}),
    ),
    "minimal-luxury": FamilyProfile(
        (-0.55, 0.20, -0.90, 0.90, -0.35, 0.20),
        frozenset({"contemplative", "asymmetric"}),
        frozenset({"none", "paper-grain"}),
        "Preserva silêncio visual, proporção e uma presença mais refinada.",
        frozenset({2}),
    ),
    "editorial-collage": FamilyProfile(
        (0.35, -0.65, 0.90, -0.30, -1.00, 0.45),
        frozenset({"layered", "asymmetric"}),
        frozenset({"paper-grain", "point-field"}),
        "Combina camadas e materialidade para uma expressão mais humana.",
        frozenset({2}),
    ),
    "technical-diagram": FamilyProfile(
        (0.05, 1.00, 0.20, 1.00, 0.60, 0.40),
        frozenset({"modular", "layered"}),
        frozenset({"technical-grid", "point-field"}),
        "Explica sistemas complexos com estrutura, precisão e rastreabilidade.",
        frozenset({1, 3}),
    ),
    "product-campaign": FamilyProfile(
        (0.45, 0.40, 0.10, 0.50, 0.10, 0.55),
        frozenset({"asymmetric", "expansive", "modular"}),
        frozenset({"none", "linear-rhythm"}),
        "Abre espaço para produto, benefício e chamada sem perder identidade.",
    ),
    "data-evidence": FamilyProfile(
        (0.10, 0.85, 0.25, 0.95, 0.65, 0.35),
        frozenset({"modular", "layered"}),
        frozenset({"technical-grid", "point-field"}),
        "Transforma números e evidências em uma narrativa visual confiável.",
        frozenset({1, 3}),
    ),
    "device-mockup": FamilyProfile(
        (0.25, 0.75, -0.05, 0.65, 1.00, 0.30),
        frozenset({"modular", "asymmetric"}),
        frozenset({"technical-grid", "none"}),
        "Mostra interfaces e experiências digitais dentro do contexto da marca.",
        frozenset({1, 4}),
    ),
}


def family_profiles() -> dict[str, FamilyProfile]:
    """Retorna um snapshot raso das assinaturas usadas pela recomendação."""
    return dict(_FAMILY_PROFILES)


_AXIS_LABELS = (
    ("contida", "expansiva"),
    ("orgânica", "geométrica"),
    ("essencial", "rica em camadas"),
    ("próxima", "institucional"),
    ("tátil", "digital"),
    ("sutil", "enfática"),
)

_CONTRADICTION_AXES = (0, 1, 4, 5)
_CONTRADICTION_THRESHOLD = 0.55
_CONTRADICTION_PENALTY = 0.25
_MISSING_REQUIRED_AXIS_PENALTY = 0.25
_CONTRADICTED_REQUIRED_AXIS_PENALTY = 0.24

_SPECIALIZED_REQUIRED_AXES: dict[str, frozenset[int]] = {
    "typographic-brutalist": frozenset({5}),
    "swiss-system": frozenset({1, 3}),
    "geometric-modernism": frozenset({1}),
    "kinetic-typography": frozenset({0, 5}),
    "constructivist-dynamics": frozenset({1, 5}),
    "technical-diagram": frozenset({1, 3}),
    "data-evidence": frozenset({1, 3}),
    "device-mockup": frozenset({4}),
}


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


def _score(direction: CreativeDirection, profile: FamilyProfile) -> float:
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
    # Energia, geometria, materialidade e contraste definem a voz visual mais
    # imediatamente que densidade e formalidade, que o conteúdo pode modular.
    # Uma família que contradiz frontalmente qualquer desses sinais não deve
    # vencer só porque compartilha a palavra estrutural "camadas".
    contradiction_penalty = sum(
        _CONTRADICTION_PENALTY
        for index in _CONTRADICTION_AXES
        if values[index] * profile.axes[index] < 0
        and abs(values[index]) >= _CONTRADICTION_THRESHOLD
        and abs(profile.axes[index]) >= _CONTRADICTION_THRESHOLD
    )
    missing_signal_penalty = sum(
        _MISSING_REQUIRED_AXIS_PENALTY for index in profile.required_axes if confidences[index] <= 0
    )
    contradicted_required_signal_penalty = sum(
        _CONTRADICTED_REQUIRED_AXIS_PENALTY
        for index in profile.required_axes
        if confidences[index] > 0
        and values[index] * profile.axes[index] < 0
        and abs(values[index]) >= _CONTRADICTION_THRESHOLD
        and abs(profile.axes[index]) >= _CONTRADICTION_THRESHOLD
    )
    return (
        axis_score
        + composition_bonus
        + surface_bonus
        - contradiction_penalty
        - missing_signal_penalty
        - contradicted_required_signal_penalty
    )


def _reason(direction: CreativeDirection, profile: FamilyProfile) -> str:
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


def _specialization_is_supported(direction: CreativeDirection, package_id: str) -> bool:
    """Evita recomendar uma linguagem especializada sem os sinais que a justificam."""
    required = _SPECIALIZED_REQUIRED_AXES.get(package_id)
    if required is None:
        return True
    values = _axis_values(direction)
    confidences = _axis_confidences(direction)
    profile = _FAMILY_PROFILES[package_id]
    return all(
        confidences[index] > 0
        and not (
            values[index] * profile.axes[index] < 0
            and abs(values[index]) >= _CONTRADICTION_THRESHOLD
            and abs(profile.axes[index]) >= _CONTRADICTION_THRESHOLD
        )
        for index in required
    )


def _family_order(layouts: list[LayoutSpec], direction: CreativeDirection | None) -> list[str]:
    present = list(dict.fromkeys(_package_id(layout) for layout in layouts))
    if direction is None:
        return present
    order = {package_id: index for index, package_id in enumerate(present)}
    return sorted(
        present,
        key=lambda package_id: (
            not _specialization_is_supported(direction, package_id),
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
