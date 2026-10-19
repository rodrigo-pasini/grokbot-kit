#!/usr/bin/env python3
"""CLI falsa: faz o papel de `claude`, `opencode` ou `codex` (pelo nome do link) nos testes do `run`.

Comportamento por env: `FAKE_RECORD` (grava argv, stdin, env e cwd), `FAKE_STDOUT` (saída), `FAKE_LAST_MESSAGE`
(conteúdo do `-o` do codex), `FAKE_NEEDS_INPUT=1` (registra um `needs_input` no task dir), `FAKE_EMIT` (lista
JSON de stdins para `grokbot-kit emit --from <tool>`) e `FAKE_EXIT` (exit code).
"""

import json
import os
import subprocess
import sys

tool = os.path.basename(sys.argv[0])
args = sys.argv[1:]

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

if os.environ.get("FAKE_NEEDS_INPUT") == "1":
    with open(os.path.join(os.environ["GROKBOT_KIT_TASK_DIR"], "events.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"event": {"event": "needs_input", "status": "permission"}}) + "\n")

for payload in json.loads(os.environ.get("FAKE_EMIT", "[]")):
    subprocess.run(
        ["grokbot-kit", "emit", "--from", tool], input=json.dumps(payload), text=True, capture_output=True, check=False
    )

sys.stdout.write(os.environ.get("FAKE_STDOUT", ""))
sys.exit(int(os.environ.get("FAKE_EXIT", "0")))
