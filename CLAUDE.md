# nhl-commentary-core

AI-powered NHL live commentary backend. Fetches play-by-play data and generates text commentary via LLMs.

## Quick Reference

- **Run**: `python main.py`
- **Test**: `python -m pytest tests/`
- **Lint**: `python -m ruff check . && python -m ruff format .`
- **Type check**: `python -m mypy .`
- **Install deps**: `pip install -r requirements.txt`
- **Serve**: `uvicorn api.app:app --reload`
- **Python**: 3.11+
- **Config**: loaded from `.env` via `config.py` → `get_settings()`

## Architecture

```
data_fetch/       # NHL API clients (schedule, play-by-play, game_story)
engine/           # LLM commentary generation pipeline
  event_handlers/ # Per-event-type handlers
gcp_ingestion/    # GCS upload / BigQuery ingestion
interpreter/      # Commentary post-processing
models/           # Pydantic data models
prompts/          # Prompt templates
config.py         # Centralised Settings dataclass (env-driven)
main.py           # CLI entry point
```

### Key Patterns

- **Config**: always use `from config import get_settings; s = get_settings()`. Never read env vars directly elsewhere.
- **NHL data**: fetched via `nhlpy` client (not raw HTTP). Instantiate once and pass down.
- **GCS bucket**: `settings.gcs_bucket_name` (default `nhl-commentary-bucket`)
- **Commentary engine**: `engine/generate_summary.py` orchestrates data → prompt → LLM → output.

## Working Approach

### Planning
- For simple, well-scoped tasks (single function, config tweak, obvious fix): proceed directly.
- For anything touching multiple files, introducing new abstractions, changing data flow, or with non-obvious side effects: pause and propose a plan first. Get sign-off before writing code.
- When in doubt, ask rather than assume scope.

### Testing
- Every piece of new functionality gets tests — happy path AND failure cases.
- Actively think about what could go wrong: bad input, empty data, API errors, type mismatches. Write tests that exercise those paths.
- Tests are written alongside code, not added as an afterthought.
- Run the full test suite after any non-trivial change: `python -m pytest tests/`

### Architectural Decisions
- Don't make structural changes (new modules, new patterns, changed data flow) without first presenting the trade-offs.
- For each option considered, state: what it enables, what it costs, what it forecloses.
- Prefer the simpler option unless there's a concrete reason not to — speculative flexibility is a cost, not a benefit.
- Flag when a decision will be hard to reverse.

## Coding Standards

- Type hints on all function signatures
- Pydantic models for all external data shapes
- `ruff` for formatting and linting (enforced via hook on file save)
- No bare `except:` — catch specific exceptions
- Don't read env vars outside `config.py`

## Testing

- Tests live in `tests/` mirroring source structure
- Use `pytest` fixtures for shared setup
- Mock external calls (NHL API, GCS) — never hit live services in tests
- `python -m pytest tests/` from project root

## What NOT to Do

- Don't run `gcloud` commands without confirming with user — affects shared infra
- Don't hardcode bucket names, API keys, or model names — use `config.py` or prompts
- Don't modify `requirements.txt` without explaining the change
- Don't add print-debugging without removing it afterwards
