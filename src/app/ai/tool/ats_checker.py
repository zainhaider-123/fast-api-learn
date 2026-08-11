"""Deterministic ATS heuristic scoring for Resume models."""

from __future__ import annotations

import re
from collections import Counter

from app.models.ats import AtsReport, SectionResult
from app.models.resume import Resume

_WEIGHT_POINTS = {"high": 15, "medium": 10, "low": 5}

_ACTION_VERBS = {
    "achieved",
    "built",
    "collaborated",
    "created",
    "delivered",
    "designed",
    "developed",
    "engineered",
    "improved",
    "increased",
    "led",
    "managed",
    "optimized",
    "reduced",
    "implemented",
    "launched",
    "owned",
    "shipped",
    "automated",
    "analyzed",
    "architected",
    "mentored",
    "negotiated",
    "presented",
    "spearheaded",
    "transformed",
}

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#.]*", re.IGNORECASE)
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,6}\b")
_MONTH_ABBREV_RE = re.compile(
    r"\b(Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b\.?",
    re.IGNORECASE,
)


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _resume_text(resume: Resume) -> str:
    parts: list[str] = [
        resume.contact.name,
        str(resume.contact.email),
        resume.contact.phone or "",
        resume.contact.location or "",
        resume.effective_summary,
    ]
    for job in resume.experiences:
        parts.extend([job.display_title, job.company, *job.bullets])
    for edu in resume.educations:
        parts.extend([edu.degree, edu.institution])
    for skill in resume.skills:
        parts.append(skill.name)
    for project in resume.projects:
        parts.extend([project.name, project.description, *project.highlights])
    for cert in resume.certifications:
        parts.extend([cert.name, cert.issuer])
    return "\n".join(p for p in parts if p)


def _check_contact(resume: Resume) -> SectionResult:
    missing = []
    if not resume.contact.name:
        missing.append("name")
    if not resume.contact.email:
        missing.append("email")
    if not resume.contact.phone:
        missing.append("phone")
    if not resume.contact.location:
        missing.append("location")
    passed = not missing
    detail = "All key contact fields present" if passed else f"Missing: {', '.join(missing)}"
    score = 100 if passed else max(0, 100 - 25 * len(missing))
    return SectionResult(
        name="contact_info",
        passed=passed,
        weight="high",
        score=score,
        detail=detail,
    )


def _check_one_page(resume: Resume) -> SectionResult:
    # Rough heuristic: ~500–650 words ≈ one page for a dense resume.
    word_count = len(_tokens(_resume_text(resume)))
    bullet_count = sum(len(j.bullets) for j in resume.experiences)
    estimated_lines = (
        8  # header
        + (3 if resume.effective_summary else 0)
        + len(resume.experiences) * 3
        + bullet_count
        + len(resume.educations) * 2
        + (2 if resume.skills else 0)
        + len(resume.projects) * 3
        + len(resume.certifications)
    )
    # ~55 lines fits one page comfortably at 11pt.
    passed = estimated_lines <= 55 and word_count <= 700
    if estimated_lines <= 40:
        score = 100
        detail = f"Compact resume (~{estimated_lines} lines, {word_count} tokens)"
    elif passed:
        score = 85
        detail = f"Likely one page (~{estimated_lines} lines, {word_count} tokens)"
    else:
        score = max(20, 100 - (estimated_lines - 55) * 3)
        detail = f"May exceed one page (~{estimated_lines} lines, {word_count} tokens)"
    return SectionResult(
        name="one_page",
        passed=passed,
        weight="high",
        score=score,
        detail=detail,
    )


def _check_standard_sections(resume: Resume) -> SectionResult:
    present = {
        "contact": True,
        "summary": bool(resume.effective_summary.strip()),
        "experience": bool(resume.experiences),
        "education": bool(resume.educations),
        "skills": bool(resume.skills),
    }
    required = ["contact", "experience", "education", "skills"]
    missing = [s for s in required if not present[s]]
    optional_bonus = 10 if present["summary"] else 0
    passed = not missing
    base = 100 - 20 * len(missing)
    score = min(100, max(0, base + optional_bonus - (0 if present["summary"] else 10)))
    detail = (
        "Standard sections present"
        if passed
        else f"Missing standard sections: {', '.join(missing)}"
    )
    if passed and not present["summary"]:
        detail = "Core sections present; consider adding a summary"
    return SectionResult(
        name="standard_sections",
        passed=passed,
        weight="high",
        score=score,
        detail=detail,
    )


