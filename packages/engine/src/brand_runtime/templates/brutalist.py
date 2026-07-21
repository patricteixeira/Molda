"""Família de brutalismo tipográfico: massa, corte e confronto."""

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

PACKAGE_ID = "typographic-brutalist"
PACKAGE_VERSION = "1.0.0"


def _ref(composition_id: str):
    return template_ref(PACKAGE_ID, PACKAGE_VERSION, composition_id)


def _manifesto(ir: BrandIR) -> LayoutSpec:
    layout_id = "brutalist-manifesto-post-4x5"
    return LayoutSpec(
        id=layout_id,
        profile="post-4x5",
        name_pt="Brutalismo tipográfico — Manifesto em bloco",
        canvas=POST_4X5_CANVAS,
        background=Background(kind="color", color_token="color.background"),
        template_ref=_ref(layout_id),
        locked_layers=[
            ShapeLayer(
                id="masthead-field",
                shape="rectangle",
                area=(0, 0, 1080, 158),
                color_token="color.primary",
                z_index=1,
            ),
            ShapeLayer(
                id="impact-field",
                shape="rectangle",
                area=(70, 332, 940, 438),
                color_token="color.primary",
                z_index=2,
            ),
            ShapeLayer(
                id="impact-shadow",
                shape="rectangle",
                area=(86, 786, 924, 16),
                color_token="color.text",
                opacity=0.18,
                z_index=1,
            ),
            ShapeLayer(
                id="lower-rule",
                shape="rectangle",
                area=(70, 1088, 940, 8),
                color_token="color.text",
                z_index=3,
            ),
            ShapeLayer(
                id="stamp",
                shape="circle",
                area=(878, 912, 132, 132),
                color_token="color.primary",
                opacity=0.14,
                z_index=1,
            ),
        ],
        slots=[
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                color_token="color.background",
                max_chars=54,
                area=(70, 58, 540, 38),
                fit="fixed",
                required=False,
                font_size_px=17,
                font_weight=700,
                text_transform="uppercase",
                letter_spacing_em=0.16,
                z_index=10,
            ),
            Slot(
                id="signature",
                kind="text",
                role="caption",
                color_token="color.background",
                max_chars=48,
                area=(704, 58, 306, 38),
                fit="fixed",
                required=False,
                font_size_px=15,
                font_weight=700,
                text_align="right",
                z_index=10,
            ),
            Slot(
                id="index",
                kind="text",
                role="heading",
                color_token="color.primary",
                max_chars=3,
                area=(70, 184, 270, 118),
                fit="fixed",
                font_size_px=96,
                font_weight=800,
                line_height=0.86,
                letter_spacing_em=-0.06,
                text_format="zero-padded",
                z_index=10,
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                color_token="color.background",
                max_chars=25,
                area=(104, 374, 846, 350),
                fit="fixed",
                font_size_px=132,
                font_weight=900,
                line_height=0.82,
                letter_spacing_em=-0.055,
                text_transform="uppercase",
                z_index=10,
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                max_chars=140,
                area=(70, 846, 650, 176),
                fit="fixed",
                required=False,
                font_size_px=29,
                font_weight=600,
                line_height=1.18,
                z_index=10,
            ),
            logo_slot(ir, (70, 1144, 136, 136)),
        ],
        scene_graph=SceneGraph(
            roots=["manifesto-root"],
            groups=[
                SceneGroup(
                    id="manifesto-root",
                    kind="frame",
                    area=(0, 0, 1080, 1350),
                    children=[
                        "masthead-field",
                        "impact-field",
                        "impact-shadow",
                        "lower-rule",
                        "stamp",
                        "masthead-stack",
                        "index",
                        "headline",
                        "body",
                        "logo",
                    ],
                ),
                SceneGroup(
                    id="masthead-stack",
                    kind="stack",
                    direction="horizontal",
                    gap_px=94,
                    area=(70, 58, 940, 38),
                    children=["kicker", "signature"],
                ),
            ],
        ),
    )


