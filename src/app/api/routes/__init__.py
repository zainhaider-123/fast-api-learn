from fastapi import APIRouter

from app.api.routes import ats, export, resume

api_router = APIRouter()
api_router.include_router(resume.router)
api_router.include_router(ats.router)
api_router.include_router(export.router)
