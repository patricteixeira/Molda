"""Auditoria offline e determinística do corpus de referências."""

from __future__ import annotations

import hashlib
import math
import unicodedata
import warnings
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import TypeVar

from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, ValidationError

from brand_runtime.template_corpus.models import (
    CORPUS_MANIFEST_FILENAME,
    TemplateCorpusManifest,
    TemplateCorpusReport,
    TemplateFamilyMatch,
    TemplateGrammar,
    TemplatePreviewEvidence,
    TemplateReferenceAssessment,
    TemplateReferenceFile,
    TemplateReferenceManifest,
    TemplateSimilarityPair,
)
from brand_runtime.templates.recommendations import FamilyProfile, family_profiles

_CHUNK_SIZE = 64 * 1024
_MAX_MANIFEST_BYTES = 1024 * 1024
_MAX_PREVIEW_PIXELS = 40_000_000
_STRUCTURAL_SIMILARITY_THRESHOLD = 0.92
_ASPECT_RATIO_TOLERANCE = math.log(1.05)
_FAMILY_VARIANT_THRESHOLD = 0.82
_NEW_COMPOSITION_THRESHOLD = 0.68
_PIL_FORMAT_BY_MEDIA = {
    "image/png": "PNG",
    "image/jpeg": "JPEG",
    "image/webp": "WEBP",
}

ModelT = TypeVar("ModelT", bound=BaseModel)


class TemplateCorpusError(ValueError):
    """Falha de contrato, segurança ou integridade no corpus."""

    def __init__(self, code: str, message: str, *, path: str | None = None) -> None:
        """Preserva um código estável e um path relativo seguro."""
        super().__init__(message)
        self.code = code
        self.path = path

    def __str__(self) -> str:
        """Inclui o path relativo sem vazar a raiz local."""
        message = super().__str__()
        return f"{message} Caminho: {self.path}." if self.path else message


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _read_manifest(path: Path, model: type[ModelT], *, relative: str) -> ModelT:
    try:
        if path.is_symlink() or not path.is_file():
            raise TemplateCorpusError(
                "MANIFEST_MISSING",
                "O corpus não contém todos os manifestos declarados.",
                path=relative,
            )
        if path.stat().st_size > _MAX_MANIFEST_BYTES:
            raise TemplateCorpusError(
                "MANIFEST_TOO_LARGE",
                "Um manifesto excede o limite de 1 MiB.",
                path=relative,
            )
        return model.model_validate_json(path.read_text(encoding="utf-8"))
    except TemplateCorpusError:
        raise
    except (OSError, UnicodeError, ValidationError) as exc:
        raise TemplateCorpusError(
            "MANIFEST_INVALID",
            "Um manifesto não corresponde ao contrato Template Corpus 0.1.0.",
            path=relative,
        ) from exc


def _inventory(base: Path) -> dict[str, Path]:
    inventory: dict[str, Path] = {}
    folded: set[str] = set()
    try:
        entries = sorted(base.rglob("*"), key=lambda item: item.as_posix().casefold())
    except OSError as exc:
        raise TemplateCorpusError(
            "CORPUS_UNREADABLE",
            "Não foi possível ler o corpus.",
        ) from exc
    for entry in entries:
        relative = entry.relative_to(base).as_posix()
        if entry.is_symlink():
            raise TemplateCorpusError(
                "SYMLINK_FORBIDDEN",
                "O corpus não pode conter links simbólicos.",
                path=relative,
            )
        if not entry.is_file():
            continue
        key = unicodedata.normalize("NFC", relative).casefold()
        if key in folded:
            raise TemplateCorpusError(
                "PATH_COLLISION",
                "O corpus contém paths que colidem sem distinguir maiúsculas.",
                path=relative,
            )
        folded.add(key)
        inventory[relative] = entry
    return inventory


def _difference_hash(image: Image.Image) -> str:
    grayscale = image.convert("L").resize((9, 8), Image.Resampling.BOX)
    pixels = (
        list(grayscale.get_flattened_data())
        if hasattr(grayscale, "get_flattened_data")
        else list(grayscale.getdata())
    )
    bits = 0
    for row in range(8):
        offset = row * 9
        for column in range(8):
            bits = (bits << 1) | int(pixels[offset + column] > pixels[offset + column + 1])
    return f"{bits:016x}"


