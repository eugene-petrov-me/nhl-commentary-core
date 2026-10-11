# engine/date_index.py
import logging
from typing import Any

from google.api_core.exceptions import GoogleAPIError

from gcp_ingestion import check_file_exists, download_json, upload_json

DATE_INDEX_BLOB = "indexes/by_date/{date}.json"

logger = logging.getLogger(__name__)


def _load_date_index(bucket: str, date: str) -> dict[str, Any]:
    blob = DATE_INDEX_BLOB.format(date=date)
    if check_file_exists(bucket, blob):
        try:
            return download_json(bucket, blob)
        except (GoogleAPIError, ValueError):
            logger.warning(
                "Unreadable date index for %s; starting a fresh one",
                date,
                exc_info=True,
            )
    return {"date": date, "games": []}


def _save_date_index(bucket: str, date: str, doc: dict[str, Any]) -> None:
    blob = DATE_INDEX_BLOB.format(date=date)
    upload_json(bucket, blob, doc)


def _find_row(doc: dict[str, Any], game_id: int) -> dict[str, Any] | None:
    for row in doc.get("games", []):
        if row.get("game_id") == game_id:
            return row
    return None


def mark_artifact(
    bucket: str,
    *,
    date: str,
    game_id: int,
    away: str | None = None,
    home: str | None = None,
    artifact: str,  # one of: "raw_pbp", "raw_story", "events", "summary_stats", "summary_ai"
    exists: bool = True,
) -> None:
    doc = _load_date_index(bucket, date)
    row = _find_row(doc, game_id)
    if not row:
        row = {"game_id": game_id}
        doc["games"].append(row)

    if away:
        row["away"] = away
    if home:
        row["home"] = home

    row[artifact] = exists
    _save_date_index(bucket, date, doc)


def list_games_missing(bucket: str, date: str, artifact: str) -> list[int]:
    doc = _load_date_index(bucket, date)
    out: list[int] = []
    for r in doc.get("games", []):
        if not r.get(artifact, False):
            gid = r.get("game_id")
            if gid is not None:
                out.append(gid)
    return out
