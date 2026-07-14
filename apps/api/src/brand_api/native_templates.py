"""Registro fechado dos templates OOXML nativos distribuídos com a API."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from brand_runtime import LayoutSpec, validate_ooxml

NativeFormat = Literal["pptx", "docx"]

CURRENT_NATIVE_TEMPLATE_VERSION = "v1"


@dataclass(frozen=True, slots=True)
class NativeTemplate:
    """Recurso imutável selecionado por formato, versão e perfil."""

    format: NativeFormat
    version: str
    profile: str
    path: Path
    native_layout_name: str | None = None


_FILENAMES: dict[tuple[NativeFormat, str], str] = {
    ("pptx", "post-1x1"): "pptx-post-1x1.pptx",
    ("pptx", "post-4x5"): "pptx-post-4x5.pptx",
    ("pptx", "story-9x16"): "pptx-story-9x16.pptx",
    ("docx", "doc-a4"): "docx-doc-a4.docx",
}


def _is_link(path: Path) -> bool:
    is_junction = getattr(os.path, "isjunction", None)
    return path.is_symlink() or bool(is_junction and is_junction(path))


class NativeTemplateRegistry:
    """Resolve somente combinações publicadas e valida a estrutura do recurso."""

    def __init__(self, root: Path | None = None) -> None:
        """Usa os recursos empacotados ou uma raiz explícita para testes."""
        self.root = root or Path(__file__).with_name("native_templates")

    def resolve(
        self,
        fmt: NativeFormat,
        layout: LayoutSpec,
        *,
        version: str = CURRENT_NATIVE_TEMPLATE_VERSION,
    ) -> NativeTemplate:
        """Retorna um template regular e estruturalmente válido."""
        if version != CURRENT_NATIVE_TEMPLATE_VERSION:
            raise ValueError(f"A versão de template nativo «{version}» não está instalada.")
        filename = _FILENAMES.get((fmt, layout.profile))
        if filename is None:
            if fmt == "pptx":
                raise ValueError("Exporte PPTX apenas para layouts sociais.")
            raise ValueError("Exporte DOCX apenas para documentos (A4).")

        version_root = self.root / version
        path = version_root / filename
        try:
            mode = path.stat(follow_symlinks=False).st_mode
            resolved_root = self.root.resolve(strict=True)
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise RuntimeError(f"O template nativo «{filename}» não está instalado.") from exc
        if (
            _is_link(self.root)
            or _is_link(version_root)
            or _is_link(path)
            or not stat.S_ISREG(mode)
            or not resolved.is_relative_to(resolved_root)
        ):
            raise RuntimeError("O template nativo precisa ser um arquivo regular do pacote.")
        blocking = [diagnostic for diagnostic in validate_ooxml(path) if diagnostic.blocking]
        if blocking:
            raise RuntimeError(
                f"O template nativo «{filename}» possui {len(blocking)} erro(s) estrutural(is)."
            )
        return NativeTemplate(
            format=fmt,
            version=version,
            profile=layout.profile,
            path=path,
            native_layout_name="Title and Content" if fmt == "pptx" else None,
        )

    def validate_all(self) -> None:
        """Falha cedo no boot quando algum recurso publicado está ausente ou inválido."""
        for fmt, profile in _FILENAMES:
            canvas = {
                "post-1x1": (1080, 1080, 48),
                "post-4x5": (1080, 1350, 48),
                "story-9x16": (1080, 1920, 64),
                "doc-a4": (794, 1123, 76),
            }[profile]
            layout = LayoutSpec(
                id=f"template-check-{profile}",
                profile=profile,
                name_pt="Validação interna de template",
                canvas={
                    "widthPx": canvas[0],
                    "heightPx": canvas[1],
                    "safeAreaPx": canvas[2],
                },
                background={"kind": "color", "colorToken": "color.background"},
                slots=[],
            )
            self.resolve(fmt, layout)
