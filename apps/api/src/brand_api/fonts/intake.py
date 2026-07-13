"""Enriquecimento do draft com fontes adquiridas e materializadas localmente."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any

from brand_api.fonts.catalog import normalize_family
from brand_api.fonts.models import (
    FontRequest,
    FontResolutionUnavailable,
    FontResolver,
    ResolvedFont,
)
from brand_runtime.intake.draft import BrandDraft
from brand_runtime.ir.models import Diagnostic, Evidence

_MAX_RESOLVED_FONTS = 4
_MAX_CANDIDATES = 8


def _eligible(candidate) -> bool:
    """Aceita apenas intenção declarada, não toda fonte observada no PDF."""
    if not isinstance(candidate.value, dict) or candidate.value.get("path") is not None:
        return False
    return any(
        evidence.source_type == "dtcg-tokens"
        or (
            evidence.source_type == "pdf-guideline"
            and (evidence.detail or "").startswith("fonte declarada para ")
        )
        for evidence in candidate.evidence
    )


def _request(value: Any) -> FontRequest | None:
    """Converte candidato hostil em uma variante estrita e limitada."""
    if not isinstance(value, dict):
        return None
    family = value.get("family")
    weight = value.get("weight", 400)
    style = value.get("style", "normal")
    if (
        not isinstance(family, str)
        or not normalize_family(family)
        or isinstance(weight, bool)
        or not isinstance(weight, int)
        or not 100 <= weight <= 900
        or style not in {"normal", "italic"}
    ):
        return None
    return FontRequest(family=family.strip(), weight=weight, style=style)


def _identity(request: FontRequest) -> tuple[str, int, str]:
    """Identidade completa que impede normal/italic ou pesos de se mascararem."""
    return normalize_family(request.family), request.weight, request.style


def _write_blob(package_dir: Path, relative: str, data: bytes) -> str:
    """Materializa bytes por hash sem sobrescrever conteúdo do pacote."""
    sha256 = hashlib.sha256(data).hexdigest()
    destination = package_dir.joinpath(*relative.split("/"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if (
            not destination.is_file()
            or destination.is_symlink()
            or destination.read_bytes() != data
        ):
            raise OSError("O pacote colide com um recurso tipográfico resolvido.")
        return sha256
    descriptor, raw_temporary = tempfile.mkstemp(
        prefix=f".{sha256}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if destination.exists() or destination.is_symlink():
            raise OSError("O pacote colide com um recurso tipográfico resolvido.")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return sha256


def _materialize(
    package_dir: Path,
    manifest: dict[str, str],
    resolved: ResolvedFont,
) -> tuple[str, str]:
    """Grava fonte e licença em paths derivados somente de seus hashes."""
    font_sha256 = hashlib.sha256(resolved.data).hexdigest()
    license_sha256 = hashlib.sha256(resolved.license_data).hexdigest()
    font_path = f"resolved-fonts/{font_sha256}.{resolved.resource.format}"
    license_path = f"resolved-fonts/licenses/{license_sha256}.txt"
    if _write_blob(package_dir, font_path, resolved.data) != font_sha256:
        raise OSError("A fonte materializada perdeu integridade.")
    if _write_blob(package_dir, license_path, resolved.license_data) != license_sha256:
        raise OSError("A licença materializada perdeu integridade.")
    manifest[font_path] = font_sha256
    manifest[license_path] = license_sha256
    return font_path, license_path


def _enrich(candidate, resolved: ResolvedFont, font_path: str) -> None:
    """Liga o recurso confiável ao candidato sem aceitar metadata do navegador."""
    candidate.value = {
        **candidate.value,
        "family": resolved.family,
        "weight": resolved.weight,
        "style": resolved.style,
        "path": font_path,
        "resource": resolved.resource.model_dump(mode="json", by_alias=True),
    }
    candidate.evidence.append(
        Evidence(
            source_type="font-catalog",
            path=font_path,
            detail=resolved.resource.upstream_ref,
            confidence=1.0,
        )
    )


async def resolve_draft_fonts(
    draft: BrandDraft,
    package_dir: Path,
    manifest: dict[str, str],
    resolver: FontResolver,
) -> None:
    """Resolve até quatro variantes declaradas, sem tornar a rede obrigatória."""
    resolved_by_identity: dict[tuple[str, int, str], tuple[ResolvedFont, str]] = {}
    attempted: set[tuple[str, int, str]] = set()
    unavailable = False
    considered = 0
    font_questions = [question for question in draft.questions if question.kind == "pick-font"]
    for question in font_questions:
        for candidate in question.candidates:
            if considered >= _MAX_CANDIDATES or len(resolved_by_identity) >= _MAX_RESOLVED_FONTS:
                break
            if not _eligible(candidate):
                continue
            request = _request(candidate.value)
            if request is None:
                continue
            identity = _identity(request)
            cached = resolved_by_identity.get(identity)
            if cached is not None:
                _enrich(candidate, cached[0], cached[1])
                continue
            if identity in attempted:
                continue
            attempted.add(identity)
            considered += 1
            try:
                resolved = await resolver.resolve(request)
            except FontResolutionUnavailable:
                unavailable = True
                break
            if resolved is None:
                continue
            try:
                font_path, _license_path = _materialize(package_dir, manifest, resolved)
            except OSError:
                unavailable = True
                break
            resolved_by_identity[identity] = (resolved, font_path)
            _enrich(candidate, resolved, font_path)
        if unavailable:
            break

    resolved_families = {identity[0] for identity in resolved_by_identity}
    unresolved_families = {
        normalize_family(request.family)
        for question in font_questions
        for candidate in question.candidates
        if isinstance(candidate.value, dict)
        and candidate.value.get("path") is None
        and (request := _request(candidate.value)) is not None
    }
    fully_resolved_families = resolved_families.difference(unresolved_families)
    if fully_resolved_families:
        draft.diagnostics = [
            diagnostic
            for diagnostic in draft.diagnostics
            if not (
                diagnostic.code == "FONT_FILE_MISSING"
                and normalize_family(diagnostic.target) in fully_resolved_families
            )
        ]
    if unavailable:
        draft.diagnostics.append(
            Diagnostic(
                code="FONT_AUTO_RESOLUTION_FAILED",
                target="fonts",
                message=(
                    "Não foi possível obter automaticamente todas as fontes abertas. "
                    "A importação continuou sem alterar a identidade declarada."
                ),
                resolution="retry-font-resolution",
            )
        )
