"""
Command-line interface for Kore.ai Agentic App Platform.

Provides CLI commands for executing runs and checking status.
"""

import argparse
import getpass
import json
import sys
from typing import NoReturn, Optional

from agentic_api_cli import __version__
from agentic_api_cli.client import AgenticAPIClient
from agentic_api_cli.config import Config
from agentic_api_cli.exceptions import AgenticAPIError
from agentic_api_cli.logging_config import setup_logging, get_logger


class HelpOnErrorArgumentParser(argparse.ArgumentParser):
    """
    Custom ArgumentParser that shows help instead of just an error message
    when unrecognized arguments are encountered.
    """

    def error(self, message: str) -> NoReturn:
        """
        Override error to show help for unrecognized arguments.

        Args:
            message: Error message from argparse
        """
        if "unrecognized arguments" in message:
            # Check if this is a profile subcommand to show more specific help
            if sys.argv and len(sys.argv) >= 3 and sys.argv[1] == "profile":
                subcommand = sys.argv[2]
                if subcommand in ["add", "list", "delete", "set-default"]:
                    # Create a temporary parser to show help for the specific subcommand
                    try:
                        # Try to parse up to the subcommand to get its help
                        self.parse_args([sys.argv[1], subcommand, "--help"])
                    except SystemExit:
                        # --help will cause SystemExit, which is expected
                        raise

            # Default: show main help
            self.print_help(sys.stderr)
            sys.stderr.write(f"\nError: {message}\n")
            sys.exit(2)
        elif "invalid choice" in message:
            self.print_help(sys.stderr)
            sys.stderr.write(f"\nError: {message}\n")
            sys.exit(2)
        else:
            # For other errors, use default behavior
            super().error(message)


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
        # Create parent parser with common options
        parent_parser = argparse.ArgumentParser(add_help=False)
        parent_parser.add_argument(
            "--api-key",
            help="API key (overrides KOREAI_API_KEY env var)",
            metavar="KEY",
        )
        parent_parser.add_argument(
            "--app-id",
            help="Application ID (overrides KOREAI_APP_ID env var)",
            metavar="ID",
        )
        parent_parser.add_argument(
            "--env-name",
            help="Environment name (overrides KOREAI_ENV_NAME env var)",
            metavar="NAME",
        )
        parent_parser.add_argument(
            "--base-url",
            help="Base URL for API (overrides KOREAI_BASE_URL env var)",
            metavar="URL",
        )
        parent_parser.add_argument(
            "--timeout",
            type=int,
            help="Request timeout in seconds (overrides KOREAI_TIMEOUT env var)",
            metavar="SECONDS",
        )
        parent_parser.add_argument(
            "--env-file",
            help="Path to .env file for configuration",
            metavar="FILE",
        )
        parent_parser.add_argument(
            "--profile",
            help="Profile name to use for configuration",
            metavar="NAME",
        )
        parent_parser.add_argument(
            "--json",
            action="store_true",
            help="Output in JSON format",
        )
        parent_parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Verbose output (enables DEBUG logging and shows details)",
        )
        parent_parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="WARNING",
            help="Set logging level (default: WARNING, --verbose sets DEBUG)",
            metavar="LEVEL",
        )
        parent_parser.add_argument(
            "--log-file",
            help="Write logs to file (with automatic rotation at 10MB)",
            metavar="FILE",
        )

        # Main parser (use custom parser for better error messages)
        parser = HelpOnErrorArgumentParser(
            prog="agentic-api-cli",
            description="Command-line interface for Kore.ai Agentic App Platform",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Profile management
  agentic-api-cli profile add                    # Add profile interactively
  agentic-api-cli profile add --name prod --api-key kg-... --app-id aa-...
  agentic-api-cli profile list                   # List all profiles
  agentic-api-cli profile list --show-keys       # Show full API keys
  agentic-api-cli profile set-default prod       # Set default profile
  agentic-api-cli profile delete staging         # Delete a profile

  # Execute with auto-generated session ID
  agentic-api-cli execute --query "Hello"
  agentic-api-cli execute --query "What is the weather?"

  # Execute with custom session ID
  agentic-api-cli execute --query "Test" --session-id custom-session-001

  # Execute with profiles
  agentic-api-cli --profile prod execute --query "Hello"

  # Execute with options
  agentic-api-cli execute --query "Explain AI" --stream tokens --debug --debug-mode thoughts

  # Use different environment
  agentic-api-cli execute --env-name stage --query "Test"

  # Interactive chat
  agentic-api-cli chat                           # Start chat with auto-generated session
  agentic-api-cli chat --session-id my-session   # Start chat with specific session
  agentic-api-cli chat --stream tokens --debug   # Chat with streaming and debug

  # Check run status
  agentic-api-cli status --run-id run-xyz-789

  # Show configuration
  agentic-api-cli config

Configuration Precedence (highest to lowest):
  1. Command-line arguments (--api-key, --app-id, etc.)
  2. Environment variables (KOREAI_API_KEY, KOREAI_APP_ID, etc.)
  3. Profile values (from --profile or default profile)
  4. Built-in defaults

Environment Variables:
  KOREAI_API_KEY       API key for authentication (required if no profile)
  KOREAI_APP_ID        Application ID (required if no profile)
  KOREAI_ENV_NAME      Environment name (default: production)
  KOREAI_BASE_URL      Base URL for API (default: https://agent-platform.kore.ai/api/v2)
  KOREAI_TIMEOUT       Request timeout in seconds (default: 30)
            """,
        )

        parser.add_argument(
            "--version", action="version", version=f"%(prog)s {__version__}"
        )

        # Subcommands (command comes FIRST)
        subparsers = parser.add_subparsers(
            dest="command",
            help="Available commands",
            required=True,
            metavar="<command>",
        )

        # Execute command
        execute_parser = subparsers.add_parser(
            "execute",
            parents=[parent_parser],
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
            required=False,
            help="Session identifier (auto-generated if not provided)",
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
            "--debug-mode",
            choices=["all", "function-call", "thoughts"],
            help="Debug mode level (requires --debug). Note: API currently validates 'thoughts'; others may be rejected",
            metavar="MODE",
        )
        execute_parser.add_argument(
            "--metadata",
            help="JSON string of metadata key-value pairs",
            metavar="JSON",
        )

        # Status command
        status_parser = subparsers.add_parser(
            "status",
            parents=[parent_parser],
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
            parents=[parent_parser],
            help="Show configuration",
            description="Display current configuration (with sensitive data masked)",
        )

        # Chat command
        chat_parser = subparsers.add_parser(
            "chat",
            parents=[parent_parser],
            help="Start interactive chat session",
            description="Start an interactive chat session with the agentic app",
        )
        chat_parser.add_argument(
            "--session-id",
            "-s",
            help="Session identifier (auto-generated if not provided)",
            metavar="ID",
        )
        chat_parser.add_argument(
            "--user-id",
            "-u",
            help="User identifier (optional, defaults to session-id)",
            metavar="ID",
        )
        chat_parser.add_argument(
            "--stream",
            choices=["tokens", "messages", "custom"],
            help="Enable streaming with specified mode",
            metavar="MODE",
        )
        chat_parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode",
        )
        chat_parser.add_argument(
            "--debug-mode",
            choices=["all", "function-call", "thoughts"],
            help="Debug mode level (requires --debug)",
            metavar="MODE",
        )
        chat_parser.add_argument(
            "--metadata",
            help="JSON string of metadata key-value pairs",
            metavar="JSON",
        )

        # Profile command (with its own subcommands)
        profile_parser = subparsers.add_parser(
            "profile",
            help="Manage configuration profiles",
            description="Add, list, delete, and manage configuration profiles",
        )

        profile_subparsers = profile_parser.add_subparsers(
            dest="profile_command",
            help="Profile operations",
            required=False,  # Allow missing subcommand to show help
            parser_class=HelpOnErrorArgumentParser,
        )

        # profile add
        add_profile_parser = profile_subparsers.add_parser(
            "add",
            help="Add a new profile",
            description="Add or update a configuration profile",
        )
        add_profile_parser.add_argument(
            "--name",
            help="Profile name",
        )
        add_profile_parser.add_argument(
            "--api-key",
            help="API key",
        )
        add_profile_parser.add_argument(
            "--app-id",
            help="App ID",
        )
        add_profile_parser.add_argument(
            "--env-name",
            help="Environment name (default: profile name)",
        )
        add_profile_parser.add_argument(
            "--base-url",
            help="Base URL (default: https://agent-platform.kore.ai/api/v2)",
        )
        add_profile_parser.add_argument(
            "--timeout",
            type=int,
            help="Timeout in seconds (default: 30)",
        )

        # profile list
        list_profile_parser = profile_subparsers.add_parser(
            "list",
            help="List all profiles",
            description="List all configuration profiles",
        )
        list_profile_parser.add_argument(
            "--show-keys",
            action="store_true",
            help="Show full API keys (default: masked)",
        )

        # profile delete
        delete_profile_parser = profile_subparsers.add_parser(
            "delete",
            help="Delete a profile",
            description="Delete a configuration profile",
        )
        delete_profile_parser.add_argument(
            "name",
            nargs='?',  # Make optional to allow showing help
            help="Profile name to delete",
        )

        # profile set-default
        set_default_parser = profile_subparsers.add_parser(
            "set-default",
            help="Set default profile",
            description="Set the default profile to use when --profile is not specified",
        )
        set_default_parser.add_argument(
            "name",
            nargs='?',  # Make optional to allow showing help
            help="Profile name to set as default",
        )

        return parser

    def _load_config(self, args: argparse.Namespace) -> Config:
        """
        Load configuration from environment and command-line arguments.

        Configuration precedence (highest to lowest):
        1. Command-line arguments
        2. Environment variables
        3. Profile values
        4. Built-in defaults

        Args:
            args: Parsed command-line arguments

        Returns:
            Configured Config instance
        """
        # Determine profile to use (explicit --profile or default)
        profile_name = None
        if hasattr(args, 'profile') and args.profile:
            profile_name = args.profile
        else:
            # Check for default profile
            from agentic_api_cli.profiles import ProfileManager
            manager = ProfileManager()
            profile_name = manager.get_default_profile()

        # Create config with profile
        config = Config(env_file=getattr(args, 'env_file', None), profile=profile_name)

        # Override with command-line arguments if provided (highest precedence)
        if hasattr(args, 'api_key') and args.api_key:
            config.api_key = args.api_key
        if hasattr(args, 'app_id') and args.app_id:
            config.app_id = args.app_id
        if hasattr(args, 'env_name') and args.env_name:
            config.env_name = args.env_name
        if hasattr(args, 'base_url') and args.base_url:
            config.base_url = args.base_url
        if hasattr(args, 'timeout') and args.timeout:
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

            # Show debug information if present
            if "debug" in data and not as_json:
                debug_info = data["debug"]
                if verbose:
                    print(f"\nDebug Information:\n{json.dumps(debug_info, indent=2)}")
                else:
                    # Show summary in normal mode
                    if isinstance(debug_info, dict):
                        print("\n[Debug] Debug information available (use --verbose to see details)")

            # Verbose mode shows full response
            if verbose:
                print(f"\nFull Response:\n{json.dumps(data, indent=2)}")

    def _generate_simple_session_id(self) -> str:
        """
        Generate unique session ID for chat using UUID.

        Returns:
            Session ID string with format: chat-{uuid4}

        Example:
            'chat-a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5g6h7'
        """
        import uuid
        return f"chat-{uuid.uuid4()}"

    def _print_chat_banner(self, session_id: str, env_name: str) -> None:
        """
        Print welcome banner for chat session.

        Args:
            session_id: Session identifier
            env_name: Environment name
        """
        print("╔═══════════════════════════════════════╗")
        print("║   Agentic API Chat Session Started    ║")
        print("╚═══════════════════════════════════════╝")
        print(f"Session ID: {session_id}")
        print(f"Environment: {env_name}")
        print()
        print("Type your message or 'exit' to quit. Type '#help' for commands.")

    def _print_chat_response(self, data: dict, verbose: bool = False) -> None:
        """
        Print agent response in chat format.

        Args:
            data: Response data from API
            verbose: Include verbose details
        """
        print("\nAgent: ", end="")

        # Extract text content from output array
        if "output" in data:
            for item in data["output"]:
                if item.get("type") == "text":
                    print(item.get("content", ""))

        # Show debug information if present and verbose
        if "debug" in data and verbose:
            debug_info = data["debug"]
            print(f"\n[Debug] {json.dumps(debug_info, indent=2)}")

    def _handle_chat_special_command(
        self,
        user_input: str,
        args: argparse.Namespace,
        session_id: str
    ) -> tuple[bool, str | None]:
        """
        Handle special commands (starting with #) in chat mode.

        Args:
            user_input: The user input string (already stripped)
            args: Parsed command-line arguments (mutable, modified in place)
            session_id: Current session ID

        Returns:
            Tuple of (should_continue, new_session_id):
                - should_continue: True to continue chat loop, False to exit
                - new_session_id: New session ID if command changed it, None otherwise
        """
        logger = get_logger()

        # Split command and arguments
        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()  # Case-insensitive
        command_args = parts[1].strip() if len(parts) > 1 else ""

        # Command dispatch table with aliases
        command_handlers = {
            '#help': self._chat_cmd_help,
            '#new': self._chat_cmd_new,
            '#newsession': self._chat_cmd_new,  # Alias
            '#info': self._chat_cmd_info,
            '#session': self._chat_cmd_info,  # Alias
            '#clear': self._chat_cmd_clear,
            '#debug': self._chat_cmd_debug,
            '#stream': self._chat_cmd_stream,
            '#history': self._chat_cmd_history,
        }

        if command in command_handlers:
            logger.debug(f"Handling special command: {command}")
            return command_handlers[command](command_args, args, session_id)
        else:
            # Unknown command - show error and continue
            print(f"Unknown command: {command}. Type #help for available commands.")
            logger.warning(f"Unknown special command attempted: {command}")
            return (True, None)

    def _chat_cmd_help(
        self, command_args: str, args: argparse.Namespace, session_id: str
    ) -> tuple[bool, str | None]:
        """Display help for special commands."""
        print("\nAvailable Commands:")
        print("  #help              - Show this help message")
        print("  #new               - Start a new session")
        print("  #info              - Show current session information")
        print("  #clear             - Clear the terminal screen")
        print("  #debug on|off      - Toggle debug mode")
        print("  #stream on|off|tokens|messages|custom - Toggle streaming")
        print("\nTo exit chat, type: exit, quit, or q")
        print()
        return (True, None)

    def _chat_cmd_debug(
        self, command_args: str, args: argparse.Namespace, session_id: str
    ) -> tuple[bool, str | None]:
        """Handle #debug on|off command."""
        logger = get_logger()

        if not command_args:
            # Show current state
            state = "enabled" if getattr(args, 'debug', False) else "disabled"
            print(f"Debug mode is currently {state}")
            return (True, None)

        arg = command_args.lower()
        if arg == "on":
            args.debug = True
            args.debug_mode = None  # Reset to default
            print("Debug mode enabled")
            logger.info("Debug mode enabled via chat command")
        elif arg == "off":
            args.debug = False
            args.debug_mode = None
            print("Debug mode disabled")
            logger.info("Debug mode disabled via chat command")
        else:
            print(f"Invalid argument: '{command_args}'. Use '#debug on' or '#debug off'")

        return (True, None)

    def _chat_cmd_stream(
        self, command_args: str, args: argparse.Namespace, session_id: str
    ) -> tuple[bool, str | None]:
        """Handle #stream on|off|tokens|messages|custom command."""
        logger = get_logger()

        if not command_args:
            # Show current state
            current = getattr(args, 'stream', None)
            if current:
                print(f"Streaming is enabled: {current}")
            else:
                print("Streaming is disabled")
            return (True, None)

        arg = command_args.lower()
        valid_modes = ["tokens", "messages", "custom"]

        if arg == "off":
            args.stream = None
            print("Streaming disabled")
            logger.info("Streaming disabled via chat command")
        elif arg == "on":
            args.stream = "tokens"  # Default mode
            print("Streaming enabled (mode: tokens)")
            logger.info("Streaming enabled with default mode: tokens")
        elif arg in valid_modes:
            args.stream = arg
            print(f"Streaming enabled (mode: {arg})")
            logger.info(f"Streaming mode set to: {arg}")
        else:
            print(f"Invalid argument: '{command_args}'")
            print("Use: #stream on|off|tokens|messages|custom")

        return (True, None)

    def _chat_cmd_new(
        self, command_args: str, args: argparse.Namespace, session_id: str
    ) -> tuple[bool, str | None]:
        """Start a new session with new session ID."""
        logger = get_logger()

        # Generate new session ID
        new_session_id = self._generate_simple_session_id()

        # Display banner
        print("\n╔═══════════════════════════════════════╗")
        print("║         New Session Started           ║")
        print("╚═══════════════════════════════════════╝")
        print(f"Previous Session: {session_id}")
        print(f"New Session: {new_session_id}")
        print()

        logger.info(f"New session started. Old: {session_id}, New: {new_session_id}")

        # Return new session ID
        return (True, new_session_id)

    def _chat_cmd_info(
        self, command_args: str, args: argparse.Namespace, session_id: str
    ) -> tuple[bool, str | None]:
        """Display current session information."""
        logger = get_logger()

        print("\nSession Information:")
        print(f"  Session ID: {session_id}")
        print(f"  Environment: {self.config.env_name}")
        print(f"  App ID: {self.config.app_id}")

        # Show optional settings
        user_id = getattr(args, 'user_id', None)
        if user_id:
            print(f"  User ID: {user_id}")

        # Show debug state
        debug_enabled = getattr(args, 'debug', False)
        debug_mode = getattr(args, 'debug_mode', None)
        if debug_enabled:
            if debug_mode:
                print(f"  Debug: enabled ({debug_mode})")
            else:
                print(f"  Debug: enabled")
        else:
            print(f"  Debug: disabled")

        # Show streaming state
        stream = getattr(args, 'stream', None)
        if stream:
            print(f"  Streaming: {stream}")
        else:
            print(f"  Streaming: disabled")

        print()
        logger.debug(f"Displayed session info for session: {session_id}")
        return (True, None)

    def _chat_cmd_clear(
        self, command_args: str, args: argparse.Namespace, session_id: str
    ) -> tuple[bool, str | None]:
        """Clear the terminal screen."""
        import os

        # Cross-platform clear screen
        os.system('cls' if os.name == 'nt' else 'clear')

        # Re-display banner after clearing
        self._print_chat_banner(session_id, self.config.env_name)

        return (True, None)

    def _chat_cmd_history(
        self, command_args: str, args: argparse.Namespace, session_id: str
    ) -> tuple[bool, str | None]:
        """Show conversation history (future feature)."""
        print("History feature not yet implemented.")
        print("Future: This will show your conversation history.")
        return (True, None)

    def _handle_execute(self, args: argparse.Namespace) -> int:
        """
        Handle the execute command.

        Args:
            args: Parsed arguments

        Returns:
            Exit code (0 for success, 1 for error)
        """
        logger = get_logger()
        try:
            # Parse metadata if provided
            metadata = None
            if args.metadata:
                try:
                    metadata = json.loads(args.metadata)
                    logger.debug(f"Parsed metadata: {metadata}")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in --metadata: {e}")
                    print(f"Error: Invalid JSON in --metadata: {e}", file=sys.stderr)
                    return 1

            # Validate debug options
            debug_mode = None
            if hasattr(args, 'debug_mode') and args.debug_mode:
                if not args.debug:
                    logger.error("--debug-mode requires --debug to be set")
                    print("Error: --debug-mode requires --debug flag to be set", file=sys.stderr)
                    return 1
                debug_mode = args.debug_mode

            # Generate session ID if not provided
            session_id = args.session_id if args.session_id else self._generate_simple_session_id()

            logger.info(f"Executing run with session: {session_id}")
            if args.verbose:
                print(f"Executing run with session: {session_id}")
                if hasattr(args, 'user_id') and args.user_id:
                    print(f"User ID: {args.user_id}")
                print(f"Query: {args.query}")

            # Execute the run with actual API format
            response = self.client.execute_run(
                query=args.query,
                session_identity=session_id,
                user_reference=getattr(args, 'user_id', None),
                stream_enabled=bool(args.stream),
                stream_mode=args.stream if args.stream else None,
                debug_enabled=args.debug if hasattr(args, 'debug') else False,
                debug_mode=debug_mode,
                metadata=metadata,
            )

            logger.info("Run execution completed successfully")
            self._print_output(response, as_json=args.json, verbose=args.verbose)
            return 0

        except AgenticAPIError as e:
            logger.error(f"API error during execute: {e.message}", exc_info=True)
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
        logger = get_logger()
        try:
            logger.info(f"Checking status for run: {args.run_id}")
            if args.verbose:
                print(f"Checking status for run: {args.run_id}")

            if args.wait:
                logger.debug(f"Polling for run status (max_attempts={args.max_attempts}, interval={args.poll_interval})")
                response = self.client.poll_run_status(
                    run_id=args.run_id,
                    max_attempts=args.max_attempts,
                    interval=args.poll_interval,
                )
                logger.info("Run completed after polling")
                if args.verbose:
                    print(f"Run completed after polling")
            else:
                response = self.client.get_run_status(args.run_id)

            logger.info("Status check completed successfully")
            self._print_output(response, as_json=args.json, verbose=args.verbose)
            return 0

        except AgenticAPIError as e:
            logger.error(f"API error during status check: {e.message}", exc_info=True)
            print(f"Error: {e.message}", file=sys.stderr)
            if args.verbose and e.status_code:
                print(f"Status Code: {e.status_code}", file=sys.stderr)
            return 1

    def _handle_chat(self, args: argparse.Namespace) -> int:
        """
        Handle the chat command - interactive REPL-style chat.

        Args:
            args: Parsed arguments

        Returns:
            Exit code (0 for success, 130 for interrupt)
        """
        logger = get_logger()

        # Generate or use provided session ID
        session_id = (
            args.session_id
            if hasattr(args, 'session_id') and args.session_id
            else self._generate_simple_session_id()
        )

        # Parse metadata if provided
        metadata = None
        if hasattr(args, 'metadata') and args.metadata:
            try:
                metadata = json.loads(args.metadata)
                logger.debug(f"Parsed metadata: {metadata}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in --metadata: {e}")
                print(f"Error: Invalid JSON in --metadata: {e}", file=sys.stderr)
                return 1

        # Validate debug options (same as execute command)
        debug_mode = None
        if hasattr(args, 'debug_mode') and args.debug_mode:
            if not args.debug:
                logger.error("--debug-mode requires --debug to be set")
                print("Error: --debug-mode requires --debug flag to be set", file=sys.stderr)
                return 1
            debug_mode = args.debug_mode

        # Display welcome banner
        self._print_chat_banner(session_id, self.config.env_name)

        logger.info(f"Starting chat session: {session_id}")

        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()

                # Skip empty input
                if not user_input:
                    continue

                # Check for special commands (starts with #)
                if user_input.startswith('#'):
                    should_continue, new_session = self._handle_chat_special_command(
                        user_input, args, session_id
                    )
                    # Update session ID if command changed it
                    if new_session:
                        session_id = new_session
                    # Exit loop if command requested it
                    if not should_continue:
                        return 0
                    # Continue to next iteration (don't execute as query)
                    continue

                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\nGoodbye! Session ended.")
                    logger.info("Chat session ended by user")
                    return 0

                # Execute the query
                logger.debug(f"Sending query: {user_input}")
                response = self.client.execute_run(
                    query=user_input,
                    session_identity=session_id,
                    user_reference=getattr(args, 'user_id', None),
                    stream_enabled=bool(args.stream) if hasattr(args, 'stream') and args.stream else False,
                    stream_mode=args.stream if hasattr(args, 'stream') and args.stream else None,
                    debug_enabled=args.debug if hasattr(args, 'debug') else False,
                    debug_mode=debug_mode,
                    metadata=metadata,
                )

                # Display response
                self._print_chat_response(
                    response,
                    verbose=args.verbose if hasattr(args, 'verbose') else False
                )

            except EOFError:
                # Ctrl+D pressed
                print("\n\nGoodbye! Session ended.")
                logger.info("Chat session ended by EOF (Ctrl+D)")
                return 0

            except KeyboardInterrupt:
                # Ctrl+C - let global handler print message
                logger.info("Chat session interrupted by user (Ctrl+C)")
                return 130

            except AgenticAPIError as e:
                # API errors - show error but continue chat
                logger.error(f"API error during chat: {e.message}", exc_info=True)
                print(f"\nError: {e.message}", file=sys.stderr)
                if hasattr(args, 'verbose') and args.verbose and e.status_code:
                    print(f"Status Code: {e.status_code}", file=sys.stderr)
                # Continue loop to allow retry
                continue

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

    def _handle_profile(self, args: argparse.Namespace) -> int:
        """
        Handle profile subcommands.

        Args:
            args: Parsed arguments

        Returns:
            Exit code (0 for success, 1 for error)
        """
        from agentic_api_cli.profiles import ProfileManager

        manager = ProfileManager()

        # Show help if no subcommand provided
        if not args.profile_command:
            # Get the profile parser to print help
            self.parser.parse_args(['profile', '--help'])
            return 0

        try:
            if args.profile_command == "add":
                return self._handle_profile_add(args, manager)
            elif args.profile_command == "list":
                return self._handle_profile_list(args, manager)
            elif args.profile_command == "delete":
                return self._handle_profile_delete(args, manager)
            elif args.profile_command == "set-default":
                return self._handle_profile_set_default(args, manager)
            else:
                print(f"Unknown profile command: {args.profile_command}", file=sys.stderr)
                return 1
        except AgenticAPIError as e:
            print(f"Error: {e.message}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _handle_profile_add(self, args: argparse.Namespace, manager) -> int:
        """
        Handle profile add command.

        Args:
            args: Parsed arguments
            manager: ProfileManager instance

        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Interactive mode if name not provided
        if not args.name:
            print("Create a new profile")
            print()
            name = input("Profile name: ").strip()
            if not name:
                print("Error: Profile name cannot be empty", file=sys.stderr)
                return 1
            api_key = getpass.getpass("API Key: ").strip()
            app_id = input("App ID: ").strip()
            env_name = input(f"Environment name [{name}]: ").strip() or name
            base_url = input("Base URL [https://agent-platform.kore.ai/api/v2]: ").strip() or "https://agent-platform.kore.ai/api/v2"
            timeout_str = input("Timeout [30]: ").strip() or "30"
            try:
                timeout = int(timeout_str)
            except ValueError:
                print(f"Error: Invalid timeout value: {timeout_str}", file=sys.stderr)
                return 1
        else:
            # Use command-line arguments, prompting for missing required fields
            name = args.name.strip()
            if not name:
                print("Error: Profile name cannot be empty", file=sys.stderr)
                return 1

            api_key = args.api_key
            if not api_key:
                api_key = getpass.getpass("API Key: ").strip()

            app_id = args.app_id
            if not app_id:
                app_id = input("App ID: ").strip()

            env_name = args.env_name or name
            base_url = args.base_url or "https://agent-platform.kore.ai/api/v2"
            timeout = args.timeout or 30

        # Check if overwriting existing profile
        profiles = manager.load_profiles()
        if name in profiles:
            response = input(f"Profile '{name}' already exists. Overwrite? [y/N]: ").strip().lower()
            if response not in ['y', 'yes']:
                print("Cancelled")
                return 0

        manager.add_profile(name, api_key, app_id, env_name, base_url, timeout)
        print(f"Profile '{name}' saved successfully!")
        return 0

    def _handle_profile_list(self, args: argparse.Namespace, manager) -> int:
        """
        Handle profile list command.

        Args:
            args: Parsed arguments
            manager: ProfileManager instance

        Returns:
            Exit code (0 for success, 1 for error)
        """
        profiles = manager.list_profiles()

        if not profiles:
            print("No profiles configured")
            print("\nTo add a profile, run: agentic-api-cli profile add")
            return 0

        default_profile = manager.get_default_profile()

        print(f"Available profiles ({len(profiles)}):")
        print()

        for profile_name in profiles:
            profile = manager.get_profile_display(profile_name, show_keys=args.show_keys)
            default_marker = " (default)" if profile_name == default_profile else ""
            print(f"  {profile_name}{default_marker}")
            print(f"    API Key:     {profile['api_key']}")
            print(f"    App ID:      {profile['app_id']}")
            print(f"    Environment: {profile['env_name']}")
            print(f"    Base URL:    {profile['base_url']}")
            print(f"    Timeout:     {profile['timeout']}s")
            print()

        return 0

    def _handle_profile_delete(self, args: argparse.Namespace, manager) -> int:
        """
        Handle profile delete command.

        Args:
            args: Parsed arguments
            manager: ProfileManager instance

        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Show help if name not provided
        if not args.name:
            self.parser.parse_args(['profile', 'delete', '--help'])
            return 0

        name = args.name

        # Confirm deletion
        response = input(f"Delete profile '{name}'? [y/N]: ").strip().lower()
        if response not in ['y', 'yes']:
            print("Cancelled")
            return 0

        manager.delete_profile(name)
        print(f"Profile '{name}' deleted successfully")

        # Warn if we deleted the default
        default_profile = manager.get_default_profile()
        if default_profile is None and manager.list_profiles():
            print("\nNote: No default profile is set. Set one with:")
            print("  agentic-api-cli profile set-default <name>")

        return 0

    def _handle_profile_set_default(self, args: argparse.Namespace, manager) -> int:
        """
        Handle profile set-default command.

        Args:
            args: Parsed arguments
            manager: ProfileManager instance

        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Show help if name not provided
        if not args.name:
            self.parser.parse_args(['profile', 'set-default', '--help'])
            return 0

        name = args.name
        manager.set_default_profile(name)
        print(f"Default profile set to '{name}'")
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

            # Set up logging based on arguments (with defaults for profile command)
            setup_logging(
                log_level=getattr(args, 'log_level', 'WARNING'),
                log_file=getattr(args, 'log_file', None),
                verbose=getattr(args, 'verbose', False),
            )
            logger = get_logger()

            # Handle profile command separately (no config/client needed)
            if args.command == "profile":
                return self._handle_profile(args)

            # Load configuration
            self.config = self._load_config(args)
            logger.debug(f"Configuration loaded for environment: {self.config.env_name}")

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
            elif args.command == "chat":
                return self._handle_chat(args)
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
