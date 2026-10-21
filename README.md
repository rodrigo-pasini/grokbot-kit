# grokbot-kit

Grok Bot integration kit: delegate tasks to headless coding agents (opencode, Claude Code, Codex) and wake the right
Grok Bot routine when they finish or need input.

> Leia em português: [docs/pt-BR/README.md](docs/pt-BR/README.md)

**Status:** `0.x`. The commands below work; the event schema `grokbot-kit.event/v1` may still change, always with a
[CHANGELOG](CHANGELOG.md) entry.

## What it is

A Grok Bot that delegates a long task to a headless coding agent hibernates while the agent runs, and nothing wakes
it up. The exit code alone does not tell whether the task was done, failed, or stopped at a permission prompt.

`grokbot-kit` wraps the agent run (`grokbot-kit run`), listens to each agent's native hooks, and sends exactly one
terminal event (`completed`, `error` or `timeout`) — plus a `needs_input` event when the agent hits a permission — to
the webhook trigger of the routine of the bot that delegated the task. Other bots are not woken up.

## Install

```sh
uv tool install --managed-python grokbot-kit
```

`pipx install grokbot-kit` also works. To try what is on `main` before it is released:

```sh
uv tool install --managed-python git+https://github.com/rodrigo-pasini/grokbot-kit
```

Requires Linux and Python 3.11 or newer (`uv` manages the interpreter). The package has no runtime dependencies.

## Quick start

### With a Grok Bot

Send this message to the bot. It installs the [skill](#grok-bot-skill) and walks you through the setup: the kit, the
CLIs and their login, the default CLI, the model tiers and the routine that the bot's events wake up. Replace
`mybot` with a short name for the bot (letters, digits, `.`, `_` and `-`).

```text
Install the grokbot-kit skill and set up grokbot-kit on this box:
1. Download https://raw.githubusercontent.com/rodrigo-pasini/grokbot-kit/v0.2.0/skills/grokbot-kit/SKILL.md
   to /home/box/agent-data/workflows/grokbot-kit/SKILL.md (create the directory).
2. Read that skill and follow its "Setup (primeira vez)" section from start to finish, one step at a time,
   skipping what `grokbot-kit doctor --json` shows as already done. Use "mybot" as the name of this bot.
3. Never ask me for a secret (API key, routine URL or key) in the chat: tell me the `grokbot-kit secret set`
   command and I run it in a terminal on the box.
4. At the end, run `grokbot-kit doctor --json` and summarise the result and any problems.
```

The skill asks you to create the routine in the Grok Bot panel, with a webhook trigger and the routine prompt it
gives you. Copy the routine URL and key from the panel only into the box terminal, never into the chat or a
screenshot. When the setup ends, ask for a small task, such as "rename the variables in x.py": the bot picks the
`trivial` tier and tells you so, and the result arrives through the routine.

### By hand

```sh
grokbot-kit setup cli add opencode
grokbot-kit setup default opencode
grokbot-kit secret set mybot-url
grokbot-kit secret set mybot-key
grokbot-kit route add mybot --url-secret mybot-url --key-secret mybot-key
grokbot-kit route test mybot
grokbot-kit run --target mybot --label rename-vars -- "Rename the variables in x.py"
```

## Grok Bot skill

`skills/grokbot-kit/` is a skill for any Grok Bot. Copy the folder into the bot's workflows directory and the bot can
install the kit, install and log in to the CLIs you choose, create the route to its own routine, and delegate tasks
choosing CLI and model.

## Configuration

The configuration lives in `~/.config/grokbot-kit/config.toml`: installed CLIs and the default one, model tiers
(`trivial`, `standard`, `complex`) per CLI, timeouts per tier, and one route per target bot. Each task keeps its
output, logs and events in `~/.grokbot-kit/tasks/<task_id>/` until `grokbot-kit gc` removes it.

## Security

- Secrets (routine URL and key, API keys) are written with `grokbot-kit secret set` to `~/.secrets/grokbot-kit/`
  with mode `0600`, never to the config file and never pasted into a chat.
- `grokbot-kit` never writes a secret to logs, stdout, stderr or events.
- `~/.claude/settings.json` and `~/.codex/` are never modified; Codex runs in its own `CODEX_HOME`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE). Third-party material in this repository is listed in [NOTICE](NOTICE).
