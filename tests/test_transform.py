import pytest

from engine.transform import transform_event


def test_transform_handles_missing_type_desc_key():
    """A missing typeDescKey should result in an unknown event instead of errors."""
    event = {
        # No 'typeDescKey' field
        "details": {},
    }
    result = transform_event(event)
    assert result["event_type"] == "unknown"
    assert result["raw_data"] == event
