# needs-input-reply verification

**Verdict**: FAIL
**Profile**: standard
**Diff range**: 913599d..5705e3c
**Round**: 1 - full
**Verifier**: independent sub-agent (author != verifier)

Motivos do FAIL, em ordem:

1. **Mutante sobrevivente na door 1 / AC 16.** Trocar o `os.link` de `write_once` (`src/grokbot_kit/emit.py:116`)
   por `os.replace` (grava por cima, sem `O_EXCL`) passa em C24, C14, C21 e em todo `test_reply.py`,
   `test_emit_wait.py`, `test_terminal.py` e `test_run_guards.py` (166 passed). A prova da C24
   (`tests/test_reply.py:176-178`) só chama o `reply` depois de `now >= deadline`, então o `reply` sai na checagem de
   prazo (`src/grokbot_kit/reply.py:76`) e nunca chega ao `write_once` (`src/grokbot_kit/reply.py:80`); a disputa que
   a check promete não é exercida. Nenhuma prova falha se o arquivo de resposta for sobrescrito.
2. **C54 sem prova para o schema.** A segunda prova da C54, `uv run pytest tests/test_payload.py -k
   needs_input_schema_new_fields`, não seleciona teste nenhum (`60 deselected`; `rg needs_input_schema_new_fields
   tests/` não acha nada). A cláusula "o `assets/event.v1.json` aceita um `needs_input` com os dois campos" não tem
   asserção: nenhum `VALIDATOR.validate` roda sobre um `needs_input` com `reply_deadline` string (só com `null`, em
   `tests/test_payload.py:201` e `:385`); `test_schema_matches_door_2` (`tests/test_payload.py:237`) só confere os
   nomes das propriedades.
3. **Door 8 sem linha no `Coverage` e com membros sem prova.** O `Landing` enumera quem pode esperar
   (`src/grokbot_kit/emit.py:153-157`): `claude` sim, `opencode` com `GROKBOT_KIT_REPLY=1` sim, `opencode` sem a
   variável (plugin v1) não, `codex` não; e só `kind` `permission` espera. `rg '"codex"' tests/test_emit_wait.py
   tests/test_reply.py` não acha nada: nenhum teste roda o `emit --from codex` numa tarefa com espera, nem um
   `question.asked` com espera. O caso opencode-sem-variável tem teste
   (`tests/test_emit_wait.py:269` `test_opencode_without_reply_flag_is_notify_only`), mas nenhuma check o cita.
4. **Precision gap na C5.** A tolerância de `tests/test_emit_wait.py:110` (`before + 2 s <= deadline <= after + 4 s`)
   aceita uma espera 1 s menor que a pedida: o mutante `timedelta(seconds=wait - 1)` em
   `src/grokbot_kit/emit.py:215` passa na C5 (3 de 3 rodadas). Ele morre na C9 (`1 <= elapsed`,
   `tests/test_emit_wait.py:158`), então não conta como sobrevivente, mas o arredondamento para cima (decisão do
   build, "nunca fica menor que a pedida") não tem asserção própria.

## Binding sources

O plano não marca nenhuma fonte como binding no sentido de design (perfil `standard`, sem tela). Fontes lidas para
contexto: `plan.md`, `checks.md`, `research.md`, `spike.md`.

## Checks

Proof run (CI, uma invocação): `uv run pytest -rA tests/test_launch.py tests/test_run_guards.py tests/test_config.py
tests/test_emit_wait.py tests/test_reply.py tests/test_opencode_plugin.py tests/test_opencode_plugin_v2.py
tests/test_doctor.py tests/test_terminal.py tests/test_setup_upgrade.py tests/test_update.py tests/test_skill_doc.py
tests/test_docs.py tests/test_payload.py -k "<os 59 nomes>"` - exit 0, 92 passed, cada teste listado por nome em
`PASSED`. Integration (host de dev, `GROKBOT_KIT_IT_OPENCODE_MODEL=opencode-go/glm-5.3-flash`, `claude` 2.1.318,
`opencode` v2.2.4): `uv run pytest -m integration tests/integration/test_real_hooks.py tests/integration/test_install.py
-k "claude_reply_allow or opencode_reply_allow or upgrade_opencode_real"` - 3 passed.

