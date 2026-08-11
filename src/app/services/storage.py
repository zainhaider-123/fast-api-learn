"""In-memory + JSON-file resume storage (no ORM)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from threading import Lock

from app.models.resume import Resume

_DEFAULT_PATH = Path(__file__).resolve().parents[3] / "data" / "resumes.json"


class ResumeStore:
    """Thread-safe store backed by a dict and optional JSON file."""

    def __init__(self, path: Path | None = _DEFAULT_PATH) -> None:
        self._path = path
        self._lock = Lock()
        self._items: dict[str, Resume] = {}
        if self._path is not None:
            self._load()

    def _load(self) -> None:
        assert self._path is not None
        if not self._path.exists():
            return
        raw = json.loads(self._path.read_text())
        for resume_id, payload in raw.items():
            self._items[resume_id] = Resume.model_validate(payload)

    def _persist(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            resume_id: resume.model_dump(mode="json")
            for resume_id, resume in self._items.items()
        }
        self._path.write_text(json.dumps(payload, indent=2))

    def save(self, resume: Resume, resume_id: str | None = None) -> tuple[str, Resume]:
        with self._lock:
            rid = resume_id or str(uuid.uuid4())
            self._items[rid] = resume
            self._persist()
            return rid, resume

    def get(self, resume_id: str) -> Resume | None:
        with self._lock:
            return self._items.get(resume_id)

    def delete(self, resume_id: str) -> bool:
        with self._lock:
            if resume_id not in self._items:
                return False
            del self._items[resume_id]
            self._persist()
            return True

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            self._persist()


# Default process-wide store (tests can replace app.state.store).
store = ResumeStore()
