"""Provas do `setup tiers <tool> <tier> <id>...` (door 22; a skill aplica a tabela de tiers do AC 109)."""

import json

import pytest
from conftest import Kit, default_config

OPENCODE_MODELS = ["opencode/a-free", "opencode/b-free", "provider/pago"]


def with_models(kit: Kit, installed: tuple[str, ...] = ("opencode", "claude", "codex")) -> None:
    text = default_config(kit.sink, installed).replace(
        'models = ["opencode/free-model"]', f"models = {json.dumps(OPENCODE_MODELS)}"
    )
    kit.write_config(text.replace('standard = ["opencode/free-model"]', 'standard = ["provider/pago"]'))


def test_setup_tiers_writes_ordered_list(kit: Kit) -> None:
    with_models(kit)
    before = kit.config()
    result = kit.cli("setup", "tiers", "opencode", "trivial", "opencode/b-free", "opencode/a-free")
    assert result.returncode == 0, result.stderr
    assert len(result.stdout.strip().splitlines()) == 1
    after = kit.config()
    assert after["cli"]["opencode"]["tiers"]["trivial"] == ["opencode/b-free", "opencode/a-free"]
    assert after["cli"]["opencode"]["tiers"]["standard"] == ["provider/pago"]
    assert after["cli"]["opencode"]["models"] == OPENCODE_MODELS
    del after["cli"]["opencode"]["tiers"]["trivial"]
    assert after == before


def test_setup_tiers_replaces_existing_tier(kit: Kit) -> None:
    with_models(kit)
    result = kit.cli("setup", "tiers", "opencode", "standard", "opencode/a-free", "provider/pago")
    assert result.returncode == 0, result.stderr
    assert kit.config()["cli"]["opencode"]["tiers"]["standard"] == ["opencode/a-free", "provider/pago"]


def test_setup_tiers_refuses_undiscovered_id(kit: Kit) -> None:
    with_models(kit)
    before = kit.config_text()
    result = kit.cli("setup", "tiers", "opencode", "trivial", "opencode/a-free", "inventado-123")
    assert result.returncode == 2
    assert "inventado-123" in result.stderr
    assert "grokbot-kit setup models refresh opencode" in result.stderr
    assert kit.config_text() == before


def test_setup_tiers_refuses_tool_not_installed(kit: Kit) -> None:
    with_models(kit, installed=("opencode",))
    before = kit.config_text()
    result = kit.cli("setup", "tiers", "claude", "standard", "sonnet")
    assert result.returncode == 2
    assert "grokbot-kit setup cli add claude" in result.stderr
    assert kit.config_text() == before


@pytest.mark.parametrize(
    "args",
    [
        ("aider", "standard", "x"),
        ("opencode", "huge", "opencode/a-free"),
        ("opencode", "trivial"),
    ],
)
def test_setup_tiers_usage_errors(kit: Kit, args: tuple[str, ...]) -> None:
    with_models(kit)
    before = kit.config_text()
    assert kit.cli("setup", "tiers", *args).returncode == 2
    assert kit.config_text() == before
