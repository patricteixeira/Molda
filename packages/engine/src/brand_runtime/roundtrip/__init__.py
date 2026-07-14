"""Parser e contratos do round-trip de documentos editados externamente."""

from brand_runtime.roundtrip.models import DocumentGraph, DocumentNode
from brand_runtime.roundtrip.pptx import PptxParseError, parse_pptx_document_graph

__all__ = [
    "DocumentGraph",
    "DocumentNode",
    "PptxParseError",
    "parse_pptx_document_graph",
]
