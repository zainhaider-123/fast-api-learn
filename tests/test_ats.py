from app.ai.tool.ats_checker import score_ats
from app.models import Resume

STRONG_RESUME = {
    "contact": {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+1 555 010 2030",
        "location": "London, UK",
    },
    "summary": "Software engineer focused on Python backends and Applicant Tracking System (ATS) tooling.",
    "experiences": [
        {
            "title": "Software Engineer",
            "company": "Analytical Engines",
            "location": "London",
            "start_date": "2020-01-01",
            "end_date": "2023-01-01",
            "bullets": [
                "Built Python APIs for resume scoring",
                "Improved ATS keyword matching by 30%",
                "Led migration to FastAPI services",
            ],
        }
    ],
    "educations": [
        {
            "degree": "BSc Computer Science",
            "institution": "University of London",
            "start_date": "2016-09-01",
            "end_date": "2019-06-01",
        }
    ],
    "skills": [
        {"name": "Python"},
        {"name": "FastAPI"},
        {"name": "ATS"},
    ],
    "projects": [],
    "certifications": [],
}


WEAK_RESUME = {
    "contact": {
        "name": "Bob",
        "email": "bob@example.com",
    },
    "summary": "",
    "experiences": [
        {
            "title": "Helper",
            "company": "Somewhere",
            "start_date": "2022-01-01",
            "end_date": "2023-01-01",
            "bullets": [
                "responsible for stuff",
                "also did things with KPI metrics",
            ],
        }
    ],
    "educations": [],
    "skills": [],
    "projects": [],
    "certifications": [],
}


class TestScoreAts:
    def test_strong_resume_scores_high(self):
        resume = Resume.model_validate(STRONG_RESUME)
        report = score_ats(
            resume,
            job_description="Looking for a Python FastAPI engineer with ATS experience",
        )
        assert report.score >= 75
        assert report.sections["contact_info"].passed
        assert report.sections["standard_sections"].passed
        assert report.sections["action_verbs"].passed
        assert report.sections["formatting"].passed
        assert report.passed_count >= 5

    def test_weak_resume_scores_lower(self):
        resume = Resume.model_validate(WEAK_RESUME)
        report = score_ats(resume, job_description="Senior Kubernetes SRE with Terraform")
        assert report.score < 75
        assert not report.sections["contact_info"].passed
        assert not report.sections["standard_sections"].passed
        assert not report.sections["action_verbs"].passed
        assert report.warnings
        assert report.suggestions

    def test_keyword_match_without_jd(self):
        resume = Resume.model_validate(STRONG_RESUME)
        report = score_ats(resume)
        assert report.sections["keyword_match"].passed
        assert "No job description" in report.sections["keyword_match"].detail

    def test_keyword_overlap(self):
        resume = Resume.model_validate(STRONG_RESUME)
        good = score_ats(resume, "Python FastAPI ATS engineer")
        bad = score_ats(resume, "Embedded COBOL mainframe assembler")
        assert good.sections["keyword_match"].score > bad.sections["keyword_match"].score

    def test_report_round_trip(self):
        resume = Resume.model_validate(STRONG_RESUME)
        report = score_ats(resume, "Python engineer")
        restored = type(report).model_validate(report.model_dump())
        assert restored.score == report.score
        assert restored.passed_count == report.passed_count
