"""Fetch NHL editorial game recaps from the NHL Forge DAPI."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from config import get_settings
from gcp_ingestion import check_file_exists, download_json, upload_json

try:  # engine module may not be available in all runtimes
    from engine.date_index import mark_artifact
except Exception:  # pragma: no cover - optional dependency
    mark_artifact = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

FORGE_INDEX_URL = (
    "https://forge-dapi.d3.nhle.com/v2/content/en-us/stories"
    "?context.slug=nhl&tags.slug=gameid-{game_id}&$limit=1"
)
FORGE_STORY_URL = "https://forge-dapi.d3.nhle.com{self_url}"

EDITORIAL_BLOB = "raw/editorial/{game_id}.json"

_HTTPX_TIMEOUT = 15.0


class EditorialFetchError(Exception):
    """Raised when fetching editorial content fails unexpectedly."""


def _bucket_name() -> str:
    return get_settings().gcs_bucket_name


def _extract_body(story: Dict[str, Any]) -> str:
    """Concatenate all markdown parts from a Forge DAPI story into plain text."""
    parts = story.get("parts", [])
    chunks: list[str] = []
    for part in parts:
        if isinstance(part, dict) and part.get("type") == "markdown":
            content = part.get("content", "")
            if content:
                chunks.append(content.strip())
    return "\n\n".join(chunks)


def _fetch_from_forge(game_id: int) -> Optional[Dict[str, Any]]:
    """Fetch editorial data from Forge DAPI. Returns None if no recap exists."""
    try:
        import httpx
    except ImportError as exc:  # pragma: no cover
        raise EditorialFetchError(
            "httpx is required for editorial fetch. Run: pip install httpx"
        ) from exc

    # Step 1: search for story by game tag
    index_url = FORGE_INDEX_URL.format(game_id=game_id)
    try:
        resp = httpx.get(index_url, timeout=_HTTPX_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        index_data = resp.json()
    except (httpx.HTTPStatusError, httpx.TimeoutException) as exc:
        raise EditorialFetchError(
            f"Forge DAPI index request failed for game {game_id}: {exc}"
        ) from exc
    except Exception as exc:
        raise EditorialFetchError(
            f"Failed to fetch editorial index for game {game_id}: {exc}"
        ) from exc

    items = index_data.get("items", [])
    if not items:
        logger.debug("No editorial found for game %s", game_id)
        return None

    item = items[0]
    self_url: Optional[str] = item.get("selfUrl") or item.get("url")
    if not self_url:
        logger.debug("Editorial index item missing selfUrl for game %s", game_id)
        return None

    headline = item.get("headline", {})
    if isinstance(headline, dict):
        headline_text = headline.get("default", "")
    else:
        headline_text = str(headline)

    summary_field = item.get("summary", {})
    if isinstance(summary_field, dict):
        summary_text = summary_field.get("default", "")
    else:
        summary_text = str(summary_field)

    content_date = item.get("contentDate") or item.get("date", "")

    # Step 2: fetch the full story for the body text
    story_url = FORGE_STORY_URL.format(self_url=self_url)
    try:
        resp2 = httpx.get(story_url, timeout=_HTTPX_TIMEOUT, follow_redirects=True)
        resp2.raise_for_status()
        story_data = resp2.json()
    except (httpx.HTTPStatusError, httpx.TimeoutException) as exc:
        raise EditorialFetchError(
            f"Forge DAPI story request failed for game {game_id}: {exc}"
        ) from exc
    except Exception as exc:
        raise EditorialFetchError(
            f"Failed to fetch editorial story for game {game_id}: {exc}"
        ) from exc

    body = _extract_body(story_data)

    return {
        "game_id": game_id,
        "headline": headline_text,
        "summary": summary_text,
        "body": body,
        "self_url": self_url,
        "content_date": content_date,
    }


def _maybe_mark_index(
    *,
    game_id: int,
    date: Optional[str],
    away_abbr: Optional[str],
    home_abbr: Optional[str],
    mark: bool,
) -> None:
    """Best-effort update of the date index for raw_editorial."""
    if not mark or not date or not mark_artifact:
        return
    try:
        mark_artifact(
            _bucket_name(),
            date=date,
            game_id=game_id,
            away=away_abbr,
            home=home_abbr,
            artifact="raw_editorial",
            exists=True,
        )
    except Exception:
        logger.warning(
            "Failed to mark raw_editorial index for game %s on %s",
            game_id,
            date,
            exc_info=True,
        )


def get_editorial(
    game_id: int,
    *,
    force_refresh: bool = False,
    date: Optional[str] = None,
    away_abbr: Optional[str] = None,
    home_abbr: Optional[str] = None,
    mark_index: bool = True,
) -> Optional[Dict[str, Any]]:
    """Fetch the editorial game recap for an NHL game, using GCS as a cache.

    Returns None if no editorial recap has been published yet for the game.
    Raises EditorialFetchError on unexpected HTTP or parsing failures.

    Args:
        game_id: Unique NHL game identifier.
        force_refresh: Bypass cache and fetch from Forge DAPI.
        date: YYYY-MM-DD for index marking (optional).
        away_abbr: Away team abbreviation for index (optional).
        home_abbr: Home team abbreviation for index (optional).
        mark_index: When True, mark 'raw_editorial' in the date index.

    Returns:
        Dict with keys: game_id, headline, summary, body, self_url, content_date.
        Or None if no editorial exists yet.

    Raises:
        EditorialFetchError: On unexpected fetch or parsing failures.
    """
    blob_path = EDITORIAL_BLOB.format(game_id=game_id)
    bucket = _bucket_name()

    # 1) Cache hit
    if not force_refresh and check_file_exists(bucket, blob_path):
        try:
            cached = download_json(bucket, blob_path)
            if isinstance(cached, dict):
                _maybe_mark_index(
                    game_id=game_id,
                    date=date,
                    away_abbr=away_abbr,
                    home_abbr=home_abbr,
                    mark=mark_index,
                )
                return cached
        except Exception:
            pass  # Fall through to live fetch on cache read error

    # 2) Fetch from Forge DAPI
    editorial = _fetch_from_forge(game_id)

    if editorial is None:
        # No recap published yet — not an error, don't cache the absence
        return None

    # 3) Best-effort cache write
    try:
        upload_json(bucket, blob_path, editorial)
    except Exception:
        logger.warning(
            "Failed to upload editorial cache for game %s", game_id, exc_info=True
        )

    _maybe_mark_index(
        game_id=game_id,
        date=date,
        away_abbr=away_abbr,
        home_abbr=home_abbr,
        mark=mark_index,
    )

    return editorial


__all__ = ["get_editorial", "EditorialFetchError"]
