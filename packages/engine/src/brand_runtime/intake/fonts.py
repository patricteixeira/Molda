"""Introspecção de arquivos de fonte (TTF/OTF) com fontTools."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from fontTools.ttLib import TTFont

from brand_runtime.ir.models import CamelModel, FontAxis


class FontInfo(CamelModel):
    """Fonte identificada: família legível, peso numérico e estilo."""

    family: str
    weight: int = 400
    style: Literal["normal", "italic"] = "normal"


DEFAULT_COVERAGE_PROFILE = "pt-BR-ui-v1"
_PT_BR_UI_CHARACTERS = (
    "".join(chr(codepoint) for codepoint in range(0x20, 0x7F))
    + "\u00a0ªº°ÁÀÂÃÉÊÍÓÔÕÚÜÇáàâãéêíóôõúüç“”‘’–—…•€"
)
_COVERAGE_PROFILES: dict[str, frozenset[int]] = {
    DEFAULT_COVERAGE_PROFILE: frozenset(ord(character) for character in _PT_BR_UI_CHARACTERS),
}


_NAME_ID_FAMILY = 1
_NAME_ID_SUBFAMILY = 2
_NAME_ID_TYPOGRAPHIC_FAMILY = 16
_FS_SELECTION_ITALIC = 0b1  # bit 0 da OS/2.fsSelection
_FAMILY_STYLE_SUFFIX = re.compile(
    r"\s+(?:thin|extra\s*light|light|book|regular|medium|semi\s*bold|demi\s*bold|"
    r"bold|extra\s*bold|black|heavy)(?:\s+(?:italic|oblique))?$",
    re.IGNORECASE,
)


def _normalized_family(value: str) -> str:
    """Remove do nome de família um peso que já está representado em OS/2."""
    normalized = re.sub(r"\s+", " ", value).strip()
    stripped = _FAMILY_STYLE_SUFFIX.sub("", normalized).strip()
    return stripped or normalized


def font_info_from_ttfont(font: TTFont, *, source: str = "fonte") -> FontInfo:
    """Lê família, peso e estilo de uma instância ``TTFont`` já validada."""
    name_table = font["name"]
    family = name_table.getDebugName(_NAME_ID_TYPOGRAPHIC_FAMILY) or name_table.getDebugName(
        _NAME_ID_FAMILY
    )
    if not family:
        msg = f"Arquivo de fonte sem nome de família na tabela name: {source}"
        raise ValueError(msg)
    os2 = font["OS/2"]
    subfamily = name_table.getDebugName(_NAME_ID_SUBFAMILY) or ""
    italic = bool(os2.fsSelection & _FS_SELECTION_ITALIC) or any(
        token in subfamily.casefold() for token in ("italic", "oblique")
    )
    return FontInfo(
        family=_normalized_family(family),
        weight=os2.usWeightClass,
        style="italic" if italic else "normal",
    )


def required_codepoints(coverage_profile: str = DEFAULT_COVERAGE_PROFILE) -> frozenset[int]:
    """Retorna o conjunto versionado de caracteres exigidos por um perfil."""
    try:
        return _COVERAGE_PROFILES[coverage_profile]
    except KeyError as exc:
        raise ValueError(f"Perfil de cobertura de fonte desconhecido: {coverage_profile}") from exc


def missing_codepoints(font: TTFont, required: Iterable[int]) -> list[int]:
    """Lista deterministicamente os codepoints exigidos que não existem no cmap."""
    cmap = font.getBestCmap() or {}
    return sorted(frozenset(required).difference(cmap))


def missing_codepoints_from_ttfont(
    font: TTFont,
    *,
    coverage_profile: str = DEFAULT_COVERAGE_PROFILE,
    required: Iterable[int] | None = None,
) -> list[int]:
    """Lista deterministicamente os caracteres exigidos que não existem no cmap."""
    expected = required if required is not None else required_codepoints(coverage_profile)
    return missing_codepoints(font, expected)


def font_axes_from_ttfont(font: TTFont) -> list[FontAxis]:
    """Extrai intervalos ``fvar`` em ordem estável; fontes estáticas retornam vazio."""
    if "fvar" not in font:
        return []
    return sorted(
        (
            FontAxis(
                tag=str(axis.axisTag),
                minimum=float(axis.minValue),
                default=float(axis.defaultValue),
                maximum=float(axis.maxValue),
            )
            for axis in font["fvar"].axes
        ),
        key=lambda axis: axis.tag,
    )


def inspect_font_capabilities(
    font_path: Path,
    *,
    coverage_profile: str = DEFAULT_COVERAGE_PROFILE,
) -> tuple[list[FontAxis], list[int]]:
    """Lê eixos variáveis e lacunas de cobertura numa única abertura validada."""
    with TTFont(font_path) as font:
        return (
            font_axes_from_ttfont(font),
            missing_codepoints_from_ttfont(font, coverage_profile=coverage_profile),
        )


def introspect_font(font_path: Path) -> FontInfo:
    """Lê família, peso e estilo diretamente das tabelas de um arquivo de fonte.

    Regras: família = nameID 16 se existir, senão nameID 1; peso =
    ``OS/2.usWeightClass``; estilo itálico se o bit 0 de ``OS/2.fsSelection``
    estiver ligado ou o nameID 2 (subfamília) contiver "Italic".
    """
    with TTFont(font_path) as font:
        return font_info_from_ttfont(font, source=str(font_path))
