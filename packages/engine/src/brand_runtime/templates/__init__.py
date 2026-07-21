"""API pública dos templates declarativos."""

from brand_runtime.templates.models import (
    ExportSupport,
    TemplateComposition,
    TemplateEvaluation,
    TemplatePackage,
)
from brand_runtime.templates.registry import (
    generate_template_layouts,
    template_packages,
    typographic_editorial_package,
)
from brand_runtime.templates.brutalist import typographic_brutalist_package
from brand_runtime.templates.collage import editorial_collage_package
from brand_runtime.templates.constructivist import constructivist_dynamics_package
from brand_runtime.templates.data import data_evidence_package
from brand_runtime.templates.device import device_mockup_package
from brand_runtime.templates.fashion import fashion_editorial_package
from brand_runtime.templates.geometric import geometric_modernism_package
from brand_runtime.templates.kinetic import kinetic_typography_package
from brand_runtime.templates.minimal import minimal_luxury_package
from brand_runtime.templates.product import product_campaign_package
from brand_runtime.templates.swiss import swiss_system_package
from brand_runtime.templates.technical import technical_diagram_package
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
    "constructivist_dynamics_package",
    "data_evidence_package",
    "device_mockup_package",
    "editorial_collage_package",
    "fashion_editorial_package",
    "geometric_modernism_package",
    "kinetic_typography_package",
    "minimal_luxury_package",
    "product_campaign_package",
    "TemplateQualityReport",
    "evaluate_template_package",
    "structural_signature",
    "swiss_system_package",
    "template_packages",
    "technical_diagram_package",
    "typographic_brutalist_package",
    "typographic_editorial_package",
]
