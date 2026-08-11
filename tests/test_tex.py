from pathlib import Path

import pytest

from app.ai.tool.tex_generator import build_tex
from app.models import Resume
from app.services.latex import escape_latex

GOLDEN_DIR = Path(__file__).parent / "golden"

SAMPLE_RESUME = {
    "contact": {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+1 (555) 010-2030",
        "location": "London, UK",
        "website": "https://ada.dev",
        "github": "https://github.com/ada",
        "linkedin": "https://linkedin.com/in/ada",
    },
    "summary": "Mathematician & first programmer; 100% dedicated to engines.",
    "experiences": [
        {
            "title": "Software Engineer",
            "company": "Analytical Engines Ltd",
            "location": "London",
            "start_date": "2020-01-01",
            "end_date": "2022-06-30",
            "bullets": [
                "Built differential engines with 50% fewer errors",
                "Collaborated on notes for Babbage's machine",
            ],
        }
    ],
    "educations": [
        {
            "degree": "BSc Mathematics",
            "institution": "University of London",
            "location": "London",
            "start_date": "2016-09-01",
            "end_date": "2019-06-01",
            "gpa": 3.9,
        }
    ],
    "skills": [
        {"name": "Python", "category": "language", "level": "expert"},
        {"name": "LaTeX", "category": "tool", "level": "advanced"},
    ],
    "projects": [
        {
            "name": "Analytical Engine Notes",
            "description": "Annotated translation with algorithms.",
            "link": "https://example.com/engine",
            "highlights": ["First published algorithm"],
        }
    ],
    "certifications": [
        {
            "name": "Chartered Mathematician",
            "issuer": "IMA",
            "date_earned": "2021-05-01",
        }
    ],
}


class TestEscapeLatex:
    def test_escapes_specials(self):
        assert escape_latex(r"100% of A & B $_#") == (
            r"100\% of A \& B \$\_\#"
        )

    def test_escapes_braces_and_slash(self):
        assert escape_latex(r"{a}\b") == r"\{a\}\textbackslash{}b"

    def test_none_and_empty(self):
        assert escape_latex(None) == ""
        assert escape_latex("") == ""


class TestBuildTex:
    def test_modern_matches_golden(self):
        resume = Resume.model_validate(SAMPLE_RESUME)
        actual = build_tex(resume, "modern")
        expected = (GOLDEN_DIR / "modern.tex").read_text()
        assert actual == expected

    def test_classic_matches_golden(self):
        resume = Resume.model_validate(SAMPLE_RESUME)
        actual = build_tex(resume, "classic")
        expected = (GOLDEN_DIR / "classic.tex").read_text()
        assert actual == expected

    def test_unknown_template_raises(self):
        resume = Resume.model_validate(SAMPLE_RESUME)
        with pytest.raises(ValueError, match="Unknown TeX template"):
            build_tex(resume, "fancy")  # type: ignore[arg-type]

    def test_escapes_user_content(self):
        resume = Resume.model_validate(
            {
                **SAMPLE_RESUME,
                "summary": "C++ & Rust; costs $5 #1",
                "experiences": [
                    {
                        "title": "Eng_Lead",
                        "company": "A&B Corp",
                        "start_date": "2020-01-01",
                        "end_date": "2021-01-01",
                        "bullets": ["Owned 100% of pipeline"],
                    }
                ],
            }
        )
        tex = build_tex(resume, "modern")
        assert r"C++ \& Rust; costs \$5 \#1" in tex
        assert r"Eng\_Lead" in tex
        assert r"A\&B Corp" in tex
        assert r"100\%" in tex
