from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.certifications import Certification
from app.models.contact import ContactInfo
from app.models.education import EducationItem
from app.models.experience import ExperienceItem
from app.models.profile import Profile
from app.models.projects import Project
from app.models.skills import Skill


class Resume(BaseModel):
    """Root resume model — nests all section models."""

    model_config = ConfigDict(
        # Serialize computed fields in model_dump() by default for TeX / AI prompts.
        ser_json_timedelta="iso8601",
    )

    contact: ContactInfo
    profile: Profile | None = None
    # Keep a top-level summary for the plan's v1 shape; prefer profile.summary when set.
    summary: Annotated[str, Field(default="", max_length=2000)] = ""
    experiences: Annotated[
        list[ExperienceItem],
        Field(default_factory=list, max_length=20),
    ]
    educations: Annotated[
        list[EducationItem],
        Field(default_factory=list, max_length=10),
    ]
    skills: Annotated[list[Skill], Field(default_factory=list, max_length=50)]
    projects: Annotated[list[Project], Field(default_factory=list, max_length=15)]
    certifications: Annotated[
        list[Certification],
        Field(default_factory=list, max_length=15),
    ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_name(self) -> str:
        return self.contact.name

    @computed_field  # type: ignore[prop-decorator]
    @property
    def years_of_experience(self) -> float:
        if not self.experiences:
            return 0.0
        return round(sum(item.years for item in self.experiences), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def effective_summary(self) -> str:
        if self.profile and self.profile.summary:
            return self.profile.summary
        return self.summary


class ResumeActionResult(BaseModel):
    """Structured agent output: updated resume plus change log."""

    resume: Resume
    changes: list[str] = Field(default_factory=list)
    notes: str = ""
