import uvicorn

from app.app import app
from app.config import settings

__all__ = ["app", "main"]


def main() -> None:
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.env.upper() == "DEV",
    )


if __name__ == "__main__":
    main()
