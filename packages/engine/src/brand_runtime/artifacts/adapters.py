"""Adaptação explícita entre ContentSpec v0 e ArtifactInstance v1."""

from __future__ import annotations

import hashlib

from brand_runtime.artifacts.models import ArtifactInstance, ArtifactValue
from brand_runtime.kit.models import ContentSpec, LayoutSpec, TemplateRef


def scene_hash(layout: LayoutSpec) -> str:
    """Produz a identidade canônica do snapshot compilado."""
    payload = layout.model_dump_json(by_alias=True, exclude_none=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def artifact_from_content_spec(
    content: ContentSpec,
    layout: LayoutSpec,
    *,
    artifact_id: str,
    locale: str = "pt-BR",
) -> ArtifactInstance:
    """Pina layout e conteúdo legados sem inventar proveniência."""
    reference = layout.template_ref or TemplateRef(
        package_id="legacy-layouts",
        version="1.0.0",
        composition_id=layout.id,
    )
    snapshot = layout.model_copy(deep=True)
    return ArtifactInstance(
        id=artifact_id,
        template_ref=reference,
        brand_revision_id=content.brand_revision_id,
        scene_snapshot=snapshot,
        scene_hash=scene_hash(snapshot),
        values={
            key: ArtifactValue(status="confirmed", value=value.model_copy(deep=True))
            for key, value in content.values.items()
        },
        background_color_token=content.background_color_token,
        overrides={key: value.model_copy(deep=True) for key, value in content.overrides.items()},
        asset_bindings=dict(content.asset_bindings),
        locale=locale,
        surface=content.surface.model_copy(deep=True) if content.surface else None,
        added_slots=[slot.model_copy(deep=True) for slot in content.added_slots],
        added_layers=[layer.model_copy(deep=True) for layer in content.added_layers],
    )


def artifact_to_content_spec(instance: ArtifactInstance) -> ContentSpec:
    """Reduz a instância v1 ao contrato legado sem incluir valores ausentes."""
    return ContentSpec(
        layout_id=instance.scene_snapshot.id,
        brand_revision_id=instance.brand_revision_id,
        values={
            key: item.value.model_copy(deep=True)
            for key, item in instance.values.items()
            if item.value is not None
        },
        background_color_token=instance.background_color_token,
        overrides={key: value.model_copy(deep=True) for key, value in instance.overrides.items()},
        asset_bindings=dict(instance.asset_bindings),
        surface=instance.surface.model_copy(deep=True) if instance.surface else None,
        added_slots=[slot.model_copy(deep=True) for slot in instance.added_slots],
        added_layers=[layer.model_copy(deep=True) for layer in instance.added_layers],
    )
