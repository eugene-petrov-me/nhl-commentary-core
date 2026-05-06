"""Tests for data_fetch.season_series."""
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

import data_fetch.season_series as series_mod  # noqa: E402
from data_fetch.season_series import SeasonSeriesFetchError, get_season_series  # noqa: E402


def _fake_right_rail(response: dict):
    return SimpleNamespace(
        game_center=SimpleNamespace(right_rail=lambda game_id: response)
    )


def test_get_season_series_extracts_series_and_wins(monkeypatch):
    response = {
        "seasonSeries": [{"id": 1}, {"id": 2}],
        "seasonSeriesWins": {"awayTeamWins": 1, "homeTeamWins": 1},
        "gameInfo": {},
    }
    monkeypatch.setattr(series_mod, "NHLClient", lambda: _fake_right_rail(response))

    result = get_season_series(2024020001)

    assert result["seasonSeries"] == [{"id": 1}, {"id": 2}]
    assert result["seasonSeriesWins"] == {"awayTeamWins": 1, "homeTeamWins": 1}
    assert "gameInfo" not in result


def test_get_season_series_handles_missing_keys(monkeypatch):
    monkeypatch.setattr(series_mod, "NHLClient", lambda: _fake_right_rail({}))

    result = get_season_series(2024020001)

    assert result["seasonSeries"] == []
    assert result["seasonSeriesWins"] == {}


def test_get_season_series_raises_on_client_error(monkeypatch):
    monkeypatch.setattr(series_mod, "NHLClient", lambda: (_ for _ in ()).throw(RuntimeError("fail")))

    import pytest
    with pytest.raises(SeasonSeriesFetchError, match="Failed to create NHL client"):
        get_season_series(2024020001)


def test_get_season_series_raises_on_api_error(monkeypatch):
    def bad_right_rail(game_id):
        raise RuntimeError("timeout")

    monkeypatch.setattr(
        series_mod,
        "NHLClient",
        lambda: SimpleNamespace(game_center=SimpleNamespace(right_rail=bad_right_rail)),
    )

    import pytest
    with pytest.raises(SeasonSeriesFetchError, match="Failed to fetch right_rail"):
        get_season_series(2024020001)
