"""Centralized runtime configuration for nhl-commentary-core."""
from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Runtime configuration values."""

    gcs_bucket_name: str
    openai_api_key: str
    openai_model: str


_override_stack: list[Settings] = []
_default_settings: Settings | None = None


def _build_settings() -> Settings:
    """Load settings from environment variables (with dotenv support)."""
    load_dotenv()
    bucket = os.getenv("GCS_BUCKET_NAME", "nhl-commentary-bucket")
    if not bucket:
        raise RuntimeError("Missing GCS_BUCKET_NAME environment variable")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_api_key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return Settings(
        gcs_bucket_name=bucket,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
    )


def get_settings() -> Settings:
    """Return the active settings, honoring any overrides."""
    if _override_stack:
        return _override_stack[-1]
    global _default_settings
    if _default_settings is None:
        _default_settings = _build_settings()
    return _default_settings


@contextmanager
def override_settings(settings: Settings) -> Iterator[Settings]:
    """Temporarily override runtime settings (useful for tests)."""
    _override_stack.append(settings)
    try:
        yield settings
    finally:
        if _override_stack:
            _override_stack.pop()


def clear_overrides() -> None:
    """Remove all active overrides (useful between tests)."""
    _override_stack.clear()


def reload_settings() -> Settings:
    """Force settings to reload from environment variables."""
    global _default_settings
    _default_settings = _build_settings()
    return _default_settings
