"""Tests for data_fetch.standings."""
import sys
from types import SimpleNamespace

# Stub heavy deps before any project imports
fake_nhlpy = SimpleNamespace(NHLClient=lambda: SimpleNamespace())
sys.modules.setdefault("nhlpy", fake_nhlpy)

fake_storage = SimpleNamespace(Client=lambda: None, Bucket=SimpleNamespace)
fake_exceptions = SimpleNamespace(NotFound=Exception)
fake_google_cloud = SimpleNamespace(storage=fake_storage)
fake_google_api_core = SimpleNamespace(exceptions=fake_exceptions)
sys.modules.setdefault("google", SimpleNamespace(cloud=fake_google_cloud, api_core=fake_google_api_core))
sys.modules.setdefault("google.cloud", fake_google_cloud)
sys.modules.setdefault("google.cloud.storage", fake_storage)
sys.modules.setdefault("google.api_core", fake_google_api_core)
sys.modules.setdefault("google.api_core.exceptions", fake_exceptions)

import data_fetch.standings as standings_mod  # noqa: E402
from data_fetch.standings import StandingsFetchError, get_standings  # noqa: E402


def _make_entry(abbrev: str, div_rank: int = 1, div: str = "Atlantic") -> dict:
    return {
        "teamAbbrev": abbrev,
        "divisionSequence": div_rank,
        "divisionName": div,
        "wins": 40,
        "losses": 30,
        "otLosses": 8,
        "points": 88,
        "streakCode": "W",
        "streakCount": 2,
    }


def _fake_client(entries: list):
    """Return a fake NHLClient whose standings.get_standings returns the given entries."""
    return SimpleNamespace(
        standings=SimpleNamespace(
            get_standings=lambda date=None, **kw: {"standings": entries}
        )
    )


def test_get_standings_filters_to_two_teams(monkeypatch):
    all_entries = [_make_entry("MTL"), _make_entry("COL"), _make_entry("TOR")]
    monkeypatch.setattr(standings_mod, "NHLClient", lambda: _fake_client(all_entries))

    result = get_standings("2025-04-25", home_abbr="MTL", away_abbr="COL")

    assert len(result) == 2
    abbrevs = {e["teamAbbrev"] for e in result}
    assert abbrevs == {"MTL", "COL"}


def test_get_standings_handles_dict_abbrev(monkeypatch):
    entry = _make_entry("MTL")
    entry["teamAbbrev"] = {"default": "MTL"}
    monkeypatch.setattr(standings_mod, "NHLClient", lambda: _fake_client([entry]))

    result = get_standings("2025-04-25", home_abbr="MTL", away_abbr="COL")

    assert len(result) == 1
    assert result[0]["teamAbbrev"]["default"] == "MTL"


def test_get_standings_returns_empty_when_no_match(monkeypatch):
    entries = [_make_entry("TOR"), _make_entry("BOS")]
    monkeypatch.setattr(standings_mod, "NHLClient", lambda: _fake_client(entries))

    result = get_standings("2025-04-25", home_abbr="MTL", away_abbr="COL")

    assert result == []


def test_get_standings_returns_empty_when_api_returns_none(monkeypatch):
    monkeypatch.setattr(
        standings_mod,
        "NHLClient",
        lambda: SimpleNamespace(
            standings=SimpleNamespace(get_standings=lambda **kw: {"standings": None})
        ),
    )

    result = get_standings("2025-04-25", home_abbr="MTL", away_abbr="COL")

    assert result == []


def test_get_standings_returns_empty_when_response_is_none(monkeypatch):
    monkeypatch.setattr(
        standings_mod,
        "NHLClient",
        lambda: SimpleNamespace(
            standings=SimpleNamespace(get_standings=lambda **kw: None)
        ),
    )

    result = get_standings("2025-04-25", home_abbr="MTL", away_abbr="COL")

    assert result == []


def test_get_standings_raises_on_api_error(monkeypatch):
    def bad_client():
        raise RuntimeError("network error")

    monkeypatch.setattr(standings_mod, "NHLClient", bad_client)

    import pytest
    with pytest.raises(StandingsFetchError, match="Failed to create NHL client"):
        get_standings("2025-04-25", home_abbr="MTL", away_abbr="COL")


def test_get_standings_raises_on_fetch_error(monkeypatch):
    def bad_get_standings(**kw):
        raise RuntimeError("timeout")

    monkeypatch.setattr(
        standings_mod,
        "NHLClient",
        lambda: SimpleNamespace(standings=SimpleNamespace(get_standings=bad_get_standings)),
    )

    import pytest
    with pytest.raises(StandingsFetchError, match="Failed to fetch standings"):
        get_standings("2025-04-25", home_abbr="MTL", away_abbr="COL")
