from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, model_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class EducationItem(BaseModel):
    """A single education entry."""

    degree: Annotated[NonEmptyStr, Field(max_length=160)]
    institution: Annotated[NonEmptyStr, Field(max_length=160)]
    location: Annotated[str | None, Field(default=None, max_length=120)] = None
    start_date: date
    end_date: date | None = None
    gpa: Annotated[float | None, Field(default=None, ge=0.0, le=4.0)] = None

    @model_validator(mode="after")
    def validate_date_order(self) -> "EducationItem":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self
