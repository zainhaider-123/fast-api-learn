from pydantic import BaseModel, Field

from app.models.resume import Resume, ResumeActionResult


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)


class ParseRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)


class AtsRequest(BaseModel):
    job_description: str = Field(default="", max_length=20_000)


class ResumeResponse(BaseModel):
    id: str
    resume: Resume


class GenerateResponse(ResumeActionResult):
    id: str
