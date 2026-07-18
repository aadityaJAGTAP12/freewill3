"""Unit tests for the Intent Compiler (src/intent_compiler.py).

Tests cover five different prompt types:
1. Read / summarization task
2. Write / file creation task
3. Shell command execution task
4. Web / network request task
5. Multi-tool task (read + write)
"""

from __future__ import annotations

from src.intent_compiler import ALWAYS_DENIED_PATHS, ALL_TOOLS, compile_intent


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def test_returns_correct_keys() -> None:
    """The returned dict must contain all expected keys."""
    policy = compile_intent("do something")
    expected_keys = {
        "original_prompt",
        "allowed_tools",
        "allowed_paths",
        "denied_tools",
        "denied_paths",
        "allowed_domains",
        "task_keywords",
    }
    assert set(policy.keys()) == expected_keys, (
        f"Expected keys {expected_keys}, got {set(policy.keys())}"
    )


# ---------------------------------------------------------------------------
# Test 1: Read / summarization task
# ---------------------------------------------------------------------------


def test_read_task() -> None:
    """'summarize files in /documents' → read_file allowed, others denied."""
    prompt = "summarize files in /documents"
    policy = compile_intent(prompt)

    assert policy["original_prompt"] == prompt
    assert policy["allowed_tools"] == ["read_file"]
    assert "write_file" in policy["denied_tools"]
    assert "shell_exec" in policy["denied_tools"]
    assert "web_request" in policy["denied_tools"]
    assert "/documents/**" in policy["allowed_paths"], (
        f"Expected /documents/** in allowed_paths, got {policy['allowed_paths']}"
    )
    # Task keywords should include summarize, file, document
    keywords = policy["task_keywords"]
    assert "summarize" in keywords or "file" in keywords or "document" in keywords, (
        f"Expected summariz/file/document keywords, got {keywords}"
    )


# ---------------------------------------------------------------------------
# Test 2: Write / file creation task
# ---------------------------------------------------------------------------


def test_write_task() -> None:
    """'write hello world to /tmp/output.txt' → write_file allowed."""
    prompt = "write hello world to /tmp/output.txt"
    policy = compile_intent(prompt)

    assert policy["original_prompt"] == prompt
    assert policy["allowed_tools"] == ["write_file"]
    assert "read_file" in policy["denied_tools"]
    assert "shell_exec" in policy["denied_tools"]
    assert "web_request" in policy["denied_tools"]
    # Path with file extension → exact match (not glob)
    assert "/tmp/output.txt" in policy["allowed_paths"], (
        f"Expected /tmp/output.txt in allowed_paths, got {policy['allowed_paths']}"
    )
    # Denied paths always include sensitive locations
    for denied in ALWAYS_DENIED_PATHS:
        assert denied in policy["denied_paths"], (
            f"Expected {denied} in denied_paths"
        )


# ---------------------------------------------------------------------------
# Test 3: Shell command task
# ---------------------------------------------------------------------------


def test_shell_task() -> None:
    """'run ls -la on the project directory' → shell_exec allowed."""
    prompt = "run ls -la on the project directory"
    policy = compile_intent(prompt)

    assert policy["original_prompt"] == prompt
    assert policy["allowed_tools"] == ["shell_exec"]
    assert "read_file" in policy["denied_tools"]
    assert "write_file" in policy["denied_tools"]
    assert "web_request" in policy["denied_tools"]
    # No explicit path in prompt → allow all
    assert "**" in policy["allowed_paths"], (
        f"Expected ** in allowed_paths when no path specified, "
        f"got {policy['allowed_paths']}"
    )
    # Denied paths always present
    assert policy["denied_paths"] == ALWAYS_DENIED_PATHS


# ---------------------------------------------------------------------------
# Test 4: Web / network request task
# ---------------------------------------------------------------------------


def test_web_task() -> None:
    """'fetch https://api.example.com/data' → web_request allowed, domain listed."""
    prompt = "fetch https://api.example.com/data"
    policy = compile_intent(prompt)

    assert policy["original_prompt"] == prompt
    assert policy["allowed_tools"] == ["web_request"]
    assert "read_file" in policy["denied_tools"]
    assert "write_file" in policy["denied_tools"]
    assert "shell_exec" in policy["denied_tools"]
    # Domain should be extracted
    assert "api.example.com" in policy["allowed_domains"], (
        f"Expected api.example.com in allowed_domains, "
        f"got {policy['allowed_domains']}"
    )
    # No explicit file path → allow all
    assert "**" in policy["allowed_paths"]


# ---------------------------------------------------------------------------
# Test 5: Multi-tool task (read + write)
# ---------------------------------------------------------------------------


def test_multi_tool_task() -> None:
    """'read the file at /etc/config and write a summary to /tmp/out.txt'
    → read_file + write_file allowed, multiple extracted paths."""
    prompt = "read the file at /etc/config and write a summary to /tmp/out.txt"
    policy = compile_intent(prompt)

    assert policy["original_prompt"] == prompt
    assert sorted(policy["allowed_tools"]) == sorted(["read_file", "write_file"])
    assert "shell_exec" in policy["denied_tools"]
    assert "web_request" in policy["denied_tools"]
    # Both paths should be present
    # /etc/config has no file extension → treated as directory → globbed
    assert "/etc/config/**" in policy["allowed_paths"], (
        f"Expected /etc/config/** in allowed_paths, got {policy['allowed_paths']}"
    )
    # /tmp/out.txt has extension → exact match
    assert "/tmp/out.txt" in policy["allowed_paths"], (
        f"Expected /tmp/out.txt in allowed_paths, got {policy['allowed_paths']}"
    )
    # Denied paths always present
    assert policy["denied_paths"] == ALWAYS_DENIED_PATHS
