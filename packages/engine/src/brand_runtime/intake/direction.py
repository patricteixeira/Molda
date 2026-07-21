"""Derivação determinística de uma hipótese de direção de arte."""

from __future__ import annotations

import re
import unicodedata

from brand_runtime.ir.models import (
    BrandIdentity,
    CreativeDirection,
    ExpressionAxis,
)

_AXES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "energy": (
        (
            "calma",
            "serena",
            "sereno",
            "silenciosa",
            "silencioso",
            "contemplativa",
            "contemplativo",
            "sutil",
            "controlada",
            "controlado",
            "quiet",
            "silent",
            "calm",
            "restrained",
        ),
        (
            "energica",
            "energico",
            "dinamica",
            "dinamico",
            "provocadora",
            "provocador",
            "ousada",
            "ousado",
            "vibrante",
            "movimento",
            "bold",
            "dynamic",
            "movement",
            "monumental",
            "dominant",
        ),
    ),
    "geometry": (
        (
            "organica",
            "organico",
            "fluida",
            "fluido",
            "natural",
            "humana",
            "humano",
            "imperfeita",
            "imperfeito",
            "organic",
            "fluid",
        ),
        (
            "geometrica",
            "geometrico",
            "precisa",
            "preciso",
            "sistematica",
            "sistematico",
            "modular",
            "arquitetonica",
            "arquitetonico",
            "rigida",
            "rigido",
            "escultural",
            "geometric",
            "modular",
            "architectural",
            "architecture",
            "rigid",
            "structure",
            "sculptural",
        ),
    ),
    "density": (
        (
            "essencial",
            "minimal",
            "respiro",
            "simples",
            "clara",
            "claro",
            "poucos elementos",
            "sparse",
            "focused",
            "few elements",
            "generous empty space",
            "restraint",
        ),
        (
            "camadas",
            "rica",
            "rico",
            "imersiva",
            "abundante",
            "textura",
            "layered",
            "immersive",
        ),
    ),
    "formality": (
        (
            "proxima",
            "proximo",
            "acolhedora",
            "acolhedor",
            "artesanal",
            "pessoal",
            "acessivel",
            "human",
            "warm",
        ),
        (
            "institucional",
            "tecnica",
            "tecnico",
            "rigorosa",
            "rigoroso",
            "confiavel",
            "especialista",
            "sofisticado",
            "professional",
            "rigorous",
            "sophisticated",
            "intellectual",
            "couture",
        ),
    ),
    "materiality": (
        (
            "tatil",
            "material",
            "papel",
            "feito a mao",
            "artesanal",
            "sensorial",
            "craft",
            "tactile",
            "material-first",
            "fabric",
            "metal",
        ),
        (
            "digital",
            "tecnologica",
            "futurista",
            "interface",
            "algoritmica",
            "technology",
            "digital",
        ),
    ),
    "contrast": (
        (
            "delicada",
            "delicado",
            "discreta",
            "discreto",
            "continua",
            "continuo",
            "harmoniosa",
            "harmonioso",
            "baixo contraste",
            "subtle",
            "gentle",
        ),
        (
            "contraste",
            "impacto",
            "ruptura",
            "radical",
            "emphatic",
            "contrast",
            "tension",
            "unexpected proportion",
            "impossible proportion",
            "visually dominant",
        ),
    ),
}


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_marks).casefold()


def _polarized_hits(
    text: str,
    negative: tuple[str, ...],
    positive: tuple[str, ...],
) -> tuple[list[str], list[str]]:
    """Prefere a expressão mais específica quando dois marcadores se sobrepõem."""
    matches: list[tuple[int, int, str, str]] = []
    for polarity, terms in (("negative", negative), ("positive", positive)):
        for term in terms:
            pattern = rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"
            matches.extend(
                (match.start(), match.end(), polarity, term) for match in re.finditer(pattern, text)
            )
    selected: list[tuple[int, int, str, str]] = []
    for candidate in sorted(matches, key=lambda item: (-(item[1] - item[0]), item[0])):
        if any(candidate[0] < other[1] and other[0] < candidate[1] for other in selected):
            continue
        selected.append(candidate)
    selected.sort(key=lambda item: item[0])
    return (
        [term for _, _, polarity, term in selected if polarity == "negative"],
        [term for _, _, polarity, term in selected if polarity == "positive"],
    )


