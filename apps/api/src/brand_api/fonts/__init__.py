"""Feature de resolução tipográfica segura durante o intake."""

from brand_api.fonts.google import GoogleFontsResolver
from brand_api.fonts.intake import resolve_draft_fonts
from brand_api.fonts.models import DisabledFontResolver, FontResolver


def build_font_resolver(base_url: str | None) -> FontResolver:
    """Constrói o provedor configurado sem introduzir segredo obrigatório."""
    if base_url is None:
        return DisabledFontResolver()
    return GoogleFontsResolver(base_url=base_url)


__all__ = ["build_font_resolver", "resolve_draft_fonts"]
