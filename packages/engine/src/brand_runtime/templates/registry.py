"""Registro interno v1 de famílias visuais autorais e compiláveis."""

from __future__ import annotations

from brand_runtime.ir.models import BrandIR
from brand_runtime.kit.models import (
    Background,
    Canvas,
    LayoutSpec,
    SceneGraph,
    SceneGroup,
    ShapeLayer,
    Slot,
    TemplateRef,
)
from brand_runtime.style.derive import derive_style_system
from brand_runtime.templates.models import (
    ExportSupport,
    TemplateComposition,
    TemplateEvaluation,
    TemplatePackage,
)

_PACKAGE_ID = "typographic-editorial"
_PACKAGE_VERSION = "1.0.0"
_CANVAS = Canvas(width_px=1080, height_px=1350, safe_area_px=48)


def _ref(composition_id: str) -> TemplateRef:
    return TemplateRef(
        package_id=_PACKAGE_ID,
        version=_PACKAGE_VERSION,
        composition_id=composition_id,
    )


def _logo(ir: BrandIR, area: tuple[int, int, int, int]) -> Slot:
    minimum = ir.assets["logo.primary"].min_width_px
    width = max(area[2], minimum)
    height = max(area[3], minimum)
    return Slot(
        id="logo",
        kind="logo",
        area=(area[0], area[1], width, height),
        fit="fixed",
        asset_token="logo.primary",
        z_index=12,
    )


def _ledger(ir: BrandIR) -> LayoutSpec:
    layout_id = "typographic-ledger-post-4x5"
    return LayoutSpec(
        id=layout_id,
        profile="post-4x5",
        name_pt="Tipográfico editorial — Caderno assimétrico",
        canvas=_CANVAS,
        background=Background(kind="color", color_token="color.background"),
        template_ref=_ref(layout_id),
        locked_layers=[
            ShapeLayer(
                id="rail",
                shape="rectangle",
                area=(0, 0, 28, 1350),
                color_token="color.primary",
                z_index=1,
            ),
            ShapeLayer(
                id="top-rule",
                shape="rectangle",
                area=(80, 142, 920, 2),
                color_token="color.text",
                opacity=0.28,
                z_index=2,
            ),
            ShapeLayer(
                id="index-field",
                shape="rectangle",
                area=(80, 190, 174, 786),
                color_token="color.primary",
                opacity=0.06,
                z_index=1,
            ),
            ShapeLayer(
                id="accent-rule",
                shape="rectangle",
                area=(286, 618, 96, 6),
                color_token="color.primary",
                z_index=3,
            ),
            ShapeLayer(
                id="footer-rule",
                shape="rectangle",
                area=(80, 1128, 920, 2),
                color_token="color.text",
                opacity=0.28,
                z_index=2,
            ),
        ],
        slots=[
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                area=(80, 78, 500, 36),
                fit="fixed",
                required=False,
                font_size_px=16,
                text_transform="uppercase",
                letter_spacing_em=0.18,
                z_index=10,
            ),
            Slot(
                id="signature",
                kind="text",
                role="caption",
                area=(700, 78, 300, 36),
                fit="fixed",
                required=False,
                font_size_px=14,
                text_align="right",
                letter_spacing_em=0.08,
                z_index=10,
            ),
            Slot(
                id="index",
                kind="text",
                role="heading",
                color_token="color.primary",
                area=(94, 210, 340, 210),
                fit="fixed",
                font_size_px=172,
                line_height=0.84,
                letter_spacing_em=-0.06,
                z_index=6,
                text_format="zero-padded",
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                color_token="color.primary",
                area=(286, 214, 694, 390),
                fit="fixed",
                font_size_px=116,
                line_height=0.9,
                letter_spacing_em=-0.045,
                z_index=10,
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                area=(286, 668, 548, 170),
                fit="fixed",
                required=False,
                font_size_px=28,
                line_height=1.26,
                z_index=10,
            ),
            _logo(ir, (864, 1164, 116, 116)),
        ],
        scene_graph=SceneGraph(
            roots=["ledger-root"],
            groups=[
                SceneGroup(
                    id="ledger-root",
                    kind="frame",
                    area=(0, 0, 1080, 1350),
                    children=[
                        "rail",
                        "top-rule",
                        "index-field",
                        "accent-rule",
                        "footer-rule",
                        "meta-stack",
                        "message-stack",
                        "index",
                        "logo",
                    ],
                ),
                SceneGroup(
                    id="meta-stack",
                    kind="stack",
                    direction="horizontal",
                    gap_px=120,
                    area=(80, 78, 920, 36),
                    children=["kicker", "signature"],
                ),
                SceneGroup(
                    id="message-stack",
                    kind="stack",
                    direction="vertical",
                    gap_px=64,
                    area=(286, 214, 694, 624),
                    children=["headline", "body"],
                ),
            ],
        ),
    )


