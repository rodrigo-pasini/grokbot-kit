"""Ponto de entrada do executável `grokbot-kit`.

`grokbot-kit emit` é chamado pelos hooks dos agentes e respeita a door 6: o despacho acontece antes de qualquer
import além de `os` e `sys`, então `argparse` e o resto só carregam nos outros comandos.
"""

import sys

# `typing` também fica fora do caminho do `emit`; o mypy reconhece o nome `TYPE_CHECKING` mesmo sem ele.
TYPE_CHECKING = False
if TYPE_CHECKING:
    import argparse


def build_parser() -> "argparse.ArgumentParser":
    import argparse

    from grokbot_kit import __version__
    from grokbot_kit.launch import TOOLS

    parser = argparse.ArgumentParser(
        prog="grokbot-kit",
        description="Delegate tasks to headless coding agents and wake the right Grok Bot routine.",
    )
    parser.add_argument("--version", action="version", version=f"grokbot-kit {__version__}")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="run a headless agent task and notify the target when it ends")
    run.add_argument("--tool", choices=TOOLS)
    run.add_argument("--model")
    run.add_argument("--tier", choices=("trivial", "standard", "complex"))
    run.add_argument("--target", required=True)
    run.add_argument("--label", required=True)
    run.add_argument("--cwd")
    run.add_argument("--prompt-file")
    run.add_argument("extras", nargs="*", metavar="-- ARGS", help="passed verbatim to the agent CLI")

    emit = sub.add_parser("emit", help="called by agent hooks inside a task")
    emit.add_argument("--from", dest="source", choices=TOOLS, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args_list = sys.argv[1:] if argv is None else argv
    if args_list[:1] == ["emit"]:
        from grokbot_kit import emit

        return emit.main(args_list[1:])

    parser = build_parser()
    args = parser.parse_args(args_list)
    if args.command == "run":
        from grokbot_kit.run import run

        return run(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
