"""Provas do S8 sobre o `skills/grokbot-kit/SKILL.md` (checks C126-C145; AC 102-119, doors 8 e 22).

As provas são do nível do documento: afirmam o que o `SKILL.md` instrui, não o que um bot faz com ele.
"""

import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "grokbot-kit" / "SKILL.md"


def text() -> str:
    return SKILL.read_text(encoding="utf-8")


def frontmatter() -> dict[str, Any]:
    match = re.match(r"^---\n(.*?)\n---\n", text(), re.DOTALL)
    assert match, "SKILL.md sem frontmatter"
    data: dict[str, Any] = yaml.safe_load(match.group(1))
    return data


def body() -> str:
    return text().split("\n---\n", 1)[1]


def section(heading: str) -> str:
    """O trecho de um título (`#`, `##` ou `###`) cujo texto contém `heading` até o próximo título de nível igual ou acima."""
    lines = body().splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#+) (.*)$", line)
        if m and heading.lower() in m.group(2).lower():
            level = len(m.group(1))
            end = next(
                (j for j in range(i + 1, len(lines)) if re.match(rf"^#{{1,{level}}} ", lines[j])),
                len(lines),
            )
            return "\n".join(lines[i:end])
    raise AssertionError(f"sem título com {heading!r}")


def paragraph_with(needle: str) -> str:
    """O parágrafo (ou item de lista) do corpo que contém `needle`."""
    for block in re.split(r"\n\s*\n|\n(?=\s*(?:[-*]|\d+\.) )", body()):
        if needle in block:
            return block
    raise AssertionError(f"nenhum parágrafo com {needle!r}")


def fenced(lang: str | None = None) -> list[str]:
    blocks = re.findall(r"^```([\w-]*)\n(.*?)^```", body(), re.DOTALL | re.MULTILINE)
    return [code for tag, code in blocks if lang is None or tag == lang]


def sh_commands() -> list[str]:
    return [line.strip() for code in fenced("sh") for line in code.splitlines() if line.strip()]


def cited_commands() -> list[str]:
    """Cada `grokbot-kit ...` citado em código: spans inline e linhas dos blocos `sh`."""
    spans = re.findall(r"`([^`\n]+)`", re.sub(r"^```.*?^```", "", body(), flags=re.DOTALL | re.MULTILINE))
    found = [s for s in spans + sh_commands() if s.startswith("grokbot-kit ")]
    return found


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s)


# C126 - AC 102, door 8
def test_frontmatter_name_and_triggers() -> None:
    fm = frontmatter()
    assert fm["name"] == "grokbot-kit"
    for trigger in ("configurar grokbot-kit", "delegar para opencode/claude/codex", "rodar tarefa headless"):
        assert f'"{trigger}"' in fm["description"], trigger


# C127 - AC 103
def test_install_first_step() -> None:
    first = paragraph_with("uv tool install --managed-python grokbot-kit")
    assert "PATH" in first
    assert "`pipx install grokbot-kit`" in first
    assert "sem `uv`" in first
    commands = [c for c in sh_commands() if c != "grokbot-kit --version"]
    assert commands[0] == "uv tool install --managed-python grokbot-kit"
    assert commands[1] == "pipx install grokbot-kit"
    setup = section("Setup")
    first_step = re.search(r"^### (.*)$", setup, re.MULTILINE)
    assert first_step and "1." in first_step.group(1)
    assert setup.index("uv tool install --managed-python grokbot-kit") < setup.index("### 2.")


# C128 - AC 104
def test_single_multichoice_cli_question() -> None:
    p = norm(paragraph_with("múltipla escolha"))
    assert "`setup.installed` vazio no `grokbot-kit doctor --json`" in p
    assert "uma única pergunta" in p
    assert "múltipla escolha" in p
    for tool in ("`opencode`", "`claude`", "`codex`"):
        assert tool in p, tool


