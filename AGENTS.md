# AGENTS.md

Resume builder on FastAPI + Jinja2 + Tailwind v4, with Pydantic v2 models and a Pydantic AI agent. The learning goal is Pydantic (validation, nested models, tools, structured output). Python 3.12 via uv/mise; frontend tooling via pnpm. Packaged with Hatchling so `uv sync` installs an editable wheel and the `fast-api-learn` console script.

## Commands

- Setup: copy `.env.example` → `.env`, then `uv sync` (Python deps + package + pytest) and `pnpm install` (Tailwind). `.venv` can be stale — run `uv sync` before assuming deps like `pydantic-ai`, `sqlmodel`, or `psycopg` are installed.
- Postgres: `docker compose up -d` — `postgres:17` on `localhost:5432`, database `postgres`, user/password `root`/`root`. Must be up before `pnpm run dev` (app lifespan connects on startup).
- Dev: `pnpm run dev` runs FastAPI + Tailwind watch in parallel; or `pnpm run dev:fastapi` / `pnpm run dev:tailwind` separately.
- Server entry: `pnpm run dev:fastapi` → `uv run fast-api-learn` → `main:main` in `src/main.py`. Port/reload come from Settings (`PORT`, `ENV`); host stays in `src/main.py`. Do not duplicate host/port/reload in `package.json`.
- Alternatives: `uv run fast-api-learn` or `uv run python src/main.py`.
- Tests: `uv run pytest`. No linters, formatters, or typecheckers are configured.

## Layout

```
src/
  main.py                 # uvicorn entry; console script target
  app/                    # installed package name `app`
    app.py                # FastAPI instance, static mount, HTML pages, api_router
    config.py             # Settings: load_dotenv + pydantic-settings (ENV, PORT, DATABASE_URL)
    models/               # Pydantic v2 resume + ATS models
    api/
      schemas.py          # request/response wrappers
      routes/             # resume, ats, export routers
    ai/
      pydantic_ai.py      # Agent + typed tools + generate_resume()
      prompt/system.py
      tool/               # tex_generator, ats_checker, resume_parser
    services/
      storage.py          # ResumeStore (SQLModel; Postgres via DATABASE_URL)
      latex.py            # escape_latex
    templates/tex/        # modern.tex.j2, classic.tex.j2 (LaTeX, not HTML)
  templates/              # Jinja2 HTML (_base, index, resume, ats)
  static/                 # /static — css/, js/main.js
tests/                    # pytest: models, tex, ats, api + golden/*.tex
docs/plan.md              # original design doc (partially implemented)
```

- `src/main.py` is force-included as top-level `main` via Hatchling so `[project.scripts] fast-api-learn = "main:main"` works.
- HTML templates/static paths resolve relative to `src/`. TeX Jinja templates live under `src/app/templates/tex/`.
- New API endpoints go in `src/app/api/routes/` and are included from `api/routes/__init__.py`. Page routes stay in `app.py`.
- `.env` is gitignored. Commit `.env.example` only. `docker-compose.yml` matches the example `DATABASE_URL`.

## Settings

`src/app/config.py` is the only place that loads env. `_ENV_FILE` is the project-root `.env` (resolved from `__file__`, not cwd). `load_dotenv` exports into `os.environ` (so `ANTHROPIC_API_KEY` works in `pydantic_ai.py`); `Settings` then reads the same file via pydantic-settings.

| Field | Env | Default | Used by |
|---|---|---|---|
| `env` | `ENV` | `DEV` | `src/main.py` — `reload=True` when `DEV` |
| `port` | `PORT` | `8000` | `src/main.py` uvicorn port |
| `database_url` | `DATABASE_URL` | **required** | app lifespan → `ResumeStore` |

Do not read `.env` from routes or services. Import `settings` / `get_settings()` from `app.config`. `DATABASE_URL` has no sqlite fallback — missing file or var fails at import. Example: `postgresql://root:root@localhost:5432/postgres`. `postgresql://` is rewritten to `postgresql+psycopg://` inside `storage.py`.

## Models (Pydantic v2)

All resume data is Pydantic `BaseModel` in `src/app/models/`. Use `model_validate` / `model_dump` only — never v1 `parse_obj` / `dict()`.

| Module | Types |
|---|---|
| `contact.py` | `ContactInfo` |
| `profile.py` | `Profile` (`headline`, `summary`, computed `word_count`) |
| `experience.py` | `ExperienceItem` + `experience_list_adapter` (`TypeAdapter`) |
| `education.py` | `EducationItem` |
| `skills.py` | `Skill`, `SkillCategory`, `SkillLevel` |
| `projects.py` | `Project` |
| `certifications.py` | `Certification` |
| `media.py` | `LinkMedia` \| `FileMedia` discriminated union (`Media`) |
| `resume.py` | `Resume` (root), `ResumeActionResult` (agent output) |
| `ats.py` | `AtsReport`, `SectionResult` |

