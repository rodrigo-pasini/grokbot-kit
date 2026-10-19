"""Provas com as CLIs reais no box (check C55; AC 40-44). Rodam só com `-m integration`.

O kit roda num `HOME` temporário, para não tocar no config nem nos task dirs do usuário. Do `HOME` real só entram,
por symlink, as credenciais do Claude (`~/.claude/.credentials.json`) e do opencode
(`~/.local/share/opencode/auth.json`). O Codex usa o `CODEX_HOME` isolado da door 7, `~/.grokbot-kit/codex-home` do
`HOME` real, com login próprio; o `~/.codex` do usuário nunca entra (AC 98).

Modelos: `haiku` no Claude (alias documentado); no opencode, `GROKBOT_KIT_IT_OPENCODE_MODEL` ou o primeiro modelo
`-free` impresso por `opencode models`; e o id de `GROKBOT_KIT_IT_CODEX_MODEL` no Codex.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

REAL_HOME = Path.home()
REAL_CODEX_HOME = REAL_HOME / ".grokbot-kit" / "codex-home"

PROMPTS = {
    "ok": "Reply with exactly the word pong. Do not use any tool.",
    "denied": "Use your shell tool to run exactly this command: touch {work}/criado.txt",
}


def real_bin(tool: str) -> str:
    path = shutil.which(tool)
    if path is None:
        pytest.fail(f"{tool} não está instalado no box")
    return path


def model_for(tool: str) -> str:
    if tool == "claude":
        return "haiku"
    if tool == "opencode":
        if os.environ.get("GROKBOT_KIT_IT_OPENCODE_MODEL"):
            return os.environ["GROKBOT_KIT_IT_OPENCODE_MODEL"]
        listed = subprocess.run(
            [real_bin("opencode"), "models"], capture_output=True, text=True, stdin=subprocess.DEVNULL, check=True
        ).stdout.split()
        free = [m for m in listed if m.endswith("-free")]
        if not free:
            pytest.fail("opencode models não listou nenhum modelo -free")
        return free[0]
    model = os.environ.get("GROKBOT_KIT_IT_CODEX_MODEL")
    if not model:
        pytest.fail("defina GROKBOT_KIT_IT_CODEX_MODEL com um id aceito pelo codex exec")
    return model


def link(src: Path, dest: Path) -> None:
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.symlink_to(src)


def prepare_home(tmp_path: Path, tool: str, case: str) -> tuple[Path, Path, str]:
    home = tmp_path / "home"
    work = tmp_path / "work"
    work.mkdir()
    # o `codex exec` só roda dentro de um repositório git (ou com `--skip-git-repo-check`), como uma task real
    subprocess.run(["git", "init", "-q", str(work)], check=True)
    link(REAL_HOME / ".claude" / ".credentials.json", home / ".claude" / ".credentials.json")
    link(
        REAL_HOME / ".local" / "share" / "opencode" / "auth.json", home / ".local" / "share" / "opencode" / "auth.json"
    )
    if tool == "opencode" and case == "denied":
        opencode_config = home / ".config" / "opencode" / "opencode.json"
        opencode_config.parent.mkdir(parents=True)
        opencode_config.write_text(json.dumps({"permission": {"bash": "ask", "edit": "ask"}}), encoding="utf-8")
    if tool == "codex" and not (REAL_CODEX_HOME / "auth.json").exists():
        pytest.fail(f"Codex sem login no CODEX_HOME isolado: rode CODEX_HOME={REAL_CODEX_HOME} codex login")

    model = model_for(tool)
    sink = tmp_path / "sink.jsonl"
    cli = [f"[cli.{tool}]", f"bin = {json.dumps(real_bin(tool))}", f"models = [{json.dumps(model)}]"]
    if tool == "codex":
        cli.append(f"codex_home = {json.dumps(str(REAL_CODEX_HOME))}")
    config = "\n".join(
        [
            "[setup]",
            "version = 1",
            f'installed = ["{tool}"]',
            f'default_cli = "{tool}"',
            "",
            *cli,
            f"[cli.{tool}.tiers]",
            f"standard = [{json.dumps(model)}]",
            "",
            "[routes.it]",
            'sinks = ["arquivo"]',
            "",
            "[sinks.arquivo]",
            'type = "file"',
            f"path = {json.dumps(str(sink))}",
            "",
        ]
    )
    config_path = home / ".config" / "grokbot-kit" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config, encoding="utf-8")
    return home, work, PROMPTS[case].format(work=work)


# C55 - AC 40-44
@pytest.mark.parametrize("case", ["ok", "denied"])
@pytest.mark.parametrize("tool", ["claude", "opencode", "codex"])
def test_completed_ok_and_denied_per_tool(tmp_path: Path, tool: str, case: str) -> None:
    home, work, prompt = prepare_home(tmp_path, tool, case)
    exe = shutil.which("grokbot-kit")
    assert exe is not None
    env = {**os.environ, "HOME": str(home)}
    result = subprocess.run(
        [exe, "run", "--tool", tool, "--target", "it", "--label", f"it-{case}", "--cwd", str(work), "--", prompt],
        capture_output=True,
        text=True,
        env=env,
        stdin=subprocess.DEVNULL,
        check=False,
        timeout=600,
    )
    sink = tmp_path / "sink.jsonl"
    lines = sink.read_text(encoding="utf-8").splitlines() if sink.exists() else []
    assert len(lines) == 1, result.stderr
    event = json.loads(lines[0])
    expected = ("completed", "ok") if case == "ok" else ("completed", "denied")
    assert (event["event"], event["status"]) == expected, (event, result.stderr)
