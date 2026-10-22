"""Provas do evento terminal do `run` (checks C46-C52, C54; AC 43-48, door 5).

Cada linha da tabela de status é provada na própria camada (`terminal.classify`, `terminal.read_output`) e na
fronteira (subprocesso `grokbot-kit run` com a CLI falsa).
"""

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import Kit

from grokbot_kit import terminal
from grokbot_kit.terminal import AgentOutput

TERMINAL_EVENTS = {"completed", "error", "timeout"}

CLAUDE_OK = json.dumps(
    {"type": "result", "subtype": "success", "is_error": False, "result": "feito", "permission_denials": []}
)
OPENCODE_OK = json.dumps({"type": "text", "sessionID": "ses_1", "part": {"type": "text", "text": "feito"}}) + "\n"
CODEX_OK = json.dumps({"type": "thread.started", "thread_id": "t1"}) + "\n" + json.dumps({"type": "turn.completed"})

CLEAN = AgentOutput(error=False, permission_denied=False, summary="")


def opencode_text(*texts: str) -> str:
    return "".join(json.dumps({"type": "text", "part": {"type": "text", "text": t}}) + "\n" for t in texts)


def run_task_with(kit: Kit, tool: str, fake: dict[str, str]) -> tuple[int, dict[str, Any]]:
    result = kit.run("--tool", tool, "--target", "bot-a", "--label", "t", "--", "faça", **fake)
    events = kit.sink_events()
    assert len(events) == 1, (events, result.stderr)
    return result.returncode, events[0]


def outcome(event: dict[str, Any]) -> tuple[str, str, str]:
    return event["event"], event["status"], event["exit_reason"]


# C46 - AC 43
def test_ok_on_clean_exit_layer() -> None:
    assert terminal.classify(0, CLEAN, needs_input=False) == ("completed", "ok", "success")


@pytest.mark.parametrize(("tool", "stdout"), [("claude", CLAUDE_OK), ("opencode", OPENCODE_OK), ("codex", CODEX_OK)])
def test_ok_on_clean_exit_cli(kit: Kit, tool: str, stdout: str) -> None:
    code, event = run_task_with(kit, tool, {"FAKE_STDOUT": stdout, "FAKE_LAST_MESSAGE": "feito"})
    assert outcome(event) == ("completed", "ok", "success")
    assert code == 0
    assert event["task_id"] == kit.task_dir().name
    assert event["target"] == "bot-a"
    assert event["tool"] == tool


# C47 - AC 44
def test_denied_on_recorded_needs_input_layer() -> None:
    assert terminal.classify(0, CLEAN, needs_input=True) == ("completed", "denied", "permission_denied")


@pytest.mark.parametrize(("tool", "stdout"), [("claude", CLAUDE_OK), ("opencode", OPENCODE_OK), ("codex", CODEX_OK)])
def test_denied_on_recorded_needs_input_cli(kit: Kit, tool: str, stdout: str) -> None:
    code, event = run_task_with(kit, tool, {"FAKE_STDOUT": stdout, "FAKE_NEEDS_INPUT": "1"})
    assert outcome(event) == ("completed", "denied", "permission_denied")
    assert code == 0


# C48 - AC 44
def test_denied_on_claude_permission_denials_layer(tmp_path: Path) -> None:
    out = {"type": "result", "is_error": False, "result": "não deu", "permission_denials": [{"tool_name": "Bash"}]}
    (tmp_path / "out.jsonl").write_text(json.dumps(out), encoding="utf-8")
    output = terminal.read_output("claude", tmp_path)
    assert output.permission_denied is True
    assert output.error is False
    assert terminal.classify(0, output, needs_input=False) == ("completed", "denied", "permission_denied")


def test_denied_on_claude_permission_denials_cli(kit: Kit) -> None:
    stdout = json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "não deu",
            "permission_denials": [{"tool_name": "Bash", "tool_use_id": "tu_1", "tool_input": {"command": "touch x"}}],
        }
    )
    code, event = run_task_with(kit, "claude", {"FAKE_STDOUT": stdout})
    assert outcome(event) == ("completed", "denied", "permission_denied")
    assert code == 0


