import pytest

import config


def test_override_settings_context_manager():
    original = config.get_settings()
    override = config.Settings(
        gcs_bucket_name="test-bucket",
        vertex_project="test-project",
        vertex_location="us-central1",
        vertex_model="gemini-3.8-flash",
    )
    with config.override_settings(override):
        assert config.get_settings() is override
    assert config.get_settings().gcs_bucket_name == original.gcs_bucket_name


def test_clear_overrides_resets_stack():
    override = config.Settings(
        gcs_bucket_name="another",
        vertex_project="test-project",
        vertex_location="us-central1",
        vertex_model="gemini-3.8-flash",
    )
    with config.override_settings(override):
        config.clear_overrides()
        assert config.get_settings() is not override


_ENV_VARS = (
    "GCS_BUCKET_NAME",
    "VERTEX_PROJECT",
    "VERTEX_LOCATION",
    "VERTEX_MODEL",
    "GEMINI_API_KEY",
)


@pytest.fixture
def clean_env(monkeypatch):
    """Isolate _build_settings from the real environment and any local .env."""
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    return monkeypatch


def test_build_settings_defaults(clean_env):
    s = config._build_settings()
    assert s.vertex_project == "nhl-commentary"
    assert s.vertex_location == "us-central1"
    assert s.vertex_model == "gemini-3.8-flash"
    assert s.gemini_api_key == ""
    assert s.gcs_bucket_name == "nhl-commentary-bucket"


def test_build_settings_empty_project_raises(clean_env):
    clean_env.setenv("VERTEX_PROJECT", "")
    with pytest.raises(RuntimeError, match="VERTEX_PROJECT"):
        config._build_settings()


def test_build_settings_empty_bucket_raises(clean_env):
    clean_env.setenv("GCS_BUCKET_NAME", "")
    with pytest.raises(RuntimeError, match="GCS_BUCKET_NAME"):
        config._build_settings()


def test_build_settings_reads_gemini_api_key(clean_env):
    clean_env.setenv("GEMINI_API_KEY", "key-123")
    assert config._build_settings().gemini_api_key == "key-123"


def test_build_settings_reads_overrides_from_env(clean_env):
    clean_env.setenv("VERTEX_PROJECT", "p")
    clean_env.setenv("VERTEX_LOCATION", "europe-west4")
    clean_env.setenv("VERTEX_MODEL", "gemini-other")
    clean_env.setenv("GCS_BUCKET_NAME", "bucket-x")
    s = config._build_settings()
    assert (s.vertex_location, s.vertex_model, s.gcs_bucket_name) == (
        "europe-west4",
        "gemini-other",
        "bucket-x",
    )
