import pytest

from brand_runtime.intake.compile import compile_ir
from brand_runtime.intake.draft import build_draft
from brand_runtime.ir.models import CompositionRules, LayoutStyleRule
from brand_runtime.kit.generator import KitGenerationError, generate_kit
from brand_runtime.kit.models import PROFILES
from tests.test_compile import FIXED, _answers, _composition_ir


def _ir(brand_package):
    draft = build_draft(brand_package)
    return compile_ir(draft, _answers(draft), "ACME", created_at=FIXED)


def test_kit_has_legacy_ten_plus_three_versioned_templates(brand_package):
    kit = generate_kit(_ir(brand_package))
    assert len(kit) == 13
    assert len({layout.id for layout in kit}) == 13
    assert {layout.profile for layout in kit} == set(PROFILES)


def test_all_token_and_role_references_exist(brand_package):
    ir = _ir(brand_package)
    for layout in generate_kit(ir):
        if layout.background.kind == "color":
            assert layout.background.color_token in ir.colors
        for slot in layout.slots:
            if slot.kind == "text":
                assert slot.role in ir.roles
                role = ir.roles[slot.role]
                assert role.font in ir.fonts
                assert role.color in ir.colors
            if slot.kind == "image":
                assert slot.fit == "fixed"


def test_slots_fit_inside_canvas(brand_package):
    for layout in generate_kit(_ir(brand_package)):
        width, height = layout.canvas.width_px, layout.canvas.height_px
        for slot in layout.slots:
            x, y, slot_width, slot_height = slot.area
            assert 0 <= x and 0 <= y and x + slot_width <= width and y + slot_height <= height, (
                layout.id,
                slot.id,
            )


def test_adaptation_not_resize(brand_package):
    kit = {layout.id: layout for layout in generate_kit(_ir(brand_package))}
    square = next(slot for slot in kit["statement-post-1x1"].slots if slot.id == "headline")
    story = next(slot for slot in kit["statement-story-9x16"].slots if slot.id == "headline")
    assert square.area != story.area  # composição recalculada por perfil


def test_logo_slot_everywhere_locked(brand_package):
    for layout in generate_kit(_ir(brand_package)):
        logo = next(slot for slot in layout.slots if slot.kind == "logo")
        assert logo.fit == "fixed"


def test_layout_ids_order_and_background_contract(brand_package):
    kit = generate_kit(_ir(brand_package))
    assert [layout.id for layout in kit] == [
        "statement-post-1x1",
        "statement-post-4x5",
        "statement-story-9x16",
        "quote-post-1x1",
        "quote-post-4x5",
        "quote-story-9x16",
        "announce-post-1x1",
        "announce-post-4x5",
        "announce-story-9x16",
        "one-pager-doc-a4",
        "typographic-ledger-post-4x5",
        "typographic-monument-post-4x5",
        "typographic-diptych-post-4x5",
    ]
    for layout in kit:
        if layout.id.startswith("quote-"):
            assert layout.background.kind == "image-slot"
        else:
            assert layout.background.color_token == "color.background"


