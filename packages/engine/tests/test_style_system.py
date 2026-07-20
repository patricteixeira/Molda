from brand_runtime.intake.compile import compile_ir
from brand_runtime.intake.draft import build_draft
from brand_runtime.style import derive_style_system
from tests.test_compile import FIXED, _answers


def _ir(brand_package):
    draft = build_draft(brand_package)
    return compile_ir(draft, _answers(draft), "ACME", created_at=FIXED)


def test_style_system_is_deterministic_and_preserves_zero(brand_package):
    ir = _ir(brand_package)
    first = derive_style_system(ir)
    second = derive_style_system(ir)

    assert first.model_dump_json(by_alias=True) == second.model_dump_json(by_alias=True)
    assert first.brand_revision_id == ir.revision.id
    assert first.spacing["none"] == 0
    assert first.radii["none"] == 0
    assert first.shadows["none"].opacity == 0
    assert first.typography["heading"].font_token == ir.roles["heading"].font


def test_style_system_uses_only_existing_color_and_font_tokens(brand_package):
    ir = _ir(brand_package)
    style = derive_style_system(ir)

    assert all(item.font_token in ir.fonts for item in style.typography.values())
    assert all(item.color_token in ir.colors for item in style.typography.values())
    assert all(item.color_token in ir.colors for item in style.strokes.values())
    assert all(item.color_token in ir.colors for item in style.shadows.values())
