# FastAPI Learn

A small FastAPI app with Jinja2 templates, Tailwind CSS, and a Pydantic AI agent.

## Stack

- **Python 3.12+** — [uv](https://docs.astral.sh/uv/) for deps and runs
- **FastAPI** + **Uvicorn** — API and server
- **Jinja2** — HTML templates
- **Tailwind CSS v4** — styles via `@tailwindcss/cli`
- **Pydantic AI** — AI agent (`anthropic:claude-sonnet-4-6`)
- **pnpm** — frontend tooling (optional: [mise](https://mise.jdx.dev/) pins `pnpm`, `python`, and `uv`)

## Setup

```bash
# Python deps
uv sync

# Frontend deps (Tailwind)
pnpm install
```

Copy or create a `.env` if you need API keys for the AI agent (e.g. Anthropic).

## Development

Run FastAPI and Tailwind watch together:

```bash
pnpm run dev
```

Or separately:

```bash
pnpm run dev:fastapi   # http://localhost:8000
pnpm run dev:tailwind  # watches src/tailwind → src/static/css
```

You can also start the app with:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir src
```

## Endpoints

| Path   | Description              |
|--------|--------------------------|
| `/`    | Home page (Jinja2)       |
| `/ping`| Health check → `{"message":"pong"}` |
| `/docs`| OpenAPI / Swagger UI     |

## Project layout

```
src/
  app/
    main.py          # FastAPI app
    ai/              # Pydantic AI agent, prompts, tools
    api/             # API routes (placeholder)
  templates/         # Jinja2 HTML
  static/            # Built CSS and static assets
  tailwind/          # Tailwind source (style.css)
```
