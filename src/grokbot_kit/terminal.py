"""Status terminal de uma task a partir do exit e da saída do agente (AC 43-46, 51)."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUMMARY_LIMIT = 2000


@dataclass(frozen=True)
class AgentOutput:
    error: bool
    permission_denied: bool
    summary: str
    session_id: str | None = None


def _json_objects(text: str) -> list[dict[str, Any]]:
    objects = []
    for line in text.splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            objects.append(obj)
    return objects


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def read_output(tool: str, task_dir: Path) -> AgentOutput:
    """Lê `out.jsonl` (e `last-message.txt` do codex) do task dir."""
    objects = _json_objects(_read(task_dir / "out.jsonl"))
    error = denied = False
    summary = ""
    session_id = None
    if tool == "claude":
        results = [o for o in objects if o.get("type") == "result"] or objects
        if results:
            result = results[-1]
            error = result.get("is_error") is True
            denied = bool(result.get("permission_denials"))
            text = result.get("result")
            summary = text if isinstance(text, str) else ""
            session_id = result.get("session_id")
    elif tool == "codex":
        error = any(o.get("type") in ("turn.failed", "error") for o in objects)
        summary = _read(task_dir / "last-message.txt")
        session_id = next((o.get("thread_id") for o in objects if o.get("type") == "thread.started"), None)
    elif tool == "opencode":
        error = any(o.get("type") == "error" for o in objects)
        texts = [o["part"].get("text") for o in objects if o.get("type") == "text" and isinstance(o.get("part"), dict)]
        texts = [t for t in texts if isinstance(t, str)]
        summary = texts[-1] if texts else ""
        session_id = next((o["sessionID"] for o in objects if o.get("sessionID")), None)
    return AgentOutput(
        error=error,
        permission_denied=denied,
        summary=summary[:SUMMARY_LIMIT],
        session_id=session_id if isinstance(session_id, str) and session_id else None,
    )


def classify(exit_code: int, output: AgentOutput, *, needs_input: bool) -> tuple[str, str, str]:
    """`(event, status, exit_reason)`; erro na saída vence exit diferente de 0, e os dois vencem `denied`."""
    if output.error:
        return "error", "failed", "agent_error"
    if exit_code != 0:
        return "error", "failed", "nonzero_exit"
    if needs_input or output.permission_denied:
        return "completed", "denied", "permission_denied"
    return "completed", "ok", "success"
