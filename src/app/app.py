from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

SRC_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=str(SRC_DIR / "templates"))

app = FastAPI(
    title="FastAPI Learn",
    description="FastAPI Learn",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=str(SRC_DIR / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Home"},
    )

@app.get("/ping")
async def ping():
    return {"message": "pong"}
