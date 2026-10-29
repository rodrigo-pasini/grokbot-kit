"""Provas dos hooks do Claude Code do repositório (sdlc-gates: checks C26-C30, C41-C43; AC 9, 20-23, 32, door 6).

Cada hook é alimentado com o JSON do evento em stdin, como o Claude Code faz.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / ".claude" / "hooks" / "gate-humano.sh"
SESSION = ROOT / ".claude" / "hooks" / "session-start.sh"
CLAUDE_MD_WARNING = "CLAUDE.md or CLAUDE.local.md found: AGENTS.md is not loaded; move its content to AGENTS.md"


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def repo_on(tmp_path: Path, branch: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", branch)
    return repo


def gate(command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(cwd),
    }
    return subprocess.run(
        ["bash", str(GATE)], input=json.dumps(payload), cwd=cwd, capture_output=True, text=True, check=False
    )


def decision(command: str, cwd: Path) -> tuple[str | None, str]:
    result = gate(command, cwd)
    assert result.returncode == 0, result.stderr
    if not result.stdout.strip():
        return None, ""
    out = json.loads(result.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    return out["permissionDecision"], out.get("permissionDecisionReason", "")


@pytest.fixture
def feature_repo(tmp_path: Path) -> Path:
    return repo_on(tmp_path, "feat/31/sdlc-gates")


# C26 - AC 20-23, door 6
def test_settings_registers_hooks() -> None:
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    hooks = settings["hooks"]

    def commands(event: str, matcher: str | None) -> list[str]:
        return [
            h["command"]
            for entry in hooks.get(event, [])
            if entry.get("matcher") == matcher
            for h in entry["hooks"]
            if h["type"] == "command"
        ]

    assert any("gate-humano.sh" in c for c in commands("PreToolUse", "Bash"))
    assert any("gate-worktree.sh" in c for c in commands("PreToolUse", "Edit|Write|MultiEdit|NotebookEdit"))
    session = [h["command"] for entry in hooks.get("SessionStart", []) for h in entry["hooks"]]
    assert any("session-start.sh" in c for c in session)


# C27 - AC 20, door 6
@pytest.mark.parametrize(
    "command",
    [
        "gh pr merge 30 --squash",
        "git tag v0.6.0",
        "git push origin v0.6.0",
        "git push --tags",
        "gh release create v0.6.0",
        "gh api -X PUT repos/o/r/branches/main/protection",
        "gh api repos/o/r/environments/pypi",
    ],
)
def test_gate_humano_ask(feature_repo: Path, command: str) -> None:
    kind, reason = decision(command, feature_repo)
    assert kind == "ask", command
    assert reason.strip()


# C28 - AC 21, door 6
@pytest.mark.parametrize(
    "command", ["git push origin main", "git push origin HEAD:main", "git status && git push origin main"]
)
def test_gate_humano_deny(feature_repo: Path, command: str) -> None:
    assert decision(command, feature_repo)[0] == "deny", command


@pytest.mark.parametrize("command", ["git push --force origin main", "git push origin -d main"])
def test_gate_humano_deny_force_main(feature_repo: Path, command: str) -> None:
    assert decision(command, feature_repo)[0] == "deny", command


@pytest.mark.parametrize("command", ["git push --force origin feat/31/x", "git push origin --delete feat/31/x"])
def test_gate_humano_no_allow_force_or_delete(feature_repo: Path, command: str) -> None:
    assert decision(command, feature_repo)[0] is None, command


def test_gate_humano_deny_current_main(tmp_path: Path) -> None:
    repo = repo_on(tmp_path, "main")
    assert decision("git push", repo)[0] == "deny"


# C29 - AC 22, door 6
@pytest.mark.parametrize(
    "command", ["git push -u origin feat/31/sdlc-gates", 'gh pr create --title "feat(ci): x" --body-file b.md']
)
def test_gate_humano_allow(feature_repo: Path, command: str) -> None:
    assert decision(command, feature_repo)[0] == "allow", command


def test_gate_humano_allow_not_outside_door_2(feature_repo: Path) -> None:
    assert decision("git push -u origin feat/sdlc", feature_repo)[0] != "allow"


def test_gate_humano_allow_not_compound(feature_repo: Path) -> None:
    """Um `allow` vale para o comando inteiro: um composto não ganha `allow` por causa de um push bom."""
    assert decision("rm -rf build && git push -u origin feat/31/sdlc-gates", feature_repo)[0] != "allow"


# C57 - AC 44, door 6
@pytest.mark.parametrize(
    "command",
    [
        'git push origin "main"',
        "git push origin 'HEAD:main'",
        "GIT_DIR=.git git push origin main",
        "env git push origin main",
        "command git push origin main",
        "/usr/bin/git push origin main",
    ],
)
def test_gate_humano_deny_disguised(feature_repo: Path, command: str) -> None:
    assert decision(command, feature_repo)[0] == "deny", command


# C58 - AC 45, door 6
@pytest.mark.parametrize(
    "command",
    [
        "git push origin $(echo main)",
        "git push origin `echo main`",
        'bash -c "git push origin main"',
        "sudo git push origin main",
        "xargs gh pr merge",
    ],
)
def test_gate_humano_ask_unparsed(feature_repo: Path, command: str) -> None:
    kind, reason = decision(command, feature_repo)
    assert kind == "ask", command
    assert reason.strip()


# C60 - AC 45, door 6
@pytest.mark.parametrize(
    "command",
    ["sudo git tag v1", 'bash -c "gh release create v1"', "xargs gh api repos/o/r/branches/main/protection"],
)
def test_gate_humano_ask_unparsed_verbs(feature_repo: Path, command: str) -> None:
    kind, reason = decision(command, feature_repo)
    assert kind == "ask", command
    assert reason.strip()


# C61 - AC 47, door 6
@pytest.mark.parametrize(
    "command",
    [
        "GIT_DIR=x/.git git push origin HEAD",
        "GIT_WORK_TREE=x git push origin feat/31/x",
        "git -C x push origin HEAD",
        "git --git-dir=x/.git push origin feat/31/x",
        "git --work-tree=x push origin feat/31/x",
    ],
)
def test_gate_humano_other_repo_no_allow(feature_repo: Path, command: str) -> None:
    assert decision(command, feature_repo)[0] != "allow", command


def test_gate_humano_other_repo_deny_main(feature_repo: Path) -> None:
    assert decision("git -C x push origin main", feature_repo)[0] == "deny"


# C62 - AC 48, door 6
@pytest.mark.parametrize(
    "command",
    [
        'git commit -m "fix: a; git push origin main"',
        'git commit -m "docs: gate | git tag"',
        "git commit -m 'a && git push origin main'",
    ],
)
def test_gate_humano_quoted_separators(feature_repo: Path, command: str) -> None:
    result = gate(command, feature_repo)
    assert result.returncode == 0
    assert result.stdout == "", command


def test_gate_humano_quoted_separators_still_split(feature_repo: Path) -> None:
    assert decision("git status && git push origin main", feature_repo)[0] == "deny"


# C63 - AC 49, door 6
@pytest.mark.parametrize(
    "command",
    [
        "\\git push origin main",
        "git push origin ma\\in",
        "(git push origin main)",
        "(cd x && git push origin main)",
        "git push origin main&",
    ],
)
def test_gate_humano_deny_escaped(feature_repo: Path, command: str) -> None:
    assert decision(command, feature_repo)[0] == "deny", command


# C64 - AC 50, door 6
@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("echo $(git push origin main)", "ask"),
        ("x=$(git push origin main)", "ask"),
        ("echo `git push origin main`", "ask"),
    ],
)
def test_gate_humano_substitution(feature_repo: Path, command: str, expected: str) -> None:
    assert decision(command, feature_repo)[0] == expected, command


# C65 - AC 48, door 6
@pytest.mark.parametrize(
    "command", ['git commit -m "a || git push origin main"', 'git commit -m "a & git push origin main"']
)
def test_gate_humano_quoted_more(feature_repo: Path, command: str) -> None:
    result = gate(command, feature_repo)
    assert result.returncode == 0
    assert result.stdout == "", command


def test_gate_humano_quoted_more_escaped_quote(feature_repo: Path) -> None:
    assert decision('git commit -m \\" ; git push origin main', feature_repo)[0] == "deny"


# C66 - AC 51, door 6
@pytest.mark.parametrize(
    "command",
    [
        "git --git-dir x/.git push origin main",
        "git --work-tree x push origin main",
        "git --namespace n push origin main",
    ],
)
def test_gate_humano_spaced_options_deny(feature_repo: Path, command: str) -> None:
    assert decision(command, feature_repo)[0] == "deny", command


def test_gate_humano_spaced_options_no_allow(feature_repo: Path) -> None:
    assert decision("git --git-dir x/.git push origin feat/31/x", feature_repo)[0] != "allow"


def test_gate_humano_spaced_options_alias(feature_repo: Path) -> None:
    assert decision("git -c alias.p=push p origin main", feature_repo)[0] == "ask"


# C67 - AC 52, door 6
@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("git push --follow-tags origin feat/31/x", "ask"),
        ("git push --tags origin main", "deny"),
        ("gh pr -R o/r merge 34", "ask"),
        ("gh api -X PUT repos/o/r/pulls/34/merge", "ask"),
        ("gh api repos/o/r/releases", "ask"),
        ("gh api -X DELETE repos/o/r/git/refs/heads/x", "ask"),
    ],
)
def test_gate_humano_more_ask(feature_repo: Path, command: str, expected: str) -> None:
    assert decision(command, feature_repo)[0] == expected, command


def test_gate_humano_more_ask_combined_force(feature_repo: Path) -> None:
    assert decision("git push -uf origin feat/31/x", feature_repo)[0] != "allow"


# C68 - AC 53, door 6
@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("git -C $(pwd) push origin main", "deny"),
        ("git push $(git remote) main", "deny"),
        ("git push $(echo origin) main", "deny"),
        ("git push origin $(true) main", "deny"),
        ("x=`git push origin main`", "ask"),
        ('git commit -m "$(git push origin main)"', "ask"),
        ('git commit -m "`git push origin main`"', "ask"),
        ("echo $(echo $(git push origin main))", "ask"),
        ("echo $(git push origin main $(true))", "ask"),
        ("echo $(git push origin main; echo $(date))", "ask"),
        ("echo `echo $(git push origin main)`", "ask"),
        ('x=$(git push origin "$(echo main)")', "ask"),
    ],
)
def test_gate_humano_substitution_args(feature_repo: Path, command: str, expected: str) -> None:
    kind, reason = decision(command, feature_repo)
    assert kind == expected, command
    assert reason.strip()


# C69 - AC 51, 52, 54, door 6
def test_gate_humano_round5_config_env_deny(feature_repo: Path) -> None:
    assert decision("git --config-env core.x=Y push origin main", feature_repo)[0] == "deny"


@pytest.mark.parametrize("command", ["git --namespace=n push origin feat/31/x", "git push -ud origin feat/31/x"])
def test_gate_humano_round5_no_allow(feature_repo: Path, command: str) -> None:
    assert decision(command, feature_repo)[0] != "allow", command


@pytest.mark.parametrize(
    "command",
    [
        "gh pr --repo o/r merge 34",
        "git -c Alias.p=push p origin main",
        "git --config-env alias.p=X p origin main",
        "gh api graphql -f query=mutation{mergePullRequest}",
    ],
)
def test_gate_humano_round5_ask(feature_repo: Path, command: str) -> None:
    assert decision(command, feature_repo)[0] == "ask", command


# C70 - AC 55, door 6
@pytest.mark.parametrize(
    "command",
    [
        "git commit -m 'fix: `git push origin main` x'",
        "rg -n '$(git push origin main)' docs",
        "git commit -F - <<'EOF'\nfix(x): cita git push origin main\nEOF",
    ],
)
def test_gate_humano_round6_no_false_deny(feature_repo: Path, command: str) -> None:
    assert decision(command, feature_repo)[0] != "deny", command


@pytest.mark.parametrize(
    "command",
    [
        "git --config-env=alias.p=X p origin main",
        "gh api graphql -f query=mutation{enablePullRequestAutoMerge}",
    ],
)
def test_gate_humano_round6_ask(feature_repo: Path, command: str) -> None:
    assert decision(command, feature_repo)[0] == "ask", command


# C30 - AC 23
@pytest.mark.parametrize("command", ["git status", "uv run pytest", "gh pr view 30"])
def test_gate_humano_neutral(feature_repo: Path, command: str) -> None:
    result = gate(command, feature_repo)
    assert result.returncode == 0
    assert result.stdout == ""


# ---------------------------------------------------------------------------- SessionStart


def stub_uv(tmp_path: Path, exit_code: int) -> tuple[Path, Path]:
    """Um `uv` falso no PATH que registra a chamada em `calls`."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls"
    uv = bin_dir / "uv"
    uv.write_text(f'#!/bin/sh\necho "$PWD $*" >> "{calls}"\nexit {exit_code}\n', encoding="utf-8")
    uv.chmod(0o755)
    return bin_dir, calls


