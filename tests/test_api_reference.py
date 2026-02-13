"""
Unit tests for API reference module.
"""

import pytest

from agentic_api_cli.api_reference import (
    BASE_URL,
    DebugMode,
    RunStatus,
    StreamMode,
    build_execute_url,
    build_headers,
    build_input,
    build_session_identity,
    build_status_url,
)


class TestConstants:
    """Test module constants."""

    def test_base_url(self):
        """Test BASE_URL constant."""
        assert BASE_URL == "https://agent-platform.kore.ai/api/v2"

    def test_stream_mode_enum(self):
        """Test StreamMode enum values."""
        assert StreamMode.TOKENS.value == "tokens"
        assert StreamMode.MESSAGES.value == "messages"
        assert StreamMode.CUSTOM.value == "custom"

    def test_debug_mode_enum(self):
        """Test DebugMode enum values."""
        assert DebugMode.ALL.value == "all"
        assert DebugMode.SUMMARY.value == "summary"
        assert DebugMode.OFF.value == "off"

    def test_run_status_enum(self):
        """Test RunStatus enum values."""
        assert RunStatus.PENDING.value == "pending"
        assert RunStatus.RUNNING.value == "running"
        assert RunStatus.SUCCESS.value == "success"
        assert RunStatus.FAILED.value == "failed"


class TestBuildExecuteUrl:
    """Test build_execute_url function."""

    def test_build_execute_url(self):
        """Test building execute URL."""
        url = build_execute_url("test-app-id", "production")
        expected = f"{BASE_URL}/apps/test-app-id/environments/production/runs/execute"
        assert url == expected

    def test_build_execute_url_with_different_env(self):
        """Test execute URL with different environment."""
        url = build_execute_url("app123", "staging")
        expected = f"{BASE_URL}/apps/app123/environments/staging/runs/execute"
        assert url == expected


class TestBuildStatusUrl:
    """Test build_status_url function."""

    def test_build_status_url(self):
        """Test building status URL."""
        url = build_status_url("test-app", "prod", "run-123")
        expected = f"{BASE_URL}/apps/test-app/environments/prod/runs/run-123/status"
        assert url == expected

    def test_build_status_url_with_long_run_id(self):
        """Test status URL with long run ID."""
        run_id = "r-12345678-abcd-efgh-ijkl-123456789012"
        url = build_status_url("app", "env", run_id)
        expected = f"{BASE_URL}/apps/app/environments/env/runs/{run_id}/status"
        assert url == expected


class TestBuildHeaders:
    """Test build_headers function."""

    def test_build_headers(self):
        """Test building request headers."""
        headers = build_headers("test-api-key")

        assert headers["x-api-key"] == "test-api-key"
        assert headers["Content-Type"] == "application/json"

    def test_build_headers_immutable(self):
        """Test that headers are not shared between calls."""
        headers1 = build_headers("key1")
        headers2 = build_headers("key2")

        assert headers1["x-api-key"] == "key1"
        assert headers2["x-api-key"] == "key2"


class TestBuildSessionIdentity:
    """Test build_session_identity function."""

    def test_build_session_identity_with_both(self):
        """Test building session identity with user and session references."""
        result = build_session_identity("user-123", "session-456")

        assert len(result) == 2
        assert result[0] == {"type": "userReference", "value": "user-123"}
        assert result[1] == {"type": "sessionReference", "value": "session-456"}

    def test_build_session_identity_user_only(self):
        """Test building session identity with only user reference."""
        result = build_session_identity("user-123")

        assert len(result) == 1
        assert result[0] == {"type": "userReference", "value": "user-123"}

    def test_build_session_identity_none_session(self):
        """Test building session identity with None session reference."""
        result = build_session_identity("user-123", None)

        assert len(result) == 1
        assert result[0] == {"type": "userReference", "value": "user-123"}

    def test_build_session_identity_empty_session(self):
        """Test building session identity with empty session reference."""
        result = build_session_identity("user-123", "")

        assert len(result) == 1
        assert result[0] == {"type": "userReference", "value": "user-123"}


class TestBuildInput:
    """Test build_input function."""

    def test_build_input_simple_text(self):
        """Test building input with simple text."""
        result = build_input("Hello world")

        assert len(result) == 1
        assert result[0] == {"type": "text", "content": "Hello world"}

    def test_build_input_with_special_characters(self):
        """Test building input with special characters."""
        text = "Test with special chars: @#$%^&*()"
        result = build_input(text)

        assert result[0] == {"type": "text", "content": text}

    def test_build_input_with_unicode(self):
        """Test building input with unicode characters."""
        text = "Hello 世界 🌍"
        result = build_input(text)

        assert result[0] == {"type": "text", "content": text}

    def test_build_input_with_newlines(self):
        """Test building input with newline characters."""
        text = "Line 1\nLine 2\nLine 3"
        result = build_input(text)

        assert result[0] == {"type": "text", "content": text}

    def test_build_input_empty_string(self):
        """Test building input with empty string."""
        result = build_input("")

        assert result[0] == {"type": "text", "content": ""}
