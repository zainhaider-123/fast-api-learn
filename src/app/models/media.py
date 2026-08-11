from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl


class LinkMedia(BaseModel):
    """An external URL associated with a project."""

    type: Literal["link"] = "link"
    url: HttpUrl
    label: Annotated[str | None, Field(default=None, max_length=80)] = None


class FileMedia(BaseModel):
    """A local or hosted file reference associated with a project."""

    type: Literal["file"] = "file"
    path: Annotated[str, Field(min_length=1, max_length=500)]
    mime_type: Annotated[str | None, Field(default=None, max_length=100)] = None


Media = Annotated[LinkMedia | FileMedia, Field(discriminator="type")]
