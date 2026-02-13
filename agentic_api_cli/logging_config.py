"""
Logging configuration for Agentic API CLI.

Provides centralized logging setup with console and file output support.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


# Define log format
SIMPLE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Logger name
LOGGER_NAME = "agentic_api_cli"


def mask_sensitive_data(text: str) -> str:
    """
    Mask sensitive data in log messages.

    Args:
        text: Text that may contain sensitive data

    Returns:
        Text with sensitive data masked

    Examples:
        >>> mask_sensitive_data("API Key: kg-12345678-abcd")
        "API Key: kg-1234****"
        >>> mask_sensitive_data("app_id: aa-12345678-abcd-efgh")
        "app_id: aa-1234****"
    """
    import re

    # Mask API keys (format: kg-...)
    text = re.sub(
        r'(kg-[a-f0-9]{8})-[a-f0-9-]+',
        r'\1****',
        text,
        flags=re.IGNORECASE
    )

    # Mask app IDs (format: aa-...)
    text = re.sub(
        r'(aa-[a-f0-9]{8})-[a-f0-9-]+',
        r'\1****',
        text,
        flags=re.IGNORECASE
    )

    # Mask any quoted strings that look like keys/tokens
    text = re.sub(
        r'(["\'])[a-zA-Z0-9_-]{20,}(["\'])',
        r'\1****\2',
        text
    )

    return text


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that masks sensitive data in log records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record by masking sensitive data.

        Args:
            record: Log record to filter

        Returns:
            Always returns True (doesn't block records)
        """
        # Mask message
        if hasattr(record, 'msg'):
            record.msg = mask_sensitive_data(str(record.msg))

        # Mask arguments
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    mask_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: mask_sensitive_data(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }

        return True


def setup_logging(
    log_level: str = "WARNING",
    log_file: Optional[str] = None,
    verbose: bool = False,
) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional). If provided, logs to file with rotation.
        verbose: If True, automatically sets log level to DEBUG

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging(log_level="INFO", log_file="app.log")
        >>> logger.info("Application started")
    """
    # Override log level if verbose mode
    if verbose:
        log_level = "DEBUG"

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.WARNING)

    # Get or create logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(SIMPLE_FORMAT, datefmt=DATE_FORMAT)

    # Console handler (always enabled, logs to stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(console_handler)

    # File handler (optional, with rotation)
    if log_file:
        try:
            # Create parent directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Rotating file handler: 10MB per file, keep 3 backups
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=3,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(SensitiveDataFilter())
            logger.addHandler(file_handler)

            logger.info(f"Logging to file: {log_file}")
        except Exception as e:
            logger.error(f"Failed to set up file logging: {e}")

    # Don't propagate to root logger
    logger.propagate = False

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Optional sub-logger name (e.g., 'client', 'config')

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger('client')
        >>> logger.debug("Making API request")
    """
    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return logging.getLogger(LOGGER_NAME)


def log_api_request(url: str, method: str, body: Optional[dict] = None) -> None:
    """
    Log an API request (with sensitive data masked).

    Args:
        url: Request URL
        method: HTTP method
        body: Request body (optional)
    """
    logger = get_logger('client')
    logger.info(f"{method} request to {url}")
    if body and logger.isEnabledFor(logging.DEBUG):
        import json
        body_str = json.dumps(body, indent=2)
        logger.debug(f"Request body: {body_str}")


def log_api_response(status_code: int, response_data: Optional[dict] = None) -> None:
    """
    Log an API response (with sensitive data masked).

    Args:
        status_code: HTTP status code
        response_data: Response data (optional)
    """
    logger = get_logger('client')
    logger.info(f"Response received: {status_code}")
    if response_data and logger.isEnabledFor(logging.DEBUG):
        import json
        response_str = json.dumps(response_data, indent=2)
        logger.debug(f"Response data: {response_str}")


def log_error(message: str, exception: Optional[Exception] = None) -> None:
    """
    Log an error with optional exception details.

    Args:
        message: Error message
        exception: Exception instance (optional)
    """
    logger = get_logger()
    if exception:
        logger.error(f"{message}: {exception}", exc_info=True)
    else:
        logger.error(message)