Root shape: `contact`, optional `profile`, `summary`, `experiences`, `educations`, `skills`, `projects`, `certifications`. Computed on `Resume`: `full_name`, `years_of_experience`, `effective_summary` (prefers `profile.summary`).

Notable validation: date order on experience/education; at least one of `title`/`position`; `EmailStr` / `HttpUrl`; `Field` length limits; `gpa` 0–4.

## API

HTML: `GET /` (generate/parse forms), `GET /resume` (saved resume + export), `GET /ats` (score UI), `GET /ping`. Client: `src/static/js/main.js` (`api()` helper; stores `resumeId` in `sessionStorage`).

| Method | Path | Purpose |
|---|---|---|
| POST | `/resume/generate` | AI builds a resume from `{prompt}` → saves, returns id + `ResumeActionResult` |
| POST | `/resume/parse` | Parse JSON or `Name:`/`Email:` text → `Resume` (does not save) |
| PUT | `/resume` | Validate + store a `Resume` → `{id, resume}` |
| GET | `/resume/{id}` | Fetch stored resume |
| POST | `/resume/{id}/ats` | Deterministic ATS score (`job_description` optional) |
| POST | `/resume/{id}/ats/improve` | Same score + heuristic recommendations (no extra LLM call) |
| GET | `/resume/{id}/export.tex` | Download `.tex` (`?template=modern\|classic`) |
| GET | `/resume/{id}/export.pdf` | Always **501** until a LaTeX compiler is wired |

## Storage

`ResumeStore` (`src/app/services/storage.py`): SQLModel `resumes` table (`id` PK + JSON `payload`). Domain `Resume` stays a Pydantic `BaseModel` in `models/`; `ResumeRecord` is the table model — do not merge them.

App lifespan (`src/app/app.py`) constructs `ResumeStore(database_url=settings.database_url)` and `create_all`s the table. Tests assign `ResumeStore(database_url="sqlite://")` to `app.state.store` **before** `TestClient` so lifespan does not open Postgres. Driver: `psycopg[binary]`. Do not persist secrets.

## Pydantic AI

`src/app/ai/pydantic_ai.py` — `Agent` named `resume_builder`, `output_type=ResumeActionResult`.

- Model: `anthropic:claude-sonnet-4-6` when `ANTHROPIC_API_KEY` is set in `.env` / the environment (via `load_dotenv` in `config.py`); otherwise `"test"` so import does not require a key.
- Tools (`@agent.tool_plain`): `tool_build_tex`, `tool_score_ats`, `tool_parse_resume` — wrappers around the deterministic modules in `ai/tool/`.
- `generate_resume(prompt)` is the only call path from the API. Tests/offline work **must mock** `app.api.routes.resume.generate_resume` (see `tests/test_api.py`). Do not hit the network in tests.

TeX: `build_tex` escapes user text via `escape_latex` and renders Jinja `.tex.j2` templates. PDF compile is not implemented.

ATS: `score_ats` is deterministic heuristics (contact, one-page, sections, keywords, action verbs, formatting, dates, acronyms). Not a live ATS.

Parser: JSON via `Resume.model_validate`; otherwise `Name:` + `Email:` lines. Other free text raises `ValueError`.

## Tailwind v4

- Source: `src/static/css/tailwind.css` (`@import "tailwindcss"`, `@source "../../templates/**/*.html"`).
- Output: `src/static/css/style.css` (generated, gitignored). Don't hand-edit it; regenerate via `pnpm run dev:tailwind`.
- Uses `@tailwindcss/cli` via `pnpm dlx`. `pnpm-workspace.yaml` must keep `allowBuilds: '@parcel/watcher': true`.

## Tests

`uv run pytest` — `tests/test_models.py` (validation, computed fields, TypeAdapter, discriminated union, round-trip), `tests/test_tex.py` (escaping + golden `modern`/`classic`), `tests/test_ats.py` (heuristic scores), `tests/test_api.py` (`TestClient`, mocked agent, in-memory SQLite store).

When changing TeX output, update `tests/golden/*.tex`. When adding endpoints, extend `test_api.py` and keep the LLM mocked.

## Skills

Project-installed Pydantic / Pydantic AI guidance lives in `.agents/skills/` (`pydantic`, `pydantic-ai-harness`, `building-pydantic-ai-agents`). Use those for API details. Design notes and leftover ideas: `docs/plan.md` (treat as historical — this file is the current map).
