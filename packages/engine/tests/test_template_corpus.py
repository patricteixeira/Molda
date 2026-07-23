import hashlib
import json
import os
import shutil

import pytest
from PIL import Image, ImageDraw
from pydantic import ValidationError
from typer.testing import CliRunner

from brand_runtime.cli import app
from brand_runtime.template_corpus import (
    TemplateCorpusError,
    TemplateCorpusProvenance,
    TemplateReferenceFile,
    audit_template_corpus,
)

runner = CliRunner()


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grammar(axes=None):
    return {
        "axes": axes
        or {
            "energy": -0.55,
            "geometry": 0.20,
            "density": -0.90,
            "formality": 0.90,
            "materiality": -0.35,
            "contrast": 0.20,
        },
        "compositions": ["contemplative"],
        "surfaces": ["none"],
        "hierarchy": "type-led",
        "alignment": "grid",
        "slotRoles": ["headline", "supporting-copy"],
        "negativeSpace": 0.82,
    }


def _draw_preview(path, palette):
    image = Image.new("RGB", (320, 400), palette[0])
    draw = ImageDraw.Draw(image)
    draw.rectangle((32, 40, 288, 96), fill=palette[1])
    draw.rectangle((32, 260, 176, 352), fill=palette[1])
    draw.line((32, 220, 288, 220), fill=palette[2], width=5)
    image.save(path, format="PNG")


def _reference(
    corpus,
    reference_id,
    *,
    intent="reference",
    grammar=True,
    palette=((245, 244, 238), (32, 31, 28), (130, 125, 112)),
    exact_from=None,
):
    reference_dir = corpus / "references" / reference_id
    reference_dir.mkdir(parents=True)
    preview = reference_dir / "preview.png"
    if exact_from is None:
        _draw_preview(preview, palette)
    else:
        shutil.copyfile(exact_from, preview)
    manifest = {
        "schemaVersion": "0.1.0",
        "id": reference_id,
        "titlePt": f"Referência {reference_id}",
        "intent": intent,
        "provenance": {
            "author": "Patric",
            "ownership": "authored",
            "usagePolicy": "derivative-authoring",
        },
        "purposes": ["explorar composição"],
        "profiles": ["post-4x5"],
        "files": [
            {
                "path": "preview.png",
                "role": "preview",
                "mediaType": "image/png",
                "size": preview.stat().st_size,
                "sha256": _sha256(preview),
            }
        ],
        "grammar": _grammar() if grammar else None,
    }
    manifest_path = reference_dir / "template-reference.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path, preview


