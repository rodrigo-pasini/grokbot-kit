# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). While the version is `0.x`, the event schema
`grokbot-kit.event/v1` may change incompatibly, always with a `Changed` or `Removed` entry here.

## [Unreleased]

### Added

- `grokbot-kit run`: launches `claude`, `opencode` or `codex` headless with stdin on `/dev/null`, keeps the task in
  `~/.grokbot-kit/tasks/<task_id>/` and sends exactly one terminal event (`completed`/`ok`, `completed`/`denied` or
  `error`/`failed`) to the target's route; exits with the agent's exit code.
- Terminal events carry `repo` (`root`, `branch`, `head` when `cwd` is inside a git repository with a commit),
  `session_id` and `resume_hint` (the command that resumes the agent session), and the `transcript_path` reported by
  the agent hook.
- Config keys `[cli.<tool>] models` (discovered model ids) and arguments after `--` passed verbatim to the agent CLI.
- `grokbot-kit emit --from claude|codex|opencode`: called by the agent hooks inside a task, sends one `needs_input`
  event (`status` `permission` or `question`) per distinct request, recorded in the task dir so the terminal event
  becomes `completed`/`denied`; always exits `0`, prints at most `{}`, and does nothing outside a task.
- The opencode plugin forwards `permission.asked` (root sessions only) and `question.asked` to `grokbot-kit emit`.
  Known limits: `opencode run` denies the question tool, so `question` events do not occur in tasks; `codex exec` never
  asks for approval, so Codex tasks send no `needs_input` and a denied command ends `completed`/`ok`.
- Sinks `grokbot-routine` (POST to the routine webhook with `Authorization: Bearer <key>`, receipt `runUuid` recorded
  in the task dir), `file`, `ntfy` and `slack`. Retries after 1 s and 4 s on `429`, `5xx` and connection failures;
  what is not delivered goes to `undelivered.jsonl` and stderr names `grokbot-kit redeliver <task_id>`.
- `grokbot-kit run` exits `2` before launching when the target has no route or a route secret is missing or not `0600`.
- `grokbot-kit redeliver <task_id>`, `grokbot-kit route add|rm|test <target>` and `grokbot-kit secret set <name>`
  (read from the terminal without echo, or from stdin, and stored in `~/.secrets/grokbot-kit/` with mode `0600`).
- The config is checked when loaded: `setup.default_cli` must be in `setup.installed`, and every id in
  `cli.<tool>.tiers` must be in `cli.<tool>.models`; otherwise commands exit `2` naming the key.
- `grokbot-kit run --timeout <duration>` (`30s`, `30m`, `2h`, `1d`): without it the timeout is `timeouts.<tier>` from
  the config (defaults `trivial = "30m"`, `standard = "2h"`, `complex = "4h"`), recorded in `meta.json` as
  `timeout_seconds`; `--tier` defaults to `standard`, also when `--model` is given. The timeout is not enforced yet.

## [0.1.0] - 2026-10-19

### Added

- Repository scaffold: MIT license, Python package `grokbot-kit` built with `uv_build`, `ruff`, `mypy --strict`,
  `pytest`, `pre-commit`, CI and release workflows, Dependabot, issue and pull request templates.
- `grokbot-kit --version`. The commands described in the README are not implemented yet.

[Unreleased]: https://github.com/rodrigo-pasini/grokbot-kit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/rodrigo-pasini/grokbot-kit/releases/tag/v0.1.0
