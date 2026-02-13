"""
API client for Kore.ai Agentic App Platform.

Provides a class-based interface for making API requests.
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


class AgenticAPIClient:
    """
    Client for Kore.ai Agentic App Platform API.

    Handles all API interactions including execute run and status checking.
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
        async_mode: bool = False,
        stream_mode: Optional[str] = None,
        debug_mode: str = "off",
        stream_debug: bool = False,
        files: Optional[list[dict[str, str]]] = None,
        metadata: Optional[dict[str, Any]] = None,
        skip_cache: bool = False,
    ) -> dict[str, Any]:
        """
        Execute an agentic run.

        Args:
            query: User query/input
            session_identity: Unique session identifier
            async_mode: Execute asynchronously (default: False)
            stream_mode: Streaming mode ('tokens', 'messages', 'custom', or None)
            debug_mode: Debug level ('all', 'summary', 'off')
            stream_debug: Stream debug data in real-time
            files: List of file attachments with 'fileUrl' and 'fileName'
            metadata: Custom metadata dictionary
            skip_cache: Bypass cache for fresh responses

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

        if debug_mode not in ["all", "summary", "off"]:
            raise ValidationError(
                f"Invalid debug mode: {debug_mode}. Must be 'all', 'summary', or 'off'"
            )

        # Build request URL
        url = build_execute_url(self.config.app_id, self.config.env_name)

        # Build request body
        request_body: dict[str, Any] = {
            "sessionIdentity": session_identity,
            "query": query,
        }

        if async_mode:
            request_body["async"] = True

        if stream_mode:
            request_body["stream"] = {"mode": stream_mode}

        if debug_mode != "off" or stream_debug:
            request_body["debug"] = {
                "mode": debug_mode,
                "streamDebugData": stream_debug,
            }

        if files:
            request_body["files"] = files

        if metadata:
            request_body["metaData"] = metadata

        if skip_cache:
            request_body["skipCache"] = True

        # Make the request
        try:
            response = self.session.post(
                url, json=request_body, timeout=self.config.timeout
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
        try:
            response = self.session.post(url, json={}, timeout=self.config.timeout)

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
        for attempt in range(max_attempts):
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

    def execute_and_wait(
        self,
        query: str,
        session_identity: str,
        max_attempts: int = 30,
        interval: int = 2,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a run asynchronously and wait for completion.

        Convenience method that combines execute_run with async=True and poll_run_status.

        Args:
            query: User query/input
            session_identity: Unique session identifier
            max_attempts: Maximum polling attempts
            interval: Seconds between polls
            **kwargs: Additional arguments for execute_run

        Returns:
            Final status response when run completes

        Raises:
            Same exceptions as execute_run and poll_run_status
        """
        # Force async mode
        kwargs["async_mode"] = True

        # Execute the run
        execute_response = self.execute_run(query, session_identity, **kwargs)
        run_id = execute_response.get("runId")

        if not run_id:
            raise APIResponseError("No run ID returned from execute request")

        # Poll for status
        return self.poll_run_status(run_id, max_attempts, interval)

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
