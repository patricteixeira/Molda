import json

import pytest
from pydantic import ValidationError

from brand_api.fonts.fontshare import FontshareCatalog


def _payload() -> dict:
    return json.loads(json.dumps(FontshareCatalog.bundled().model_dump(mode="json", by_alias=True)))


def test_catalogo_bundled_contem_as_cem_familias_oficiais_sem_bytes():
    catalog = FontshareCatalog.bundled()

    assert len(catalog.families) == 100
    assert catalog.provider == "fontshare-external"
    assert catalog.source == "https://api.fontshare.com/v2/fonts?offset=0&limit=100"
    assert set(catalog.families) >= {"clashdisplay", "generalsans"}

    raw_family = _payload()["families"]["clashdisplay"]
    assert set(raw_family) == {"name", "slug", "licenseType", "styles"}
    assert set(raw_family["styles"][0]) == {"code", "weight", "style", "variable"}
    serialized = json.dumps(raw_family)
    assert "file" not in serialized
    assert "cdn.fontshare.com" not in serialized


def test_seleciona_clash_e_general_exatas_e_constroi_url_allowlisted():
    catalog = FontshareCatalog.bundled()

    clash = catalog.select("  Clash-Display  ", 700, "normal")
    general = catalog.select("General Sans", 400, "normal")
    general_italic = catalog.select("general sans", 400, "italic")

    assert clash is not None
    assert clash.canonical_family == "Clash Display"
    assert clash.provider == "fontshare-external"
    assert clash.variant.code == 700
    assert clash.stylesheet_url == (
        "https://api.fontshare.com/v2/css?f[]=clash-display@700&display=swap"
    )
    assert clash.css_url == clash.stylesheet_url
    assert general is not None and general.variant.code == 400
    assert general_italic is not None and general_italic.variant.code == 401


def test_variavel_nao_finge_correspondencia_exata():
    catalog = FontshareCatalog.bundled()

    assert any(item.variable for item in catalog.families["clashdisplay"].styles)
    assert catalog.select("Clash Display", 900, "normal") is None
    assert catalog.select("Clash Display", 700, "italic") is None
    assert catalog.select("Clash Display", 0, "normal") is None
    # Array possui Regular e Wide com a mesma identidade no recorte compacto.
    assert catalog.select("Array", 400, "normal") is None


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda payload: payload["families"]["clashdisplay"].update(
                {"slug": "https://evil.example/font"}
            ),
            "slug",
        ),
        (
            lambda payload: payload["families"]["clashdisplay"]["styles"][0].update({"code": 0}),
            "greater than or equal to 1",
        ),
        (
            lambda payload: payload["families"]["clashdisplay"].update(
                {"binaryUrl": "https://evil.example/font.woff2"}
            ),
            "Extra inputs",
        ),
    ],
)
def test_catalogo_rejeita_slug_codigo_e_campos_nao_allowlisted(mutation, message):
    payload = _payload()
    mutation(payload)

    with pytest.raises(ValidationError, match=message):
        FontshareCatalog.model_validate(payload)


def test_catalogo_rejeita_chave_e_revisao_divergentes():
    payload = _payload()
    family = payload["families"].pop("clashdisplay")
    payload["families"]["familiaerrada"] = family

    with pytest.raises(ValidationError, match="Chave de família Fontshare divergente"):
        FontshareCatalog.model_validate(payload)

    payload = _payload()
    payload["revision"] = "0" * 64
    with pytest.raises(ValidationError, match="Revisão do catálogo Fontshare"):
        FontshareCatalog.model_validate(payload)
