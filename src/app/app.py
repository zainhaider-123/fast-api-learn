from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import api_router
from app.config import settings
from app.services.storage import ResumeStore

SRC_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=str(SRC_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    owns_store = getattr(app.state, "store", None) is None
    if owns_store:
        app.state.store = ResumeStore(database_url=settings.database_url)
    yield
    if owns_store:
        app.state.store.close()


app = FastAPI(
    title="Resume Builder",
    description="Pydantic-powered resume builder with ATS scoring and LaTeX export",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(SRC_DIR / "static")), name="static")
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Resume Builder"},
    )


@app.get("/resume", response_class=HTMLResponse)
async def resume_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="resume.html",
        context={"title": "Resume"},
    )


@app.get("/ats", response_class=HTMLResponse)
async def ats_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="ats.html",
        context={"title": "ATS"},
    )


@app.get("/ping")
async def ping():
    return {"message": "pong"}