# C49 - AC 45: exit != 0 sem erro na saída, mais as 4 formas de erro na saída
ERROR_OUTPUTS = {
    "claude is_error": ("claude", json.dumps({"type": "result", "is_error": True, "result": "falhou"})),
    "codex turn.failed": ("codex", json.dumps({"type": "turn.failed", "error": {"message": "boom"}})),
    "codex error": ("codex", json.dumps({"type": "error", "message": "boom"})),
    "opencode error": ("opencode", json.dumps({"type": "error", "error": {"name": "UnknownError"}})),
}


@pytest.mark.parametrize("case", sorted(ERROR_OUTPUTS))
def test_error_table_all_5_conditions_output_layer(tmp_path: Path, case: str) -> None:
    tool, stdout = ERROR_OUTPUTS[case]
    (tmp_path / "out.jsonl").write_text(stdout + "\n", encoding="utf-8")
    output = terminal.read_output(tool, tmp_path)
    assert output.error is True
    assert terminal.classify(0, output, needs_input=False) == ("error", "failed", "agent_error")
    assert terminal.classify(1, output, needs_input=False) == ("error", "failed", "agent_error")


def test_error_table_all_5_conditions_nonzero_layer() -> None:
    assert terminal.classify(1, CLEAN, needs_input=False) == ("error", "failed", "nonzero_exit")
    assert terminal.classify(3, CLEAN, needs_input=True) == ("error", "failed", "nonzero_exit")


@pytest.mark.parametrize("case", sorted(ERROR_OUTPUTS))
def test_error_table_all_5_conditions_output_cli(kit: Kit, case: str) -> None:
    tool, stdout = ERROR_OUTPUTS[case]
    code, event = run_task_with(kit, tool, {"FAKE_STDOUT": stdout})
    assert outcome(event) == ("error", "failed", "agent_error")
    assert code == 0


def test_error_table_all_5_conditions_nonzero_cli(kit: Kit) -> None:
    code, event = run_task_with(kit, "opencode", {"FAKE_STDOUT": OPENCODE_OK, "FAKE_EXIT": "1"})
    assert outcome(event) == ("error", "failed", "nonzero_exit")
    assert event["exit_code"] == 1
    assert code == 1


# C50 - AC 45 sobre AC 44
def test_error_wins_over_needs_input_layer() -> None:
    err = AgentOutput(error=True, permission_denied=True, summary="")
    assert terminal.classify(0, err, needs_input=True) == ("error", "failed", "agent_error")


def test_error_wins_over_needs_input_cli(kit: Kit) -> None:
    stdout = json.dumps({"type": "error", "error": {"name": "UnknownError"}})
    code, event = run_task_with(kit, "opencode", {"FAKE_STDOUT": stdout, "FAKE_NEEDS_INPUT": "1"})
    assert outcome(event) == ("error", "failed", "agent_error")
    assert code == 0


# C51 - AC 46
def write_summary_source(task_dir: Path, tool: str, text: str) -> None:
    if tool == "claude":
        out = json.dumps({"type": "result", "is_error": False, "result": text, "permission_denials": []})
    elif tool == "opencode":
        out = opencode_text("rascunho", text)
    else:
        out = CODEX_OK
        (task_dir / "last-message.txt").write_text(text, encoding="utf-8")
    (task_dir / "out.jsonl").write_text(out, encoding="utf-8")


@pytest.mark.parametrize("tool", ["claude", "opencode", "codex"])
@pytest.mark.parametrize(("size", "expected"), [(1999, 1999), (2000, 2000), (2001, 2000)])
def test_summary_source_per_tool_and_2000_bound_layer(tmp_path: Path, tool: str, size: int, expected: int) -> None:
    text = "é" * (size - 1) + "z"
    write_summary_source(tmp_path, tool, text)
    assert terminal.read_output(tool, tmp_path).summary == text[:expected]


@pytest.mark.parametrize("tool", ["claude", "opencode", "codex"])
def test_summary_source_per_tool_and_2000_bound_cli(kit: Kit, tool: str) -> None:
    text = "r" * 2001
    if tool == "claude":
        fake = {"FAKE_STDOUT": json.dumps({"type": "result", "is_error": False, "result": text})}
    elif tool == "opencode":
        fake = {"FAKE_STDOUT": opencode_text("rascunho", text)}
    else:
        fake = {"FAKE_STDOUT": CODEX_OK, "FAKE_LAST_MESSAGE": text}
    _, event = run_task_with(kit, tool, fake)
    assert event["summary"] == "r" * 2000


