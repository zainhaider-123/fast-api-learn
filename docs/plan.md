# Resume Builder — Plan

Build a resume builder app on top of the existing FastAPI + Pydantic AI project. The core goal is to **learn Pydantic** (v2) while building something real: a structured resume model, an AI agent that generates/edit resume content, a tool that renders a LaTeX (`.tex`) file, and a tool that scores the resume for ATS (Applicant Tracking System) compatibility.

## 1. Goals

- Understand Pydantic v2: models, validation, serialization, nested models, fields, computed fields, model validators.
- Use Pydantic AI to orchestrate an agent that helps build and improve resumes.
- Generate a valid, compilable LaTeX resume file.
- Analyze a resume against ATS rules and return a score + suggestions.

## 2. Tech Stack (current + added)

| Piece | Tool |
|---|---|
| API framework | FastAPI (already present) |
| Data validation | Pydantic v2 (already a dep) |
| AI agent | Pydantic AI (already a dep) |
| AI model | `anthropic:claude-sonnet-4-6` (already configured) |
| LaTeX rendering | Python tool that emits `.tex` (optionally compile with `pdflatex`/TinyTeX) |
| ATS scoring | Python tool + optional Pydantic AI review pass |
| Frontend | Jinja2 + Tailwind (already present) |

## 3. Pydantic Models (the learning core)

All resume data is defined as Pydantic models in `src/app/models/`. Every concept below is a chance to practice a Pydantic feature.

```
src/app/models/
  contact.py        # ContactInfo
  profile.py        # Profile / summary
  experience.py     # Experience, ExperienceItem
  education.py      # Education, EducationItem
  skills.py         # Skill, SkillCategory
  projects.py       # Project
  certifications.py # Certification
  resume.py         # Resume (root model, ties everything together)
```

Model features to use deliberately:

- **Base model + nested models** — `Resume` embeds `ContactInfo`, `list[ExperienceItem]`, etc.
- **`Field(...)` constraints** — e.g. `min_length`, `max_length`, `Pattern` (URL, email), `ge/le` for years, `max_items` for list sizes.
- **`field_validator` / `model_validator`** — e.g. an end date must not be before start date; at least one of `title`/`position` required.
- **`computed_field`** — e.g. `years_of_experience`, total years, or `full_name`.
- **`model_dump()` / `model_dump_json()`** — serialize for the TeX tool and for the AI prompt.
- **`model_validate()`** — parse AI output / raw JSON back into models (round-tripping).
- **`DiscriminatedUnion`** — e.g. a `Media` field that is either `Link` or `File`.
- **`TypeAdapter`** — validate a raw list of `ExperienceItem` without a wrapper model.
- **`Alias` / `serialization_alias`** — map frontend snake_case to desired output naming if needed.

Resume shape (v1):

```text
Resume
├── contact: ContactInfo        (name, email, phone, location, website, github, linkedin)
├── summary: str
├── experiences: [ExperienceItem]  (title, company, location, start_date, end_date, bullets)
├── educations: [EducationItem]    (degree, institution, location, start_date, end_date, gpa?)
├── skills: [Skill]                (name, category?, level?)
├── projects: [Project]            (name, description, link?, highlights)
└── certifications: [Certification]
```

## 4. Pydantic AI Agent

The agent lives in `src/app/ai/` (structure already exists).

```
src/app/ai/
  pydantic_ai.py      # Agent instance + result types
  prompt/
    system.py         # System prompt for the resume-builder agent
  tool/
    tex_generator.py  # Tool: build .tex from Resume model
    ats_checker.py    # Tool: score resume against ATS rules
    resume_parser.py  # Tool: parse raw text/JSON into Resume model
```

### Agent result schema (Pydantic output)

Use a Pydantic model as the agent's `result_type` so every reply is validated:

```python
class ResumeActionResult(BaseModel):
    resume: Resume
    changes: list[str] = Field(default_factory=list)  # what the AI changed
    notes: str = ""
```

### Tools (learn how Pydantic AI tools work)

- `build_tex(resume: Resume) -> str` — renders the LaTeX.
- `score_ats(resume: Resume, job_description: str = "") -> AtsReport` — returns a structured `AtsReport`.
- `parse_resume(raw: str) -> Resume` — best-effort parse of pasted text into the model (uses `model_validate` + validation errors surfaced to the model).

All tools get **typed parameters** — Pydantic AI validates tool args against the model automatically. That is a great Pydantic learning moment.

## 5. LaTeX Generator Tool

`src/app/ai/tool/tex_generator.py`:

