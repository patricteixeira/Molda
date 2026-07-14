import json

import pytest

from brand_runtime import validate_brand_package
from brand_runtime.intake.draft import build_draft
from brand_runtime_adapter.builder import (
    AdapterBuildError,
    AdapterIdentity,
    BrandPackageBuilder,
    SourceIdentity,
)
from brand_runtime_adapter.dtcg import build_dtcg_package, main


def _sources(tmp_path):
    tokens = tmp_path / "source.tokens.json"
    tokens.write_text(
        json.dumps(
            {
                "color": {
                    "primary": {"$type": "color", "$value": "#1844D8"},
                    "background": {"$type": "color", "$value": "#FFFFFF"},
                    "text": {"$type": "color", "$value": "#171815"},
                }
            }
        ),
        encoding="utf-8",
    )
    logo = tmp_path / "source.svg"
    logo.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<rect width="10" height="10" fill="#1844D8"/></svg>',
        encoding="utf-8",
    )
    return tokens, logo


def _builder():
    return BrandPackageBuilder(
        AdapterIdentity(id="org.example.fixture", name="Fixture", version="1.2.3"),
        SourceIdentity(kind="fixture", label="Teste local"),
    )


def test_dtcg_adapter_builds_package_accepted_by_real_engine(tmp_path):
    tokens, logo = _sources(tmp_path)
    package = tmp_path / "package"

    built = build_dtcg_package(tokens, logo, package, label="Tokens locais")
    report = validate_brand_package(package)
    draft = build_draft(package)

    assert built.package_sha256 == report.package_sha256
    assert report.adapter.id == "org.brandruntime.dtcg"
    assert report.file_count == 2
    primary = next(item for item in draft.questions if item.id == "color.primary")
    assert primary.candidates[0].value == "#1844D8"


def test_builder_refuses_traversal_collision_and_media_mismatch(tmp_path):
    tokens, logo = _sources(tmp_path)
    builder = _builder()

    with pytest.raises(AdapterBuildError, match="portável"):
        builder.add_file(tokens, "../tokens.json", role="tokens", media_type="application/json")
    with pytest.raises(AdapterBuildError, match="Logos"):
        builder.add_file(logo, "assets/logos/logo.svg", role="logo", media_type="image/png")

    builder.add_file(logo, "assets/logos/logo.svg", role="logo", media_type="image/svg+xml")
    with pytest.raises(AdapterBuildError, match="colidentes"):
        builder.add_file(logo, "assets/logos/Logo.svg", role="logo", media_type="image/svg+xml")


def test_builder_never_overwrites_destination(tmp_path):
    tokens, _logo = _sources(tmp_path)
    out = tmp_path / "existing"
    out.mkdir()
    sentinel = out / "sentinel.txt"
    sentinel.write_text("preservar", encoding="utf-8")
    builder = _builder().add_file(
        tokens,
        "tokens.json",
        role="tokens",
        media_type="application/json",
    )

    with pytest.raises(AdapterBuildError, match="já existe"):
        builder.build(out)
    assert sentinel.read_text(encoding="utf-8") == "preservar"


def test_builder_rechecks_source_before_copy(tmp_path):
    tokens, _logo = _sources(tmp_path)
    out = tmp_path / "removed-source"
    builder = _builder().add_file(
        tokens,
        "tokens.json",
        role="tokens",
        media_type="application/json",
    )
    tokens.unlink()

    with pytest.raises(AdapterBuildError, match="deixou de ser"):
        builder.build(out)

    assert not out.exists()
    assert not list(tmp_path.glob(".removed-source.stage-*"))


def test_failed_publication_cleans_staging(tmp_path, monkeypatch):
    tokens, _logo = _sources(tmp_path)
    out = tmp_path / "failed"
    builder = _builder().add_file(
        tokens,
        "tokens.json",
        role="tokens",
        media_type="application/json",
    )

    def fail_copy(*_args, **_kwargs):
        raise OSError("falha simulada")

    monkeypatch.setattr("brand_runtime_adapter.builder.shutil.copyfile", fail_copy)
    with pytest.raises(AdapterBuildError, match="publicar"):
        builder.build(out)

    assert not out.exists()
    assert not list(tmp_path.glob(".failed.stage-*"))


def test_cli_prints_receipt_and_fails_without_partial_output(tmp_path, capsys):
    tokens, logo = _sources(tmp_path)
    out = tmp_path / "cli-package"

    assert main([str(tokens), "--logo", str(logo), "--out", str(out)]) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["packageSha256"] == validate_brand_package(out).package_sha256

    invalid_out = tmp_path / "invalid"
    assert main([str(tokens), "--logo", str(tokens), "--out", str(invalid_out)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "SVG ou PNG" in captured.err
    assert not invalid_out.exists()
