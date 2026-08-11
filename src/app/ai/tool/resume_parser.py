"""Best-effort parsing of raw resume text/JSON into a Resume model."""

from __future__ import annotations

import json

from pydantic import ValidationError

from app.models.resume import Resume


def parse_resume(raw: str) -> Resume:
    """
    Parse pasted resume content into a Resume.

    Prefers JSON (model_validate). Plain text is not fully supported in v1 —
    validation errors are raised so the agent/API can surface them.
    """
    text = raw.strip()
    if not text:
        raise ValueError("Resume text is empty")

    # Try JSON object first.
    if text[0] in "{[":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc
        try:
            return Resume.model_validate(data)
        except ValidationError:
            raise

    # Minimal plain-text heuristic: look for "Name:" / "Email:" lines.
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key in {"name", "email", "phone", "location", "summary"} and value:
            fields[key] = value

    if "name" in fields and "email" in fields:
        payload = {
            "contact": {
                "name": fields["name"],
                "email": fields["email"],
                "phone": fields.get("phone"),
                "location": fields.get("location"),
            },
            "summary": fields.get("summary", ""),
            "experiences": [],
            "educations": [],
            "skills": [],
            "projects": [],
            "certifications": [],
        }
        return Resume.model_validate(payload)

    raise ValueError(
        "Could not parse resume. Provide JSON matching the Resume schema, "
        "or plain text with at least 'Name:' and 'Email:' lines."
    )
