from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, Response

from app.ai.tool.tex_generator import TemplateName, build_tex
from app.services.storage import ResumeStore

router = APIRouter(prefix="/resume", tags=["export"])


def _store(request: Request) -> ResumeStore:
    return request.app.state.store


@router.get("/{resume_id}/export.tex", response_class=PlainTextResponse)
async def export_tex(
    resume_id: str,
    request: Request,
    template: TemplateName = Query(default="modern"),
) -> PlainTextResponse:
    resume = _store(request).get(resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    tex = build_tex(resume, template)
    return PlainTextResponse(
        content=tex,
        media_type="application/x-tex",
        headers={
            "Content-Disposition": f'attachment; filename="resume-{resume_id}.tex"'
        },
    )


@router.get("/{resume_id}/export.pdf")
async def export_pdf(resume_id: str, request: Request) -> Response:
    resume = _store(request).get(resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    # PDF compilation is optional; degrade gracefully when LaTeX is unavailable.
    raise HTTPException(
        status_code=501,
        detail="PDF export requires a LaTeX compiler (pdflatex/xelatex). "
        "Download export.tex and compile locally, or install TinyTeX.",
    )
