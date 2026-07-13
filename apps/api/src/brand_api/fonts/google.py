"""Aquisição segura de fontes do snapshot oficial Google Fonts."""

from __future__ import annotations

import hashlib
from io import BytesIO

import httpx
from fontTools.ttLib import TTFont, TTLibError

from brand_api.fonts.catalog import GoogleFontSelection, GoogleFontsCatalog, normalize_family
from brand_api.fonts.models import FontRequest, FontResolutionUnavailable, ResolvedFont
from brand_runtime.intake.fonts import (
    DEFAULT_COVERAGE_PROFILE,
    font_info_from_ttfont,
    missing_codepoints,
    required_codepoints,
)
from brand_runtime.ir.models import FontAxis, FontResource

_MAX_FONT_BYTES = 5 * 2**20
_MAX_LICENSE_BYTES = 256 * 2**10
_COVERAGE_PROFILE = DEFAULT_COVERAGE_PROFILE
_REQUIRED_CODEPOINTS = tuple(sorted(required_codepoints(_COVERAGE_PROFILE)))


def _git_blob_oid(data: bytes) -> str:
    """Recalcula o OID Git SHA-1 que ancora os bytes na árvore fixada."""
    digest = hashlib.sha1(usedforsecurity=False)
    digest.update(f"blob {len(data)}\0".encode("ascii"))
    digest.update(data)
    return digest.hexdigest()


class GoogleFontsResolver:
    """Resolve famílias do catálogo sem aceitar URLs vindas do documento."""

    def __init__(
        self,
        *,
        base_url: str,
        catalog: GoogleFontsCatalog | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Configura o endpoint restrito, o snapshot e o transporte injetável."""
        url = httpx.URL(base_url)
        if (
            url.scheme not in {"http", "https"}
            or not url.host
            or url.userinfo
            or url.query
            or url.fragment
        ):
            raise ValueError("BRANDRT_FONT_FETCH_BASE_URL precisa ser uma URL HTTP base segura.")
        self.base_url = str(url).rstrip("/") + "/"
        self.catalog = catalog or GoogleFontsCatalog.bundled()
        self.transport = transport

    async def _download(self, path: str, *, maximum: int) -> bytes:
        """Baixa um path do catálogo com timeout, limite e redirects recusados."""
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                follow_redirects=False,
                timeout=httpx.Timeout(12.0, connect=5.0),
                transport=self.transport,
                trust_env=False,
            ) as client:
                async with client.stream("GET", path) as response:
                    if response.status_code != 200:
                        raise FontResolutionUnavailable(
                            f"O provedor respondeu HTTP {response.status_code}."
                        )
                    declared = response.headers.get("content-length")
                    if declared is not None and int(declared) > maximum:
                        raise FontResolutionUnavailable("O arquivo de fonte excede o limite.")
                    chunks: list[bytes] = []
                    size = 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > maximum:
                            raise FontResolutionUnavailable("O arquivo de fonte excede o limite.")
                        chunks.append(chunk)
        except FontResolutionUnavailable:
            raise
        except (httpx.HTTPError, OSError, ValueError) as exc:
            raise FontResolutionUnavailable("O provedor de fontes está indisponível.") from exc
        return b"".join(chunks)

    @staticmethod
    def _validate_font(
        data: bytes,
        selection: GoogleFontSelection,
        request: FontRequest,
    ) -> tuple[list[FontAxis], list[int]]:
        """Confirma identidade, variante, eixos e cobertura do binário real."""
        try:
            with TTFont(BytesIO(data), lazy=False) as font:
                for table in ("name", "OS/2", "cmap", "maxp"):
                    font[table]
                if font["maxp"].numGlyphs <= 0:
                    raise ValueError("Fonte sem glifos.")
                info = font_info_from_ttfont(font, source=selection.font_path)
                if normalize_family(info.family) != normalize_family(selection.family.name):
                    raise ValueError("Família interna divergente do catálogo.")
                if info.style != request.style:
                    raise ValueError("Estilo interno divergente do catálogo.")

                axes: list[FontAxis] = []
                if selection.variant.variable:
                    fvar = font["fvar"]
                    axes = [
                        FontAxis(
                            tag=axis.axisTag,
                            minimum=axis.minValue,
                            default=axis.defaultValue,
                            maximum=axis.maxValue,
                        )
                        for axis in sorted(fvar.axes, key=lambda item: item.axisTag)
                    ]
                    weight_axis = next((axis for axis in axes if axis.tag == "wght"), None)
                    if (
                        weight_axis is None
                        or request.weight < weight_axis.minimum
                        or request.weight > weight_axis.maximum
                    ):
                        raise ValueError("Peso fora da faixa variável real.")
                elif info.weight != request.weight:
                    raise ValueError("Peso interno divergente do catálogo.")
                missing = missing_codepoints(font, _REQUIRED_CODEPOINTS)
        except (AssertionError, EOFError, KeyError, OSError, TTLibError, ValueError) as exc:
            raise FontResolutionUnavailable("O binário de fonte não passou na validação.") from exc
        return axes, missing

    async def resolve(self, request: FontRequest) -> ResolvedFont | None:
        """Adquire uma variante exata e registra sua licença e cobertura."""
        selection = self.catalog.select(request.family, request.weight, request.style)
        if selection is None:
            return None
        font_data = await self._download(selection.font_path, maximum=_MAX_FONT_BYTES)
        if _git_blob_oid(font_data) != selection.variant.git_blob_oid:
            raise FontResolutionUnavailable("O binário diverge do objeto Git fixado no catálogo.")
        license_data = await self._download(selection.license_path, maximum=_MAX_LICENSE_BYTES)
        license_sha256 = hashlib.sha256(license_data).hexdigest()
        if license_sha256 != selection.family.license.sha256:
            raise FontResolutionUnavailable("A licença baixada diverge do catálogo fixado.")
        try:
            if not license_data.decode("utf-8").strip():
                raise UnicodeError
        except UnicodeError as exc:
            raise FontResolutionUnavailable("O texto de licença é inválido.") from exc

        axes, missing = self._validate_font(font_data, selection, request)
        if missing:
            raise FontResolutionUnavailable(
                "A fonte não cobre todos os caracteres exigidos pelo perfil pt-BR."
            )
        upstream_ref = f"google/fonts@{self.catalog.revision}:{selection.font_path}"
        resource = FontResource(
            provider="google-fonts",
            format="ttf",
            upstream_ref=upstream_ref,
            license_id=selection.family.license.id,
            license_sha256=license_sha256,
            usage_policy="redistributable",
            coverage_profile=_COVERAGE_PROFILE,
            missing_codepoints=missing,
            axes=axes,
        )
        return ResolvedFont(
            family=selection.family.name,
            weight=request.weight,
            style=request.style,
            data=font_data,
            license_data=license_data,
            resource=resource,
        )
