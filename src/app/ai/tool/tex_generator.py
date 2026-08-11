"""Build compilable LaTeX (.tex) resume files from a Resume model."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.resume import Resume
from app.services.latex import escape_latex

_TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates" / "tex"

TemplateName = Literal["modern", "classic"]


class TexTemplate(StrEnum):
    MODERN = "modern"
    CLASSIC = "classic"


def _format_date(value: date | None, *, current: bool = False) -> str:
    if current or value is None:
        return "Present"
    return value.strftime("%b %Y")


def _format_range(
    start: date,
    end: date | None,
    *,
    is_current: bool = False,
) -> str:
    start_s = _format_date(start)
    end_s = _format_date(end, current=is_current or end is None)
    return f"{start_s} -- {end_s}"


def _url_str(value: Any) -> str:
    return "" if value is None else str(value)


def _resume_context(resume: Resume) -> dict[str, Any]:
    contact = resume.contact
    website = _url_str(contact.website)
    github = _url_str(contact.github)
    linkedin = _url_str(contact.linkedin)

    experiences = []
    for job in resume.experiences:
        experiences.append(
            {
                "title": escape_latex(job.display_title),
                "company": escape_latex(job.company),
                "location": escape_latex(job.location),
                "dates": escape_latex(
                    _format_range(job.start_date, job.end_date, is_current=job.is_current)
                ),
                "bullets": [escape_latex(b) for b in job.bullets],
            }
        )

    educations = []
    for edu in resume.educations:
        educations.append(
            {
                "degree": escape_latex(edu.degree),
                "institution": escape_latex(edu.institution),
                "location": escape_latex(edu.location),
                "dates": escape_latex(_format_range(edu.start_date, edu.end_date)),
                "gpa": f"{edu.gpa:.2f}" if edu.gpa is not None else None,
            }
        )

    projects = []
    for project in resume.projects:
        link = _url_str(project.link)
        projects.append(
            {
                "name": escape_latex(project.name),
                "description": escape_latex(project.description),
                "link": link,
                "link_label": escape_latex(link.replace("https://", "").replace("http://", "")),
                "highlights": [escape_latex(h) for h in project.highlights],
            }
        )

    certifications = []
    for cert in resume.certifications:
        certifications.append(
            {
                "name": escape_latex(cert.name),
                "issuer": escape_latex(cert.issuer),
                "date": escape_latex(_format_date(cert.date_earned))
                if cert.date_earned
                else None,
            }
        )

    skill_names = [escape_latex(s.name) for s in resume.skills]

    return {
        "contact": {
            "name": escape_latex(contact.name),
            "email": escape_latex(str(contact.email)),
            "phone": escape_latex(contact.phone),
            "location": escape_latex(contact.location),
            "website": website,
            "website_label": escape_latex(
                website.replace("https://", "").replace("http://", "")
            )
            if website
            else "",
            "github": github,
            "linkedin": linkedin,
        },
        "summary": escape_latex(resume.effective_summary),
        "experiences": experiences,
        "educations": educations,
        "skills": resume.skills,
        "skills_line": ", ".join(skill_names),
        "projects": projects,
        "certifications": certifications,
    }


def _environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def build_tex(
    resume: Resume,
    template: TemplateName | TexTemplate = "modern",
) -> str:
    """Render a Resume model to LaTeX source using the given template."""
    name = template.value if isinstance(template, TexTemplate) else template
    if name not in {t.value for t in TexTemplate}:
        raise ValueError(f"Unknown TeX template: {name!r}")

    env = _environment()
    jinja_template = env.get_template(f"{name}.tex.j2")
    return jinja_template.render(**_resume_context(resume))
