"""Upload e enfileiramento do round-trip de apresentações PPTX."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import ValidationError

from brand_api.auth import require_token
from brand_api.db import new_id
from brand_api.media import EXT_TYPES, sniff_content_type
from brand_api.models import Job
from brand_runtime import FixPlan

router = APIRouter(prefix="/v1", dependencies=[Depends(require_token)])

_PPTX_MIME = EXT_TYPES[".pptx"]
_UPLOAD_TOO_LARGE_DETAIL = "O arquivo enviado excede o tamanho máximo permitido."
_INVALID_PPTX_DETAIL = "Envie uma apresentação PPTX válida."


def _completed_pptx_export(job: Job | None, request: Request) -> tuple[str, str]:
    """Valida o job original e retorna documento + SHA do baseline."""
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job não encontrado.")
    result = job.result if isinstance(job.result, dict) else {}
    sha256 = result.get("sha256")
    if (
        job.kind != "export"
        or job.status != "succeeded"
        or job.document_id is None
        or result.get("format") != "pptx"
        or not isinstance(sha256, str)
        or not request.app.state.storage.has(sha256)
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O round-trip exige um export PPTX concluído e íntegro.",
        )
    return job.document_id, sha256


@router.post("/jobs/{export_job_id}/roundtrips", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_roundtrip(
    export_job_id: str,
    request: Request,
    file: Annotated[UploadFile, File()],
) -> dict[str, str]:
    """Armazena o PPTX editado e enfileira parser, linter e Fix Plan."""
    with request.app.state.session_factory() as session:
        document_id, baseline_sha256 = _completed_pptx_export(
            session.get(Job, export_job_id),
            request,
        )

    limit = request.app.state.settings.max_upload_bytes
    try:
        data = await file.read(limit + 1)
    finally:
        await file.close()
    if len(data) > limit:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=_UPLOAD_TOO_LARGE_DETAIL,
        )
    if sniff_content_type(data) != _PPTX_MIME:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_INVALID_PPTX_DETAIL)

    edited_sha256 = request.app.state.storage.put(data)
    with request.app.state.session_factory() as session:
        job_id = new_id("job")
        session.add(
            Job(
                id=job_id,
                kind="roundtrip-lint",
                document_id=document_id,
                params={
                    "baselineSha256": baseline_sha256,
                    "editedSha256": edited_sha256,
                    "sourceJobId": export_job_id,
                },
                status="queued",
                checks=[],
            )
        )
        session.commit()
    return {"jobId": job_id}


@router.post("/jobs/{roundtrip_job_id}/fixes", status_code=status.HTTP_202_ACCEPTED)
def enqueue_roundtrip_fix(roundtrip_job_id: str, request: Request) -> dict[str, str]:
    """Enfileira a correção usando somente o plano persistido no job anterior."""
    with request.app.state.session_factory() as session:
        source_job = session.get(Job, roundtrip_job_id)
        if source_job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job não encontrado.")
        result = source_job.result if isinstance(source_job.result, dict) else {}
        if (
            source_job.kind != "roundtrip-lint"
            or source_job.status != "succeeded"
            or source_job.document_id is None
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A análise de round-trip ainda não está concluída.",
            )
        try:
            plan = FixPlan.model_validate(result.get("fixPlan"))
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="O job não possui um plano de correção válido.",
            ) from exc
        if not plan.operations:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="O arquivo não possui correções automáticas pendentes.",
            )

        job_id = new_id("job")
        session.add(
            Job(
                id=job_id,
                kind="roundtrip-fix",
                document_id=source_job.document_id,
                params={
                    "baselineSha256": plan.baseline_sha256,
                    "editedSha256": plan.edited_sha256,
                    "fixPlan": plan.model_dump(mode="json", by_alias=True),
                    "sourceJobId": roundtrip_job_id,
                },
                status="queued",
                checks=[],
            )
        )
        session.commit()
    return {"jobId": job_id}
