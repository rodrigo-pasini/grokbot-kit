"""`grokbot-kit install opencode` / `uninstall opencode`: o plugin global do opencode (AC 95-97, AD-016, AD-028)."""

import json
import os
import sys
from pathlib import Path

from grokbot_kit import launch

ASSET = Path(__file__).parent / "assets" / "opencode" / "grokbot-kit.ts"
PLACEHOLDER = '"__GROKBOT_KIT_EXE__"'


def plugin_path() -> Path:
    return Path.home() / ".config" / "opencode" / "plugins" / "grokbot-kit.ts"


def _fail(action: str, message: str) -> int:
    print(f"grokbot-kit {action} opencode: {message}", file=sys.stderr)
    return 1


def install() -> int:
    path = plugin_path()
    text = ASSET.read_text(encoding="utf-8").replace(PLACEHOLDER, json.dumps(launch.kit_executable()))
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except OSError as e:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return _fail("install", f"cannot write {path}: {e.strerror}")
    print(f"opencode plugin written to {path}")
    return 0


def uninstall() -> int:
    path = plugin_path()
    try:
        path.unlink(missing_ok=True)
    except OSError as e:
        return _fail("uninstall", f"cannot remove {path}: {e.strerror}")
    print(f"opencode plugin removed: {path}")
    return 0
