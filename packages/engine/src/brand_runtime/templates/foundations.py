"""Primitivas compartilhadas por famílias visuais declarativas."""

from __future__ import annotations

from brand_runtime.ir.models import BrandIR
from brand_runtime.kit.models import Canvas, Slot, TemplateRef
from brand_runtime.templates.models import TemplateEvaluation

POST_4X5_CANVAS = Canvas(width_px=1080, height_px=1350, safe_area_px=48)


def template_ref(package_id: str, version: str, composition_id: str) -> TemplateRef:
    """Cria a referência imutável que liga uma cena ao pacote publicado."""
    return TemplateRef(
        package_id=package_id,
        version=version,
        composition_id=composition_id,
    )


def logo_slot(
    ir: BrandIR,
    area: tuple[int, int, int, int],
    *,
    slot_id: str = "logo",
) -> Slot:
    """Posiciona a marca sem violar a largura mínima confirmada no Brand IR."""
    minimum = ir.assets["logo.primary"].min_width_px
    width = max(area[2], minimum)
    height = max(area[3], minimum)
    return Slot(
        id=slot_id,
        kind="logo",
        area=(area[0], area[1], width, height),
        fit="fixed",
        asset_token="logo.primary",
        z_index=12,
    )


def publication_evaluations() -> list[TemplateEvaluation]:
    """Mantém o mesmo portão de autoria e segurança em todas as famílias."""
    return [
        TemplateEvaluation(kind="no-overflow", stage="renderer"),
        TemplateEvaluation(kind="safe-area"),
        TemplateEvaluation(kind="contrast", stage="guard"),
        TemplateEvaluation(kind="type-hierarchy", minimum=2.5),
        TemplateEvaluation(kind="negative-space", minimum=0.12, maximum=0.72),
        TemplateEvaluation(kind="structural-distance", minimum=0.35),
    ]
