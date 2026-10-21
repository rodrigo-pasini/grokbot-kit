# kit-update verification

**Verdict**: PASS
**Profile**: standard
**Diff range**: 3b1b42f..ec22a31
**Round**: 2 - scoped
**Verifier**: independent sub-agent (author != verifier)

Rodada 2, escopo `4cced4e..ec22a31` (correção `ec22a31`, só `tests/test_update.py`, +14 linhas; nenhum arquivo de
`src/` mudou). As duas lacunas da rodada 1 estão fechadas. O mutante F3 foi reinjetado e agora morre
(`tests/test_update.py:474`). O caminho `cannot run <instalador>` (`src/grokbot_kit/update.py:280-281`) ganhou prova
(`tests/test_update.py:587-588`), e as duas faults injetadas nele morreram. Todas as provas rodaram de novo e por
inteiro em `ec22a31`. O resto vem da rodada 1 e cada seção diz de onde veio.

## Binding sources

carried from 4cced4e - a correção não tocou interface, plano nem `SKILL.md`.

Não há fonte de design de UI (profile `standard`, sem passo 1). As ADs que o plano marca foram abertas em
`docs/.specs/STATE.md` e comparadas com os checks.

| Source | Opened | Contradiction | Uncovered |
| --- | --- | --- | --- |
| AD-009 (zero dependências, `uv tool install --managed-python`) | yes - `docs/.specs/STATE.md:15`; `update.py:8-20` importa só stdlib (`urllib.request`, `json`, `subprocess`) | none | - |
| AD-016/AD-028/AD-033 (plugin global `~/.config/opencode/plugins/grokbot-kit.ts`) | yes - `docs/.specs/STATE.md:22,34,39`; C21 e C31 usam esse caminho | none | - |
| AD-032 (`SKILL.md` na URL `/releases/latest/download/SKILL.md`) | yes - `docs/.specs/STATE.md:38`; C34 cita a mesma URL | none | - |
| AD-035 (a própria feature) | yes - `docs/.specs/STATE.md:41`; comandos, cache 24 h/1 h, recibos e três opções batem com C1-C38 | none | - |

## Checks

verified at ec22a31 - provas rodadas de novo e por inteiro em `ec22a31`. Citações de `tests/test_update.py` atualizadas
(o único arquivo que a correção tocou; as linhas a partir de 467 andaram +2 e a partir de 579, +14). As citações dos
outros arquivos não mudaram de linha e vêm de `4cced4e`.

Prova em lote (uma invocação): `uv run pytest tests/test_update.py tests/test_skill_doc.py tests/test_doctor.py -v -k "<as 38 alternativas dos checks>"` - 68 passed, 46 deselected, cada teste listado individualmente como PASSED (inclui o novo `test_apply_installer_failed_not_found`). Integração (uma invocação, `uv` real): `uv run pytest -m integration tests/integration/test_install.py -k "update_installer_uv or update_apply_uv" -v` - 2 passed (`test_update_installer_uv`, `test_update_apply_uv`). Todos os testes nomeados são novos no diff `3b1b42f..ec22a31` (exceto `test_every_cited_command_exists` e `test_install_location_and_allowed_commands`, pré-existentes e reexercitados pelo `SKILL.md` alterado).

