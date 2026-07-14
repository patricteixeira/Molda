"""Preview derivado e isolável para arquivos nativos OOXML."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from brand_runtime.native.ooxml import NativeDiagnostic, OoxmlError, validate_ooxml


@dataclass(frozen=True, slots=True)
class PreviewResult:
    """Resultado explícito: preview pode falhar sem corromper o documento fonte."""

    ok: bool
    pdf_path: Path | None
    png_paths: tuple[Path, ...]
    diagnostics: tuple[NativeDiagnostic, ...]


def _converter(explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit.resolve() if explicit.is_file() else None
    configured = os.environ.get("BRANDRT_LIBREOFFICE")
    if configured:
        candidate = Path(configured).resolve()
        return candidate if candidate.is_file() else None
    resolved = shutil.which("soffice")
    return Path(resolved).resolve() if resolved else None


def render_native_preview(
    source_path: Path,
    output_dir: Path,
    *,
    converter_path: Path | None = None,
    timeout_seconds: int = 90,
) -> PreviewResult:
    """Converte por LibreOffice e rasteriza o PDF, sem alterar o OOXML de origem."""
    source_path = source_path.resolve()
    if not source_path.is_file():
        raise OoxmlError(f"O arquivo «{source_path}» não foi encontrado.")
    structural = tuple(validate_ooxml(source_path))
    if any(item.blocking for item in structural):
        return PreviewResult(False, None, (), structural)
    converter = _converter(converter_path)
    if converter is None:
        diagnostic = NativeDiagnostic(
            "preview.converter_unavailable",
            "warning",
            "LibreOffice não está disponível; o arquivo estruturalmente válido foi preservado.",
        )
        return PreviewResult(False, None, (), (*structural, diagnostic))

    original_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)
    profile_dir = Path(tempfile.mkdtemp(prefix="brandrt-lo-"))
    try:
        command = [
            str(converter),
            "--headless",
            f"-env:UserInstallation={profile_dir.as_uri()}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(source_path),
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            diagnostic = NativeDiagnostic(
                "preview.conversion_failed",
                "warning",
                f"A conversão não terminou: {error}.",
            )
            return PreviewResult(False, None, (), (*structural, diagnostic))
        pdf_path = output_dir / f"{source_path.stem}.pdf"
        if completed.returncode != 0 or not pdf_path.is_file() or pdf_path.stat().st_size == 0:
            detail = (completed.stderr or completed.stdout or "sem detalhe").strip()[:500]
            diagnostic = NativeDiagnostic(
                "preview.conversion_failed",
                "warning",
                f"LibreOffice não produziu o PDF: {detail}.",
            )
            return PreviewResult(False, None, (), (*structural, diagnostic))

        png_paths: list[Path] = []
        with pymupdf.open(pdf_path) as document:
            for page_index, page in enumerate(document):
                pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
                png_path = output_dir / f"{source_path.stem}-{page_index + 1}.png"
                pixmap.save(png_path)
                png_paths.append(png_path)
        if not png_paths:
            diagnostic = NativeDiagnostic(
                "preview.empty_pdf",
                "warning",
                "O conversor produziu um PDF sem páginas.",
            )
            return PreviewResult(False, pdf_path, (), (*structural, diagnostic))
        if hashlib.sha256(source_path.read_bytes()).hexdigest() != original_hash:
            raise OoxmlError("O conversor alterou o arquivo fonte, violando a imutabilidade.")
        return PreviewResult(True, pdf_path, tuple(png_paths), structural)
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)