def _check_keyword_match(resume: Resume, job_description: str) -> SectionResult:
    if not job_description.strip():
        return SectionResult(
            name="keyword_match",
            passed=True,
            weight="medium",
            score=70,
            detail="No job description provided; skipped keyword overlap",
        )

    resume_counts = Counter(_tokens(_resume_text(resume)))
    jd_tokens = [t for t in _tokens(job_description) if len(t) > 2]
    if not jd_tokens:
        return SectionResult(
            name="keyword_match",
            passed=True,
            weight="medium",
            score=70,
            detail="Job description had no usable tokens",
        )

    jd_counts = Counter(jd_tokens)
    # Simple overlap: fraction of unique JD tokens present in the resume.
    unique_jd = set(jd_counts)
    overlap = sum(1 for t in unique_jd if t in resume_counts)
    ratio = overlap / len(unique_jd)
    score = int(round(ratio * 100))
    passed = ratio >= 0.25
    detail = f"Matched {overlap}/{len(unique_jd)} job-description tokens ({score}%)"
    return SectionResult(
        name="keyword_match",
        passed=passed,
        weight="medium",
        score=score,
        detail=detail,
    )


def _check_action_verbs(resume: Resume) -> SectionResult:
    bullets = [b for job in resume.experiences for b in job.bullets]
    if not bullets:
        return SectionResult(
            name="action_verbs",
            passed=False,
            weight="medium",
            score=0,
            detail="No experience bullets to evaluate",
        )

    good = 0
    for bullet in bullets:
        first = _tokens(bullet)[:1]
        if first and first[0] in _ACTION_VERBS:
            good += 1
    ratio = good / len(bullets)
    score = int(round(ratio * 100))
    passed = ratio >= 0.6
    detail = f"{good}/{len(bullets)} bullets start with an action verb"
    return SectionResult(
        name="action_verbs",
        passed=passed,
        weight="medium",
        score=score,
        detail=detail,
    )


def _check_formatting(resume: Resume) -> SectionResult:
    text = _resume_text(resume)
    warnings: list[str] = []
    if "|" in text or "\t" in text:
        warnings.append("pipe/tab characters may indicate multi-column layout")
    if re.search(r"<table|<img|┌|│|─┐", text, re.IGNORECASE):
        warnings.append("table/graphic markers detected")
    # Model-based resumes are inherently text-safe.
    score = 100 - 25 * len(warnings)
    passed = not warnings
    detail = (
        "Structured text-safe model (no tables/columns/graphics)"
        if passed
        else "; ".join(warnings)
    )
    return SectionResult(
        name="formatting",
        passed=passed,
        weight="medium",
        score=max(0, score),
        detail=detail,
    )


def _check_dates(resume: Resume) -> SectionResult:
    # Model stores ISO dates; dump for prompt/export may abbreviate in TeX only.
    # Flag if any free-text fields contain abbreviated months without years context.
    free_text = " ".join(
        [
            resume.effective_summary,
            *[b for job in resume.experiences for b in job.bullets],
            *[p.description for p in resume.projects],
        ]
    )
    abbrevs = _MONTH_ABBREV_RE.findall(free_text)
    has_iso_dates = all(
        job.start_date.isoformat() for job in resume.experiences
    ) and all(edu.start_date.isoformat() for edu in resume.educations)
    passed = has_iso_dates and len(abbrevs) == 0
    score = 100 if passed else (70 if has_iso_dates else 40)
    detail = (
        "Dates stored as ISO date objects"
        if passed
        else f"ISO dates present; found {len(abbrevs)} month abbreviations in prose"
        if has_iso_dates
        else "Missing structured dates"
    )
    return SectionResult(
        name="dates",
        passed=passed,
        weight="low",
        score=score,
        detail=detail,
    )