| Check | Claim | Proof run | Evidence | Result |
| --- | --- | --- | --- | --- |
| C1 | hook `timeout` 660 com espera 600, ausente com 0 | `test_claude_settings_hook_timeout[600-660/30-90/0-None]` PASSED | `tests/test_launch.py:182` - `assert hook.get("timeout") == timeout` | PASS |
| C2 | `ask_wait_seconds` 600/120/30/0 pela precedência | `test_ask_wait_meta[...]` x5 PASSED | `tests/test_run_guards.py:295` - `assert _meta(kit)["ask_wait_seconds"] == expected` | PASS |
| C3 | `--ask-wait 10x` sai 2, sem task dir | `test_ask_wait_invalid` PASSED | `tests/test_run_guards.py:303` - `assert kit.tasks() == []` (com `returncode == 2` e `invalid duration '10x'` logo acima) | PASS |
| C4 | `[ask] wait = "abc"` -> `ConfigError` com `ask.wait`; `"0"` carrega | `test_ask_wait_validation` PASSED | `tests/test_config.py:162` - `assert "ask.wait" in str(raised.value)`; `:164` | PASS |
| C5 | `request_id` = discriminador; `reply_deadline` = pedido + 3 s, `Z`, tolerância 1 s | `test_needs_input_fields` PASSED | `tests/test_emit_wait.py:106` - `assert event["needs_input"]["request_id"] == request_id(data)`; `:110` - `before + timedelta(seconds=2) <= parse_ts(deadline) <= after + timedelta(seconds=4)` (precision gap, ver motivo 4) | PASS |
| C6 | prazo limitado por `started_at + timeout_seconds` | `test_deadline_capped_by_task_timeout` PASSED | `tests/test_emit_wait.py:120` - `assert parse_ts(event["needs_input"]["reply_deadline"]) == expected` | PASS |
| C7 | `allow` -> JSON exato da door 6, exit 0, < 3 s | `test_claude_allow` PASSED | `tests/test_emit_wait.py:131` - `assert proc.stdout == json.dumps(CLAUDE_ALLOW, separators=(",", ":"))`; `:132` `elapsed < 3` | PASS |
| C8 | `deny` com `"não"`; `null` -> `denied by the user` | `test_claude_deny_message`, `test_claude_deny_message_null` PASSED | `tests/test_emit_wait.py:141` - `== claude_deny("não")`; `:149` - `== claude_deny("denied by the user")` | PASS |
| C9 | prazo vencido grava `deny`/`timeout` e imprime `no reply before <deadline>` | `test_timeout_denies_and_records` PASSED | `tests/test_emit_wait.py:160` - `(recorded["decision"], recorded["by"]) == ("deny", "timeout")`; `:164` | PASS |
| C10 | espera 0: `reply_deadline` null, `{}`, < 1 s, sem `replies/` | `test_wait_zero_notify_only` PASSED | `tests/test_emit_wait.py:171` - `(proc.returncode, proc.stdout) == (0, "{}")`; `:174`, `:176` | PASS |
| C11 | meta antigo sem `ask_wait_seconds` = C10 | `test_old_meta_is_notify_only` PASSED | `tests/test_emit_wait.py:186` - `(proc.returncode, proc.stdout) == (0, "{}")`; `:189` | PASS |
| C12 | sink em 500 x3 e ainda espera e devolve `allow` | `test_waits_after_failed_delivery` PASSED | `tests/test_emit_wait.py:201` - `len(receiver.requests) == 3`; `:202` - `== CLAUDE_ALLOW` | PASS |
| C13 | segundo `emit` reaproveita a resposta, < 1 s, um só `needs_input` | `test_repeated_request_reuses_reply` PASSED | `tests/test_emit_wait.py:214` - `elapsed < 1`; `:215` - `len(needs_inputs(kit)) == 1` | PASS |
| C14 | dois `emit` simultâneos: um `needs_input`, ambos `allow` | `test_concurrent_same_request` PASSED | `tests/test_emit_wait.py:235` - `== [CLAUDE_ALLOW, CLAUDE_ALLOW]`; `:236` | PASS |
| C15 | resposta ilegível -> `{}`, motivo no `kit.log`, exit 0 | `test_unreadable_reply_no_decision` PASSED | `tests/test_emit_wait.py:248` - `(proc.returncode, proc.stdout) == (0, "{}")`; `:249` | PASS |
| C16 | `claude` real espera até `reply allow`, roda e termina `ok` | `-m integration test_claude_reply_allow` PASSED (rodado por este Verifier) | `tests/integration/test_real_hooks.py:176` - `(work / "criado.txt").exists()`; `:178` - `== ("completed", "ok", "success")` | PASS |
| C58 | 401: 1 tentativa e `undelivered`; 429: 3; segue esperando | `test_needs_input_delivery_statuses` PASSED | `tests/test_emit_wait.py:298` - `len(receiver.requests) == attempts`; `:302`; `:303` - `== CLAUDE_ALLOW` | PASS |
| C17 | `reply allow` grava `allow`/`null`/`user`/`at` e imprime a linha | `test_allow_recorded` PASSED | `tests/test_reply.py:70` - `== (0, f"recorded allow for {p.rid} (by user)")`; `:72` | PASS |
| C18 | `deny --message` grava a mensagem | `test_deny_with_message` PASSED | `tests/test_reply.py:83` - `== ("deny", "fora do repo")` | PASS |
| C19 | `allow --message` sai 2 sem `replies/` | `test_message_with_allow_rejected` PASSED | `tests/test_reply.py:91` - `returncode == 2`; `:93` | PASS |
| C20 | tarefa ou pedido desconhecido -> 1 com o motivo | `test_unknown_task_or_request` PASSED | `tests/test_reply.py:102` - `"task not found" in ...`; `:105` - `"no needs_input with request_id sha256:outro" in ...`; `:106` | PASS |
| C21 | já respondido / vencido -> 1, arquivo intacto | `test_already_answered_or_expired` PASSED | `tests/test_reply.py:117` - `"already answered: allow" in again.stderr`; `:118`; `:127` | PASS |
| C22 | `finished_at` -> 1 `task already finished` | `test_task_finished` PASSED | `tests/test_reply.py:151` - `"task already finished" in result.stderr`; `:152` | PASS |
| C23 | `request_id` inválido -> 2; `sha256:abc` passa | `test_request_id_charset` PASSED | `tests/test_reply.py:161` - `returncode == 2`; `:165-166` | PASS |
| C24 | `reply` x prazo no mesmo instante, 20 rodadas, uma decisão | `test_race_single_decision` PASSED | `tests/test_reply.py:181` - `len(files) == 1`; `:182` - `recorded(files[0])["decision"] == decision` - verde, mas a prova não cria a disputa (o `reply` roda depois do prazo e para em `src/grokbot_kit/reply.py:76`); o mutante F1 sobrevive | FAIL |
| C25 | `--by bot` grava, imprime e loga | `test_by_bot_logged` PASSED | `tests/test_reply.py:189` - `(by bot)`; `:190`; `:191` - `f"reply: allow for {p.rid} by bot" in ...` | PASS |
| C26 | `--by robot` -> 2 sem arquivo | `test_by_invalid` PASSED | `tests/test_reply.py:199` - `returncode == 2`; `:200` | PASS |
| C27 | `install` com v2 ou sem opencode grava o asset v2 | `test_install_picks_v2[v2/sem-opencode]` PASSED | `tests/test_opencode_plugin.py:103` - `text.splitlines()[0] == "// grokbot-kit opencode plugin for opencode 2"`; `:108` | PASS |
| C28 | `install` com v1 grava o asset v1 com marcador | `test_install_picks_v1` PASSED | `tests/test_opencode_plugin.py:119`; `:120` - `assert text == expected` | PASS |
| C29 | plugin v2 chama `emit --from opencode` com o JSON da door 14 | `test_evaluate_calls_emit` PASSED | `tests/test_opencode_plugin_v2.py:145` - `call["argv"] == ["emit", "--from", "opencode"]`; `:149`; `:151-156` | PASS |
| C30 | não bloqueia (>= 10 ticks) e timeout = espera + 60 s | `test_does_not_block` PASSED | `tests/test_opencode_plugin_v2.py:163` - `out["ticks"] >= 10`; `:164` - `== [{"timeout": (5 + 60) * 1000}]` | PASS |
| C31 | aplica `allow`/`deny`; `{}`, vazio, não JSON, exit 1, timeout deixam `ask` | `test_applies_emit_decision[7 ids]` PASSED | `tests/test_opencode_plugin_v2.py:183` - `out["event"]["effect"] == effect`; `:184` | PASS |
| C32 | `effect` da config ou sessão filha não chamam o kit | `test_only_root_ask[3]` PASSED | `tests/test_opencode_plugin_v2.py:193`; `:194` - `harness.calls() == []` | PASS |
| C33 | sem `GROKBOT_KIT_TASK_ID`, inerte | `test_inert_without_task` PASSED | `tests/test_opencode_plugin_v2.py:200` - `out["registered"] == 0`; `:202` | PASS |
| C34 | `emit --from opencode` imprime o JSON exato da door 6 | `test_opencode_effect_output` PASSED | `tests/test_emit_wait.py:264` - `(proc.returncode, proc.stdout) == (0, expected)` | PASS |
| C35 | `doctor` acusa asset fora do major; sem marcador = 1 | `test_plugin_major_mismatch[3]` PASSED | `tests/test_doctor.py:424` - `assert expected in out["problems"]` (com `code == 1` acima) | PASS |
| C36 | `run` reescreve antes de lançar; certo = mtime igual; ausente = nada | `test_run_rewrites_stale_plugin`, `..._untouched_when_current`, `..._absent` PASSED | `tests/test_run_guards.py:378`; `:380`; `:397` - `st_mtime == 1_000_000_000`; `:408` | PASS |
| C37 | reescrita falha: loga e a tarefa roda | `test_run_plugin_rewrite_failure` PASSED | `tests/test_run_guards.py:426` - `"cannot rewrite the opencode plugin" in log`; `:429` | PASS |
| C59 | `--standalone` com v2.2.4, sem ele com v1.19.3 | `test_opencode_standalone_by_major[2]` PASSED | `tests/test_launch.py:200` - `kit.launched()["argv"] == ["run", "--format", "json", "-m", MODELS["opencode"], *flag, "oi"]` | PASS |
| C38 | `opencode` 2.x real espera até `reply allow` e termina `ok` | `-m integration test_opencode_reply_allow` PASSED (rodado por este Verifier, `opencode-go/glm-5.3-flash`) | `tests/integration/test_real_hooks.py:186`; `:188` (marcador 2); `:190` - `== ("completed", "ok", "success")` | PASS |
| C39 | dois `allow` -> `completed/ok/success` | `test_all_allowed_is_success` PASSED | `tests/test_terminal.py:410` - `classify(...) == ("completed", "ok", "success")` | PASS |
| C40 | sem resposta / deny / timeout / `permission_denials` -> `denied` | `test_any_unallowed_is_denied[3]`, `..._permission_denials`, `..._legacy_record` PASSED | `tests/test_terminal.py:422` - `unanswered(...) == [asked[1]]`; `:424`; `:435` | PASS |
| C41 | `run` com pedido respondido `allow` termina `ok` | `test_run_allowed_request_ends_ok` PASSED | `tests/test_run_guards.py:347` - `== ("completed", "ok", "success")` | PASS |
| C42 | tarefa de plugin não espera nem entrega | `test_plugin_task_no_wait` PASSED | `tests/test_emit_wait.py:283` - `(0, "{}")`; `:284` `elapsed < 1`; `:285` `needs_inputs(kit) == []` | PASS |
| C43 | upgrade imprime `old -> new` / `already the latest` | `test_upgrade_prints_versions` PASSED | `tests/test_setup_upgrade.py:27`; `:28` - argv `[["--no-modify-path"]] * 2`; `:32` | PASS |
| C44 | upgrade de `claude` e `codex` com o argv do `add` | `test_upgrade_each_tool[claude/codex]` PASSED | `tests/test_setup_upgrade.py:44` - `calls[1] == {**calls[0], "path": ...}`; `:46` | PASS |
| C45 | sem `bin` -> 2 com a mensagem; `foo` -> 2 | `test_upgrade_not_installed` PASSED | `tests/test_setup_upgrade.py:54`; `:55`; `:56` | PASS |
| C46 | falha do instalador ou do `--version` -> 1, config intacto | `test_upgrade_failure_keeps_config[2]` PASSED | `tests/test_setup_upgrade.py:73` - `fresh.config_text() == before` (com `returncode == 1` acima) | PASS |
| C47 | reescreve o plugin; ausente não cria; sem escrita -> 1 | `test_upgrade_rewrites_plugin`, `..._absent`, `..._unwritable` PASSED | `tests/test_setup_upgrade.py:84`; `:92`; `:105` | PASS |
| C48 | aviso do opencode 1.x fora de `problems`, exit igual | `test_opencode_1_warning` PASSED | `tests/test_doctor.py:442` - `["warning"] == warning`; `:449` - `code == code_2` | PASS |
| C49 | `setup cli upgrade opencode` real leva à última versão | `-m integration test_upgrade_opencode_real` PASSED (rodado por este Verifier) | `tests/integration/test_install.py:206` - `latest in version.stdout`; `:207` | PASS |
| C57 | `update apply` + v2.2.4 termina com o plugin v2 | `test_apply_rewrites_plugin_for_major` PASSED | `tests/test_update.py:691` - `call["argv"] == ["install", "opencode"]`; `:703` | PASS |
| C50 | SKILL: `reply_deadline` preenchido -> regra de risco; `null` -> `resume_hint` | `test_needs_input_reply_flow` PASSED | `tests/test_skill_doc.py:519`; `:521` | PASS |
| C51 | lista de baixo risco exata, sem `rm`/`push`/`curl`/`install` | `test_risk_rule_low_list` PASSED | `tests/test_skill_doc.py:533` - `len(items) == 4`; `:541` | PASS |
| C52 | lista de perguntar ao usuário | `test_risk_rule_ask_list` PASSED | `tests/test_skill_doc.py:563` - `assert needle in ask, needle` | PASS |
| C53 | `--by bot`, `--by user`, nunca nega sozinho, upgrade; comandos existem | `test_reply_by_and_upgrade`, `test_every_cited_command_exists` PASSED | `tests/test_skill_doc.py:570`; `:573`; `:576`; `tests/test_skill_doc.py:286` - `result.returncode == 0` por comando citado | PASS |
| C54 | README/event.md nas duas línguas; schema aceita os campos novos | `gate_*_repo_clean`, `test_needs_input_reply_docs` PASSED; `tests/test_payload.py -k needs_input_schema_new_fields` -> 0 selecionados | `tests/test_docs.py:357`; `:362`; `:363`; schema: nenhuma asserção (ver motivo 2) | FAIL |
| C55 | README diz Claude/opencode 2.x/1.x e o upgrade | `test_opencode_version_note` PASSED | `tests/test_docs.py:372`; `:373` | PASS |
| C56 | CHANGELOG `[Unreleased]` com os 10 termos | `test_changelog_needs_input_reply` PASSED | `tests/test_docs.py:392` - `assert term in unreleased, term` | PASS |

