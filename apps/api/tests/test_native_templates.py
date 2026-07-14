from pathlib import Path

import pytest
from pptx import Presentation

from brand_api.native_templates import (
    CURRENT_NATIVE_TEMPLATE_VERSION,
    NativeTemplateRegistry,
)
from brand_runtime import LayoutSpec


def _layout(profile: str) -> LayoutSpec:
    dimensions = {
        "post-1x1": (1080, 1080, 48),
        "post-4x5": (1080, 1350, 48),
        "story-9x16": (1080, 1920, 64),
        "doc-a4": (794, 1123, 76),
    }[profile]
    return LayoutSpec(
        id=f"layout-{profile}",
        profile=profile,
        name_pt="Fixture",
        canvas={
            "widthPx": dimensions[0],
            "heightPx": dimensions[1],
            "safeAreaPx": dimensions[2],
        },
        background={"kind": "color", "colorToken": "color.background"},
        slots=[],
    )


def test_registry_publica_templates_v1_com_aspect_ratio_do_perfil():
    registry = NativeTemplateRegistry()
    registry.validate_all()

    for profile in ("post-1x1", "post-4x5", "story-9x16"):
        layout = _layout(profile)
        template = registry.resolve("pptx", layout)
        presentation = Presentation(template.path)
        assert template.version == CURRENT_NATIVE_TEMPLATE_VERSION
        assert template.native_layout_name == "Title and Content"
        assert presentation.slide_width / presentation.slide_height == pytest.approx(
            layout.canvas.width_px / layout.canvas.height_px,
            rel=1e-6,
        )

    docx = registry.resolve("docx", _layout("doc-a4"))
    assert docx.path.name == "docx-doc-a4.docx"


def test_registry_recusa_matriz_e_versao_nao_publicadas():
    registry = NativeTemplateRegistry()

    with pytest.raises(ValueError, match="PPTX"):
        registry.resolve("pptx", _layout("doc-a4"))
    with pytest.raises(ValueError, match="DOCX"):
        registry.resolve("docx", _layout("post-1x1"))
    with pytest.raises(ValueError, match="não está instalada"):
        registry.resolve("pptx", _layout("post-1x1"), version="v0")


def test_registry_falha_fechado_quando_recurso_esta_ausente(tmp_path: Path):
    registry = NativeTemplateRegistry(tmp_path / "templates")

    with pytest.raises(RuntimeError, match="não está instalado"):
        registry.resolve("pptx", _layout("post-1x1"))
