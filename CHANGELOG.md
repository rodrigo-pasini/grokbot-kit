# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). While the version is `0.x`, the event schema
`grokbot-kit.event/v1` may change incompatibly, always with a `Changed` or `Removed` entry here.

## [Unreleased]

### Changed

- The `skills/grokbot-kit/` skill stores secrets with `grokbot-kit secret set` reading the value from standard
  input: the bot reads the routine URL and key with its own tools or asks for each value in a masked secret field;
  a terminal on the box is only the fallback when there is no masked field. The README quick start prompt says the
  same and shows screenshots of a setup and a task.

## [0.2.0] - 2026-10-21

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
  `timeout_seconds`; `--tier` defaults to `standard`, also when `--model` is given.
- `grokbot-kit setup models refresh [<tool>] [--add <id>]...`: records in `[cli.<tool>] models` the ids printed by
  `opencode models`; for Claude the aliases `haiku`, `sonnet` and `opus` plus each added or stored id that a test
  `claude -p --model <id>` accepts; for Codex each added or stored id that a test `codex exec -m <id>` accepts. Exits
  `1` when the CLI list fails or an id is rejected; tiers are never changed.
- `grokbot-kit run` enforces the timeout: the agent runs in its own process group, which gets `SIGINT`, then `SIGTERM`
  10 s later and `SIGKILL` 10 s after that; the event is `timeout`/`timeout` and the run exits `124`. `SIGINT` or
  `SIGTERM` sent to the run is forwarded to that group (followed by the same `SIGTERM`/`SIGKILL` steps if the agent
  keeps running), the event is `error`/`interrupted` and the run exits `130`. A missing agent binary gives
  `error`/`failed` with `exit_reason` `agent_error` and exit `127`. In these three events `exit_code` is the run's own
  exit code.
- `grokbot-kit setup cli add <tool>` installs `claude`, `opencode` or `codex` with the official installer
  (`claude.ai/install.sh`, `opencode.ai/install` with `--no-modify-path`, `chatgpt.com/codex/install.sh` with
  `CODEX_HOME` set to the kit's Codex home and the binary in `~/.grokbot-kit/bin`), checks `<cli> --version` and
  records `cli.<tool>.bin`; `grokbot-kit setup default <tool>` sets `setup.default_cli`.
- `grokbot-kit login <tool> [--method subscription|api-key] [--secret <name>]`: `codex login --device-auth` or
  `codex login --with-api-key` (key from the secret on stdin) in the kit's `CODEX_HOME`, `claude auth login` or an API
  key secret recorded as `[cli.claude] api_key_secret` and passed as `ANTHROPIC_API_KEY` only to the `claude`
  processes the kit starts, and `opencode auth login`.
- `grokbot-kit doctor [--json]`: kit and Python versions and, per installed CLI, version, login state, whether it is
  the default and how many models each tier has, plus routes and secret modes; exits `1` and lists what to fix (with
  the command) when something needs attention. opencode without credentials (free models) is not a problem.
- `grokbot-kit install opencode` writes `~/.config/opencode/plugins/grokbot-kit.ts` with the absolute path of the
  `grokbot-kit` executable (rerunning replaces it); `grokbot-kit uninstall opencode` removes only that file. Outside a
  task the plugin does nothing.
- `grokbot-kit setup tiers <tool> <tier> <id>...` sets the ordered model ids of `cli.<tool>.tiers.<tier>`; exits `2`
  without changing the config when the tool is not installed or an id is not in `cli.<tool>.models`.
- The `skills/grokbot-kit/` skill for any Grok Bot: installs the kit, the chosen CLIs and their login, sets the
  default CLI and the model tiers, guides the routine with a webhook trigger (secrets only through
  `grokbot-kit secret set` in a terminal) and its route, delegates tasks with `grokbot-kit run` choosing the tier by a
  rubric, and handles the events, including `redeliver` when one did not arrive.
- `grokbot-kit gc --older-than <duration> [--dry-run]` removes (or only lists) the task dirs whose task finished more
  than `<duration>` ago (`30d`, `12h`, ...), never a task still running nor one with a non-empty `undelivered.jsonl`;
  an invalid duration exits `2`.

## [0.1.0] - 2026-10-19

### Added

- Repository scaffold: MIT license, Python package `grokbot-kit` built with `uv_build`, `ruff`, `mypy --strict`,
  `pytest`, `pre-commit`, CI and release workflows, Dependabot, issue and pull request templates.
- `grokbot-kit --version`. The commands described in the README are not implemented yet.

[Unreleased]: https://github.com/rodrigo-pasini/grokbot-kit/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/rodrigo-pasini/grokbot-kit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/rodrigo-pasini/grokbot-kit/releases/tag/v0.1.0
