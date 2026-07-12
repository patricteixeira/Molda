from brand_runtime.intake.pdf_fonts import FontInfo, extract_pdf_fonts, parse_ps_font_name


def test_parse_subset_bold():
    info = parse_ps_font_name("ABCDEF+Archivo-Bold")
    assert info == FontInfo(family="Archivo", weight=700, style="normal")


def test_parse_semibold_italic_concatenated():
    info = parse_ps_font_name("Inter-SemiBoldItalic")
    assert info.family == "Inter"
    assert info.weight == 600
    assert info.style == "italic"


def test_parse_suffix_embedded_in_family():
    assert parse_ps_font_name("TimesBold").weight == 700


def test_parse_camel_case_family_split():
    assert parse_ps_font_name("ArchivoNarrow-Regular").family == "Archivo Narrow"


def test_extract_from_fixture_pdf(brand_pdf):
    cands = extract_pdf_fonts(brand_pdf)
    families = {c.value["family"] for c in cands}
    assert "Helvetica" in families           # builtin "helv"
    weights = {c.value["family"]: c.value["weight"] for c in cands}
    assert weights.get("Times", weights.get("Times New Roman", 0)) == 700  # tibo = Times-Bold
