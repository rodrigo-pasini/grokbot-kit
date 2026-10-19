"""`grokbot-kit run`: valida, cria o task dir (door 4), lança o agente e envia um único evento terminal (AC 39-48)."""

import argparse
import json
import os
import re
import secrets
import stat
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from grokbot_kit import config, deliver, launch, terminal

SECRET_KEYS = ("url_secret", "key_secret", "token_secret", "webhook_secret")
LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class UsageError(Exception):
    pass


def rfc3339(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds").replace("+00:00", "Z")


def _check_secret(name: str) -> None:
    path = config.secrets_dir() / name
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        raise UsageError(f"secret {name!r} not found; run: grokbot-kit secret set {name}") from None
    if mode != 0o600:
        raise UsageError(f"secret {name!r} has mode {mode:04o}, expected 0600: {path}")


def _resolve(args: argparse.Namespace, cfg: dict[str, Any]) -> dict[str, Any]:
    """Tudo o que o AC 47 manda recusar com `2` antes de existir task dir."""
    setup = cfg.get("setup", {})
    tool = args.tool or setup.get("default_cli")
    if tool not in launch.TOOLS:
        raise UsageError(f"no tool given and setup.default_cli is not one of {', '.join(launch.TOOLS)}")
    if tool not in setup.get("installed", []):
        raise UsageError(f"{tool} is not in setup.installed; run: grokbot-kit setup cli add {tool}")
    if tool == "claude" and "--bare" in args.extras:
        raise UsageError("--bare disables the hooks grokbot-kit relies on; remove it")
    cli = cfg.get("cli", {}).get(tool, {})
    tier = args.tier
    if args.model:
        model, model_source = args.model, "user"
    else:
        tier = tier or "standard"
        candidates = cli.get("tiers", {}).get(tier, [])
        if not candidates:
            raise UsageError(f"no model in cli.{tool}.tiers.{tier}; run: grokbot-kit setup models refresh {tool}")
        model, model_source = candidates[0], "tier"
    if model not in cli.get("models", []):
        raise UsageError(f"model {model!r} was not discovered for {tool}; run: grokbot-kit setup models refresh {tool}")
    route = cfg.get("routes", {}).get(args.target)
    if route is None:
        raise UsageError(f"target {args.target!r} has no route; run: grokbot-kit route add {args.target}")
    for name in route.get("sinks", []):
        sink = cfg.get("sinks", {}).get(name)
        if sink is None:
            raise UsageError(f"route {args.target!r} uses sink {name!r}, which is not in [sinks]")
        for key in SECRET_KEYS:
            if key in sink:
                _check_secret(sink[key])
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
        "tool": tool,
        "cli": cli,
        "model": model,
        "model_source": model_source,
        "tier": tier,
        "cwd": cwd,
        "extras": extras,
    }


def _needs_input_recorded(task_dir: Path) -> bool:
    try:
        lines = (task_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return False
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        event = record.get("event") if isinstance(record, dict) else None
        if isinstance(event, dict) and event.get("event") == "needs_input":
            return True
    return False


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
    }
    if tool == "codex":
        env["CODEX_HOME"] = os.path.expanduser(r["cli"].get("codex_home", launch.DEFAULT_CODEX_HOME))

    meta: dict[str, Any] = {
        "task_id": task_id,
        "task_label": args.label,
        "target": args.target,
        "tool": tool,
        "model": r["model"],
        "model_source": r["model_source"],
        "tier": r["tier"],
        "cwd": str(r["cwd"]),
        "started_at": rfc3339(started),
        "finished_at": None,
        "exit_code": None,
    }
    _write_meta(task_dir, meta)
    _log(task_dir, f"launch {tool} model={r['model']}")

    with (task_dir / "out.jsonl").open("wb") as out, (task_dir / "stderr.log").open("wb") as err:
        try:
            proc = subprocess.run(
                argv, check=False, stdin=subprocess.DEVNULL, stdout=out, stderr=err, cwd=r["cwd"], env=env
            )
        except FileNotFoundError:
            proc = None
    if proc is None:
        _log(task_dir, f"binary not found: {bin_path}")
        exit_code = 127
        output = terminal.AgentOutput(error=True, permission_denied=False, summary=f"binary not found: {bin_path}")
    else:
        exit_code = proc.returncode if proc.returncode >= 0 else 128 - proc.returncode
        output = terminal.read_output(tool, task_dir)
    event_name, status, exit_reason = terminal.classify(exit_code, output, needs_input=_needs_input_recorded(task_dir))

    event = {
        "schema": "grokbot-kit.event/v1",
        "event": event_name,
        "status": status,
        "task_id": task_id,
        "task_label": args.label,
        "target": args.target,
        "tool": tool,
        "model": r["model"],
        "model_source": r["model_source"],
        "tier": r["tier"],
        "session_id": None,
        "cwd": str(r["cwd"]),
        "repo": None,
        "exit_code": exit_code,
        "exit_reason": exit_reason,
        "summary": output.summary,
        "needs_input": None,
        "resume_hint": None,
        "output_file": str(task_dir / "out.jsonl"),
        "transcript_path": None,
        "log_file": str(task_dir / "stderr.log"),
        "started_at": rfc3339(started),
        "timestamp": rfc3339(datetime.now(UTC)),
    }
    _log(task_dir, f"exit {exit_code}: {event_name}/{status}/{exit_reason}")
    deliver.deliver(task_dir, cfg, args.target, event, "terminal")
    meta.update(finished_at=event["timestamp"], exit_code=exit_code)
    _write_meta(task_dir, meta)
    return exit_code
