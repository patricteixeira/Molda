from brand_runtime.artifacts import (
    ArtifactValue,
    artifact_from_content_spec,
    artifact_to_content_spec,
)
from brand_runtime.intake.compile import compile_ir
from brand_runtime.intake.draft import build_draft
from brand_runtime.kit.generator import generate_kit
from brand_runtime.kit.models import AssetLayer, ContentSpec, LayerOverride, TextValue
from tests.test_compile import FIXED, _answers


def _ir(brand_package):
    draft = build_draft(brand_package)
    return compile_ir(draft, _answers(draft), "ACME", created_at=FIXED)


def test_content_spec_artifact_roundtrip_is_lossless(brand_package):
    ir = _ir(brand_package)
    layout = next(item for item in generate_kit(ir) if item.id == "typographic-ledger-post-4x5")
    content = ContentSpec(
        layout_id=layout.id,
        brand_revision_id=ir.revision.id,
        values={"headline": TextValue(text="Forma é argumento.")},
        background_color_token="color.primary",
        asset_bindings={"logo": "logo.primary"},
        overrides={"headline": LayerOverride(font_size_px=144, area=(80, 200, 860, 420))},
    )

    artifact = artifact_from_content_spec(content, layout, artifact_id="artifact-1")
    restored = artifact_to_content_spec(artifact)

    assert artifact.template_ref == layout.template_ref
    assert artifact.scene_snapshot == layout
    assert artifact.values["headline"].status == "confirmed"
    assert artifact.background_color_token == "color.primary"
    assert artifact.asset_bindings == {"logo": "logo.primary"}
    assert restored == content


def test_missing_content_never_carries_a_value():
    missing = ArtifactValue(status="missing")
    assert missing.value is None


def test_artifact_accepts_binding_for_structural_asset(brand_package):
    ir = _ir(brand_package)
    layout = next(item for item in generate_kit(ir) if item.id == "typographic-ledger-post-4x5")
    layout.locked_layers.append(
        AssetLayer(
            id="brand-mark",
            asset_token="logo.primary",
            area=(900, 80, 96, 96),
            fit="contain",
            z_index=12,
        )
    )
    content = ContentSpec(
        layout_id=layout.id,
        brand_revision_id=ir.revision.id,
        values={"headline": TextValue(text="Forma é argumento.")},
        asset_bindings={"brand-mark": "logo.primary"},
    )

    artifact = artifact_from_content_spec(content, layout, artifact_id="artifact-asset")

    assert artifact.asset_bindings == {"brand-mark": "logo.primary"}
    assert artifact_to_content_spec(artifact) == content