def test_golden_geometry_for_every_layout(brand_package):
    kit = {layout.id: layout for layout in generate_kit(_ir(brand_package))}
    expected = {
        "statement-post-1x1": {"headline": (48, 324, 984, 432), "logo": (902, 902, 130, 130)},
        "statement-post-4x5": {"headline": (48, 405, 984, 540), "logo": (902, 1172, 130, 130)},
        "statement-story-9x16": {"headline": (64, 576, 952, 768), "logo": (886, 1726, 130, 130)},
        "quote-post-1x1": {
            "photo": (0, 0, 1080, 1080),
            "quote": (48, 346, 984, 389),
            "author": (48, 778, 984, 65),
            "logo": (902, 902, 130, 130),
        },
        "quote-post-4x5": {
            "photo": (0, 0, 1080, 1350),
            "quote": (48, 432, 984, 486),
            "author": (48, 972, 984, 81),
            "logo": (902, 1172, 130, 130),
        },
        "quote-story-9x16": {
            "photo": (0, 0, 1080, 1920),
            "quote": (64, 614, 952, 691),
            "author": (64, 1382, 952, 115),
            "logo": (886, 1726, 130, 130),
        },
        "announce-post-1x1": {
            "headline": (48, 48, 984, 238),
            "body": (48, 324, 984, 302),
            "photo": (0, 670, 1080, 410),
            "logo": (902, 902, 130, 130),
        },
        "announce-post-4x5": {
            "headline": (48, 48, 984, 297),
            "body": (48, 405, 984, 378),
            "photo": (0, 837, 1080, 513),
            "logo": (902, 1172, 130, 130),
        },
        "announce-story-9x16": {
            "headline": (64, 64, 952, 422),
            "body": (64, 576, 952, 538),
            "photo": (0, 1190, 1080, 730),
            "logo": (886, 1726, 130, 130),
        },
        "one-pager-doc-a4": {
            "title": (76, 76, 642, 120),
            "body": (76, 226, 642, 725),
            "logo": (622, 951, 96, 96),
        },
    }
    for layout_id, slots in expected.items():
        assert {slot.id: slot.area for slot in kit[layout_id].slots} == slots


def test_generation_is_deterministic_and_does_not_share_state(brand_package):
    ir = _ir(brand_package)
    first = generate_kit(ir)
    second = generate_kit(ir)
    assert [item.model_dump_json(by_alias=True) for item in first] == [
        item.model_dump_json(by_alias=True) for item in second
    ]

    first[0].slots[0].area = (0, 0, 1, 1)
    assert second[0].slots[0].area == (48, 324, 984, 432)
    assert generate_kit(ir)[0].slots[0].area == (48, 324, 984, 432)


def test_missing_ir_references_and_impossible_logo_fail_explicitly(brand_package):
    ir = _ir(brand_package).model_copy(deep=True)
    del ir.colors["color.background"]
    with pytest.raises(KitGenerationError, match="color.background"):
        generate_kit(ir)

    ir = _ir(brand_package).model_copy(deep=True)
    ir.roles["heading"].color = "color.inexistente"
    with pytest.raises(KitGenerationError, match="heading.color"):
        generate_kit(ir)

    ir = _ir(brand_package).model_copy(deep=True)
    ir.assets["logo.primary"].min_width_px = 1000
    with pytest.raises(KitGenerationError, match="não cabe"):
        generate_kit(ir)


def test_explicit_composition_adds_four_editorial_4x5_layouts_after_canonical_ten(
    brand_package,
):
    ir = _composition_ir(brand_package)
    kit = generate_kit(ir)

    editorial = kit[-4:]
    assert len(kit) == 17
    assert [layout.id for layout in editorial] == [
        "editorial-light-post-4x5",
        "editorial-dark-post-4x5",
        "editorial-closure-light-post-4x5",
        "editorial-closure-dark-post-4x5",
    ]
    assert all(layout.profile == "post-4x5" for layout in editorial)
    assert [layout.composition_mode for layout in editorial] == [
        "light",
        "dark",
        "light",
        "dark",
    ]

    for layout, logo_token in zip(editorial[:2], ("logo.onLight", "logo.onDark"), strict=True):
        layers = {layer.id: layer for layer in layout.locked_layers}
        slots = {slot.id: slot for slot in layout.slots}
        assert list(layers) == [
            "diagonal-field",
            "frame-top",
            "frame-left",
            "frame-right",
            "frame-bottom",
            "register-top-left-x",
            "register-top-left-y",
            "register-top-right-x",
            "register-top-right-y",
            "register-bottom-left-x",
            "register-bottom-left-y",
            "register-bottom-right-x",
            "register-bottom-right-y",
            "accent-rule",
            "brand-mark",
        ]
        assert layers["diagonal-field"].area == (0, 0, 1080, 1350)
        assert layers["diagonal-field"].motif == "diagonal-lines"
        assert layers["diagonal-field"].opacity == 0.06
        assert layers["diagonal-field"].spacing_px == 22
        assert layers["brand-mark"].asset_token == logo_token
        assert layers["brand-mark"].area == (918, 116, 58, 58)
        assert layers["accent-rule"].area == (104, 445, 56, 4)
        assert set(slots) == {"index", "kicker", "headline", "signature"}
        assert slots["index"].area == (80, 890, 760, 460)
        assert slots["index"].fill_mode == "stroke"
        assert slots["index"].text_format == "zero-padded"
        assert slots["index"].opacity == 0.08
        assert slots["headline"].area == (104, 525, 840, 360)
        assert slots["headline"].emphasis_color_token == "color.secondary"
        assert slots["headline"].text_transform == "uppercase"
        assert slots["kicker"].color_token == slots["headline"].color_token
        assert slots["kicker"].max_chars == 48
        assert slots["kicker"].required is False
        assert slots["kicker"].fit == "shrink-within-role-range"
        assert slots["signature"].text_align == "center"

    for layout, logo_token in zip(editorial[2:], ("logo.onLight", "logo.onDark"), strict=True):
        layers = {layer.id: layer for layer in layout.locked_layers}
        slots = {slot.id: slot for slot in layout.slots}
        assert layers["brand-mark"].asset_token == logo_token
        assert layers["brand-mark"].area == (474, 470, 132, 132)
        assert layers["accent-diagonals"].area == (0, 930, 1080, 420)
        assert set(slots) == {"headline", "tagline", "signature"}
        assert slots["headline"].text_align == "center"
        assert slots["tagline"].emphasis_color_token == "color.secondary"


