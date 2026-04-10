"""Tests for models.game_summary.GameSummary."""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from models.game_summary import GameSummary

NOW = datetime.now(timezone.utc)


def _make(**kwargs) -> GameSummary:
    defaults = dict(
        game_id=2024020001,
        summary_markdown="Great game.",
        summary_type="ai",
        generated_at=NOW,
        cached=False,
    )
    defaults.update(kwargs)
    return GameSummary(**defaults)


def test_minimal_valid_model():
    gs = _make()
    assert gs.game_id == 2024020001
    assert gs.summary_markdown == "Great game."
    assert gs.home_team is None
    assert gs.cached is False


def test_full_model():
    gs = _make(
        date="2025-04-25",
        home_team="MTL",
        away_team="COL",
        home_score=3,
        away_score=2,
        summary_type="rule_based",
        editorial_headline="Habs win!",
        editorial_summary="Short recap.",
        cached=True,
    )
    assert gs.home_team == "MTL"
    assert gs.home_score == 3
    assert gs.editorial_headline == "Habs win!"
    assert gs.summary_type == "rule_based"


def test_json_round_trip():
    gs = _make(date="2025-04-25", home_team="MTL", away_team="COL")
    serialised = gs.model_dump_json()
    restored = GameSummary.model_validate_json(serialised)
    assert restored.game_id == gs.game_id
    assert restored.home_team == gs.home_team
    assert restored.generated_at == gs.generated_at


def test_invalid_summary_type_raises():
    with pytest.raises(ValidationError):
        _make(summary_type="unknown")


def test_model_copy_enrichment():
    gs = _make()
    assert gs.home_team is None
    enriched = gs.model_copy(update={"home_team": "MTL", "away_team": "COL", "home_score": 3, "away_score": 2})
    assert enriched.home_team == "MTL"
    assert enriched.away_score == 2
    # Original unchanged
    assert gs.home_team is None