| Check | Claim | Proof run | Evidence | Result |
| --- | --- | --- | --- | --- |
| C1 | estado ausente/vencido -> 1 GET, grava `latest`, `error` null | `-k check_fetches_when_stale` 3 casos PASSED | `tests/test_update.py:90` - `assert gets(receiver) == 1`; `:92-93` - `saved["latest"] == "9.0.0"`, `saved["error"] is None` | PASS |
| C2 | estado fresco -> 0 requisições | `-k check_uses_fresh_state` 2 casos PASSED | `tests/test_update.py:107` - `assert gets(receiver) == 0`; `:108` - `out["latest"] == state["latest"]` | PASS |
| C3 | comparação numérica por componente | `-k compare_versions` 6 casos, `-k check_update_available_boundary` 3 casos PASSED | `tests/test_update.py:125` - `update.newer(a, b) is expected`; `:145-146` - `out["update_available"] is available`, `out["ask"] is available` | PASS |
| C4 | 5 falhas -> exit 0, `latest` null, `error`, estado gravado | `-k check_failure_exit_zero` 5 casos PASSED | `tests/test_update.py:68` - `result.returncode == 0`; `:161-164` - `out["latest"] is None`, `update_available is False`, `ask is False`, `out["error"]`; `:167` - `saved["error"] == out["error"]` | PASS |
| C5 | resposta lenta vira `error`; timeout do `urlopen` é 5 | `-k fetch_timeout` 2 testes PASSED | `tests/test_update.py:181` - `seen["timeout"] == 5`; `:188-189` - `out["error"]`, `update_available is False` | PASS |
| C6 | `{not json` tratado como ausente e regravado | `-k invalid_state_rewritten` PASSED | `tests/test_update.py:199-200` - `gets(receiver) == 1`, `read_state(...)["latest"] == "9.0.0"` | PASS |
| C7 | stdout é um objeto com exatamente as 9 chaves | `-k check_json_shape` PASSED | `tests/test_update.py:209` - `assert set(out) == KEYS` (KEYS em `:24`) | PASS |
| C8 | três linhas de texto do AC 8 | `-k check_text_lines` PASSED | `tests/test_update.py:217,222,229` - igualdade exata de `result.stdout` com as três linhas | PASS |
| C9 | recibo -> `uv` / `pipx` / null | `-k installer_detection` 3 casos PASSED | `tests/test_update.py:239` - `update.installer(tmp_path) == expected` | PASS |
| C10 | `uv tool install` real -> `installer` `uv` | `-m integration -k update_installer_uv` PASSED | `tests/integration/test_install.py:107` - `json.loads(result.stdout)["installer"] == "uv"` | PASS |
| C11 | GET com `User-Agent: grokbot-kit/<v>` | `-k user_agent_header` PASSED | `tests/test_update.py:246-247` - `request.method == "GET"`, `headers["user-agent"] == f"grokbot-kit/{__version__}"` | PASS |
| C12 | `update.json` com 5 chaves, sem temporário | `-k state_file_shape` PASSED | `tests/test_update.py:253-254` - `set(read_state(...)) == STATE_KEYS`, `sorted(...) == ["update.json"]` | PASS |
| C13 | `skip 9.0.0` exit 0, linha, grava `skipped` | `-k skip_records_version` PASSED | `tests/test_update.py:261-263` - `returncode == 0`, `stdout == "skipping grokbot-kit 9.0.0\n"`, `["skipped"] == "9.0.0"` | PASS |
| C14 | versão inválida -> exit 2, estado byte a byte igual | `-k skip_rejects_bad_version` 4 casos PASSED | `tests/test_update.py:272-273` - `returncode == 2`, `read_bytes() == before` | PASS |
| C15 | `skipped` = `latest` -> `ask` false; versão maior -> `ask` true | `-k skip_until_newer` PASSED | `tests/test_update.py:280-281` - `update_available is True`, `ask is False`; `:287-288` - `latest == "9.0.1"`, `ask is True` | PASS |
| C16 | `later` exit 0, linha, `later_until` +24 h (±60 s) | `-k later_records_24h` PASSED | `tests/test_update.py:297` - `stdout == f"asking again after {later_until}\n"`; `:299` - `abs(...) <= 60` | PASS |
| C17 | `later_until` futuro -> `ask` false; passado -> true | `-k later_until_gates_ask` PASSED | `tests/test_update.py:307` - `out["ask"] is False`; `:310` - `check(pkit)["ask"] is True` | PASS |
| C18 | tabela do `ask` (1 true + 4 false) | `-k ask_table` 6 casos PASSED | `tests/test_update.py:331` - `update.ask(available, "9.0.0", skipped, later_until, NOW) is expected` (linhas `:322-327`) | PASS |
| C19 | `uv` falso `tool upgrade grokbot-kit`; `pipx` falso `upgrade grokbot-kit` | `-k apply_runs_installer` 2 casos PASSED | `tests/test_update.py:420-421` - `gets(receiver) == 1`, `venv.upgrader_calls() == [call]` (calls em `:411-412`) | PASS |
| C20 | timeout do instalador é 300 | `-k installer_timeout_value` PASSED | `tests/test_update.py:451` - `call["timeout"] == 300` | PASS |
| C21 | com plugin, o executável novo recebe `install opencode`; sem, não | `-k apply_rewrites_plugin_with_new_exe` 2 casos PASSED | `tests/test_update.py:462` - `new_kit_calls() == ([{"tool": "new-kit", "argv": ["install", "opencode"]}] if plugin else [])` | PASS |
| C22 | imprime `<instalada> -> 9.0.0`, exit 0, limpa `skipped`/`later_until` | `-k apply_success_output_and_state` PASSED | `tests/test_update.py:469` - `receiver.respond(pypi("8.0.0"))` (precondição: PyPI diz 8.0.0, executável novo responde 9.0.0); `:474` - `stdout == f"grokbot-kit {__version__} -> 9.0.0\n"`; `:476-477` - `skipped is None`, `later_until is None`. Com `latest` e `--version` agora diferentes, a `<nova>` só sai 9.0.0 se vier do `--version` (AC 19); F3 morto | PASS |
| C23 | já na última -> linha, exit 0, sem instalador | `-k apply_already_latest` PASSED | `tests/test_update.py:486-487` - `stdout == f"grokbot-kit {__version__} is the latest\n"`, `upgrader_calls() == []` | PASS |
| C24 | checagem falha -> exit 1, `update check failed:`, sem instalador | `-k apply_check_failed` PASSED | `tests/test_update.py:494-496` - `returncode == 1`, `stderr.startswith("update check failed:")`, `upgrader_calls() == []` | PASS |
| C25 | sem recibo -> exit 2 com a mensagem exata | `-k apply_unknown_installer` PASSED | `tests/test_update.py:503-504` - `returncode == 2`, `UNKNOWN in result.stderr` (texto em `:26`) | PASS |
| C26 | predicado de tarefa rodando (rodando/terminada/vencida/ausente/ilegível) | `-k running_task_predicate` PASSED | `tests/test_update.py:531` - `update.task_running(...) is expected` (casos `:517-528`); `:533,536` - `is False` para sem meta e meta ilegível | PASS |
| C27 | tarefa rodando -> exit 2, `task_id` em stderr, sem instalador | `-k apply_refuses_running_task` PASSED | `tests/test_update.py:551-553` - `returncode == 2`, `task_id in result.stderr`, `upgrader_calls() == []` | PASS |
| C28 | instalador sai 3 -> exit 1, código e últimas 20 linhas, sem `install opencode`; timeout -> 1 | `-k apply_installer_failed` 3 testes PASSED | `tests/test_update.py:561-565` - `returncode == 1`, `"3" in stderr.splitlines()[0]`, `(f"installer line {i:02d}" in stderr) is (i > 10)`, `new_kit_calls() == []`; `:574` - `update.apply() == 1`; `:587-588` - `update.apply() == 1`, `err.startswith("cannot run uv:")` (instalador fora do `PATH`, caminho que o texto do C28 não nomeia; ver nota em Coverage) | PASS |
| C29 | plugin falha -> exit 1 com a mensagem exata | `-k apply_plugin_failed` PASSED | `tests/test_update.py:596-598` - `returncode == 1`, `message in result.stderr` | PASS |
| C30 | lock com pid vivo -> 2; pid morto -> tomado; lock removido | `-k apply_lock` PASSED | `tests/test_update.py:615-617` - `returncode == 2`, `upgrader_calls() == []`, `lock.exists()`; `:621-623` - `returncode == 0`, `len(upgrader_calls()) == 1`, `not lock.exists()` | PASS |
| C31 | `uv tool upgrade` real, exit 0, plugin chama `~/.local/bin/grokbot-kit` | `-m integration -k update_apply_uv` PASSED | `tests/integration/test_install.py:120-122` - `returncode == 0`, `" -> " in result.stdout`; `:124` - `f"const GROKBOT_KIT = {json.dumps(str(exe))}" in plugin`. Reprodução manual com o `uv` real imprimiu `grokbot-kit 0.2.2 -> 0.2.2` (exit 0) | PASS |
| C32 | `update check --json` em seção antes do Setup, antes de Setup e Tarefa | `-k update_check_before_setup_and_task` PASSED | `tests/test_skill_doc.py:341` - `b.index(s) < b.index("## Setup (primeira vez)") < b.index("## Tarefa")`; `:344-345` - `"antes do setup"`, `"antes de delegar uma tarefa"` | PASS |
| C33 | uma pergunta, três opções, cada uma com o comando | `-k update_three_options` PASSED | `tests/test_skill_doc.py:355-356` - `"uma única pergunta"`, `"escolha múltipla"`; `:366` - `command in item` para os três pares de `:360-363` | PASS |
| C34 | baixar a URL `latest`, redirects, sobrescrever, reler | `-k update_refreshes_skill` PASSED | `tests/test_skill_doc.py:371-379` - `paragraph_with(LATEST_URL)`, `"redirects" in p`, `"sobrescreva o \`SKILL.md\`" in p`, `p.index("baixe") < p.index("sobrescreva") < p.index("releia")` | PASS |
| C35 | `apply` 1/2 -> stderr e seguir; `ask` false/`error` -> silêncio | `-k update_failure_and_silence` PASSED | `tests/test_skill_doc.py:387-388` - `"stderr" in failure`, `"siga com o que ele pediu" in failure`; `:391-392` - `"\`ask\` \`false\`"`, `"\`error\`"` em `silence` | PASS |
| C36 | todo comando citado existe no `--help`; sem `curl` | `-k every_cited_command_exists` 2 testes, `-k install_location_and_allowed_commands` PASSED | `tests/test_skill_doc.py:286` - `result.returncode == 0, (command, ...)`; `:399` - `command in commands` para os 4 `update`; `:400-401` - sem `curl`; `:305` - `command.split()[0] in ALLOWED` | PASS |
| C37 | `doctor --json` com `kit.update` de 9 chaves, `update_available` true, cache, `ok`/`problems`/exit inalterados | `-k doctor_update_field` PASSED | `tests/test_doctor.py:272-279` - `code == 0`, `ok is True`, `problems == []`, `set(update) == UPDATE_KEYS`, `update_available is True`, `gets(receiver) == 1`; `:284` - `gets(receiver) == 1` na segunda chamada | PASS |
| C38 | linha `update:` com 9.0.0; ausente na versão instalada | `-k doctor_update_text_line` PASSED | `tests/test_doctor.py:294` - `UPDATE_LINE in result.stdout.splitlines()`; `:300` - `not [line ... startswith("update:")]` | PASS |

