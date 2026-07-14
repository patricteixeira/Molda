"""Derivação única de tema OOXML a partir do Brand IR."""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

from brand_runtime.ir.models import BrandIR
from brand_runtime.native.ooxml import OoxmlError, validate_ooxml

_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_COLOR_ORDER = ("dk1", "lt1", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6")


def _token_value(ir: BrandIR, *candidates: str, fallback: str) -> str:
    for candidate in candidates:
        token = ir.colors.get(candidate)
        if token is not None:
            return token.value.removeprefix("#")
    return fallback


def _font_family(ir: BrandIR, role_name: str, fallback: str) -> str:
    role = ir.roles.get(role_name)
    if role is None:
        return fallback
    font = ir.fonts.get(role.font)
    return font.family if font is not None and font.family.strip() else fallback


def _brand_theme(ir: BrandIR) -> tuple[dict[str, str], str, str]:
    palette = {
        "dk1": _token_value(ir, "color.text", "color.foreground", fallback="111111"),
        "lt1": _token_value(ir, "color.background", fallback="FFFFFF"),
        "accent1": _token_value(ir, "color.primary", fallback="2F5597"),
        "accent2": _token_value(ir, "color.secondary", fallback="ED7D31"),
        "accent3": _token_value(ir, "color.success", "color.primary", fallback="70AD47"),
        "accent4": _token_value(ir, "color.info", "color.secondary", fallback="5B9BD5"),
        "accent5": _token_value(ir, "color.warning", "color.secondary", fallback="FFC000"),
        "accent6": _token_value(ir, "color.danger", "color.primary", fallback="C00000"),
    }
    major = _font_family(ir, "heading", "Aptos Display")
    minor = _font_family(ir, "body", "Aptos")
    return palette, major, minor


def _patch_theme(payload: bytes, ir: BrandIR) -> bytes:
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    root = etree.fromstring(payload, parser=parser)
    palette, major, minor = _brand_theme(ir)
    namespaces = {"a": _A_NS}
    scheme = root.find(".//a:themeElements/a:clrScheme", namespaces)
    if scheme is None:
        raise OoxmlError("O template não possui um color scheme OOXML editável.")
    for name in _COLOR_ORDER:
        slot = scheme.find(f"a:{name}", namespaces)
        if slot is None:
            continue
        for child in list(slot):
            slot.remove(child)
        etree.SubElement(slot, f"{{{_A_NS}}}srgbClr", val=palette[name])

    major_latin = root.find(".//a:fontScheme/a:majorFont/a:latin", namespaces)
    minor_latin = root.find(".//a:fontScheme/a:minorFont/a:latin", namespaces)
    if major_latin is not None:
        major_latin.set("typeface", major)
    if minor_latin is not None:
        minor_latin.set("typeface", minor)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def derive_branded_template(template_path: Path, output_path: Path, ir: BrandIR) -> Path:
    """Copia o template e troca apenas theme parts, preservando o restante do pacote."""
    template_path = template_path.resolve()
    output_path = output_path.resolve()
    if template_path == output_path:
        raise OoxmlError("O template original nunca pode ser sobrescrito.")
    diagnostics = validate_ooxml(template_path)
    blocking = [item for item in diagnostics if item.blocking]
    if blocking:
        raise OoxmlError(f"O template possui {len(blocking)} erro(s) estrutural(is).")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        prefix=f".{output_path.stem}-",
        suffix=output_path.suffix,
        dir=output_path.parent,
    )
    os.close(handle)
    temp_path = Path(temp_name)
    try:
        patched = 0
        with (
            zipfile.ZipFile(template_path) as source,
            zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as destination,
        ):
            for info in source.infolist():
                payload = source.read(info.filename)
                if info.filename.endswith("theme/theme1.xml") or "/theme/theme" in info.filename:
                    payload = _patch_theme(payload, ir)
                    patched += 1
                destination.writestr(info, payload)
        if patched == 0:
            raise OoxmlError("O template não possui um theme part OOXML.")
        os.replace(temp_path, output_path)
    finally:
        temp_path.unlink(missing_ok=True)
    return output_path
