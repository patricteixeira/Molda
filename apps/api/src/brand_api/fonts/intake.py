"""Enriquecimento do draft com fontes adquiridas e materializadas localmente."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any, Literal

from brand_api.fonts.catalog import GoogleFontsCatalog, normalize_family
from brand_api.fonts.fontshare import FontshareCatalog
from brand_api.fonts.models import (
    FontRequest,
    FontResolutionUnavailable,
    FontResolver,
    ResolvedFont,
)
from brand_runtime.intake.base import Candidate
from brand_runtime.intake.draft import BrandDraft
from brand_runtime.ir.models import Diagnostic, Evidence, FontResource

MAX_RESOLVED_FONTS = 4
MAX_FONT_RESOLUTION_CANDIDATES = 8
_FONTSHARE_CATALOG = FontshareCatalog.bundled()
_GOOGLE_FONTS_CATALOG = GoogleFontsCatalog.bundled()


def _eligible(candidate) -> bool:
    """Aceita apenas intenção declarada, não toda fonte observada no PDF."""
    if not isinstance(candidate.value, dict) or candidate.value.get("path") is not None:
        return False
    return any(
        evidence.source_type == "dtcg-tokens"
        or evidence.source_type == "manual-entry"
        or (
            evidence.source_type == "pdf-guideline"
            and (evidence.detail or "").startswith("fonte declarada para ")
        )
        for evidence in candidate.evidence
    )


FontCandidateResolution = Literal[
    "local-ready",
    "vendor-hosted",
    "not-found",
    "capacity-reached",
    "failed",
]


def preferred_font_request(
    family: str,
    preferred_weight: int,
    style: Literal["normal", "italic"] = "normal",
) -> FontRequest:
    """Escolhe a variante catalogada mais próxima sem inventar substituição."""
    cleaned_family = " ".join(family.split())
    weights = sorted(
        range(100, 901, 100),
        key=lambda weight: (
            abs(weight - preferred_weight),
            -weight if preferred_weight >= 500 else weight,
        ),
    )
    for weight in weights:
        google = _GOOGLE_FONTS_CATALOG.select(cleaned_family, weight, style)
        if google is not None:
            return FontRequest(family=google.family.name, weight=weight, style=style)
        fontshare = _FONTSHARE_CATALOG.select(cleaned_family, weight, style)
        if fontshare is not None and fontshare.family.license_type == "itf_ffl":
            return FontRequest(family=fontshare.family.name, weight=weight, style=style)
    return FontRequest(family=cleaned_family, weight=preferred_weight, style=style)


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


def _enrich_fontshare(candidate: Candidate, request: FontRequest) -> bool:
    """Liga uma variante FFL ao CSS oficial sem baixar ou re-hospedar seus bytes."""
    selection = _FONTSHARE_CATALOG.select(request.family, request.weight, request.style)
    if selection is None or selection.family.license_type != "itf_ffl":
        return False
    resource = FontResource(
        provider="fontshare-external",
        format="woff2",
        upstream_ref=selection.css_url,
        license_id="ITF-FFL-1.0",
        usage_policy="restricted",
    )
    candidate.value = {
        **candidate.value,
        "family": selection.family.name,
        "weight": selection.variant.weight,
        "style": selection.variant.style,
        "resource": resource.model_dump(mode="json", by_alias=True),
    }
    candidate.evidence.append(
        Evidence(
            source_type="font-catalog",
            detail=(
                f"fontshare@{_FONTSHARE_CATALOG.revision}:"
                f"{selection.family.slug}@{selection.variant.code}"
            ),
            confidence=1.0,
        )
    )
    return True


async def resolve_font_candidate(
    candidate: Candidate,
    package_dir: Path,
    manifest: dict[str, str],
    resolver: FontResolver,
    *,
    allow_local_materialization: bool = True,
) -> FontCandidateResolution:
    """Resolve uma escolha explícita sem obrigar o usuário a reenviar o pacote."""
    if not isinstance(candidate.value, dict):
        return "not-found"
    if candidate.value.get("path") is not None:
        return "local-ready"
    resource = candidate.value.get("resource")
    if isinstance(resource, dict) and resource.get("provider") == "fontshare-external":
        return "vendor-hosted"
    if not _eligible(candidate):
        return "not-found"
    request = _request(candidate.value)
    if request is None:
        return "not-found"
    if not allow_local_materialization:
        return "vendor-hosted" if _enrich_fontshare(candidate, request) else "capacity-reached"
    try:
        resolved = await resolver.resolve(request)
    except FontResolutionUnavailable:
        return "vendor-hosted" if _enrich_fontshare(candidate, request) else "failed"
    if resolved is None:
        return "vendor-hosted" if _enrich_fontshare(candidate, request) else "not-found"
    try:
        font_path, _license_path = _materialize(package_dir, manifest, resolved)
    except OSError:
        return "failed"
    _enrich(candidate, resolved, font_path)
    return "local-ready"


def reconcile_resolved_font_diagnostics(draft: BrandDraft) -> None:
    """Remove falta de arquivo apenas quando toda a família está materializada."""
    font_candidates = [
        candidate
        for question in draft.questions
        if question.kind == "pick-font"
        for candidate in question.candidates
        if isinstance(candidate.value, dict) and _request(candidate.value) is not None
    ]
    locally_resolved = {
        normalize_family(candidate.value["family"])
        for candidate in font_candidates
        if candidate.value.get("path") is not None
    }
    unresolved = {
        normalize_family(candidate.value["family"])
        for candidate in font_candidates
        if candidate.value.get("path") is None
    }
    fully_resolved = locally_resolved.difference(unresolved)
    if fully_resolved:
        draft.diagnostics = [
            diagnostic
            for diagnostic in draft.diagnostics
            if not (
                diagnostic.code == "FONT_FILE_MISSING"
                and normalize_family(diagnostic.target) in fully_resolved
            )
        ]


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
            if (
                considered >= MAX_FONT_RESOLUTION_CANDIDATES
                or len(resolved_by_identity) >= MAX_RESOLVED_FONTS
            ):
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

    # Fontshare permanece uma referência externa: nenhum byte ou CSS passa
    # pelo backend. O navegador só ativa a URL allowlisted após aceite da FFL.
    for question in font_questions:
        for candidate in question.candidates:
            if not _eligible(candidate) or not isinstance(candidate.value, dict):
                continue
            if (
                candidate.value.get("path") is not None
                or candidate.value.get("resource") is not None
            ):
                continue
            request = _request(candidate.value)
            if request is not None:
                _enrich_fontshare(candidate, request)

    reconcile_resolved_font_diagnostics(draft)
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
