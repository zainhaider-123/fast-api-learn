from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, HttpUrl, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ContactInfo(BaseModel):
    """Contact block shown at the top of a resume."""

    name: Annotated[NonEmptyStr, Field(max_length=120, description="Full name")]
    email: EmailStr
    phone: Annotated[
        str | None,
        Field(default=None, max_length=40, pattern=r"^[\d\s\-().+/]+$"),
    ] = None
    location: Annotated[str | None, Field(default=None, max_length=120)] = None
    website: HttpUrl | None = None
    github: HttpUrl | None = None
    linkedin: HttpUrl | None = None
