"""Provas do `run` com a escolha de provedores, o `summary` de erro e o fallback de modelo do tier (model-setup-docs:
checks C12, C24, C26-C35; doors 3-6).

Na fronteira: o subprocesso `grokbot-kit run` com as CLIs falsas; `FAKE_STDOUT_BY_MODEL` dá uma saída por id.
"""

import json

from conftest import Kit, default_config


def opencode_config(kit: Kit, models: list[str], standard: list[str], providers: list[str] | None = None) -> None:
    text = default_config(kit.sink).replace('models = ["opencode/free-model"]', f"models = {json.dumps(models)}")
    text = text.replace('standard = ["opencode/free-model"]', f"standard = {json.dumps(standard)}", 1)
    if providers is not None:
        text = text.replace("[cli.opencode.tiers]", f"providers = {json.dumps(providers)}\n[cli.opencode.tiers]", 1)
    kit.write_config(text)


# C12 - AC 13: o `run` não recusa id de tier fora de `providers`
def test_run_tier_outside_providers(kit: Kit) -> None:
    opencode_config(kit, ["opencode/a-free", "opencode-go/b"], ["opencode/a-free"], ["opencode-go"])
    result = kit.run("--target", "bot-a", "--label", "l", "--", "x")
    assert result.returncode == 0, result.stderr
    argv = kit.launched()["argv"]
    assert argv[argv.index("-m") + 1] == "opencode/a-free"