## Coverage

verified at ec22a31 para a linha `caminhos de saída do \`update apply\``, recalculada em `src/grokbot_kit/update.py:249-294`
(arquivo sem mudança em `4cced4e..ec22a31`, então os membros são os mesmos 10). As outras linhas: carried from 4cced4e
(nenhum arquivo de autoridade delas mudou).

Recalculado a partir do código (`src/grokbot_kit/update.py`, `doctor.py`, `cli.py`) e do plano (Surface, Landing, AC), não da tabela do autor.

| Set (size) | Recomputed from | Member -> proof | Unproven |
| --- | --- | --- | --- |
| resultados do GET da door 3 (7) | plano Surface + `update.py:99-117` | `200` X.Y.Z C1 · `200` sem `info.version` C4[no-version] · `200` fora de X.Y.Z C4[not-x-y-z] · não JSON C4[not-json] · `500` (HTTPError) C4[500] · conexão recusada C4[refused] · timeout C5 | - |
| frescor do estado (5) | `update.py:137-139` + AC 1/2 | ausente C1[absent] · ok >24 h C1 · erro >1 h C1 · ok <24 h C2 · erro <1 h C2 | - |
| `update check` exit (1) | `update.py:179-189` | `0` C4, C7, C8 | - |
| `update check` texto (3) | `update.py:183-188` | erro C8 · disponível C8 · última C8 | - |
| caminhos de saída do `update apply` (10) | `update.py:249-294` | lock ocupado (2) C30 · checagem falhou (1) C24 · já na última (0) C23 · instalador desconhecido (2) C25 · tarefa rodando (2) C27 · timeout do instalador (1) C28 `:574` · instalador fora do `PATH`/não executável, `cannot run <tool>` (1) C28 `test_apply_installer_failed_not_found` `:587-588` · instalador sai ≠0 (1) C28 · plugin falhou (1) C29 · sucesso (0) C22 | - |
| `update skip` exit (2) | `update.py:192-200` | `0` C13 · `2` C14 | - |
| `update later` exit (1) | `update.py:203-209` | `0` C16 | - |
| `doctor` com `kit.update` (exit, json, texto) (3) | `doctor.py:159,171-173` | json + exit 0 C37 · linha presente C38 · linha ausente C38 | - |
| instalador da door 5 (3) | `update.py:33,69-74` | `uv` C9, C10, C19, C31 · `pipx` C9, C19 · null C9, C25 | - |
| tabela do `ask` (5) | door 4 + `update.py:61-66` | as 5 linhas C18 (`:322-327`), mais C15/C17 na fronteira | - |
| predicado de tarefa rodando (5) | AC 23 + `update.py:77-86` | rodando C26, C27 · terminada C26 · janela vencida C26 · `meta.json` ausente C26 · ilegível C26 | - |
| lock do `apply` (3) | AC 26 + `update.py:222-241,255` | pid vivo C30 · pid morto C30 · removido no fim C30 | - |
| opções da skill (3) | AC 28/29 | atualizar C33 · agora não C33 · pular C33 | - |
| doors do plano (5) | plano Landing | 1 C7, C13, C16, C22, C36 · 2 C12 · 3 C1, C5, C11 · 4 C7, C18, C37 · 5 C9, C10 | - |

