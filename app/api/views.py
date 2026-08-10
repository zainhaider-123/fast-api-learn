from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


views_router = APIRouter()

@views_router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Home"},
    )
