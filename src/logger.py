"""Shared logging helpers and project-specific exceptions."""

from enum import Enum


class LogType(Enum):
    """Severity levels used by the terminal logger."""

    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


def log_message(message: str, log_type: LogType = LogType.INFO) -> None:
    """Print a colored log message with a severity prefix."""
    colors = {
        LogType.INFO: "\033[94m",  # Blue
        LogType.SUCCESS: "\033[92m",  # Green
        LogType.WARNING: "\033[93m",  # Yellow
        LogType.ERROR: "\033[91m",  # Red
    }
    reset = "\033[0m"
    print(f"{colors[log_type]}[{log_type.value}] {message}{reset}")
