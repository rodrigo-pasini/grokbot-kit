"""Prova da instalação isolada com `uv tool` (check C123; door 6). Roda só com `-m integration`.

O wheel é construído deste checkout e instalado num `HOME` limpo. O cache e os Pythons gerenciados do `uv` do
usuário são reaproveitados (`UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR`) para não baixar de novo um Python que já está
no box; o ambiente da ferramenta e o executável ficam no `HOME` limpo.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

TYPE_CHECKING = False
if TYPE_CHECKING:
    from conftest import Receiver

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]


def uv() -> str:
    found = shutil.which("uv")
    if found is None:
        pytest.fail("uv não está instalado no box")
    return found


def uv_dir(*args: str) -> str:
    return subprocess.run([uv(), *args], capture_output=True, text=True, check=True).stdout.strip()


# C123 - door 6
def test_uv_tool_install_isolated(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    subprocess.run([uv(), "build", "--wheel", "-o", str(dist)], cwd=ROOT, capture_output=True, check=True)
    (wheel,) = dist.glob("grokbot_kit-*.whl")

    home = tmp_path / "home"
    home.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith(("UV_", "XDG_", "VIRTUAL_ENV", "PYTHON"))}
    bin_dir = home / ".local" / "bin"
    env.update(
        HOME=str(home),
        PATH=os.pathsep.join([str(bin_dir), os.path.dirname(uv()), "/usr/bin", "/bin"]),
        UV_CACHE_DIR=uv_dir("cache", "dir"),
        UV_PYTHON_INSTALL_DIR=uv_dir("python", "dir"),
    )
    installed = subprocess.run(
        [uv(), "tool", "install", "--managed-python", str(wheel)], capture_output=True, text=True, env=env, check=False
    )
    assert installed.returncode == 0, installed.stderr

    exe = bin_dir / "grokbot-kit"
    assert exe.exists()
    version = subprocess.run([str(exe), "--version"], capture_output=True, text=True, env=env, check=False)
    assert version.returncode == 0, version.stderr
    assert version.stdout.startswith("grokbot-kit ")

    tool_python = home / ".local" / "share" / "uv" / "tools" / "grokbot-kit" / "bin" / "python"
    assert tool_python.exists()
    real_python = Path(os.path.realpath(tool_python))
    assert real_python.is_relative_to(Path(env["UV_PYTHON_INSTALL_DIR"])), real_python

    system = subprocess.run(
        ["/usr/bin/python3", "-I", "-c", "import grokbot_kit"], capture_output=True, text=True, env=env, check=False
    )
    assert system.returncode != 0
    assert "ModuleNotFoundError" in system.stderr


def install_kit(tmp_path: Path) -> tuple[Path, dict[str, str], Path]:
    """O kit instalado por `uv tool install --managed-python <wheel deste checkout>` num `HOME` limpo."""
    dist = tmp_path / "dist"
    subprocess.run([uv(), "build", "--wheel", "-o", str(dist)], cwd=ROOT, capture_output=True, check=True)
    (wheel,) = dist.glob("grokbot_kit-*.whl")
    home = tmp_path / "home"
    home.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith(("UV_", "XDG_", "VIRTUAL_ENV", "PYTHON"))}
    bin_dir = home / ".local" / "bin"
    env.update(
        HOME=str(home),
        PATH=os.pathsep.join([str(bin_dir), os.path.dirname(uv()), "/usr/bin", "/bin"]),
        UV_CACHE_DIR=uv_dir("cache", "dir"),
        UV_PYTHON_INSTALL_DIR=uv_dir("python", "dir"),
    )
    installed = subprocess.run(
        [uv(), "tool", "install", "--managed-python", str(wheel)], capture_output=True, text=True, env=env, check=False
    )
    assert installed.returncode == 0, installed.stderr
    return home, env, bin_dir / "grokbot-kit"


# C10 - kit-update AC 9, door 5
def test_update_installer_uv(tmp_path: Path) -> None:
    from conftest import closed_port_url

    _, env, exe = install_kit(tmp_path)
    env["GROKBOT_KIT_PYPI_URL"] = closed_port_url()
    result = subprocess.run(
        [str(exe), "update", "check", "--json"], capture_output=True, text=True, env=env, check=False
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["installer"] == "uv"


# C31 - kit-update AC 17, AC 18, door 5
def test_update_apply_uv(tmp_path: Path, receiver: "Receiver") -> None:
    home, env, exe = install_kit(tmp_path)
    plugin = subprocess.run([str(exe), "install", "opencode"], env=env, capture_output=True, check=False)
    assert plugin.returncode == 0, plugin.stderr
    receiver.respond((200, json.dumps({"info": {"version": "9.0.0"}})))
    env["GROKBOT_KIT_PYPI_URL"] = receiver.url
    result = subprocess.run(
        [str(exe), "update", "apply"], capture_output=True, text=True, env=env, timeout=600, check=False
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("grokbot-kit ")
    assert " -> " in result.stdout
    plugin = (home / ".config" / "opencode" / "plugins" / "grokbot-kit.ts").read_text(encoding="utf-8")
    assert f"const GROKBOT_KIT = {json.dumps(str(exe))}" in plugin
