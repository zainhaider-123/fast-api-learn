from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from app.ai.pydantic_ai import generate_resume
from app.ai.tool.resume_parser import parse_resume
from app.api.schemas import GenerateRequest, GenerateResponse, ParseRequest, ResumeResponse
from app.models.resume import Resume
from app.services.storage import ResumeStore

router = APIRouter(prefix="/resume", tags=["resume"])


def _store(request: Request) -> ResumeStore:
    return request.app.state.store


@router.post("/generate", response_model=GenerateResponse)
async def resume_generate(body: GenerateRequest, request: Request) -> GenerateResponse:
    result = await generate_resume(body.prompt)
    resume_id, _ = _store(request).save(result.resume)
    return GenerateResponse(
        id=resume_id,
        resume=result.resume,
        changes=result.changes,
        notes=result.notes,
    )

@router.post("/parse", response_model=Resume)
async def resume_parse(body: ParseRequest) -> Resume:
    try:
        return parse_resume(body.text)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("", response_model=ResumeResponse)
async def resume_upsert(resume: Resume, request: Request) -> ResumeResponse:
    resume_id, saved = _store(request).save(resume)
    return ResumeResponse(id=resume_id, resume=saved)


@router.get("/{resume_id}", response_model=Resume)
async def resume_get(resume_id: str, request: Request) -> Resume:
    resume = _store(request).get(resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