Notas (não contadas como membros do conjunto do plano): o texto do C28 em `checks.md:110` não foi estendido para nomear
o caminho `cannot run <instalador>`; a prova nova está atribuída ao C28 só pelo comentário em `tests/test_update.py:579`.
O membro está provado e com fault morta; fica o registro de que o artifact de checks não nomeia o caminho. O
`checks.md:156` ainda resume o `apply` em 3 exits e o `checks.md:185` fala em 7 caminhos, enquanto o código tem 10;
todos os 10 têm prova. Continuam fora do plano e sem prova (código sem mudança): o ramo `response.status != 200` para 2xx diferente de 200
(`update.py:101-102`) não tem prova; o plano o agrupa em "qualquer outro status", provado por `500`. O lock com
conteúdo ilegível (`update.py:232-233`, pid `0`, tomado) também não tem prova, e o plano não o nomeia.

## Test policy rows

verified at ec22a31 para a linha "Ponto de entrada", rejulgada. Nenhuma linha classifica `tests/test_update.py` (o único
arquivo tocado), então as outras são carried from 4cced4e.

Linhas de `docs/.specs/features/agent-run-notify/checks.md` (`## Test policy`), aplicadas sem mudança.

| Row | Files it classifies | Required proof | Expectation met |
| --- | --- | --- | --- |
| Decide, alcançado através de uma fronteira | `update.py`: `newer` (C3 + `check_update_available_boundary`), `ask` (C18 + C15/C17), `installer` (C9 + C19/C25), frescor (C1/C2, um caso por linha na fronteira) | fronteira e própria camada, um caso por linha | yes |
| Decide, sem fronteira | `update.py`: `task_running` (C26, 6 casos na própria camada; C27 na fronteira) | própria camada, um caso por linha | yes |
| Ponto de entrada que não decide | `update.py`: `check`, `skip`, `later`, `apply` pela CLI (`cli.py`) | fronteira: entrada aceita, cada recusada, cada caminho de erro | yes - os 10 caminhos do `apply` têm prova; `cannot run <instalador>` (`update.py:280-281`) em `tests/test_update.py:587-588`, chamando `update.apply()`, que é o que a CLI devolve sem transformar (`src/grokbot_kit/cli.py:163`), ao mesmo nível do caso de timeout aceito na rodada 1 |
| Instrumentação, repasse | `doctor.py` (`kit.update` e a linha `update:`) | nenhuma própria; coberto por quem consome | yes - C37, C38 |
| Integração com CLI real ou GitHub | `uv tool install`/`uv tool upgrade` reais | `-m integration` no box | yes - C10, C31 rodaram aqui com o `uv` real; `pipx` real não existe nesta máquina (declarado em checks.md) |

