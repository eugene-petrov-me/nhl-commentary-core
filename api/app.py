from __future__ import annotations

import logging
from datetime import date as Date
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query

from data_fetch.game_story import GameStoryFetchError
from data_fetch.play_by_play import PlayByPlayFetchError
from data_fetch.schedule import ScheduleFetchError
from engine.batch import summarize_date
from engine.summarize_game import summarize_game
from models.game_summary import GameSummary

logger = logging.getLogger(__name__)

app = FastAPI(title="NHL Commentary API", version="1.0.0")


@app.get("/v1/games/{game_id}/summary", response_model=GameSummary)
def get_game_summary(
    game_id: int,
    date: Optional[str] = Query(default=None),
    use_ai: bool = Query(default=True),
) -> GameSummary:
    try:
        return summarize_game(game_id, date=date, use_ai=use_ai)
    except (PlayByPlayFetchError, GameStoryFetchError) as exc:
        logger.warning("NHL API fetch failed for game %s: %s", game_id, exc)
        raise HTTPException(status_code=502, detail=str(exc))
    except RuntimeError as exc:
        logger.error("OpenAI failure for game %s: %s", game_id, exc)
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/v1/games/date/{date}/summaries", response_model=List[GameSummary])
def get_date_summaries(
    date: Date,
    use_ai: bool = Query(default=True),
) -> List[GameSummary]:
    date_str = date.isoformat()
    try:
        return summarize_date(date_str, use_ai=use_ai)
    except ScheduleFetchError as exc:
        logger.warning("Schedule fetch failed for %s: %s", date_str, exc)
        raise HTTPException(status_code=502, detail=str(exc))