Testes antigos que mudaram de valor (convenções do `checks.md`), conferidos no diff `913599d..HEAD`: nenhum afrouxou.
`tests/test_launch.py` e `tests/test_docs.py` trocam `13` por `14` com `reply` no conjunto exato;
`tests/test_run_plugin.py::test_run_without_plugin_unchanged` segue com igualdade exata do argv (agora com
`--standalone`) e do `claude-settings.json` (agora com `"timeout": 660`); `tests/test_payload.py:237` passa a exigir
o conjunto exato de 5 chaves; as provas do aviso (`run_with_emits`, `test_transcript_path_from_hook_cli_through_emit`,
`test_exactly_one_terminal_per_task`, `[ask] wait = "0"` em `test_real_cli.py`) só ganham `--ask-wait 0`, sem
mudança de asserção; o teste da AC 44 (`tests/test_terminal.py:64-67`) não mudou; `tests/test_run_fallback.py`
filtra só as chamadas `["--version"]`. Suíte inteira do CI: 1089 passed.

## Coverage

| Set (size) | Recomputed from | Member -> proof | Unproven |
| --- | --- | --- | --- |
| `POST` webhook statuses (4) | tabela de retry da agent-run-notify (`deliver.py`) | `200` C5 · `401` C58 · `429` C58 · `500` C12, C58 | - |
| `reply` exit codes (3) | `src/grokbot_kit/reply.py` + argparse em `cli.py` | `0` C17 · `1` C20-C22 · `2` C19, C23, C26 | - |
| `reply` recusas com `1` (6) | `reply.py:62-81` | task C20 · finished C22 · request C20 · já respondido C21 · prazo vencido C21 · pedido sem espera (`reply.py`, `does not wait for a reply`) só em `test_notify_only_request_refused`, sem check | - |
| `reply` recusas com `2` (3) | `reply.py:57-60`, argparse `--by` | C19 · C23 · C26 | - |
| `setup cli upgrade` exit codes (3) | `setup.py` `cli_upgrade` | `0` C43 · `1` C46, C47 · `2` C45 | - |
| `setup cli upgrade` tools (3) | `launch.TOOLS` | opencode C43 · claude C44 · codex C44 | - |
| precedência da espera (4) | `resolve.ask_wait` | C2 x5 | - |
| espera inválida (2) | `resolve.ask_wait` em `run` e `config.check_constraints` | flag C3 · config C4 | - |
| desfechos do `emit` com espera (7) | `emit.py:181-243` | allow C7 · deny msg C8 · deny null C8 · prazo C9 · espera 0 C10 · reaproveitada C13 · ilegível C15 | - |
| saída por fonte, door 6 (5) | `emit._answer` | C7 · C8 · C34 x2 · `{}` C10, C15 | - |
| `by`, door 1 (3) | door 1 | user C17 · bot C25 · timeout C9 | - |
| `reply_deadline` (3) | `emit.py:212-219` | espera C5 (precision gap: aceita 1 s a menos) · teto C6 · `null` C10 | - |
| door 1: uma decisão por `request_id`, nunca sobrescrita (1) | plan `Relations`/door 1, `emit.write_once` | C24 não exerce a disputa; mutante `os.replace` sobrevive | escrita exclusiva (`O_EXCL`/`link`) |
| door 8: quem espera (5) | plan `Landing` door 8, `emit._can_wait` | claude C7 · opencode+`GROKBOT_KIT_REPLY=1` C34 · opencode sem a variável: só teste sem check (`test_emit_wait.py:269`) | `codex` nunca espera; `question` nunca espera |
| `--standalone` por major, door 9 (2) | `run.py:361` | `2` C59 · `1` C59 | - |
| asset por major, door 5 (3) | `opencode_plugin.asset_major` | 2 C27 · desconhecido C27 · 1 C28 | - |
| resposta do plugin v2 (6) | `grokbot-kit.v2.ts` `emit`/`decision` | C31 x6 | - |
| eventos ignorados pelo plugin v2 (4) | `grokbot-kit.v2.ts:71-75` | sem task C33 · allow C32 · deny C32 · filha C32 | - |
| lugares que escrevem o plugin (4) | `install`, `cli_upgrade`, `run`, `update apply` | C27/C28 · C47 · C36 · C57 | - |
| `doctor` e a versão (3) | `doctor._reply`/`problems` | C35 x2 · C48 | - |
| classificação com respostas (5) | `terminal.unanswered`/`classify` | C39, C41 · C40 x4 | - |
| campos novos do evento, door 2 (2) | door 2 + `assets/event.v1.json` | `request_id` C5, `tests/test_payload.py:237` · `reply_deadline` C5 (evento), mas o schema com string não é validado | `reply_deadline` string aceito pelo schema |
| regra de risco: baixo (4) / pergunta (7) | AC 36/37 | C51 · C52 | - |
| docs (4) | AGENTS.md, regra de par | C54 (docs), C55, C50-C53, C56 | - |
| startup config do hook do Claude (2) | `launch.claude_settings` no `run`; harness de plugin | `run` C1 (lido em `run.py`: `launch.claude_settings(kit_exe, r["ask_wait"])`) · plugin C42 | - |

