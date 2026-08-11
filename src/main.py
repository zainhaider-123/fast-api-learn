import uvicorn

from app.app import app

__all__ = ["app", "main"]


def main() -> None:
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
