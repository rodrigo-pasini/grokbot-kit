"""Linha de comando de cada CLI de agente (AC 40-42, doors 7 e 13)."""

import json
import os
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any

TOOLS = ("opencode", "claude", "codex")
DEFAULT_CODEX_HOME = "~/.grokbot-kit/codex-home"


def kit_executable() -> str:
    """Caminho absoluto do executável `grokbot-kit` que os hooks chamam (door 6)."""
    argv0 = sys.argv[0]
    if os.path.basename(argv0) == "grokbot-kit":
        return os.path.abspath(argv0)
    found = shutil.which("grokbot-kit")
    return os.path.abspath(found or argv0)


def emit_command(kit_exe: str, tool: str) -> str:
    return f"{shlex.quote(kit_exe)} emit --from {tool}"


def claude_settings(kit_exe: str) -> dict[str, Any]:
    hook = {"type": "command", "command": emit_command(kit_exe, "claude")}
    return {"hooks": {"PermissionRequest": [{"matcher": "*", "hooks": [hook]}]}}


def codex_hooks_override(kit_exe: str) -> str:
    command = json.dumps(emit_command(kit_exe, "codex"))
    return f'hooks.PermissionRequest=[{{hooks=[{{type="command",command={command}}}]}}]'


def agent_argv(tool: str, bin_path: str, model: str, task_dir: Path, kit_exe: str, extras: list[str]) -> list[str]:
    if tool == "claude":
        settings = str(task_dir / "claude-settings.json")
        head = ["-p", "--output-format", "json", "--model", model, "--settings", settings]
    elif tool == "opencode":
        head = ["run", "--format", "json", "-m", model]
    elif tool == "codex":
        last_message = str(task_dir / "last-message.txt")
        head = ["exec", "--json", "-m", model, "-o", last_message, "--dangerously-bypass-hook-trust"]
        head += ["-c", codex_hooks_override(kit_exe)]
    else:
        raise ValueError(f"unknown tool: {tool}")
    return [bin_path, *head, *extras]
