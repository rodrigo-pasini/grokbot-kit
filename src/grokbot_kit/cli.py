"""Ponto de entrada do executável `grokbot-kit`."""

import argparse

from grokbot_kit import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="grokbot-kit",
        description="Delegate tasks to headless coding agents and wake the right Grok Bot routine.",
    )
    parser.add_argument("--version", action="version", version=f"grokbot-kit {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
