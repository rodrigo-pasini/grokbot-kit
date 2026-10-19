"""Roteador: entrega um evento aos sinks da rota do `target`, uma vez por chave de dedupe (door 5).

No S1 só o sink `file` (AC 120) entrega; os demais tipos chegam no S4 e, até lá, o evento vai para
`undelivered.jsonl`.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any


def _append(path: Path, line: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def deliver(task_dir: Path, config: dict[str, Any], target: str, event: dict[str, Any], discriminator: str) -> None:
    key = f"{event['task_id']}:{event['event']}:{discriminator}"
    sent = task_dir / "sent"
    sent.mkdir(exist_ok=True)
    try:
        receipt_fd = os.open(sent / key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return
    body = json.dumps(event, ensure_ascii=False)
    deliveries = []
    for name in config["routes"][target]["sinks"]:
        sink = config["sinks"][name]
        error = None
        if sink.get("type") == "file":
            try:
                _append(Path(os.path.expanduser(sink["path"])), body)
            except OSError as e:
                error = str(e)
        else:
            error = f"sink type {sink.get('type')!r} not supported yet"
        deliveries.append({"sink": name, "type": sink.get("type"), "delivered": error is None})
        if error is not None:
            _append(task_dir / "undelivered.jsonl", json.dumps({"sink": name, "error": error, "event": event}))
            print(f"grokbot-kit: {event['event']} event not delivered to sink {name}: {error}", file=sys.stderr)
    with os.fdopen(receipt_fd, "w", encoding="utf-8") as f:
        json.dump({"deliveries": deliveries}, f)
    record = {"dedupe_key": key, "event": event, "deliveries": deliveries}
    _append(task_dir / "events.jsonl", json.dumps(record, ensure_ascii=False))
