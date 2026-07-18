"""Aplicação assíncrona de uma revisão de marca a documentos Word existentes."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import ValidationError

from brand_api.auth import require_token
from brand_api.db import new_id
from brand_api.media import EXT_TYPES, sniff_content_type
from brand_api.models import BrandRevision, Job
from brand_runtime import DocxBrandPlan

router = APIRouter(prefix="/v1", dependencies=[Depends(require_token)])

_DOCX_MIME = EXT_TYPES[".docx"]
_UPLOAD_TOO_LARGE_DETAIL = "O arquivo enviado excede o tamanho máximo permitido."
_INVALID_DOCX_DETAIL = "Envie um documento Word .docx válido e sem macros."


def _safe_source_filename(raw: str | None) -> str:
    normalized = (raw or "documento.docx").replace("\\", "/")
    filename = PurePosixPath(normalized).name.strip()
    if not filename.casefold().endswith(".docx"):
        return "documento.docx"
    stem = filename[:-5].strip(" .")[:100]
    return f"{stem or 'documento'}.docx"


@router.post(
    "/brand-revisions/{revision_id}/docx-brandings",
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_docx_branding(
    revision_id: str,
    request: Request,
    file: Annotated[UploadFile, File()],
) -> dict[str, str]:
    """Armazena o DOCX imutável e enfileira um plano legível de aplicação."""
    with request.app.state.session_factory() as session:
        if session.get(BrandRevision, revision_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revisão de marca não encontrada.",
            )

    limit = request.app.state.settings.max_upload_bytes
    try:
        data = await file.read(limit + 1)
        filename = _safe_source_filename(file.filename)
    finally:
        await file.close()
    if len(data) > limit:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=_UPLOAD_TOO_LARGE_DETAIL,
        )
    if sniff_content_type(data) != _DOCX_MIME:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_INVALID_DOCX_DETAIL)

    source_sha256 = request.app.state.storage.put(data)
    with request.app.state.session_factory() as session:
        job_id = new_id("job")
        session.add(
            Job(
                id=job_id,
                kind="docx-brand-analyze",
                document_id=None,
                params={
                    "brandRevisionId": revision_id,
                    "sourceSha256": source_sha256,
                    "sourceFilename": filename,
                },
                status="queued",
                checks=[],
            )
        )
        session.commit()
    return {"jobId": job_id}


@router.post(
    "/jobs/{analysis_job_id}/docx-brandings",
    status_code=status.HTTP_202_ACCEPTED,
)
def apply_docx_branding(analysis_job_id: str, request: Request) -> dict[str, str]:
    """Enfileira a aplicação usando somente o plano persistido pela análise."""
    with request.app.state.session_factory() as session:
        source_job = session.get(Job, analysis_job_id)
        if source_job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job não encontrado.")
        result = source_job.result if isinstance(source_job.result, dict) else {}
        if source_job.kind != "docx-brand-analyze" or source_job.status != "succeeded":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A análise do Word ainda não está concluída.",
            )
        try:
            plan = DocxBrandPlan.model_validate(result.get("plan"))
        except ValidationError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="O job não possui um plano de aplicação válido.",
            ) from error
        params = source_job.params if isinstance(source_job.params, dict) else {}
        revision_id = params.get("brandRevisionId")
        source_sha256 = params.get("sourceSha256")
        source_filename = params.get("sourceFilename")
        if (
            not isinstance(revision_id, str)
            or not isinstance(source_sha256, str)
            or not request.app.state.storage.has(source_sha256)
            or plan.source.sha256 != source_sha256
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A análise não referencia um Word íntegro.",
            )

        job_id = new_id("job")
        session.add(
            Job(
                id=job_id,
                kind="docx-brand-apply",
                document_id=None,
                params={
                    "brandRevisionId": revision_id,
                    "sourceSha256": source_sha256,
                    "sourceFilename": source_filename,
                    "plan": plan.model_dump(mode="json", by_alias=True),
                    "sourceJobId": analysis_job_id,
                },
                status="queued",
                checks=[],
            )
        )
        session.commit()
    return {"jobId": job_id}
