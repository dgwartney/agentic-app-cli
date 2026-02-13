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

        # Add metadata if provided
        if metadata:
            request_body["metaData"] = metadata

        # Make the request
        log_api_request(url, "POST", request_body)
        try:
            response = self.session.post(
                url, json=request_body, timeout=self.config.timeout
            )

            log_api_response(response.status_code, response.json() if response.text else None)

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

    def get_run_status(self, run_id: str) -> dict[str, Any]:
        """
        Get the status of an asynchronous run.

        Args:
            run_id: The run ID to check

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

        # Make the request
        log_api_request(url, "POST", {})
        try:
            response = self.session.post(url, json={}, timeout=self.config.timeout)

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
