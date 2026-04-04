# Testing Guide: AgentTestSession

End-to-end testing of Kore.ai agentic agents using pytest.

## Overview

`AgentTestSession` is a lightweight wrapper around the `agxr` API client that provides a simple `send(message) -> str` interface for testing agent behavior. Tests make **real API calls** to the agent platform, validating actual agent responses just like a live user chatting.

On initialization, `AgentTestSession` calls the Kore.ai Sessions API to create a real server-side session. The `session_id` property returns the API-assigned `sessionReference` that identifies this session on the server. This ensures proper server-side memory management: `reset()` performs a true server-side context reset (terminate + recreate), and `close()` terminates the session to free server resources.

## Prerequisites

You need a configured profile with valid credentials:

```bash
agxr profile add \
  --name staging \
  --api-key "your-api-key" \
  --app-id "your-app-id" \
  --env-name staging
```

Verify the profile works:

```bash
agxr chat --profile staging
```

## Quick Start

```python
from agxr.testing import AgentTestSession


def test_agent_responds(agent_session):
    response = agent_session.send("Hello")
    assert len(response) > 0


def test_remembers_context(agent_session):
    agent_session.send("My name is Alice")
    response = agent_session.send("What is my name?")
    assert "Alice" in response
```

Run the tests:

```bash
pytest tests/e2e/ --agent-profile staging
```

## Class API

### `AgentTestSession(profile: Optional[str] = None)`

Creates a test session using the specified configuration profile. If `profile` is `None`, credentials are loaded from environment variables (`KOREAI_API_KEY`, `KOREAI_APP_ID`, `KOREAI_ENV_NAME`).

On construction, the Kore.ai Sessions API is called to create a server-side session.

```python
session = AgentTestSession(profile="staging")
```

Or as a context manager (recommended — ensures the session is properly terminated):

```python
with AgentTestSession(profile="staging") as session:
    response = session.send("Hello")
```

### `send(message: str) -> str`

Sends a message to the agent and returns the text response. Maintains conversation context across calls within the same session.

```python
response = session.send("What is 2 + 2?")
assert "4" in response
```

### `reset()`

Performs a full server-side context reset: terminates the current Kore.ai session (clearing all server-side agent memory) and creates a new one. The agent will not remember previous messages after `reset()`.

```python
session.send("My name is Bob")
session.reset()
response = session.send("What is my name?")
# Agent should NOT know the name
```

### `close()`

Terminates the Kore.ai session (freeing server-side resources) and closes the underlying HTTP connection pool. Called automatically when using the context manager.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `session_id` | `str` | API-assigned `sessionReference` from the Kore.ai Sessions API |
| `last_response_raw` | `dict \| None` | Full API response from the last `send()` call |
| `history` | `list[dict]` | Conversation history: `[{"role": "user"\|"agent", "text": "..."}]` |

## Pytest Fixtures

The `tests/e2e/conftest.py` provides two fixtures:

### `agent_profile` (session-scoped)

Resolves the profile name with this precedence:

1. `--agent-profile` pytest CLI option
2. `AGXR_TEST_PROFILE` environment variable
3. `"default"` fallback

### `agent_session` (function-scoped)

Provides a fresh `AgentTestSession` for each test. Automatically closed after the test.

```python
def test_example(agent_session):
    response = agent_session.send("Hello")
    assert response
```

## Running Tests

```bash
# With a specific profile
pytest tests/e2e/ --agent-profile staging

# Via environment variable
AGXR_TEST_PROFILE=staging pytest tests/e2e/

# Single test
pytest tests/e2e/test_agent_basic.py::TestMultiTurnConversation::test_context_retention -v

# With verbose output
pytest tests/e2e/ --agent-profile staging -v
```

Unit tests exclude e2e tests by default:

```bash
# Runs only unit tests (e2e ignored)
pytest
```

## Example Test Patterns

### Testing Specific Agent Capabilities

```python
class TestAgentKnowledge:
    def test_answers_domain_question(self, agent_session):
        response = agent_session.send("What services do you support?")
        assert "support" in response.lower() or len(response) > 10

    def test_handles_unknown_question(self, agent_session):
        response = agent_session.send("What is the airspeed velocity of an unladen swallow?")
        assert len(response) > 0  # Agent should respond gracefully
```

