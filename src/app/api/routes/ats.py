from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.ai.tool.ats_checker import score_ats
from app.api.schemas import AtsRequest
from app.models.ats import AtsReport
from app.services.storage import ResumeStore

router = APIRouter(prefix="/resume", tags=["ats"])


class AtsImproveResponse(BaseModel):
    report: AtsReport
    recommendations: list[str] = Field(default_factory=list)


def _store(request: Request) -> ResumeStore:
    return request.app.state.store


@router.post("/{resume_id}/ats", response_model=AtsReport)
async def resume_ats(
    resume_id: str,
    request: Request,
    body: AtsRequest | None = None,
) -> AtsReport:
    resume = _store(request).get(resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    jd = body.job_description if body else ""
    return score_ats(resume, jd)


@router.post("/{resume_id}/ats/improve", response_model=AtsImproveResponse)
async def resume_ats_improve(
    resume_id: str,
    request: Request,
    body: AtsRequest | None = None,
) -> AtsImproveResponse:
    """Run ATS checks and return heuristic suggestions (AI pass can be added later)."""
    resume = _store(request).get(resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    jd = body.job_description if body else ""
    report = score_ats(resume, jd)
    recommendations = list(report.suggestions)
    if report.score < 70:
        recommendations.append(
            "Consider regenerating bullets with stronger action verbs and role keywords."
        )
    return AtsImproveResponse(report=report, recommendations=recommendations)
