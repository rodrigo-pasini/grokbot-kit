"""Fixtures do `run`: `HOME` isolado em `tmp_path`, CLIs falsas de `tests/fakes/` no `PATH` e um sink `file`."""

import http.server
import json
import os
import shutil
import socket
import subprocess
import threading
import time
import tomllib
from collections.abc import Iterator
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

    def config_text(self) -> str:
        return (self.home / ".config" / "grokbot-kit" / "config.toml").read_text(encoding="utf-8")

    def cli(self, *args: str, input: str = "", timeout: float = 60) -> subprocess.CompletedProcess[str]:
        exe = shutil.which("grokbot-kit")
        assert exe is not None, "console script grokbot-kit não instalado"
        return subprocess.run(
            [exe, *args],
            input=input,
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.home,
            check=False,
            timeout=timeout,
        )

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

    def calls(self) -> list[dict[str, Any]]:
        """As linhas de `FAKE_CALLS` gravadas pelas CLIs e instaladores falsos, na ordem."""
        path = Path(self.env["FAKE_CALLS"])
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def config(self) -> dict[str, Any]:
        return tomllib.loads(self.config_text())


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


def clean_path() -> str:
    """`PATH` sem as CLIs reais do box: o `curl` falso, o `grokbot-kit` do ambiente de teste e o sistema."""
    exe = shutil.which("grokbot-kit")
    assert exe is not None, "console script grokbot-kit não instalado"
    return os.pathsep.join([str(FAKES / "installers"), os.path.dirname(exe), "/usr/bin", "/bin"])


@pytest.fixture
def fresh(tmp_path: Path) -> Kit:
    """Box limpo: `HOME` isolado sem config, nenhuma CLI no `PATH` e `FAKE_CALLS` gravando as chamadas."""
    home = tmp_path / "home"
    home.mkdir()
    env = {"HOME": str(home), "PATH": clean_path(), "LANG": "C.UTF-8", "FAKE_CALLS": str(tmp_path / "calls.jsonl")}
    return Kit(home=home, sink=tmp_path / "sink.jsonl", record=tmp_path / "launched.json", env=env)


KEY = "crsr_test-key-not-real"


def write_secret(home: Path, name: str, value: str, mode: int = 0o600) -> Path:
    secrets = home / ".secrets" / "grokbot-kit"
    secrets.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = secrets / name
    path.write_text(value, encoding="utf-8")
    os.chmod(path, mode)
    return path


@dataclass
class Received:
    method: str
    path: str
    headers: dict[str, str]
    body: bytes
    at: float


class Receiver:
    """Receptor HTTP local: responde, em ordem, cada item de `responses` (o último se repete) e grava as requisições."""

    def __init__(self) -> None:
        self.responses: list[tuple[int, str]] = [(200, json.dumps({"success": True, "runUuid": "u-1"}))]
        self.delay = 0.0
        self.requests: list[Received] = []
        self._lock = threading.Lock()
        receiver = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                with receiver._lock:
                    receiver.requests.append(
                        Received(
                            "POST", self.path, {k.lower(): v for k, v in self.headers.items()}, body, time.monotonic()
                        )
                    )
                    index = min(len(receiver.requests), len(receiver.responses)) - 1
                    status, text = receiver.responses[index]
                if receiver.delay:
                    time.sleep(receiver.delay)
                data = text.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, format: str, *args: Any) -> None:
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/automations/webhook/0f3c-routine-uuid"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def respond(self, *responses: tuple[int, str]) -> None:
        self.responses = list(responses)

    def bodies(self) -> list[dict[str, Any]]:
        return [json.loads(r.body) for r in self.requests]

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def receiver() -> Iterator[Receiver]:
    r = Receiver()
    yield r
    r.close()


@pytest.fixture
def receiver_b() -> Iterator[Receiver]:
    r = Receiver()
    yield r
    r.close()


def closed_port_url() -> str:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    return f"http://127.0.0.1:{port}/automations/webhook/fechado"


def routine_route(
    target: str, sink: str, url_secret: str, key_secret: str, headers: dict[str, str] | None = None
) -> str:
    lines = [
        "",
        f"[routes.{target}]",
        f'sinks = ["{sink}"]',
        "",
        f"[sinks.{sink}]",
        'type = "grokbot-routine"',
        f'url_secret = "{url_secret}"',
        f'key_secret = "{key_secret}"',
    ]
    if headers:
        lines += ["", f"[sinks.{sink}.headers]", *(f"{json.dumps(k)} = {json.dumps(v)}" for k, v in headers.items())]
    return "\n".join(lines) + "\n"


def add_routine(kit: Kit, receiver: Receiver, target: str = "bot-r", headers: dict[str, str] | None = None) -> None:
    """Rota `target` com um sink `grokbot-routine` apontando para `receiver`, segredos `0600` com `\\n` final."""
    write_secret(kit.home, f"{target}-url", receiver.url + "\n")
    write_secret(kit.home, f"{target}-key", KEY + "\n")
    kit.write_config(
        kit.config_text() + routine_route(target, f"rotina-{target}", f"{target}-url", f"{target}-key", headers)
    )
