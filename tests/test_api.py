import pytest
from fastapi.testclient import TestClient

from app.app import app
from app.models.resume import Resume, ResumeActionResult
from app.services.storage import ResumeStore

SAMPLE_RESUME = {
    "contact": {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+1 555 010 2030",
        "location": "London, UK",
    },
    "summary": "Mathematician and programmer.",
    "experiences": [
        {
            "title": "Software Engineer",
            "company": "Analytical Engines",
            "start_date": "2020-01-01",
            "end_date": "2022-01-01",
            "bullets": ["Built differential engines", "Improved reliability by 20%"],
        }
    ],
    "educations": [
        {
            "degree": "BSc Mathematics",
            "institution": "University of London",
            "start_date": "2016-09-01",
            "end_date": "2019-06-01",
        }
    ],
    "skills": [{"name": "Python"}, {"name": "LaTeX"}],
    "projects": [],
    "certifications": [],
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = ResumeStore(path=None)
    app.state.store = store

    async def fake_generate(prompt: str) -> ResumeActionResult:
        resume = Resume.model_validate(SAMPLE_RESUME)
        return ResumeActionResult(
            resume=resume,
            changes=[f"Generated from prompt: {prompt[:40]}"],
            notes="mocked",
        )

    monkeypatch.setattr("app.api.routes.resume.generate_resume", fake_generate)
    with TestClient(app) as test_client:
        yield test_client


class TestResumeApi:
    def test_put_and_get(self, client: TestClient):
        put = client.put("/resume", json=SAMPLE_RESUME)
        assert put.status_code == 200
        resume_id = put.json()["id"]
        assert put.json()["resume"]["contact"]["name"] == "Ada Lovelace"

        get = client.get(f"/resume/{resume_id}")
        assert get.status_code == 200
        assert get.json()["full_name"] == "Ada Lovelace"

    def test_get_missing(self, client: TestClient):
        assert client.get("/resume/does-not-exist").status_code == 404

    def test_parse_json(self, client: TestClient):
        import json

        resp = client.post("/resume/parse", json={"text": json.dumps(SAMPLE_RESUME)})
        assert resp.status_code == 200
        assert resp.json()["contact"]["email"] == "ada@example.com"

    def test_parse_plain_text(self, client: TestClient):
        text = "Name: Grace Hopper\nEmail: grace@example.com\nSummary: COBOL pioneer"
        resp = client.post("/resume/parse", json={"text": text})
        assert resp.status_code == 200
        assert resp.json()["contact"]["name"] == "Grace Hopper"

    def test_parse_invalid(self, client: TestClient):
        resp = client.post("/resume/parse", json={"text": "not a resume"})
        assert resp.status_code == 400

    def test_generate_mocked(self, client: TestClient):
        resp = client.post("/resume/generate", json={"prompt": "Make a resume for Ada"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"]
        assert body["resume"]["contact"]["name"] == "Ada Lovelace"
        assert body["changes"]
        assert body["notes"] == "mocked"
        assert client.get(f"/resume/{body['id']}").status_code == 200


class TestAtsAndExportApi:
    def _seed(self, client: TestClient) -> str:
        return client.put("/resume", json=SAMPLE_RESUME).json()["id"]

    def test_ats_score(self, client: TestClient):
        resume_id = self._seed(client)
        resp = client.post(
            f"/resume/{resume_id}/ats",
            json={"job_description": "Python engineer LaTeX"},
        )
        assert resp.status_code == 200
        assert 0 <= resp.json()["score"] <= 100
        assert "contact_info" in resp.json()["sections"]

    def test_ats_improve(self, client: TestClient):
        resume_id = self._seed(client)
        resp = client.post(f"/resume/{resume_id}/ats/improve", json={})
        assert resp.status_code == 200
        assert "report" in resp.json()
        assert "recommendations" in resp.json()

    def test_export_tex(self, client: TestClient):
        resume_id = self._seed(client)
        resp = client.get(f"/resume/{resume_id}/export.tex")
        assert resp.status_code == 200
        assert "Ada Lovelace" in resp.text
        assert r"\documentclass" in resp.text

    def test_export_pdf_not_implemented(self, client: TestClient):
        resume_id = self._seed(client)
        resp = client.get(f"/resume/{resume_id}/export.pdf")
        assert resp.status_code == 501
