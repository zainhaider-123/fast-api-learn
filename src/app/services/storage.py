"""SQLModel-backed resume storage (Postgres in the app, SQLite in tests)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Column, JSON
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine, delete

from app.models.resume import Resume


class ResumeRecord(SQLModel, table=True):
    """Persistence row. Domain validation stays on `Resume`."""

    __tablename__ = "resumes"

    id: str = Field(primary_key=True)
    payload: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))


def _engine_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    return database_url


def _create_engine(database_url: str) -> Engine:
    url = _engine_url(database_url)
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url)


class ResumeStore:
    """CRUD for `Resume` documents in a SQLModel `resumes` table."""

    def __init__(self, database_url: str) -> None:
        self._engine = _create_engine(database_url)
        SQLModel.metadata.create_all(self._engine)

    def close(self) -> None:
        self._engine.dispose()

    def save(self, resume: Resume, resume_id: str | None = None) -> tuple[str, Resume]:
        rid = resume_id or str(uuid.uuid4())
        payload = resume.model_dump(mode="json")
        with Session(self._engine) as session:
            existing = session.get(ResumeRecord, rid)
            if existing is None:
                session.add(ResumeRecord(id=rid, payload=payload))
            else:
                existing.payload = payload
                session.add(existing)
            session.commit()
        return rid, resume

    def get(self, resume_id: str) -> Resume | None:
        with Session(self._engine) as session:
            row = session.get(ResumeRecord, resume_id)
            if row is None:
                return None
            return Resume.model_validate(row.payload)

    def delete(self, resume_id: str) -> bool:
        with Session(self._engine) as session:
            row = session.get(ResumeRecord, resume_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    def clear(self) -> None:
        with Session(self._engine) as session:
            session.exec(delete(ResumeRecord))
            session.commit()
