"""Resolução única de layouts persistidos e layouts internos derivados."""

from __future__ import annotations

import re

from brand_api.models import BrandRevision
from brand_api.revision_ir import revision_brand_ir
from brand_runtime import (
    LayoutSpec,
    generate_carousel_layouts,
    generate_template_layouts,
)

_CAROUSEL_LAYOUT_ID = re.compile(r"^carousel-(?:cover|content-[ab]|closing)-(post-1x1|post-4x5)$")


def public_kit(revision: BrandRevision) -> list[dict]:
    """Sobrepõe templates versionados sem reescrever o snapshot persistido."""
    persisted = list(revision.kit)
    known_ids = {
        item.get("id")
        for item in persisted
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    ir = revision_brand_ir(revision)
    additions = [
        layout.model_dump(mode="json", by_alias=True)
        for layout in generate_template_layouts(ir)
        if layout.id not in known_ids
    ]
    return [*persisted, *additions]


def resolve_layout(revision: BrandRevision, layout_id: str) -> LayoutSpec | None:
    """Resolve um layout sem alterar o snapshot imutável da revisão."""
    raw_layout = next(
        (item for item in revision.kit if isinstance(item, dict) and item.get("id") == layout_id),
        None,
    )
    if raw_layout is not None:
        return LayoutSpec.model_validate(raw_layout)

    ir = revision_brand_ir(revision)
    template_layout = next(
        (layout for layout in generate_template_layouts(ir) if layout.id == layout_id),
        None,
    )
    if template_layout is not None:
        return template_layout

    match = _CAROUSEL_LAYOUT_ID.fullmatch(layout_id)
    if match is None:
        return None
    return next(
        (
            layout
            for layout in generate_carousel_layouts(ir, match.group(1))
            if layout.id == layout_id
        ),
        None,
    )
