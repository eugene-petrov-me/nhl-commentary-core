import logging
from typing import Any, Dict, Optional, Tuple

from nhlpy import NHLClient

from config import get_settings
from gcp_ingestion import check_file_exists, download_json, upload_json

try:  # engine is optional in some environments (e.g. tests)
    from engine.date_index import mark_artifact
except Exception:  # pragma: no cover - optional dependency
    mark_artifact = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _bucket_name() -> str:
    return get_settings().gcs_bucket_name

PBP_BLOB = "raw/play_by_play/{game_id}.json"

class PlayByPlayFetchError(Exception):
    """Raised when fetching play-by-play data fails."""

def _looks_like_pbp(payload: Dict[str, Any]) -> bool:
    """Loose shape check for MVP."""
    return isinstance(payload, dict) and "plays" in payload

def _infer_date(pbp: Dict[str, Any]) -> Optional[str]:
    """Try to pull YYYY-MM-DD from typical fields in the PBP."""
    for key in ("gameDate", "startTimeUTC", "gameDateUTC"):
        v = pbp.get(key)
        if isinstance(v, str):
            if "T" in v:  # e.g. 2025-04-25T23:00:00Z
                return v.split("T", 1)[0]
            if len(v) == 10 and v[4] == "-" and v[7] == "-":
                return v
    return None

def _infer_abbrs(pbp: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """Return (away_abbr, home_abbr) if present."""
    away = (pbp.get("awayTeam") or {}).get("abbrev")
    home = (pbp.get("homeTeam") or {}).get("abbrev")
    return away, home

def _maybe_mark_index(pbp: Dict[str, Any],
                      *,
                      game_id: int,
                      date: Optional[str],
                      away_abbr: Optional[str],
                      home_abbr: Optional[str],
                      mark: bool) -> None:
    """Best-effort update of the date index for raw_pbp."""
    if not mark:
        return
    d = date or _infer_date(pbp)
    a, h = _infer_abbrs(pbp)
    away = away_abbr or a
    home = home_abbr or h
    if d and mark_artifact:
        try:
            mark_artifact(
                _bucket_name(),
                date=d,
                game_id=game_id,
                away=away,
                home=home,
                artifact="raw_pbp",
                exists=True,
            )
        except Exception:
            logger.warning(
                "Failed to mark raw_pbp index for game %s on %s", game_id, d, exc_info=True
            )

def get_play_by_play(
    game_id: int,
    *,
    force_refresh: bool = False,
    date: Optional[str] = None,       # "YYYY-MM-DD" (optional, used for index)
    away_abbr: Optional[str] = None,  # optional abbrevs for index
    home_abbr: Optional[str] = None,
    mark_index: bool = True,          # turn index marking on/off
) -> Dict[str, Any]:
    """
    Fetch the play-by-play data for a specific NHL game, using GCS as a cache.
    Optionally updates a per-date index with a 'raw_pbp' flag.
    """
    blob_path = PBP_BLOB.format(game_id=game_id)
    bucket = _bucket_name()

    # 1) Cache
    if not force_refresh and check_file_exists(bucket, blob_path):
        pbp = download_json(bucket, blob_path)
        if _looks_like_pbp(pbp):
            _maybe_mark_index(pbp, game_id=game_id,
                              date=date, away_abbr=away_abbr, home_abbr=home_abbr,
                              mark=mark_index)
            return pbp
        # fall through to refetch if cache is malformed

    # 2) API fetch
    try:
        client = NHLClient()
    except Exception as exc:  # pragma: no cover - defensive programming
        raise PlayByPlayFetchError(f"Failed to create NHL client: {exc}") from exc

    try:
        pbp = client.game_center.play_by_play(game_id=game_id)
        if not _looks_like_pbp(pbp):
            raise PlayByPlayFetchError(
                f"Unexpected PBP shape for game {game_id}: missing 'plays'."
            )

        # 3) Best-effort cache write
        try:
            upload_json(bucket, blob_path, pbp)
        except Exception:
            logger.warning(
                "Failed to upload play-by-play cache for game %s", game_id, exc_info=True
            )

        _maybe_mark_index(pbp, game_id=game_id,
                          date=date, away_abbr=away_abbr, home_abbr=home_abbr,
                          mark=mark_index)
        return pbp

    except Exception as exc:
        raise PlayByPlayFetchError(
            f"Failed to fetch play-by-play for game {game_id}: {exc}"
        ) from exc
