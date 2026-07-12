import pytest

from brand_runtime.intake.svg_logo import (
    SvgInvalid,
    extract_svg_colors,
    sanitize_svg,
    svg_canvas_size,
)

MALICIOUS = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <script>alert(1)</script>
  <rect width="60" height="100" fill="#1A4D8F" onclick="evil()"/>
  <circle r="20" fill="#F4A300" stroke="#1A4D8F"/>
  <image href="https://evil.example/x.png"/>
  <use href="#ok"/>
</svg>"""

# Bomba de expansão de entidades (billion laughs): ~400 bytes que expandem para
# 100 KB — cada nível extra de entidade multiplica por 10 (DoS de memória).
ENTITY_BOMB = b"""<?xml version="1.0"?>
<!DOCTYPE svg [
  <!ENTITY a "0123456789">
  <!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">
  <!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">
  <!ENTITY d "&c;&c;&c;&c;&c;&c;&c;&c;&c;&c;">
  <!ENTITY e "&d;&d;&d;&d;&d;&d;&d;&d;&d;&d;">
]>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="#1A4D8F" data-bomb="&e;"/>
</svg>"""


def test_sanitize_strips_dangerous_content():
    clean = sanitize_svg(MALICIOUS)
    text = clean.decode("utf-8")
    assert "<script" not in text
    assert "onclick" not in text
    assert "evil.example" not in text
    assert 'href="#ok"' in text            # referência local preservada


def test_extract_colors_counts_fills_and_strokes(tmp_path):
    p = tmp_path / "logo.svg"
    p.write_bytes(MALICIOUS)
    cands = extract_svg_colors(p)
    scores = {c.value: c.score for c in cands}
    assert scores["#1A4D8F"] == 1.0        # 2 ocorrências (fill + stroke), normalizado
    assert scores["#F4A300"] == 0.5        # 1 ocorrência


def test_canvas_size_from_viewbox(tmp_path):
    p = tmp_path / "logo.svg"
    p.write_bytes(MALICIOUS)
    assert svg_canvas_size(p) == (100.0, 100.0)


def test_sanitize_rejects_entity_expansion_bomb():
    with pytest.raises(SvgInvalid):
        sanitize_svg(ENTITY_BOMB)
