"""Introspecção de arquivos de fonte (TTF/OTF) com fontTools."""

from __future__ import annotations

from pathlib import Path

from fontTools.ttLib import TTFont

from brand_runtime.intake.pdf_fonts import FontInfo

_NAME_ID_FAMILY = 1
_NAME_ID_SUBFAMILY = 2
_NAME_ID_TYPOGRAPHIC_FAMILY = 16
_FS_SELECTION_ITALIC = 0b1  # bit 0 da OS/2.fsSelection


def introspect_font(font_path: Path) -> FontInfo:
    """Lê família, peso e estilo diretamente das tabelas de um arquivo de fonte.

    Regras: família = nameID 16 se existir, senão nameID 1; peso =
    ``OS/2.usWeightClass``; estilo itálico se o bit 0 de ``OS/2.fsSelection``
    estiver ligado ou o nameID 2 (subfamília) contiver "Italic".
    """
    with TTFont(font_path) as font:
        name_table = font["name"]
        family = name_table.getDebugName(_NAME_ID_TYPOGRAPHIC_FAMILY) or name_table.getDebugName(
            _NAME_ID_FAMILY
        )
        if not family:
            msg = f"Arquivo de fonte sem nome de família na tabela name: {font_path}"
            raise ValueError(msg)
        os2 = font["OS/2"]
        subfamily = name_table.getDebugName(_NAME_ID_SUBFAMILY) or ""
        italic = bool(os2.fsSelection & _FS_SELECTION_ITALIC) or "italic" in subfamily.lower()
    return FontInfo(
        family=family,
        weight=os2.usWeightClass,
        style="italic" if italic else "normal",
    )
