"""Contratos da aquisição de fontes, independentes de HTTP e do wizard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from brand_runtime.ir.models import FontResource


@dataclass(frozen=True, slots=True)
class FontRequest:
    """Variante exata que o intake precisa transformar em recurso local."""

    family: str
    weight: int
    style: Literal["normal", "italic"]


@dataclass(frozen=True, slots=True)
class ResolvedFont:
    """Bytes validados e sua proveniência pronta para materialização."""

    family: str
    weight: int
    style: Literal["normal", "italic"]
    data: bytes
    license_data: bytes
    resource: FontResource


class FontResolver(Protocol):
    """Porta de aplicação para provedores de fontes permitidos."""

    async def resolve(self, request: FontRequest) -> ResolvedFont | None:
        """Resolve uma correspondência exata ou devolve ``None``."""


class FontResolutionUnavailable(RuntimeError):
    """O catálogo conhecia a fonte, mas a aquisição segura não concluiu."""


class DisabledFontResolver:
    """Resolvedor nulo usado quando a instância não configurou aquisição."""

    async def resolve(self, request: FontRequest) -> None:
        """Mantém o fluxo original sem rede ou efeitos colaterais."""
        return None
