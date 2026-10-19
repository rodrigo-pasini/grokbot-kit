"""Montagem do evento `grokbot-kit.event/v1` de uma task (AC 49-53, door 2).

Os campos de task vêm do `meta.json` do task dir, para que o `run` (evento terminal) e o `emit` (`needs_input`)
montem o mesmo payload.
"""

import os
import shlex
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = "grokbot-kit.event/v1"
EXIT_REASONS = (
    "success",
    "permission_denied",
    "agent_error",
    "nonzero_exit",
    "timeout",
    "interrupted",
    "needs_input",
)


def rfc3339(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _git(cwd: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def repo_info(cwd: Path) -> dict[str, str | None] | None:
    """`{root, branch, head}` do repositório git que contém `cwd`; `None` fora de um repo ou sem nenhum commit."""
    root = _git(cwd, "rev-parse", "--show-toplevel")
    head = _git(cwd, "rev-parse", "--verify", "-q", "HEAD")
    if not root or not head:
        return None
    branch = _git(cwd, "symbolic-ref", "-q", "--short", "HEAD")
    return {"root": root, "branch": branch or None, "head": head}


def resume_hint(tool: str, session_id: str | None, codex_home: str | None) -> str | None:
    if not session_id:
        return None
    sid = shlex.quote(session_id)
    if tool == "claude":
        return f"claude -p --resume {sid}"
    if tool == "opencode":
        return f"opencode run -s {sid}"
    if tool == "codex":
        return f"CODEX_HOME={shlex.quote(codex_home or '')} codex exec resume {sid}"
    return None


def task_event(
    meta: dict[str, Any],
    task_dir: Path,
    *,
    event: str,
    status: str,
    exit_reason: str,
    exit_code: int | None,
    summary: str,
    session_id: str | None = None,
    needs_input: dict[str, str | None] | None = None,
    transcript_path: str | None = None,
) -> dict[str, Any]:
    if exit_reason not in EXIT_REASONS:
        raise ValueError(f"exit_reason {exit_reason!r} is not one of {', '.join(EXIT_REASONS)}")
    if (event == "needs_input") != (exit_reason == "needs_input"):
        raise ValueError("exit_reason needs_input is used by, and only by, event needs_input")
    return {
        "schema": SCHEMA,
        "event": event,
        "status": status,
        "task_id": meta["task_id"],
        "task_label": meta["task_label"],
        "target": meta["target"],
        "tool": meta["tool"],
        "model": meta["model"],
        "model_source": meta["model_source"],
        "tier": meta["tier"],
        "session_id": session_id,
        "cwd": meta["cwd"],
        "repo": repo_info(Path(meta["cwd"])),
        "exit_code": exit_code,
        "exit_reason": exit_reason,
        "summary": summary,
        "needs_input": needs_input,
        "resume_hint": resume_hint(meta["tool"], session_id, meta.get("codex_home")),
        "output_file": str(task_dir / "out.jsonl"),
        "transcript_path": transcript_path,
        "log_file": str(task_dir / "stderr.log"),
        "started_at": meta["started_at"],
        "timestamp": rfc3339(datetime.now(UTC)),
    }


def needs_input_event(
    meta: dict[str, Any],
    task_dir: Path,
    *,
    kind: str,
    tool_name: str | None,
    detail: str | None,
    session_id: str | None = None,
    transcript_path: str | None = None,
) -> dict[str, Any]:
    """`event: "needs_input"`, com `status` igual ao `kind` (`permission` ou `question`) e `exit_reason: "needs_input"`."""
    return task_event(
        meta,
        task_dir,
        event="needs_input",
        status=kind,
        exit_reason="needs_input",
        exit_code=None,
        summary="",
        session_id=session_id,
        needs_input={"kind": kind, "tool_name": tool_name, "detail": detail},
        transcript_path=transcript_path,
    )


def route_test_event(target: str) -> dict[str, Any]:
    """`event: "test"` do `route test` (AC 75): os campos de task da door 2 ficam `null`."""
    return {
        "schema": SCHEMA,
        "event": "test",
        "status": "test",
        "task_id": None,
        "task_label": None,
        "target": target,
        "tool": None,
        "model": None,
        "model_source": None,
        "tier": None,
        "session_id": None,
        "cwd": os.getcwd(),
        "repo": None,
        "exit_code": None,
        "exit_reason": None,
        "summary": "",
        "needs_input": None,
        "resume_hint": None,
        "output_file": None,
        "transcript_path": None,
        "log_file": None,
        "started_at": None,
        "timestamp": rfc3339(datetime.now(UTC)),
    }
