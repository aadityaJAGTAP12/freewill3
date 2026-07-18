"""LangChain Agent setup with Ollama Mistral and tool monitoring callbacks.

Creates a ReAct-style agent using LangChain's create_agent (LangGraph-based)
with exactly 4 tools: read_file, write_file, shell_exec, web_request.

Includes ToolMonitorCallback that prints every tool call to the terminal
and records structured telemetry events via TelemetryCapture.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama

from src.telemetry import TelemetryCapture
from src.tools import read_file, shell_exec, web_request, write_file

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OLLAMA_MODEL = "mistral"
"""Ollama model name to use for the agent."""

AGENT_SYSTEM_PROMPT = (
    "You are a helpful AI assistant with access to the following tools. "
    "You MUST use these tools to answer the user — do NOT just write code or plans.\n\n"
    "Available tools:\n"
    "- read_file(path): Read and return the contents of a file\n"
    "- write_file(path, content): Write content to a file\n"
    "- shell_exec(command): Run a shell command and return its output\n"
    "- web_request(url): Make an HTTP GET request to a URL\n\n"
    "Examples:\n"
    "- To list files: shell_exec('ls -la <directory>')\n"
    "- To read a file: read_file(path)\n"
    "- To summarize files: list them first, then read each one.\n\n"
    "Think step by step. Call one tool at a time. "
    "After you have all the information, provide the final answer."
)

# ---------------------------------------------------------------------------
# Callback Handler
# ---------------------------------------------------------------------------


class ToolMonitorCallback(BaseCallbackHandler):
    """Callback handler that prints every tool call to the terminal
    and records structured telemetry events.

    Parameters
    ----------
    telemetry : TelemetryCapture
        The telemetry capture instance to record events into.
    """

    def __init__(self, telemetry: TelemetryCapture) -> None:
        super().__init__()
        self._telemetry = telemetry

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts executing."""
        tool_name = serialized.get("name", "unknown")

        # Parse arguments — they arrive as a JSON string or dict
        # depending on the LangGraph execution path
        tool_args: dict[str, Any] = {}
        if input_str:
            if isinstance(input_str, str):
                try:
                    tool_args = json.loads(input_str)
                except json.JSONDecodeError:
                    tool_args = {"_raw": input_str}
            elif isinstance(input_str, dict):
                tool_args = input_str
            else:
                tool_args = {"_raw": str(input_str)}

        # Record structured telemetry event
        event = self._telemetry.record_tool_call(tool_name, tool_args)

        # Print to terminal (no monitor logic yet)
        print(f"\n{'='*60}")
        print(f"  TOOL CALLED: {tool_name}")
        print(f"  ARGS: {input_str}")
        print(f"  STEP: {event['step']}")
        print(f"{'='*60}")
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------


def build_agent(
    tools: list[BaseTool] | None = None,
    model_name: str = OLLAMA_MODEL,
    temperature: float = 0.0,
) -> tuple[Any, list[BaseTool]]:
    """Build and return a LangChain agent with the given tools.

    Parameters
    ----------
    tools : list[BaseTool] | None
        List of tools to provide to the agent. Defaults to the standard 4.
    model_name : str
        Ollama model name to use.
    temperature : float
        Model temperature (0.0 = deterministic, 1.0 = creative).

    Returns
    -------
    tuple[Any, list[BaseTool]]
        (compiled agent graph, list of tools used).
    """
    if tools is None:
        tools = [read_file, write_file, shell_exec, web_request]

    llm = ChatOllama(model=model_name, temperature=temperature)

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=AGENT_SYSTEM_PROMPT,
    )

    return agent, tools


# ---------------------------------------------------------------------------
# Main entry point (for testing)
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the agent with a test prompt to verify callbacks fire correctly.

    Usage:
        python -m src.agent "summarize files in data/documents"
    """
    prompt = sys.argv[1] if len(sys.argv) > 1 else "summarize files in data/documents"

    print(f"\n{'='*60}")
    print(f"  AGENT TEST RUN")
    print(f"{'='*60}")
    print(f"  Prompt: {prompt}")
    print(f"{'='*60}\n")

    # Build agent
    agent, tools = build_agent()

    # Create telemetry capture and callback handler
    telemetry = TelemetryCapture()
    monitor = ToolMonitorCallback(telemetry=telemetry)

    # Run the agent
    inputs = {"messages": [HumanMessage(content=prompt)]}
    config = {"callbacks": [monitor]}

    print("\n--- Agent output ---\n")
    result = agent.invoke(inputs, config=config)

    # Extract final output from the result messages
    final_messages = result.get("messages", [])
    if final_messages:
        last = final_messages[-1]
        if hasattr(last, "content"):
            print(f"\n--- Final response ---\n{last.content}")
        else:
            print(f"\n--- Final response ---\n{last}")
    else:
        print(f"\n--- Result ---\n{result}")

    # Print telemetry summary
    print(f"\n{'='*60}")
    print(f"  TELEMETRY LOG ({len(telemetry.get_history())} events)")
    print(f"{'='*60}")
    for event in telemetry.get_history():
        print(f"  Step {event['step']}: {event['tool_called']}")
        if event["file_paths"]:
            print(f"    paths: {event['file_paths']}")
        if event["commands"]:
            print(f"    cmds:  {event['commands']}")
        if event["urls"]:
            print(f"    urls:  {event['urls']}")

    print(f"\n{'='*60}")
    print("  AGENT RUN COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
