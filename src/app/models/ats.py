from typing import Annotated

from pydantic import BaseModel, Field, computed_field


class SectionResult(BaseModel):
    """Result of a single ATS heuristic check."""

    name: Annotated[str, Field(min_length=1, max_length=80)]
    passed: bool
    weight: Annotated[str, Field(pattern=r"^(high|medium|low)$")]
    score: Annotated[int, Field(ge=0, le=100)]
    detail: str = ""


class AtsReport(BaseModel):
    """Aggregated ATS compatibility report for a resume."""

    score: Annotated[int, Field(ge=0, le=100)]
    sections: dict[str, SectionResult]
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passed_count(self) -> int:
        return sum(1 for s in self.sections.values() if s.passed)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def failed_count(self) -> int:
        return sum(1 for s in self.sections.values() if not s.passed)