# C129 - AC 105
def test_cli_add_and_login_per_cli() -> None:
    s = norm(section("CLIs"))
    assert "`grokbot-kit setup cli add <tool>`" in s
    assert "para cada CLI" in s
    assert "assinatura" in s
    assert "API key" in s
    assert "grokbot-kit login <tool> --method subscription" in s
    assert "grokbot-kit login <tool> --method api-key" in s
    assert s.index("grokbot-kit setup cli add <tool>") < s.index("grokbot-kit login <tool>")


# C130 - AC 106
def test_never_ask_secret_in_chat() -> None:
    p = norm(paragraph_with("sender key"))
    assert p.lower().count("nunca") >= 1
    for needle in ("API key", "sender key", "URL secreta", "no chat"):
        assert needle in p, needle
    assert re.search(r"`grokbot-kit secret set <\w+>`", p)
    assert "terminal do box" in p


# C131 - AC 107
def test_leaked_secret_handling() -> None:
    p = norm(paragraph_with("regenerar"))
    assert "colar" in p or "colado" in p
    assert "print" in p
    assert "painel" in p
    assert "`grokbot-kit secret set" in p
    assert "não grave" in p
    assert "não repita" in p


# C132 - AC 108
def test_default_cli_step() -> None:
    s = norm(section("CLI padrão"))
    assert "Pergunte" in s
    assert "grokbot-kit setup default <tool>" in s


# C133 - AC 109, door 22
def test_models_refresh_and_free_first() -> None:
    s = norm(section("Modelos e tiers"))
    assert "grokbot-kit setup models refresh" in s
    assert "só ids da lista descoberta" in s
    assert "gratuitos do opencode primeiro" in s
    assert "`trivial`" in s and "`standard`" in s
    assert "grokbot-kit setup tiers <tool> <tier> <id>" in s
    assert s.index("grokbot-kit setup models refresh") < s.index("grokbot-kit setup tiers")


# C134 - AC 110
def test_routine_setup_order() -> None:
    s = norm(section("Routine"))
    steps = [
        "webhook trigger",
        "grokbot-kit secret set <bot>-url",
        "grokbot-kit secret set <bot>-key",
        "grokbot-kit route add <bot>",
        "grokbot-kit route test <bot>",
    ]
    positions = [s.index(step) for step in steps]
    assert positions == sorted(positions), positions
    assert "terminal do box" in s[positions[0] : positions[2]]


# C135 - AC 111
def test_print_warning_before_panel() -> None:
    s = section("Routine")
    warning = next(i for i, line in enumerate(s.splitlines()) if "print" in line and "colagem" in line)
    line = s.splitlines()[warning]
    assert "mensagem" in line and "key" in line
    panel = next(i for i, line in enumerate(s.splitlines()) if "abra o painel" in line.lower())
    assert warning < panel


# C136 - AC 112
def test_routine_prompt_parse_schema_target() -> None:
    blocks = re.findall(r"^```text\n(.*?)^```", section("Prompt da routine"), re.DOTALL | re.MULTILINE)
    assert len(blocks) == 1
    prompt = norm(blocks[0])
    assert "`body`" in prompt and "JSON" in prompt and "parse" in prompt
    assert '"grokbot-kit.event/v1"' in prompt
    assert "`schema`" in prompt
    assert "`target`" in prompt and "ignore" in prompt.lower()


# C137 - AC 113
def test_run_with_tool_and_model() -> None:
    assert any(c.startswith("grokbot-kit run --tool <cli> --model <id> --target <este bot>") for c in sh_commands())


# C138 - AC 114
def test_omit_tool_for_default() -> None:
    p = norm(paragraph_with("Omita `--tool`"))
    assert "CLI padrão" in p
    runs = [c for c in sh_commands() if c.startswith("grokbot-kit run ")]
    assert any("--tool" not in c for c in runs)


# C139 - AC 115
def test_tier_classification_one_line() -> None:
    p = norm(paragraph_with("--tier <tier>"))
    for tier in ("`trivial`", "`standard`", "`complex`"):
        assert tier in p, tier
    assert "uma linha" in p
    runs = [c for c in sh_commands() if c.startswith("grokbot-kit run ")]
    assert any("--tier <tier>" in c and "--model" not in c for c in runs)


