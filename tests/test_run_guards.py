"""Provas das recusas do `run` antes de lançar o agente (check C53; AC 47 sobre os AC 64, 65, 81, 82 e 90)."""

import os
import tomllib
from collections.abc import Callable
from typing import Any

import pytest
from conftest import Kit, default_config

from grokbot_kit import config, resolve

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


SINK_SECRETS = """
[routes.bot-s]
sinks = ["rotina-s", "avisos", "canal"]

[sinks.rotina-s]
type = "grokbot-routine"
url_secret = "s-url"
key_secret = "s-key"

[sinks.avisos]
type = "ntfy"
topic_url = "https://ntfy.example/topico"
token_secret = "s-ntfy"

[sinks.canal]
type = "slack"
webhook_secret = "s-slack"
"""


# C76 - AC 64
def test_unknown_target_exit_2(kit: Kit) -> None:
    result = kit.run("--target", "bot-inexistente", "--label", "alvo", "--", "oi")
    assert result.returncode == 2
    assert "bot-inexistente" in result.stderr
    assert not kit.record.exists(), "o agente foi lançado"
    assert kit.tasks() == []


def test_unknown_target_exit_2_control_known_target_launches(kit: Kit) -> None:
    result = kit.run("--target", "bot-a", "--label", "alvo", "--", "oi")
    assert result.returncode == 0, result.stderr
    assert kit.record.exists()


# C77 - AC 65: cada segredo referenciado pela rota (url, key, token do ntfy, webhook do slack)
@pytest.mark.parametrize("secret", ["s-url", "s-key", "s-ntfy", "s-slack"])
@pytest.mark.parametrize("problem", ["ausente", "0644", "0640", "0400"])
def test_secret_missing_or_wrong_mode_exit_2(kit: Kit, secret: str, problem: str) -> None:
    kit.write_config(default_config(kit.sink) + SINK_SECRETS)
    for name in ("s-url", "s-key", "s-ntfy", "s-slack"):
        if name != secret:
            write_secret(kit, name, 0o600)
        elif problem != "ausente":
            write_secret(kit, name, int(problem, 8))
    result = kit.run("--target", "bot-s", "--label", "segredo", "--", "oi")
    assert result.returncode == 2
    assert secret in result.stderr
    assert "valor-de-teste" not in result.stderr + result.stdout
    assert not kit.record.exists(), "o agente foi lançado"
    assert kit.tasks() == []


def test_secret_missing_or_wrong_mode_exit_2_control_0600_launches(kit: Kit) -> None:
    kit.write_config(default_config(kit.sink) + SINK_SECRETS)
    for name in ("s-url", "s-key", "s-ntfy", "s-slack"):
        write_secret(kit, name, 0o600)
    result = kit.run("--target", "bot-s", "--label", "segredo", "--", "oi")
    assert kit.record.exists(), result.stderr
    assert len(kit.tasks()) == 1


def config_with(kit: Kit, mutate: Callable[[dict[str, Any]], None]) -> None:
    cfg = tomllib.loads(default_config(kit.sink))
    mutate(cfg)
    kit.write_config(config.dump(cfg))


# C101 - AC 81: o modelo resolvido, venha de `--model` ou do tier, precisa estar na lista descoberta
@pytest.mark.parametrize("origin", ["--model", "tier"])
@pytest.mark.parametrize("tool", ["opencode", "claude", "codex"])
def test_undiscovered_model_exit_2(kit: Kit, tool: str, origin: str) -> None:
    if origin == "tier":
        config_with(kit, lambda c: c["cli"][tool]["tiers"].update(standard=["inventado-123"]))
        args = ["--tool", tool]
    else:
        args = ["--tool", tool, "--model", "inventado-123"]
    result = kit.run(*args, "--target", "bot-a", "--label", "modelo", "--", "oi")
    assert result.returncode == 2
    assert f"grokbot-kit setup models refresh {tool}" in result.stderr
    assert not kit.record.exists(), "o agente foi lançado"
    assert kit.tasks() == []


def test_undiscovered_model_exit_2_resolve_layer(kit: Kit) -> None:
    cfg = tomllib.loads(default_config(kit.sink))
    with pytest.raises(resolve.ResolveError) as raised:
        resolve.resolve(cfg, tool="codex", model="inventado-123", tier=None, timeout=None)
    assert "grokbot-kit setup models refresh codex" in str(raised.value)
    cfg["cli"]["claude"]["tiers"]["standard"] = ["inventado-123"]
    with pytest.raises(resolve.ResolveError) as raised:
        resolve.resolve(cfg, tool="claude", model=None, tier=None, timeout=None)
    assert "grokbot-kit setup models refresh claude" in str(raised.value)


def test_undiscovered_model_exit_2_control_discovered_launches(kit: Kit) -> None:
    result = kit.run("--tool", "codex", "--model", "gpt-test", "--target", "bot-a", "--label", "modelo", "--", "oi")
    assert result.returncode == 0, result.stderr
    assert kit.record.exists()


# C102 - AC 82: pela `--tool` ou pela `default_cli`
@pytest.mark.parametrize("via", ["--tool", "default_cli"])
def test_tool_not_installed_exit_2(kit: Kit, via: str) -> None:
    def mutate(c: dict[str, Any]) -> None:
        c["setup"]["installed"] = ["opencode"]
        if via == "default_cli":
            c["setup"]["default_cli"] = "codex"

    config_with(kit, mutate)
    args = ["--tool", "codex"] if via == "--tool" else []
    result = kit.run(*args, "--target", "bot-a", "--label", "instalada", "--", "oi")
    assert result.returncode == 2
    assert "codex" in result.stderr
    assert not kit.record.exists(), "o agente foi lançado"
    assert kit.tasks() == []


def test_tool_not_installed_exit_2_resolve_layer(kit: Kit) -> None:
    cfg = tomllib.loads(default_config(kit.sink, installed=("opencode",)))
    with pytest.raises(resolve.ResolveError) as raised:
        resolve.resolve(cfg, tool="claude", model=None, tier=None, timeout=None)
    assert "setup.installed" in str(raised.value)
    assert resolve.resolve(cfg, tool="opencode", model=None, tier=None, timeout=None).tool == "opencode"


def test_tool_not_installed_exit_2_control_installed_launches(kit: Kit) -> None:
    config_with(kit, lambda c: c["setup"].update(installed=["opencode", "codex"]))
    result = kit.run("--tool", "codex", "--target", "bot-a", "--label", "instalada", "--", "oi")
    assert result.returncode == 0, result.stderr
    assert kit.launched()["tool"] == "codex"
