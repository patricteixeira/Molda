import hashlib
import io
import json
import zipfile

from brand_api.fonts.models import FontRequest, FontResolutionUnavailable, ResolvedFont
from brand_runtime.ir.models import FontResource
from tests.conftest import _answers


class _FakeResolver:
    def __init__(self, font_data: bytes) -> None:
        self.font_data = font_data
        self.requests: list[FontRequest] = []

    async def resolve(self, request: FontRequest) -> ResolvedFont | None:
        self.requests.append(request)
        if request.family != "Fixture Sans" or request.weight != 700:
            return None
        license_data = b"SIL Open Font License 1.1\n"
        return ResolvedFont(
            family="Fixture Sans",
            weight=700,
            style="normal",
            data=self.font_data,
            license_data=license_data,
            resource=FontResource(
                provider="google-fonts",
                format="ttf",
                upstream_ref="google/fonts@" + "a" * 40 + ":ofl/fixturesans/Fixture.ttf",
                license_id="OFL-1.1",
                license_sha256=hashlib.sha256(license_data).hexdigest(),
                usage_policy="redistributable",
                coverage_profile="pt-BR-ui-v1",
            ),
        )


class _UnavailableResolver:
    async def resolve(self, request: FontRequest) -> ResolvedFont | None:
        raise FontResolutionUnavailable("offline")


def _package_without_font(package_zip: bytes, *, body_family: str = "Missing Sans") -> bytes:
    source = io.BytesIO(package_zip)
    destination = io.BytesIO()
    tokens = {
        "font": {
            "heading": {
                "family": {"$type": "fontFamily", "$value": "Fixture Sans"},
                "weight": {"$type": "fontWeight", "$value": 700},
            },
            "body": {
                "family": {"$type": "fontFamily", "$value": body_family},
                "weight": {"$type": "fontWeight", "$value": 400},
            },
        }
    }
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(destination, "w") as output:
        for info in original.infolist():
            if not info.filename.startswith("fonts/"):
                output.writestr(info, original.read(info))
        output.writestr("tokens.json", json.dumps(tokens))
    return destination.getvalue()


def test_import_resolve_fonte_aberta_sem_upload_manual(
    make_client, package_zip, fixture_font_bytes
):
    resolver = _FakeResolver(fixture_font_bytes)
    client = make_client(font_resolver=resolver)

    response = client.post(
        "/v1/brands/imports",
        files={"package": ("marca.zip", _package_without_font(package_zip), "application/zip")},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    heading = next(question for question in body["questions"] if question["id"] == "font.heading")
    candidate = heading["candidates"][0]["value"]
    assert candidate["family"] == "Fixture Sans"
    assert candidate["path"].startswith("resolved-fonts/")
    assert candidate["resource"]["provider"] == "google-fonts"
    assert candidate["resource"]["usagePolicy"] == "redistributable"
    assert (
        client.get(f"/v1/drafts/{body['draftId']}/assets/{candidate['path']}").content
        == fixture_font_bytes
    )
    assert not any(
        item["code"] == "FONT_FILE_MISSING" and item["target"] == "Fixture Sans"
        for item in body["diagnostics"]
    )

    compiled = client.post(
        f"/v1/drafts/{body['draftId']}/compile",
        json={"answers": _answers(body), "brandName": "ACME tipografica"},
    )
    assert compiled.status_code == 201, compiled.text
    revision = client.get(f"/v1/brand-revisions/{compiled.json()['brandRevisionId']}").json()
    heading_token = revision["fonts"]["font.heading"]
    assert heading_token["source"] == "file"
    assert heading_token["fileSha256"] == hashlib.sha256(fixture_font_bytes).hexdigest()
    assert heading_token["resource"]["provider"] == "google-fonts"
    assert heading_token["resource"]["licenseId"] == "OFL-1.1"


def test_indisponibilidade_do_provedor_nao_bloqueia_import(make_client, package_zip):
    client = make_client(font_resolver=_UnavailableResolver())

    response = client.post(
        "/v1/brands/imports",
        files={"package": ("marca.zip", _package_without_font(package_zip), "application/zip")},
    )

    assert response.status_code == 201, response.text
    assert any(
        item["code"] == "FONT_AUTO_RESOLUTION_FAILED" for item in response.json()["diagnostics"]
    )


def test_fonte_ja_fornecida_nao_dispara_resolucao(make_client, package_zip, fixture_font_bytes):
    resolver = _FakeResolver(fixture_font_bytes)
    client = make_client(font_resolver=resolver)

    response = client.post(
        "/v1/brands/imports",
        files={"package": ("marca.zip", package_zip, "application/zip")},
    )

    assert response.status_code == 201, response.text
    assert resolver.requests == []


def test_variante_nao_resolvida_preserva_diagnostico_da_familia(
    make_client, package_zip, fixture_font_bytes
):
    client = make_client(font_resolver=_FakeResolver(fixture_font_bytes))

    response = client.post(
        "/v1/brands/imports",
        files={
            "package": (
                "marca.zip",
                _package_without_font(package_zip, body_family="Fixture Sans"),
                "application/zip",
            )
        },
    )

    assert response.status_code == 201, response.text
    assert any(
        item["code"] == "FONT_FILE_MISSING"
        and item["target"] == "Fixture Sans"
        and "(400, normal)" in item["message"]
        for item in response.json()["diagnostics"]
    )
