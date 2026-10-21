"""Provas do guia de autoria `docs/plugins.md` (check C57; AC 64, doors 1, 2, 6 e 8).

A tabela da matriz do guia é comparada com a matriz que `plugin.py` usa; o C8 (S1) prova que essa é a de `spike.md`.
"""

import re
from pathlib import Path

from grokbot_kit import plugin

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "docs" / "plugins.md"


def guide() -> str:
    return GUIDE.read_text(encoding="utf-8")


def section(heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", guide(), re.DOTALL | re.MULTILINE)
    assert match, f"sem a seção {heading!r}"
    return match.group(1)


# C57 - AC 64
def test_guide_sections() -> None:
    text = guide()
    assert "pode mudar antes da 1.0" in text.split("\n## ", 1)[0], "o aviso vem antes da primeira seção"

    layout = section("Layout")
    for part in (".claude-plugin/plugin.json", "grokbot-kit.toml", "skills/<skill>/SKILL.md"):
        assert part in layout, part
    for refused in ("`hooks/`", "`commands/`", "`agents/`", "`.mcp.json`", "`.lsp.json`"):
        assert refused in layout, refused

    manifest = section("Manifesto e capacidades")
    for needle in (
        '`"grokbot-kit.plugin/v0"`',
        plugin.NAME_RE.pattern,
        '`"repo"`, `"text"` ou `"file"`',
        '`"task-dir"`, `"none"`',
        '`"on"`, `"off"`',
        "`{workspace}`",
        "`{result_file}`",
        "`{task_dir}`",
        "`max_bytes` (padrão `16384`)",
    ):
        assert needle in manifest, needle

    rows = re.findall(r"^\| `(claude|opencode|codex)` \| (.*) \|$", section("Matriz de capacidades"), re.MULTILINE)
    table = {cli: [cell.strip(" `") for cell in cells.split("|")] for cli, cells in rows}
    assert table == {cli: [cells[c] for c in plugin.MATRIX_COLUMNS] for cli, cells in plugin.matrix().items()}

    result = section("Resultado")
    for needle in ("`<task_dir>/result.json`", "`GROKBOT_KIT_RESULT_FILE`", "`result_invalid`", "`max_bytes`"):
        assert needle in result, needle

    example = section("Exemplo comentado: `code-review`")
    builtin = next(p for p in plugin.builtins() if p.name == "code-review")
    assert f"```toml\n{(builtin.path / 'grokbot-kit.toml').read_text(encoding='utf-8')}```" in example
    assert f"```markdown\n{(builtin.path / 'prompt.md').read_text(encoding='utf-8')}```" in example
