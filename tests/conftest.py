"""Fixtures do `run`: `HOME` isolado em `tmp_path`, CLIs falsas de `tests/fakes/` no `PATH` e um sink `file`."""

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

FAKES = Path(__file__).resolve().parent / "fakes"

MODELS = {"claude": "sonnet", "opencode": "opencode/free-model", "codex": "gpt-test"}


def default_config(sink: Path, installed: tuple[str, ...] = ("opencode", "claude", "codex")) -> str:
    lines = [
        "[setup]",
        "version = 1",
        f"installed = {json.dumps(list(installed))}",
        f'default_cli = "{installed[0]}"',
        "",
    ]
    for tool, model in MODELS.items():
        lines += [f"[cli.{tool}]", f'models = ["{model}"]']
        if tool == "codex":
            lines.append('codex_home = "~/.grokbot-kit/codex-home"')
        lines += [f"[cli.{tool}.tiers]", f'standard = ["{model}"]', ""]
    lines += [
        "[routes.bot-a]",
        'sinks = ["arquivo"]',
        "",
        "[sinks.arquivo]",
        'type = "file"',
        f"path = {json.dumps(str(sink))}",
        "",
    ]
    return "\n".join(lines)


@dataclass
class Kit:
    home: Path
    sink: Path
    record: Path
    env: dict[str, str]

    def write_config(self, text: str) -> None:
        path = self.home / ".config" / "grokbot-kit" / "config.toml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run(self, *args: str, **fake: str) -> subprocess.CompletedProcess[str]:
        exe = shutil.which("grokbot-kit")
        assert exe is not None, "console script grokbot-kit não instalado"
        env = {**self.env, "FAKE_RECORD": str(self.record), **fake}
        return subprocess.run(
            [exe, "run", *args],
            input="stdin do run, que o agente não pode herdar",
            capture_output=True,
            text=True,
            env=env,
            cwd=self.home,
            check=False,
            timeout=60,
        )

    def tasks(self) -> list[Path]:
        root = self.home / ".grokbot-kit" / "tasks"
        return sorted(root.iterdir()) if root.exists() else []

    def task_dir(self) -> Path:
        tasks = self.tasks()
        assert len(tasks) == 1, tasks
        return tasks[0]

    def sink_events(self) -> list[dict[str, Any]]:
        if not self.sink.exists():
            return []
        return [json.loads(line) for line in self.sink.read_text(encoding="utf-8").splitlines()]

    def launched(self) -> dict[str, Any]:
        result: dict[str, Any] = json.loads(self.record.read_text(encoding="utf-8"))
        return result


@pytest.fixture
def kit(tmp_path: Path) -> Kit:
    home = tmp_path / "home"
    home.mkdir()
    env = {
        "HOME": str(home),
        "PATH": f"{FAKES}{os.pathsep}{os.environ['PATH']}",
        "LANG": "C.UTF-8",
    }
    k = Kit(home=home, sink=tmp_path / "sink.jsonl", record=tmp_path / "launched.json", env=env)
    k.write_config(default_config(k.sink))
    return k
