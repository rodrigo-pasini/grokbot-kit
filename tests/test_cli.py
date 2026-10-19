"""Fumaça do executável instalado pelo pacote."""

import shutil
import subprocess
import sys

from grokbot_kit import __version__


def test_cli_version() -> None:
    exe = shutil.which("grokbot-kit")
    assert exe is not None, "console script grokbot-kit não instalado"
    result = subprocess.run([exe, "--version"], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == f"grokbot-kit {__version__}"


def test_emit_without_task_id_exits_0() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "grokbot_kit.emit"], capture_output=True, text=True, env={}, check=False
    )
    assert result.returncode == 0
    assert result.stdout == ""
