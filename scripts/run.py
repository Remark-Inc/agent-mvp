#!/usr/bin/env python3
"""Run a scenario through the agent and save traced output to runs/.

Usage:
    python scripts/run.py scenarios/simple_research.yaml
    python scripts/run.py scenarios/simple_research.yaml --model openai:gpt-4.1-mini
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import click
import yaml
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from rich.console import Console

# Add project root to path for imports
sys.path.insert(0, ".")

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from orchestrator.agent import build_agent
from orchestrator.tracer import Tracer

console = Console()


@click.command()
@click.argument("scenario_path", type=click.Path(exists=True))
@click.option("--model", default=None, help="Model override, e.g. openai:gpt-5.2")
def main(scenario_path: str, model: str | None) -> None:
    """Run a scenario YAML through the agent with trace capture."""
    # Load scenario
    with open(scenario_path) as f:
        scenario = yaml.safe_load(f)

    scenario_name = scenario.get("name", Path(scenario_path).stem)
    user_request = scenario["input"]["user_request"]
    model_override = model or scenario.get("model")

    console.print(f"[bold blue]Scenario:[/] {scenario_name}")
    console.print(f"[bold blue]Model:[/] {model_override or 'from AGENT_MODEL env'}")
    console.print(f"[bold blue]Input:[/] {user_request[:200]}")
    console.print("[dim]---[/]")

    # Build agent — create_deep_agent returns a CompiledStateGraph directly
    compiled, initial_files = build_agent(model_name=model_override)
    config = {"configurable": {"thread_id": f"run-{scenario_name}"}}

    # Set up invoke state
    invoke_state: dict = {"messages": [{"role": "user", "content": user_request}]}
    if initial_files:
        invoke_state["files"] = initial_files

    # Run with trace capture via streaming
    tracer = Tracer()
    tracer.start()

    try:
        # Stream events for tracing
        final_result = None
        for event in compiled.stream(invoke_state, config, stream_mode="updates"):
            tracer.capture_stream_event(event)
            # Keep track of latest state
            final_result = event

        # Also get the final state for the response
        state = compiled.get_state(config)
        messages = state.values.get("messages", [])

    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        tracer.stop()
        raise
    finally:
        tracer.stop()

    # Extract response
    if messages:
        last_msg = messages[-1]
        response = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    else:
        response = "(no response)"

    # Add final output step
    tracer.add_step("final_output", content=response[:3000])

    console.print(f"\n[bold green]Response:[/]\n{response[:2000]}")
    console.print(f"\n[dim]Elapsed: {tracer.elapsed:.1f}s | Steps: {len(tracer.steps)}[/]")

    # Save to runs/
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path("runs") / f"{timestamp}_{scenario_name}"

    tracer.save(
        run_dir=run_dir,
        scenario_name=scenario_name,
        model=model_override or "default",
        scenario_path=scenario_path,
    )

    # Also save the full output for convenience
    (run_dir / "output.md").write_text(
        f"# Run: {scenario_name}\n\n"
        f"**Model:** {model_override or 'default'}\n"
        f"**Latency:** {tracer.elapsed:.1f}s\n\n"
        f"## Response\n\n{response}\n"
    )

    console.print(f"\n[bold]Run saved to:[/] {run_dir}")
    console.print(f"  trace.md, trace.json, metadata.json, output.md")


if __name__ == "__main__":
    main()
