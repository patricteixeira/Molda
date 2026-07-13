"""Catálogo Google Fonts versionado e estritamente validado."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from importlib.resources import files
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_DIRECTORY_RE = re.compile(r"^(?:ofl|apache|ufl)/[a-z0-9_]+$")
_FILENAME_RE = re.compile(r"^[A-Za-z0-9_.+,\[\]() -]+\.ttf$")
_GIT_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def normalize_family(value: str) -> str:
    """Produz a chave exata compartilhada por catálogo e documento."""
    if (
        not isinstance(value, str)
        or len(value) > 128
        or any(ord(character) < 32 for character in value)
    ):
        return ""
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    return "".join(character for character in normalized if character.isalnum())


class _CatalogModel(BaseModel):
    """Base fechada do JSON gerado administrativamente."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class CatalogAxis(_CatalogModel):
    """Faixa declarada por um eixo variável da família."""

    tag: str = Field(min_length=4, max_length=4)
    minimum: float
    maximum: float

    @model_validator(mode="after")
    def _ordered(self) -> CatalogAxis:
        if self.minimum > self.maximum:
            raise ValueError("O eixo do catálogo possui faixa invertida.")
        return self


class CatalogVariant(_CatalogModel):
    """Arquivo upstream que representa uma variante estática ou variável."""

    filename: str = Field(pattern=_FILENAME_RE.pattern)
    style: Literal["normal", "italic"]
    weight: int = Field(ge=100, le=900)
    variable: bool
    git_blob_oid: str = Field(pattern=_GIT_OID_RE.pattern)


class CatalogLicense(_CatalogModel):
    """Licença registrada e verificável antes da aquisição."""

    id: Literal["OFL-1.1", "Apache-2.0", "Ubuntu-font-1.0"]
    filename: str = Field(pattern=r"^(?:OFL|UFL|LICEN[CS]E)\.txt$")
    sha256: str = Field(pattern=_SHA256_RE.pattern)


class CatalogFamily(_CatalogModel):
    """Família canônica com os únicos paths que o downloader pode usar."""

    name: str = Field(min_length=1, max_length=128)
    directory: str = Field(pattern=_DIRECTORY_RE.pattern)
    subsets: list[str]
    axes: list[CatalogAxis]
    variants: list[CatalogVariant] = Field(min_length=1)
    license: CatalogLicense
    metadata_sha256: str = Field(pattern=_SHA256_RE.pattern)


class CatalogExclusion(_CatalogModel):
    """Família deliberadamente ausente por falta de licença verificável."""

    directory: str = Field(pattern=_DIRECTORY_RE.pattern)
    reason: Literal["license-text-missing"]


class GoogleFontsCatalog(_CatalogModel):
    """Snapshot local do repositório oficial ``google/fonts``."""

    schema_version: Literal["1.0.0"]
    provider: Literal["google-fonts"]
    revision: str = Field(pattern=_REVISION_RE.pattern)
    families: dict[str, CatalogFamily]
    excluded: list[CatalogExclusion]

    @model_validator(mode="after")
    def _keys_match_families(self) -> GoogleFontsCatalog:
        for key, family in self.families.items():
            if key != normalize_family(family.name):
                raise ValueError(f"Chave de família divergente no catálogo: {key}.")
        return self

    @classmethod
    def bundled(cls) -> GoogleFontsCatalog:
        """Carrega o snapshot que viaja dentro do pacote da API."""
        resource = files("brand_api.fonts").joinpath("google-fonts.catalog.json")
        return cls.model_validate(json.loads(resource.read_text(encoding="utf-8")))

    def select(
        self,
        family_name: str,
        weight: int,
        style: Literal["normal", "italic"],
    ) -> GoogleFontSelection | None:
        """Seleciona somente variante exata; fontes variáveis cobrem sua faixa."""
        family = self.families.get(normalize_family(family_name))
        if family is None or not 100 <= weight <= 900:
            return None
        styled = [variant for variant in family.variants if variant.style == style]
        weight_axis = next((axis for axis in family.axes if axis.tag == "wght"), None)
        if weight_axis is not None and weight_axis.minimum <= weight <= weight_axis.maximum:
            variable = sorted(
                (variant for variant in styled if variant.variable),
                key=lambda variant: variant.filename,
            )
            if variable:
                return GoogleFontSelection(self, family, variable[0])
        static = sorted(
            (variant for variant in styled if not variant.variable and variant.weight == weight),
            key=lambda variant: variant.filename,
        )
        return GoogleFontSelection(self, family, static[0]) if static else None


@dataclass(frozen=True, slots=True)
class GoogleFontSelection:
    """Entrada do catálogo já reduzida a paths fixados e permitidos."""

    catalog: GoogleFontsCatalog
    family: CatalogFamily
    variant: CatalogVariant

    @property
    def font_path(self) -> str:
        """Path relativo e allowlisted do binário upstream."""
        return f"{self.family.directory}/{self.variant.filename}"

    @property
    def license_path(self) -> str:
        """Path relativo e allowlisted do texto de licença upstream."""
        return f"{self.family.directory}/{self.family.license.filename}"
