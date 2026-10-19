"""Leitura do config do kit (door 3); o serializador chega no S4."""

import tomllib
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    pass


def config_path() -> Path:
    return Path.home() / ".config" / "grokbot-kit" / "config.toml"


def secrets_dir() -> Path:
    return Path.home() / ".secrets" / "grokbot-kit"


def tasks_dir() -> Path:
    return Path.home() / ".grokbot-kit" / "tasks"


def load() -> dict[str, Any]:
    path = config_path()
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        raise ConfigError(f"config not found: {path}") from None
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"invalid config {path}: {e}") from None
