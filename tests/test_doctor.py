"""Provas do `grokbot-kit doctor` (check C121; AC 100, door 21)."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from conftest import Kit, write_secret

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
    shebang = Path(exe).read_text(encoding="utf-8").splitlines()[0]
    python = shebang.removeprefix("#!").strip()
    code = "import platform; print(platform.python_version())"
    return subprocess.run([python, "-c", code], capture_output=True, text=True, check=True).stdout.strip()


def report(kit: Kit, **extra: str) -> tuple[int, dict[str, Any]]:
    result = run_doctor(kit, "--json", **extra)
    return result.returncode, json.loads(result.stdout)


# C121 - AC 100
def test_fields_and_exit_codes(kit: Kit) -> None:
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