## Test policy rows

| Row | Files it classifies | Required proof | Expectation met |
| --- | --- | --- | --- |
| `emit.py` decide, alcançado pela CLI | `src/grokbot_kit/emit.py` | fronteira (subprocess `emit`) C5-C15, C34, C42 | no - door 8 sem prova para `codex` e `question`; escrita exclusiva não exercida |
| `reply` ponto de entrada que decide, na fronteira | `src/grokbot_kit/reply.py` | CLI C17-C26 | no - a disputa da AC 16 (C24) não chega ao `write_once` |
| `terminal.py` decide | `src/grokbot_kit/terminal.py`, `run.py` | camada C39, C40; fronteira C41 | yes |
| plugin v2 decide | `assets/opencode/grokbot-kit.v2.ts` | `node` com `ctx` falso C29-C33; real C38 | yes |
| asset e marcador | `opencode_plugin.py`, `run.py`, `doctor.py` | C27, C28, C35-C37 | yes |
| `setup.py` upgrade, na fronteira | `src/grokbot_kit/setup.py` | CLI C43-C47; real C49 | yes |

## Faults injected

Isolamento: cópia de `HEAD` por `git archive` no scratchpad, com `.venv` próprio; a worktree real não foi tocada
(`git status --porcelain` vazio antes e depois).

