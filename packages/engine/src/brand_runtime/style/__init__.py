"""API pública do sistema visual derivado."""

from brand_runtime.style.derive import derive_style_system
from brand_runtime.style.models import StyleSystemIR

__all__ = ["StyleSystemIR", "derive_style_system"]
