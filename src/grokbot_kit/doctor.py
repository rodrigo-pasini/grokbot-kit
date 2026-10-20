"""`grokbot-kit doctor [--json]`: versões, CLIs, login, padrão, tiers, rotas e segredos (AC 100, door 21)."""

import json
import os
import platform
import stat
import subprocess
import sys
from typing import Any

from grokbot_kit import config
from grokbot_kit.launch import TOOLS

TIERS = ("trivial", "standard", "complex")
STATUS_ARGV = {"claude": ["auth", "status"], "codex": ["login", "status"], "opencode": ["auth", "list"]}
COMMAND_TIMEOUT = 60
SECRET_KEYS = ("url_secret", "key_secret", "token_secret", "webhook_secret")


def _call(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            env=env,
            timeout=COMMAND_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _opencode_logged_in(proc: subprocess.CompletedProcess[str]) -> bool:
    # `opencode auth list` sai com 0 também sem login e termina com "<n> credentials"
    for line in reversed(proc.stdout.splitlines()):
        words = line.replace("└", " ").split()
        if len(words) >= 2 and words[-1] == "credentials" and words[-2].isdigit():
            return int(words[-2]) > 0
    return False


def _cli(tool: str, cli: dict[str, Any], default: str | None) -> dict[str, Any]:
    bin_path = os.path.expanduser(str(cli.get("bin", tool)))
    method = "api-key" if tool == "claude" and "api_key_secret" in cli else "subscription"
    try:
        env = {**os.environ, **config.cli_env(tool, cli)}
    except config.ConfigError:
        env = dict(os.environ)
    version = _call([bin_path, "--version"], env)
    status = _call([bin_path, *STATUS_ARGV[tool]], env)
    logged_in: bool | None
    if status is None:
        logged_in = None
    elif tool == "opencode":
        logged_in = _opencode_logged_in(status) if status.returncode == 0 else None
    else:
        logged_in = status.returncode == 0
    tiers = cli.get("tiers", {})
    return {
        "bin": bin_path,
        "version": (version.stdout.strip().splitlines() or [""])[0] if version and version.returncode == 0 else None,
        "default": tool == default,
        "login": {"command": " ".join([tool, *STATUS_ARGV[tool]]), "method": method, "logged_in": logged_in},
        "tiers": {tier: len(tiers.get(tier, [])) for tier in TIERS},
    }


def problems(out: dict[str, Any], facts: dict[str, Any]) -> list[str]:
    """O que precisa de correção, cada item com o comando que corrige; vazio quando tudo está OK (door 21)."""
    found = []
    setup = out["setup"]
    if not setup["installed"]:
        found.append("no CLI installed; run: grokbot-kit setup cli add <tool>")
    elif setup["default_cli"] is None:
        found.append("setup.default_cli is not set; run: grokbot-kit setup default <tool>")
    if facts.get("config_error"):
        found.append(str(facts["config_error"]))
    for tool, cli in out["cli"].items():
        if cli["version"] is None:
            found.append(f"{cli['bin']} --version failed; run: grokbot-kit setup cli add {tool}")
        logged_in = cli["login"]["logged_in"]
        if logged_in is None and tool == "opencode":
            found.append(f"{cli['login']['command']} failed")
        elif not logged_in and tool != "opencode":
            found.append(f"{tool} is not logged in; run: grokbot-kit login {tool}")
    mode = facts.get("secrets_dir_mode")
    if mode is not None and mode != 0o700:
        found.append(
            f"{config.secrets_dir()} has mode {mode:04o}, expected 0700; run: chmod 700 {config.secrets_dir()}"
        )
    for name, secret in out["secrets"].items():
        if not secret["ok"]:
            found.append(f"secret {name!r} has mode {secret['mode']}, expected 0600; run: chmod 600 {name}")
    for name in facts.get("missing_secrets", []):
        found.append(f"secret {name!r} is used in the config but not found; run: grokbot-kit secret set {name}")
    return found


def collect() -> tuple[dict[str, Any], dict[str, Any]]:
    from grokbot_kit import __version__

    facts: dict[str, Any] = {}
    cfg: dict[str, Any] = {}
    if config.config_path().exists():
        try:
            cfg = config.load(validate=False)
            config.check_constraints(cfg)
        except config.ConfigError as e:
            facts["config_error"] = str(e)
    setup = cfg.get("setup", {})
    installed = [t for t in setup.get("installed", []) if t in TOOLS]
    default = setup.get("default_cli")
    secrets: dict[str, Any] = {}
    directory = config.secrets_dir()
    if directory.is_dir():
        facts["secrets_dir_mode"] = stat.S_IMODE(directory.stat().st_mode)
        for path in sorted(directory.iterdir()):
            if path.is_file() and not path.name.startswith("."):
                mode = stat.S_IMODE(path.stat().st_mode)
                secrets[path.name] = {"mode": f"{mode:04o}", "ok": mode == 0o600}
    used = [sink[k] for sink in cfg.get("sinks", {}).values() for k in SECRET_KEYS if k in sink]
    used += [cli["api_key_secret"] for cli in cfg.get("cli", {}).values() if "api_key_secret" in cli]
    facts["missing_secrets"] = sorted({str(n) for n in used if str(n) not in secrets})
    out = {
        "ok": True,
        "problems": [],
        "kit": {"version": __version__},
        "python": {"version": platform.python_version(), "executable": sys.executable},
        "setup": {"installed": installed, "default_cli": default},
        "cli": {tool: _cli(tool, cfg.get("cli", {}).get(tool, {}), default) for tool in installed},
        "routes": {target: list(route.get("sinks", [])) for target, route in cfg.get("routes", {}).items()},
        "secrets": secrets,
    }
    return out, facts


def _text(out: dict[str, Any]) -> str:
    lines = [f"grokbot-kit {out['kit']['version']} (Python {out['python']['version']}, {out['python']['executable']})"]
    for tool, cli in out["cli"].items():
        login = cli["login"]
        state = {True: "logged in", False: "not logged in", None: "unknown"}[login["logged_in"]]
        tiers = ", ".join(f"{t} {n}" for t, n in cli["tiers"].items())
        default = " (default)" if cli["default"] else ""
        lines.append(f"{tool}{default}: {cli['version'] or 'version unknown'} at {cli['bin']}")
        lines.append(f"  login: {state} ({login['method']}, {login['command']}); tiers: {tiers}")
    for target, sinks in out["routes"].items():
        lines.append(f"route {target}: {', '.join(sinks)}")
    for name, secret in out["secrets"].items():
        lines.append(f"secret {name}: {secret['mode']}")
    lines += [f"problem: {p}" for p in out["problems"]] or ["ok"]
    return "\n".join(lines)


def doctor(as_json: bool) -> int:
    out, facts = collect()
    out["problems"] = problems(out, facts)
    out["ok"] = not out["problems"]
    print(json.dumps(out, ensure_ascii=False, indent=2) if as_json else _text(out))
    return 0 if out["ok"] else 1
