from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class SkillLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillCategory(StrEnum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    TOOL = "tool"
    SOFT = "soft"
    OTHER = "other"


class Skill(BaseModel):
    """A single skill entry."""

    name: Annotated[NonEmptyStr, Field(max_length=80)]
    category: SkillCategory | None = None
    level: SkillLevel | None = None

    @field_validator("name", mode="after")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()
