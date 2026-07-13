import pytest
from pydantic import ValidationError

from brand_api.fonts.catalog import GoogleFontsCatalog, normalize_family


def test_catalogo_fixado_resolve_fraunces_variavel_exata():
    catalog = GoogleFontsCatalog.bundled()

    normal = catalog.select("Fraunces", 700, "normal")
    italic = catalog.select("Fraunces", 400, "italic")

    assert catalog.revision == "ec0464b978de222073645d6d3366f3fdf03376d8"
    assert len(catalog.families) == 2009
    assert normal is not None and normal.variant.variable is True
    assert normal.font_path.endswith("Fraunces[SOFT,WONK,opsz,wght].ttf")
    assert normal.variant.git_blob_oid == "8210f9488d3c732359a9292dd09aca3f2bae830e"
    assert italic is not None and "Italic" in italic.variant.filename
    assert normal.family.license.id == "OFL-1.1"


def test_catalogo_nao_finge_que_fontshare_esta_no_google():
    catalog = GoogleFontsCatalog.bundled()

    assert catalog.select("Clash Display", 700, "normal") is None
    assert catalog.select("General Sans", 400, "normal") is None


def test_normalizacao_e_exata_e_limita_input():
    assert normalize_family("  Fraunces  ") == "fraunces"
    assert normalize_family("Noto-Sans") == "notosans"
    assert normalize_family("x" * 129) == ""
    assert normalize_family("Fraunces\n") == ""


def test_catalogo_rejeita_chave_que_nao_corresponde_a_familia():
    payload = GoogleFontsCatalog.bundled().model_dump(mode="json", by_alias=True)
    family = payload["families"].pop("fraunces")
    payload["families"]["familia-errada"] = family

    with pytest.raises(ValidationError, match="Chave de família divergente"):
        GoogleFontsCatalog.model_validate(payload)
