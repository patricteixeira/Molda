"""Família de sistema suíço: grade, ritmo, precisão e silêncio."""

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

PACKAGE_ID = "swiss-system"
PACKAGE_VERSION = "1.0.0"


def _ref(composition_id: str):
    return template_ref(PACKAGE_ID, PACKAGE_VERSION, composition_id)


def _grid_lines() -> list[ShapeLayer]:
    return [
        ShapeLayer(
            id=f"grid-line-{index}",
            shape="rectangle",
            area=(80 + index * 155, 74, 1, 1202),
            color_token="color.text",
            opacity=0.1,
            z_index=1,
        )
        for index in range(7)
    ]


def _rational_grid(ir: BrandIR) -> LayoutSpec:
    layout_id = "swiss-rational-grid-post-4x5"
    return LayoutSpec(
        id=layout_id,
        profile="post-4x5",
        name_pt="Sistema suíço — Grade racional",
        canvas=POST_4X5_CANVAS,
        background=Background(kind="color", color_token="color.background"),
        template_ref=_ref(layout_id),
        locked_layers=[
            *_grid_lines(),
            ShapeLayer(
                id="top-rule",
                shape="rectangle",
                area=(80, 74, 930, 2),
                color_token="color.text",
                z_index=2,
            ),
            ShapeLayer(
                id="accent-square",
                shape="rectangle",
                area=(80, 196, 28, 28),
                color_token="color.primary",
                z_index=3,
            ),
            ShapeLayer(
                id="footer-rule",
                shape="rectangle",
                area=(80, 1274, 930, 2),
                color_token="color.text",
                z_index=2,
            ),
        ],
        slots=[
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                max_chars=54,
                area=(122, 192, 484, 40),
                fit="fixed",
                required=False,
                font_size_px=15,
                text_transform="uppercase",
                letter_spacing_em=0.18,
                z_index=10,
            ),
            Slot(
                id="signature",
                kind="text",
                role="caption",
                max_chars=48,
                area=(700, 192, 310, 40),
                fit="fixed",
                required=False,
                font_size_px=14,
                text_align="right",
                letter_spacing_em=0.06,
                z_index=10,
            ),
            Slot(
                id="index",
                kind="text",
                role="heading",
                color_token="color.primary",
                max_chars=3,
                area=(80, 318, 240, 116),
                fit="fixed",
                font_size_px=88,
                font_weight=700,
                line_height=0.9,
                letter_spacing_em=-0.04,
                text_format="zero-padded",
                z_index=10,
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                max_chars=38,
                area=(390, 318, 620, 360),
                fit="fixed",
                font_size_px=98,
                font_weight=700,
                line_height=0.94,
                letter_spacing_em=-0.035,
                z_index=10,
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                max_chars=150,
                area=(545, 780, 465, 274),
                fit="fixed",
                required=False,
                font_size_px=25,
                line_height=1.36,
                z_index=10,
            ),
            logo_slot(ir, (80, 1124, 112, 112)),
        ],
        scene_graph=SceneGraph(
            roots=["rational-grid-root"],
            groups=[
                SceneGroup(
                    id="rational-grid-root",
                    kind="grid",
                    columns=6,
                    gap_px=0,
                    area=(80, 74, 930, 1202),
                    children=[
                        *(f"grid-line-{index}" for index in range(7)),
                        "top-rule",
                        "accent-square",
                        "footer-rule",
                        "kicker",
                        "signature",
                        "index",
                        "headline",
                        "body",
                        "logo",
                    ],
                )
            ],
        ),
    )


