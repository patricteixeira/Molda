"""Catálogo Fontshare versionado para referências CSS hospedadas pelo provedor.

Este módulo trabalha somente com metadados. Ele não baixa, extrai nem
armazena os binários das fontes anunciadas pelo Fontshare.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from importlib.resources import files
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

from brand_api.fonts.catalog import normalize_family

_CATALOG_SOURCE = "https://api.fontshare.com/v2/fonts?offset=0&limit=100"
_CSS_ENDPOINT = "https://api.fontshare.com/v2/css"
_REVISION_RE = re.compile(r"^[0-9a-f]{64}$")
_SLUG_RE = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")


class _FontshareModel(BaseModel):
    """Base fechada e estrita para o snapshot administrativo."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        strict=True,
    )


class FontshareStyle(_FontshareModel):
    """Código CSS e identidade tipográfica de uma variante Fontshare."""

    code: int = Field(ge=1, le=1000)
    weight: int = Field(ge=0, le=1000)
    style: Literal["normal", "italic"]
    variable: bool

    @model_validator(mode="after")
    def _code_matches_identity(self) -> FontshareStyle:
        if self.variable:
            expected_code = 2 if self.style == "italic" else 1
            if self.weight != 0 or self.code != expected_code:
                raise ValueError("Código de variante variável Fontshare inconsistente.")
            return self

        if not 1 <= self.weight <= 1000:
            raise ValueError("Variante estática Fontshare precisa declarar peso real.")
        return self


class FontshareFamily(_FontshareModel):
    """Família Fontshare reduzida aos metadados necessários para CSS."""

    name: str = Field(min_length=1, max_length=128)
    slug: str = Field(min_length=1, max_length=96, pattern=_SLUG_RE.pattern)
    license_type: Literal["itf_ffl", "sil_ofl"]
    styles: list[FontshareStyle] = Field(min_length=1, max_length=32)

    @field_validator("name")
    @classmethod
    def _safe_name(cls, value: str) -> str:
        if not normalize_family(value):
            raise ValueError("Nome de família Fontshare inválido.")
        return value

    @model_validator(mode="after")
    def _unique_styles(self) -> FontshareFamily:
        codes = [style.code for style in self.styles]
        if len(codes) != len(set(codes)):
            raise ValueError("Família Fontshare contém estilos duplicados.")
        return self


def _content_revision(families: dict[str, FontshareFamily]) -> str:
    """Calcula a identidade do conteúdo sem depender da formatação do JSON."""
    payload = {
        key: family.model_dump(mode="json", by_alias=True) for key, family in families.items()
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class FontshareCatalog(_FontshareModel):
    """Snapshot local do endpoint oficial de metadados Fontshare."""

    schema_version: Literal["1.0.0"]
    provider: Literal["fontshare-external"]
    source: Literal["https://api.fontshare.com/v2/fonts?offset=0&limit=100"]
    revision: str = Field(pattern=_REVISION_RE.pattern)
    families: dict[str, FontshareFamily]

    @model_validator(mode="after")
    def _validate_catalog(self) -> FontshareCatalog:
        slugs: set[str] = set()
        for key, family in self.families.items():
            if key != normalize_family(family.name):
                raise ValueError(f"Chave de família Fontshare divergente: {key}.")
            if family.slug in slugs:
                raise ValueError(f"Slug Fontshare duplicado: {family.slug}.")
            slugs.add(family.slug)
        if self.revision != _content_revision(self.families):
            raise ValueError("Revisão do catálogo Fontshare diverge do conteúdo.")
        return self

    @classmethod
    def bundled(cls) -> FontshareCatalog:
        """Carrega o snapshot que viaja dentro do pacote da API."""
        resource = files("brand_api.fonts").joinpath("fontshare.catalog.json")
        return cls.model_validate(json.loads(resource.read_text(encoding="utf-8")))

    def select(
        self,
        family_name: str,
        weight: int,
        style: Literal["normal", "italic"],
    ) -> FontshareSelection | None:
        """Seleciona uma variante estática exatamente igual ao pedido."""
        if not 1 <= weight <= 1000 or style not in {"normal", "italic"}:
            return None
        family = self.families.get(normalize_family(family_name))
        if family is None:
            return None
        matches = [
            variant
            for variant in family.styles
            if not variant.variable and variant.weight == weight and variant.style == style
        ]
        if len(matches) != 1:
            return None
        return FontshareSelection(catalog=self, family=family, variant=matches[0])


@dataclass(frozen=True, slots=True)
class FontshareSelection:
    """Referência exata já reduzida a valores allowlisted pelo catálogo."""

    catalog: FontshareCatalog
    family: FontshareFamily
    variant: FontshareStyle

    @property
    def canonical_family(self) -> str:
        """Expõe o nome oficial sem reutilizar a grafia livre do pedido."""
        return self.family.name

    @property
    def provider(self) -> Literal["fontshare-external"]:
        """Identifica que a fonte permanece hospedada pelo Fontshare."""
        return "fontshare-external"

    @property
    def stylesheet_url(self) -> str:
        """Produz somente a URL CSS oficial, sem incorporar entrada livre."""
        return f"{_CSS_ENDPOINT}?f[]={self.family.slug}@{self.variant.code}&display=swap"

    @property
    def css_url(self) -> str:
        """Mantém um alias curto para consumidores internos de metadados."""
        return self.stylesheet_url


__all__ = [
    "FontshareCatalog",
    "FontshareFamily",
    "FontshareSelection",
    "FontshareStyle",
]
