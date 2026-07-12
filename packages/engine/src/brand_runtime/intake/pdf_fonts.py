"""Extração e parsing de nomes de fonte de PDFs de diretrizes (PyMuPDF)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import pymupdf

from brand_runtime.intake.base import Candidate
from brand_runtime.ir.models import CamelModel, Evidence

_CONFIDENCE = 0.8

_SUBSET_PREFIX = re.compile(r"^[A-Z]{6}\+")

_WEIGHT_TOKENS: dict[str, int] = {
    "thin": 100,
    "extralight": 200,
    "light": 300,
    "regular": 400,
    "book": 400,
    "medium": 500,
    "semibold": 600,
    "demibold": 600,
    "bold": 700,
    "extrabold": 800,
    "black": 900,
    "heavy": 900,
}
_STYLE_TOKENS = ("italic", "oblique")
# Match mais longo primeiro: "semibold" antes de "bold", "extralight" antes de "light".
_ALL_TOKENS = sorted([*_WEIGHT_TOKENS, *_STYLE_TOKENS], key=len, reverse=True)


class FontInfo(CamelModel):
    """Fonte identificada: família legível, peso numérico e estilo."""

    family: str
    weight: int = 400
    style: Literal["normal", "italic"] = "normal"


def _consume_tokens(text: str) -> tuple[int | None, bool, bool]:
    """Consome tokens concatenados (ex.: "SemiBoldItalic"), case-insensitive.

    Retorna (weight, italic, matched_any); o token de peso mais à direita vence.
    """
    lower = text.lower()
    weight: int | None = None
    italic = False
    matched_any = False
    pos = 0
    while pos < len(lower):
        for token in _ALL_TOKENS:
            if lower.startswith(token, pos):
                if token in _WEIGHT_TOKENS:
                    weight = _WEIGHT_TOKENS[token]
                else:
                    italic = True
                pos += len(token)
                matched_any = True
                break
        else:
            break  # trecho sem token conhecido: ignora o restante
    return weight, italic, matched_any


def _strip_trailing_tokens(name: str) -> tuple[str, int | None, bool]:
    """Remove tokens de peso/estilo colados ao fim do nome (ex.: "TimesBold")."""
    weight: int | None = None
    italic = False
    while True:
        lower = name.lower()
        for token in _ALL_TOKENS:
            if lower.endswith(token) and len(name) > len(token):
                if token in _WEIGHT_TOKENS:
                    if weight is None:  # o mais à direita vence
                        weight = _WEIGHT_TOKENS[token]
                else:
                    italic = True
                name = name[: len(name) - len(token)]
                break
        else:
            return name, weight, italic


def _split_camel_case(family: str) -> str:
    family = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", family)
    family = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", family)
    return family.strip()


def parse_ps_font_name(ps_name: str) -> FontInfo:
    """Interpreta um nome PostScript de fonte (ex.: "ABCDEF+Archivo-Bold").

    Regras: remove prefixo de subset; separa família de modificadores no último
    "-"; mapeia tokens de peso/estilo (podem vir concatenados); sem sufixo,
    procura os tokens no fim do nome da família; família final tem CamelCase
    separado por espaço.
    """
    name = _SUBSET_PREFIX.sub("", ps_name)
    family_part, sep, suffix = name.rpartition("-")
    if sep:
        weight, italic, matched_any = _consume_tokens(suffix)
        if not matched_any:
            family_part = f"{family_part}{suffix}"  # sufixo sem modificadores: parte da família
    else:
        family_part, weight, italic = _strip_trailing_tokens(name)
    family = _split_camel_case(family_part.replace("-", " "))
    return FontInfo(
        family=family,
        weight=weight if weight is not None else 400,
        style="italic" if italic else "normal",
    )


def extract_pdf_fonts(pdf_path: Path) -> list[Candidate]:
    """Extrai fontes usadas no texto de um PDF, com score por volume de caracteres.

    Usa os spans de ``page.get_text("dict")`` (campo ``span["font"]``);
    score = caracteres com a fonte / caracteres totais do documento.
    """
    char_counts: dict[str, int] = {}  # ps_name -> caracteres
    pages_by_ps: dict[str, set[int]] = {}
    total_chars = 0

    with pymupdf.open(pdf_path) as doc:
        for page_index, page in enumerate(doc):
            page_number = page_index + 1
            for block in page.get_text("dict")["blocks"]:
                if block["type"] != 0:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        n_chars = len(span["text"])
                        if n_chars == 0:
                            continue
                        ps_name = span["font"]
                        char_counts[ps_name] = char_counts.get(ps_name, 0) + n_chars
                        pages_by_ps.setdefault(ps_name, set()).add(page_number)
                        total_chars += n_chars

    if total_chars == 0:
        return []

    infos: dict[tuple[str, int, str], FontInfo] = {}
    chars: dict[tuple[str, int, str], int] = {}
    evidence: dict[tuple[str, int, str], list[Evidence]] = {}
    for ps_name, count in char_counts.items():
        info = parse_ps_font_name(ps_name)
        key = (info.family, info.weight, info.style)
        infos.setdefault(key, info)
        chars[key] = chars.get(key, 0) + count
        evidence.setdefault(key, []).extend(
            Evidence(
                source_type="pdf-guideline",
                path=str(pdf_path),
                page=page_number,
                detail=ps_name,
                confidence=_CONFIDENCE,
            )
            for page_number in sorted(pages_by_ps[ps_name])
        )

    candidates = [
        Candidate(
            value=infos[key].model_dump(by_alias=True),
            score=chars[key] / total_chars,
            evidence=evidence[key],
        )
        for key in infos
    ]
    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates
