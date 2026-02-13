"""
API client for Kore.ai Agentic App Platform.

Provides a class-based interface for making API requests using the ACTUAL
API format (not the initially documented format which was inaccurate).
"""

import time
from typing import Any, Optional

import requests
from requests.exceptions import RequestException, Timeout

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
from agentic_api_cli.config import Config
from agentic_api_cli.exceptions import (
    APIRequestError,
    APIResponseError,
    AuthenticationError,
    RunNotFoundError,
    TimeoutError as AgenticTimeoutError,
    ValidationError,
)
from agentic_api_cli.logging_config import (
    get_logger,
    log_api_request,
    log_api_response,
)


class AgenticAPIClient:
    """
    Client for Kore.ai Agentic App Platform API.

    Handles all API interactions using the actual API format.
    """

    def __init__(self, config: Config) -> None:
        """
        Initialize the API client.

        Args:
            config: Configuration object with API credentials and settings
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(build_headers(self.config.api_key))

    def execute_run(
        self,
        query: str,
        session_identity: str,
        user_reference: Optional[str] = None,
        stream_enabled: bool = False,
        stream_mode: Optional[str] = None,
        debug_enabled: bool = False,
        debug_mode: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Execute an agentic run.

        Args:
            query: User query/input text
            session_identity: Session identifier (used as sessionReference)
            user_reference: User identifier (optional, uses session_identity if not provided)
            stream_enabled: Enable streaming
            stream_mode: Streaming mode ('tokens', 'messages', or 'custom')
            debug_enabled: Enable debug mode
            debug_mode: Debug mode level ('all', 'function-call', or 'thoughts')
            metadata: Custom metadata dictionary

        Returns:
            Response dictionary from the API

        Raises:
            ValidationError: If input validation fails
            AuthenticationError: If authentication fails (401)
            APIRequestError: If the request fails
            APIResponseError: If the API returns an error
            AgenticTimeoutError: If the request times out
        """
        # Validate inputs
        if not query or not query.strip():
            raise ValidationError("Query cannot be empty")

        if not session_identity or not session_identity.strip():
            raise ValidationError("Session identity cannot be empty")

        if stream_mode and stream_mode not in ["tokens", "messages", "custom"]:
            raise ValidationError(
                f"Invalid stream mode: {stream_mode}. Must be 'tokens', 'messages', or 'custom'"
            )

        if debug_mode and debug_mode not in ["all", "function-call", "thoughts"]:
            raise ValidationError(
                f"Invalid debug mode: {debug_mode}. Must be 'all', 'function-call', or 'thoughts'"
            )

        # Build request URL
        url = build_execute_url(self.config.app_id, self.config.env_name)

        # Build sessionIdentity array
        # If user_reference not provided, use session_identity for both
        user_ref = user_reference if user_reference else session_identity
        session_id_array = build_session_identity(user_ref, session_identity)

        # Build input array
        input_array = build_input(query)

        # Build request body with actual API format
        request_body: dict[str, Any] = {
            "sessionIdentity": session_id_array,
            "input": input_array,
        }

        # Add streaming config if enabled
        if stream_enabled or stream_mode:
            request_body["stream"] = {
                "enable": stream_enabled,
            }
            if stream_mode:
                request_body["stream"]["streamMode"] = stream_mode

        # Add debug config if enabled
        if debug_enabled:
            request_body["debug"] = {
                "enable": True
            }
            if debug_mode:
                request_body["debug"]["debugMode"] = debug_mode

        # Add metadata if provided
        if metadata:
            request_body["metaData"] = metadata

        # Make the request
        log_api_request(url, "POST", request_body)

        # Check if streaming is enabled
        # NOTE: "Streaming" provides status updates via SSE, not real-time content streaming
        # Content is fetched from status endpoint after execution completes
        is_streaming = "stream" in request_body and request_body["stream"].get("enable", False)

        try:
            response = self.session.post(
                url, json=request_body, timeout=self.config.timeout, stream=is_streaming
            )

            # Handle different HTTP status codes
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check your API key.", status_code=401
                )
            elif response.status_code == 404:
                raise APIRequestError(
                    f"Resource not found. Check app_id '{self.config.app_id}' "
                    f"and environment '{self.config.env_name}'.",
                    status_code=404,
                )
            elif response.status_code == 429:
                raise APIRequestError(
                    "Rate limit exceeded. Please retry later.", status_code=429
                )
            elif response.status_code >= 400:
                # For error responses, try to parse as JSON
                error_data = response.json() if response.text else {}
                error_message = error_data.get("error", {}).get(
                    "message", response.text or "Unknown error"
                )
                raise APIResponseError(
                    f"API error: {error_message}", status_code=response.status_code
                )

            # Handle streaming response (SSE format)
            if is_streaming:
                return self._process_streaming_response(response)

            # Handle normal JSON response
            log_api_response(response.status_code, response.json() if response.text else None)
            return response.json()

        except Timeout:
            raise AgenticTimeoutError(
                f"Request timed out after {self.config.timeout} seconds"
            )
        except RequestException as e:
            raise APIRequestError(f"Request failed: {str(e)}")

    def _process_streaming_response(self, response) -> dict[str, Any]:
        """
        Process Server-Sent Events (SSE) streaming response.

        IMPORTANT: Kore.ai API's "streaming mode" provides STATUS streaming, not CONTENT streaming.

        Behavior:
        - SSE events contain status updates (busy → idle) and runId
        - Events do NOT contain the actual content/output
        - Content must be fetched separately from Find Run Status endpoint after completion

        This is NOT true streaming like ChatGPT where tokens appear in real-time.
        This IS async execution with status updates via SSE.

        Args:
            response: Streaming response object from requests

        Returns:
            Collected response data in standard format (fetched from status endpoint)

        Raises:
            APIRequestError: If streaming response cannot be processed
        """
        import json as json_module
        from agentic_api_cli.logging_config import get_logger

        logger = get_logger()
        collected_content = []
        collected_tokens = []
        line_count = 0
        run_id = None
        last_session_info = None

        try:
            # Process SSE stream line by line
            # Use chunk_size=1 to get data as soon as it arrives
            for line in response.iter_lines(decode_unicode=True, chunk_size=1):
                line_count += 1

                # DEBUG: Log ALL lines including empty ones
                logger.debug(f"SSE Line {line_count}: {repr(line[:200]) if line else '(empty)'}")

                if not line:
                    continue

                # Check for event type lines
                if line.startswith("event: "):
                    event_type = line[7:].strip()
                    logger.debug(f"Event type: {event_type}")
                    continue

                # SSE events start with "data: "
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix

                    # Skip [DONE] marker
                    if data_str.strip() == "[DONE]":
                        logger.debug("Received [DONE] marker")
                        break

                    try:
                        # Parse the JSON data - Kore.ai format
                        event_data = json_module.loads(data_str)
                        # Log the full event (not truncated)
                        logger.debug(f"Parsed SSE event keys: {event_data.keys()}")
                        if "output" in event_data:
                            logger.debug(f"Event has output: {event_data['output']}")
                        else:
                            logger.debug(f"Event has NO output field. Full event: {json_module.dumps(event_data, indent=2)}")

                        # Capture runId and sessionInfo for status lookup
                        if "sessionInfo" in event_data:
                            last_session_info = event_data["sessionInfo"]
                            if "runId" in last_session_info:
                                run_id = last_session_info["runId"]
                                logger.debug(f"Captured runId: {run_id}")

                        # Extract output array from event
                        # Format: {"eventIndex": N, "messageId": "...", "output": [...], ...}
                        if "output" in event_data and isinstance(event_data["output"], list):
                            for output_item in event_data["output"]:
                                if isinstance(output_item, dict) and output_item.get("type") == "text":
                                    content = output_item.get("content", "")
                                    if content:
                                        collected_content.append(content)
                                        logger.debug(f"Collected content: {content[:100]}...")

                        # Check if this is the last event
                        if event_data.get("isLastEvent", False):
                            logger.debug("Received isLastEvent=true")
                            break

                    except json_module.JSONDecodeError as e:
                        logger.warning(f"Failed to parse SSE event: {data_str[:100]}... Error: {e}")
                        continue
                else:
                    # DEBUG: Log non-data lines
                    logger.debug(f"Non-data line: {line[:200]}")

            # Return collected data in standard format
            # Combine all collected content pieces
            full_content = "".join(collected_content)

            logger.debug(f"Streaming complete. Lines: {line_count}, Content items: {len(collected_content)}")
            logger.debug(f"Full content length: {len(full_content)}")

            # If no content was collected from the stream, fetch it from the status endpoint
            if not full_content and run_id and last_session_info:
                logger.info(f"No content in stream. Fetching output from status endpoint for runId: {run_id}")
                try:
                    # Build sessionIdentity with only sessionReference (per API docs)
                    session_identity = None
                    if "sessionReference" in last_session_info:
                        session_identity = [{
                            "type": "sessionReference",
                            "value": last_session_info["sessionReference"]
                        }]
                        logger.debug(f"Calling status endpoint with sessionIdentity: {session_identity}")

                    # Call the Find Run Status endpoint to get the output
                    status_response = self.get_run_status(run_id, session_identity)
                    logger.debug(f"Status response: {status_response}")

                    # Extract output from status response
                    # Format: {"run": {"kwargs": {"output": [...]}}}
                    if "run" in status_response and "kwargs" in status_response["run"]:
                        output_data = status_response["run"]["kwargs"].get("output", [])
                        logger.debug(f"Fetched output from status endpoint: {output_data}")

                        return {
                            "output": output_data,
                            "sessionInfo": last_session_info,
                            "streaming": True
                        }
                except Exception as e:
                    logger.error(f"Failed to fetch output from status endpoint: {e}", exc_info=True)

            # If we have content from the stream, return it
            if full_content:
                return {
                    "output": [
                        {
                            "type": "text",
                            "content": full_content
                        }
                    ],
                    "streaming": True
                }

            # No content from either source
            logger.warning("No content collected from streaming or status endpoint!")
            return {
                "output": [],
                "streaming": True
            }

        except Exception as e:
            logger.error(f"Error processing streaming response: {e}", exc_info=True)
            raise APIRequestError(f"Failed to process streaming response: {str(e)}")

    def get_run_status(
        self,
        run_id: str,
        session_identity: Optional[list[dict[str, str]]] = None
    ) -> dict[str, Any]:
        """
        Get the status of an asynchronous run.

        Args:
            run_id: The run ID to check
            session_identity: Optional session identity array for context verification

        Returns:
            Status response dictionary

        Raises:
            ValidationError: If run_id is empty
            RunNotFoundError: If the run is not found (404)
            AuthenticationError: If authentication fails (401)
            APIRequestError: If the request fails
            AgenticTimeoutError: If the request times out
        """
        if not run_id or not run_id.strip():
            raise ValidationError("Run ID cannot be empty")

        # Build request URL
        url = build_status_url(self.config.app_id, self.config.env_name, run_id)

        # Build request body with sessionIdentity if provided
        request_body = {}
        if session_identity:
            request_body["sessionIdentity"] = session_identity

        # Make the request
        log_api_request(url, "POST", request_body)
        try:
            response = self.session.post(url, json=request_body, timeout=self.config.timeout)

            log_api_response(response.status_code, response.json() if response.text else None)

            # Handle different HTTP status codes
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check your API key.", status_code=401
                )
            elif response.status_code == 404:
                raise RunNotFoundError(
                    f"Run '{run_id}' not found. Check the run ID.", status_code=404
                )
            elif response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_message = error_data.get("error", {}).get(
                    "message", response.text or "Unknown error"
                )
                raise APIResponseError(
                    f"API error: {error_message}", status_code=response.status_code
                )

            return response.json()

        except Timeout:
            raise AgenticTimeoutError(
                f"Request timed out after {self.config.timeout} seconds"
            )
        except RequestException as e:
            raise APIRequestError(f"Request failed: {str(e)}")

    def poll_run_status(
        self, run_id: str, max_attempts: int = 30, interval: int = 2
    ) -> dict[str, Any]:
        """
        Poll for run status until completion or timeout.

        Args:
            run_id: The run ID to poll
            max_attempts: Maximum number of polling attempts (default: 30)
            interval: Seconds between polling attempts (default: 2)

        Returns:
            Final status response when run completes (success or failed)

        Raises:
            AgenticTimeoutError: If polling times out
            RunNotFoundError: If the run is not found
            APIResponseError: If the API returns an error status
        """
        logger = get_logger('client')
        logger.debug(f"Starting poll for run {run_id} (max_attempts={max_attempts}, interval={interval})")

        for attempt in range(max_attempts):
            logger.debug(f"Poll attempt {attempt + 1}/{max_attempts} for run {run_id}")
            status_response = self.get_run_status(run_id)
            status = status_response.get("status")

            if status == RunStatus.SUCCESS.value:
                return status_response
            elif status == RunStatus.FAILED.value:
                error_info = status_response.get("error", {})
                error_message = error_info.get("message", "Run failed")
                raise APIResponseError(
                    f"Run failed: {error_message}", status_code=500
                )
            elif status in [RunStatus.PENDING.value, RunStatus.RUNNING.value]:
                # Still processing, wait before next attempt
                if attempt < max_attempts - 1:  # Don't sleep on last attempt
                    time.sleep(interval)
                continue
            else:
                # Unknown status
                raise APIResponseError(f"Unknown run status: {status}")

        # Timeout
        raise AgenticTimeoutError(
            f"Run did not complete after {max_attempts * interval} seconds"
        )

    def close(self) -> None:
        """Close the session and clean up resources."""
        self.session.close()

    def __enter__(self) -> "AgenticAPIClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"AgenticAPIClient(app_id='{self.config.app_id}', "
            f"env_name='{self.config.env_name}')"
        )