COMPLEX_CLASSES = [
    ("revisão de segurança",),
    ("decisões de arquitetura",),
    ("checagem de fatos",),
    ("produção", "credenciais", "dados sensíveis"),
]


# C140 - AC 116
@pytest.mark.parametrize("words", COMPLEX_CLASSES)
def test_rubric_complex_classes_never_free(words: tuple[str, ...]) -> None:
    rubric = section("Rubrica")
    rows = [line for line in rubric.splitlines() if line.startswith("| `complex`")]
    assert len(rows) == 1
    for word in words:
        assert word in rows[0], word
    rule = norm(paragraph_with("nunca vão a modelos gratuitos"))
    assert "`complex`" in rule


# C141 - AC 117
def test_event_handling() -> None:
    s = norm(section("Quando um evento chega"))
    assert "parse" in s and "`body`" in s and "JSON" in s
    for field in ("`event`", "`status`", "`summary`", "`output_file`"):
        assert field in s, field
    p = norm(paragraph_with("`resume_hint`"))
    assert "`needs_input`" in p and "`denied`" in p
    assert "mostre" in p.lower()


# C142 - AC 118
def test_undelivered_and_redeliver() -> None:
    p = norm(paragraph_with("`undelivered.jsonl`"))
    assert "task dir" in p
    assert "`grokbot-kit redeliver <task_id>`" in p


def help_of(words: list[str]) -> subprocess.CompletedProcess[str]:
    exe = shutil.which("grokbot-kit")
    assert exe is not None, "console script grokbot-kit não instalado"
    return subprocess.run([exe, *words, "--help"], capture_output=True, text=True, check=False, timeout=60)


# C143 - AC 119
def test_every_cited_command_exists() -> None:
    commands = cited_commands()
    assert len(commands) >= 15
    for command in commands:
        tokens = shlex.split(command.replace("<", "'<").replace(">", ">'"))[1:]
        words: list[str] = []
        for token in tokens:
            if not re.fullmatch(r"[a-z][a-z-]*", token):
                break
            words.append(token)
        result = help_of(words)
        assert result.returncode == 0, (command, result.stderr)
        for flag in re.findall(r"(?<!\S)(--[a-z][a-z-]*)", command.split(" -- ")[0]):
            assert flag in result.stdout, (command, flag)
    rule = norm(paragraph_with("Nunca invente"))
    for needle in ("id de modelo", "comando", "flag"):
        assert needle in rule, needle


ALLOWED = {"grokbot-kit", "uv", "pipx", "opencode", "claude", "codex"}


# C144 - door 8
def test_install_location_and_allowed_commands() -> None:
    p = norm(paragraph_with("/home/box/agent-data/workflows/grokbot-kit/"))
    assert "copi" in p.lower()
    assert "workflows" in p
    commands = sh_commands()
    assert commands
    for command in commands:
        assert command.split()[0] in ALLOWED, command
    rule = norm(paragraph_with("Só chame"))
    for program in ("`grokbot-kit`", "`uv`", "`pipx`"):
        assert program in rule, program


MODEL_ID_PATTERNS = [
    r"\b(haiku|sonnet|opus|fable)\b",
    r"\b(gpt|gemini|claude|llama|mistral|deepseek|qwen|grok|glm|kimi|minimax|nemotron)-[\w.]+",
    r"\b[\w.]+-free\b",
    r"\b(opencode|anthropic|openai|google|xai|deepseek|mistral|meta|qwen|openrouter|groq|zai|moonshotai)/(?!(claude|codex|opencode)\b)[\w.-]+",
    r"\bo[1-9](-\w+)?\b",
]


# C145 - AC 109, AC 119, AD-011
@pytest.mark.parametrize("pattern", MODEL_ID_PATTERNS)
def test_no_literal_model_ids(pattern: str) -> None:
    assert not re.search(pattern, text(), re.IGNORECASE), re.search(pattern, text(), re.IGNORECASE)
