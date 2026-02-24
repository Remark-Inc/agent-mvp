#!/usr/bin/env python3
"""Compare two agent runs structurally.

Usage:
    python scripts/compare.py runs/<first> runs/<second>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


def load_run(run_dir: Path) -> dict:
    """Load metadata and trace from a run directory."""
    data: dict = {"path": str(run_dir)}

    metadata_path = run_dir / "metadata.json"
    if metadata_path.exists():
        data["metadata"] = json.loads(metadata_path.read_text())
    else:
        data["metadata"] = {}

    trace_path = run_dir / "trace.json"
    if trace_path.exists():
        data["trace"] = json.loads(trace_path.read_text())
    else:
        data["trace"] = []

    output_path = run_dir / "output.md"
    if output_path.exists():
        data["output"] = output_path.read_text()
    else:
        data["output"] = ""

    return data


def extract_skills_invoked(trace: list[dict]) -> list[str]:
    """Extract skill names from trace steps."""
    skills = []
    for step in trace:
        if step.get("type") in ("skill_read", "skill_activation"):
            tool_name = step.get("metadata", {}).get("tool_name", "")
            if tool_name and tool_name not in skills:
                skills.append(tool_name)
    return skills


def extract_tools_called(trace: list[dict]) -> list[str]:
    """Extract tool names from trace steps."""
    tools = set()
    for step in trace:
        if step.get("type") in ("tool_call", "skill_read", "skill_activation"):
            tool_name = step.get("metadata", {}).get("tool_name", "")
            if tool_name:
                tools.add(tool_name)
    return sorted(tools)


def count_step_types(trace: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for step in trace:
        t = step.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts


@click.command()
@click.argument("run_a", type=click.Path(exists=True))
@click.argument("run_b", type=click.Path(exists=True))
def main(run_a: str, run_b: str) -> None:
    """Compare two agent runs side-by-side."""
    a = load_run(Path(run_a))
    b = load_run(Path(run_b))

    meta_a = a["metadata"]
    meta_b = b["metadata"]

    # Summary table
    table = Table(title="Run Comparison", show_lines=True)
    table.add_column("Attribute", style="bold")
    table.add_column(f"Run A", style="cyan")
    table.add_column(f"Run B", style="green")

    table.add_row("Path", a["path"], b["path"])
    table.add_row("Scenario", meta_a.get("scenario", "?"), meta_b.get("scenario", "?"))
    table.add_row("Model", meta_a.get("model", "?"), meta_b.get("model", "?"))
    table.add_row(
        "Latency",
        f"{meta_a.get('latency_seconds', '?')}s",
        f"{meta_b.get('latency_seconds', '?')}s",
    )
    table.add_row(
        "Total Steps",
        str(meta_a.get("total_steps", len(a["trace"]))),
        str(meta_b.get("total_steps", len(b["trace"]))),
    )

    # Tools used
    tools_a = meta_a.get("tools_used", extract_tools_called(a["trace"]))
    tools_b = meta_b.get("tools_used", extract_tools_called(b["trace"]))
    table.add_row("Tools Used", ", ".join(tools_a), ", ".join(tools_b))

    # Skills invoked
    skills_a = extract_skills_invoked(a["trace"])
    skills_b = extract_skills_invoked(b["trace"])
    table.add_row(
        "Skills Invoked",
        ", ".join(skills_a) or "(none)",
        ", ".join(skills_b) or "(none)",
    )

    # Output length
    table.add_row(
        "Output Length",
        f"{len(a['output'])} chars",
        f"{len(b['output'])} chars",
    )

    # Summarization
    table.add_row(
        "Summarization",
        str(meta_a.get("summarization_occurred", False)),
        str(meta_b.get("summarization_occurred", False)),
    )

    console.print(table)

    # Step type breakdown
    console.print("\n[bold]Step Type Breakdown:[/]")
    types_a = meta_a.get("step_types", count_step_types(a["trace"]))
    types_b = meta_b.get("step_types", count_step_types(b["trace"]))

    all_types = sorted(set(list(types_a.keys()) + list(types_b.keys())))

    step_table = Table(show_lines=True)
    step_table.add_column("Step Type", style="bold")
    step_table.add_column("Run A", justify="right")
    step_table.add_column("Run B", justify="right")

    for t in all_types:
        step_table.add_row(t, str(types_a.get(t, 0)), str(types_b.get(t, 0)))

    console.print(step_table)

    # Behavioral diff
    console.print("\n[bold]Behavioral Differences:[/]")
    diffs = []

    if meta_a.get("model") != meta_b.get("model"):
        diffs.append(f"  Different models: {meta_a.get('model')} vs {meta_b.get('model')}")

    if set(tools_a) != set(tools_b):
        only_a = set(tools_a) - set(tools_b)
        only_b = set(tools_b) - set(tools_a)
        if only_a:
            diffs.append(f"  Tools only in A: {', '.join(only_a)}")
        if only_b:
            diffs.append(f"  Tools only in B: {', '.join(only_b)}")

    if set(skills_a) != set(skills_b):
        diffs.append(f"  Skills A: {skills_a} vs Skills B: {skills_b}")

    latency_a = meta_a.get("latency_seconds", 0)
    latency_b = meta_b.get("latency_seconds", 0)
    if latency_a and latency_b and latency_a > 0:
        ratio = latency_b / latency_a
        if ratio > 1.5 or ratio < 0.67:
            diffs.append(
                f"  Significant latency difference: {latency_a}s vs {latency_b}s "
                f"({ratio:.1f}x)"
            )

    if diffs:
        for d in diffs:
            console.print(d)
    else:
        console.print("  No significant behavioral differences detected.")


if __name__ == "__main__":
    main()