# C52 - AC 47, door 5
EMIT_TERMINAL_ATTEMPTS = [
    {"event": "completed"},
    {"event": "error"},
    {"event": "timeout"},
    {"hook_event_name": "Stop"},
    {"hook_event_name": "SessionEnd"},
    {"type": "session.idle"},
]


@pytest.mark.parametrize("tool", ["claude", "opencode", "codex"])
def test_exactly_one_terminal_per_task(kit: Kit, tool: str) -> None:
    result = kit.run(
        "--tool", tool, "--target", "bot-a", "--label", "um", "--", "faça", FAKE_EMIT=json.dumps(EMIT_TERMINAL_ATTEMPTS)
    )
    assert result.returncode == 0, result.stderr
    task_dir = kit.task_dir()
    sunk = [e for e in kit.sink_events() if e["event"] in TERMINAL_EVENTS]
    assert len(sunk) == 1
    assert sunk[0]["task_id"] == task_dir.name
    records = [json.loads(line) for line in (task_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["event"]["event"] for r in records if r["event"]["event"] in TERMINAL_EVENTS] == [sunk[0]["event"]]


# C54 - AC 48
@pytest.mark.parametrize("code", [0, 1, 3])
def test_run_exit_mirrors_agent(kit: Kit, code: int) -> None:
    result = kit.run(
        "--tool",
        "opencode",
        "--target",
        "bot-a",
        "--label",
        "x",
        "--",
        "faça",
        FAKE_STDOUT=OPENCODE_OK,
        FAKE_EXIT=str(code),
    )
    assert result.returncode == code, result.stderr
    assert kit.sink_events()[0]["exit_code"] == code


# C43 - AC 44
def test_plugin_task_never_denied() -> None:
    denied = AgentOutput(error=False, permission_denied=True, summary="")
    for needs_input in (False, True):
        assert terminal.classify(0, denied, needs_input=needs_input, plugin=True, result_valid=True) == (
            "completed",
            "ok",
            "success",
        )
        assert terminal.classify(0, denied, needs_input=needs_input, plugin=True, result_valid=False) == (
            "error",
            "failed",
            "result_invalid",
        )
    assert terminal.classify(0, denied, needs_input=False) == ("completed", "denied", "permission_denied")


# C44 - AC 45: a mesma precedência de hoje antes do resultado, que só decide quando o agente saiu limpo
PLUGIN_PRECEDENCE = [
    ("timeout", 124, CLEAN, "timeout", True, ("timeout", "timeout", "timeout")),
    ("interrompida", 130, CLEAN, "interrupted", True, ("error", "interrupted", "interrupted")),
    (
        "binario_ausente",
        127,
        AgentOutput(error=True, permission_denied=False, summary=""),
        None,
        True,
        ("error", "failed", "agent_error"),
    ),
    (
        "erro_do_agente",
        0,
        AgentOutput(error=True, permission_denied=False, summary=""),
        None,
        True,
        ("error", "failed", "agent_error"),
    ),
    ("exit_diferente_de_0", 3, CLEAN, None, True, ("error", "failed", "nonzero_exit")),
    ("resultado_invalido", 0, CLEAN, None, False, ("error", "failed", "result_invalid")),
    (
        "negacao_com_resultado_valido",
        0,
        AgentOutput(error=False, permission_denied=True, summary=""),
        None,
        True,
        ("completed", "ok", "success"),
    ),
]


@pytest.mark.parametrize(
    ("case", "code", "output", "stopped", "valid", "expected"), PLUGIN_PRECEDENCE, ids=[r[0] for r in PLUGIN_PRECEDENCE]
)
def test_plugin_precedence_table(
    case: str, code: int, output: AgentOutput, stopped: str | None, valid: bool, expected: tuple[str, str, str]
) -> None:
    got = terminal.classify(code, output, needs_input=True, stopped=stopped, plugin=True, result_valid=valid)
    assert got == expected
