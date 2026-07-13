import hashlib
from io import BytesIO

import httpx
import pytest
from fontTools.ttLib import TTFont

from brand_api.fonts.catalog import GoogleFontsCatalog
from brand_api.fonts.google import GoogleFontsResolver
from brand_api.fonts.models import FontRequest, FontResolutionUnavailable


def _blob_oid(data: bytes) -> str:
    digest = hashlib.sha1(usedforsecurity=False)
    digest.update(f"blob {len(data)}\0".encode("ascii"))
    digest.update(data)
    return digest.hexdigest()


def _catalog(license_data: bytes, font_data: bytes = b"") -> GoogleFontsCatalog:
    return GoogleFontsCatalog.model_validate(
        {
            "schemaVersion": "1.0.0",
            "provider": "google-fonts",
            "revision": "a" * 40,
            "families": {
                "fixturesans": {
                    "name": "Fixture Sans",
                    "directory": "ofl/fixturesans",
                    "subsets": ["latin", "latin-ext"],
                    "axes": [],
                    "variants": [
                        {
                            "filename": "FixtureSans-Bold.ttf",
                            "style": "normal",
                            "weight": 700,
                            "variable": False,
                            "gitBlobOid": _blob_oid(font_data),
                        }
                    ],
                    "license": {
                        "id": "OFL-1.1",
                        "filename": "OFL.txt",
                        "sha256": hashlib.sha256(license_data).hexdigest(),
                    },
                    "metadataSha256": "b" * 64,
                }
            },
            "excluded": [],
        }
    )


def _transport(font_data: bytes, license_data: bytes) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("FixtureSans-Bold.ttf"):
            return httpx.Response(200, content=font_data)
        if request.url.path.endswith("OFL.txt"):
            return httpx.Response(200, content=license_data)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


@pytest.mark.anyio
async def test_resolver_valida_fonte_licenca_cobertura_e_proveniencia(coverage_font_bytes):
    license_data = b"SIL Open Font License 1.1\n"
    resolver = GoogleFontsResolver(
        base_url="https://font-fetch.test/google-fonts/",
        catalog=_catalog(license_data, coverage_font_bytes),
        transport=_transport(coverage_font_bytes, license_data),
    )

    resolved = await resolver.resolve(FontRequest("Fixture Sans", 700, "normal"))

    assert resolved is not None
    assert resolved.data == coverage_font_bytes
    assert resolved.resource.provider == "google-fonts"
    assert resolved.resource.license_id == "OFL-1.1"
    assert resolved.resource.usage_policy == "redistributable"
    assert resolved.resource.coverage_profile == "pt-BR-ui-v1"
    assert resolved.resource.missing_codepoints == []
    assert resolved.resource.upstream_ref.endswith("ofl/fixturesans/FixtureSans-Bold.ttf")


@pytest.mark.anyio
async def test_resolver_recusa_redirect():
    license_data = b"license\n"

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "https://evil.example/font.ttf"})

    resolver = GoogleFontsResolver(
        base_url="https://font-fetch.test/google-fonts/",
        catalog=_catalog(license_data),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(FontResolutionUnavailable, match="HTTP 302"):
        await resolver.resolve(FontRequest("Fixture Sans", 700, "normal"))


@pytest.mark.anyio
async def test_resolver_recusa_cobertura_incompleta(coverage_font_bytes):
    license_data = b"license\n"
    font = TTFont(BytesIO(coverage_font_bytes))
    for table in font["cmap"].tables:
        table.cmap.pop(ord("ç"), None)
    reduced = BytesIO()
    font.save(reduced)
    font.close()
    resolver = GoogleFontsResolver(
        base_url="https://font-fetch.test/google-fonts/",
        catalog=_catalog(license_data, reduced.getvalue()),
        transport=_transport(reduced.getvalue(), license_data),
    )

    with pytest.raises(FontResolutionUnavailable, match="cobre todos"):
        await resolver.resolve(FontRequest("Fixture Sans", 700, "normal"))


@pytest.mark.anyio
async def test_resolver_recusa_um_byte_divergente_do_objeto_git(coverage_font_bytes):
    license_data = b"license\n"
    altered = coverage_font_bytes + b"x"
    resolver = GoogleFontsResolver(
        base_url="https://font-fetch.test/google-fonts/",
        catalog=_catalog(license_data, coverage_font_bytes),
        transport=_transport(altered, license_data),
    )

    with pytest.raises(FontResolutionUnavailable, match="objeto Git"):
        await resolver.resolve(FontRequest("Fixture Sans", 700, "normal"))
