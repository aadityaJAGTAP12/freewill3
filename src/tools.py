"""LangChain Tool implementations for the agent.

Implements exactly 4 tools:
- read_file(path: str) → reads and returns file contents
- write_file(path: str, content: str) → writes content to file
- shell_exec(command: str) → runs a shell command, returns output
- web_request(url: str) → makes HTTP GET request, returns response text
"""

from __future__ import annotations

import os
import subprocess
import traceback
from pathlib import Path

import requests
from langchain_core.tools import tool


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@tool
def read_file(path: str) -> str:
    """Read and return the contents of a file at the given path.

    Handles both absolute paths and paths relative to the current working
    directory. Returns a descriptive error message if the file does not
    exist or cannot be read.
    """
    try:
        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            return f"Error: File not found: {resolved}"
        if not resolved.is_file():
            return f"Error: Not a file: {resolved} (is a directory)"
        content = resolved.read_text(encoding="utf-8", errors="replace")
        return content
    except PermissionError:
        return f"Error: Permission denied reading: {path}"
    except Exception as exc:  # noqa: BLE001
        return f"Error reading {path}: {exc}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file at the given path.

    Creates parent directories if they do not exist. Overwrites the
    file if it already exists. Returns a success or error message.
    """
    try:
        resolved = Path(path).expanduser().resolve()
        # Create parent directories if needed
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} bytes to {resolved}"
    except PermissionError:
        return f"Error: Permission denied writing to: {path}"
    except IsADirectoryError:
        return f"Error: {path} is a directory, cannot write"
    except Exception as exc:  # noqa: BLE001
        return f"Error writing to {path}: {exc}"


@tool
def shell_exec(command: str) -> str:
    """Run a shell command and return its stdout and stderr output.

    The command is executed in a subprocess with a 30-second timeout.
    Returns both stdout and stderr combined.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.stderr:
            if output:
                output += "\n--- stderr ---\n"
            output += result.stderr
        if result.returncode != 0:
            output += f"\n(exit code: {result.returncode})"
        return output if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except FileNotFoundError:
        return f"Error: Command not found: {command.split()[0]}"
    except Exception as exc:  # noqa: BLE001
        return f"Error executing command: {exc}"


@tool
def web_request(url: str) -> str:
    """Make an HTTP GET request to the given URL and return the response text.

    Includes the HTTP status code in the response. On failure returns
    a descriptive error message.
    """
    try:
        response = requests.get(url, timeout=15)
        text = response.text[:10_000]  # limit response size
        return f"Status: {response.status_code}\n\n{text}"
    except requests.Timeout:
        return f"Error: Request to {url} timed out after 15 seconds"
    except requests.ConnectionError:
        return f"Error: Could not connect to {url}"
    except requests.RequestException as exc:
        return f"Error requesting {url}: {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"Error requesting {url}: {exc}"
