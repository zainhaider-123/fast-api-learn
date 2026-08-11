from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, computed_field

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Profile(BaseModel):
    """Professional summary / headline shown under contact info."""

    headline: Annotated[str | None, Field(default=None, max_length=160)] = None
    summary: Annotated[
        NonEmptyStr,
        Field(max_length=2000, description="Short professional summary"),
    ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def word_count(self) -> int:
        return len(self.summary.split())
