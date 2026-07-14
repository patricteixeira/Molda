"""Arquivos OOXML nativos derivados do Brand IR por template-fill."""

from brand_runtime.native.docx import render_docx
from brand_runtime.native.ooxml import (
    NativeDiagnostic,
    OoxmlManifest,
    canonical_ooxml_manifest,
    validate_ooxml,
)
from brand_runtime.native.pptx import inspect_semantic_shapes, render_pptx
from brand_runtime.native.preview import PreviewResult, render_native_preview
from brand_runtime.native.theme import derive_branded_template

__all__ = [
    "NativeDiagnostic",
    "OoxmlManifest",
    "PreviewResult",
    "canonical_ooxml_manifest",
    "derive_branded_template",
    "inspect_semantic_shapes",
    "render_docx",
    "render_native_preview",
    "render_pptx",
    "validate_ooxml",
]
