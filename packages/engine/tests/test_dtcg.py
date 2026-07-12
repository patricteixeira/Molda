import json
import pytest
from brand_runtime.intake.dtcg import DtcgError, load_dtcg

TOKENS = {
    "color": {
        "brand": {"$type": "color", "$value": "#1A4D8F"},
        "action": {"$type": "color", "$value": "{color.brand}"},
    }
}


def test_alias_resolution(tmp_path):
    p = tmp_path / "tokens.json"
    p.write_text(json.dumps(TOKENS), encoding="utf-8")
    out = load_dtcg(p)
    assert out["color.action"].value == "#1A4D8F"
    assert out["color.action"].evidence[0].source_type == "dtcg-tokens"


def test_cycle_raises(tmp_path):
    cyc = {"color": {"a": {"$type": "color", "$value": "{color.b}"},
                     "b": {"$type": "color", "$value": "{color.a}"}}}
    p = tmp_path / "tokens.json"
    p.write_text(json.dumps(cyc), encoding="utf-8")
    with pytest.raises(DtcgError):
        load_dtcg(p)


def test_draft_ranks_dtcg_first(brand_package, tmp_path):
    from brand_runtime.intake.draft import build_draft
    (brand_package / "tokens.json").write_text(
        json.dumps({"color": {"brand": {"$type": "color", "$value": "#00FF88"}}}),
        encoding="utf-8")
    draft = build_draft(brand_package)
    q = next(q for q in draft.questions if q.id == "color.primary")
    assert q.candidates[0].value == "#00FF88"


def test_draft_ranks_dtcg_first_even_when_extractors_agree(tmp_path):
    """Pesos de extração são aditivos por arquivo (dois SVGs concordando em uma
    cor somam 6.0) e não podem passar na frente de um token DTCG (camada de
    maior autoridade, spec §5.3) — o contrato é DTCG primeiro no ranking."""
    from brand_runtime.intake.draft import build_draft

    package = tmp_path / "pacote"
    logos = package / "assets" / "logos"
    logos.mkdir(parents=True)
    svg = (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        b'<rect width="100" height="100" fill="#FF0000"/></svg>'
    )
    (logos / "logo.svg").write_bytes(svg)
    (logos / "logo-horizontal.svg").write_bytes(svg)
    (package / "tokens.json").write_text(
        json.dumps({"color": {"brand": {"$type": "color", "$value": "#00FF88"}}}),
        encoding="utf-8",
    )
    draft = build_draft(package)
    q = next(q for q in draft.questions if q.id == "color.primary")
    assert q.candidates[0].value == "#00FF88"
    assert q.candidates[1].value == "#FF0000"  # extração concordante vem logo depois


def test_deep_nesting_raises_no_recursion_error(tmp_path):
    """tokens.json é input hostil: aninhamento de ~5000 níveis (aceito pelo
    json.loads) não pode estourar a recursão do interpretador em ``_walk``."""
    depth = 5000
    doc = '{"level":' * depth + '{"$type": "color", "$value": "#1A4D8F"}' + "}" * depth
    p = tmp_path / "tokens.json"
    p.write_text(doc, encoding="utf-8")
    out = load_dtcg(p)
    assert out["color.level"].value == "#1A4D8F"


def test_long_alias_chain_raises_no_recursion_error(tmp_path):
    """Cadeia legal (sem ciclo) de 1500 aliases resolve sem RecursionError."""
    n = 1500
    tokens = {"color": {"c0": {"$type": "color", "$value": "#1A4D8F"}}}
    for i in range(1, n):
        tokens["color"][f"c{i}"] = {"$type": "color", "$value": f"{{color.c{i - 1}}}"}
    p = tmp_path / "tokens.json"
    p.write_text(json.dumps(tokens), encoding="utf-8")
    out = load_dtcg(p)
    assert out[f"color.c{n - 1}"].value == "#1A4D8F"
    assert len(out) == n


def test_root_level_value_is_not_a_token(tmp_path):
    """A raiz do documento DTCG é um grupo, nunca um token nomeado: ``$value``
    na raiz é ignorado (sem crash com IndexError na montagem da chave)."""
    p = tmp_path / "tokens.json"
    p.write_text(json.dumps({"$type": "color", "$value": "#1A4D8F"}), encoding="utf-8")
    assert load_dtcg(p) == {}
