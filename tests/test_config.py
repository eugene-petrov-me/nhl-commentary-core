import config


def test_override_settings_context_manager():
    original = config.get_settings()
    override = config.Settings(gcs_bucket_name="test-bucket", openai_api_key="k", openai_model="gpt-4o-mini")
    with config.override_settings(override):
        assert config.get_settings() is override
    assert config.get_settings().gcs_bucket_name == original.gcs_bucket_name


def test_clear_overrides_resets_stack():
    override = config.Settings(gcs_bucket_name="another", openai_api_key="k", openai_model="gpt-4o-mini")
    with config.override_settings(override):
        config.clear_overrides()
        assert config.get_settings() is not override
