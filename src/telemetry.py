"""Telemetry Capture — records every agent tool call as a structured event.

Stores session history as a list of events matching the schema in
SAMPLE_EVENTS.md. Extracts file paths, URLs, and commands from
tool arguments using observable signals only (no agent thoughts).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class TelemetryCapture:
    """Captures and stores structured telemetry events for an agent session.

    On every tool call, creates an event with:
    - step number and ISO timestamp
    - tool name and arguments
    - extracted file_paths, urls, commands
    - last 5 tool names (for sequence detection)

    Use get_history() to retrieve the full session log.
    """

    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []
        self._step: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_tool_call(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
    ) -> dict[str, Any]:
        """Record a tool call and return the structured event.

        Parameters
        ----------
        tool_name : str
            Name of the tool that was called (e.g. "read_file").
        tool_args : dict[str, Any]
            Dictionary of arguments passed to the tool.

        Returns
        -------
        dict
            The structured telemetry event that was appended to history.
        """
        self._step += 1

        event: dict[str, Any] = {
            "step": self._step,
            "timestamp": _iso_timestamp(),
            "tool_called": tool_name,
            "tool_args": tool_args,
            "file_paths": _extract_file_paths(tool_name, tool_args),
            "urls": _extract_urls(tool_name, tool_args),
            "commands": _extract_commands(tool_name, tool_args),
            "previous_tools": self._last_n_tool_names(5),
        }

        self._history.append(event)
        return event

    def get_history(self) -> list[dict[str, Any]]:
        """Return the full session history of telemetry events.

        Returns a shallow copy so callers cannot mutate internal state.
        """
        return list(self._history)

    def clear(self) -> None:
        """Reset the session (step counter and history)."""
        self._history.clear()
        self._step = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _last_n_tool_names(self, n: int) -> list[str]:
        """Return the last *n* tool names from history (most recent last)."""
        return [e["tool_called"] for e in self._history[-n:]]


# ---------------------------------------------------------------------------
# Module-level helpers (observable signal extraction)
# ---------------------------------------------------------------------------


def _iso_timestamp() -> str:
    """Return the current UTC time as an ISO-8601 string ending in 'Z'."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_file_paths(tool_name: str, tool_args: dict[str, Any]) -> list[str]:
    """Extract file paths from tool arguments.

    Only looks at tools that operate on files:
    - read_file  → args["path"]
    - write_file → args["path"]
    """
    if tool_name in ("read_file", "write_file") and "path" in tool_args:
        path = str(tool_args["path"])
        return [path] if path.strip() else []
    return []


def _extract_commands(tool_name: str, tool_args: dict[str, Any]) -> list[str]:
    """Extract shell commands from tool arguments.

    Only looks at shell_exec:
    - shell_exec → args["command"]
    """
    if tool_name == "shell_exec" and "command" in tool_args:
        cmd = str(tool_args["command"])
        return [cmd] if cmd.strip() else []
    return []


def _extract_urls(tool_name: str, tool_args: dict[str, Any]) -> list[str]:
    """Extract URLs from tool arguments.

    Only looks at web_request:
    - web_request → args["url"]
    """
    if tool_name == "web_request" and "url" in tool_args:
        url = str(tool_args["url"])
        return [url] if url.strip() else []
    return []
