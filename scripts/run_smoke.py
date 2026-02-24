#!/usr/bin/env python3
"""Smoke test: send one message, print response, validate model hot-swap.

Usage:
    AGENT_MODEL=openai:gpt-4o python scripts/run_smoke.py "What is 2+2?"
    python scripts/run_smoke.py --model openai:gpt-4.1-mini "What is 2+2?"
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from rich.console import Console

# Add project root to path for imports
sys.path.insert(0, ".")

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from orchestrator.agent import build_agent

console = Console()


@click.command()
@click.argument("message")
@click.option("--model", default=None, help="Model string, e.g. openai:gpt-4o")
def main(message: str, model: str | None) -> None:
    """Send a single message to the agent and print the response."""
    # create_deep_agent returns a CompiledStateGraph directly
    compiled, initial_files = build_agent(model_name=model)
    config = {"configurable": {"thread_id": "smoke-test"}}

    console.print(f"[bold blue]Model:[/] {model or 'from AGENT_MODEL env'}")
    console.print(f"[bold blue]Input:[/] {message}")
    console.print("[dim]---[/]")

    invoke_state: dict = {"messages": [{"role": "user", "content": message}]}
    if initial_files:
        invoke_state["files"] = initial_files

    result = compiled.invoke(invoke_state, config)

    # Extract the last AI message
    last_msg = result["messages"][-1]
    content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    console.print(f"[bold green]Response:[/] {content}")


if __name__ == "__main__":
    main()
