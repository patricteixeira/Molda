import pymupdf

from brand_runtime.intake.pdf_colors import extract_pdf_colors, extract_pdf_declared_colors


def test_extracts_the_three_colors(brand_pdf):
    cands = extract_pdf_colors(brand_pdf)
    values = [c.value for c in cands]
    assert "#1A4D8F" in values
    assert "#F4A300" in values
    assert "#333333" in values


def test_big_rect_outranks_small_rect(brand_pdf):
    cands = extract_pdf_colors(brand_pdf)
    by_value = {c.value: c.score for c in cands}
    assert by_value["#1A4D8F"] > by_value["#F4A300"]


def test_evidence_carries_page_and_source(brand_pdf):
    cands = extract_pdf_colors(brand_pdf)
    ev = cands[0].evidence[0]
    assert ev.source_type == "pdf-guideline"
    assert ev.page == 1


def test_stroke_only_pdf_with_zero_area_rect_does_not_crash(tmp_path):
    """Linha horizontal com stroke: rect delimitador tem área zero → todos os pesos 0."""
    pdf_path = tmp_path / "linha.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page(width=595, height=842)
        page.draw_line((50, 100), (500, 100), color=(1, 0, 0))
        doc.save(pdf_path)

    cands = extract_pdf_colors(pdf_path)

    values = [c.value for c in cands]
    assert "#FF0000" in values
    assert all(0.0 <= c.score <= 1.0 for c in cands)


def test_declared_hex_colors_are_ranked_by_semantic_role_across_pages(tmp_path):
    pdf_path = tmp_path / "manual-declarativo.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_textbox(
            pymupdf.Rect(40, 40, 500, 700),
            "PRIMARIAS\nGrafite - tinta\n60%\nHEX #1F232A\n"
            "Ambar - o ponto\n10%\nHEX #CA6B0B\nPapel - fundo\n30%",
            fontsize=12,
        )
        page = doc.new_page()
        page.insert_text((40, 40), "HEX #FCFBF8", fontsize=12)
        doc.save(pdf_path)

    roles = extract_pdf_declared_colors(pdf_path)

    assert roles["primary"][0].value == "#1F232A"
    assert roles["background"][0].value == "#FCFBF8"
    assert roles["text"][0].value == "#1F232A"
    assert roles["accent"][0].value == "#CA6B0B"
    assert roles["primary"][0].evidence[0].detail == "cor HEX declarada no texto: #1F232A"


def test_design_tokens_bind_brand_pillars_without_promoting_technical_black(tmp_path):
    pdf_path = tmp_path / "vita-cann-med.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_textbox(
            pymupdf.Rect(40, 40, 500, 700),
            "CORES\nPaleta\nVerde institucional, creme como papel, "
            "ouro medicinal como tempero - nunca molho.\nPILARES\n"
            "Verde floresta\n--green-800 : #1C382A\n"
            "Creme\n--cream-200 : #F4F1E8\n"
            "Ouro medicinal\n--gold-500 : #C89C40\n"
            "VERDE - ESCALA\n14271D 244736 2F5A44\n"
            "OURO - ESCALA\n94722A B08A34\n",
            fontsize=12,
        )
        # Preto técnico de construção, sem declaração textual de pertencimento à paleta.
        page.draw_line((40, 760), (500, 760), color=(0, 0, 0), width=1)
        doc.save(pdf_path)

    roles = extract_pdf_declared_colors(pdf_path)

    assert roles["primary"][0].value == "#1C382A"
    assert roles["background"][0].value == "#F4F1E8"
    assert roles["accent"][0].value == "#C89C40"
    assert {"#14271D", "#244736", "#2F5A44", "#94722A", "#B08A34"}.issubset(
        {candidate.value for candidate in roles["all"]}
    )
    assert "#000000" not in {candidate.value for candidate in roles["all"]}


def test_usage_after_hex_can_add_a_second_background_without_contaminating_neighbors(tmp_path):
    pdf_path = tmp_path / "fundos-claro-escuro.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_textbox(
            pymupdf.Rect(40, 40, 500, 700),
            "Grafite - tinta\n60%\nHEX #1F232A\n"
            "Texto, traco do simbolo, fundos escuros.\n"
            "Ambar - o ponto\n10%\nHEX #CA6B0B\n"
            "Acento unico. Nunca como cor de massa.\n"
            "Papel - fundo\n30%\nHEX #FCFBF8\n"
            "Fundo padrao. Branco quente, levemente off-white.",
            fontsize=12,
        )
        doc.save(pdf_path)

    roles = extract_pdf_declared_colors(pdf_path)
    background = [candidate.value for candidate in roles["background"]]

    assert background[:2] == ["#FCFBF8", "#1F232A"]
    assert "#CA6B0B" not in background


def test_functional_hex_colors_are_not_promoted_to_background_or_text(tmp_path):
    pdf_path = tmp_path / "cores-funcionais.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_textbox(
            pymupdf.Rect(40, 40, 500, 700),
            "Papel - fundo\nHEX #FCFBF8\nGrafite - tinta\nHEX #1F232A\n"
            "FUNCIONAIS - apenas interface\nSucesso\n#4F7D5F\nErro\n#B1492F\nInformacao\n#5A6F88",
            fontsize=12,
        )
        doc.save(pdf_path)

    roles = extract_pdf_declared_colors(pdf_path)
    background = {candidate.value for candidate in roles["background"]}
    text = {candidate.value for candidate in roles["text"]}
    all_declared = {candidate.value for candidate in roles["all"]}

    assert background == {"#FCFBF8"}
    assert text == {"#1F232A"}
    assert {"#FCFBF8", "#1F232A", "#4F7D5F", "#B1492F", "#5A6F88"}.issubset(all_declared)