Swept: não há linhas `existing` no `## Swept` do checks.md. As duas linhas `existing` do `Observable` do plano
conferem: a seção `## Atualização` (`skills/grokbot-kit/SKILL.md:31`) é imperativa e curta como o resto da skill, e o
`CHANGELOG.md:22-23` traz o aviso de baixar a skill nova uma vez.

## Faults injected

verified at ec22a31 para F3 (reinjetada), F6 e F7 (superfície nova `cannot run`); F1, F2, F4 e F5 carried from 4cced4e
(nenhuma das superfícies delas foi tocada pela correção).

Rodada 2: worktree scratch em `ec22a31`
(`/tmp/claude-1000/-home-rodrigo-projetos-pessoal-worktrees-grokbot-kit-kit-update/cfb9c49a-125d-4c99-a510-ee5f78f06b0d/scratchpad/verify-wt2`).
`git status --porcelain` do tree real antes: `?? docs/.specs/features/kit-update/verification.md`; depois, idêntico
(conferido com `diff`). Scratch removida com `git worktree remove --force`, sem `git stash`. Cada fault revertida com
`git checkout -- src` antes da seguinte.

| Mutation | Location | Killed |
| --- | --- | --- |
| F1: `ask` ignora `skipped` (removido `latest != skipped and`) | `src/grokbot_kit/update.py:66` | yes - `test_ask_table[True-9.0.0-None-False]` falhou |
| F2: frescor usa sempre 24 h (erro deixa de valer 1 h) | `src/grokbot_kit/update.py:139` | yes - `test_check_fetches_when_stale[error-older-than-1h]` falhou |
| F3: `<nova>` vem do `latest` do PyPI em vez de `<exe> --version` (`new = out["latest"]`) | `src/grokbot_kit/update.py:286` | yes - reinjetada na rodada 2: `test_apply_success_output_and_state` falhou em `tests/test_update.py:474` (`'grokbot-kit 0.2.2 -> 8.0.0\n' == '... -> 9.0.0\n'`) |
| F4: linha `update:` do doctor condicionada a `latest` em vez de `update_available` | `src/grokbot_kit/doctor.py:172` | yes - `test_doctor_update_text_line` falhou |
| F5: opção "Agora não" mapeada para `grokbot-kit update apply` | `skills/grokbot-kit/SKILL.md:42` | yes - `test_update_three_options` falhou |
| F6: `cannot run` sai com `2` em vez de `1` | `src/grokbot_kit/update.py:281` | yes - `test_apply_installer_failed_not_found` falhou em `tests/test_update.py:587` (`assert 2 == 1`) |
| F7: mensagem `cannot run <tool>:` trocada por `could not start <tool>:` | `src/grokbot_kit/update.py:281` | yes - `test_apply_installer_failed_not_found` falhou em `tests/test_update.py:588` (`startswith("cannot run uv:")` falso) |

## Gate

verified at ec22a31. `uv run pytest` - 610 passed, 0 failed (18 deselected: `-m integration`); `uv run pytest -m integration tests/integration/test_install.py -k "update_installer_uv or update_apply_uv" -v` - 2 passed, 0 failed

Ranked gaps: nenhum que conte no veredito. Notas, fora do plano:

1. (nota) O texto do C28 (`docs/.specs/features/kit-update/checks.md:110`) não nomeia o caminho `cannot run <instalador>`, e as linhas `checks.md:156` e `:185` contam 3 exits e 7 caminhos do `apply` contra 10 no código (`src/grokbot_kit/update.py:249-294`). Todos os 10 estão provados - C28 - `tests/test_update.py:579-588`.
2. (nota, carried from 4cced4e) ramo 2xx ≠ 200 e lock ilegível sem prova, e o plano não os nomeia - `src/grokbot_kit/update.py:101-102`, `:232-233`.