def _check_acronyms(resume: Resume) -> SectionResult:
    text = _resume_text(resume)
    acronyms = sorted(set(_ACRONYM_RE.findall(text)))
    # Heuristic: an acronym is "explained" if a nearby expanded phrase exists —
    # e.g. "Applicant Tracking System (ATS)" or "ATS (Applicant Tracking System)".
    unexplained: list[str] = []
    for acr in acronyms:
        if len(acr) < 2:
            continue
        # Skip very common resume acronyms that ATS parsers know.
        if acr in {"USA", "UK", "GPA", "PDF", "URL", "AI", "API"}:
            continue
        pattern_before = re.compile(
            rf"([A-Za-z]+(?:\s+[A-Za-z]+){{1,5}})\s*\({re.escape(acr)}\)"
        )
        pattern_after = re.compile(
            rf"{re.escape(acr)}\s*\(([A-Za-z]+(?:\s+[A-Za-z]+){{1,5}})\)"
        )
        if not pattern_before.search(text) and not pattern_after.search(text):
            unexplained.append(acr)

    if not acronyms:
        return SectionResult(
            name="acronyms",
            passed=True,
            weight="low",
            score=100,
            detail="No acronyms detected",
        )

    ratio_explained = 1 - (len(unexplained) / len(acronyms))
    score = int(round(ratio_explained * 100))
    passed = len(unexplained) <= max(1, len(acronyms) // 3)
    detail = (
        "Acronyms look explained on first use"
        if not unexplained
        else f"Consider spelling out: {', '.join(unexplained[:8])}"
    )
    return SectionResult(
        name="acronyms",
        passed=passed,
        weight="low",
        score=score,
        detail=detail,
    )


def score_ats(resume: Resume, job_description: str = "") -> AtsReport:
    """Run deterministic ATS heuristics and return a weighted score report."""
    sections = {
        "contact_info": _check_contact(resume),
        "one_page": _check_one_page(resume),
        "standard_sections": _check_standard_sections(resume),
        "keyword_match": _check_keyword_match(resume, job_description),
        "action_verbs": _check_action_verbs(resume),
        "formatting": _check_formatting(resume),
        "dates": _check_dates(resume),
        "acronyms": _check_acronyms(resume),
    }

    total_weight = 0
    weighted = 0.0
    for section in sections.values():
        w = _WEIGHT_POINTS[section.weight]
        total_weight += w
        weighted += section.score * w

    score = int(round(weighted / total_weight)) if total_weight else 0

    warnings: list[str] = []
    suggestions: list[str] = []
    for key, section in sections.items():
        if not section.passed:
            warnings.append(f"{key}: {section.detail}")
            if key == "contact_info":
                suggestions.append("Add missing contact fields (phone, location).")
            elif key == "one_page":
                suggestions.append("Trim bullets and older roles to fit one page.")
            elif key == "standard_sections":
                suggestions.append("Ensure Experience, Education, and Skills sections exist.")
            elif key == "keyword_match":
                suggestions.append("Mirror important keywords from the job description.")
            elif key == "action_verbs":
                suggestions.append("Start bullets with strong action verbs (Built, Led, Improved).")
            elif key == "formatting":
                suggestions.append("Avoid tables, columns, and graphics for ATS parsers.")
            elif key == "dates":
                suggestions.append("Use consistent ISO-style dates (YYYY-MM).")
            elif key == "acronyms":
                suggestions.append("Spell out acronyms on first use, e.g. Applicant Tracking System (ATS).")

    if not resume.effective_summary.strip():
        suggestions.append("Add a short professional summary tailored to the role.")

    # Dedupe while preserving order
    seen: set[str] = set()
    unique_suggestions: list[str] = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique_suggestions.append(s)

    return AtsReport(
        score=score,
        sections=sections,
        warnings=warnings,
        suggestions=unique_suggestions,
    )
