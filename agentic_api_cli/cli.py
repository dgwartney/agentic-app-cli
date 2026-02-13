"""
Command-line interface for Kore.ai Agentic App Platform.

This module provides the main CLI entry point for the agentic-api-cli tool.
"""

import sys
from agentic_api_cli import __version__


def main():
    """Main CLI entry point."""
    print(f"Agentic API CLI v{__version__}")
    print("Command-line interface for Kore.ai Agentic App Platform")
    print()
    print("This is a placeholder. Full CLI implementation coming soon!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
