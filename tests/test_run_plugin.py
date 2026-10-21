"""Provas de `grokbot-kit run --plugin` (checks C27-C35, C38-C44, C59; AC 26-33, 39-46, doors 3, 5, 6 e 7).

Tudo na fronteira: subprocesso `grokbot-kit run` com a CLI falsa, o `gh` falso (`tests/fakes/gh`) clonando um
repositório git local, e uma matriz de capacidades de teste em `GROKBOT_KIT_CAPABILITIES` (a do pacote só muda com
o S1, no box).
"""

import json
import shlex
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest
from conftest import MODELS, Kit, Receiver, add_routine, plugin_manifest, write_plugin
from test_payload import VALIDATOR

CAPABILITIES = ("write", "network", "commands", "workspace_config", "skills")
CLIS = ("claude", "opencode", "codex")
PR_URL = "https://github.com/o/r/pull/7"
NOTA_MAX_BYTES = 4096
VALID_RESULT = {"summary": "feito", "verdict": "ok"}
NOTA_PROMPT = "Nota: {nota}. Grave {result_file}.\n"
NOTA_PLUGIN = {"name": "nota", "version": "1.2.3", "source": "dir", "commit": None}


def write_matrix(path: Path, **unsupported: str) -> Path:
    """Matriz com todas as células `tool`, menos as de `unsupported` (`cli="capacidade,capacidade"`)."""
    cells = {cli: dict.fromkeys(CAPABILITIES, "tool") for cli in CLIS}
    for cli, caps in unsupported.items():
        for cap in caps.split(","):
            cells[cli][cap] = "unsupported"
    path.write_text(json.dumps(cells), encoding="utf-8")
    return path


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return proc.stdout.strip()


