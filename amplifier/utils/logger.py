"""Simple logger wrapper for amplifier utilities."""

import os

from amplifier.ccsdk_toolkit.logger import LogFormat
from amplifier.ccsdk_toolkit.logger import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import create_logger as create_toolkit_logger


def get_logger(name: str) -> ToolkitLogger:
    """Get a logger instance for the given name.

    Automatically uses JSON format when AMPLIFIER_WEB_UI environment variable is set.

    Args:
        name: Logger name (typically __name__)

    Returns:
        ToolkitLogger instance
    """
    # Use JSON format for web UI, plain for CLI
    log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
    return create_toolkit_logger(name=name, format=log_format)
