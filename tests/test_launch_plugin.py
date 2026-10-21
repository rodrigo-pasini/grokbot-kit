"""Provas do harness por CLI (checks C36 e C39; AC 34-38 e 40, door 8).

C39: sem `--plugin`, o argv e o `claude-settings.json` são os de antes desta feature, literais. C36 (o harness de
cada CLI a partir das capacidades) entra quando a matriz da door 8 estiver provada no box (S1).
"""

from pathlib import Path

from grokbot_kit import launch

EXE = "/opt/gk/grokbot-kit"


# C39 - AC 40
def test_argv_without_plugin_matches_baseline(tmp_path: Path) -> None:
    assert launch.agent_argv("claude", "/bin/claude", "sonnet", tmp_path, EXE, ["oi"]) == [
        "/bin/claude",
        "-p",
        "--output-format",
        "json",
        "--model",
        "sonnet",
        "--settings",
        str(tmp_path / "claude-settings.json"),
        "oi",
    ]
    assert launch.agent_argv("opencode", "/bin/opencode", "opencode/m", tmp_path, EXE, ["oi"]) == [
        "/bin/opencode",
        "run",
        "--format",
        "json",
        "-m",
        "opencode/m",
        "oi",
    ]
    assert launch.agent_argv("codex", "/bin/codex", "gpt-x", tmp_path, EXE, ["oi"]) == [
        "/bin/codex",
        "exec",
        "--json",
        "-m",
        "gpt-x",
        "-o",
        str(tmp_path / "last-message.txt"),
        "--dangerously-bypass-hook-trust",
        "-c",
        'hooks.PermissionRequest=[{hooks=[{type="command",command="/opt/gk/grokbot-kit emit --from codex"}]}]',
        "oi",
    ]
    hook = {"type": "command", "command": f"{EXE} emit --from claude"}
    assert launch.claude_settings(EXE) == {"hooks": {"PermissionRequest": [{"matcher": "*", "hooks": [hook]}]}}
