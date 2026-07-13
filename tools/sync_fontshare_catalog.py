"""Atualiza o snapshot de METADADOS do endpoint oficial Fontshare.

O script projeta apenas nome, slug, licença e identidade dos estilos. Nenhuma
URL de binário e nenhum arquivo de fonte são lidos ou persistidos.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

_ROOT = Path(__file__).resolve().parents[1]
_API_SOURCE = _ROOT / "apps" / "api" / "src"
_SOURCE = "https://api.fontshare.com/v2/fonts?offset=0&limit=100"
_DEFAULT_OUTPUT = _API_SOURCE / "brand_api" / "fonts" / "fontshare.catalog.json"
_MAX_RESPONSE_BYTES = 2 * 2**20
_LICENSE_TYPES = {"itf_ffl", "sil_ofl"}
_SLUG_RE = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")


def _load_normalizer() -> Callable[[str], str]:
    """Carrega ``normalize_family`` sem executar o pacote ou ler o snapshot atual."""
    source = _API_SOURCE / "brand_api" / "fonts" / "catalog.py"
    spec = importlib.util.spec_from_file_location("_brand_runtime_font_catalog", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("Não foi possível carregar a normalização de famílias.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.normalize_family


normalize_family = _load_normalizer()


class _RejectRedirects(HTTPRedirectHandler):
    """Recusa mudança silenciosa de origem durante a sincronização."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise HTTPError(req.full_url, code, "Redirect Fontshare recusado.", headers, fp)


def _strict_int(value: Any, *, field: str) -> int:
    """Aceita somente inteiros JSON reais, nunca booleanos ou strings."""
    if type(value) is not int:
        raise ValueError(f"Campo Fontshare {field!r} não é inteiro.")
    return value


def _strict_bool(value: Any, *, field: str) -> bool:
    """Aceita somente booleanos JSON reais."""
    if type(value) is not bool:
        raise ValueError(f"Campo Fontshare {field!r} não é booleano.")
    return value


def _fetch() -> dict[str, Any]:
    """Lê o JSON oficial com tamanho limitado e sem redirects."""
    request = Request(
        _SOURCE,
        headers={"Accept": "application/json", "User-Agent": "brand-runtime-catalog/1"},
    )
    try:
        with build_opener(_RejectRedirects()).open(request, timeout=30) as response:
            if response.status != 200 or response.geturl() != _SOURCE:
                raise ValueError("Resposta Fontshare não veio do endpoint allowlisted.")
            declared = response.headers.get("Content-Length")
            if declared is not None and int(declared) > _MAX_RESPONSE_BYTES:
                raise ValueError("Resposta Fontshare excede o limite permitido.")
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, OSError) as exc:
        raise RuntimeError(
            "Não foi possível consultar os metadados Fontshare."
        ) from exc
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise ValueError("Resposta Fontshare excede o limite permitido.")
    decoded = json.loads(raw)
    if not isinstance(decoded, dict):
        raise ValueError("Resposta Fontshare não é um objeto JSON.")
    return decoded


def _project_style(raw: Any) -> dict[str, object]:
    """Reduz um estilo upstream à identidade usada pelo endpoint CSS."""
    if not isinstance(raw, dict) or not isinstance(raw.get("weight"), dict):
        raise ValueError("Estilo Fontshare inválido.")
    code = _strict_int(raw["weight"].get("number"), field="weight.number")
    weight = _strict_int(raw["weight"].get("weight"), field="weight.weight")
    italic = _strict_bool(raw.get("is_italic"), field="is_italic")
    variable = _strict_bool(raw.get("is_variable"), field="is_variable")
    if not 1 <= code <= 1000 or not 0 <= weight <= 1000:
        raise ValueError("Código ou peso Fontshare fora do intervalo seguro.")
    if variable:
        expected_code = 2 if italic else 1
        if weight != 0 or code != expected_code:
            raise ValueError("Variante variável Fontshare inconsistente.")
    elif weight == 0:
        raise ValueError("Variante estática Fontshare sem peso real.")
    return {
        "code": code,
        "weight": weight,
        "style": "italic" if italic else "normal",
        "variable": variable,
    }


