from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.views import views_router

app = FastAPI(
    title="FastAPI Learn",
    description="FastAPI Learn",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(views_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