| Mutation | Location | Killed |
| --- | --- | --- |
| F1 `os.link(tmp, path)` -> `os.replace(tmp, path)` (grava por cima, sem exclusão) | `src/grokbot_kit/emit.py:116` | no - C24, C14, C21 e os 166 testes de `test_reply`/`test_emit_wait`/`test_terminal`/`test_run_guards` passam |
| F2 espera `wait` -> `wait - 1` | `src/grokbot_kit/emit.py:215` | yes - por C9 (`tests/test_emit_wait.py:158`, 3/3); C5 sozinha não mata (3/3 verde) |
| F3 door 9 `major >= 2` -> `major >= 3` | `src/grokbot_kit/run.py:361` | yes - C59 |
| F4 `deny` contado como resposta (`if reply is None:`) | `src/grokbot_kit/terminal.py:125` | yes - C40 (2 falhas) |
| F5 filtro de sessão filha removido (`if (false && parentID) return`) | `src/grokbot_kit/assets/opencode/grokbot-kit.v2.ts:75` | yes - C32 |

## Swept existing

- data lifecycle: `replies/` sai com o `gc` - confirmado, `src/grokbot_kit/gc.py:35` faz `shutil.rmtree(task_dir)`.
- authorization (n/a aprovado): `REQUEST_ID_RE` em `src/grokbot_kit/reply.py:18` e `TASK_ID_RE` impedem caminho fora
  de `replies/`; o `emit` só usa um id sem hash quando ele cabe em `_SAFE_ID` (`emit.py:21`).

