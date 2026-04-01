"""Pytest configuration for end-to-end agent tests."""

import os

import pytest

from agxr.testing import AgentTestSession

DEFAULT_PROFILE = "default"


def pytest_addoption(parser):
    """Add --agent-profile CLI option to pytest."""
    parser.addoption(
        "--agent-profile",
        action="store",
        default=None,
        help="Kore.ai profile name for e2e tests (default: env AGXR_TEST_PROFILE or 'default')",
    )


@pytest.fixture(scope="session")
def agent_profile(request) -> str:
    """Resolve the profile name from CLI option, env var, or default."""
    return (
        request.config.getoption("--agent-profile")
        or os.environ.get("AGXR_TEST_PROFILE")
        or DEFAULT_PROFILE
    )


@pytest.fixture
def agent_session(agent_profile) -> AgentTestSession:
    """
    Provide a fresh AgentTestSession for each test.

    Yields an AgentTestSession configured with the resolved profile.
    Automatically closes the session after the test completes.
    """
    with AgentTestSession(profile=agent_profile) as session:
        yield session
