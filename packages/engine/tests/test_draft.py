from brand_runtime.intake.draft import build_draft


def test_question_set(brand_package):
    draft = build_draft(brand_package)
    ids = [q.id for q in draft.questions]
    for required in [
        "color.primary",
        "color.background",
        "color.text",
        "font.heading",
        "font.body",
        "logo.primary",
    ]:
        assert required in ids


def test_primary_candidates_are_non_neutral_and_svg_weighted(brand_package):
    draft = build_draft(brand_package)
    q = next(q for q in draft.questions if q.id == "color.primary")
    assert q.candidates[0].value == "#1A4D8F"  # aparece no SVG (peso 3) e no PDF
    assert all(c.value != "#333333" for c in q.candidates)  # neutra não entra em primary


def test_background_has_white_default_last(brand_package):
    draft = build_draft(brand_package)
    q = next(q for q in draft.questions if q.id == "color.background")
    assert q.candidates[-1].value == "#FFFFFF"


def test_heading_candidates_prefer_font_files(brand_package):
    draft = build_draft(brand_package)
    q = next(q for q in draft.questions if q.id == "font.heading")
    first = q.candidates[0]
    assert first.value["family"] == "Fixture Sans"
    assert first.evidence[0].source_type == "font-file"


def test_logo_question_and_prompt(brand_package):
    draft = build_draft(brand_package)
    q = next(q for q in draft.questions if q.id == "logo.primary")
    assert q.prompt_pt == "Este é o logo oficial da marca?"
    assert q.candidates[0].value.endswith("logo.svg")


def test_extensoes_sao_case_insensitive_em_toda_plataforma(brand_package, tmp_path):
    import json
    import shutil

    package = tmp_path / "uppercase"
    shutil.copytree(brand_package, package)
    renames = (
        (package / "manual.pdf", package / "MANUAL.PDF"),
        (package / "assets" / "logos" / "logo.svg", package / "assets" / "logos" / "LOGO.SVG"),
        (
            package / "fonts" / "fixture-sans-bold.ttf",
            package / "fonts" / "FIXTURE-SANS-BOLD.TTF",
        ),
    )
    for source, destination in renames:
        temporary = source.with_name(f"rename-{source.name}")
        source.rename(temporary)
        temporary.rename(destination)
    (package / "TOKENS.JSON").write_text(
        json.dumps({"color": {"brand": {"$type": "color", "$value": "#00FF88"}}}),
        encoding="utf-8",
    )

    draft = build_draft(package)

    assert not any(item.code == "NO_PDF_FOUND" for item in draft.diagnostics)
    assert (
        next(q for q in draft.questions if q.id == "color.primary").candidates[0].value == "#00FF88"
    )
    assert (
        next(q for q in draft.questions if q.id == "font.heading").candidates[0].value["family"]
        == "Fixture Sans"
    )
    assert (
        next(q for q in draft.questions if q.id == "logo.primary")
        .candidates[0]
        .value.endswith("LOGO.SVG")
    )
