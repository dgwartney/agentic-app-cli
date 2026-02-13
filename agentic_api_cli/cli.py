"""
Command-line interface for Kore.ai Agentic App Platform.

Provides CLI commands for executing runs and checking status.
"""

import argparse
import json
import sys
from typing import NoReturn, Optional

from agentic_api_cli import __version__
from agentic_api_cli.client import AgenticAPIClient
from agentic_api_cli.config import Config
from agentic_api_cli.exceptions import AgenticAPIError


class CLI:
    """
    Main CLI class for Agentic API.

    Handles argument parsing and command execution.
    """

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.parser = self._create_parser()
        self.config: Optional[Config] = None
        self.client: Optional[AgenticAPIClient] = None

    def _create_parser(self) -> argparse.ArgumentParser:
        """
        Create and configure the argument parser.

        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            prog="agentic-api-cli",
            description="Command-line interface for Kore.ai Agentic App Platform",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Execute a synchronous run
  agentic-api-cli execute --query "What is the weather?" --session-id session-001

  # Execute with streaming
  agentic-api-cli execute --query "Explain AI" --session-id session-001 --stream tokens

  # Execute asynchronously
  agentic-api-cli execute --query "Analyze data" --session-id session-001 --async

  # Check run status
  agentic-api-cli status --run-id run-xyz-789

  # Execute and wait for completion
  agentic-api-cli execute --query "Process data" --session-id session-001 --async --wait

Environment Variables:
  KOREAI_API_KEY       API key for authentication (required)
  KOREAI_APP_ID        Application ID (required)
  KOREAI_ENV_NAME      Environment name (default: production)
  KOREAI_BASE_URL      Base URL for API (default: https://agent-platform.kore.ai/api/v2)
  KOREAI_TIMEOUT       Request timeout in seconds (default: 30)
            """,
        )

        # Global options
        parser.add_argument(
            "--version", action="version", version=f"%(prog)s {__version__}"
        )
        parser.add_argument(
            "--api-key",
            help="API key (overrides KOREAI_API_KEY env var)",
            metavar="KEY",
        )
        parser.add_argument(
            "--app-id",
            help="Application ID (overrides KOREAI_APP_ID env var)",
            metavar="ID",
        )
        parser.add_argument(
            "--env-name",
            help="Environment name (overrides KOREAI_ENV_NAME env var)",
            metavar="NAME",
        )
        parser.add_argument(
            "--base-url",
            help="Base URL for API (overrides KOREAI_BASE_URL env var)",
            metavar="URL",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            help="Request timeout in seconds (overrides KOREAI_TIMEOUT env var)",
            metavar="SECONDS",
        )
        parser.add_argument(
            "--env-file",
            help="Path to .env file for configuration",
            metavar="FILE",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output in JSON format",
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Verbose output (show request/response details)",
        )

        # Subcommands
        subparsers = parser.add_subparsers(
            dest="command", help="Available commands", required=True
        )

        # Execute command
        execute_parser = subparsers.add_parser(
            "execute",
            help="Execute an agentic run",
            description="Execute an agentic app run with a query",
        )
        execute_parser.add_argument(
            "--query",
            "-q",
            required=True,
            help="Query or input text for the agent",
            metavar="TEXT",
        )
        execute_parser.add_argument(
            "--session-id",
            "-s",
            required=True,
            help="Session identifier (used as sessionReference)",
            metavar="ID",
        )
        execute_parser.add_argument(
            "--user-id",
            "-u",
            help="User identifier (optional, defaults to session-id)",
            metavar="ID",
        )
        execute_parser.add_argument(
            "--stream",
            choices=["tokens", "messages", "custom"],
            help="Enable streaming with specified mode",
            metavar="MODE",
        )
        execute_parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode",
        )
        execute_parser.add_argument(
            "--metadata",
            help="JSON string of metadata key-value pairs",
            metavar="JSON",
        )

        # Status command
        status_parser = subparsers.add_parser(
            "status",
            help="Check run status",
            description="Check the status of an asynchronous run",
        )
        status_parser.add_argument(
            "--run-id",
            "-r",
            required=True,
            help="Run ID to check status for",
            metavar="ID",
        )
        status_parser.add_argument(
            "--wait",
            action="store_true",
            help="Wait for run to complete",
        )
        status_parser.add_argument(
            "--poll-interval",
            type=int,
            default=2,
            help="Polling interval in seconds when waiting (default: 2)",
            metavar="SECONDS",
        )
        status_parser.add_argument(
            "--max-attempts",
            type=int,
            default=30,
            help="Maximum polling attempts when waiting (default: 30)",
            metavar="N",
        )

        # Config command
        config_parser = subparsers.add_parser(
            "config",
            help="Show configuration",
            description="Display current configuration (with sensitive data masked)",
        )

        return parser

    def _load_config(self, args: argparse.Namespace) -> Config:
        """
        Load configuration from environment and command-line arguments.

        Args:
            args: Parsed command-line arguments

        Returns:
            Configured Config instance
        """
        config = Config(env_file=args.env_file)

        # Override with command-line arguments if provided
        if args.api_key:
            config.api_key = args.api_key
        if args.app_id:
            config.app_id = args.app_id
        if args.env_name:
            config.env_name = args.env_name
        if args.base_url:
            config.base_url = args.base_url
        if args.timeout:
            config.timeout = args.timeout

        return config

    def _print_output(
        self, data: dict, as_json: bool = False, verbose: bool = False
    ) -> None:
        """
        Print output to stdout.

        Args:
            data: Data to print
            as_json: Output as JSON
            verbose: Include all fields
        """
        if as_json:
            print(json.dumps(data, indent=2))
        else:
            # Pretty print for human readability
            # Handle actual API response format with output array
            if "output" in data:
                # Extract text content from output array
                for item in data["output"]:
                    if item.get("type") == "text":
                        print(item.get("content", ""))
            # Handle sessionInfo for metadata
            elif "sessionInfo" in data:
                session_info = data["sessionInfo"]
                if "runId" in session_info:
                    print(f"Run ID: {session_info['runId']}")
                if "status" in session_info:
                    print(f"Status: {session_info['status']}")
            # Handle old format (for backwards compatibility)
            elif "response" in data:
                print(f"\nResponse:\n{data['response']}")
            elif "message" in data:
                print(f"Message: {data['message']}")

            # Show errors if present
            if "error" in data:
                print(f"\nError: {data['error']}")

            # Verbose mode shows full response
            if verbose:
                print(f"\nFull Response:\n{json.dumps(data, indent=2)}")

    def _handle_execute(self, args: argparse.Namespace) -> int:
        """
        Handle the execute command.

        Args:
            args: Parsed arguments

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            # Parse metadata if provided
            metadata = None
            if args.metadata:
                try:
                    metadata = json.loads(args.metadata)
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in --metadata: {e}", file=sys.stderr)
                    return 1

            if args.verbose:
                print(f"Executing run with session: {args.session_id}")
                if hasattr(args, 'user_id') and args.user_id:
                    print(f"User ID: {args.user_id}")
                print(f"Query: {args.query}")

            # Execute the run with actual API format
            response = self.client.execute_run(
                query=args.query,
                session_identity=args.session_id,
                user_reference=getattr(args, 'user_id', None),
                stream_enabled=bool(args.stream),
                stream_mode=args.stream if args.stream else None,
                debug_enabled=args.debug if hasattr(args, 'debug') else False,
                metadata=metadata,
            )

            self._print_output(response, as_json=args.json, verbose=args.verbose)
            return 0

        except AgenticAPIError as e:
            print(f"Error: {e.message}", file=sys.stderr)
            if args.verbose and e.status_code:
                print(f"Status Code: {e.status_code}", file=sys.stderr)
            return 1

    def _handle_status(self, args: argparse.Namespace) -> int:
        """
        Handle the status command.

        Args:
            args: Parsed arguments

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            if args.verbose:
                print(f"Checking status for run: {args.run_id}")

            if args.wait:
                response = self.client.poll_run_status(
                    run_id=args.run_id,
                    max_attempts=args.max_attempts,
                    interval=args.poll_interval,
                )
                if args.verbose:
                    print(f"Run completed after polling")
            else:
                response = self.client.get_run_status(args.run_id)

            self._print_output(response, as_json=args.json, verbose=args.verbose)
            return 0

        except AgenticAPIError as e:
            print(f"Error: {e.message}", file=sys.stderr)
            if args.verbose and e.status_code:
                print(f"Status Code: {e.status_code}", file=sys.stderr)
            return 1

    def _handle_config(self, args: argparse.Namespace) -> int:
        """
        Handle the config command.

        Args:
            args: Parsed arguments

        Returns:
            Exit code (0 for success, 1 for error)
        """
        if args.json:
            config_data = {
                "api_key": f"{self.config._api_key[:8]}..." if self.config._api_key else "Not set",
                "app_id": self.config._app_id or "Not set",
                "env_name": self.config._env_name,
                "base_url": self.config._base_url,
                "timeout": self.config._timeout,
            }
            print(json.dumps(config_data, indent=2))
        else:
            print("Current Configuration:")
            print(f"  {self.config}")

        return 0

    def run(self, argv: Optional[list[str]] = None) -> int:
        """
        Run the CLI application.

        Args:
            argv: Command-line arguments (uses sys.argv if None)

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            args = self.parser.parse_args(argv)

            # Load configuration
            self.config = self._load_config(args)

            # Handle config command separately (no client needed)
            if args.command == "config":
                return self._handle_config(args)

            # Validate configuration for other commands
            try:
                self.config.validate()
            except AgenticAPIError as e:
                print(f"Configuration Error: {e.message}", file=sys.stderr)
                print("\nPlease set the required environment variables or use command-line options.", file=sys.stderr)
                return 1

            # Create API client
            self.client = AgenticAPIClient(self.config)

            # Route to command handler
            if args.command == "execute":
                return self._handle_execute(args)
            elif args.command == "status":
                return self._handle_status(args)
            else:
                print(f"Unknown command: {args.command}", file=sys.stderr)
                return 1

        except KeyboardInterrupt:
            print("\nInterrupted by user", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            if hasattr(args, "verbose") and args.verbose:
                import traceback

                traceback.print_exc()
            return 1
        finally:
            if self.client:
                self.client.close()


def main() -> NoReturn:
    """
    Main entry point for the CLI.

    This function is called when the agentic-api-cli command is executed.
    """
    cli = CLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
