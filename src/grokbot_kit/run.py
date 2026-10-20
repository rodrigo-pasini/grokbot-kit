"""`grokbot-kit run`: valida, cria o task dir (door 4), lança o agente e envia um único evento terminal (AC 39-53, 87-89)."""

import argparse
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from grokbot_kit import config, deliver, launch, payload, resolve, terminal
from grokbot_kit.payload import rfc3339

SECRET_KEYS = ("url_secret", "key_secret", "token_secret", "webhook_secret")
LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
EXIT_NOT_FOUND = 127
EXIT_TIMEOUT = 124
EXIT_INTERRUPTED = 130
GRACE_SECONDS = 10.0
POLL_SECONDS = 0.05


class UsageError(Exception):
    pass


def _resolve(args: argparse.Namespace, cfg: dict[str, Any]) -> dict[str, Any]:
    """Tudo o que o AC 47 manda recusar com `2` antes de existir task dir."""
    try:
        agent = resolve.resolve(cfg, tool=args.tool, model=args.model, tier=args.tier, timeout=args.timeout)
    except resolve.ResolveError as e:
        raise UsageError(str(e)) from None
    if agent.tool == "claude" and "--bare" in args.extras:
        raise UsageError("--bare disables the hooks grokbot-kit relies on; remove it")
    cli = cfg.get("cli", {}).get(agent.tool, {})
    if agent.tool == "claude" and "api_key_secret" in cli:
        config.check_secret(cli["api_key_secret"])
    route = cfg.get("routes", {}).get(args.target)
    if route is None:
        raise UsageError(f"target {args.target!r} has no route; run: grokbot-kit route add {args.target}")
    for name in route.get("sinks", []):
        sink = cfg.get("sinks", {}).get(name)
        if sink is None:
            raise UsageError(f"route {args.target!r} uses sink {name!r}, which is not in [sinks]")
        for key in SECRET_KEYS:
            if key in sink:
                config.check_secret(sink[key])
    if not LABEL_RE.match(args.label):
        raise UsageError("--label must use only letters, digits, '.', '_' and '-'")
    cwd = Path(args.cwd or os.getcwd()).resolve()
    if not cwd.is_dir():
        raise UsageError(f"--cwd is not a directory: {cwd}")
    extras = list(args.extras)
    if args.prompt_file:
        try:
            extras.append(Path(args.prompt_file).read_text(encoding="utf-8"))
        except OSError as e:
            raise UsageError(f"cannot read --prompt-file: {e}") from None
    return {
        **agent._asdict(),
        "cli": cli,
        "cwd": cwd,
        "extras": extras,
    }


