# grokbot-kit

Grok Bot integration kit: delegate tasks to headless coding agents (opencode, Claude Code, Codex) and wake the right
Grok Bot routine when they finish or need input.

> Leia em português: [docs/pt-BR/README.md](docs/pt-BR/README.md)

**Status:** pre-release. The repository scaffold is in place; the commands below are being built and are not usable
yet.

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

`pipx install grokbot-kit` also works. Before the first release, install from the repository:

```sh
uv tool install git+https://github.com/rodrigo-pasini/grokbot-kit
```

Requires Linux and Python 3.11 or newer (`uv` manages the interpreter). The package has no runtime dependencies.

## Quick start

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
