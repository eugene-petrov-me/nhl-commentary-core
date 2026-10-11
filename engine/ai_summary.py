"""Generate an AI-powered game summary using Vertex AI (Gemini)."""

from __future__ import annotations

import json
from pathlib import Path

from google import genai
from google.genai import types

from config import get_settings

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "prompts"

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        s = get_settings()
        if s.gemini_api_key:
            _client = genai.Client(api_key=s.gemini_api_key)
        else:
            _client = genai.Client(
                vertexai=True,
                project=s.vertex_project,
                location=s.vertex_location,
            )
    return _client


def _load_template(name: str) -> str:
    """Load a text template from the prompts directory."""
    path = TEMPLATE_DIR / name
    return path.read_text(encoding="utf-8")


def _ordinal(n: object) -> str:
    """Return ordinal suffix for an integer (1 → 'st', 2 → 'nd', etc.)."""
    try:
        i = int(n)  # type: ignore[call-overload]
    except (TypeError, ValueError):
        return ""
    if 11 <= (i % 100) <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(i % 10, "th")


def _format_standings(standings: list[dict]) -> str:
    """Format filtered standings list into a compact prompt-ready string."""
    lines = []
    for s in standings:
        raw = s.get("teamAbbrev", "")
        abbrev = raw.get("default", "") if isinstance(raw, dict) else raw
        div_rank = s.get("divisionSequence", "?")
        div = s.get("divisionName", "?")
        w = s.get("wins", 0)
        losses = s.get("losses", 0)
        ot = s.get("otLosses", 0)
        pts = s.get("points", 0)
        streak = f"{s.get('streakCode', '')}{s.get('streakCount', '')}"
        lines.append(
            f"{abbrev}: {div_rank}{_ordinal(div_rank)} {div} | {w}W-{losses}L-{ot}OT | {pts}pts | Streak: {streak}"
        )
    return "\n".join(lines) if lines else "Standings unavailable."


def _format_season_series(season_series: dict) -> str:
    """Format season series data into a compact prompt-ready string."""
    wins = season_series.get("seasonSeriesWins") or {}
    games = season_series.get("seasonSeries") or []
    if not games:
        return "Season series data unavailable."
    away_wins = wins.get("awayTeamWins", 0)
    home_wins = wins.get("homeTeamWins", 0)
    lines = [f"Series record: {away_wins}-{home_wins} (away-home wins)"]
    for g in games:
        away_team = g.get("awayTeam") or {}
        home_team = g.get("homeTeam") or {}
        away = away_team.get("abbrev", "?")
        home = home_team.get("abbrev", "?")
        a_score = away_team.get("score", "?")
        h_score = home_team.get("score", "?")
        game_date = (g.get("gameDate") or "")[:10]
        lines.append(f"  {game_date}: {away} {a_score} @ {home} {h_score}")
    return "\n".join(lines)


def generate_ai_summary(
    play_by_play: dict,
    game_story: dict,
    editorial: dict | None = None,
    standings: list[dict] | None = None,
    season_series: dict | None = None,
) -> str:
    """Generate a natural language summary for a game.

    Args:
        play_by_play (Dict): Structured play-by-play event data for the game.
        game_story (Dict): Additional narrative data for the game, including
            stars and statistics.
        editorial (Dict, optional): NHL.com editorial recap with headline,
            summary, and full body text. When provided, enriches the AI prompt
            with narrative context (game significance, player quotes, milestones).
        standings (list, optional): Filtered standings entries for home/away teams.
        season_series (dict, optional): Season series games and wins record.

    Returns:
        str: Summary produced by the AI model.
    """
    template = _load_template("game_summary.txt")
    editorial_text = (
        f"{editorial.get('headline', '')}\n\n{editorial.get('body', '')}".strip()
        if editorial
        else "No editorial recap available."
    )
    standings_text = (
        _format_standings(standings) if standings else "Standings unavailable."
    )
    series_text = (
        _format_season_series(season_series)
        if season_series
        else "Season series data unavailable."
    )
    populated = template.format(
        play_by_play=json.dumps(play_by_play, indent=2),
        game_story=json.dumps(game_story, indent=2),
        editorial=editorial_text,
        standings=standings_text,
        season_series=series_text,
    )

    try:
        response = _get_client().models.generate_content(
            model=get_settings().vertex_model,
            contents=populated,
            config=types.GenerateContentConfig(
                system_instruction="Talk like The Hockey Guy.",
            ),
        )
    except Exception as exc:  # pragma: no cover - upstream exceptions vary
        raise RuntimeError(f"Gemini request failed: {exc}") from exc

    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response")
    return text


__all__ = ["generate_ai_summary"]