def _recorded_needs_input(task_dir: Path) -> list[dict[str, Any]]:
    """Os `needs_input` registrados em `events.jsonl` pelo `emit`, na ordem."""
    try:
        lines = (task_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    found = []
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        event = record.get("event") if isinstance(record, dict) else None
        if isinstance(event, dict) and event.get("event") == "needs_input":
            found.append(event)
    return found


def _signal_group(pgid: int, sig: int) -> None:
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        pass


def _group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def stop_group(proc: "subprocess.Popen[bytes]", sent_at: float, grace: float = GRACE_SECONDS) -> None:
    """Escada do AC 87 depois do primeiro sinal, mandado em `sent_at`: `SIGTERM` ao grupo `grace` s depois e
    `SIGKILL` `grace` s depois disso, a menos que o agente saia e o grupo dele esvazie antes."""
    for sig, at in ((signal.SIGTERM, sent_at + grace), (signal.SIGKILL, sent_at + 2 * grace)):
        while time.monotonic() < at:
            if proc.poll() is not None and not _group_alive(proc.pid):
                return
            time.sleep(POLL_SECONDS)
        _signal_group(proc.pid, sig)
    proc.wait()


def _supervise(argv: list[str], timeout_seconds: int, task_dir: Path, **popen: Any) -> tuple[int | None, str | None]:
    """Lança o agente num grupo próprio e espera; devolve `(returncode, stopped)`, com `returncode` `None` quando o
    binário não existe e `stopped` `"timeout"` ou `"interrupted"` quando o kit encerrou o agente (AC 87, 88)."""
    received: list[tuple[int, float]] = []
    group: list[int] = []

    def forward(signum: int, frame: object) -> None:
        received.append((signum, time.monotonic()))
        if group:
            _signal_group(group[0], signum)

    previous = {sig: signal.signal(sig, forward) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        try:
            proc = subprocess.Popen(argv, process_group=0, **popen)
        except FileNotFoundError:
            return None, None
        group.append(proc.pid)
        if received:
            _signal_group(proc.pid, received[0][0])
        deadline = time.monotonic() + timeout_seconds
        while proc.poll() is None and not received and time.monotonic() < deadline:
            time.sleep(POLL_SECONDS)
        stopped = None
        if received:
            stopped = "interrupted"
            _log(task_dir, f"{signal.Signals(received[0][0]).name} received: forwarded to the agent's process group")
            stop_group(proc, received[0][1])
        elif proc.returncode is None:
            stopped = "timeout"
            _log(task_dir, f"timeout after {timeout_seconds}s: SIGINT to the agent's process group")
            sent_at = time.monotonic()
            _signal_group(proc.pid, signal.SIGINT)
            stop_group(proc, sent_at)
        return proc.returncode, stopped
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def _log(task_dir: Path, message: str) -> None:
    with (task_dir / "kit.log").open("a", encoding="utf-8") as f:
        f.write(f"{rfc3339(datetime.now(UTC))} {message}\n")


def _write_meta(task_dir: Path, meta: dict[str, Any]) -> None:
    (task_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    try:
        cfg = config.load()
        r = _resolve(args, cfg)
    except (config.ConfigError, UsageError) as e:
        print(f"grokbot-kit run: {e}", file=sys.stderr)
        return 2

    tool: str = r["tool"]
    started = datetime.now(UTC)
    task_id = f"{started:%Y%m%dT%H%M%S}-{args.label}-{secrets.token_hex(3)}"
    task_dir = config.tasks_dir() / task_id
    task_dir.mkdir(parents=True, mode=0o700)
    print(f"grokbot-kit: task dir {task_dir}", file=sys.stderr)

    kit_exe = launch.kit_executable()
    if tool == "claude":
        settings = json.dumps(launch.claude_settings(kit_exe), indent=2) + "\n"
        (task_dir / "claude-settings.json").write_text(settings, encoding="utf-8")
    bin_path = os.path.expanduser(r["cli"].get("bin", tool))
    argv = launch.agent_argv(tool, bin_path, r["model"], task_dir, kit_exe, r["extras"])
    env = {
        **os.environ,
        "GROKBOT_KIT_TASK_ID": task_id,
        "GROKBOT_KIT_TARGET": args.target,
        "GROKBOT_KIT_LABEL": args.label,
        "GROKBOT_KIT_TASK_DIR": str(task_dir),
        **config.cli_env(tool, r["cli"]),
    }

    meta: dict[str, Any] = {
        "task_id": task_id,
        "task_label": args.label,
        "target": args.target,
        "tool": tool,
        "model": r["model"],
        "model_source": r["model_source"],
        "tier": r["tier"],
        "timeout_seconds": r["timeout_seconds"],
        "cwd": str(r["cwd"]),
        "started_at": rfc3339(started),
        "finished_at": None,
        "exit_code": None,
    }
    if tool == "codex":
        meta["codex_home"] = env["CODEX_HOME"]
    _write_meta(task_dir, meta)
    _log(task_dir, f"launch {tool} model={r['model']} timeout={r['timeout_seconds']}s")

    with (task_dir / "out.jsonl").open("wb") as out, (task_dir / "stderr.log").open("wb") as err:
        returncode, stopped = _supervise(
            argv,
            r["timeout_seconds"],
            task_dir,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=err,
            cwd=r["cwd"],
            env=env,
        )
    if returncode is None:
        _log(task_dir, f"binary not found: {bin_path}")
        exit_code = EXIT_NOT_FOUND
        output = terminal.AgentOutput(error=True, permission_denied=False, summary=f"binary not found: {bin_path}")
    else:
        exit_code = returncode if returncode >= 0 else 128 - returncode
        output = terminal.read_output(tool, task_dir)
    if stopped == "timeout":
        exit_code = EXIT_TIMEOUT
    elif stopped == "interrupted":
        exit_code = EXIT_INTERRUPTED
    asked = _recorded_needs_input(task_dir)
    event_name, status, exit_reason = terminal.classify(exit_code, output, needs_input=bool(asked), stopped=stopped)
    transcripts = [e["transcript_path"] for e in asked if isinstance(e.get("transcript_path"), str)]
    event = payload.task_event(
        meta,
        task_dir,
        event=event_name,
        status=status,
        exit_reason=exit_reason,
        exit_code=exit_code,
        summary=output.summary,
        session_id=output.session_id,
        transcript_path=transcripts[-1] if transcripts else None,
    )
    _log(task_dir, f"exit {exit_code}: {event_name}/{status}/{exit_reason}")
    deliver.deliver(task_dir, cfg, args.target, event, "terminal")
    meta.update(finished_at=event["timestamp"], exit_code=exit_code)
    _write_meta(task_dir, meta)
    return exit_code
