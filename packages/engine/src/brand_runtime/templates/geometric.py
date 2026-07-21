"""Família de modernismo geométrico: módulo, órbita e contraponto."""

from __future__ import annotations

from brand_runtime.ir.models import BrandIR
from brand_runtime.kit.models import (
    Background,
    LayoutSpec,
    SceneGraph,
    SceneGroup,
    ShapeLayer,
    Slot,
)
from brand_runtime.style.derive import derive_style_system
from brand_runtime.templates.foundations import (
    POST_4X5_CANVAS,
    logo_slot,
    publication_evaluations,
    template_ref,
)
from brand_runtime.templates.models import ExportSupport, TemplateComposition, TemplatePackage

PACKAGE_ID = "geometric-modernism"
PACKAGE_VERSION = "1.0.0"


def _ref(composition_id: str):
    return template_ref(PACKAGE_ID, PACKAGE_VERSION, composition_id)


def _orbit(ir: BrandIR) -> LayoutSpec:
    layout_id = "geometric-orbit-post-4x5"
    return LayoutSpec(
        id=layout_id,
        profile="post-4x5",
        name_pt="Modernismo geométrico — Órbita construtiva",
        canvas=POST_4X5_CANVAS,
        background=Background(kind="color", color_token="color.background"),
        template_ref=_ref(layout_id),
        locked_layers=[
            ShapeLayer(
                id="orbit-main",
                shape="circle",
                area=(548, 140, 442, 442),
                color_token="color.primary",
                z_index=2,
            ),
            ShapeLayer(
                id="orbit-counter",
                shape="circle",
                area=(694, 286, 150, 150),
                color_token="color.background",
                z_index=3,
            ),
            ShapeLayer(
                id="horizontal-axis",
                shape="rectangle",
                area=(82, 620, 916, 5),
                color_token="color.text",
                z_index=2,
            ),
            ShapeLayer(
                id="vertical-axis",
                shape="rectangle",
                area=(530, 140, 5, 1090),
                color_token="color.text",
                opacity=0.28,
                z_index=1,
            ),
            ShapeLayer(
                id="information-module",
                shape="rectangle",
                area=(82, 1002, 342, 208),
                color_token="color.primary",
                z_index=2,
            ),
        ],
        slots=[
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                max_chars=48,
                area=(82, 82, 400, 36),
                fit="fixed",
                required=False,
                font_size_px=15,
                font_weight=700,
                text_transform="uppercase",
                letter_spacing_em=0.18,
                z_index=10,
            ),
            Slot(
                id="signature",
                kind="text",
                role="caption",
                color_token="color.background",
                max_chars=42,
                area=(660, 196, 250, 34),
                fit="fixed",
                required=False,
                font_size_px=14,
                font_weight=700,
                text_align="center",
                letter_spacing_em=0.06,
                z_index=10,
            ),
            Slot(
                id="index",
                kind="text",
                role="heading",
                color_token="color.background",
                max_chars=3,
                area=(600, 348, 290, 112),
                fit="fixed",
                font_size_px=92,
                font_weight=800,
                text_align="center",
                line_height=0.86,
                letter_spacing_em=-0.05,
                text_format="zero-padded",
                z_index=10,
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                max_chars=38,
                area=(82, 680, 850, 280),
                fit="fixed",
                font_size_px=104,
                font_weight=750,
                line_height=0.92,
                letter_spacing_em=-0.045,
                z_index=10,
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                color_token="color.background",
                max_chars=112,
                area=(90, 1018, 326, 178),
                fit="fixed",
                required=False,
                font_size_px=23,
                font_weight=600,
                line_height=1.16,
                z_index=10,
            ),
            logo_slot(ir, (842, 1084, 142, 142)),
        ],
        scene_graph=SceneGraph(
            roots=["orbit-root"],
            groups=[
                SceneGroup(
                    id="orbit-root",
                    kind="frame",
                    area=(0, 0, 1080, 1350),
                    children=[
                        "orbit-main",
                        "orbit-counter",
                        "horizontal-axis",
                        "vertical-axis",
                        "information-module",
                        "meta-row",
                        "index",
                        "headline",
                        "body",
                        "logo",
                    ],
                ),
                SceneGroup(
                    id="meta-row",
                    kind="stack",
                    direction="horizontal",
                    gap_px=178,
                    area=(82, 82, 828, 148),
                    children=["kicker", "signature"],
                ),
            ],
        ),
    )


