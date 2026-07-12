import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from brand_runtime.intake.compile import Answers, CompileError, compile_ir
from brand_runtime.intake.draft import build_draft

FIXED = datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc)


def _answers(draft):
    def first(qid):
        q = next(q for q in draft.questions if q.id == qid)
        return q.candidates[0].value

    return Answers(
        values={
            "color.primary": first("color.primary"),
            "color.background": "#FFFFFF",
            "color.text": "#1A1A1A",
            "font.heading": first("font.heading"),
            "font.body": first("font.body"),
            "logo.primary": first("logo.primary"),
        }
    )


def test_missing_required_raises(brand_package):
    draft = build_draft(brand_package)
    with pytest.raises(CompileError) as exc:
        compile_ir(draft, Answers(values={}), "ACME")
    assert "color.primary" in str(exc.value)


def test_happy_path_produces_valid_ir(brand_package):
    draft = build_draft(brand_package)
    ir = compile_ir(draft, _answers(draft), "ACME", created_at=FIXED)
    assert ir.brand.name == "ACME"
    assert ir.colors["color.primary"].value == "#1A4D8F"
    ev_types = [e.source_type for e in ir.colors["color.primary"].evidence]
    assert "wizard-confirmation" in ev_types and "svg-asset" in ev_types
    assert ir.fonts["font.heading"].source == "file"
    assert ir.roles["heading"].font == "font.heading"
    assert ir.assets["logo.primary"].sha256 and len(ir.assets["logo.primary"].sha256) == 64
    logo_evidence = [e.source_type for e in ir.assets["logo.primary"].evidence]
    assert "svg-asset" in logo_evidence and "wizard-confirmation" in logo_evidence


def test_revision_id_is_deterministic(brand_package):
    draft = build_draft(brand_package)
    a = compile_ir(draft, _answers(draft), "ACME", created_at=FIXED)
    b = compile_ir(draft, _answers(draft), "ACME", created_at=FIXED)
    assert a.revision.id == b.revision.id
    assert a.revision.id.startswith("brandrev_")


def test_revision_id_ignores_audit_timestamp(brand_package):
    draft = build_draft(brand_package)
    a = compile_ir(draft, _answers(draft), "ACME", created_at=FIXED)
    b = compile_ir(draft, _answers(draft), "ACME", created_at=FIXED + timedelta(days=1))

    assert a.revision.created_at != b.revision.created_at
    assert a.revision.id == b.revision.id


def test_revision_id_is_portable_between_package_roots(brand_package, tmp_path):
    copied_package = tmp_path / "copied-package"
    shutil.copytree(brand_package, copied_package)
    a_draft = build_draft(brand_package)
    b_draft = build_draft(copied_package)

    a = compile_ir(a_draft, _answers(a_draft), "ACME", created_at=FIXED)
    b = compile_ir(b_draft, _answers(b_draft), "ACME", created_at=FIXED)

    assert a.revision.id == b.revision.id
    assert all(
        not Path(evidence.path).is_absolute()
        for token in [*a.colors.values(), *a.fonts.values()]
        for evidence in token.evidence
        if evidence.path is not None
    )


def test_unanswered_secondary_yields_diagnostic(brand_package):
    draft = build_draft(brand_package)
    ir = compile_ir(draft, _answers(draft), "ACME", created_at=FIXED)
    assert any(
        d.code == "UNDETERMINED" and d.target == "color.secondary" for d in ir.diagnostics
    )


def test_missing_error_lists_every_required_answer(brand_package):
    draft = build_draft(brand_package)
    with pytest.raises(CompileError) as exc:
        compile_ir(draft, Answers(values={}), "ACME")
    message = str(exc.value)
    for question_id in (
        "color.primary",
        "color.background",
        "color.text",
        "font.heading",
        "font.body",
        "logo.primary",
    ):
        assert question_id in message