- Pure Python string/template rendering → deterministic `.tex` output (Jinja2 template for the `.tex`).
- Escape LaTeX special chars (`& % $ # _ { } ~ ^ \`) so user content never breaks the file.
- Support two templates: `modern` and `classic` (LaTeX `article`/custom section styling, no heavy packages — must compile anywhere).
- Optionally shell out to `pdflatex`/`xelatex` (via TinyTeX) to produce a PDF. Guard behind a flag since not everyone has LaTeX installed.
- Output: `.tex` file content (and PDF if compiler available).

Template location: `src/app/templates/tex/modern.tex.j2`, `classic.tex.j2`.

## 6. ATS Scoring Tool

`src/app/ai/tool/ats_checker.py` — deterministic + heuristic checks:

| Check | Rule | Weight |
|---|---|---|
| Contact info | name, email, phone, location present | high |
| One page | estimated length / page count | high |
| Standard sections | headers match expected section names | high |
| Keyword match | overlap between resume and job description (tf-idf / simple token overlap) | medium |
| Action verbs | bullets start with action verbs | medium |
| Formatting | no tables/columns/graphics that break parsers; simple text-safe formatting | medium |
| Dates | ISO-ish date format present, no abbreviations | low |
| Acronyms | acronyms are spelled out on first use | low |

Output model:

```python
class AtsReport(BaseModel):
    score: int  # 0-100
    sections: dict[str, SectionResult]
    warnings: list[str]
    suggestions: list[str]
```

- `score_ats` is deterministic (fast, reproducible).
- Optional second step: the AI agent reviews the same `AtsReport` and produces natural-language recommendations via a `result_type` model (shows Pydantic AI + structured output together).

## 7. API Endpoints

```
src/app/api/
  routes/
    resume.py        # /resume
    ats.py           # /ats
    export.py        # /export
```

| Method | Path | Body → Response | Purpose |
|---|---|---|---|
| POST | `/resume/generate` | `{prompt}` → `ResumeActionResult` | AI builds a resume from a prompt |
| POST | `/resume/parse` | `{text}` → `Resume` | Parse pasted resume text |
| PUT  | `/resume` | `Resume` → `Resume` | Validate + store a resume |
| GET  | `/resume/{id}` | → `Resume` | Fetch stored resume |
| POST | `/resume/{id}/ats` | `{job_description?}` → `AtsReport` | Run ATS checks |
| POST | `/resume/{id}/ats/improve` | → `AtsReport` + recommendations | ATS check + AI suggestions |
| GET  | `/resume/{id}/export.tex` | → `.tex` (plain text response) | Download TeX source |
| GET  | `/resume/{id}/export.pdf` | → PDF file (if compiler present) | Download compiled PDF |

Storage for v1: in-memory dict + JSON file (or SQLite via `sqlite3` stdlib). No ORM yet — keep focus on Pydantic.

## 8. Frontend (light)

Keep the existing Jinja2 + Tailwind setup. Add pages:

- `/` — form to paste text or describe the job, call `/resume/generate`.
- `/resume` — editable form mirroring the `Resume` model (rendered from `model_fields`), then actions: export `.tex`, run ATS.
- `/ats` — score breakdown + suggestions list.

A JS fetch wrapper in `src/static/js/main.js` calls the API. Keep it minimal — this is a backend/learning project.

## 9. Project Structure (target)

```
src/
  app/
    main.py              # FastAPI app (mount routers, static, templates)
    models/              # Pydantic models (the learning core)
    ai/
      pydantic_ai.py     # Agent + result types
      prompt/system.py
      tool/
        tex_generator.py
        ats_checker.py
        resume_parser.py
    api/
      routes/
        resume.py
        ats.py
        export.py
    services/            # storage, tex escaping, ats engine helpers
    templates/
      index.html
      resume.html
      ats.html
      tex/               # .tex.j2 templates
  tests/
    test_models.py       # Pydantic validation tests
    test_tex.py          # escaping, golden .tex output
    test_ats.py          # score cases
    test_api.py          # endpoint tests (httpx/TestClient)
```

## 10. Implementation Phases

### Phase 1 — Models (learn Pydantic)
- Define all models in `src/app/models/`.
- Write `tests/test_models.py` covering validation: missing fields, date-order rule, URL/email patterns, computed `years_of_experience`, round-trip `model_dump` → `model_validate`.

### Phase 2 — LaTeX tool
- Escaping util + `modern`/`classic` Jinja templates.
- `build_tex(resume)` producing a compilable `.tex`.
- Golden-file test: known `Resume` → expected `.tex`.

### Phase 3 — ATS tool
- Implement heuristic checks + `AtsReport`.
- Tests for each check with pass/fail fixtures.

### Phase 4 — Agent wiring
- `parse_resume`, `build_tex`, `score_ats` as Pydantic AI tools.
- `ResumeActionResult` as agent `result_type`.
- `tests/test_api.py` for the endpoints (mock the LLM with a fake when needed).

### Phase 5 — Frontend + export
- Resume editor page, ATS results page.
- `.tex` / `.pdf` download endpoints.

### Phase 6 — Polish
- `uv sync`-fresh verification, docs, optional PDF compile flag, `.env` example.

## 11. Testing

Run with `uv`:

```bash
uv run pytest
```

Key test types:
- **Model validation** — negative + positive cases (fast, no LLM).
- **TeX golden files** — deterministic output, escaping edge cases.
- **ATS engine** — synthetic resumes with known scores.
- **API integration** — `TestClient`; mock Pydantic AI agent responses so tests don't hit the network.

## 12. Risks / Notes

- **LLM in tests** — always mock the agent for tests; keep the model call behind the agent class.
- **LaTeX not installed** — PDF export degrades gracefully (return 501 with a message); `.tex` always works.
- **ATS rules are heuristics** — real ATS vary; document assumptions.
- **Pydantic v2 API** — use `model_validate`/`model_dump`, not deprecated v1 methods.

## 13. Learning Checklist

- [ ] Nest models and use `Field` constraints.
- [ ] Write a `field_validator` and a `model_validator`.
- [ ] Derive data with `computed_field`.
- [ ] Round-trip with `model_dump` / `model_validate`.
- [ ] Use `TypeAdapter` for bare lists.
- [ ] Use a `DiscriminatedUnion`.
- [ ] Use a Pydantic AI tool with typed args (auto validation).
- [ ] Use an agent `result_type` (structured, validated AI output).
- [ ] Serialize model → LLM context; parse LLM output → model.