def _staircase(ir: BrandIR) -> LayoutSpec:
    layout_id = "geometric-staircase-post-4x5"
    return LayoutSpec(
        id=layout_id,
        profile="post-4x5",
        name_pt="Modernismo geométrico — Escada modular",
        canvas=POST_4X5_CANVAS,
        background=Background(kind="color", color_token="color.background"),
        template_ref=_ref(layout_id),
        locked_layers=[
            ShapeLayer(
                id="step-one",
                shape="rectangle",
                area=(78, 760, 214, 420),
                color_token="color.primary",
                opacity=0.16,
                z_index=1,
            ),
            ShapeLayer(
                id="step-two",
                shape="rectangle",
                area=(292, 642, 214, 538),
                color_token="color.primary",
                opacity=0.34,
                z_index=1,
            ),
            ShapeLayer(
                id="step-three",
                shape="rectangle",
                area=(506, 524, 214, 656),
                color_token="color.primary",
                opacity=0.62,
                z_index=1,
            ),
            ShapeLayer(
                id="step-four",
                shape="rectangle",
                area=(720, 406, 282, 774),
                color_token="color.primary",
                z_index=1,
            ),
            ShapeLayer(
                id="top-marker",
                shape="circle",
                area=(924, 86, 78, 78),
                color_token="color.primary",
                z_index=2,
            ),
        ],
        slots=[
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                max_chars=48,
                area=(78, 82, 482, 38),
                fit="fixed",
                required=False,
                font_size_px=15,
                font_weight=700,
                text_transform="uppercase",
                letter_spacing_em=0.18,
                z_index=10,
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                max_chars=36,
                area=(78, 190, 640, 276),
                fit="fixed",
                font_size_px=96,
                font_weight=760,
                line_height=0.92,
                letter_spacing_em=-0.045,
                z_index=10,
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                max_chars=128,
                area=(78, 516, 404, 190),
                fit="fixed",
                required=False,
                font_size_px=24,
                line_height=1.22,
                z_index=10,
            ),
            Slot(
                id="index",
                kind="text",
                role="heading",
                color_token="color.background",
                max_chars=3,
                area=(752, 650, 218, 222),
                fit="fixed",
                font_size_px=170,
                font_weight=850,
                text_align="right",
                line_height=0.86,
                letter_spacing_em=-0.07,
                text_format="zero-padded",
                z_index=10,
            ),
            Slot(
                id="signature",
                kind="text",
                role="caption",
                color_token="color.background",
                max_chars=42,
                area=(752, 1072, 218, 34),
                fit="fixed",
                required=False,
                font_size_px=14,
                font_weight=700,
                text_align="right",
                z_index=10,
            ),
            logo_slot(ir, (78, 1168, 132, 132)),
        ],
        scene_graph=SceneGraph(
            roots=["stair-root"],
            groups=[
                SceneGroup(
                    id="stair-root",
                    kind="grid",
                    columns=4,
                    gap_px=0,
                    area=(78, 82, 924, 1248),
                    children=[
                        "step-one",
                        "step-two",
                        "step-three",
                        "step-four",
                        "top-marker",
                        "message-stack",
                        "index",
                        "signature",
                        "logo",
                    ],
                ),
                SceneGroup(
                    id="message-stack",
                    kind="stack",
                    direction="vertical",
                    gap_px=64,
                    area=(78, 82, 640, 616),
                    children=["kicker", "headline", "body"],
                ),
            ],
        ),
    )


