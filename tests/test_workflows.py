"""Provas do S0 sobre os workflows e o Dependabot (checks C13-C15, C19, C38)."""

import itertools
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load(rel: str) -> dict[str, Any]:
    data: dict[str, Any] = yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))
    # PyYAML lê a chave `on` como o booleano True.
    if True in data:
        data["on"] = data.pop(True)
    return data


def runs(job: dict[str, Any]) -> str:
    return "\n".join(step.get("run", "") for step in job["steps"])


def job_names(job_id: str, job: dict[str, Any]) -> list[str]:
    name = job.get("name", job_id)
    matrix = job.get("strategy", {}).get("matrix", {})
    if not matrix:
        return [name]
    keys = [key for key in matrix if key not in ("include", "exclude")]
    names = []
    for combo in itertools.product(*(matrix[key] for key in keys)):
        expanded = name
        for key, value in zip(keys, combo, strict=True):
            expanded = expanded.replace(f"${{{{ matrix.{key} }}}}", str(value))
        names.append(expanded)
    return names


# C13 - AC 10
def test_ci_jobs_and_triggers() -> None:
    ci = load(".github/workflows/ci.yml")
    assert ci["on"]["push"]["branches"] == ["main"]
    assert ci["on"]["pull_request"]["branches"] == ["main"]
    jobs = ci["jobs"]
    names = {name: job_id for job_id, job in jobs.items() for name in job_names(job_id, job)}
    assert sorted(names) == sorted(["lint", "typecheck", "test (3.11)", "test (3.12)", "test (3.13)"])
    for job in jobs.values():
        assert job["runs-on"] == "ubuntu-latest"
        assert "uv sync --locked" in runs(job)
    lint = runs(jobs[names["lint"]])
    assert "uv run ruff check" in lint
    assert "uv run ruff format --check" in lint
    assert "uv run mypy" in runs(jobs[names["typecheck"]])
    test_job = jobs[names["test (3.11)"]]
    assert "uv run pytest" in runs(test_job)
    assert [str(v) for v in test_job["strategy"]["matrix"]["python"]] == ["3.11", "3.12", "3.13"]


# C14 - AC 11
def test_release_jobs_and_permissions() -> None:
    release = load(".github/workflows/release.yml")
    assert release["on"] == {"push": {"tags": ["v*"]}}
    build = release["jobs"]["build"]
    publish = release["jobs"]["publish"]
    assert "id-token" not in build.get("permissions", {})
    assert "id-token" not in release.get("permissions", {})
    assert "uv build" in runs(build)
    uploads = [s for s in build["steps"] if s.get("uses", "").startswith("actions/upload-artifact@")]
    assert len(uploads) == 1 and uploads[0]["with"]["path"].rstrip("/") == "dist"
    assert publish["needs"] in ("build", ["build"])
    environment = publish["environment"]
    assert environment == "pypi" or environment.get("name") == "pypi"
    assert publish["permissions"] == {"id-token": "write", "contents": "write"}
    uses = [s.get("uses", "") for s in publish["steps"]]
    assert "pypa/gh-action-pypi-publish@release/v1" in uses
    pypi_step = next(s for s in publish["steps"] if s.get("uses") == "pypa/gh-action-pypi-publish@release/v1")
    assert "password" not in pypi_step.get("with", {})
    attach = [s for s in publish["steps"] if "gh release create" in s.get("run", "")]
    assert len(attach) == 1 and "dist/*" in attach[0]["run"]


# C15 - AC 12
def version_check_step() -> dict[str, Any]:
    build = load(".github/workflows/release.yml")["jobs"]["build"]
    steps = [s for s in build["steps"] if "version" in s.get("name", "").lower() and "run" in s]
    assert len(steps) == 1, "o job build precisa de exatamente um passo de checagem de versão"
    names = [s.get("name") for s in build["steps"]]
    build_step = next(s for s in build["steps"] if "uv build" in s.get("run", ""))
    assert names.index(steps[0]["name"]) < names.index(build_step.get("name")), "checagem depois do build"
    return steps[0]


@pytest.mark.parametrize(("tag", "version", "ok"), [("v0.2.0", "0.1.0", False), ("v0.1.0", "0.1.0", True)])
def test_release_version_mismatch_fails(tmp_path: Path, tag: str, version: str, ok: bool) -> None:
    step = version_check_step()
    (tmp_path / "pyproject.toml").write_text(f'[project]\nname = "grokbot-kit"\nversion = "{version}"\n')
    result = subprocess.run(
        ["bash", "-e", "-c", step["run"]],
        cwd=tmp_path,
        check=False,
        env={"PATH": "/usr/bin:/bin", "GITHUB_REF_NAME": tag, "GITHUB_REF": f"refs/tags/{tag}"},
        capture_output=True,
    )
    assert (result.returncode == 0) is ok


# C19 - AC 17
def test_dependabot_ecosystems() -> None:
    dependabot = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
    assert dependabot["version"] == 2
    updates = {u["package-ecosystem"]: u for u in dependabot["updates"]}
    assert set(updates) == {"uv", "github-actions"}
    for update in updates.values():
        assert update["schedule"]["interval"] == "weekly"
        assert update["directory"] == "/"


# C38 - AC 35
def test_release_reads_no_secret() -> None:
    text = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "secrets." not in text
    assert "secrets[" not in text