def _collision(ir: BrandIR) -> LayoutSpec:
    layout_id = "brutalist-collision-post-4x5"
    return LayoutSpec(
        id=layout_id,
        profile="post-4x5",
        name_pt="Brutalismo tipográfico — Colisão lateral",
        canvas=POST_4X5_CANVAS,
        background=Background(kind="color", color_token="color.background"),
        template_ref=_ref(layout_id),
        locked_layers=[
            ShapeLayer(
                id="left-field",
                shape="rectangle",
                area=(0, 0, 348, 1350),
                color_token="color.primary",
                z_index=1,
            ),
            ShapeLayer(
                id="headline-rule",
                shape="rectangle",
                area=(402, 174, 608, 12),
                color_token="color.text",
                z_index=2,
            ),
            ShapeLayer(
                id="collision-tab",
                shape="rectangle",
                area=(318, 654, 92, 214),
                color_token="color.text",
                z_index=3,
            ),
            ShapeLayer(
                id="footer-field",
                shape="rectangle",
                area=(348, 1206, 732, 144),
                color_token="color.primary",
                opacity=0.1,
                z_index=1,
            ),
        ],
        slots=[
            Slot(
                id="index",
                kind="text",
                role="heading",
                color_token="color.background",
                max_chars=3,
                area=(62, 90, 230, 244),
                fit="fixed",
                font_size_px=188,
                font_weight=900,
                line_height=0.82,
                letter_spacing_em=-0.08,
                text_format="zero-padded",
                z_index=10,
            ),
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                max_chars=54,
                area=(402, 92, 608, 42),
                fit="fixed",
                required=False,
                font_size_px=16,
                font_weight=700,
                text_transform="uppercase",
                letter_spacing_em=0.18,
                z_index=10,
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                color_token="color.primary",
                max_chars=34,
                area=(402, 236, 608, 450),
                fit="fixed",
                font_size_px=96,
                font_weight=900,
                line_height=0.9,
                letter_spacing_em=-0.05,
                z_index=10,
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                color_token="color.background",
                max_chars=130,
                area=(62, 702, 230, 310),
                fit="fixed",
                required=False,
                font_size_px=24,
                font_weight=600,
                line_height=1.18,
                z_index=10,
            ),
            Slot(
                id="signature",
                kind="text",
                role="caption",
                max_chars=48,
                area=(610, 1258, 400, 34),
                fit="fixed",
                required=False,
                font_size_px=15,
                font_weight=700,
                text_align="right",
                z_index=10,
            ),
            logo_slot(ir, (402, 1018, 148, 148)),
        ],
        scene_graph=SceneGraph(
            roots=["collision-root"],
            groups=[
                SceneGroup(
                    id="collision-root",
                    kind="grid",
                    columns=2,
                    gap_px=54,
                    area=(0, 0, 1080, 1350),
                    children=["left-panel", "right-panel", "collision-tab", "footer-field"],
                ),
                SceneGroup(
                    id="left-panel",
                    kind="frame",
                    area=(0, 0, 348, 1350),
                    children=["left-field", "index", "body"],
                ),
                SceneGroup(
                    id="right-panel",
                    kind="frame",
                    area=(348, 0, 732, 1350),
                    children=["headline-rule", "kicker", "headline", "logo", "signature"],
                ),
            ],
        ),
    )


