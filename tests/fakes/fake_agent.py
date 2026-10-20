#!/usr/bin/env python3
"""CLI falsa: faz o papel de `claude`, `opencode` ou `codex` (pelo nome do link) nos testes do `run`.

Comportamento por env: `FAKE_RECORD` (grava argv, stdin, env e cwd), `FAKE_STDOUT` (saída), `FAKE_LAST_MESSAGE`
(conteúdo do `-o` do codex), `FAKE_NEEDS_INPUT=1` (registra um `needs_input` no task dir; um objeto JSON no lugar
do `1` entra como campos extras desse evento, ex. `transcript_path`), `FAKE_EMIT` (lista JSON de stdins para
`grokbot-kit emit --from <tool>`) e `FAKE_EXIT` (exit code).

Descoberta de modelos: `opencode models` imprime `FAKE_OPENCODE_MODELS` e sai com `FAKE_MODELS_EXIT`. Com
`FAKE_ACCEPT_MODELS` (lista JSON) no env, `claude`/`codex` fazem o papel da chamada de teste de um modelo: aceitam os
ids da lista e recusam os outros com erro de modelo e exit `1`; os ids de `FAKE_ERROR_EXIT0` saem com `0` e erro na
saída JSON. `FAKE_CALLS` acumula uma linha JSON por chamada (argv, stdin, cwd e `CODEX_HOME`).
"""

import json
import os
import subprocess
import sys

tool = os.path.basename(sys.argv[0])
args = sys.argv[1:]

calls = os.environ.get("FAKE_CALLS")
if calls:
    with open(calls, "a", encoding="utf-8") as f:
        call = {
            "tool": tool,
            "argv": args,
            "stdin_target": os.readlink("/proc/self/fd/0"),
            "cwd": os.getcwd(),
            "codex_home": os.environ.get("CODEX_HOME"),
        }
        f.write(json.dumps(call) + "\n")

if tool == "opencode" and args[:1] == ["models"]:
    sys.stdout.write(os.environ.get("FAKE_OPENCODE_MODELS", ""))
    sys.exit(int(os.environ.get("FAKE_MODELS_EXIT", "0")))

if "FAKE_ACCEPT_MODELS" in os.environ and tool in ("claude", "codex"):
    flag = "--model" if tool == "claude" else "-m"
    model = args[args.index(flag) + 1]
    accepted = model in json.loads(os.environ["FAKE_ACCEPT_MODELS"])
    error_exit0 = model in json.loads(os.environ.get("FAKE_ERROR_EXIT0", "[]"))
    failed = error_exit0 or not accepted
    if tool == "claude":
        result = f"model {model} not found" if failed else "ok"
        sys.stdout.write(json.dumps({"type": "result", "is_error": failed, "result": result}) + "\n")
    elif failed:
        sys.stdout.write(json.dumps({"type": "error", "message": f"model {model} is not supported"}) + "\n")
    else:
        sys.stdout.write(json.dumps({"type": "thread.started", "thread_id": "th-1"}) + "\n")
    sys.exit(1 if failed and not error_exit0 else 0)

record = os.environ.get("FAKE_RECORD")
if record:
    with open(record, "w", encoding="utf-8") as f:
        json.dump(
            {
                "tool": tool,
                "argv": args,
                "stdin_target": os.readlink("/proc/self/fd/0"),
                "stdin_read": sys.stdin.read(),
                "env": {k: v for k, v in os.environ.items() if k.startswith("GROKBOT_KIT_") or k == "CODEX_HOME"},
                "cwd": os.getcwd(),
            },
            f,
        )

if "FAKE_LAST_MESSAGE" in os.environ and "-o" in args:
    with open(args[args.index("-o") + 1], "w", encoding="utf-8") as f:
        f.write(os.environ["FAKE_LAST_MESSAGE"])

needs_input = os.environ.get("FAKE_NEEDS_INPUT")
if needs_input:
    extra = {} if needs_input == "1" else json.loads(needs_input)
    with open(os.path.join(os.environ["GROKBOT_KIT_TASK_DIR"], "events.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"event": {"event": "needs_input", "status": "permission", **extra}}) + "\n")

for payload in json.loads(os.environ.get("FAKE_EMIT", "[]")):
    subprocess.run(
        ["grokbot-kit", "emit", "--from", tool], input=json.dumps(payload), text=True, capture_output=True, check=False
    )

sys.stdout.write(os.environ.get("FAKE_STDOUT", ""))
sys.exit(int(os.environ.get("FAKE_EXIT", "0")))
