import hashlib
import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from brand_runtime.cli import app
from brand_runtime.ecosystem.package import (
    AdapterIdentity,
    BrandPackageFile,
    BrandPackageManifest,
    BrandPackageSource,
    PackageValidationError,
    validate_brand_package,
)

runner = CliRunner()
REFERENCE_PACKAGE = (
    Path(__file__).resolve().parents[3] / "examples" / "brand-package-reference"
)


def _file(package, relative, role, media_type):
    data = (package / relative).read_bytes()
    return BrandPackageFile(
        path=relative,
        role=role,
        media_type=media_type,
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )


def _package(tmp_path):
    package = tmp_path / "package"
    logos = package / "assets" / "logos"
    logos.mkdir(parents=True)
    (package / "tokens.json").write_text(
        '{"color":{"primary":{"$type":"color","$value":"#1844D8"}}}',
        encoding="utf-8",
    )
    (logos / "logo.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"/>',
        encoding="utf-8",
    )
    manifest = BrandPackageManifest(
        schema_version="0.1.0",
        adapter=AdapterIdentity(
            id="org.brandruntime.reference",
            name="Adapter de referência",
            version="0.1.0",
        ),
        source=BrandPackageSource(kind="dtcg", label="Fixture portátil"),
        files=[
            _file(package, "tokens.json", "tokens", "application/json"),
            _file(package, "assets/logos/logo.svg", "logo", "image/svg+xml"),
        ],
    )
    (package / "brand-package.json").write_text(
        manifest.model_dump_json(by_alias=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return package


def test_valid_package_emits_portable_deterministic_receipt(tmp_path):
    package = _package(tmp_path)

    first = validate_brand_package(package)
    copied = tmp_path / "copied"
    shutil.copytree(package, copied)
    second = validate_brand_package(copied)

    assert first.status == "pass"
    assert first.file_count == 2
    assert first.total_bytes > 0
    assert first.package_sha256 == second.package_sha256
    assert first.adapter.id == "org.brandruntime.reference"


def test_public_reference_package_remains_conformant():
    report = validate_brand_package(REFERENCE_PACKAGE)

    assert (
        report.package_sha256
        == "f6a804980e6020bb6a5c5131d2ab5be1dfe15a9777c5776a9e48732086e78a92"
    )


def test_package_rejects_hash_mismatch_and_undeclared_file(tmp_path):
    package = _package(tmp_path)
    tokens = package / "tokens.json"
    original = tokens.read_bytes()
    tokens.write_bytes(b"[" + original[1:])

    with pytest.raises(PackageValidationError) as mismatch:
        validate_brand_package(package)
    assert mismatch.value.code == "HASH_MISMATCH"
    assert mismatch.value.path == "tokens.json"

    package = _package(tmp_path / "other")
    (package / "references").mkdir()
    (package / "references" / "extra.pdf").write_bytes(b"%PDF-extra")
    with pytest.raises(PackageValidationError) as undeclared:
        validate_brand_package(package)
    assert undeclared.value.code == "FILE_UNDECLARED"
    assert undeclared.value.path == "references/extra.pdf"


@pytest.mark.parametrize(
    ("path", "role", "media_type"),
    [
        ("../tokens.json", "tokens", "application/json"),
        ("assets/logos/logo.svg", "font", "image/svg+xml"),
        ("tokens.json", "tokens", "image/png"),
        ("nested/tokens.json", "tokens", "application/json"),
        ("assets/logos/logo.SVG", "logo", "image/svg+xml"),
    ],
)
def test_manifest_rejects_nonportable_or_unusable_declarations(path, role, media_type):
    with pytest.raises(ValidationError):
        BrandPackageFile(
            path=path,
            role=role,
            media_type=media_type,
            size=1,
            sha256="0" * 64,
        )


def test_manifest_rejects_case_insensitive_path_collision():
    shared = {
        "role": "logo",
        "media_type": "image/svg+xml",
        "size": 2,
        "sha256": "0" * 64,
    }
    with pytest.raises(ValidationError, match="únicos"):
        BrandPackageManifest(
            schema_version="0.1.0",
            adapter=AdapterIdentity(id="org.example.adapter", name="Adapter", version="1.0.0"),
            source=BrandPackageSource(kind="other"),
            files=[
                BrandPackageFile(path="assets/logos/logo.svg", **shared),
                BrandPackageFile(path="assets/logos/Logo.svg", **shared),
            ],
        )


def test_package_validate_cli_emits_json_and_fails_closed(tmp_path):
    package = _package(tmp_path)
    result = runner.invoke(app, ["package-validate", str(package)])

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["packageSha256"]
    assert result.stderr == ""

    tokens = package / "tokens.json"
    original = tokens.read_bytes()
    tokens.write_bytes(b"[" + original[1:])
    failed = runner.invoke(app, ["package-validate", str(package)])
    assert failed.exit_code == 2
    assert failed.stdout == ""
    assert "SHA-256" in failed.stderr
