# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is `supabase-py`, a Python monorepo containing all official Supabase client libraries for Python. The repository uses a workspace structure managed by `uv` with the following packages:

- `supabase` - Main Supabase client library
- `realtime` - Realtime subscriptions client
- `supabase_functions` - Edge Functions client
- `storage3` - Storage client
- `postgrest` - PostgREST client
- `supabase_auth` - Authentication client

## Development Setup

### Prerequisites
- `uv` for Python project management
- `make` for command running
- `docker` for test containers (postgrest, auth)
- `supabase-cli` for test containers (storage, realtime)

### Environment Setup
```bash
# Create and activate virtual environment
uv venv supabase-py
source supabase-py/bin/activate
uv sync
```

### Alternative: Nix
If you have Nix installed, use the development shell:
```bash
nix develop
```

## Common Commands

### Testing
```bash
# Run all tests for all packages
make ci

# Run tests in parallel (faster but messy output)
make ci -j

# Run tests for specific package
make realtime.tests
make supabase.tests
make storage.tests
# etc.
```

### Linting and Formatting
```bash
# Run pre-commit hooks (ruff lint/format, trailing whitespace, etc.)
make pre-commit

# Run type checking for specific package
make realtime.mypy
```

### Infrastructure Management
```bash
# Start all test containers
make start-infra

# Stop all test containers
make stop-infra
```

### Cleanup
```bash
# Clean all cache files and coverage reports
make clean

# Clean specific package
make realtime.clean
```

### Building
```bash
# Build all packages
make publish

# Build specific package
make supabase.build
```

## Architecture

### Monorepo Structure
The codebase uses a `uv` workspace with each package in `src/` having its own:
- `pyproject.toml` - Package configuration and dependencies
- `Makefile` - Package-specific commands
- `README.md` - Package documentation

### Async/Sync Pattern
The `supabase` package maintains both async and sync versions:
- `src/supabase/_async/` - Async implementations
- `src/supabase/_sync/` - Auto-generated sync versions using `unasync`

The sync versions are generated via:
```bash
make supabase.unasync
make supabase.build-sync
```

### Testing Infrastructure
- Tests require containers for services (PostgreSQL, Supabase services)
- Each package with external dependencies has `start-infra`/`stop-infra` targets
- Uses `pytest` with coverage reporting
- Type checking with `mypy` where applicable

### Code Quality
- `ruff` for linting and formatting
- `pre-commit` hooks for automated checks
- `commitizen` for conventional commits
- Coverage reporting with `pytest-cov`

## Package-Specific Notes

### Realtime
- Requires Supabase CLI containers for testing
- Has mypy type checking

### Storage
- Requires Supabase CLI containers for testing

### Auth & PostgREST
- Require Docker containers for testing

### Functions
- Standalone package with minimal infrastructure needs

### Supabase (Main Client)
- Aggregates all other packages
- Has special async/sync build process
- Most complex package with full integration tests