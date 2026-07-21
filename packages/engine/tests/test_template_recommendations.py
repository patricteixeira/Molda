from brand_runtime.ir.models import CreativeDirection, ExpressionAxis
from brand_runtime.intake.direction import derive_creative_direction
from brand_runtime.ir.models import BrandIdentity
from brand_runtime.templates import generate_template_layouts, recommend_template_layouts
from tests.test_compile import FIXED, _answers
from brand_runtime.intake.compile import compile_ir
from brand_runtime.intake.draft import build_draft


def _ir(brand_package):
    draft = build_draft(brand_package)
    return compile_ir(draft, _answers(draft), "ACME", created_at=FIXED)


def _direction(
    *,
    energy: float,
    geometry: float,
    density: float,
    formality: float,
    materiality: float,
    contrast: float,
    composition: str,
    surface: str,
) -> CreativeDirection:
    axis = lambda value: ExpressionAxis(  # noqa: E731
        value=value,
        confidence=1,
        evidence_terms=["evidência confirmada"],
    )
    return CreativeDirection(
        energy=axis(energy),
        geometry=axis(geometry),
        density=axis(density),
        formality=axis(formality),
        materiality=axis(materiality),
        contrast=axis(contrast),
        composition=composition,
        surface=surface,
        scale_contrast=0.7,
        negative_space=0.4,
        bleed=0.5,
        surface_density=0.35,
        rationale_pt=["Direção confirmada."],
    )


def _packages(recommendations, layouts):
    by_id = {layout.id: layout for layout in layouts}
    return [by_id[item.layout_id].template_ref.package_id for item in recommendations]


def test_recommends_precise_families_for_a_geometric_institutional_brand(brand_package):
    ir = _ir(brand_package).model_copy(
        update={
            "creative_direction": _direction(
                energy=0.1,
                geometry=1,
                density=0,
                formality=1,
                materiality=0.7,
                contrast=0.4,
                composition="modular",
                surface="technical-grid",
            )
        }
    )
    layouts = generate_template_layouts(ir)
    recommendations = recommend_template_layouts(ir, layouts)
    packages = _packages(recommendations, layouts)

    assert len(recommendations) == 8
    assert recommendations[0].basis == "brand"
    assert packages[0] in {"technical-diagram", "data-evidence", "swiss-system"}
    assert len(set(packages)) == 4
    assert "geométrica" in recommendations[0].reason_pt


def test_recommends_quiet_families_for_a_sparse_formal_brand(brand_package):
    ir = _ir(brand_package).model_copy(
        update={
            "creative_direction": _direction(
                energy=-0.8,
                geometry=0.1,
                density=-1,
                formality=0.9,
                materiality=-0.5,
                contrast=-0.2,
                composition="contemplative",
                surface="none",
            )
        }
    )
    layouts = generate_template_layouts(ir)
    recommendations = recommend_template_layouts(ir, layouts)
    packages = _packages(recommendations, layouts)

    assert packages[0] == "minimal-luxury"
    assert "essencial" in recommendations[0].reason_pt


def test_falls_back_to_an_honest_diverse_sample_without_direction(brand_package):
    ir = _ir(brand_package).model_copy(update={"creative_direction": None})
    layouts = generate_template_layouts(ir)
    recommendations = recommend_template_layouts(ir, layouts)

    assert len(recommendations) == 8
    assert all(item.basis == "exploratory" for item in recommendations)
    assert len(set(_packages(recommendations, layouts))) == 4
    assert "Ponto de partida variado" in recommendations[0].reason_pt


def test_real_artisanal_layered_language_avoids_technical_and_data_families(brand_package):
    direction = derive_creative_direction(
        BrandIdentity(
            essence="Afeto em camadas, construído com calma e cuidado.",
            personality="Afetuosa, artesanal, acolhedora e delicada.",
            voice="Escrita quente e próxima.",
            avoid="Nunca fria, dessaturada, rígida ou impessoal.",
            evidence=[],
        )
    )
    assert direction is not None
    ir = _ir(brand_package).model_copy(update={"creative_direction": direction})
    layouts = generate_template_layouts(ir)

    first = recommend_template_layouts(ir, layouts)
    second = recommend_template_layouts(ir, layouts)
    packages = _packages(first, layouts)

    assert first == second
    assert packages[0] == "editorial-collage"
    assert set(packages).isdisjoint(
        {
            "technical-diagram",
            "data-evidence",
            "kinetic-typography",
            "typographic-brutalist",
            "constructivist-dynamics",
        }
    )


def test_partial_ocr_identity_does_not_invent_specialized_visual_language(brand_package):
    direction = derive_creative_direction(
        BrandIdentity(
            essence=(
                "Afeto em camadas. Um bolo no pote se faz camada por camada, com calma e cuidado."
            ),
            personality="",
            voice="Escrita quente e próxima.",
            avoid="Nunca fria ou dessaturada.",
            evidence=[],
        )
    )
    assert direction is not None
    ir = _ir(brand_package).model_copy(update={"creative_direction": direction})
    layouts = generate_template_layouts(ir)

    recommendations = recommend_template_layouts(ir, layouts)
    packages = set(_packages(recommendations, layouts))

    assert "editorial-collage" in packages
    assert packages.isdisjoint(
        {
            "technical-diagram",
            "data-evidence",
            "device-mockup",
            "kinetic-typography",
            "typographic-brutalist",
            "constructivist-dynamics",
        }
    )


def test_default_selection_keeps_principal_and_alternative_together(brand_package):
    ir = _ir(brand_package)
    layouts = generate_template_layouts(ir)
    recommendations = recommend_template_layouts(ir, layouts)

    assert [item.rank for item in recommendations] == list(range(1, 9))
    for principal, alternative in zip(recommendations[::2], recommendations[1::2], strict=True):
        assert alternative.layout_id == f"{principal.layout_id}-alternative"


def test_filtered_story_catalog_never_recommends_an_unavailable_layout(brand_package):
    ir = _ir(brand_package)
    story_layouts = [
        layout for layout in generate_template_layouts(ir) if layout.profile == "story-9x16"
    ]

    recommendations = recommend_template_layouts(ir, story_layouts)
    available_ids = {layout.id for layout in story_layouts}

    assert len(recommendations) == min(8, len(story_layouts))
    assert {item.layout_id for item in recommendations}.issubset(available_ids)
