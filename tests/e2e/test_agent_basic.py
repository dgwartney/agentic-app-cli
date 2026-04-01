"""Example end-to-end tests for the agentic agent."""

import pytest


class TestAgentGreeting:
    """Basic greeting and response tests."""

    def test_agent_responds(self, agent_session):
        """Agent should return a non-empty response to a greeting."""
        response = agent_session.send("Hello")
        assert len(response) > 0

    def test_agent_response_is_string(self, agent_session):
        """Response should be a string."""
        response = agent_session.send("Hi there")
        assert isinstance(response, str)


class TestMultiTurnConversation:
    """Tests that require multiple conversation turns."""

    def test_context_retention(self, agent_session):
        """Agent should remember context from earlier in the conversation."""
        agent_session.send("My name is Alice")
        response = agent_session.send("What is my name?")
        assert "Alice" in response

    def test_session_history_tracked(self, agent_session):
        """Session history should record both user and agent messages."""
        agent_session.send("Hello")
        assert len(agent_session.history) == 2  # 1 user + 1 agent
        assert agent_session.history[0]["role"] == "user"
        assert agent_session.history[1]["role"] == "agent"


class TestSessionManagement:
    """Tests for session reset and isolation."""

    def test_reset_clears_context(self, agent_session):
        """After reset, agent should not remember previous conversation."""
        agent_session.send("My name is Bob")
        agent_session.reset()
        response = agent_session.send("What is my name?")
        assert "Bob" not in response

    def test_reset_changes_session_id(self, agent_session):
        """Reset should generate a new session ID."""
        old_id = agent_session.session_id
        agent_session.reset()
        assert agent_session.session_id != old_id


class TestRawResponse:
    """Tests demonstrating raw response access."""

    def test_raw_response_has_output(self, agent_session):
        """Raw response should contain output array."""
        agent_session.send("Hello")
        raw = agent_session.last_response_raw
        assert raw is not None
        assert "output" in raw
        assert isinstance(raw["output"], list)