def origin_repo(path: Path) -> Path:
    """O repositório que o `gh` falso clona: `main` com `README.md` e a branch `feat/x` com `x.txt`."""
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    (path / "README.md").write_text("main\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "main")
    git(path, "checkout", "-q", "-b", "feat/x")
    (path / "x.txt").write_text("x\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "x")
    git(path, "checkout", "-q", "main")
    return path


def nota_manifest(name: str = "nota", **caps: Any) -> dict[str, Any]:
    manifest = plugin_manifest(name)
    manifest["inputs"] = {"nota": {"kind": "text", "required": True}}
    manifest["capabilities"].update(caps)
    manifest["result"] = {"required": ["summary", "verdict"], "max_bytes": NOTA_MAX_BYTES}
    return manifest


@pytest.fixture
def env(kit: Kit, tmp_path: Path) -> dict[str, str]:
    """Instala `teste` (entrada `repo` `pr`) e `nota` (entrada `text` `nota`); devolve o env das provas."""
    sources = tmp_path / "plugins"
    for path, manifest, prompt in (
        (sources / "teste", plugin_manifest(), None),
        (sources / "nota", nota_manifest(), NOTA_PROMPT),
    ):
        write_plugin(path, manifest, **({"prompt": prompt} if prompt else {}))
        result = kit.cli("plugin", "add", str(path), "--yes")
        assert result.returncode == 0, result.stderr
    return {
        "GROKBOT_KIT_CAPABILITIES": str(write_matrix(tmp_path / "matrix.json")),
        "FAKE_GH_REPO": str(origin_repo(tmp_path / "origem")),
        "FAKE_GH_LOG": str(tmp_path / "gh.jsonl"),
    }


def run_plugin(
    kit: Kit, env: dict[str, str], name: str, *args: str, tool: str = "opencode", target: str = "bot-a", **fake: str
) -> subprocess.CompletedProcess[str]:
    return kit.run("--tool", tool, "--target", target, "--label", "plug", "--plugin", name, *args, **{**env, **fake})


def run_nota(
    kit: Kit, env: dict[str, str], *args: str, **fake: str
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    result = run_plugin(kit, env, "nota", "--input", "nota=oi", *args, **fake)
    events = kit.sink_events()
    assert len(events) == 1, (events, result.stderr)
    return result, events[0]


def gh_calls(env: dict[str, str]) -> list[dict[str, Any]]:
    path = Path(env["FAKE_GH_LOG"])
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def tree(path: Path) -> dict[str, bytes]:
    return {str(p.relative_to(path)): p.read_bytes() for p in sorted(path.rglob("*")) if p.is_file()}


def outcome(event: dict[str, Any]) -> tuple[str, str, str]:
    return event["event"], event["status"], event["exit_reason"]


def padded_result(size: int) -> str:
    """Um resultado válido com exatamente `size` bytes."""
    base = json.dumps({"summary": "", "verdict": "ok"})
    return json.dumps({"summary": "s" * (size - len(base)), "verdict": "ok"})


# C27 - AC 26, doors 3 e 7
def test_launches_in_clone_with_prompt(kit: Kit, env: dict[str, str], tmp_path: Path) -> None:
    result = run_plugin(kit, env, "teste", "--input", f"pr={PR_URL}")
    assert result.returncode == 0, result.stderr
    task_dir = kit.task_dir()
    assert tree(task_dir / "plugin") == tree(tmp_path / "plugins" / "teste")
    work = task_dir / "work"
    assert (work / "README.md").read_text(encoding="utf-8") == "main\n"
    assert git(work, "rev-parse", "--abbrev-ref", "HEAD") == "pr-7"
    calls = gh_calls(env)
    assert calls[0]["argv"] == ["repo", "clone", "o/r", str(work)]
    assert calls[1] == {"argv": ["pr", "checkout", "7"], "cwd": str(work)}
    launched = kit.launched()
    assert launched["cwd"] == str(work)
    assert launched["argv"][-1] == (
        f"Revise {PR_URL} em {work}; grave {task_dir / 'result.json'}; task dir {task_dir}.\n"
    )
    assert launched["env"]["GROKBOT_KIT_RESULT_FILE"] == str(task_dir / "result.json")


# C28 - AC 26, door 7
def test_branch_url_checkout(kit: Kit, env: dict[str, str]) -> None:
    result = run_plugin(kit, env, "teste", "--input", "pr=https://github.com/o/r/tree/feat/x")
    assert result.returncode == 0, result.stderr
    work = kit.task_dir() / "work"
    assert git(work, "rev-parse", "--abbrev-ref", "HEAD") == "feat/x"
    assert (work / "x.txt").exists()
    assert [c["argv"] for c in gh_calls(env)] == [["repo", "clone", "o/r", str(work), "--", "--branch", "feat/x"]]


# C29 - AC 27, door 7
@pytest.mark.parametrize(
    "inputs",
    [
        [],
        ["--input", f"pr={PR_URL}", "--input", "extra=1"],
        ["--input", "pr"],
        ["--input", "pr=https://gitlab.com/o/r/-/merge_requests/1"],
        ["--input", "pr=https://github.com/o/r/pull/abc"],
        ["--input", "pr=https://github.com/o/r"],
    ],
    ids=["required_ausente", "nao_declarada", "sem_igual", "gitlab", "pr_nao_numerico", "repo_sem_pr"],
)
def test_refuses_bad_inputs_before_task_dir(kit: Kit, env: dict[str, str], inputs: list[str]) -> None:
    result = run_plugin(kit, env, "teste", *inputs)
    assert result.returncode == 2, result.stderr
    assert result.stderr.startswith("grokbot-kit run: ")
    assert kit.tasks() == []
    assert not kit.record.exists()


@pytest.fixture
def arquivos(kit: Kit, env: dict[str, str], tmp_path: Path) -> None:
    """Plugin `arquivos` com as entradas opcionais `doc` (`file`) e `nota` (`text`)."""
    manifest = plugin_manifest("arquivos")
    manifest["inputs"] = {"doc": {"kind": "file", "required": False}, "nota": {"kind": "text", "required": False}}
    source = write_plugin(tmp_path / "arquivos", manifest, prompt="Doc {doc} nota {nota}. Grave {result_file}.\n")
    assert kit.cli("plugin", "add", str(source), "--yes").returncode == 0


def sized(path: Path, size: int) -> str:
    path.write_bytes(b"a" * size)
    return str(path)


# C30 - AC 28
@pytest.mark.parametrize(
    ("make_input", "accepted"),
    [
        (lambda d: f"doc={d / 'nao-existe'}", False),
        (lambda d: f"doc={sized(d / 'grande', 1024 * 1024 + 1)}", False),
        (lambda d: "nota=" + "a" * (64 * 1024 + 1), False),
        (lambda d: f"doc={sized(d / 'limite', 1024 * 1024)}", True),
        (lambda d: "nota=" + "a" * (64 * 1024), True),
    ],
    ids=["file_inexistente", "file_1mib_mais_1", "text_64kib_mais_1", "file_1mib", "text_64kib"],
)
def test_input_size_bounds(
    kit: Kit, env: dict[str, str], arquivos: None, tmp_path: Path, make_input: Any, accepted: bool
) -> None:
    result = run_plugin(kit, env, "arquivos", "--input", make_input(tmp_path))
    if accepted:
        assert result.returncode == 0, result.stderr
        assert len(kit.tasks()) == 1
    else:
        assert result.returncode == 2, result.stderr
        assert kit.tasks() == []


# C31 - AC 29
def test_file_input_copied(kit: Kit, env: dict[str, str], arquivos: None, tmp_path: Path) -> None:
    doc = tmp_path / "alerta.txt"
    doc.write_text("ZeroDivisionError\n", encoding="utf-8")
    result = run_plugin(kit, env, "arquivos", "--input", f"doc={doc}")
    assert result.returncode == 0, result.stderr
    task_dir = kit.task_dir()
    copied = task_dir / "inputs" / "doc"
    assert copied.read_text(encoding="utf-8") == "ZeroDivisionError\n"
    assert kit.launched()["argv"][-1] == f"Doc {copied} nota . Grave {task_dir / 'result.json'}.\n"


# C32 - AC 30
def test_unknown_plugin(kit: Kit, env: dict[str, str]) -> None:
    result = run_plugin(kit, env, "nao-existe")
    assert result.returncode == 2
    assert "no plugin named nao-existe; run: grokbot-kit plugin list" in result.stderr
    assert kit.tasks() == []


# C33 - AC 31
@pytest.mark.parametrize("conflict", ["prompt_file", "extras", "cwd"])
def test_plugin_flag_conflicts(kit: Kit, env: dict[str, str], tmp_path: Path, conflict: str) -> None:
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("faça\n", encoding="utf-8")
    extra = {
        "prompt_file": ["--prompt-file", str(prompt)],
        "extras": ["--", "faça"],
        "cwd": ["--cwd", str(tmp_path)],
    }[conflict]
    result = run_plugin(kit, env, "teste", "--input", f"pr={PR_URL}", *extra)
    assert result.returncode == 2, result.stderr
    assert kit.tasks() == []


# C34 - AC 32, door 8
def test_refuses_unenforceable_capability(kit: Kit, env: dict[str, str], tmp_path: Path) -> None:
    source = write_plugin(tmp_path / "offline", nota_manifest("offline", network="off"), prompt=NOTA_PROMPT)
    assert kit.cli("plugin", "add", str(source), "--yes").returncode == 0
    env = {**env, "GROKBOT_KIT_CAPABILITIES": str(write_matrix(tmp_path / "m.json", opencode="network"))}
    result = run_plugin(kit, env, "offline", "--input", "nota=oi", tool="opencode")
    assert result.returncode == 2
    assert "plugin offline needs network=off, which opencode cannot enforce" in result.stderr
    assert kit.tasks() == []
    result = run_plugin(kit, env, "offline", "--input", "nota=oi", tool="claude", FAKE_RESULT=json.dumps(VALID_RESULT))
    assert result.returncode == 0, result.stderr
    assert len(kit.tasks()) == 1


# C35 - AC 33
def test_clone_failure_event(kit: Kit, env: dict[str, str]) -> None:
    result = run_plugin(kit, env, "teste", "--input", f"pr={PR_URL}", FAKE_GH_EXIT="1")
    assert result.returncode == 1
    assert not kit.record.exists(), "a CLI não pode ser lançada sem o clone"
    (event,) = kit.sink_events()
    assert outcome(event) == ("error", "failed", "agent_error")
    assert "Could not resolve to a Repository" in event["summary"]
    assert event["task_id"] == kit.task_dir().name
    assert event["result"] is None
    assert event["plugin"]["name"] == "teste"


# C38 - AC 39
def test_meta_records_plugin(kit: Kit, env: dict[str, str]) -> None:
    result = run_plugin(kit, env, "teste", "--input", f"pr={PR_URL}")
    assert result.returncode == 0, result.stderr
    meta = json.loads((kit.task_dir() / "meta.json").read_text(encoding="utf-8"))
    assert set(meta["plugin"]) == {"name", "version", "source", "commit", "capabilities", "support"}
    assert meta["plugin"]["name"] == "teste"
    assert meta["plugin"]["version"] == "1.2.3"
    assert meta["plugin"]["source"] == "dir"
    assert meta["plugin"]["commit"] is None
    assert meta["plugin"]["capabilities"] == {"write": "task-dir", "network": "on", "commands": ["git", "gh pr view"]}
    assert meta["plugin"]["support"] == dict.fromkeys(CAPABILITIES, "tool")


# C39 - AC 40
def test_run_without_plugin_unchanged(kit: Kit) -> None:
    result = kit.run("--tool", "opencode", "--target", "bot-a", "--label", "sem", "--", "oi", FAKE_NEEDS_INPUT="1")
    assert result.returncode == 0, result.stderr
    task_dir = kit.task_dir()
    launched = kit.launched()
    assert launched["argv"] == ["run", "--format", "json", "-m", MODELS["opencode"], "oi"]
    assert "GROKBOT_KIT_RESULT_FILE" not in launched["env"]
    assert "plugin" not in json.loads((task_dir / "meta.json").read_text(encoding="utf-8"))
    (event,) = kit.sink_events()
    assert outcome(event) == ("completed", "denied", "permission_denied")
    assert event["plugin"] is None
    assert event["result"] is None

    shutil.rmtree(task_dir)
    kit.sink.unlink()
    result = kit.run("--tool", "claude", "--target", "bot-a", "--label", "sem", "--", "oi")
    assert result.returncode == 0, result.stderr
    exe = shutil.which("grokbot-kit")
    assert exe is not None
    hook = {"type": "command", "command": f"{shlex.quote(exe)} emit --from claude"}
    settings = json.loads((kit.task_dir() / "claude-settings.json").read_text(encoding="utf-8"))
    assert settings == {"hooks": {"PermissionRequest": [{"matcher": "*", "hooks": [hook]}]}}


# C40 - AC 41, door 5
def test_valid_result_delivered(kit: Kit, env: dict[str, str]) -> None:
    result, event = run_nota(kit, env, FAKE_RESULT=json.dumps(VALID_RESULT))
    assert result.returncode == 0, result.stderr
    assert outcome(event) == ("completed", "ok", "success")
    assert event["result"] == VALID_RESULT
    assert event["plugin"] == NOTA_PLUGIN
    VALIDATOR.validate(event)


# C41 - AC 42
def test_summary_from_result(kit: Kit, env: dict[str, str]) -> None:
    long = "r" * 2001
    _, event = run_nota(kit, env, FAKE_RESULT=json.dumps({**VALID_RESULT, "summary": long}))
    assert outcome(event) == ("completed", "ok", "success")
    assert event["summary"] == "r" * 2000
    assert event["result"]["summary"] == long


# C42 - AC 43, door 6
@pytest.mark.parametrize(
    "content",
    [None, "[]", "{not json", json.dumps({"summary": "s"}), padded_result(NOTA_MAX_BYTES + 1)],
    ids=["ausente", "lista", "nao_json", "campo_faltando", "max_bytes_mais_1"],
)
def test_invalid_result_cases(kit: Kit, env: dict[str, str], content: str | None) -> None:
    fake = {} if content is None else {"FAKE_RESULT": content}
    result, event = run_nota(kit, env, **fake)
    assert result.returncode == 0, result.stderr
    assert outcome(event) == ("error", "failed", "result_invalid")
    assert event["result"] is None
    assert event["plugin"] == NOTA_PLUGIN
    assert "result.json" in event["summary"]
    VALIDATOR.validate(event)


def test_invalid_result_cases_exact_max_bytes_is_ok(kit: Kit, env: dict[str, str]) -> None:
    content = padded_result(NOTA_MAX_BYTES)
    assert len(content.encode("utf-8")) == NOTA_MAX_BYTES
    _, event = run_nota(kit, env, FAKE_RESULT=content)
    assert outcome(event) == ("completed", "ok", "success")
    assert event["result"] == json.loads(content)


# C43 - AC 44
def test_denial_logged_not_status(kit: Kit, env: dict[str, str]) -> None:
    denied = {
        "type": "result",
        "is_error": False,
        "result": "feito",
        "permission_denials": [{"tool_name": "Write", "tool_input": {"file_path": "/home/x"}}],
    }
    result = run_plugin(
        kit,
        env,
        "nota",
        "--input",
        "nota=oi",
        tool="claude",
        FAKE_STDOUT=json.dumps(denied),
        FAKE_RESULT=json.dumps(VALID_RESULT),
        FAKE_NEEDS_INPUT="1",
    )
    assert result.returncode == 0, result.stderr
    (event,) = kit.sink_events()
    assert outcome(event) == ("completed", "ok", "success")
    log = (kit.task_dir() / "kit.log").read_text(encoding="utf-8")
    assert "the CLI denied a permission" in log


def interrupted_run(kit: Kit, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    exe = shutil.which("grokbot-kit")
    assert exe is not None
    argv = [exe, "run", "--tool", "opencode", "--target", "bot-a", "--label", "plug", "--plugin", "nota"]
    fake = {"FAKE_RECORD": str(kit.record), "FAKE_SLEEP": "60", "FAKE_RESULT": json.dumps(VALID_RESULT)}
    proc = subprocess.Popen(
        [*argv, "--input", "nota=oi"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**kit.env, **env, **fake},
        cwd=kit.home,
    )
    try:
        deadline = time.monotonic() + 20
        while not kit.record.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        proc.send_signal(signal.SIGTERM)
        stdout, stderr = proc.communicate(timeout=60)
    finally:
        if proc.poll() is None:
            proc.kill()
    return subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)


# C44 - AC 45
@pytest.mark.parametrize(
    ("case", "expected", "code"),
    [
        ("timeout", ("timeout", "timeout", "timeout"), 124),
        ("interrompida", ("error", "interrupted", "interrupted"), 130),
        ("binario_ausente", ("error", "failed", "agent_error"), 127),
        ("erro_do_agente", ("error", "failed", "agent_error"), 0),
        ("exit_3", ("error", "failed", "nonzero_exit"), 3),
    ],
)
def test_plugin_failure_paths(
    kit: Kit, env: dict[str, str], case: str, expected: tuple[str, str, str], code: int
) -> None:
    valid = {"FAKE_RESULT": json.dumps(VALID_RESULT)}
    if case == "timeout":
        result = run_plugin(kit, env, "nota", "--input", "nota=oi", "--timeout", "1s", FAKE_SLEEP="60", **valid)
    elif case == "interrompida":
        result = interrupted_run(kit, env)
    elif case == "binario_ausente":
        text = kit.config_text()
        kit.write_config(text.replace("[cli.opencode]\n", f'[cli.opencode]\nbin = "{kit.home}/nao-existe"\n', 1))
        result = run_plugin(kit, env, "nota", "--input", "nota=oi", **valid)
    elif case == "erro_do_agente":
        result = run_plugin(
            kit, env, "nota", "--input", "nota=oi", FAKE_STDOUT=json.dumps({"type": "error"}) + "\n", **valid
        )
    else:
        result = run_plugin(kit, env, "nota", "--input", "nota=oi", FAKE_EXIT="3", **valid)
    assert result.returncode == code, result.stderr
    (event,) = kit.sink_events()
    assert outcome(event) == expected
    assert event["result"] is None
    assert event["plugin"] == NOTA_PLUGIN
    VALIDATOR.validate(event)


# C59 - door 5
@pytest.mark.parametrize("status", [200, 401, 500])
def test_plugin_event_delivery_statuses(kit: Kit, env: dict[str, str], receiver: Receiver, status: int) -> None:
    add_routine(kit, receiver)
    if status != 200:
        receiver.respond((status, json.dumps({"message": f"status {status}"})))
    result = run_plugin(kit, env, "nota", "--input", "nota=oi", target="bot-r", FAKE_RESULT=json.dumps(VALID_RESULT))
    assert result.returncode == 0, result.stderr
    task_dir = kit.task_dir()
    bodies = receiver.bodies()
    assert bodies[0]["plugin"] == NOTA_PLUGIN
    assert bodies[0]["result"] == VALID_RESULT
    undelivered = task_dir / "undelivered.jsonl"
    if status == 200:
        assert len(bodies) == 1
        assert [p.name for p in (task_dir / "sent").iterdir()] == [f"{task_dir.name}:completed:terminal"]
        assert not undelivered.exists()
    else:
        assert len(bodies) == (1 if status == 401 else 3)
        (line,) = [json.loads(x) for x in undelivered.read_text(encoding="utf-8").splitlines()]
        assert line["http_status"] == status
