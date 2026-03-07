from __future__ import annotations

import logging

from app.logging_utils import RedactionFilter, redact_value


def test_redact_value_masks_sensitive_keys_and_bearer():
    payload = {
        "api_key": "abc123",
        "nested": {"token": "tok-xyz", "safe": "ok"},
        "authorization": "Bearer SECRET_TOKEN_123",
        "message": "token=aaa password=bbb normal=ccc",
    }

    redacted = redact_value(payload)
    assert redacted["api_key"] == "***REDACTED***"
    assert redacted["nested"]["token"] == "***REDACTED***"
    assert redacted["nested"]["safe"] == "ok"
    assert "***REDACTED***" in redacted["authorization"]
    assert "password=***REDACTED***" in redacted["message"]


def test_redaction_filter_masks_record_extras():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="authorization=Bearer abc.def",
        args=(),
        exc_info=None,
    )
    record.api_key = "super-secret"
    record.user_id = "u-1"

    filt = RedactionFilter()
    assert filt.filter(record) is True
    assert "***REDACTED***" in record.msg
    assert record.api_key == "***REDACTED***"
    assert record.user_id == "u-1"
