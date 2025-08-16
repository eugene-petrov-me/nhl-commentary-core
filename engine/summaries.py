# engine/summaries.py
from typing import List, Dict, Optional
from os import getenv
from dotenv import load_dotenv

from gcp_ingestion import check_file_exists, download_text, upload_text

# Lazy import inside functions to avoid any possible import loops:
def _mark(artifact: str, *, bucket: str, date: Optional[str], game_id: int) -> None:
    if not date:
        return
    try:
        from engine.date_index import mark_artifact
        mark_artifact(bucket, date=date, game_id=game_id, artifact=artifact, exists=True)
    except Exception:
        pass  # index is convenience only

load_dotenv()
_BUCKET = getenv("GCS_BUCKET_NAME", "nhl-commentary-bucket")

_STATS_BLOB = "derived/summary/stats/{game_id}.txt"
_AI_BLOB    = "derived/summary/ai/{game_id}.md"

def get_or_build_stats_summary(
    *,
    game_id: int,
    events: List[Dict],
    date: Optional[str] = None,
    force_refresh: bool = False,
    generator_fn=None  # inject generate_summary to avoid circular import
) -> str:
    """
    Return rule-based (stats) summary from GCS if present, otherwise build and upload.
    """
    if generator_fn is None:
        # import here (lazy) to avoid circular imports at module load time
        from engine.generate_summary import generate_summary as _gen
        generator_fn = _gen

    blob = _STATSBLOB = _STATS_BLOB.format(game_id=game_id)

    if not force_refresh and check_file_exists(_BUCKET, blob):
        return download_text(_BUCKET, blob)

    # Build, upload, mark index
    summary = generator_fn(events)
    upload_text(_BUCKET, blob, summary, content_type="text/plain")
    _mark("summary_stats", bucket=_BUCKET, date=date, game_id=game_id)
    return summary


def save_ai_summary(*, game_id: int, md: str, date: Optional[str] = None) -> None:
    """
    Persist an AI-written markdown summary and mark the date index.
    """
    blob = _AI_BLOB.format(game_id=game_id)
    upload_text(_BUCKET, blob, md, content_type="text/markdown")
    _mark("summary_ai", bucket=_BUCKET, date=date, game_id=game_id)
    print(f"AI summary for game {game_id} saved to {_BUCKET}/{blob}")


def load_ai_summary(*, game_id: int) -> Optional[str]:
    """
    Load an AI summary if it exists; return None otherwise.
    """
    blob = _AI_BLOB.format(game_id=game_id)
    if not check_file_exists(_BUCKET, blob):
        return None
    return download_text(_BUCKET, blob)