def _quiet_axis(ir: BrandIR) -> LayoutSpec:
    layout_id = "swiss-quiet-axis-post-4x5"
    return LayoutSpec(
        id=layout_id,
        profile="post-4x5",
        name_pt="Sistema suíço — Eixo de silêncio",
        canvas=POST_4X5_CANVAS,
        background=Background(kind="color", color_token="color.background"),
        template_ref=_ref(layout_id),
        locked_layers=[
            ShapeLayer(
                id="vertical-axis",
                shape="rectangle",
                area=(300, 80, 2, 1190),
                color_token="color.text",
                opacity=0.22,
                z_index=2,
            ),
            ShapeLayer(
                id="accent-marker",
                shape="rectangle",
                area=(282, 246, 38, 38),
                color_token="color.primary",
                z_index=3,
            ),
            ShapeLayer(
                id="body-rule",
                shape="rectangle",
                area=(366, 908, 586, 2),
                color_token="color.text",
                opacity=0.28,
                z_index=2,
            ),
            ShapeLayer(
                id="footer-index-field",
                shape="rectangle",
                area=(80, 1090, 222, 180),
                color_token="color.primary",
                opacity=0.08,
                z_index=1,
            ),
        ],
        slots=[
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                max_chars=54,
                area=(366, 84, 586, 38),
                fit="fixed",
                required=False,
                font_size_px=15,
                text_transform="uppercase",
                letter_spacing_em=0.2,
                z_index=10,
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                max_chars=40,
                area=(366, 246, 586, 430),
                fit="fixed",
                font_size_px=92,
                font_weight=700,
                line_height=0.98,
                letter_spacing_em=-0.03,
                z_index=10,
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                max_chars=160,
                area=(366, 952, 586, 222),
                fit="fixed",
                required=False,
                font_size_px=24,
                line_height=1.4,
                z_index=10,
            ),
            Slot(
                id="index",
                kind="text",
                role="heading",
                color_token="color.primary",
                max_chars=3,
                area=(96, 1120, 190, 116),
                fit="fixed",
                font_size_px=86,
                font_weight=700,
                line_height=0.9,
                text_format="zero-padded",
                z_index=10,
            ),
            Slot(
                id="signature",
                kind="text",
                role="caption",
                max_chars=48,
                area=(366, 1222, 390, 30),
                fit="fixed",
                required=False,
                font_size_px=14,
                letter_spacing_em=0.08,
                z_index=10,
            ),
            logo_slot(ir, (80, 80, 112, 112)),
        ],
        scene_graph=SceneGraph(
            roots=["quiet-root"],
            groups=[
                SceneGroup(
                    id="quiet-root",
                    kind="frame",
                    area=(80, 80, 872, 1190),
                    children=[
                        "vertical-axis",
                        "accent-marker",
                        "body-rule",
                        "footer-index-field",
                        "copy-stack",
                        "index",
                        "signature",
                        "logo",
                    ],
                ),
                SceneGroup(
                    id="copy-stack",
                    kind="stack",
                    direction="vertical",
                    gap_px=246,
                    area=(366, 246, 586, 928),
                    children=["headline", "body"],
                ),
            ],
        ),
    )