def _bands(ir: BrandIR) -> LayoutSpec:
    layout_id = "brutalist-bands-post-4x5"
    return LayoutSpec(
        id=layout_id,
        profile="post-4x5",
        name_pt="Brutalismo tipográfico — Ritmo de faixas",
        canvas=POST_4X5_CANVAS,
        background=Background(kind="color", color_token="color.background"),
        template_ref=_ref(layout_id),
        locked_layers=[
            ShapeLayer(
                id="top-rule",
                shape="rectangle",
                area=(0, 148, 1080, 10),
                color_token="color.text",
                z_index=2,
            ),
            ShapeLayer(
                id="headline-band",
                shape="rectangle",
                area=(0, 276, 1080, 342),
                color_token="color.primary",
                z_index=1,
            ),
            ShapeLayer(
                id="counter-band",
                shape="rectangle",
                area=(0, 654, 446, 266),
                color_token="color.text",
                z_index=1,
            ),
            ShapeLayer(
                id="body-rule",
                shape="rectangle",
                area=(496, 920, 514, 6),
                color_token="color.primary",
                z_index=2,
            ),
            ShapeLayer(
                id="end-stop",
                shape="rectangle",
                area=(1010, 654, 70, 570),
                color_token="color.primary",
                opacity=0.16,
                z_index=1,
            ),
        ],
        slots=[
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                max_chars=54,
                area=(70, 72, 620, 38),
                fit="fixed",
                required=False,
                font_size_px=16,
                font_weight=800,
                text_transform="uppercase",
                letter_spacing_em=0.18,
                z_index=10,
            ),
            Slot(
                id="signature",
                kind="text",
                role="caption",
                max_chars=48,
                area=(728, 72, 282, 38),
                fit="fixed",
                required=False,
                font_size_px=15,
                font_weight=700,
                text_align="right",
                z_index=10,
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                color_token="color.background",
                max_chars=34,
                area=(70, 318, 940, 252),
                fit="fixed",
                font_size_px=104,
                font_weight=900,
                line_height=0.84,
                letter_spacing_em=-0.05,
                text_transform="uppercase",
                z_index=10,
            ),
            Slot(
                id="index",
                kind="text",
                role="heading",
                color_token="color.background",
                max_chars=3,
                area=(70, 692, 320, 184),
                fit="fixed",
                font_size_px=166,
                font_weight=900,
                line_height=0.82,
                letter_spacing_em=-0.07,
                text_format="zero-padded",
                z_index=10,
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                max_chars=140,
                area=(496, 962, 470, 186),
                fit="fixed",
                required=False,
                font_size_px=27,
                font_weight=600,
                line_height=1.2,
                z_index=10,
            ),
            logo_slot(ir, (70, 1134, 144, 144)),
        ],
        scene_graph=SceneGraph(
            roots=["bands-root"],
            groups=[
                SceneGroup(
                    id="bands-root",
                    kind="group",
                    area=(0, 0, 1080, 1350),
                    children=[
                        "top-rule",
                        "headline-band",
                        "counter-band",
                        "body-rule",
                        "end-stop",
                        "meta-stack",
                        "headline",
                        "index",
                        "body",
                        "logo",
                    ],
                ),
                SceneGroup(
                    id="meta-stack",
                    kind="stack",
                    direction="horizontal",
                    gap_px=38,
                    area=(70, 72, 940, 38),
                    children=["kicker", "signature"],
                ),
            ],
        ),
    )


def typographic_brutalist_package(ir: BrandIR) -> TemplatePackage:
    """Publica três arquiteturas de alto impacto sem rasterizar seus elementos."""
    style = derive_style_system(ir)
    layouts = (_manifesto(ir), _collision(ir), _bands(ir))
    samples = {
        "brutalist-manifesto-post-4x5": {
            "kicker": "Manifesto visual",
            "signature": "@sua-marca",
            "index": "1",
            "headline": "Ideias pedem presença.",
            "body": "Peso, corte e contraste transformam a mensagem em uma tomada de posição.",
        },
        "brutalist-collision-post-4x5": {
            "index": "2",
            "kicker": "Atrito como linguagem",
            "headline": "O espaço não precisa ser neutro.",
            "body": "Dois campos se chocam para construir uma leitura direta.",
            "signature": "@sua-marca",
        },
        "brutalist-bands-post-4x5": {
            "kicker": "Ritmo em alta tensão",
            "signature": "@sua-marca",
            "headline": "Cada faixa muda o pulso.",
            "index": "3",
            "body": "A sequência alterna massa, pausa e informação.",
        },
    }
    intents = {
        "brutalist-manifesto-post-4x5": (
            "Manifesto em bloco",
            "Transformar a mensagem central numa massa tipográfica frontal e incontornável.",
        ),
        "brutalist-collision-post-4x5": (
            "Colisão lateral",
            "Criar tensão por dois campos assimétricos que disputam peso e função.",
        ),
        "brutalist-bands-post-4x5": (
            "Ritmo de faixas",
            "Construir uma leitura sequencial por interrupções horizontais e mudanças de escala.",
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
        family="Brutalismo tipográfico",
        title_pt="Brutalismo tipográfico",
        description_pt=(
            "Três cartazes editáveis guiados por massa, corte, repetição e contraste físico."
        ),
        profiles=["post-4x5"],
        required_roles=list(style.typography),
        required_color_tokens=["color.background", "color.text", "color.primary"],
        compositions=compositions,
        evaluations=publication_evaluations(),
    )