def _axis(
    affirmed_text: str,
    avoided_text: str,
    negative: tuple[str, ...],
    positive: tuple[str, ...],
) -> ExpressionAxis:
    """Lê declarações afirmadas e inverte explicitamente o campo de restrições."""
    affirmed_negative, affirmed_positive = _polarized_hits(affirmed_text, negative, positive)
    avoided_negative, avoided_positive = _polarized_hits(avoided_text, negative, positive)
    negative_hits = [*affirmed_negative, *avoided_positive]
    positive_hits = [*affirmed_positive, *avoided_negative]
    total = len(negative_hits) + len(positive_hits)
    value = 0.0 if total == 0 else (len(positive_hits) - len(negative_hits)) / total
    return ExpressionAxis(
        value=value,
        confidence=min(1.0, total / 4),
        evidence_terms=[
            *affirmed_negative,
            *affirmed_positive,
            *(f"não {term}" for term in avoided_negative),
            *(f"não {term}" for term in avoided_positive),
        ],
    )


def derive_creative_direction(identity: BrandIdentity) -> CreativeDirection | None:
    """Converte linguagem confirmada em parâmetros; sinal fraco não gera palpite."""
    affirmed_text = _normalized(" ".join((identity.essence, identity.personality, identity.voice)))
    avoided_text = _normalized(identity.avoid)
    axes = {
        name: _axis(affirmed_text, avoided_text, negative, positive)
        for name, (negative, positive) in _AXES.items()
    }
    evidence_count = sum(len(axis.evidence_terms) for axis in axes.values())
    if evidence_count < 2:
        return None

    energy = axes["energy"].value
    geometry = axes["geometry"].value
    density = axes["density"].value
    formality = axes["formality"].value
    materiality = axes["materiality"].value
    contrast = axes["contrast"].value

    if density > 0.35:
        composition = "layered"
    elif energy > 0.35 or contrast > 0.45:
        composition = "expansive"
    elif geometry > 0.4 and formality > 0.15:
        composition = "modular"
    elif energy < -0.3 and density <= 0:
        composition = "contemplative"
    else:
        composition = "asymmetric"

    if materiality < -0.25:
        surface = "paper-grain"
    elif geometry > 0.4 and formality > 0.15:
        surface = "technical-grid"
    elif energy > 0.35:
        surface = "linear-rhythm"
    elif geometry < -0.3:
        surface = "concentric-rings"
    elif density > 0.2:
        surface = "point-field"
    else:
        surface = "none"

    scale_contrast = max(0.15, min(1.0, 0.5 + energy * 0.25 + contrast * 0.25))
    negative_space = max(0.1, min(0.9, 0.5 - density * 0.3 - energy * 0.1))
    bleed = max(0.0, min(1.0, 0.3 + energy * 0.35 + contrast * 0.2))
    surface_density = (
        0.0
        if surface == "none"
        else max(0.12, min(0.82, 0.38 + density * 0.25 + abs(geometry) * 0.12))
    )

    rationale: list[str] = []
    strongest = sorted(
        axes.items(),
        key=lambda item: (item[1].confidence, abs(item[1].value)),
        reverse=True,
    )
    labels = {
        "energy": ("contida", "expansiva"),
        "geometry": ("orgânica", "geométrica"),
        "density": ("essencial", "estratificada"),
        "formality": ("humana", "institucional"),
        "materiality": ("tátil", "digital"),
        "contrast": ("sutil", "enfática"),
    }
    for name, axis in strongest[:3]:
        if axis.confidence == 0:
            continue
        label = labels[name][1 if axis.value >= 0 else 0]
        terms = ", ".join(f"“{term}”" for term in axis.evidence_terms[:3])
        rationale.append(f"A identidade se declara {label}; sinais confirmados: {terms}.")
    rationale.append(
        {
            "contemplative": "A estrutura preserva silêncio, respiro e uma hierarquia deliberada.",
            "asymmetric": "A estrutura usa assimetria controlada para equilibrar autoria e legibilidade.",
            "modular": "A estrutura parte de módulos precisos e relações repetíveis.",
            "expansive": "A estrutura usa contraste de escala e sangria como parte da expressão.",
            "layered": "A estrutura trabalha camadas, profundidade e ritmos simultâneos.",
        }[composition]
    )

    return CreativeDirection(
        **axes,
        composition=composition,
        surface=surface,
        scale_contrast=scale_contrast,
        negative_space=negative_space,
        bleed=bleed,
        surface_density=surface_density,
        rationale_pt=rationale,
    )