def _modular_field(ir: BrandIR) -> LayoutSpec:
    layout_id = "swiss-modular-field-post-4x5"
    return LayoutSpec(
        id=layout_id,
        profile="post-4x5",
        name_pt="Sistema suíço — Campo modular",
        canvas=POST_4X5_CANVAS,
        background=Background(kind="color", color_token="color.background"),
        template_ref=_ref(layout_id),
        locked_layers=[
            ShapeLayer(
                id="module-a",
                shape="rectangle",
                area=(80, 80, 278, 278),
                color_token="color.primary",
                opacity=0.08,
                z_index=1,
            ),
            ShapeLayer(
                id="module-b",
                shape="rectangle",
                area=(390, 80, 620, 2),
                color_token="color.text",
                z_index=2,
            ),
            ShapeLayer(
                id="module-c",
                shape="rectangle",
                area=(80, 640, 930, 2),
                color_token="color.text",
                opacity=0.26,
                z_index=2,
            ),
            ShapeLayer(
                id="module-d",
                shape="rectangle",
                area=(700, 698, 310, 478),
                color_token="color.primary",
                opacity=0.07,
                z_index=1,
            ),
            ShapeLayer(
                id="accent-bar",
                shape="rectangle",
                area=(80, 1220, 930, 12),
                color_token="color.primary",
                z_index=3,
            ),
        ],
        slots=[
            Slot(
                id="index",
                kind="text",
                role="heading",
                color_token="color.primary",
                max_chars=3,
                area=(108, 112, 220, 164),
                fit="fixed",
                font_size_px=126,
                font_weight=700,
                line_height=0.88,
                letter_spacing_em=-0.05,
                text_format="zero-padded",
                z_index=10,
            ),
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                max_chars=54,
                area=(390, 122, 620, 38),
                fit="fixed",
                required=False,
                font_size_px=15,
                text_transform="uppercase",
                letter_spacing_em=0.18,
                z_index=10,
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                max_chars=38,
                area=(390, 228, 620, 342),
                fit="fixed",
                font_size_px=92,
                font_weight=700,
                line_height=0.96,
                letter_spacing_em=-0.035,
                z_index=10,
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                max_chars=160,
                area=(80, 714, 526, 302),
                fit="fixed",
                required=False,
                font_size_px=25,
                line_height=1.38,
                z_index=10,
            ),
            Slot(
                id="signature",
                kind="text",
                role="caption",
                max_chars=48,
                area=(700, 1090, 310, 34),
                fit="fixed",
                required=False,
                font_size_px=14,
                text_align="right",
                letter_spacing_em=0.08,
                z_index=10,
            ),
            logo_slot(ir, (80, 1066, 112, 112)),
        ],
        scene_graph=SceneGraph(
            roots=["modular-root"],
            groups=[
                SceneGroup(
                    id="modular-root",
                    kind="group",
                    area=(80, 80, 930, 1152),
                    children=[
                        "module-a",
                        "module-b",
                        "module-c",
                        "module-d",
                        "accent-bar",
                        "index",
                        "kicker",
                        "headline",
                        "body",
                        "signature",
                        "logo",
                    ],
                )
            ],
        ),
    )


def swiss_system_package(ir: BrandIR) -> TemplatePackage:
    """Publica três composições modulares com relações de grade explícitas."""
    style = derive_style_system(ir)
    layouts = (_rational_grid(ir), _quiet_axis(ir), _modular_field(ir))
    samples = {
        "swiss-rational-grid-post-4x5": {
            "kicker": "Sistema / informação",
            "signature": "@sua-marca",
            "index": "1",
            "headline": "Clareza também tem ritmo.",
            "body": "A grade organiza diferenças de escala sem tornar a leitura previsível.",
        },
        "swiss-quiet-axis-post-4x5": {
            "kicker": "Precisão e intervalo",
            "headline": "O silêncio orienta o olhar.",
            "body": "Um eixo firme permite que cada informação encontre sua distância.",
            "index": "2",
            "signature": "@sua-marca",
        },
        "swiss-modular-field-post-4x5": {
            "index": "3",
            "kicker": "Unidades em relação",
            "headline": "Partes distintas. Um sistema coerente.",
            "body": "Módulos mudam de função sem abandonar proporção, alinhamento e continuidade.",
            "signature": "@sua-marca",
        },
    }
    intents = {
        "swiss-rational-grid-post-4x5": (
            "Grade racional",
            "Distribuir hierarquia e metadados sobre uma grade visível de seis colunas.",
        ),
        "swiss-quiet-axis-post-4x5": (
            "Eixo de silêncio",
            "Usar uma única linha estrutural para sustentar assimetria e grande intervalo visual.",
        ),
        "swiss-modular-field-post-4x5": (
            "Campo modular",
            "Relacionar blocos independentes como unidades de um mesmo sistema proporcional.",
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
        family="Sistema suíço",
        title_pt="Sistema suíço",
        description_pt=(
            "Três composições editáveis construídas por grade, intervalo, proporção e precisão."
        ),
        profiles=["post-4x5"],
        required_roles=list(style.typography),
        required_color_tokens=["color.background", "color.text", "color.primary"],
        compositions=compositions,
        evaluations=publication_evaluations(),
    )
