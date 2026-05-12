# nhl-commentary-core

AI-powered NHL game summary backend. Fetches play-by-play, game story, editorial, standings, and season series data from the NHL API, then generates structured game summaries via OpenAI. Exposes results over a FastAPI HTTP service.

## Features

- Rule-based stats summaries (goals, shots, stars, team breakdown)
- AI summaries enriched with editorial recaps, standings, and season series context
- GCS caching for raw data and AI summaries
- Batch processing for all games on a given date
- FastAPI service with typed `GameSummary` responses
- CI with ruff, mypy, and pytest

## Requirements

- Python 3.11+
- OpenAI API key
- Google Cloud Storage bucket

## Setup

```bash
git clone https://github.com/eugene-petrov-me/nhl-commentary-core.git
cd nhl-commentary-core
pip install -r requirements-dev.txt   # runtime + dev/test tools
cp .env.example .env                  # fill in your keys
```

`.env` variables:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `GCS_BUCKET_NAME` | GCS bucket for caching (default: `nhl-commentary-bucket`) |
| `OPENAI_MODEL` | Model to use (default: `gpt-4o-mini`) |

## Usage

**Interactive CLI:**
```bash
python main.py
```

**HTTP API:**
```bash
uvicorn api.app:app --reload
```

Endpoints:

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/games/{game_id}/summary` | Summary for a single game |
| `GET` | `/v1/games/date/{date}/summaries` | Summaries for all games on a date |

Query params: `use_ai=true/false`, `date=YYYY-MM-DD` (on the single-game endpoint).

## Development

```bash
python -m pytest tests/    # run tests
python -m ruff check .     # lint
python -m ruff format .    # format
python -m mypy .           # type check
```

## Project Structure

```
api/              # FastAPI service layer
data_fetch/       # NHL API clients (schedule, play-by-play, game story,
                  #   editorial, standings, season series)
engine/           # Summary generation pipeline
  ai_summary.py      # OpenAI prompt + response
  summarize_game.py  # Orchestrator (AI vs rule-based)
  batch.py           # summarize_date() for daily runs
  process_game.py    # Event processing
gcp_ingestion/    # GCS upload/download helpers
models/           # Pydantic models (GameSummary, GameSchedule)
prompts/          # Prompt templates
config.py         # Settings (env-driven, via get_settings())
main.py           # CLI entry point
```

## Contributing

Fork the repository, create a feature branch, and open a pull request.