def session(repo: Path, bin_dir: Path) -> tuple[subprocess.CompletedProcess[str], str]:
    payload = {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(repo)}
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "CLAUDE_PROJECT_DIR": str(repo)}
    result = subprocess.run(
        ["bash", str(SESSION)],
        input=json.dumps(payload),
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    context = ""
    if result.stdout.strip():
        out: dict[str, Any] = json.loads(result.stdout)["hookSpecificOutput"]
        assert out["hookEventName"] == "SessionStart"
        context = out["additionalContext"]
    return result, context


# C41 - AC 9
def test_session_start_installs_hooks(tmp_path: Path) -> None:
    repo = repo_on(tmp_path, "feat/31/x")
    bin_dir, calls = stub_uv(tmp_path, 0)
    result, context = session(repo, bin_dir)
    assert result.returncode == 0, result.stderr
    assert calls.read_text(encoding="utf-8").split() == [str(repo), "run", "pre-commit", "install"]
    assert context.strip() and "install" in context

    calls.unlink()
    (repo / ".git" / "hooks" / "commit-msg").write_text("#!/bin/sh\n", encoding="utf-8")
    again, _ = session(repo, bin_dir)
    assert again.returncode == 0
    assert not calls.exists(), "reinstalou com o hook já presente"


# C42 - AC 32
@pytest.mark.parametrize("name", ["CLAUDE.md", "CLAUDE.local.md"])
def test_session_start_warns_claude_md(tmp_path: Path, name: str) -> None:
    repo = repo_on(tmp_path, "feat/31/x")
    (repo / ".git" / "hooks" / "commit-msg").write_text("#!/bin/sh\n", encoding="utf-8")
    bin_dir, _ = stub_uv(tmp_path, 0)
    _, clean = session(repo, bin_dir)
    assert CLAUDE_MD_WARNING not in clean
    (repo / name).write_text("# x\n", encoding="utf-8")
    result, context = session(repo, bin_dir)
    assert result.returncode == 0
    assert CLAUDE_MD_WARNING in context.splitlines()


# C43 - AC 9
def test_session_start_install_failure(tmp_path: Path) -> None:
    repo = repo_on(tmp_path, "feat/31/x")
    bin_dir, calls = stub_uv(tmp_path, 1)
    result, context = session(repo, bin_dir)
    assert result.returncode == 0
    assert calls.exists()
    assert "fail" in context.lower()
