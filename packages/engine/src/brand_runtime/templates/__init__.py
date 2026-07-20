"""API pública dos templates declarativos."""

from brand_runtime.templates.models import (
    ExportSupport,
    TemplateComposition,
    TemplateEvaluation,
    TemplatePackage,
)
from brand_runtime.templates.registry import (
    generate_template_layouts,
    typographic_editorial_package,
)
from brand_runtime.templates.quality import (
    TemplateQualityReport,
    evaluate_template_package,
    structural_signature,
)

__all__ = [
    "ExportSupport",
    "TemplateComposition",
    "TemplateEvaluation",
    "TemplatePackage",
    "generate_template_layouts",
    "TemplateQualityReport",
    "evaluate_template_package",
    "structural_signature",
    "typographic_editorial_package",
]
