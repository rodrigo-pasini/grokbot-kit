"""Provas dos hooks com as CLIs reais no box (checks C67-C69; AC 54-57). Rodam só com `-m integration`.

Mesmo `HOME` temporário de `test_real_cli.py`, que no opencode já instala o plugin `grokbot-kit.ts` com o caminho
absoluto do `grokbot-kit` do ambiente de teste, como `grokbot-kit install opencode` o deixaria.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from test_real_cli import prepare_home

pytestmark = pytest.mark.integration

QUESTION_PROMPT = (
    "Before doing anything else, use your question tool to ask me which file name to use, "
    "offering the options a.txt and b.txt. Do not use any other tool."
)


def kit_exe() -> str:
    exe = shutil.which("grokbot-kit")
    assert exe is not None
    return exe


def run_task(tmp_path: Path, home: Path, work: Path, tool: str, *cli_args: str) -> list[dict[str, Any]]:
    result = subprocess.run(
        [kit_exe(), "run", "--tool", tool, "--target", "it", "--label", "hook", "--cwd", str(work), "--", *cli_args],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(home)},
        stdin=subprocess.DEVNULL,
        check=False,
        timeout=600,
    )
    sink = tmp_path / "sink.jsonl"
    events = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines()] if sink.exists() else []
    assert events, result.stderr
    assert events[-1]["event"] in ("completed", "error", "timeout"), (events, result.stderr)
    return events


def asked_before_terminal(events: list[dict[str, Any]], status: str) -> list[dict[str, Any]]:
    asked = [e for e in events[:-1] if e["event"] == "needs_input" and e["status"] == status]
    assert asked, events
    return asked


# C67 - AC 54
def test_claude_hook_fires(tmp_path: Path) -> None:
    home, work, prompt = prepare_home(tmp_path, "claude", "denied")
    events = run_task(tmp_path, home, work, "claude", prompt)
    asked = asked_before_terminal(events, "permission")
    assert asked[0]["needs_input"]["tool_name"] == "Bash"
    assert (events[-1]["event"], events[-1]["status"]) == ("completed", "denied")


# C68 - AC 55
def test_opencode_plugin_fires_permission(tmp_path: Path) -> None:
    home, work, prompt = prepare_home(tmp_path, "opencode", "denied")
    events = run_task(tmp_path, home, work, "opencode", prompt)
    asked_before_terminal(events, "permission")


# C68 - AC 56
def test_opencode_plugin_fires_question(tmp_path: Path) -> None:
    home, work, _ = prepare_home(tmp_path, "opencode", "ok")
    events = run_task(tmp_path, home, work, "opencode", QUESTION_PROMPT)
    asked_before_terminal(events, "question")


# C69 - AC 57 (pergunta 2)
def test_codex_hook_fires(tmp_path: Path) -> None:
    home, work, prompt = prepare_home(tmp_path, "codex", "denied")
    events = run_task(tmp_path, home, work, "codex", "-s", "read-only", prompt)
    asked = asked_before_terminal(events, "permission")
    assert asked[0]["needs_input"]["tool_name"]
