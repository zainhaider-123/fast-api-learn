from datetime import date
from typing import Annotated

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    TypeAdapter,
    computed_field,
    field_validator,
    model_validator,
)

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Bullet = Annotated[NonEmptyStr, Field(max_length=500)]


class ExperienceItem(BaseModel):
    """A single work experience entry."""

    title: Annotated[NonEmptyStr | None, Field(default=None, max_length=120)] = None
    position: Annotated[NonEmptyStr | None, Field(default=None, max_length=120)] = None
    company: Annotated[NonEmptyStr, Field(max_length=120)]
    location: Annotated[str | None, Field(default=None, max_length=120)] = None
    start_date: date
    end_date: date | None = None  # None means "present"
    bullets: Annotated[list[Bullet], Field(default_factory=list, max_length=12)]
    is_current: bool = False

    @field_validator("bullets", mode="after")
    @classmethod
    def strip_empty_bullets(cls, value: list[str]) -> list[str]:
        return [b for b in value if b.strip()]

    @model_validator(mode="after")
    def require_title_or_position(self) -> "ExperienceItem":
        if not self.title and not self.position:
            raise ValueError("At least one of 'title' or 'position' is required")
        return self

    @model_validator(mode="after")
    def validate_date_order(self) -> "ExperienceItem":
        end = date.today() if self.is_current or self.end_date is None else self.end_date
        if end < self.start_date:
            raise ValueError("end_date must not be before start_date")
        if self.is_current:
            self.end_date = None
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_title(self) -> str:
        return self.title or self.position or ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def years(self) -> float:
        end = date.today() if self.end_date is None else self.end_date
        days = (end - self.start_date).days
        return round(max(days, 0) / 365.25, 2)


# Validate a bare list of experience items without a wrapper model.
experience_list_adapter: TypeAdapter[list[ExperienceItem]] = TypeAdapter(
    list[ExperienceItem]
)