def test_equivalent_css_color_inherits_evidence_and_revision(brand_package):
    draft = build_draft(brand_package)
    canonical = _answers(draft)
    equivalent = Answers(values={**canonical.values, "color.primary": "rgb(26, 77, 143)"})

    a = compile_ir(draft, canonical, "ACME", created_at=FIXED)
    b = compile_ir(draft, equivalent, "ACME", created_at=FIXED)

    assert b.colors["color.primary"].value == "#1A4D8F"
    assert any(e.source_type == "svg-asset" for e in b.colors["color.primary"].evidence)
    assert a.revision.id == b.revision.id


def test_compile_does_not_mutate_draft_or_answers(brand_package):
    draft = build_draft(brand_package)
    answers = _answers(draft)
    before_draft = draft.model_dump(mode="json")
    before_answers = answers.model_dump(mode="json")

    compile_ir(draft, answers, "ACME", created_at=FIXED)
    compile_ir(draft, answers, "ACME", created_at=FIXED)

    assert draft.model_dump(mode="json") == before_draft
    assert answers.model_dump(mode="json") == before_answers


def test_unknown_answer_does_not_change_revision(brand_package):
    draft = build_draft(brand_package)
    answers = _answers(draft)
    with_unknown = Answers(values={**answers.values, "future.unknown": "ignorado"})

    a = compile_ir(draft, answers, "ACME", created_at=FIXED)
    b = compile_ir(draft, with_unknown, "ACME", created_at=FIXED)

    assert a.revision.id == b.revision.id


def test_manual_font_cannot_inject_file_path(brand_package, tmp_path):
    outside = tmp_path / "outside.ttf"
    outside.write_bytes(b"nao e uma fonte")
    draft = build_draft(brand_package)
    answers = _answers(draft)
    answers.values["font.heading"] = {
        "family": "Fonte Manual",
        "weight": 700,
        "style": "normal",
        "path": str(outside),
    }

    ir = compile_ir(draft, answers, "ACME", created_at=FIXED)

    assert ir.fonts["font.heading"].source == "referenced-only"
    assert ir.fonts["font.heading"].file_sha256 is None


def test_file_candidate_wins_tie_when_its_path_was_selected(brand_package):
    (brand_package / "tokens.json").write_text(
        """{
          "font": {
            "$type": "fontFamily",
            "heading": {"$value": "Fixture Sans"}
          },
          "weight": {
            "$type": "fontWeight",
            "heading": {"$value": 700}
          }
        }""",
        encoding="utf-8",
    )
    draft = build_draft(brand_package)
    answers = _answers(draft)
    heading = next(question for question in draft.questions if question.id == "font.heading")
    file_candidate = next(candidate for candidate in heading.candidates if "path" in candidate.value)
    answers.values["font.heading"] = file_candidate.value

    ir = compile_ir(draft, answers, "ACME", created_at=FIXED)

    assert ir.fonts["font.heading"].source == "file"
    assert ir.fonts["font.heading"].file_sha256 is not None


def test_logo_path_cannot_escape_package(brand_package):
    draft = build_draft(brand_package)
    answers = _answers(draft)
    answers.values["logo.primary"] = "../fora.svg"

    with pytest.raises(CompileError, match="dentro do pacote"):
        compile_ir(draft, answers, "ACME", created_at=FIXED)


def test_invalid_answers_are_reported_as_compile_errors(brand_package):
    draft = build_draft(brand_package)
    answers = _answers(draft)
    answers.values["color.primary"] = "isto-nao-e-cor"
    with pytest.raises(CompileError, match="color.primary"):
        compile_ir(draft, answers, "ACME", created_at=FIXED)

    answers = _answers(draft)
    answers.values["font.heading"] = {
        "family": "Fixture Sans",
        "weight": 950,
        "style": "normal",
    }
    with pytest.raises(CompileError, match="font.heading"):
        compile_ir(draft, answers, "ACME", created_at=FIXED)
