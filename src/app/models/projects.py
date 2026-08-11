from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, StringConstraints

from app.models.media import Media

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Highlight = Annotated[NonEmptyStr, Field(max_length=400)]


class Project(BaseModel):
    """A project showcase entry."""

    name: Annotated[NonEmptyStr, Field(max_length=120)]
    description: Annotated[NonEmptyStr, Field(max_length=2000)]
    link: HttpUrl | None = None
    highlights: Annotated[list[Highlight], Field(default_factory=list, max_length=10)]
    media: Media | None = None