def _signal(ir: BrandIR) -> LayoutSpec:
    layout_id = "geometric-signal-post-4x5"
    return LayoutSpec(
        id=layout_id,
        profile="post-4x5",
        name_pt="Modernismo geométrico — Sinal e contraponto",
        canvas=POST_4X5_CANVAS,
        background=Background(kind="color", color_token="color.background"),
        template_ref=_ref(layout_id),
        locked_layers=[
            ShapeLayer(
                id="vertical-signal",
                shape="rectangle",
                area=(78, 74, 176, 1202),
                color_token="color.primary",
                z_index=2,
            ),
            ShapeLayer(
                id="signal-circle-large",
                shape="circle",
                area=(344, 148, 294, 294),
                color_token="color.primary",
                opacity=0.22,
                z_index=1,
            ),
            ShapeLayer(
                id="signal-circle-medium",
                shape="circle",
                area=(606, 238, 176, 176),
                color_token="color.primary",
                opacity=0.52,
                z_index=2,
            ),
            ShapeLayer(
                id="signal-circle-small",
                shape="circle",
                area=(806, 306, 92, 92),
                color_token="color.primary",
                z_index=3,
            ),
            ShapeLayer(
                id="lower-rule",
                shape="rectangle",
                area=(344, 1008, 658, 5),
                color_token="color.text",
                z_index=2,
            ),
        ],
        slots=[
            Slot(
                id="index",
                kind="text",
                role="heading",
                color_token="color.background",
                max_chars=3,
                area=(98, 114, 136, 152),
                fit="fixed",
                font_size_px=104,
                font_weight=850,
                text_align="center",
                line_height=0.88,
                text_format="zero-padded",
                z_index=10,
            ),
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                color_token="color.background",
                max_chars=30,
                area=(102, 580, 128, 176),
                fit="fixed",
                required=False,
                font_size_px=17,
                font_weight=700,
                line_height=1.12,
                text_align="center",
                text_transform="uppercase",
                letter_spacing_em=0.12,
                z_index=10,
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                max_chars=40,
                area=(344, 506, 658, 326),
                fit="fixed",
                font_size_px=100,
                font_weight=760,
                line_height=0.93,
                letter_spacing_em=-0.045,
                z_index=10,
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                max_chars=144,
                area=(344, 866, 520, 126),
                fit="fixed",
                required=False,
                font_size_px=24,
                line_height=1.2,
                z_index=10,
            ),
            Slot(
                id="signature",
                kind="text",
                role="caption",
                max_chars=42,
                area=(344, 1072, 396, 34),
                fit="fixed",
                required=False,
                font_size_px=14,
                font_weight=700,
                letter_spacing_em=0.05,
                z_index=10,
            ),
            logo_slot(ir, (860, 1128, 142, 142)),
        ],
        scene_graph=SceneGraph(
            roots=["signal-root"],
            groups=[
                SceneGroup(
                    id="signal-root",
                    kind="group",
                    area=(78, 74, 924, 1202),
                    children=[
                        "vertical-signal",
                        "orbit-sequence",
                        "lower-rule",
                        "index",
                        "kicker",
                        "message-stack",
                        "signature",
                        "logo",
                    ],
                ),
                SceneGroup(
                    id="orbit-sequence",
                    kind="stack",
                    direction="horizontal",
                    gap_px=24,
                    area=(344, 148, 554, 294),
                    children=[
                        "signal-circle-large",
                        "signal-circle-medium",
                        "signal-circle-small",
                    ],
                ),
                SceneGroup(
                    id="message-stack",
                    kind="stack",
                    direction="vertical",
                    gap_px=34,
                    area=(344, 506, 658, 486),
                    children=["headline", "body"],
                ),
            ],
        ),
    )


def geometric_modernism_package(ir: BrandIR) -> TemplatePackage:
    """Publica três construções editáveis baseadas em forma e proporção."""
    style = derive_style_system(ir)
    layouts = (_orbit(ir), _staircase(ir), _signal(ir))
    samples = {
        "geometric-orbit-post-4x5": {
            "kicker": "Forma em movimento",
            "signature": "@sua-marca",
            "index": "1",
            "headline": "Toda ideia encontra seu eixo.",
            "body": "Círculo, linha e módulo organizam uma mensagem de leitura imediata.",
        },
        "geometric-staircase-post-4x5": {
            "kicker": "Progresso por módulos",
            "headline": "Um passo muda a escala do próximo.",
            "body": "A construção cresce em ritmo, peso e presença.",
            "index": "2",
            "signature": "@sua-marca",
        },
        "geometric-signal-post-4x5": {
            "index": "3",
            "kicker": "Sistema vivo",
            "headline": "A forma também orienta a leitura.",
            "body": "Contrapontos geométricos criam direção sem depender de ornamento.",
            "signature": "@sua-marca",
        },
    }
    intents = {
        "geometric-orbit-post-4x5": (
            "Órbita construtiva",
            "Equilibrar um centro circular dominante com eixos e módulos de informação.",
        ),
        "geometric-staircase-post-4x5": (
            "Escada modular",
            "Materializar progressão por blocos ascendentes e mudanças graduais de densidade.",
        ),
        "geometric-signal-post-4x5": (
            "Sinal e contraponto",
            "Conduzir o olhar por uma baliza vertical e uma sequência de círculos proporcionais.",
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
        id=PACKAGE_ID,
        version=PACKAGE_VERSION,
        family="Modernismo geométrico",
        title_pt="Modernismo geométrico",
        description_pt=(
            "Três sistemas editáveis construídos por órbitas, módulos, progressão e contraponto."
        ),
        profiles=["post-4x5"],
        required_roles=list(style.typography),
        required_color_tokens=["color.background", "color.text", "color.primary"],
        compositions=compositions,
        evaluations=publication_evaluations(),
    )
