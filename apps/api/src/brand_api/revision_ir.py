"""Leitura compatível do Brand IR para revisões anteriores ao catálogo de logos."""

from __future__ import annotations

from copy import deepcopy
from pathlib import PurePosixPath
from typing import Any

from brand_runtime import BrandIR

from brand_api.models import BrandRevision


def revision_ir_payload(revision: BrandRevision) -> dict[str, Any]:
    """Expõe cada logo preservado no manifest sem reescrever a revisão imutável."""
    payload = deepcopy(revision.ir)
    assets = dict(payload.get("assets") or {})
    known_hashes = {
        item.get("sha256")
        for item in assets.values()
        if isinstance(item, dict) and isinstance(item.get("sha256"), str)
    }
    primary = assets.get("logo.primary") if isinstance(assets.get("logo.primary"), dict) else {}

    for relative, sha256 in sorted(revision.manifest.items()):
        path = PurePosixPath(relative)
        if (
            len(path.parts) < 3
            or path.parts[:2] != ("assets", "logos")
            or path.suffix.casefold() not in {".svg", ".png"}
            or sha256 in known_hashes
        ):
            continue
        image_format = path.suffix.casefold().removeprefix(".")
        assets[f"logo.variant.{sha256}"] = {
            "path": relative,
            "sha256": sha256,
            "format": image_format,
            "evidence": [
                {
                    "sourceType": "svg-asset" if image_format == "svg" else "raster-asset",
                    "path": relative,
                    "page": None,
                    "detail": "arquivo preservado no pacote original da revisão",
                    "confidence": 0.95 if image_format == "svg" else 0.85,
                    "authoritative": False,
                    "confirmedAt": None,
                }
            ],
            "minWidthPx": primary.get("minWidthPx", 96),
            "clearSpaceRatio": primary.get("clearSpaceRatio", 0.25),
        }
        known_hashes.add(sha256)

    payload["assets"] = assets
    return payload


def revision_brand_ir(revision: BrandRevision) -> BrandIR:
    """Valida o IR público já enriquecido com logos legados."""
    return BrandIR.model_validate(revision_ir_payload(revision))
