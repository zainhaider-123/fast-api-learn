from datetime import date

import pytest
from pydantic import ValidationError

from app.models import (
    ContactInfo,
    EducationItem,
    ExperienceItem,
    FileMedia,
    LinkMedia,
    Project,
    Resume,
    Skill,
    SkillCategory,
    SkillLevel,
    experience_list_adapter,
)


def _minimal_contact(**overrides) -> dict:
    data = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+1 (555) 010-2030",
        "location": "London, UK",
    }
    data.update(overrides)
    return data


def _minimal_experience(**overrides) -> dict:
    data = {
        "title": "Software Engineer",
        "company": "Analytical Engines Ltd",
        "start_date": "2020-01-01",
        "end_date": "2022-06-30",
        "bullets": ["Built differential engines"],
    }
    data.update(overrides)
    return data


def _minimal_resume(**overrides) -> dict:
    data = {
        "contact": _minimal_contact(),
        "summary": "Mathematician and first programmer.",
        "experiences": [_minimal_experience()],
        "educations": [
            {
                "degree": "BSc Mathematics",
                "institution": "University of London",
                "start_date": "2016-09-01",
                "end_date": "2019-06-01",
                "gpa": 3.9,
            }
        ],
        "skills": [{"name": "Python", "category": "language", "level": "expert"}],
        "projects": [],
        "certifications": [],
    }
    data.update(overrides)
    return data


class TestContactInfo:
    def test_valid_contact(self):
        contact = ContactInfo.model_validate(
            _minimal_contact(
                website="https://ada.dev",
                github="https://github.com/ada",
                linkedin="https://linkedin.com/in/ada",
            )
        )
        assert contact.name == "Ada Lovelace"
        assert str(contact.email) == "ada@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError) as exc:
            ContactInfo.model_validate(_minimal_contact(email="not-an-email"))
        assert "email" in str(exc.value)

    def test_invalid_phone_pattern(self):
        with pytest.raises(ValidationError):
            ContactInfo.model_validate(_minimal_contact(phone="call-me!!!"))

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            ContactInfo.model_validate(_minimal_contact(name="  "))


class TestExperienceItem:
    def test_requires_title_or_position(self):
        with pytest.raises(ValidationError) as exc:
            ExperienceItem.model_validate(
                {
                    "company": "Acme",
                    "start_date": "2020-01-01",
                    "end_date": "2021-01-01",
                }
            )
        assert "title" in str(exc.value).lower() or "position" in str(exc.value).lower()

    def test_accepts_position_without_title(self):
        item = ExperienceItem.model_validate(
            {
                "position": "Engineer",
                "company": "Acme",
                "start_date": "2020-01-01",
                "end_date": "2021-01-01",
            }
        )
        assert item.display_title == "Engineer"

    def test_end_before_start_rejected(self):
        with pytest.raises(ValidationError) as exc:
            ExperienceItem.model_validate(
                _minimal_experience(start_date="2022-01-01", end_date="2020-01-01")
            )
        assert "end_date" in str(exc.value)

    def test_years_computed(self):
        item = ExperienceItem.model_validate(
            _minimal_experience(start_date="2020-01-01", end_date="2022-01-01")
        )
        assert item.years == pytest.approx(2.0, abs=0.02)

    def test_current_role_clears_end_date(self):
        item = ExperienceItem.model_validate(
            _minimal_experience(is_current=True, end_date="2025-01-01")
        )
        assert item.end_date is None
        assert item.years > 0


class TestEducationItem:
    def test_gpa_bounds(self):
        with pytest.raises(ValidationError):
            EducationItem.model_validate(
                {
                    "degree": "BS",
                    "institution": "MIT",
                    "start_date": "2015-01-01",
                    "gpa": 4.5,
                }
            )

    def test_date_order(self):
        with pytest.raises(ValidationError):
            EducationItem.model_validate(
                {
                    "degree": "BS",
                    "institution": "MIT",
                    "start_date": "2018-01-01",
                    "end_date": "2015-01-01",
                }
            )


class TestSkillsAndProjects:
    def test_skill_enums(self):
        skill = Skill.model_validate(
            {"name": " FastAPI ", "category": "framework", "level": "advanced"}
        )
        assert skill.name == "FastAPI"
        assert skill.category == SkillCategory.FRAMEWORK
        assert skill.level == SkillLevel.ADVANCED

    def test_project_link_media_discriminator(self):
        project = Project.model_validate(
            {
                "name": "Engine",
                "description": "A computing engine",
                "media": {"type": "link", "url": "https://example.com", "label": "Demo"},
            }
        )
        assert isinstance(project.media, LinkMedia)
        assert project.media.type == "link"

    def test_project_file_media_discriminator(self):
        project = Project.model_validate(
            {
                "name": "Engine",
                "description": "A computing engine",
                "media": {"type": "file", "path": "/tmp/demo.pdf", "mime_type": "application/pdf"},
            }
        )
        assert isinstance(project.media, FileMedia)
        assert project.media.type == "file"

    def test_unknown_media_type_rejected(self):
        with pytest.raises(ValidationError):
            Project.model_validate(
                {
                    "name": "Engine",
                    "description": "A computing engine",
                    "media": {"type": "video", "url": "https://example.com"},
                }
            )


class TestResume:
    def test_full_name_and_years(self):
        resume = Resume.model_validate(_minimal_resume())
        assert resume.full_name == "Ada Lovelace"
        assert resume.years_of_experience == pytest.approx(2.5, abs=0.1)

    def test_effective_summary_from_profile(self):
        resume = Resume.model_validate(
            _minimal_resume(
                summary="fallback",
                profile={"summary": "From profile", "headline": "Engineer"},
            )
        )
        assert resume.effective_summary == "From profile"
        assert resume.profile is not None
        assert resume.profile.word_count == 2

    def test_round_trip_dump_validate(self):
        original = Resume.model_validate(_minimal_resume())
        dumped = original.model_dump(mode="json")
        restored = Resume.model_validate(dumped)
        assert restored.model_dump(mode="json") == dumped
        assert restored.contact.name == original.contact.name

    def test_round_trip_json(self):
        original = Resume.model_validate(_minimal_resume())
        raw = original.model_dump_json()
        restored = Resume.model_validate_json(raw)
        assert restored.full_name == original.full_name

    def test_max_experiences(self):
        experiences = [
            _minimal_experience(company=f"Co{i}", start_date=f"20{10 + i % 9}-01-01")
            for i in range(21)
        ]
        with pytest.raises(ValidationError):
            Resume.model_validate(_minimal_resume(experiences=experiences))


class TestTypeAdapter:
    def test_experience_list_adapter(self):
        items = experience_list_adapter.validate_python(
            [
                _minimal_experience(company="A"),
                _minimal_experience(company="B", title=None, position="Lead"),
            ]
        )
        assert len(items) == 2
        assert items[0].company == "A"
        assert items[1].display_title == "Lead"

    def test_experience_list_adapter_rejects_bad_item(self):
        with pytest.raises(ValidationError):
            experience_list_adapter.validate_python(
                [{"company": "A", "start_date": "2020-01-01"}]
            )


class TestSerializationAliases:
    def test_dates_serialize_as_iso(self):
        item = ExperienceItem.model_validate(_minimal_experience())
        dumped = item.model_dump(mode="json")
        assert dumped["start_date"] == "2020-01-01"
        assert dumped["end_date"] == "2022-06-30"
        assert "years" in dumped
        assert "display_title" in dumped