### Testing Multi-Turn Workflows

```python
class TestWorkflow:
    def test_step_by_step_task(self, agent_session):
        agent_session.send("I want to create a new account")
        response = agent_session.send("My email is test@example.com")
        assert "email" in response.lower() or "account" in response.lower()
```

### Inspecting Raw Responses

```python
class TestResponseStructure:
    def test_response_format(self, agent_session):
        agent_session.send("Hello")
        raw = agent_session.last_response_raw
        assert "output" in raw
        for item in raw["output"]:
            assert "type" in item
            assert "content" in item
```

### Using History for Assertions

```python
class TestConversationFlow:
    def test_three_turn_conversation(self, agent_session):
        agent_session.send("Hello")
        agent_session.send("Tell me a joke")
        agent_session.send("Tell me another one")
        assert len(agent_session.history) == 6  # 3 user + 3 agent
```

### Standalone Usage (Without Fixtures)

```python
from agxr.testing import AgentTestSession


def test_standalone():
    with AgentTestSession(profile="staging") as session:
        response = session.send("Hello")
        assert len(response) > 0
```

## Evaluating Agent Responses with deepeval

For assertions beyond simple string matching, [deepeval](https://github.com/confident-ai/deepeval) provides LLM-as-judge evaluation — define quality criteria in plain English and let an LLM score the response.

### Install

```bash
pip install deepeval
```

deepeval requires an OpenAI API key for its evaluation LLM:

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### Basic Usage

```python
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


def test_helpful_greeting(agent_session):
    response = agent_session.send("Hello")
    metric = GEval(
        name="Helpfulness",
        criteria="The response is a helpful greeting that offers assistance.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.5,
    )
    assert_test(LLMTestCase(input="Hello", actual_output=response), [metric])
```

### Custom Evaluation Criteria

Define any criteria in plain English:

```python
def test_professional_tone(agent_session):
    response = agent_session.send("I need help with my account")
    metric = GEval(
        name="Professionalism",
        criteria="The response uses a professional, empathetic tone appropriate for customer support.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7,
    )
    assert_test(LLMTestCase(input="I need help with my account", actual_output=response), [metric])
```

### Evaluating Against Expected Output

Check if the response matches an expected answer:

```python
def test_factual_answer(agent_session):
    response = agent_session.send("What are your business hours?")
    metric = GEval(
        name="Correctness",
        criteria="The response accurately states the business hours and matches the expected information.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.7,
    )
    assert_test(
        LLMTestCase(
            input="What are your business hours?",
            actual_output=response,
            expected_output="Our business hours are Monday to Friday, 9 AM to 5 PM.",
        ),
        [metric],
    )
```

### Multiple Criteria in One Test

Apply several metrics to a single response:

```python
def test_comprehensive_response(agent_session):
    question = "How do I reset my password?"
    response = agent_session.send(question)

    relevance = GEval(
        name="Relevance",
        criteria="The response directly addresses the password reset question.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7,
    )
    clarity = GEval(
        name="Clarity",
        criteria="The response provides clear, step-by-step instructions.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.6,
    )
    assert_test(LLMTestCase(input=question, actual_output=response), [relevance, clarity])
```

### Notes

- Each evaluation call costs ~$0.01-0.05 (OpenAI API usage)
- The `threshold` (0.0-1.0) controls how strict the evaluation is
- `assert_test` raises `AssertionError` on failure with detailed scoring output
- Run with `pytest -s` to see evaluation scores in the output

## Tips

- **Each test gets a fresh session** via the `agent_session` fixture, so tests are isolated by default.
- **Use `reset()`** within a single test to verify the agent forgets previous context.
- **Check `last_response_raw`** when you need to assert on response structure beyond the text content.
- **Keep tests focused** — each test should verify one behavior. Multi-turn tests are fine but keep the turn count low.
- **Be flexible with assertions** — agent responses are non-deterministic. Assert on key content rather than exact strings.
- **Set timeouts** — real API calls can be slow. Consider pytest-timeout if tests hang.