## Observations (não mudam o veredito)

- Major desconhecido (`--version` falha): `run` chama `opencode_plugin.sync(None)` (`src/grokbot_kit/run.py:413`), que
  pede o asset v2 (`src/grokbot_kit/opencode_plugin.py:29`) e reescreve um plugin v1 já instalado, mas não passa
  `--standalone` (`run.py:361` exige `major is not None`). Num opencode 1.x com `--version` falhando por acaso, o
  plugin vira v2 (formato que o loader do 1.x nunca provou carregar, door 5); num 2.x, o plugin fica inerte no serviço
  compartilhado. Coerente com a letra das doors 5 e 9, mas as duas escolhas divergem no caso desconhecido.
- C57 prova o `update apply` em duas metades: o apply chama `install opencode` (`tests/test_update.py:691`) e o teste
  roda esse argv à mão (`:703`); não é o apply que termina com o plugin v2.
- C49 instala a última versão e depois faz o upgrade, então cobre o ramo `is already the latest`, não a troca de
  versão; a frase "`opencode upgrade --help` não é usado" da check não tem asserção.
- Coverage do `checks.md`: a linha da door 9 não tem a célula `Unproven`; a recusa "pedido sem espera" do `reply`
  (`exit 1`) não aparece no conjunto de recusas com `1`, embora tenha teste (`tests/test_reply.py:204`).

## Gate

`uv run pytest` (suíte do CI) - 1089 passed, 0 failed, 53 deselected. Provas nomeadas: 92 passed, 0 failed.
`-m integration` (C16, C38, C49): 3 passed, 0 failed.
