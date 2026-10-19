"""`grokbot-kit emit`: chamado pelos hooks dos agentes dentro de uma task.

Antes do gate de `GROKBOT_KIT_TASK_ID` só entram `os`, `sys` e `json` (door 6); o resto é
carregado sob demanda. O emit nunca envia evento terminal (door 5): o registro e o envio de
`needs_input` chegam no S3.
"""

import os
import sys


def main(argv: list[str] | None = None) -> int:
    if not os.environ.get("GROKBOT_KIT_TASK_ID"):
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
