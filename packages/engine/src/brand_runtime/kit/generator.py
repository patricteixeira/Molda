"""Geração determinística do kit inicial de layouts a partir do Brand IR."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from brand_runtime.ir.models import BrandIR
from brand_runtime.kit.models import (
    PROFILES,
    AssetLayer,
    Background,
    Canvas,
    LayoutSpec,
    MotifLayer,
    Profile,
    ShapeLayer,
    Slot,
)

_SOCIAL_PROFILES: tuple[Profile, ...] = ("post-1x1", "post-4x5", "story-9x16")


class KitGenerationError(ValueError):
    """Erro de contrato que impede gerar um kit coerente com a revisão da marca."""


def _canvas(profile: Profile) -> Canvas:
    """Materializa o canvas canônico de um perfil publicado."""
    width, height, safe_area = PROFILES[profile]
    return Canvas(width_px=width, height_px=height, safe_area_px=safe_area)


def _validate_ir(ir: BrandIR) -> None:
    """Falha explicitamente quando uma referência obrigatória não existe no IR."""
    missing: list[str] = []
    if "color.background" not in ir.colors:
        missing.append("color.background")
    for role in ("heading", "body", "caption"):
        if role not in ir.roles:
            missing.append(f"role:{role}")
            continue
        semantic_role = ir.roles[role]
        if semantic_role.font not in ir.fonts:
            missing.append(f"{role}.font:{semantic_role.font}")
        if semantic_role.color not in ir.colors:
            missing.append(f"{role}.color:{semantic_role.color}")
    if "logo.primary" not in ir.assets:
        missing.append("logo.primary")
    if ir.composition_rules is not None:
        rules = ir.composition_rules
        for mode_name, mode in (("light", rules.modes.light), ("dark", rules.modes.dark)):
            if mode is None:
                continue
            if mode.background_color_token not in ir.colors:
                missing.append(f"composition.{mode_name}.background:{mode.background_color_token}")
            if mode.foreground_color_token not in ir.colors:
                missing.append(f"composition.{mode_name}.foreground:{mode.foreground_color_token}")
            if mode.logo_asset_token is not None and mode.logo_asset_token not in ir.assets:
                missing.append(f"composition.{mode_name}.logo:{mode.logo_asset_token}")
        for ratio in rules.color_ratios:
            if ratio.color_token not in ir.colors:
                missing.append(f"composition.ratio:{ratio.color_token}")
        if rules.accent is not None and rules.accent.color_token not in ir.colors:
            missing.append(f"composition.accent:{rules.accent.color_token}")
    if missing:
        raise KitGenerationError(
            "O Brand IR não contém referências obrigatórias para o kit: " + ", ".join(missing) + "."
        )


def _logo_slot(ir: BrandIR, canvas: Canvas) -> Slot:
    """Cria o logo travado no canto inferior direito, respeitando seu mínimo."""
    minimum = ir.assets["logo.primary"].min_width_px
    size = max(minimum, round(canvas.width_px * 0.12))
    x = canvas.width_px - canvas.safe_area_px - size
    y = canvas.height_px - canvas.safe_area_px - size
    if size <= 0 or x < canvas.safe_area_px or y < canvas.safe_area_px:
        raise KitGenerationError(
            "O tamanho mínimo do logo não cabe na área segura do perfil "
            f"{canvas.width_px}×{canvas.height_px}px."
        )
    return Slot(id="logo", kind="logo", area=(x, y, size, size), fit="fixed")


def _centered_logo_slot(ir: BrandIR, canvas: Canvas) -> Slot:
    """Centraliza o logo sem violar o mínimo ou a área segura declarados."""
    minimum = ir.assets["logo.primary"].min_width_px
    size = max(minimum, round(canvas.width_px * 0.14))
    x = round((canvas.width_px - size) / 2)
    y = min(round(canvas.height_px * 0.8), canvas.height_px - canvas.safe_area_px - size)
    if size <= 0 or x < canvas.safe_area_px or y < canvas.safe_area_px:
        raise KitGenerationError(
            "O tamanho mínimo do logo não cabe centralizado na área segura do perfil "
            f"{canvas.width_px}×{canvas.height_px}px."
        )
    return Slot(id="logo", kind="logo", area=(x, y, size, size), fit="fixed")


def _statement(ir: BrandIR, profile: Profile) -> LayoutSpec:
    """Gera o arquétipo de frase de impacto para um perfil social."""
    canvas = _canvas(profile)
    width, height, safe = canvas.width_px, canvas.height_px, canvas.safe_area_px
    return LayoutSpec(
        id=f"statement-{profile}",
        profile=profile,
        name_pt="Frase de impacto",
        canvas=canvas,
        background=Background(kind="color", color_token="color.background"),
        slots=[
            Slot(
                id="headline",
                kind="text",
                role="heading",
                max_chars=90,
                area=(safe, round(height * 0.30), width - 2 * safe, round(height * 0.40)),
            ),
            _logo_slot(ir, canvas),
        ],
    )


def _quote(ir: BrandIR, profile: Profile) -> LayoutSpec:
    """Gera o arquétipo de citação sobre imagem para um perfil social."""
    canvas = _canvas(profile)
    width, height, safe = canvas.width_px, canvas.height_px, canvas.safe_area_px
    return LayoutSpec(
        id=f"quote-{profile}",
        profile=profile,
        name_pt="Citação sobre foto",
        canvas=canvas,
        background=Background(kind="image-slot"),
        slots=[
            Slot(
                id="photo",
                kind="image",
                min_resolution=(width, height),
                area=(0, 0, width, height),
                fit="fixed",
            ),
            Slot(
                id="quote",
                kind="text",
                role="heading",
                max_chars=140,
                area=(safe, round(height * 0.32), width - 2 * safe, round(height * 0.36)),
            ),
            Slot(
                id="author",
                kind="text",
                role="caption",
                max_chars=40,
                area=(safe, round(height * 0.72), width - 2 * safe, round(height * 0.06)),
                required=False,
            ),
            _logo_slot(ir, canvas),
        ],
    )


def _announce(ir: BrandIR, profile: Profile) -> LayoutSpec:
    """Gera o arquétipo de anúncio editorial para um perfil social."""
    canvas = _canvas(profile)
    width, height, safe = canvas.width_px, canvas.height_px, canvas.safe_area_px
    return LayoutSpec(
        id=f"announce-{profile}",
        profile=profile,
        name_pt="Anúncio com foto",
        canvas=canvas,
        background=Background(kind="color", color_token="color.background"),
        slots=[
            Slot(
                id="headline",
                kind="text",
                role="heading",
                max_chars=70,
                area=(safe, safe, width - 2 * safe, round(height * 0.22)),
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                max_chars=240,
                area=(safe, round(height * 0.30), width - 2 * safe, round(height * 0.28)),
            ),
            Slot(
                id="photo",
                kind="image",
                min_resolution=(width, round(height * 0.34)),
                area=(0, round(height * 0.62), width, round(height * 0.38)),
                fit="fixed",
            ),
            _logo_slot(ir, canvas),
        ],
    )


def _one_pager(ir: BrandIR) -> LayoutSpec:
    """Gera o documento A4 de uma página com rodapé reservado ao logo."""
    profile: Profile = "doc-a4"
    canvas = _canvas(profile)
    width, height, safe = canvas.width_px, canvas.height_px, canvas.safe_area_px
    logo = _logo_slot(ir, canvas)
    logo_size = logo.area[2]
    return LayoutSpec(
        id="one-pager-doc-a4",
        profile=profile,
        name_pt="Documento de uma página",
        canvas=canvas,
        background=Background(kind="color", color_token="color.background"),
        slots=[
            Slot(
                id="title",
                kind="text",
                role="heading",
                max_chars=80,
                area=(safe, safe, width - 2 * safe, 120),
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                max_chars=2200,
                area=(
                    safe,
                    safe + 150,
                    width - 2 * safe,
                    height - 2 * safe - 150 - logo_size,
                ),
            ),
            logo,
        ],
    )


_EDITORIAL_LOGO_SIZE_PX = 58


def _editorial_frame_layers(foreground: str) -> list[ShapeLayer]:
    """Desenha moldura e marcas de registro como vocabulário, não como imagem opaca."""
    return [
        ShapeLayer(
            id="frame-top",
            shape="rectangle",
            area=(52, 52, 976, 2),
            color_token=foreground,
            opacity=0.1,
            z_index=1,
        ),
        ShapeLayer(
            id="frame-left",
            shape="rectangle",
            area=(52, 52, 2, 1246),
            color_token=foreground,
            opacity=0.1,
            z_index=1,
        ),
        ShapeLayer(
            id="frame-right",
            shape="rectangle",
            area=(1026, 52, 2, 1246),
            color_token=foreground,
            opacity=0.1,
            z_index=1,
        ),
        ShapeLayer(
            id="frame-bottom",
            shape="rectangle",
            area=(52, 1296, 976, 2),
            color_token=foreground,
            opacity=0.1,
            z_index=1,
        ),
        ShapeLayer(
            id="register-top-left-x",
            shape="rectangle",
            area=(32, 34, 20, 2),
            color_token=foreground,
            opacity=0.45,
            z_index=2,
        ),
        ShapeLayer(
            id="register-top-left-y",
            shape="rectangle",
            area=(34, 34, 2, 20),
            color_token=foreground,
            opacity=0.45,
            z_index=2,
        ),
        ShapeLayer(
            id="register-top-right-x",
            shape="rectangle",
            area=(1028, 34, 20, 2),
            color_token=foreground,
            opacity=0.45,
            z_index=2,
        ),
        ShapeLayer(
            id="register-top-right-y",
            shape="rectangle",
            area=(1046, 34, 2, 20),
            color_token=foreground,
            opacity=0.45,
            z_index=2,
        ),
        ShapeLayer(
            id="register-bottom-left-x",
            shape="rectangle",
            area=(32, 1314, 20, 2),
            color_token=foreground,
            opacity=0.45,
            z_index=2,
        ),
        ShapeLayer(
            id="register-bottom-left-y",
            shape="rectangle",
            area=(34, 1296, 2, 20),
            color_token=foreground,
            opacity=0.45,
            z_index=2,
        ),
        ShapeLayer(
            id="register-bottom-right-x",
            shape="rectangle",
            area=(1028, 1314, 20, 2),
            color_token=foreground,
            opacity=0.45,
            z_index=2,
        ),
        ShapeLayer(
            id="register-bottom-right-y",
            shape="rectangle",
            area=(1046, 1296, 2, 20),
            color_token=foreground,
            opacity=0.45,
            z_index=2,
        ),
    ]


def _editorial_ready(ir: BrandIR) -> bool:
    """Exige a gramática completa; regras parciais nunca são completadas por suposição."""
    rules = ir.composition_rules
    if rules is None or rules.modes.light is None or rules.modes.dark is None:
        return False
    if rules.accent is None or rules.numbering is None:
        return False
    if not any(motif.kind == "diagonal-lines" for motif in rules.motifs):
        return False
    ratio_tokens = {item.color_token for item in rules.color_ratios}
    required_ratio_tokens = {
        rules.modes.light.background_color_token,
        rules.modes.dark.background_color_token,
        rules.accent.color_token,
    }
    if (
        len(rules.color_ratios) < 3
        or not required_ratio_tokens.issubset(ratio_tokens)
        or abs(sum(item.ratio for item in rules.color_ratios) - 1.0) > 0.001
    ):
        return False
    if rules.modes.light.logo_asset_token is None or rules.modes.dark.logo_asset_token is None:
        return False
    for token in (rules.modes.light.logo_asset_token, rules.modes.dark.logo_asset_token):
        asset = ir.assets.get(token)
        if asset is None or asset.min_width_px > _EDITORIAL_LOGO_SIZE_PX:
            return False
    return all(role in ir.roles for role in ("display", "label", "index", "signature"))


def _editorial_layout(ir: BrandIR, mode_name: Literal["light", "dark"]) -> LayoutSpec:
    """Materializa o arquétipo editorial 4:5 sem CSS ou geometria arbitrária."""
    rules = ir.composition_rules
    if rules is None:
        raise KitGenerationError("As regras de composição editoriais não foram compiladas.")
    mode = rules.modes.light if mode_name == "light" else rules.modes.dark
    if mode is None or mode.logo_asset_token is None or rules.accent is None:
        raise KitGenerationError(f"O modo editorial {mode_name} está incompleto.")

    canvas = _canvas("post-4x5")
    foreground = mode.foreground_color_token
    accent = rules.accent.color_token
    motif_color = foreground
    is_light = mode_name == "light"
    return LayoutSpec(
        id=f"editorial-{mode_name}-post-4x5",
        profile="post-4x5",
        name_pt=f"Editorial {'claro' if is_light else 'escuro'}",
        canvas=canvas,
        background=Background(kind="color", color_token=mode.background_color_token),
        composition_mode=mode_name,
        locked_layers=[
            MotifLayer(
                id="diagonal-field",
                motif="diagonal-lines",
                area=(0, 0, 1080, 1350),
                color_token=motif_color,
                opacity=0.06,
                stroke_width_px=2,
                spacing_px=22,
                z_index=0,
            ),
            *_editorial_frame_layers(foreground),
            ShapeLayer(
                id="accent-rule",
                shape="rectangle",
                area=(104, 445, 56, 4),
                color_token=accent,
                z_index=2,
            ),
            AssetLayer(
                id="brand-mark",
                asset_token=mode.logo_asset_token,
                area=(918, 116, _EDITORIAL_LOGO_SIZE_PX, _EDITORIAL_LOGO_SIZE_PX),
                fit="contain",
                z_index=2,
            ),
        ],
        slots=[
            Slot(
                id="index",
                kind="text",
                role="index",
                color_token=foreground,
                max_chars=2,
                # O índice é deliberadamente monumental e chega até a borda do
                # canvas. Os 450 px também acomodam a métrica do fallback
                # controlado sem transformar esse recorte expressivo em overflow.
                area=(80, 890, 760, 460),
                fit="fixed",
                z_index=5,
                opacity=0.08,
                text_format="zero-padded",
                fill_mode="stroke",
                stroke_color_token=foreground,
                stroke_width_px=2.5,
                letter_spacing_em=-0.04,
            ),
            Slot(
                id="kicker",
                kind="text",
                role="label",
                color_token=foreground,
                max_chars=48,
                area=(104, 470, 820, 40),
                fit="shrink-within-role-range",
                required=False,
                z_index=10,
                text_transform="uppercase",
                letter_spacing_em=0.18,
            ),
            Slot(
                id="headline",
                kind="text",
                role="display",
                color_token=foreground,
                emphasis_color_token=accent,
                max_chars=96,
                area=(104, 525, 840, 360),
                z_index=10,
                text_transform="uppercase",
                letter_spacing_em=-0.035,
            ),
            Slot(
                id="signature",
                kind="text",
                role="signature",
                color_token=foreground,
                max_chars=48,
                area=(270, 1210, 540, 36),
                fit="fixed",
                required=False,
                z_index=10,
                text_align="center",
                text_transform="uppercase",
                letter_spacing_em=0.12,
            ),
        ],
    )


def _editorial_closure_layout(ir: BrandIR, mode_name: Literal["light", "dark"]) -> LayoutSpec:
    """Fecha uma sequência editorial com marca, postura e ritmo do mesmo sistema."""
    rules = ir.composition_rules
    if rules is None:
        raise KitGenerationError("As regras de composição editoriais não foram compiladas.")
    mode = rules.modes.light if mode_name == "light" else rules.modes.dark
    if mode is None or mode.logo_asset_token is None or rules.accent is None:
        raise KitGenerationError(f"O modo editorial {mode_name} está incompleto.")

    canvas = _canvas("post-4x5")
    foreground = mode.foreground_color_token
    accent = rules.accent.color_token
    is_light = mode_name == "light"
    return LayoutSpec(
        id=f"editorial-closure-{mode_name}-post-4x5",
        profile="post-4x5",
        name_pt=f"Fechamento editorial {'claro' if is_light else 'escuro'}",
        canvas=canvas,
        background=Background(kind="color", color_token=mode.background_color_token),
        composition_mode=mode_name,
        locked_layers=[
            MotifLayer(
                id="diagonal-field",
                motif="diagonal-lines",
                area=(0, 0, 1080, 1350),
                color_token=foreground,
                opacity=0.06,
                stroke_width_px=2,
                spacing_px=22,
                z_index=0,
            ),
            MotifLayer(
                id="accent-diagonals",
                motif="diagonal-lines",
                area=(0, 930, 1080, 420),
                color_token=accent,
                opacity=0.16,
                stroke_width_px=2,
                spacing_px=74,
                z_index=1,
            ),
            *_editorial_frame_layers(foreground),
            AssetLayer(
                id="brand-mark",
                asset_token=mode.logo_asset_token,
                area=(474, 470, 132, 132),
                fit="contain",
                z_index=5,
            ),
        ],
        slots=[
            Slot(
                id="headline",
                kind="text",
                role="display",
                color_token=foreground,
                max_chars=32,
                area=(140, 675, 800, 92),
                fit="fixed",
                z_index=10,
                text_align="center",
                text_transform="uppercase",
                letter_spacing_em=-0.025,
            ),
            Slot(
                id="tagline",
                kind="text",
                role="body",
                color_token=foreground,
                emphasis_color_token=accent,
                max_chars=120,
                area=(170, 800, 740, 130),
                z_index=10,
                text_align="center",
                required=False,
            ),
            Slot(
                id="signature",
                kind="text",
                role="signature",
                color_token=foreground,
                max_chars=48,
                area=(270, 1210, 540, 36),
                fit="fixed",
                required=False,
                z_index=10,
                text_align="center",
                letter_spacing_em=0.08,
            ),
        ],
    )


def _signature_ready(ir: BrandIR) -> bool:
    """Exige um arquétipo declarado e o token de acento que materializa seus detalhes."""
    rules = ir.composition_rules
    return bool(
        rules is not None and rules.layout_style is not None and "color.secondary" in ir.colors
    )


def _signature_layout(ir: BrandIR) -> LayoutSpec:
    """Materializa uma prova 4:5 fechada para o tratamento declarado pelo manual."""
    rules = ir.composition_rules
    if rules is None or rules.layout_style is None:
        raise KitGenerationError("O arquétipo de composição não foi declarado.")

    canvas = _canvas("post-4x5")
    style = rules.layout_style.kind
    accent = "color.secondary"
    foreground = "color.text"

    if style == "ornamental-divider":
        return LayoutSpec(
            id="signature-ornamental-post-4x5",
            profile="post-4x5",
            name_pt="Editorial com divisor ornamental",
            canvas=canvas,
            background=Background(kind="color", color_token="color.background"),
            locked_layers=[
                ShapeLayer(
                    id="divider-left",
                    shape="rectangle",
                    area=(180, 674, 330, 2),
                    color_token=accent,
                    z_index=2,
                ),
                ShapeLayer(
                    id="divider-dot",
                    shape="circle",
                    area=(536, 671, 8, 8),
                    color_token=accent,
                    z_index=2,
                ),
                ShapeLayer(
                    id="divider-right",
                    shape="rectangle",
                    area=(570, 674, 330, 2),
                    color_token=accent,
                    z_index=2,
                ),
            ],
            slots=[
                Slot(
                    id="kicker",
                    kind="text",
                    role="caption",
                    max_chars=48,
                    area=(120, 160, 840, 54),
                    required=False,
                    text_align="center",
                    text_transform="uppercase",
                    letter_spacing_em=0.16,
                ),
                Slot(
                    id="headline",
                    kind="text",
                    role="heading",
                    max_chars=90,
                    area=(100, 270, 880, 300),
                    text_align="center",
                ),
                Slot(
                    id="body",
                    kind="text",
                    role="body",
                    max_chars=220,
                    area=(180, 740, 720, 180),
                    required=False,
                    text_align="center",
                ),
                _centered_logo_slot(ir, canvas),
            ],
        )

    return LayoutSpec(
        id="signature-clinical-post-4x5",
        profile="post-4x5",
        name_pt="Editorial em grade clínica",
        canvas=canvas,
        background=Background(kind="color", color_token="color.background"),
        locked_layers=[
            ShapeLayer(
                id="grid-panel",
                shape="rectangle",
                area=(760, 0, 320, 1350),
                color_token="color.primary",
                opacity=0.06,
                z_index=0,
            ),
            ShapeLayer(
                id="accent-rule",
                shape="rectangle",
                area=(80, 200, 72, 3),
                color_token=accent,
                z_index=2,
            ),
            ShapeLayer(
                id="body-rule",
                shape="rectangle",
                area=(80, 790, 560, 1),
                color_token=foreground,
                opacity=0.2,
                z_index=1,
            ),
            ShapeLayer(
                id="accent-dot",
                shape="circle",
                area=(940, 190, 8, 8),
                color_token=accent,
                z_index=2,
            ),
        ],
        slots=[
            Slot(
                id="kicker",
                kind="text",
                role="caption",
                max_chars=48,
                area=(80, 104, 680, 40),
                required=False,
                text_transform="uppercase",
                letter_spacing_em=0.18,
            ),
            Slot(
                id="headline",
                kind="text",
                role="heading",
                max_chars=96,
                area=(80, 250, 680, 330),
            ),
            Slot(
                id="body",
                kind="text",
                role="body",
                max_chars=220,
                area=(80, 640, 560, 130),
                required=False,
            ),
            Slot(
                id="fact",
                kind="text",
                role="heading",
                color_token="color.primary",
                max_chars=20,
                area=(780, 560, 280, 80),
                required=False,
                text_align="center",
            ),
            _logo_slot(ir, canvas),
        ],
    )


def generate_kit(ir: BrandIR) -> list[LayoutSpec]:
    """Gera os dez layouts canônicos e editoriais quando há regras explícitas."""
    _validate_ir(ir)
    builders: tuple[Callable[[BrandIR, Profile], LayoutSpec], ...] = (
        _statement,
        _quote,
        _announce,
    )
    layouts = [builder(ir, profile) for builder in builders for profile in _SOCIAL_PROFILES]
    layouts.append(_one_pager(ir))
    if _editorial_ready(ir):
        layouts.extend(
            (
                _editorial_layout(ir, "light"),
                _editorial_layout(ir, "dark"),
                _editorial_closure_layout(ir, "light"),
                _editorial_closure_layout(ir, "dark"),
            )
        )
    if _signature_ready(ir):
        layouts.append(_signature_layout(ir))
    return layouts
