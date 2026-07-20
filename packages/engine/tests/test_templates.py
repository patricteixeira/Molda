import pytest

from brand_runtime.export import export_document
from brand_runtime.intake.compile import compile_ir
from brand_runtime.intake.draft import build_draft
from brand_runtime.kit.models import ContentSpec, LayoutSpec, TextValue
from brand_runtime.templates import evaluate_template_package, typographic_editorial_package
from tests.test_compile import FIXED, _answers


def _ir(brand_package):
    draft = build_draft(brand_package)
    return compile_ir(draft, _answers(draft), "ACME", created_at=FIXED)


def _fingerprint(layout):
    return (
        tuple((slot.id, slot.area, slot.font_size_px, slot.text_align) for slot in layout.slots),
        tuple((layer.id, layer.area, layer.color_token) for layer in layout.locked_layers),
        tuple(
            (group.kind, group.area, tuple(group.children)) for group in layout.scene_graph.groups
        ),
    )


def test_typographic_editorial_publishes_three_individual_compositions(brand_package):
    package = typographic_editorial_package(_ir(brand_package))

    assert package.id == "typographic-editorial"
    assert package.version == "1.0.0"
    assert [composition.id for composition in package.compositions] == [
        "typographic-ledger-post-4x5",
        "typographic-monument-post-4x5",
        "typographic-diptych-post-4x5",
    ]
    assert all(composition.layout.scene_graph for composition in package.compositions)
    assert all(composition.export_support.pptx == "native" for composition in package.compositions)


def test_compositions_have_distinct_structural_fingerprints(brand_package):
    package = typographic_editorial_package(_ir(brand_package))
    fingerprints = [_fingerprint(item.layout) for item in package.compositions]

    assert len(set(fingerprints)) == 3
    assert [len(item.layout.locked_layers) for item in package.compositions] == [5, 4, 4]
    assert [item.layout.scene_graph.groups[0].kind for item in package.compositions] == [
        "frame",
        "group",
        "grid",
    ]


def test_template_compilation_is_deterministic_and_does_not_share_state(brand_package):
    ir = _ir(brand_package)
    first = typographic_editorial_package(ir)
    second = typographic_editorial_package(ir)

    assert first.model_dump_json(by_alias=True) == second.model_dump_json(by_alias=True)
    first.compositions[0].layout.slots[0].area = (0, 0, 1, 1)
    assert second.compositions[0].layout.slots[0].area == (80, 78, 500, 36)


def test_template_publication_quality_gates_pass(brand_package):
    report = evaluate_template_package(typographic_editorial_package(_ir(brand_package)))

    assert report.passed, report.findings
    assert len(set(report.structural_signatures.values())) == 3
    assert len(report.pair_distances) == 3
    assert min(report.pair_distances.values()) >= 0.35
    assert report.delegated_checks == {"no-overflow": "renderer", "contrast": "guard"}


def test_template_samples_pass_guard_and_measured_renderer(brand_package, render_dist, tmp_path):
    ir = _ir(brand_package)
    package = typographic_editorial_package(ir)

    for composition in package.compositions:
        content = ContentSpec(
            layout_id=composition.id,
            brand_revision_id=ir.revision.id,
            values={
                slot_id: TextValue(text=text)
                for slot_id, text in composition.sample_content_pt.items()
            },
        )
        result = export_document(
            ir,
            composition.layout,
            content,
            brand_package,
            render_dist,
            tmp_path / f"{composition.id}.png",
        )

        assert result.out_path.stat().st_size > 0
        assert not [check for check in result.guard_verdict.checks if check.status == "blocked"]


def test_scene_graph_rejects_cycles_and_unknown_references(brand_package):
    package = typographic_editorial_package(_ir(brand_package))
    serialized = package.compositions[0].layout.model_dump(mode="json", by_alias=True)
    serialized["sceneGraph"]["groups"][1]["children"] = ["message-stack"]
    serialized["sceneGraph"]["groups"][2]["children"] = ["meta-stack"]
    with pytest.raises(ValueError, match="ciclos"):
        LayoutSpec.model_validate(serialized)

    serialized = package.compositions[0].layout.model_dump(mode="json", by_alias=True)
    serialized["sceneGraph"]["groups"][0]["children"].append("unknown-node")
    with pytest.raises(ValueError, match="desconhecidos"):
        LayoutSpec.model_validate(serialized)
