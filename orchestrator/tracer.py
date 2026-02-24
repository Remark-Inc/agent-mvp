"""Structured trace capture for agent runs.

Captures events from LangGraph streaming and produces:
- trace.json — one object per step
- trace.md — human-readable markdown
- metadata.json — run metadata
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class TraceStep:
    """A single step in the agent's execution trace."""

    step_number: int
    type: str  # orchestrator_reasoning, skill_read, skill_activation,
    # tool_call, tool_result, skill_output, context_summarization, final_output
    node: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step_number,
            "type": self.type,
            "node": self.node,
            "content": self.content[:5000],
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class Tracer:
    """Captures and saves structured traces from agent execution."""

    def __init__(self) -> None:
        self.steps: list[TraceStep] = []
        self._step_counter = 0
        self.start_time: float = 0
        self.end_time: float = 0

    def start(self) -> None:
        self.start_time = time.time()

    def stop(self) -> None:
        self.end_time = time.time()

    @property
    def elapsed(self) -> float:
        return self.end_time - self.start_time if self.end_time else 0

    def add_step(
        self,
        step_type: str,
        content: str = "",
        node: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> TraceStep:
        self._step_counter += 1
        step = TraceStep(
            step_number=self._step_counter,
            type=step_type,
            node=node,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.steps.append(step)
        return step

    def capture_stream_event(self, event: dict[str, Any]) -> None:
        """Process a single LangGraph stream event and add trace steps."""
        for node_name, node_data in event.items():
            if node_name == "__metadata__":
                continue

            if not isinstance(node_data, dict):
                continue

            messages = node_data.get("messages", [])

            # LangGraph wraps values in Overwrite objects for reducer state
            if hasattr(messages, "value"):
                messages = messages.value

            if not isinstance(messages, list):
                messages = [messages] if messages else []

            for msg in messages:
                self._process_message(msg, node_name)

    def _process_message(self, msg: Any, node: str) -> None:
        """Classify and trace a single message."""
        msg_type = getattr(msg, "type", "unknown")
        content = getattr(msg, "content", str(msg))

        # Tool calls
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                tc_name = tc.get("name", "unknown") if isinstance(tc, dict) else str(tc)
                tc_args = tc.get("args", {}) if isinstance(tc, dict) else {}

                # Classify by tool name
                if tc_name == "read_file":
                    step_type = "skill_read"
                elif tc_name == "task":
                    step_type = "skill_activation"
                else:
                    step_type = "tool_call"

                self.add_step(
                    step_type=step_type,
                    content=f"{tc_name}({json.dumps(tc_args, default=str)[:500]})",
                    node=node,
                    metadata={"tool_name": tc_name},
                )
            return

        # Tool results
        if msg_type == "tool":
            tool_name = getattr(msg, "name", "unknown")
            self.add_step(
                step_type="tool_result",
                content=content[:2000] if isinstance(content, str) else str(content)[:2000],
                node=node,
                metadata={"tool_name": tool_name},
            )
            return

        # AI reasoning
        if msg_type == "ai" and content:
            self.add_step(
                step_type="orchestrator_reasoning",
                content=content[:3000] if isinstance(content, str) else str(content)[:3000],
                node=node,
            )

    def save(
        self,
        run_dir: Path,
        scenario_name: str = "",
        model: str = "",
        scenario_path: str = "",
    ) -> None:
        """Save trace.json, trace.md, and metadata.json to run directory."""
        run_dir.mkdir(parents=True, exist_ok=True)

        # trace.json
        trace_json = [step.to_dict() for step in self.steps]
        (run_dir / "trace.json").write_text(json.dumps(trace_json, indent=2))

        # trace.md
        trace_md = self._build_trace_md(scenario_name, model)
        (run_dir / "trace.md").write_text(trace_md)

        # metadata.json
        metadata = {
            "scenario": scenario_name,
            "scenario_path": scenario_path,
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latency_seconds": round(self.elapsed, 2),
            "total_steps": len(self.steps),
            "step_types": self._count_step_types(),
            "tools_used": self._list_tools_used(),
            "summarization_occurred": any(
                s.type == "context_summarization" for s in self.steps
            ),
        }
        (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    def _build_trace_md(self, scenario_name: str, model: str) -> str:
        """Build human-readable trace markdown."""
        lines = [
            f"# Trace: {scenario_name}",
            "",
            f"**Model:** {model}",
            f"**Latency:** {self.elapsed:.1f}s",
            f"**Steps:** {len(self.steps)}",
            "",
            "---",
            "",
        ]

        for step in self.steps:
            icon = _step_icon(step.type)
            lines.append(f"### Step {step.step_number}: {icon} {step.type}")
            if step.node:
                lines.append(f"**Node:** {step.node}")
            lines.append("")

            # Verbose content in collapsible details
            if len(step.content) > 200:
                lines.append("<details>")
                lines.append(f"<summary>{step.content[:200]}...</summary>")
                lines.append("")
                lines.append(f"```\n{step.content}\n```")
                lines.append("</details>")
            else:
                lines.append(f"```\n{step.content}\n```")

            lines.append("")

        return "\n".join(lines)

    def _count_step_types(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for step in self.steps:
            counts[step.type] = counts.get(step.type, 0) + 1
        return counts

    def _list_tools_used(self) -> list[str]:
        tools = set()
        for step in self.steps:
            if step.type in ("tool_call", "skill_read", "skill_activation"):
                tool_name = step.metadata.get("tool_name", "")
                if tool_name:
                    tools.add(tool_name)
        return sorted(tools)


def _step_icon(step_type: str) -> str:
    """Return an icon for trace.md readability."""
    icons = {
        "orchestrator_reasoning": "🧠",
        "skill_read": "📖",
        "skill_activation": "🚀",
        "tool_call": "🔧",
        "tool_result": "📤",
        "skill_output": "📋",
        "context_summarization": "⚡",
        "final_output": "✅",
    }
    return icons.get(step_type, "▪️")
