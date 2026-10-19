"""Provas das recusas do `run` antes de lançar o agente (check C53; AC 47 sobre os AC 64, 65, 81, 82 e 90)."""

import os

import pytest
from conftest import Kit, default_config

ROUTINE_ROUTE = """
[routes.bot-r]
sinks = ["rotina"]

[sinks.rotina]
type = "grokbot-routine"
url_secret = "bot-r-url"
key_secret = "bot-r-key"
"""


def write_secret(kit: Kit, name: str, mode: int) -> None:
    secrets = kit.home / ".secrets" / "grokbot-kit"
    secrets.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = secrets / name
    path.write_text("valor-de-teste\n", encoding="utf-8")
    os.chmod(path, mode)


def arrange(kit: Kit, cause: str) -> list[str]:
    base = ["--target", "bot-a", "--label", "recusa"]
    if cause == "target inexistente (AC 64)":
        return ["--target", "bot-inexistente", "--label", "recusa", "--", "oi"]
    if cause.startswith("segredo"):
        kit.write_config(default_config(kit.sink) + ROUTINE_ROUTE)
        if cause == "segredo com modo 0644 (AC 65)":
            write_secret(kit, "bot-r-url", 0o600)
            write_secret(kit, "bot-r-key", 0o644)
        else:
            write_secret(kit, "bot-r-url", 0o600)
        return ["--target", "bot-r", "--label", "recusa", "--", "oi"]
    if cause == "modelo não descoberto (AC 81)":
        return ["--tool", "opencode", "--model", "inventado-123", *base, "--", "oi"]
    if cause == "tool não instalada (AC 82)":
        kit.write_config(default_config(kit.sink, installed=("opencode",)))
        return ["--tool", "codex", *base, "--", "oi"]
    if cause == "--bare com claude (AC 90)":
        return ["--tool", "claude", *base, "--", "--bare", "oi"]
    raise AssertionError(cause)


# C53 - AC 47
@pytest.mark.parametrize(
    "cause",
    [
        "target inexistente (AC 64)",
        "segredo ausente (AC 65)",
        "segredo com modo 0644 (AC 65)",
        "modelo não descoberto (AC 81)",
        "tool não instalada (AC 82)",
        "--bare com claude (AC 90)",
    ],
)
def test_exit_2_creates_no_task_dir(kit: Kit, cause: str) -> None:
    result = kit.run(*arrange(kit, cause))
    assert result.returncode == 2, result.stderr
    assert kit.tasks() == []
    assert not kit.sink.exists()
    assert not kit.record.exists(), "o agente foi lançado"


def test_exit_2_creates_no_task_dir_control_valid_secrets_launch(kit: Kit) -> None:
    kit.write_config(default_config(kit.sink) + ROUTINE_ROUTE)
    write_secret(kit, "bot-r-url", 0o600)
    write_secret(kit, "bot-r-key", 0o600)
    result = kit.run("--target", "bot-r", "--label", "aceita", "--", "oi")
    assert result.returncode == 0, result.stderr
    assert kit.record.exists()
    assert len(kit.tasks()) == 1