def _monument(ir: BrandIR) -> LayoutSpec:
    layout_id = "typographic-monument-post-4x5"
    return LayoutSpec(
        id=layout_id,
        profile="post-4x5",
        name_pt="Tipográfico editorial — Margem monumental",
        canvas=_CANVAS,
        background=Background(kind="color", color_token="color.background"),
        template_ref=_ref(layout_id),
        locked_layers=[
            ShapeLayer(
                id="quiet-field",
                shape="rectangle",
                area=(0, 0, 312, 1350),
                color_token="color.primary",
                opacity=0.055,
                z_index=0,
            ),
            ShapeLayer(
                id="top-rule",
                shape="rectangle",
                area=(78, 74, 924, 2),
                color_token="color.text",
                opacity=0.24,
                z_index=2,
            ),
            ShapeLayer(
                id="closing-field",
                shape="rectangle",
                area=(0, 1262, 1080, 88),
                color_token="color.primary",
                z_index=1,
            ),
            ShapeLayer(
                id="accent-square",
                shape="rectangle",
                area=(78, 690, 18, 18),
                color_token="color.primary",
                z_index=4,
            ),
        ],
        slots=[
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                area=(78, 96, 470, 34),
                fit="fixed",
                required=False,
                font_size_px=15,
                text_transform="uppercase",
                letter_spacing_em=0.2,
                z_index=10,
            ),
            Slot(
                id="index",
                kind="text",
                role="heading",
                color_token="color.primary",
                area=(18, 160, 880, 430),
                fit="fixed",
                font_size_px=382,
                line_height=0.78,
                letter_spacing_em=-0.08,
                opacity=0.075,
                fill_mode="stroke",
                stroke_color_token="color.primary",
                stroke_width_px=2,
                text_format="zero-padded",
                z_index=2,
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                color_token="color.primary",
                area=(78, 730, 904, 340),
                fit="fixed",
                font_size_px=122,
                line_height=0.88,
                letter_spacing_em=-0.05,
                z_index=10,
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                area=(600, 1092, 382, 96),
                fit="fixed",
                required=False,
                font_size_px=22,
                line_height=1.3,
                text_align="right",
                z_index=10,
            ),
            Slot(
                id="signature",
                kind="text",
                role="caption",
                color_token="color.background",
                area=(78, 1287, 520, 28),
                fit="fixed",
                required=False,
                font_size_px=14,
                letter_spacing_em=0.08,
                z_index=10,
            ),
            _logo(ir, (882, 94, 100, 100)),
        ],
        scene_graph=SceneGraph(
            roots=["monument-root"],
            groups=[
                SceneGroup(
                    id="monument-root",
                    kind="group",
                    area=(0, 0, 1080, 1350),
                    children=[
                        "quiet-field",
                        "top-rule",
                        "closing-field",
                        "accent-square",
                        "upper-frame",
                        "message-stack",
                        "body",
                        "signature",
                    ],
                ),
                SceneGroup(
                    id="upper-frame",
                    kind="frame",
                    area=(18, 94, 964, 496),
                    children=["kicker", "index", "logo"],
                ),
                SceneGroup(
                    id="message-stack",
                    kind="stack",
                    direction="vertical",
                    gap_px=40,
                    area=(78, 690, 904, 350),
                    children=["headline"],
                ),
            ],
        ),
    )


