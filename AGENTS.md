# AGENTS.md

FastAPI + Jinja2 + Tailwind v4 app with a Pydantic AI agent. Python 3.12 managed by uv/mise; frontend tooling via pnpm. Packaged with Hatchling so `uv sync` installs an editable wheel and the `fast-api-learn` console script.

## Commands

- Setup: `uv sync` (Python deps + package install) then `pnpm install` (Tailwind). `.venv` can be stale — run `uv sync` before assuming deps like `pydantic-ai` are installed.
- Dev: `pnpm run dev` runs both in parallel; or `pnpm run dev:fastapi` / `pnpm run dev:tailwind` separately.
- Server entry: `pnpm run dev:fastapi` → `uv run fast-api-learn` → `main:main` in `src/main.py`. Host/port/reload live only in `src/main.py` — do not duplicate them in `package.json`.
- Alternatives: `uv run fast-api-learn` or `uv run python src/main.py`.
- No linters, formatters, typecheckers, or tests are configured. None exist yet (see Roadmap).

## Layout

- Entry point: `src/main.py` — imports `app` from `app.app` and runs uvicorn.
- FastAPI app: `src/app/app.py` — creates the FastAPI instance, mounts static files, defines routes. Templates/static paths resolve relative to `src/`.
- Package: `src/app/` (installed as `app`). `src/main.py` is force-included as top-level `main` via Hatchling so the `[project.scripts]` entry `fast-api-learn = "main:main"` works.
- Templates: `src/templates/` (Jinja2). `_base.html` links to `/about` and `/contact`, which don't exist (404).
- Static: FastAPI mounts `src/static/` at `/static`.

## Tailwind v4

- Source: `src/static/css/tailwind.css` (`@import "tailwindcss"`, `@source "../../templates/**/*.html"`).
- Build output: `src/static/css/style.css` (generated and committed). Don't hand-edit it; regenerate via `pnpm run dev:tailwind`.
- Uses `@tailwindcss/cli` via `pnpm dlx`. `pnpm-workspace.yaml` must keep `allowBuilds: '@parcel/watcher': true` for the native watcher to build.

## Pydantic AI agent

- `src/app/ai/pydantic_ai.py` — Agent using `anthropic:claude-sonnet-4-6`. Requires an Anthropic API key in `.env` (gitignored) to run; tests/offline work must mock the agent.

## Roadmap

- `docs/plan.md` is the design doc: a resume-builder app whose point is learning Pydantic v2. Models go in `src/app/models/`, routes in `src/app/routes/`, tests in `tests/` — none exist yet.
- Pydantic v2 API only: `model_validate`/`model_dump`, not the deprecated v1 methods.
- Project-installed Pydantic/Pydantic-AI guidance lives in `.agents/skills/` (pydantic, pydantic-ai-harness, building-pydantic-ai-agents) — use these for API details.
