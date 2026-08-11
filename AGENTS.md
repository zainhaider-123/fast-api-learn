# AGENTS.md

FastAPI + Jinja2 + Tailwind v4 app with a Pydantic AI agent. Python 3.12 managed by uv/mise; frontend tooling via pnpm.

## Commands

- Setup: `uv sync` (Python deps) then `pnpm install` (Tailwind). `.venv` can be stale — run `uv sync` before assuming deps like `pydantic-ai` are installed.
- Dev: `pnpm run dev` runs both in parallel; or `pnpm run dev:fastapi` / `pnpm run dev:tailwind` separately.
- Raw uvicorn: `uv run uvicorn app.main:app --reload --app-dir src`. The `--app-dir src` is required — the app package is `src/app`, not a root `app/`.
- No linters, formatters, typecheckers, or tests are configured. None exist yet (see Roadmap).

## Layout traps

- The real app lives in `src/app/` (`main.py` resolves templates/static relative to `src/`). Root-level `app/` (stale `__pycache__`) and root `static/` are leftover duplicates and are **not** served — ignore them.
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
