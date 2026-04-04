"""Testing utilities for end-to-end testing of Kore.ai agentic agents."""

import uuid
from typing import Any, Optional

from agxr.client import AgenticAPIClient
from agxr.config import Config


class AgentTestSession:
    """
    Test session for end-to-end testing of a Kore.ai agentic agent.

    Wraps AgenticAPIClient with a simple send/receive interface that maintains
    conversation context across multiple turns. Uses the Kore.ai Sessions API to
    create and manage server-side session state, ensuring proper context isolation
    between sessions and accurate server-side memory reset on ``reset()``.

    Usage::

        session = AgentTestSession(profile="my-profile")
        response = session.send("Hello")
        assert "hello" in response.lower()
        session.close()

    Or as a context manager (recommended — ensures session is properly terminated)::

        with AgentTestSession(profile="my-profile") as session:
            response = session.send("Hello")
            assert len(response) > 0

    Attributes:
        session_id: The Kore.ai ``sessionReference`` returned by the Sessions API.
            Use this value when referencing the session in other API calls.
        history: Ordered list of ``{"role": "user"|"agent", "text": "..."}`` entries
            for the current session.
        last_response_raw: The raw API response dict from the most recent ``send()`` call.
    """

    def __init__(self, profile: Optional[str] = None) -> None:
        """
        Initialize a test session by creating a real Kore.ai session via the Sessions API.

        Args:
            profile: Name of a configuration profile from ``~/.kore/profiles``.
                If ``None``, configuration is loaded from environment variables.
        """
        self._config = Config(profile=profile)
        self._client = AgenticAPIClient(self._config)
        self._user_reference = f"test-{uuid.uuid4()}"
        self._session_data = self._client.create_session(self._user_reference)
        self._session_reference: str = self._session_data["sessionReference"]
        self._history: list[dict[str, str]] = []
        self._last_response: Optional[dict[str, Any]] = None

    @property
    def session_id(self) -> str:
        """
        The Kore.ai ``sessionReference`` for the current session.

        This value is assigned by the Kore.ai Sessions API and should be used
        as the ``session_identity`` in direct ``AgenticAPIClient.execute_run()``
        calls that need to continue this conversation.
        """
        return self._session_reference

    @property
    def last_response_raw(self) -> Optional[dict[str, Any]]:
        """Raw API response dict from the most recent ``send()`` call."""
        return self._last_response

    @property
    def history(self) -> list[dict[str, str]]:
        """
        Ordered conversation history for the current session.

        Returns a snapshot list; modifications to the returned list do not
        affect the internal state.
        """
        return list(self._history)

    def send(self, message: str) -> str:
        """
        Send a message and return the agent's text response.

        Args:
            message: The user message to send.

        Returns:
            The agent's text response (text output items concatenated with newlines).

        Raises:
            agxr.exceptions.AgenticAPIError: On any API error.
        """
        response = self._client.execute_run(
            query=message,
            session_identity=self._session_reference,
        )
        self._last_response = response
        text = self._extract_text(response)
        self._history.append({"role": "user", "text": message})
        self._history.append({"role": "agent", "text": text})
        return text

    @staticmethod
    def _extract_text(response: dict[str, Any]) -> str:
        """Extract concatenated text content from an API response output array."""
        parts = []
        for item in response.get("output", []):
            if item.get("type") == "text":
                content = item.get("content", "")
                if content:
                    parts.append(content)
        return "\n".join(parts)

    def reset(self) -> None:
        """
        Start a fresh conversation by terminating the current session and creating a new one.

        This performs a full server-side reset: the current session is terminated (clearing
        all server-side memory) and a new session is created. The agent will not have any
        memory of previous turns after ``reset()`` is called.

        Raises:
            agxr.exceptions.AgenticAPIError: If termination or creation fails.
        """
        self._client.terminate_session(self._session_reference)
        self._session_data = self._client.create_session(self._user_reference)
        self._session_reference = self._session_data["sessionReference"]
        self._history.clear()
        self._last_response = None

    def close(self) -> None:
        """
        Terminate the session and close the underlying HTTP client.

        Terminates the Kore.ai session (freeing server-side resources and memory)
        before closing the HTTP connection pool. Called automatically when used
        as a context manager.
        """
        self._client.terminate_session(self._session_reference)
        self._client.close()

    def __enter__(self) -> "AgentTestSession":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return (
            f"AgentTestSession(env='{self._config.env_name}', "
            f"session_reference='{self._session_reference}')"
        )
