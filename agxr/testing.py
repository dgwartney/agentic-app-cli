"""Testing utilities for end-to-end testing of Kore.ai agentic agents."""

import uuid
from typing import Any, Optional

from agxr.client import AgenticAPIClient
from agxr.config import Config


class AgentTestSession:
    """
    Test session for end-to-end testing of a Kore.ai agentic agent.

    Wraps AgenticAPIClient with a simple send/receive interface
    that maintains conversation context across multiple turns.

    Usage:
        session = AgentTestSession(profile="my-profile")
        response = session.send("Hello")
        assert "hello" in response.lower()
        session.close()

    Or as context manager:
        with AgentTestSession(profile="my-profile") as session:
            response = session.send("Hello")
            assert len(response) > 0
    """

    def __init__(self, profile: str) -> None:
        self._config = Config(profile=profile)
        self._client = AgenticAPIClient(self._config)
        self._session_id = self._generate_session_id()
        self._history: list[dict[str, str]] = []
        self._last_response: Optional[dict[str, Any]] = None

    @staticmethod
    def _generate_session_id() -> str:
        return f"test-{uuid.uuid4()}"

    @property
    def session_id(self) -> str:
        """Current session ID."""
        return self._session_id

    @property
    def last_response_raw(self) -> Optional[dict[str, Any]]:
        """Raw API response dict from the last send() call."""
        return self._last_response

    @property
    def history(self) -> list[dict[str, str]]:
        """List of {"role": "user"|"agent", "text": "..."} entries."""
        return list(self._history)

    def send(self, message: str) -> str:
        """
        Send a message and return the agent's text response.

        Args:
            message: The user message to send.

        Returns:
            The agent's text response (concatenated from all text output items).

        Raises:
            agxr.exceptions.AgenticAPIError: On any API error.
        """
        response = self._client.execute_run(
            query=message,
            session_identity=self._session_id,
        )
        self._last_response = response
        text = self._extract_text(response)
        self._history.append({"role": "user", "text": message})
        self._history.append({"role": "agent", "text": text})
        return text

    @staticmethod
    def _extract_text(response: dict[str, Any]) -> str:
        """Extract concatenated text content from API response."""
        parts = []
        for item in response.get("output", []):
            if item.get("type") == "text":
                content = item.get("content", "")
                if content:
                    parts.append(content)
        return "\n".join(parts)

    def reset(self) -> None:
        """Start a new session (new session ID, clear history)."""
        self._session_id = self._generate_session_id()
        self._history.clear()
        self._last_response = None

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._client.close()

    def __enter__(self) -> "AgentTestSession":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return (
            f"AgentTestSession(profile='{self._config.env_name}', "
            f"session_id='{self._session_id}')"
        )