def test_partial_composition_never_invents_editorial_layouts(brand_package):
    ir = _ir(brand_package).model_copy(deep=True)
    assert ir.composition_rules is None
    assert len(generate_kit(ir)) == 13

    composition_ir = _composition_ir(brand_package)
    ir = composition_ir.model_copy(deep=True)
    ir.composition_rules.color_ratios = []
    assert len(generate_kit(ir)) == 13

    ir = composition_ir.model_copy(deep=True)
    ir.assets["logo.onLight"].min_width_px = 96
    assert len(generate_kit(ir)) == 13


@pytest.mark.parametrize(
    ("style", "layout_id", "layer_ids", "headline_area"),
    [
        (
            "ornamental-divider",
            "signature-ornamental-post-4x5",
            ["divider-left", "divider-dot", "divider-right"],
            (100, 270, 880, 300),
        ),
        (
            "restrained-clinical-grid",
            "signature-clinical-post-4x5",
            ["grid-panel", "accent-rule", "body-rule", "accent-dot"],
            (80, 250, 680, 330),
        ),
    ],
)
def test_declared_layout_style_adds_one_distinct_signature_layout(
    brand_package,
    style,
    layout_id,
    layer_ids,
    headline_area,
):
    ir = _ir(brand_package).model_copy(deep=True)
    ir.colors["color.secondary"] = ir.colors["color.primary"].model_copy(deep=True)
    ir.composition_rules = CompositionRules(
        layout_style=LayoutStyleRule(kind=style),
    )

    kit = generate_kit(ir)
    layout = kit[-1]

    assert len(kit) == 14
    assert layout.id == layout_id
    assert layout.profile == "post-4x5"
    assert [layer.id for layer in layout.locked_layers] == layer_ids
    assert next(slot for slot in layout.slots if slot.id == "headline").area == headline_area
    assert next(slot for slot in layout.slots if slot.kind == "logo").fit == "fixed"


def test_ornamental_signature_respects_declared_logo_minimum(brand_package):
    ir = _ir(brand_package).model_copy(deep=True)
    ir.colors["color.secondary"] = ir.colors["color.primary"].model_copy(deep=True)
    ir.composition_rules = CompositionRules(
        layout_style=LayoutStyleRule(kind="ornamental-divider"),
    )
    ir.assets["logo.primary"].min_width_px = 180

    layout = generate_kit(ir)[-1]
    logo = next(slot for slot in layout.slots if slot.kind == "logo")

    assert logo.area[2:] == (180, 180)
    assert logo.area[0] == 450
