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
    run.add_argument("--timeout", help="duration such as 30m, 2h or 1d; defaults to timeouts.<tier> in the config")
    run.add_argument("--cwd")
    run.add_argument("--prompt-file")
    run.add_argument("extras", nargs="*", metavar="-- ARGS", help="passed verbatim to the agent CLI")

    emit = sub.add_parser("emit", help="called by agent hooks inside a task")
    emit.add_argument("--from", dest="source", choices=TOOLS, required=True)

    redeliver = sub.add_parser("redeliver", help="resend the events of a task that were not delivered")
    redeliver.add_argument("task_id")

    route = sub.add_parser("route", help="manage the route (sinks) of each target bot")
    route_sub = route.add_subparsers(dest="route_command", required=True)
    route_add = route_sub.add_parser("add", help="route a target to its Grok Bot routine")
    route_add.add_argument("target")
    route_add.add_argument("--url-secret", required=True, help="secret holding the routine webhook URL")
    route_add.add_argument("--key-secret", required=True, help="secret holding the routine key (crsr_...)")
    route_add.add_argument("--header", action="append", default=[], help="extra header, 'Name: value'")
    route_sub.add_parser("rm", help="remove the route of a target").add_argument("target")
    route_sub.add_parser("test", help="send a test event to every sink of the route").add_argument("target")

    setup = sub.add_parser("setup", help="set up the agent CLIs")
    setup_sub = setup.add_subparsers(dest="setup_command", required=True)
    models = setup_sub.add_parser("models", help="model ids discovered for each CLI")
    models_sub = models.add_subparsers(dest="models_command", required=True)
    refresh = models_sub.add_parser("refresh", help="discover the model ids of a CLI (or of every installed one)")
    refresh.add_argument("tool", nargs="?", choices=TOOLS)
    refresh.add_argument(
        "--add", action="append", default=[], metavar="ID", help="claude/codex: also test and record this model id"
    )

    secret = sub.add_parser("secret", help="store secrets in ~/.secrets/grokbot-kit/ (mode 0600)")
    secret_sub = secret.add_subparsers(dest="secret_command", required=True)
    secret_sub.add_parser("set", help="read a secret from the terminal (no echo) or stdin").add_argument("name")
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
    if args.command == "redeliver":
        from grokbot_kit.redeliver import redeliver

        return redeliver(args.task_id)
    if args.command == "route":
        from grokbot_kit import route

        if args.route_command == "add":
            return route.add(args.target, args.url_secret, args.key_secret, args.header)
        return route.rm(args.target) if args.route_command == "rm" else route.test(args.target)
    if args.command == "setup":
        from grokbot_kit.models import refresh

        return refresh(args.tool, args.add)
    if args.command == "secret":
        from grokbot_kit.secret import set_secret

        return set_secret(args.name)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
