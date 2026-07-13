"""Feature de resolução tipográfica segura durante o intake."""

from brand_api.fonts.google import GoogleFontsResolver
from brand_api.fonts.intake import (
    MAX_FONT_RESOLUTION_CANDIDATES,
    MAX_RESOLVED_FONTS,
    preferred_font_request,
    reconcile_resolved_font_diagnostics,
    resolve_draft_fonts,
    resolve_font_candidate,
)
from brand_api.fonts.models import DisabledFontResolver, FontResolver


def build_font_resolver(base_url: str | None) -> FontResolver:
    """Constrói o provedor configurado sem introduzir segredo obrigatório."""
    if base_url is None:
        return DisabledFontResolver()
    return GoogleFontsResolver(base_url=base_url)


__all__ = [
    "MAX_FONT_RESOLUTION_CANDIDATES",
    "MAX_RESOLVED_FONTS",
    "build_font_resolver",
    "preferred_font_request",
    "reconcile_resolved_font_diagnostics",
    "resolve_draft_fonts",
    "resolve_font_candidate",
]
