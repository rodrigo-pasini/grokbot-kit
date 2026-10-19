"""Config do kit e segredos (door 3)."""

import stat
import tomllib
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    pass


def config_path() -> Path:
    return Path.home() / ".config" / "grokbot-kit" / "config.toml"


def secrets_dir() -> Path:
    return Path.home() / ".secrets" / "grokbot-kit"


def check_secret(name: str) -> Path:
    """O caminho do segredo `name`, que precisa existir com modo `0600` (AC 65); nunca lê o conteúdo."""
    path = secrets_dir() / name
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        raise ConfigError(f"secret {name!r} not found; run: grokbot-kit secret set {name}") from None
    if mode != 0o600:
        raise ConfigError(f"secret {name!r} has mode {mode:04o}, expected 0600: {path}")
    return path


def read_secret(name: str) -> str:
    """O conteúdo do segredo `name` sem a quebra de linha final (AC 66)."""
    path = check_secret(name)
    try:
        return path.read_text(encoding="utf-8").rstrip("\r\n")
    except OSError as e:
        raise ConfigError(f"cannot read secret {name!r}: {e.strerror}") from None


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
