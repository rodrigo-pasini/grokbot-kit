# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). While the version is `0.x`, the event schema
`grokbot-kit.event/v1` may change incompatibly, always with a `Changed` or `Removed` entry here.

## [Unreleased]

### Added

- `grokbot-kit run`: launches `claude`, `opencode` or `codex` headless with stdin on `/dev/null`, keeps the task in
  `~/.grokbot-kit/tasks/<task_id>/` and sends exactly one terminal event (`completed`/`ok`, `completed`/`denied` or
  `error`/`failed`) to the target's route; exits with the agent's exit code. Only the `file` sink delivers so far.
- Terminal events carry `repo` (`root`, `branch`, `head` when `cwd` is inside a git repository with a commit),
  `session_id` and `resume_hint` (the command that resumes the agent session), and the `transcript_path` reported by
  the agent hook.
- Config keys `[cli.<tool>] models` (discovered model ids) and arguments after `--` passed verbatim to the agent CLI.
- `grokbot-kit emit --from claude|codex|opencode`: called by the agent hooks inside a task, sends one `needs_input`
  event (`status` `permission` or `question`) per distinct request, recorded in the task dir so the terminal event
  becomes `completed`/`denied`; always exits `0`, prints at most `{}`, and does nothing outside a task.
- The opencode plugin forwards `permission.asked` (root sessions only) and `question.asked` to `grokbot-kit emit`.

## [0.1.0] - 2026-10-19

### Added

- Repository scaffold: MIT license, Python package `grokbot-kit` built with `uv_build`, `ruff`, `mypy --strict`,
  `pytest`, `pre-commit`, CI and release workflows, Dependabot, issue and pull request templates.
- `grokbot-kit --version`. The commands described in the README are not implemented yet.

[Unreleased]: https://github.com/rodrigo-pasini/grokbot-kit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/rodrigo-pasini/grokbot-kit/releases/tag/v0.1.0