def _project_family(raw: Any) -> tuple[str, dict[str, object]]:
    """Projeta e valida os únicos campos de família mantidos localmente."""
    if not isinstance(raw, dict):
        raise ValueError("Família Fontshare inválida.")
    name = raw.get("name")
    slug = raw.get("slug")
    license_type = raw.get("license_type")
    styles = raw.get("styles")
    if not isinstance(name, str) or not isinstance(slug, str):
        raise ValueError("Nome ou slug Fontshare inválido.")
    if len(name) > 128 or len(slug) > 96 or not _SLUG_RE.fullmatch(slug):
        raise ValueError("Nome ou slug Fontshare fora do contrato allowlisted.")
    if license_type not in _LICENSE_TYPES:
        raise ValueError(f"Licença Fontshare desconhecida: {license_type!r}.")
    if not isinstance(styles, list) or not 1 <= len(styles) <= 32:
        raise ValueError(f"Família Fontshare sem estilos: {name!r}.")
    key = normalize_family(name)
    if not key:
        raise ValueError(f"Nome de família Fontshare inseguro: {name!r}.")
    projected_styles = sorted(
        (_project_style(style) for style in styles),
        key=lambda item: (
            bool(item["variable"]),
            int(item["weight"]),
            1 if item["style"] == "italic" else 0,
            int(item["code"]),
        ),
    )
    codes = [int(style["code"]) for style in projected_styles]
    if len(codes) != len(set(codes)):
        raise ValueError(f"Família Fontshare com códigos duplicados: {name!r}.")
    return key, {
        "name": name,
        "slug": slug,
        "licenseType": license_type,
        "styles": projected_styles,
    }


def build_catalog(upstream: dict[str, Any]) -> dict[str, object]:
    """Monta e valida o snapshot determinístico do payload oficial."""
    raw_fonts = upstream.get("fonts")
    if not isinstance(raw_fonts, list):
        raise ValueError("Resposta Fontshare não contém uma lista de famílias.")
    count = _strict_int(upstream.get("count"), field="count")
    count_total = _strict_int(upstream.get("count_total"), field="count_total")
    if count != len(raw_fonts) or count_total != len(raw_fonts):
        raise ValueError(
            "Endpoint Fontshare está paginado ou inconsistente; snapshot recusado."
        )

    families: dict[str, dict[str, object]] = {}
    slugs: set[str] = set()
    for raw_family in raw_fonts:
        key, family = _project_family(raw_family)
        if key in families:
            raise ValueError(f"Família Fontshare duplicada: {family['name']!r}.")
        slug = str(family["slug"])
        if slug in slugs:
            raise ValueError(f"Slug Fontshare duplicado: {slug!r}.")
        slugs.add(slug)
        families[key] = family
    families = dict(sorted(families.items()))
    canonical = json.dumps(
        families,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    payload: dict[str, object] = {
        "schemaVersion": "1.0.0",
        "provider": "fontshare-external",
        "source": _SOURCE,
        "revision": hashlib.sha256(canonical).hexdigest(),
        "families": families,
    }
    return payload


def _write_catalog(output: Path, catalog: dict[str, object]) -> None:
    """Publica o JSON atomicamente e com serialização determinística."""
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, raw_temporary = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    """Sincroniza o endpoint fixo para o destino informado."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    args = parser.parse_args()
    catalog = build_catalog(_fetch())
    _write_catalog(args.output.resolve(), catalog)
    print(
        f"{len(catalog['families'])} famílias Fontshare publicadas; "
        f"revisão: {catalog['revision']}; destino: {args.output.resolve()}"
    )


if __name__ == "__main__":
    main()