def _diptych(ir: BrandIR) -> LayoutSpec:
    layout_id = "typographic-diptych-post-4x5"
    return LayoutSpec(
        id=layout_id,
        profile="post-4x5",
        name_pt="Tipográfico editorial — Díptico de contraste",
        canvas=_CANVAS,
        background=Background(kind="color", color_token="color.background"),
        template_ref=_ref(layout_id),
        locked_layers=[
            ShapeLayer(
                id="contrast-field",
                shape="rectangle",
                area=(676, 0, 404, 1350),
                color_token="color.primary",
                z_index=1,
            ),
            ShapeLayer(
                id="spine",
                shape="rectangle",
                area=(650, 0, 26, 1350),
                color_token="color.text",
                opacity=0.14,
                z_index=2,
            ),
            ShapeLayer(
                id="left-rule",
                shape="rectangle",
                area=(80, 166, 510, 2),
                color_token="color.text",
                opacity=0.25,
                z_index=2,
            ),
            ShapeLayer(
                id="right-rule",
                shape="rectangle",
                area=(730, 954, 296, 2),
                color_token="color.background",
                opacity=0.42,
                z_index=3,
            ),
        ],
        slots=[
            Slot(
                id="signature",
                kind="text",
                role="caption",
                area=(320, 74, 440, 32),
                fit="fixed",
                required=False,
                font_size_px=14,
                text_align="center",
                letter_spacing_em=0.09,
                z_index=10,
            ),
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                area=(80, 112, 510, 34),
                fit="fixed",
                required=False,
                font_size_px=15,
                text_transform="uppercase",
                letter_spacing_em=0.19,
                z_index=10,
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                color_token="color.primary",
                area=(80, 244, 510, 560),
                fit="fixed",
                font_size_px=112,
                line_height=0.92,
                letter_spacing_em=-0.04,
                z_index=10,
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                color_token="color.background",
                area=(730, 264, 296, 286),
                fit="fixed",
                required=False,
                font_size_px=26,
                line_height=1.28,
                z_index=10,
            ),
            Slot(
                id="index",
                kind="text",
                role="heading",
                color_token="color.background",
                area=(730, 1010, 296, 156),
                fit="fixed",
                font_size_px=138,
                line_height=0.86,
                text_align="right",
                letter_spacing_em=-0.05,
                text_format="zero-padded",
                z_index=10,
            ),
            _logo(ir, (80, 1120, 126, 126)),
        ],
        scene_graph=SceneGraph(
            roots=["diptych-root"],
            groups=[
                SceneGroup(
                    id="diptych-root",
                    kind="grid",
                    columns=2,
                    gap_px=26,
                    area=(0, 0, 1080, 1350),
                    children=["left-panel", "right-panel", "spine", "signature"],
                ),
                SceneGroup(
                    id="left-panel",
                    kind="frame",
                    area=(0, 0, 650, 1350),
                    children=["left-rule", "kicker", "headline", "logo"],
                ),
                SceneGroup(
                    id="right-panel",
                    kind="frame",
                    area=(676, 0, 404, 1350),
                    children=["contrast-field", "right-rule", "body", "index"],
                ),
            ],
        ),
    )


def typographic_editorial_package(ir: BrandIR) -> TemplatePackage:
    """Compila três arquiteturas individuais usando somente tokens confirmados."""
    style = derive_style_system(ir)
    layouts = (_ledger(ir), _monument(ir), _diptych(ir))
    samples = {
        "typographic-ledger-post-4x5": {
            "kicker": "Sistema visual em uso",
            "signature": "@sua-marca",
            "index": "1",
            "headline": "Forma também é argumento.",
            "body": "Uma composição que organiza contexto, voz e presença sem reduzir a mensagem a um molde.",
        },
        "typographic-monument-post-4x5": {
            "kicker": "Uma ideia, sem ruído",
            "index": "2",
            "headline": "O essencial pode ocupar espaço.",
            "body": "Silêncio e escala constroem a hierarquia.",
            "signature": "@sua-marca",
        },
        "typographic-diptych-post-4x5": {
            "signature": "@sua-marca",
            "kicker": "Contraste como estrutura",
            "headline": "Duas tensões. Uma só voz.",
            "body": "O campo secundário sustenta contexto, ritmo e continuidade.",
            "index": "3",
        },
    }
    intents = {
        "typographic-ledger-post-4x5": (
            "Caderno assimétrico",
            "Organizar uma mensagem editorial densa com trilho, índice e metadados claros.",
        ),
        "typographic-monument-post-4x5": (
            "Margem monumental",
            "Criar presença por escala extrema, grande área de silêncio e fechamento ancorado.",
        ),
        "typographic-diptych-post-4x5": (
            "Díptico de contraste",
            "Separar argumento e contexto em dois campos cromáticos deliberadamente desiguais.",
        ),
    }
    compositions = []
    for layout in layouts:
        name, intent = intents[layout.id]
        compositions.append(
            TemplateComposition(
                id=layout.id,
                name_pt=name,
                intent_pt=intent,
                layout=layout,
                sample_content_pt=samples[layout.id],
                critical_nodes=["headline", "logo"],
                export_support=ExportSupport(pptx="native"),
            )
        )

    return TemplatePackage(
        id=_PACKAGE_ID,
        version=_PACKAGE_VERSION,
        family="Tipográfico Editorial",
        title_pt="Tipográfico Editorial",
        description_pt=(
            "Três composições individuais com esqueletos distintos, tipografia em escala e "
            "estrutura preservada para edição."
        ),
        profiles=["post-4x5"],
        required_roles=list(style.typography),
        required_color_tokens=["color.background", "color.text", "color.primary"],
        compositions=compositions,
        evaluations=[
            TemplateEvaluation(kind="no-overflow", stage="renderer"),
            TemplateEvaluation(kind="safe-area"),
            TemplateEvaluation(kind="contrast", stage="guard"),
            TemplateEvaluation(kind="type-hierarchy", minimum=2.5),
            TemplateEvaluation(kind="negative-space", minimum=0.12, maximum=0.72),
            TemplateEvaluation(kind="structural-distance", minimum=0.35),
        ],
    )


def generate_template_layouts(ir: BrandIR) -> list[LayoutSpec]:
    """Devolve cópias dos layouts compilados para o catálogo público atual."""
    package = typographic_editorial_package(ir)
    return [composition.layout.model_copy(deep=True) for composition in package.compositions]
