# FastAPI Realtime Rule Engine

An example application that stress-tests `supabase-py`'s async Realtime path,
per-request JWT injection, Postgres Changes, and server-side broadcast from Python.

## What it does

Users create **watch rules**: "when `tasks.status` changes to `done`, broadcast to
`#team-alerts`." A background Python coroutine holds a persistent Realtime
connection, subscribes to Postgres Changes on the `tasks` table, evaluates rules,
and broadcasts enriched events. The browser subscribes to those channels via the
JS client and shows a live event feed.

## Prerequisites

- A Supabase project (create one free at supabase.com)
- uv installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Supabase CLI installed (`brew install supabase/tap/supabase`)
- Python 3.10+

## Setup

**1. Install workspace dependencies (from repo root):**
```bash
uv sync
```

**2. Apply the database migration:**
```bash
# Using Supabase CLI connected to your project
supabase db push --db-url "postgresql://..." supabase/migrations/001_initial.sql
```

Or copy-paste `supabase/migrations/001_initial.sql` into the Supabase SQL editor.

**3. Configure environment:**
```bash
cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY from your project settings
```

**4. Run the app:**
```bash
cd examples/fastapi
uv run uvicorn main:app --reload
```

Open http://localhost:8000/signin, sign up, create rules, update tasks, and watch
broadcasts appear in the live feed.

## Run tests

```bash
cd examples/fastapi
uv run pytest tests/ -v
```

Tests mock all Supabase I/O — no real project required.

## SDK friction log

See `friction_log.md` for every pain point discovered during implementation,
with severity ratings and recommended SDK improvements.

## Architecture

See the design spec at `docs/superpowers/specs/2026-06-23-fastapi-realtime-rule-engine-design.md`.
