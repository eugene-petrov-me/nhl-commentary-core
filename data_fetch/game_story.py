from nhlpy import NHLClient
from typing import Any, Dict, Optional, Tuple
from gcp_ingestion import check_file_exists, download_json, upload_json
from engine.date_index import mark_artifact
from dotenv import load_dotenv
from os import getenv

# Load environment variables
load_dotenv()
bucket_name = getenv("GCS_BUCKET_NAME", "nhl-commentary-bucket")
if not bucket_name:
    raise RuntimeError("Missing GCS_BUCKET_NAME environment variable")

GS_BLOB = "raw/game_story/{game_id}.json"
_client = NHLClient()


class GameStoryFetchError(Exception):
    """Raised when fetching a game's story fails."""


def _looks_like_gs(payload: Dict[str, Any]) -> bool:
    """Loose shape check for MVP."""
    return isinstance(payload, dict) and "summary" in payload


def _infer_date(story: Dict[str, Any]) -> Optional[str]:
    """
    Try to find YYYY-MM-DD in typical fields found in game story payloads.
    """
    for key in ("gameDate", "startTimeUTC", "gameDateUTC"):
        v = story.get(key)
        if isinstance(v, str):
            if "T" in v:
                return v.split("T", 1)[0]
            if len(v) == 10 and v[4] == "-" and v[7] == "-":
                return v
    # Sometimes story mirrors PBP team blocks; fallback if present:
    gcl = story.get("gameCenterLink")
    # e.g. "/gamecenter/col-vs-mtl/2025/04/25/2024030133"
    if isinstance(gcl, str):
        parts = gcl.strip("/").split("/")
        if len(parts) >= 5 and parts[2].isdigit() and parts[3].isdigit() and parts[4].isdigit():
            # parts[2:5] -> YYYY/MM/DD
            return "-".join(parts[2:5])
    return None


def _infer_abbrs(story: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """Return (away_abbr, home_abbr) if present."""
    away = (story.get("awayTeam") or {}).get("abbrev")
    home = (story.get("homeTeam") or {}).get("abbrev")
    return away, home


def _maybe_mark_index(story: Dict[str, Any],
                      *,
                      game_id: int,
                      date: Optional[str],
                      away_abbr: Optional[str],
                      home_abbr: Optional[str],
                      mark: bool) -> None:
    """Best-effort update of the date index for raw_story."""
    if not mark:
        return
    d = date or _infer_date(story)
    a, h = _infer_abbrs(story)
    away = away_abbr or a
    home = home_abbr or h
    if d:
        try:
            mark_artifact(bucket_name, date=d, game_id=game_id,
                          away=away, home=home,
                          artifact="raw_story", exists=True)
        except Exception:
            pass  # index is convenience only


def get_game_story(
    game_id: int,
    *,
    force_refresh: bool = False,
    date: Optional[str] = None,       # "YYYY-MM-DD" for index (optional)
    away_abbr: Optional[str] = None,  # optional for index
    home_abbr: Optional[str] = None,
    mark_index: bool = True,          # toggle index marking
) -> Dict[str, Any]:
    """
    Fetch the game story data for a specific NHL game, using GCS as a cache.
    Optionally updates a per-date index with a 'raw_story' flag.

    Args:
        game_id: Unique identifier for the game.
        force_refresh: If True, bypass cache and fetch from API.
        date, away_abbr, home_abbr: Optional hints to make index rows perfect.
        mark_index: When True, mark 'raw_story' in the date index if we can infer a date.

    Returns:
        Dict[str, Any]: Game story (incl. three stars).

    Raises:
        GameStoryFetchError: On retrieval/validation errors.
    """
    blob_path = GS_BLOB.format(game_id=game_id)

    # 1) Cache
    if not force_refresh and check_file_exists(bucket_name, blob_path):
        try:
            cached = download_json(bucket_name, blob_path)
            if _looks_like_gs(cached):
                _maybe_mark_index(cached, game_id=game_id,
                                  date=date, away_abbr=away_abbr, home_abbr=home_abbr,
                                  mark=mark_index)
                return cached
        except Exception:
            # Ignore cache errors; fall back to API
            pass

    # 2) API
    try:
        story = _client.game_center.game_story(game_id=game_id)
        if not _looks_like_gs(story):
            raise GameStoryFetchError(
                f"Unexpected game story shape for game {game_id}: missing 'summary'."
            )

        # 3) Best-effort cache write
        try:
            upload_json(bucket_name, blob_path, story)
        except Exception:
            pass

        _maybe_mark_index(story, game_id=game_id,
                          date=date, away_abbr=away_abbr, home_abbr=home_abbr,
                          mark=mark_index)
        return story

    except Exception as exc:
        raise GameStoryFetchError(
            f"Failed to fetch game story for game {game_id}: {exc}"
        ) from exc