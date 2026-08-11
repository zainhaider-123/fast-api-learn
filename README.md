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
# Python deps (installs the package + `fast-api-learn` script)
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
pnpm run dev:tailwind  # watches src/static/css/tailwind.css → style.css
```

`dev:fastapi` runs `uv run fast-api-learn`, which calls `main()` in `src/main.py` (host, port, and reload are configured there).

You can also start the app directly:

```bash
uv run fast-api-learn
# or
uv run python src/main.py
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
  main.py            # Entry point (uvicorn.run)
  app/
    app.py           # FastAPI app, mounts, routes
    ai/              # Pydantic AI agent, prompts, tools
  templates/         # Jinja2 HTML
  static/            # Built CSS and static assets
    css/
      tailwind.css   # Tailwind source
      style.css      # Generated output (committed)
```