def _corpus(tmp_path, references):
    corpus = tmp_path / "corpus"
    corpus.mkdir(parents=True)
    paths = []
    for reference in references:
        manifest, _ = _reference(corpus, **reference)
        paths.append(manifest.relative_to(corpus).as_posix())
    root = {
        "schemaVersion": "0.1.0",
        "id": "atelier-patric",
        "titlePt": "Corpus autoral de templates",
        "owner": "Patric",
        "references": paths,
    }
    (corpus / "template-corpus.json").write_text(
        json.dumps(root, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return corpus


def test_valid_corpus_is_deterministic_and_finds_recolored_structure(tmp_path):
    corpus = _corpus(
        tmp_path,
        [
            {"reference_id": "alpha"},
            {
                "reference_id": "beta",
                "intent": "negative-control",
                "palette": ((252, 239, 218), (68, 35, 18), (154, 105, 74)),
            },
        ],
    )

    first = audit_template_corpus(corpus)
    copied = tmp_path / "copied"
    shutil.copytree(corpus, copied)
    second = audit_template_corpus(copied)

    assert first == second
    assert first.promotion_policy == "manual-review-required"
    assert first.reference_count == 2
    assert first.assessments[0].nearest_family.family_id == "minimal-luxury"
    assert first.assessments[0].disposition == "family-variant"
    assert first.assessments[1].disposition == "negative-control"
    assert len(first.similarity_pairs) == 1
    assert first.similarity_pairs[0].kind == "structural-near-duplicate"


def test_corpus_marks_exact_duplicate_and_missing_annotation(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    alpha_manifest, alpha_preview = _reference(corpus, "alpha")
    pending_manifest, _ = _reference(
        corpus,
        "pending",
        grammar=False,
        palette=((230, 242, 255), (20, 61, 110), (96, 148, 204)),
    )
    duplicate_manifest, _ = _reference(corpus, "zeta", exact_from=alpha_preview)
    root = {
        "schemaVersion": "0.1.0",
        "id": "triagem",
        "titlePt": "Triagem",
        "owner": "Ateliê",
        "references": [
            path.relative_to(corpus).as_posix()
            for path in (alpha_manifest, pending_manifest, duplicate_manifest)
        ],
    }
    (corpus / "template-corpus.json").write_text(json.dumps(root), encoding="utf-8")

    report = audit_template_corpus(corpus)
    assessments = {item.reference_id: item for item in report.assessments}

    assert assessments["pending"].disposition == "needs-annotation"
    assert assessments["pending"].nearest_family is None
    assert assessments["zeta"].disposition == "redundant"
    assert assessments["zeta"].duplicate_of == "alpha"
    assert any(pair.kind == "exact-duplicate" for pair in report.similarity_pairs)


def test_corpus_rejects_hash_mismatch_and_undeclared_file(tmp_path):
    corpus = _corpus(tmp_path, [{"reference_id": "alpha"}])
    preview = corpus / "references" / "alpha" / "preview.png"
    preview.write_bytes(preview.read_bytes() + b"alterado")

    with pytest.raises(TemplateCorpusError) as mismatch:
        audit_template_corpus(corpus)
    assert mismatch.value.code == "SIZE_MISMATCH"
    assert mismatch.value.path == "references/alpha/preview.png"

    corpus = _corpus(tmp_path / "other", [{"reference_id": "alpha"}])
    extra = corpus / "references" / "alpha" / "fonte.html"
    extra.write_text("<script>não executar</script>", encoding="utf-8")
    with pytest.raises(TemplateCorpusError) as undeclared:
        audit_template_corpus(corpus)
    assert undeclared.value.code == "FILE_UNDECLARED"
    assert undeclared.value.path == "references/alpha/fonte.html"


def test_corpus_rejects_invalid_preview_and_total_size_limit(tmp_path):
    corpus = _corpus(tmp_path, [{"reference_id": "alpha"}])
    preview = corpus / "references" / "alpha" / "preview.png"
    preview.write_bytes(b"isto nao e png")
    manifest_path = corpus / "references" / "alpha" / "template-reference.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["size"] = preview.stat().st_size
    manifest["files"][0]["sha256"] = _sha256(preview)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(TemplateCorpusError) as invalid:
        audit_template_corpus(corpus)
    assert invalid.value.code == "PREVIEW_INVALID"

    corpus = _corpus(tmp_path / "limited", [{"reference_id": "alpha"}])
    with pytest.raises(TemplateCorpusError) as too_large:
        audit_template_corpus(corpus, max_total_bytes=32)
    assert too_large.value.code == "CORPUS_TOO_LARGE"


@pytest.mark.parametrize(
    ("path", "role", "media_type"),
    [
        ("../preview.png", "preview", "image/png"),
        ("preview.PNG", "preview", "image/png"),
        ("preview.svg", "preview", "image/svg+xml"),
        ("license.html", "license", "text/html"),
        ("source.png", "source", "text/css"),
    ],
)
def test_reference_file_rejects_unsafe_or_incoherent_declarations(path, role, media_type):
    with pytest.raises(ValidationError):
        TemplateReferenceFile(
            path=path,
            role=role,
            media_type=media_type,
            size=1,
            sha256="0" * 64,
        )


def test_public_or_unknown_provenance_is_analysis_only():
    with pytest.raises(ValidationError, match="análise"):
        TemplateCorpusProvenance(
            author="Referência pública",
            ownership="public-reference",
            usage_policy="derivative-authoring",
        )


def test_corpus_rejects_symlink(tmp_path):
    corpus = _corpus(tmp_path, [{"reference_id": "alpha"}])
    link = corpus / "references" / "alpha" / "atalho.png"
    try:
        os.symlink(corpus / "references" / "alpha" / "preview.png", link)
    except OSError:
        pytest.skip("O ambiente não autorizou a criação de symlink.")

    with pytest.raises(TemplateCorpusError) as forbidden:
        audit_template_corpus(corpus)
    assert forbidden.value.code == "SYMLINK_FORBIDDEN"


def test_template_corpus_cli_is_atomic_and_fails_closed(tmp_path):
    corpus = _corpus(tmp_path, [{"reference_id": "alpha"}])
    output = tmp_path / "report.json"
    result = runner.invoke(
        app,
        ["template-corpus-audit", str(corpus), "--out", str(output)],
    )

    assert result.exit_code == 0, result.output
    assert json.loads(output.read_text(encoding="utf-8"))["promotionPolicy"] == (
        "manual-review-required"
    )
    previous = output.read_bytes()

    preview = corpus / "references" / "alpha" / "preview.png"
    preview.write_bytes(preview.read_bytes() + b"alterado")
    failed = runner.invoke(
        app,
        ["template-corpus-audit", str(corpus), "--out", str(output)],
    )
    assert failed.exit_code == 2
    assert failed.stdout == ""
    assert "tamanho" in failed.stderr
    assert output.read_bytes() == previous
    assert list(tmp_path.glob("*.tmp")) == []
