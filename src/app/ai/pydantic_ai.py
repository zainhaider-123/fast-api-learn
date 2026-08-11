"""Pydantic AI resume-builder agent with typed tools and structured output."""

from __future__ import annotations

import os

from pydantic_ai import Agent

from app.ai.prompt.system import system_prompt
from app.ai.tool.ats_checker import score_ats
from app.ai.tool.resume_parser import parse_resume
from app.ai.tool.tex_generator import build_tex
from app.models.ats import AtsReport
from app.models.resume import Resume, ResumeActionResult


def _default_model() -> str:
    # Avoid requiring an API key at import time (tests / offline).
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic:claude-sonnet-4-6"
    return "test"


agent = Agent(
    _default_model(),
    name="resume_builder",
    instructions=system_prompt,
    output_type=ResumeActionResult,
)


@agent.tool_plain
def tool_build_tex(resume: Resume, template: str = "modern") -> str:
    """Render a Resume to LaTeX (.tex) source using the modern or classic template."""
    if template not in {"modern", "classic"}:
        template = "modern"
    return build_tex(resume, template)  # type: ignore[arg-type]


@agent.tool_plain
def tool_score_ats(resume: Resume, job_description: str = "") -> AtsReport:
    """Score a resume for ATS compatibility; optionally match a job description."""
    return score_ats(resume, job_description)


@agent.tool_plain
def tool_parse_resume(raw: str) -> Resume:
    """Parse pasted resume JSON or simple Name:/Email: text into a Resume model."""
    return parse_resume(raw)


async def generate_resume(prompt: str) -> ResumeActionResult:
    """Run the agent to build or improve a resume from a natural-language prompt."""
    result = await agent.run(prompt)
    return result.output
