import pytest
from fontTools.ttLib import TTFont

from brand_runtime.intake.fonts import (
    DEFAULT_COVERAGE_PROFILE,
    font_axes_from_ttfont,
    inspect_font_capabilities,
    introspect_font,
    missing_codepoints_from_ttfont,
    required_codepoints,
)


def test_reads_family_weight_style(fixture_font):
    info = introspect_font(fixture_font)
    assert info.family == "Fixture Sans"
    assert info.weight == 700
    assert info.style == "normal"


def test_coverage_uses_real_cmap_and_returns_stable_codepoints(fixture_font):
    with TTFont(fixture_font) as font:
        missing = missing_codepoints_from_ttfont(
            font,
            required=[ord("—"), ord("A"), ord("á"), ord("—")],
        )

    assert missing == [ord("—")]


def test_capability_inspection_reports_profile_gaps_and_static_axes(fixture_font):
    axes, missing = inspect_font_capabilities(fixture_font)

    assert axes == []
    assert ord("A") not in missing
    assert ord("Á") in missing
    assert missing == sorted(set(missing))
    assert ord("Á") in required_codepoints(DEFAULT_COVERAGE_PROFILE)


def test_unknown_coverage_profile_is_rejected(fixture_font):
    with TTFont(fixture_font) as font, pytest.raises(ValueError, match="desconhecido"):
        missing_codepoints_from_ttfont(font, coverage_profile="pt-BR-futuro")


def test_static_font_has_no_variable_axes(fixture_font):
    with TTFont(fixture_font) as font:
        assert font_axes_from_ttfont(font) == []