def _preview_evidence(
    path: Path,
    *,
    relative: str,
    declared: TemplateReferenceFile,
    digest: str,
) -> TemplatePreviewEvidence:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as source:
                if source.format != _PIL_FORMAT_BY_MEDIA[declared.media_type]:
                    raise TemplateCorpusError(
                        "PREVIEW_FORMAT_MISMATCH",
                        "O conteúdo da prévia não corresponde ao mediaType declarado.",
                        path=relative,
                    )
                if getattr(source, "n_frames", 1) != 1:
                    raise TemplateCorpusError(
                        "PREVIEW_ANIMATED",
                        "A prévia precisa conter apenas um quadro.",
                        path=relative,
                    )
                width, height = source.size
                if width * height > _MAX_PREVIEW_PIXELS:
                    raise TemplateCorpusError(
                        "PREVIEW_TOO_LARGE",
                        "A prévia excede o limite de 40 megapixels.",
                        path=relative,
                    )
                source.load()
                normalized = ImageOps.exif_transpose(source)
                width, height = normalized.size
                difference_hash = _difference_hash(normalized)
    except TemplateCorpusError:
        raise
    except (
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise TemplateCorpusError(
            "PREVIEW_INVALID",
            "A prévia declarada não é uma imagem raster válida e segura.",
            path=relative,
        ) from exc
    return TemplatePreviewEvidence(
        path=relative,
        media_type=declared.media_type,
        width_px=width,
        height_px=height,
        aspect_ratio=round(width / height, 6),
        sha256=digest,
        difference_hash=difference_hash,
    )


def _jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    union = left_set | right_set
    return len(left_set & right_set) / len(union) if union else 1.0


def _score_family(grammar: TemplateGrammar, family: FamilyProfile) -> tuple[float, ...]:
    distance = math.sqrt(
        sum(
            (value - target) ** 2
            for value, target in zip(grammar.axes.values(), family.axes, strict=True)
        )
    )
    axis_similarity = max(0.0, 1.0 - distance / math.sqrt(24.0))
    composition_overlap = _jaccard(grammar.compositions, family.compositions)
    surface_overlap = _jaccard(grammar.surfaces, family.surfaces)
    score = 0.75 * axis_similarity + 0.15 * composition_overlap + 0.10 * surface_overlap
    return score, axis_similarity, composition_overlap, surface_overlap


def _nearest_family(grammar: TemplateGrammar) -> TemplateFamilyMatch:
    ranked = []
    for family_id, family in family_profiles().items():
        score = _score_family(grammar, family)
        ranked.append((score[0], family_id, score))
    _, family_id, components = sorted(ranked, key=lambda item: (-item[0], item[1]))[0]
    score, axis_similarity, composition_overlap, surface_overlap = components
    return TemplateFamilyMatch(
        family_id=family_id,
        score=round(score, 6),
        axis_similarity=round(axis_similarity, 6),
        composition_overlap=round(composition_overlap, 6),
        surface_overlap=round(surface_overlap, 6),
    )


def _hamming_similarity(left: str, right: str) -> float:
    distance = (int(left, 16) ^ int(right, 16)).bit_count()
    return 1.0 - distance / 64.0


def _similarity_pairs(
    evidence: dict[str, TemplatePreviewEvidence],
) -> list[TemplateSimilarityPair]:
    pairs: list[TemplateSimilarityPair] = []
    reference_ids = sorted(evidence)
    for left_index, left_id in enumerate(reference_ids):
        left = evidence[left_id]
        for right_id in reference_ids[left_index + 1 :]:
            right = evidence[right_id]
            structural_similarity = _hamming_similarity(
                left.difference_hash,
                right.difference_hash,
            )
            exact = left.sha256 == right.sha256
            aspect_close = (
                abs(math.log(left.aspect_ratio / right.aspect_ratio)) <= _ASPECT_RATIO_TOLERANCE
            )
            if not exact and (
                structural_similarity < _STRUCTURAL_SIMILARITY_THRESHOLD or not aspect_close
            ):
                continue
            pairs.append(
                TemplateSimilarityPair(
                    left_reference_id=left_id,
                    right_reference_id=right_id,
                    kind="exact-duplicate" if exact else "structural-near-duplicate",
                    structural_similarity=round(structural_similarity, 6),
                )
            )
    return pairs


def _corpus_identity(
    inventory: dict[str, Path],
    *,
    max_total_bytes: int,
) -> tuple[int, str, dict[str, str]]:
    identity = hashlib.sha256()
    digests: dict[str, str] = {}
    total_bytes = 0
    for relative in sorted(inventory, key=str.casefold):
        target = inventory[relative]
        try:
            size = target.stat().st_size
        except OSError as exc:
            raise TemplateCorpusError(
                "FILE_UNREADABLE",
                "Não foi possível ler um arquivo do corpus.",
                path=relative,
            ) from exc
        total_bytes += size
        if total_bytes > max_total_bytes:
            raise TemplateCorpusError(
                "CORPUS_TOO_LARGE",
                "O corpus excede o tamanho total autorizado.",
            )
        try:
            digest = _sha256(target)
        except OSError as exc:
            raise TemplateCorpusError(
                "FILE_UNREADABLE",
                "Não foi possível ler um arquivo do corpus.",
                path=relative,
            ) from exc
        digests[relative] = digest
        identity.update(relative.encode("utf-8"))
        identity.update(b"\0")
        identity.update(digest.encode("ascii"))
        identity.update(b"\0")
        identity.update(str(size).encode("ascii"))
        identity.update(b"\n")
    return total_bytes, identity.hexdigest(), digests


def _validate_declared_files(
    manifests: dict[str, TemplateReferenceManifest],
    inventory: dict[str, Path],
    digests: dict[str, str],
) -> dict[str, TemplatePreviewEvidence]:
    previews: dict[str, TemplatePreviewEvidence] = {}
    for manifest_path in sorted(manifests, key=str.casefold):
        manifest = manifests[manifest_path]
        reference_dir = PurePosixPath(manifest_path).parent
        for declared in sorted(manifest.files, key=lambda item: item.path.casefold()):
            relative = (reference_dir / declared.path).as_posix()
            target = inventory[relative]
            try:
                size = target.stat().st_size
            except OSError as exc:
                raise TemplateCorpusError(
                    "FILE_UNREADABLE",
                    "Não foi possível ler um arquivo declarado.",
                    path=relative,
                ) from exc
            if size != declared.size:
                raise TemplateCorpusError(
                    "SIZE_MISMATCH",
                    "O tamanho do arquivo não corresponde ao manifesto.",
                    path=relative,
                )
            if digests[relative] != declared.sha256:
                raise TemplateCorpusError(
                    "HASH_MISMATCH",
                    "O SHA-256 do arquivo não corresponde ao manifesto.",
                    path=relative,
                )
            if declared.role == "preview":
                previews[manifest.id] = _preview_evidence(
                    target,
                    relative=relative,
                    declared=declared,
                    digest=digests[relative],
                )
    return previews


def _classify(
    manifests: dict[str, TemplateReferenceManifest],
    previews: dict[str, TemplatePreviewEvidence],
    pairs: list[TemplateSimilarityPair],
) -> list[TemplateReferenceAssessment]:
    exact_duplicate_of: dict[str, str] = {}
    near_duplicates: dict[str, list[str]] = {}
    for pair in pairs:
        if pair.kind == "exact-duplicate":
            exact_duplicate_of.setdefault(pair.right_reference_id, pair.left_reference_id)
        else:
            near_duplicates.setdefault(pair.left_reference_id, []).append(pair.right_reference_id)
            near_duplicates.setdefault(pair.right_reference_id, []).append(pair.left_reference_id)

    by_id = {manifest.id: manifest for manifest in manifests.values()}
    assessments: list[TemplateReferenceAssessment] = []
    for reference_id in sorted(by_id):
        manifest = by_id[reference_id]
        nearest = _nearest_family(manifest.grammar) if manifest.grammar is not None else None
        duplicate_of = exact_duplicate_of.get(reference_id)
        findings: list[str] = []
        if manifest.intent == "negative-control":
            disposition = "negative-control"
            findings.append(
                "Controle negativo: preservado para testar redundância, não para síntese."
            )
        elif duplicate_of is not None:
            disposition = "redundant"
            findings.append(f"Conteúdo idêntico à referência «{duplicate_of}».")
        elif manifest.grammar is None:
            disposition = "needs-annotation"
            findings.append("A gramática visual precisa ser anotada antes da classificação.")
        elif nearest is not None and nearest.score >= _FAMILY_VARIANT_THRESHOLD:
            disposition = "family-variant"
            findings.append(
                f"Variação próxima da família «{nearest.family_id}»; comparar composição e slots."
            )
        elif nearest is not None and nearest.score >= _NEW_COMPOSITION_THRESHOLD:
            disposition = "new-composition"
            findings.append(
                f"Gramática adjacente a «{nearest.family_id}», com distância útil para composição."
            )
        else:
            disposition = "family-gap"
            family_id = nearest.family_id if nearest is not None else "catálogo"
            findings.append(
                f"Lacuna em relação a «{family_id}»; exige crítica humana antes de propor família."
            )
        if manifest.intent == "holdout":
            findings.append("Holdout: manter fora da síntese e usar somente na validação.")
        if reference_id in near_duplicates:
            related = ", ".join(f"«{item}»" for item in sorted(near_duplicates[reference_id]))
            findings.append(f"Estrutura raster muito próxima de {related}; revisar recoloração.")
        assessments.append(
            TemplateReferenceAssessment(
                reference_id=reference_id,
                title_pt=manifest.title_pt,
                intent=manifest.intent,
                preview=previews[reference_id],
                disposition=disposition,
                nearest_family=nearest,
                duplicate_of=duplicate_of,
                findings_pt=findings,
            )
        )
    return assessments


def audit_template_corpus(
    corpus_dir: Path,
    *,
    max_references: int = 200,
    max_total_bytes: int = 2 * 2**30,
) -> TemplateCorpusReport:
    """Valida e classifica um corpus sem executar fontes nem promover templates."""
    supplied = Path(corpus_dir)
    if supplied.is_symlink():
        raise TemplateCorpusError(
            "CORPUS_SYMLINK_FORBIDDEN",
            "A raiz do corpus não pode ser um link simbólico.",
        )
    try:
        base = supplied.resolve(strict=True)
    except OSError as exc:
        raise TemplateCorpusError(
            "CORPUS_MISSING",
            "O Template Corpus informado não é um diretório legível.",
        ) from exc
    if not base.is_dir():
        raise TemplateCorpusError(
            "CORPUS_MISSING",
            "O Template Corpus informado não é um diretório legível.",
        )

    inventory = _inventory(base)
    root_manifest = _read_manifest(
        base / CORPUS_MANIFEST_FILENAME,
        TemplateCorpusManifest,
        relative=CORPUS_MANIFEST_FILENAME,
    )
    if len(root_manifest.references) > max_references:
        raise TemplateCorpusError(
            "TOO_MANY_REFERENCES",
            "O corpus contém mais referências do que o limite autorizado.",
        )

    manifests: dict[str, TemplateReferenceManifest] = {}
    expected_paths = {CORPUS_MANIFEST_FILENAME, *root_manifest.references}
    for manifest_path in sorted(root_manifest.references, key=str.casefold):
        manifest = _read_manifest(
            base / Path(*PurePosixPath(manifest_path).parts),
            TemplateReferenceManifest,
            relative=manifest_path,
        )
        expected_id = PurePosixPath(manifest_path).parent.name
        if manifest.id != expected_id:
            raise TemplateCorpusError(
                "REFERENCE_ID_MISMATCH",
                "O id da referência precisa ser igual ao nome do seu diretório.",
                path=manifest_path,
            )
        manifests[manifest_path] = manifest
        reference_dir = PurePosixPath(manifest_path).parent
        expected_paths.update((reference_dir / item.path).as_posix() for item in manifest.files)

    actual_paths = set(inventory)
    missing = sorted(expected_paths - actual_paths, key=str.casefold)
    unexpected = sorted(actual_paths - expected_paths, key=str.casefold)
    if missing:
        raise TemplateCorpusError(
            "FILE_MISSING",
            "O corpus não contém todos os arquivos declarados.",
            path=missing[0],
        )
    if unexpected:
        raise TemplateCorpusError(
            "FILE_UNDECLARED",
            "O corpus contém arquivo não declarado.",
            path=unexpected[0],
        )

    total_bytes, corpus_sha256, digests = _corpus_identity(
        inventory,
        max_total_bytes=max_total_bytes,
    )
    previews = _validate_declared_files(manifests, inventory, digests)
    pairs = _similarity_pairs(previews)
    assessments = _classify(manifests, previews, pairs)
    return TemplateCorpusReport(
        corpus_id=root_manifest.id,
        title_pt=root_manifest.title_pt,
        reference_count=len(manifests),
        total_bytes=total_bytes,
        corpus_sha256=corpus_sha256,
        assessments=assessments,
        similarity_pairs=pairs,
    )
