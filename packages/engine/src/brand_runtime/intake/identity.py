"""Leitura local das declarações que explicam o que uma marca é.

O extrator preserva trechos do próprio manual; ele não inventa uma síntese nem
depende de um serviço remoto. A pessoa revisa e pode reescrever tudo no wizard
antes que o conteúdo entre no Brand IR.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Literal, cast

import pymupdf

from brand_runtime.intake.base import Candidate
from brand_runtime.ir.models import CamelModel, Evidence

IdentityField = Literal["essence", "personality", "voice", "avoid"]

_MARKERS: dict[IdentityField, tuple[str, ...]] = {
    "essence": (
        "essencia",
        "proposito",
        "manifesto",
        "missao",
        "visao",
        "posicionamento",
        "por que existimos",
        "existe para",
        "acreditamos",
    ),
    "personality": (
        "personalidade",
        "atributos",
        "valores",
        "principios",
        "atitude",
        "somos",
    ),
    "voice": (
        "tom de voz",
        "nossa voz",
        "linguagem",
        "como falamos",
        "comunicacao",
    ),
    "avoid": (
        "nao somos",
        "nunca",
        "evitar",
        "nao deve",
        "nao usamos",
    ),
}
_FIELD_LIMIT = 1_200
_MIN_EXCERPT_LENGTH = 24


class IdentityDraftValue(CamelModel):
    """Texto editável oferecido para confirmação no wizard."""

    essence: str = ""
    personality: str = ""
    voice: str = ""
    avoid: str = ""


def _searchable(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_marks).strip().casefold()


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _field_for(text: str) -> IdentityField | None:
    searchable = _searchable(text)
    matches = [
        (field, marker)
        for field, markers in _MARKERS.items()
        for marker in markers
        if marker in searchable
    ]
    if not matches:
        return None
    matches.sort(key=lambda item: (-len(item[1]), tuple(_MARKERS).index(item[0])))
    return matches[0][0]


def _evidence(path: Path, page: int, field: IdentityField, excerpt: str) -> Evidence:
    return Evidence(
        source_type="pdf-guideline",
        path=str(path),
        page=page,
        detail=f"declaração de {field}: {excerpt[:240]}",
        confidence=0.9,
        authoritative=True,
    )


def _page_excerpts(path: Path) -> list[tuple[IdentityField, str, Evidence]]:
    found: list[tuple[IdentityField, str, Evidence]] = []
    with pymupdf.open(path) as document:
        for page_index in range(len(document)):
            page = document.load_page(page_index)
            blocks = cast(list[tuple], page.get_text("blocks"))
            for block in blocks:
                text = _clean(str(block[4]))
                if len(text) < _MIN_EXCERPT_LENGTH:
                    continue
                field = _field_for(text)
                if field is None:
                    continue
                excerpt = text[:_FIELD_LIMIT]
                found.append((field, excerpt, _evidence(path, page_index + 1, field, excerpt)))
    return found


def identity_candidate(pdf_paths: list[Path]) -> Candidate:
    """Agrupa declarações relevantes sem resumir ou completar lacunas."""
    values: dict[IdentityField, list[str]] = {
        "essence": [],
        "personality": [],
        "voice": [],
        "avoid": [],
    }
    evidence: list[Evidence] = []
    seen: set[tuple[IdentityField, str]] = set()
    for path in pdf_paths:
        for field, excerpt, item_evidence in _page_excerpts(path):
            key = (field, _searchable(excerpt))
            if key in seen:
                continue
            seen.add(key)
            current_length = sum(len(item) for item in values[field])
            if current_length >= _FIELD_LIMIT:
                continue
            values[field].append(excerpt[: _FIELD_LIMIT - current_length])
            evidence.append(item_evidence)

    value = IdentityDraftValue(**{field: "\n\n".join(items) for field, items in values.items()})
    return Candidate(
        value=value.model_dump(mode="json", by_alias=True),
        score=float(len(evidence)),
        evidence=evidence,
    )
