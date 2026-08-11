from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Certification(BaseModel):
    """A professional certification or credential."""

    name: Annotated[NonEmptyStr, Field(max_length=160)]
    issuer: Annotated[NonEmptyStr, Field(max_length=160)]
    date_earned: date | None = None
    expires: date | None = None
    credential_url: HttpUrl | None = None
    credential_id: Annotated[str | None, Field(default=None, max_length=80)] = None
