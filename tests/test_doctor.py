"""Provas do `grokbot-kit doctor` (checks C121 e C150; AC 100 e 126, doors 21 e 24)."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from conftest import Kit, default_config, write_secret

from grokbot_kit import __version__, doctor

STATUS_COMMAND = {"claude": "claude auth status", "codex": "codex login status", "opencode": "opencode auth list"}


def run_doctor(kit: Kit, *args: str, **extra: str) -> subprocess.CompletedProcess[str]:
    saved = kit.env
    kit.env = {**saved, "FAKE_CALLS": str(kit.home.parent / "calls.jsonl"), "FAKE_OPENCODE_CREDENTIALS": "2", **extra}
    try:
        return kit.cli("doctor", *args)
    finally:
        kit.env = saved


def kit_python_version() -> str:
    exe = shutil.which("grokbot-kit")
    assert exe is not None
    # o console script fica no `bin/` do venv ao lado do `python`; ler o shebang falha quando o caminho é longo e o
    # launcher vira `#!/bin/sh` com o interpretador na segunda linha
    python = str(Path(exe).parent / "python")
    code = "import platform; print(platform.python_version())"
    return subprocess.run([python, "-c", code], capture_output=True, text=True, check=True).stdout.strip()


def report(kit: Kit, **extra: str) -> tuple[int, dict[str, Any]]:
    result = run_doctor(kit, "--json", **extra)
    return result.returncode, json.loads(result.stdout)


# C121 - AC 100 (o "tudo OK" inclui o plugin do opencode instalado, door 24)
def test_fields_and_exit_codes(kit: Kit) -> None:
    assert kit.cli("install", "opencode").returncode == 0
    write_secret(kit.home, "bot-a-key", "crsr_x\n")
    code, out = report(kit)
    assert code == 0, out
    assert out["ok"] is True
    assert out["problems"] == []
    assert out["kit"]["version"] == __version__
    assert out["python"]["version"] == kit_python_version()
    assert os.path.isabs(out["python"]["executable"])
    assert out["setup"] == {"installed": ["opencode", "claude", "codex"], "default_cli": "opencode"}
    assert set(out["cli"]) == {"opencode", "claude", "codex"}
    for tool, cli in out["cli"].items():
        assert cli["version"] == f"9.9.9 ({tool} fake)"
        assert cli["login"]["command"] == STATUS_COMMAND[tool]
        assert cli["login"]["logged_in"] is True
        assert cli["login"]["method"] == "subscription"
        assert cli["default"] is (tool == "opencode")
        assert cli["tiers"] == {"trivial": 0, "standard": 1, "complex": 0}
    assert out["routes"] == {"bot-a": ["arquivo"]}
    assert out["secrets"] == {"bot-a-key": {"mode": "0600", "ok": True}}

    calls = [json.loads(line) for line in (kit.home.parent / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
    codex_status = [c for c in calls if c["tool"] == "codex" and c["argv"] == ["login", "status"]]
    assert codex_status
    assert codex_status[0]["codex_home"] == str(kit.home / ".grokbot-kit" / "codex-home")

    text = run_doctor(kit)
    assert text.returncode == 0
    assert __version__ in text.stdout
    assert "9.9.9 (claude fake)" in text.stdout


def test_fields_and_exit_codes_open_secret(kit: Kit) -> None:
    write_secret(kit.home, "bot-a-key", "crsr_x\n", mode=0o644)
    code, out = report(kit)
    assert code == 1
    assert out["ok"] is False
    assert out["secrets"]["bot-a-key"] == {"mode": "0644", "ok": False}
    assert any("bot-a-key" in p for p in out["problems"])
    assert run_doctor(kit).returncode == 1


@pytest.mark.parametrize("tool", ["claude", "codex"])
def test_fields_and_exit_codes_logged_out(kit: Kit, tool: str) -> None:
    code, out = report(kit, FAKE_LOGGED_OUT=tool)
    assert code == 1
    assert out["cli"][tool]["login"]["logged_in"] is False
    assert any(tool in p and "grokbot-kit login" in p for p in out["problems"])


def test_fields_and_exit_codes_opencode_free(kit: Kit) -> None:
    assert kit.cli("install", "opencode").returncode == 0
    code, out = report(kit, FAKE_OPENCODE_CREDENTIALS="0")
    assert code == 0, out
    assert out["cli"]["opencode"]["login"]["logged_in"] is False


def test_fields_and_exit_codes_empty_box(tmp_path: Path, fresh: Kit) -> None:
    result = fresh.cli("doctor", "--json")
    assert result.returncode == 1
    out = json.loads(result.stdout)
    assert out["setup"] == {"installed": [], "default_cli": None}
    assert out["cli"] == {}
    assert any("grokbot-kit setup cli add" in p for p in out["problems"])


def cli_entry(**over: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "bin": "/x",
        "version": "1.0",
        "default": True,
        "login": {"command": "claude auth status", "method": "subscription", "logged_in": True},
        "tiers": {"trivial": 0, "standard": 1, "complex": 0},
    }
    entry.update(over)
    return entry


def base(**over: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        "setup": {"installed": ["claude"], "default_cli": "claude"},
        "cli": {"claude": cli_entry()},
        "secrets": {},
    }
    out.update(over)
    return out


@pytest.mark.parametrize(
    ("out", "facts", "expect"),
    [
        (base(), {}, None),
        (base(setup={"installed": [], "default_cli": None}, cli={}), {}, "setup cli add"),
        (base(setup={"installed": ["claude"], "default_cli": None}), {}, "setup default"),
        (base(), {"config_error": "cli.claude.tiers.standard has 'x'"}, "cli.claude.tiers.standard"),
        (base(cli={"claude": cli_entry(version=None)}), {}, "--version"),
        (
            base(cli={"claude": cli_entry(login={"command": "c", "method": "subscription", "logged_in": False})}),
            {},
            "grokbot-kit login claude",
        ),
        (
            base(
                cli={
                    "opencode": cli_entry(
                        login={"command": "opencode auth list", "method": "subscription", "logged_in": None}
                    )
                },
                setup={"installed": ["opencode"], "default_cli": "opencode"},
            ),
            {},
            "opencode auth list",
        ),
        (
            base(
                cli={
                    "opencode": cli_entry(
                        login={"command": "opencode auth list", "method": "subscription", "logged_in": False}
                    )
                },
                setup={"installed": ["opencode"], "default_cli": "opencode"},
            ),
            {},
            None,
        ),
        (base(), {"secrets_dir_mode": 0o755}, "0700"),
        (base(secrets={"k": {"mode": "0640", "ok": False}}), {}, "k"),
        (base(), {"missing_secrets": ["bot-url"]}, "bot-url"),
    ],
)
def test_fields_and_exit_codes_layer(out: dict[str, Any], facts: dict[str, Any], expect: str | None) -> None:
    found = doctor.problems(out, facts)
    if expect is None:
        assert found == []
    else:
        assert len(found) == 1, found
        assert expect in found[0]


def plugin_file(kit: Kit) -> Path:
    return kit.home / ".config" / "opencode" / "plugins" / "grokbot-kit.ts"


# C150 - AC 126, door 24
def test_opencode_plugin_installed(kit: Kit) -> None:
    assert kit.cli("install", "opencode").returncode == 0
    code, out = report(kit)
    assert code == 0, out
    plugin = out["cli"]["opencode"]["plugin"]
    assert plugin["path"] == str(plugin_file(kit))
    assert plugin["ok"] is True
    assert isinstance(plugin["exe"], str) and os.path.isabs(plugin["exe"])
    assert not any("plugin" in p for p in out["problems"])
    assert "plugin: ok" in run_doctor(kit).stdout


def test_opencode_plugin_missing(kit: Kit) -> None:
    code, out = report(kit)
    assert code == 1
    plugin = out["cli"]["opencode"]["plugin"]
    assert plugin == {"path": str(plugin_file(kit)), "exe": None, "ok": False}
    found = [p for p in out["problems"] if "plugin" in p]
    assert len(found) == 1 and "grokbot-kit install opencode" in found[0]
    assert "plugin: missing" in run_doctor(kit).stdout


def test_opencode_plugin_other_executable(kit: Kit) -> None:
    assert kit.cli("install", "opencode").returncode == 0
    path = plugin_file(kit)
    current = report(kit)[1]["cli"]["opencode"]["plugin"]["exe"]
    text = path.read_text(encoding="utf-8")
    assert text.count(json.dumps(current)) == 1
    path.write_text(text.replace(json.dumps(current), json.dumps("/old/bin/grokbot-kit")), encoding="utf-8")
    code, out = report(kit)
    assert code == 1
    plugin = out["cli"]["opencode"]["plugin"]
    assert plugin["exe"] == "/old/bin/grokbot-kit"
    assert plugin["ok"] is False
    found = [p for p in out["problems"] if "plugin" in p]
    assert len(found) == 1
    assert "/old/bin/grokbot-kit" in found[0] and "grokbot-kit install opencode" in found[0]
    assert "plugin: stale" in run_doctor(kit).stdout


# C151 - AC 126, door 24
@pytest.mark.parametrize("case", ["sem a linha", "valor não string", "valor não JSON", "ilegível"])
def test_plugin_without_exe_line(kit: Kit, case: str) -> None:
    assert kit.cli("install", "opencode").returncode == 0
    path = plugin_file(kit)
    lines = path.read_text(encoding="utf-8").splitlines()
    exe_line = [i for i, line in enumerate(lines) if line.startswith("const GROKBOT_KIT = ")]
    assert len(exe_line) == 1
    if case == "sem a linha":
        del lines[exe_line[0]]
    elif case == "valor não string":
        lines[exe_line[0]] = "const GROKBOT_KIT = 42"
    elif case == "valor não JSON":
        lines[exe_line[0]] = "const GROKBOT_KIT = process.env.GROKBOT_KIT"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if case == "ilegível":
        path.chmod(0)
    code, out = report(kit)
    assert code == 1
    plugin = out["cli"]["opencode"]["plugin"]
    assert plugin["exe"] is None
    assert plugin["ok"] is False
    found = [p for p in out["problems"] if "plugin" in p]
    assert len(found) == 1 and "grokbot-kit install opencode" in found[0]


def test_opencode_plugin_not_installed_tool(kit: Kit) -> None:
    kit.write_config(default_config(kit.sink, installed=("claude",)))
    code, out = report(kit)
    assert code == 0, out
    assert all("plugin" not in cli for cli in out["cli"].values())
    assert not any("plugin" in p for p in out["problems"])
