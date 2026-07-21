from brand_api.carousel_preflight import assess_carousel_candidate
from brand_api.models import BrandRevision
from brand_api.revision_ir import revision_brand_ir
from brand_runtime import ContentSpec, generate_carousel_layouts


def _ir(client, revision_id):
    with client.app.state.session_factory() as session:
        revision = session.get(BrandRevision, revision_id)
        assert revision is not None
        return revision_brand_ir(revision)


def _content(ir, layout, **values):
    return ContentSpec(
        layout_id=layout.id,
        brand_revision_id=ir.revision.id,
        values={slot_id: {"kind": "text", "text": text} for slot_id, text in values.items()},
    )


def test_preflight_accepts_content_that_fits_and_has_contrast(client, compiled, tmp_path):
    ir = _ir(client, compiled["brandRevisionId"])
    layout = generate_carousel_layouts(ir, "post-4x5")[1]
    content = _content(
        ir,
        layout,
        index="02 / 05",
        kicker="Uma leitura",
        headline="Uma mensagem clara",
        **{"body-1": "Um argumento curto e legível."},
    )

    assessment = assess_carousel_candidate(ir, layout, content, tmp_path)

    assert assessment.viable
    assert assessment.issues == ()


def test_preflight_rejects_text_collision(client, compiled, tmp_path):
    ir = _ir(client, compiled["brandRevisionId"])
    layout = generate_carousel_layouts(ir, "post-4x5")[0]
    headline = next(slot for slot in layout.slots if slot.id == "headline")
    collided = layout.model_copy(
        update={
            "slots": [
                slot.model_copy(update={"area": headline.area}) if slot.id == "kicker" else slot
                for slot in layout.slots
            ]
        }
    )
    content = _content(
        ir,
        collided,
        index="01 / 05",
        kicker="Mensagem sobreposta",
        headline="Título que ocupa o mesmo lugar",
    )

    assessment = assess_carousel_candidate(ir, collided, content, tmp_path)

    assert not assessment.viable
    assert any(issue.startswith("text-collision:kicker:headline") for issue in assessment.issues)


def test_preflight_rejects_low_contrast_text(client, compiled, tmp_path):
    ir = _ir(client, compiled["brandRevisionId"])
    layout = generate_carousel_layouts(ir, "post-4x5")[0]
    low_contrast = layout.model_copy(
        update={
            "slots": [
                slot.model_copy(update={"color_token": layout.background.color_token})
                if slot.id == "kicker"
                else slot
                for slot in layout.slots
            ]
        }
    )
    content = _content(
        ir,
        low_contrast,
        index="01 / 05",
        kicker="Texto invisível",
        headline="Título legível",
    )

    assessment = assess_carousel_candidate(ir, low_contrast, content, tmp_path)

    assert not assessment.viable
    assert "contrast:kicker" in assessment.issues


def test_preflight_rejects_text_that_cannot_fit_at_the_minimum_size(
    client,
    compiled,
    tmp_path,
):
    ir = _ir(client, compiled["brandRevisionId"])
    layout = generate_carousel_layouts(ir, "post-4x5")[0]
    constrained = layout.model_copy(
        update={
            "slots": [
                slot.model_copy(update={"area": (slot.area[0], slot.area[1], slot.area[2], 8)})
                if slot.id == "headline"
                else slot
                for slot in layout.slots
            ]
        }
    )
    content = _content(
        ir,
        constrained,
        index="01 / 05",
        headline="Mesmo uma frase curta precisa de altura para existir",
    )

    assessment = assess_carousel_candidate(ir, constrained, content, tmp_path)

    assert not assessment.viable
    assert "text-overflow:headline" in assessment.issues
