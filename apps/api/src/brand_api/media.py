"""Tipos de mídia e respostas seguras para blobs servidos pela API."""

from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import PurePosixPath

from fastapi import Response

EXT_TYPES: dict[str, str] = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".pdf": "application/pdf",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".json": "application/json",
}


def content_type_for(path: str) -> str:
    """Resolve o content type por extensão conhecida, sem confiar no cliente."""
    return EXT_TYPES.get(PurePosixPath(path).suffix.casefold(), "application/octet-stream")


def sniff_content_type(data: bytes) -> str:
    """Reconhece imagens, PDF e o tipo OOXML pelos parts canônicos."""
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data.startswith(b"%PDF"):
        return "application/pdf"
    if data.startswith(b"PK"):
        try:
            with zipfile.ZipFile(BytesIO(data)) as package:
                names = set(package.namelist())
        except (OSError, zipfile.BadZipFile):
            return "application/octet-stream"
        has_presentation = "ppt/presentation.xml" in names
        has_document = "word/document.xml" in names
        if has_presentation and not has_document:
            return EXT_TYPES[".pptx"]
        if has_document and not has_presentation:
            return EXT_TYPES[".docx"]
    return "application/octet-stream"


def asset_response(data: bytes, content_type: str) -> Response:
    """Monta uma resposta sem sniffing e isola SVG em defesa adicional."""
    headers = {"X-Content-Type-Options": "nosniff"}
    if content_type == "image/svg+xml":
        headers["Content-Security-Policy"] = "default-src 'none'"
    return Response(content=data, media_type=content_type, headers=headers)
