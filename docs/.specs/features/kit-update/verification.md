# kit-update verification

**Verdict**: PASS
**Profile**: standard
**Diff range**: 3b1b42f..c9e4e65
**Round**: 3 - scoped
**Verifier**: independent sub-agent (author != verifier)

Rodada 3, escopo `ec22a31..c9e4e65`. Nenhum arquivo de `src/`, `skills/`, `tests/conftest.py`, `tests/fakes/`,
`tests/integration/` ou `tests/test_skill_doc.py` mudou nesse intervalo (`git diff --stat ec22a31..HEAD` vazio para
esses caminhos). Mudaram quatro coisas:

- `tests/test_update.py`, +21 linhas (83df498): `test_check_failure_exit_zero_non_200` (C4) e `test_apply_lock_unreadable` (C30);
- `tests/test_doctor.py` (+26) e `tests/test_workflows.py` (+3), pelo merge da `main` (PR 18);
- `checks.md` (22bfb11): o texto do C28, a linha nova do Coverage e o "10 caminhos" da Test policy;
- a versão `0.3.0` em `pyproject.toml`, `uv.lock` e `CHANGELOG.md` (8c6939d).

Todas as provas rodaram de novo e por inteiro em `c9e4e65`. As duas superfícies novas levaram uma fault cada, e as
duas morreram. As notas 1 e 2 da rodada 2 estão fechadas. Cada seção diz de onde veio.

## Binding sources

carried from ec22a31, com a citação da AD da feature atualizada em c9e4e65. O merge renumerou a decisão da feature de
AD-035 para AD-036 (`docs/.specs/STATE.md:42`). A AD-035 agora é da agent-run-notify. A interface, o plano e o
`SKILL.md` não mudaram.

Não há fonte de design de UI (profile `standard`, sem passo 1). As ADs que o plano marca foram abertas em
`docs/.specs/STATE.md` e comparadas com os checks.

| Source | Opened | Contradiction | Uncovered |
| --- | --- | --- | --- |
| AD-009 (zero dependências, `uv tool install --managed-python`) | yes - `docs/.specs/STATE.md:15`; `src/grokbot_kit/update.py:8-20` importa só stdlib | none | - |
| AD-016/AD-028/AD-033 (plugin global `~/.config/opencode/plugins/grokbot-kit.ts`) | yes - `docs/.specs/STATE.md:22,34,39`; C21 e C31 usam esse caminho | none | - |
| AD-032 (`SKILL.md` na URL `/releases/latest/download/SKILL.md`) | yes - `docs/.specs/STATE.md:38`; C34 cita a mesma URL | none | - |
| AD-036 (a própria feature, antes AD-035) | yes - `docs/.specs/STATE.md:42`; comandos, cache 24 h/1 h, recibos e três opções batem com C1-C38 | none | - |

## Checks

verified at c9e4e65. As provas rodaram de novo, por inteiro e em lote, em `c9e4e65`. As citações dos arquivos tocados
foram atualizadas. Em `tests/test_update.py`, as linhas a partir de 170 andaram +9, e há linhas novas em `:170-176` e
`:635-644`. Em `tests/test_doctor.py`, C37 e C38 andaram +26. As citações de `tests/test_skill_doc.py` e
`tests/integration/test_install.py` não mudaram, porque esses arquivos não foram tocados.

As provas rodaram em três invocações:

- Prova em lote, uma invocação: `uv run pytest tests/test_update.py tests/test_skill_doc.py tests/test_doctor.py -v -k "<as 38 alternativas dos checks, OR>"` deu 70 passed e 50 deselected. Cada teste aparece listado individualmente como PASSED, inclusive os novos `test_check_failure_exit_zero_non_200` e `test_apply_lock_unreadable`. O `-k check_failure_exit_zero` do C4 e o `-k apply_lock` do C30 os pegam por substring.
- Integração, uma invocação com o `uv` real: `uv run pytest -m integration tests/integration/test_install.py -k "update_installer_uv or update_apply_uv" -v` deu 2 passed (`test_update_installer_uv`, `test_update_apply_uv`).
- Em `tests/test_doctor.py` inteiro, depois do merge: 27 passed. C37 e C38 convivem com o `test_plugin_without_exe_line` da `main` (C151 da agent-run-notify, `tests/test_doctor.py:235-258`).

| Check | Claim | Proof run | Evidence | Result |
| --- | --- | --- | --- | --- |
| C1 | estado ausente/vencido -> 1 GET, grava `latest`, `error` null | `-k check_fetches_when_stale` 3 casos PASSED | `tests/test_update.py:90` - `assert gets(receiver) == 1`; `:92-93` - `saved["latest"] == "9.0.0"`, `saved["error"] is None` | PASS |
| C2 | estado fresco -> 0 requisições | `-k check_uses_fresh_state` 2 casos PASSED | `tests/test_update.py:107` - `assert gets(receiver) == 0`; `:108` - `out["latest"] == state["latest"]` | PASS |
| C3 | comparação numérica por componente | `-k compare_versions` 6 casos, `-k check_update_available_boundary` 3 casos PASSED | `tests/test_update.py:125` - `update.newer(a, b) is expected`; `:145-146` - `out["update_available"] is available`, `out["ask"] is available` (com a instalada agora `0.3.0`, o caso `0.3.0-False` é o de igualdade) | PASS |
| C4 | falhas do GET -> exit 0, `latest` null, `error`, estado gravado | `-k check_failure_exit_zero` 5 casos + `test_check_failure_exit_zero_non_200` PASSED | `tests/test_update.py:68` - `result.returncode == 0`; `:161-164` - `out["latest"] is None`, `update_available is False`, `ask is False`, `out["error"]`; `:167` - `saved["error"] == out["error"]`; novo `:172` - `receiver.respond((203, pypi("9.0.0")[1]))` (precondição: 2xx com versão válida no corpo); `:174-176` - `out["latest"] is None`, `update_available is False`, `"203" in out["error"]` | PASS |
| C5 | resposta lenta vira `error`; timeout do `urlopen` é 5 | `-k fetch_timeout` 2 testes PASSED | `tests/test_update.py:190` - `seen["timeout"] == 5`; `:197-198` - `out["error"]`, `update_available is False` | PASS |
| C6 | `{not json` tratado como ausente e regravado | `-k invalid_state_rewritten` PASSED | `tests/test_update.py:208-209` - `gets(receiver) == 1`, `read_state(...)["latest"] == "9.0.0"` | PASS |
| C7 | stdout é um objeto com exatamente as 9 chaves | `-k check_json_shape` PASSED | `tests/test_update.py:218` - `assert set(out) == KEYS` (KEYS em `:24`) | PASS |
| C8 | três linhas de texto do AC 8 | `-k check_text_lines` PASSED | `tests/test_update.py:226,231,238` - igualdade exata de `result.stdout` com as três linhas | PASS |
| C9 | recibo -> `uv` / `pipx` / null | `-k installer_detection` 3 casos PASSED | `tests/test_update.py:248` - `update.installer(tmp_path) == expected` | PASS |
| C10 | `uv tool install` real -> `installer` `uv` | `-m integration -k update_installer_uv` PASSED | `tests/integration/test_install.py:107` - `json.loads(result.stdout)["installer"] == "uv"` | PASS |
| C11 | GET com `User-Agent: grokbot-kit/<v>` | `-k user_agent_header` PASSED | `tests/test_update.py:255-256` - `request.method == "GET"`, `headers["user-agent"] == f"grokbot-kit/{__version__}"` | PASS |
| C12 | `update.json` com 5 chaves, sem temporário | `-k state_file_shape` PASSED | `tests/test_update.py:262-263` - `set(read_state(...)) == STATE_KEYS`, `sorted(...) == ["update.json"]` | PASS |
| C13 | `skip 9.0.0` exit 0, linha, grava `skipped` | `-k skip_records_version` PASSED | `tests/test_update.py:270-272` - `returncode == 0`, `stdout == "skipping grokbot-kit 9.0.0\n"`, `["skipped"] == "9.0.0"` | PASS |
| C14 | versão inválida -> exit 2, estado byte a byte igual | `-k skip_rejects_bad_version` 4 casos PASSED | `tests/test_update.py:281-282` - `returncode == 2`, `read_bytes() == before` | PASS |
| C15 | `skipped` = `latest` -> `ask` false; versão maior -> `ask` true | `-k skip_until_newer` PASSED | `tests/test_update.py:289-290` - `update_available is True`, `ask is False`; `:296-297` - `latest == "9.0.1"`, `ask is True` | PASS |
| C16 | `later` exit 0, linha, `later_until` +24 h (±60 s) | `-k later_records_24h` PASSED | `tests/test_update.py:306` - `stdout == f"asking again after {later_until}\n"`; `:308` - `abs(...) <= 60` | PASS |
| C17 | `later_until` futuro -> `ask` false; passado -> true | `-k later_until_gates_ask` PASSED | `tests/test_update.py:316` - `out["ask"] is False`; `:319` - `check(pkit)["ask"] is True` | PASS |
| C18 | tabela do `ask` (1 true + 4 false) | `-k ask_table` 6 casos PASSED | `tests/test_update.py:340` - `update.ask(available, "9.0.0", skipped, later_until, NOW) is expected` (linhas `:331-336`) | PASS |
| C19 | `uv` falso `tool upgrade grokbot-kit`; `pipx` falso `upgrade grokbot-kit` | `-k apply_runs_installer` 2 casos PASSED | `tests/test_update.py:429-430` - `gets(receiver) == 1`, `venv.upgrader_calls() == [call]` (calls em `:420-421`) | PASS |
| C20 | timeout do instalador é 300 | `-k installer_timeout_value` PASSED | `tests/test_update.py:460` - `call["timeout"] == 300` | PASS |
| C21 | com plugin, o executável novo recebe `install opencode`; sem, não | `-k apply_rewrites_plugin_with_new_exe` 2 casos PASSED | `tests/test_update.py:471` - `new_kit_calls() == ([{"tool": "new-kit", "argv": ["install", "opencode"]}] if plugin else [])` | PASS |
| C22 | imprime `<instalada> -> 9.0.0`, exit 0, limpa `skipped`/`later_until` | `-k apply_success_output_and_state` PASSED | `tests/test_update.py:478` - `receiver.respond(pypi("8.0.0"))` (precondição: PyPI diz 8.0.0, executável novo responde 9.0.0); `:483` - `stdout == f"grokbot-kit {__version__} -> 9.0.0\n"`; `:485-486` - `skipped is None`, `later_until is None` | PASS |
| C23 | já na última -> linha, exit 0, sem instalador | `-k apply_already_latest` PASSED | `tests/test_update.py:495-496` - `stdout == f"grokbot-kit {__version__} is the latest\n"`, `upgrader_calls() == []` | PASS |
| C24 | checagem falha -> exit 1, `update check failed:`, sem instalador | `-k apply_check_failed` PASSED | `tests/test_update.py:503-505` - `returncode == 1`, `stderr.startswith("update check failed:")`, `upgrader_calls() == []` | PASS |
| C25 | sem recibo -> exit 2 com a mensagem exata | `-k apply_unknown_installer` PASSED | `tests/test_update.py:512-513` - `returncode == 2`, `UNKNOWN in result.stderr` (texto em `:26`) | PASS |
| C26 | predicado de tarefa rodando (rodando/terminada/vencida/ausente/ilegível) | `-k running_task_predicate` PASSED | `tests/test_update.py:540` - `update.task_running(...) is expected` (casos `:526-537`); `:542,545` - `is False` para sem meta e meta ilegível | PASS |
| C27 | tarefa rodando -> exit 2, `task_id` em stderr, sem instalador | `-k apply_refuses_running_task` PASSED | `tests/test_update.py:560-562` - `returncode == 2`, `task_id in result.stderr`, `upgrader_calls() == []` | PASS |
| C28 | instalador sai 3 -> exit 1, código e últimas 20 linhas, sem `install opencode`; timeout -> 1; fora do `PATH` -> 1 com `cannot run <instalador>` | `-k apply_installer_failed` 3 testes PASSED | `tests/test_update.py:570-574` - `returncode == 1`, `"3" in stderr.splitlines()[0]`, `(f"installer line {i:02d}" in stderr) is (i > 10)`, `new_kit_calls() == []`; `:583` - `update.apply() == 1`; `:596-597` - `update.apply() == 1`, `err.startswith("cannot run uv:")`. O texto do C28 (`checks.md:110`) agora nomeia o caso do `PATH` | PASS |
| C29 | plugin falha -> exit 1 com a mensagem exata | `-k apply_plugin_failed` PASSED | `tests/test_update.py:605-607` - `returncode == 1`, `message in result.stderr` | PASS |
| C30 | lock com pid vivo -> 2; pid morto -> tomado; lock removido | `-k apply_lock` 2 testes PASSED | `tests/test_update.py:624-626` - `returncode == 2`, `upgrader_calls() == []`, `lock.exists()`; `:630-632` - `returncode == 0`, `len(upgrader_calls()) == 1`, `not lock.exists()`; novo `:640` - `lock.write_text("not a pid")` (precondição: lock ilegível); `:642-644` - `returncode == 0`, `len(upgrader_calls()) == 1`, `not lock.exists()` | PASS |
| C31 | `uv tool upgrade` real, exit 0, plugin chama `~/.local/bin/grokbot-kit` | `-m integration -k update_apply_uv` PASSED | `tests/integration/test_install.py:120-122` - `returncode == 0`, `" -> " in result.stdout`; `:124` - `f"const GROKBOT_KIT = {json.dumps(str(exe))}" in plugin` | PASS |
| C32 | `update check --json` em seção antes do Setup, antes de Setup e Tarefa | `-k update_check_before_setup_and_task` PASSED | `tests/test_skill_doc.py:341` - `b.index(s) < b.index("## Setup (primeira vez)") < b.index("## Tarefa")`; `:344-345` - `"antes do setup"`, `"antes de delegar uma tarefa"` | PASS |
| C33 | uma pergunta, três opções, cada uma com o comando | `-k update_three_options` PASSED | `tests/test_skill_doc.py:355-356` - `"uma única pergunta"`, `"escolha múltipla"`; `:366` - `command in item` para os três pares de `:360-363` | PASS |
| C34 | baixar a URL `latest`, redirects, sobrescrever, reler | `-k update_refreshes_skill` PASSED | `tests/test_skill_doc.py:371-379` - `paragraph_with(LATEST_URL)`, `"redirects" in p`, `"sobrescreva o \`SKILL.md\`" in p`, `p.index("baixe") < p.index("sobrescreva") < p.index("releia")` | PASS |
| C35 | `apply` 1/2 -> stderr e seguir; `ask` false/`error` -> silêncio | `-k update_failure_and_silence` PASSED | `tests/test_skill_doc.py:387-388` - `"stderr" in failure`, `"siga com o que ele pediu" in failure`; `:391-392` - `"\`ask\` \`false\`"`, `"\`error\`"` em `silence` | PASS |
| C36 | todo comando citado existe no `--help`; sem `curl` | `-k every_cited_command_exists` 2 testes, `-k install_location_and_allowed_commands` PASSED | `tests/test_skill_doc.py:286` - `result.returncode == 0, (command, ...)`; `:399` - `command in commands` para os 4 `update`; `:400-401` - sem `curl`; `:305` - `command.split()[0] in ALLOWED` | PASS |
| C37 | `doctor --json` com `kit.update` de 9 chaves, `update_available` true, cache, `ok`/`problems`/exit inalterados | `-k doctor_update_field` PASSED | `tests/test_doctor.py:298-305` - `code == 0`, `ok is True`, `problems == []`, `set(update) == UPDATE_KEYS`, `update_available is True`, `gets(receiver) == 1`; `:310` - `gets(receiver) == 1` na segunda chamada | PASS |
| C38 | linha `update:` com 9.0.0; ausente na versão instalada | `-k doctor_update_text_line` PASSED | `tests/test_doctor.py:320` - `UPDATE_LINE in result.stdout.splitlines()`; `:326` - `not [line ... startswith("update:")]` | PASS |

## Coverage

As linhas "resultados do GET" (C4) e "caminhos de saída do `update apply`" foram recalculadas em c9e4e65, e a do lock
também, porque o C30 ganhou um membro. As outras são carried from ec22a31: nenhum arquivo de autoridade delas mudou
(`src/` sem diff em `ec22a31..HEAD`).

Recalculado a partir do código (`src/grokbot_kit/update.py`, `doctor.py`, `cli.py`) e do plano (Surface, Landing,
AC), não da tabela do autor.

| Set (size) | Recomputed from | Member -> proof | Unproven |
| --- | --- | --- | --- |
| resultados do GET da door 3 (8) | plano Surface ("`200` com X.Y.Z; `200` sem ele, qualquer outro status, timeout ou falha de conexão") + AC 5 ("HTTP diferente de `200`") + `update.py:99-117` | `200` X.Y.Z C1 · `200` sem `info.version` C4[no-version] · `200` fora de X.Y.Z C4[not-x-y-z] · `200` não JSON C4[not-json] · não-2xx (`HTTPError`, `update.py:104-105`) C4[500] · 2xx diferente de `200` (`update.py:101-102`) C4 `test_check_failure_exit_zero_non_200` `:172-176` · conexão recusada C4[refused] · timeout C5 | - |
| frescor do estado (5) | `update.py:137-139` + AC 1/2 | ausente C1[absent] · ok >24 h C1 · erro >1 h C1 · ok <24 h C2 · erro <1 h C2 | - |
| `update check` exit (1) | `update.py:179-189` | `0` C4, C7, C8 | - |
| `update check` texto (3) | `update.py:183-188` | erro C8 · disponível C8 · última C8 | - |
| caminhos de saída do `update apply` (10) | `update.py:249-294` | lock ocupado `:251` (2) C30 · checagem falhou `:263` (1) C24 · já na última `:266` (0) C23 · instalador desconhecido `:269` (2) C25 · tarefa rodando `:272` (2) C27 · timeout do instalador `:279` (1) C28 `:583` · instalador fora do `PATH`, `cannot run <tool>` `:281` (1) C28 `:596-597` · instalador sai ≠0 `:284` (1) C28 `:570-574` · plugin falhou `:288` (1) C29 · sucesso `:294` (0) C22. Bate com `checks.md:157` (10) | - |
| `update skip` exit (2) | `update.py:192-200` | `0` C13 · `2` C14 | - |
| `update later` exit (1) | `update.py:203-209` | `0` C16 | - |
| `doctor` com `kit.update` (exit, json, texto) (3) | `doctor.py:159,171-173` | json + exit 0 C37 · linha presente C38 · linha ausente C38 | - |
| instalador da door 5 (3) | `update.py:33,69-74` | `uv` C9, C10, C19, C31 · `pipx` C9, C19 · null C9, C25 | - |
| tabela do `ask` (5) | door 4 + `update.py:61-66` | as 5 linhas C18 (`:331-336`), mais C15/C17 na fronteira | - |
| predicado de tarefa rodando (5) | AC 23 + `update.py:77-86` | rodando C26, C27 · terminada C26 · janela vencida C26 · `meta.json` ausente C26 · ilegível C26 | - |
| lock do `apply` (4) | AC 26 + `update.py:222-241,251` | pid vivo C30 `:624-626` · pid morto C30 `:630-632` · conteúdo ilegível, tratado como pid `0` e tomado (`update.py:232-233`) C30 `:642-644` · removido no fim C30 | - |
| opções da skill (3) | AC 28/29 | atualizar C33 · agora não C33 · pular C33 | - |
| doors do plano (5) | plano Landing | 1 C7, C13, C16, C22, C36 · 2 C12 · 3 C1, C5, C11 · 4 C7, C18, C37 · 5 C9, C10 | - |

Notas, que não contam como membros sem prova:

- A nota 1 da rodada 2 está fechada. O texto do C28 (`checks.md:110`) nomeia o caminho do `PATH`, a linha nova
  `checks.md:157` conta os 10 caminhos do `apply` e a Test policy (`checks.md:186`) fala em 10. O resumo
  `checks.md:156` continua em 3 exits, o que está correto como conjunto de exit codes.
- A nota 2 da rodada 2 está fechada. O ramo 2xx ≠ 200 e o lock ilegível têm prova, cada um com uma fault que morreu
  (ver Faults).
- Restam três imprecisões de texto (precisão, não cobertura):
  - o texto do C4 (`checks.md:34`) ainda enumera 5 falhas e não nomeia o 2xx ≠ 200, e a linha `checks.md:152` do
    Coverage do autor continua com 7 membros sem ele;
  - o texto do C30 (`checks.md:116`) e a linha do lock (`checks.md:164`, 3 membros) não nomeiam o lock ilegível;
  - as duas provas novas estão atribuídas ao C4 e ao C30 pelos comentários (`tests/test_update.py:170,635`) e pelo
    `-k` por substring.
- Visto no recálculo, sem prova própria, igual às rodadas anteriores: o `except OSError` genérico do fetch
  (`update.py:110-111`, por exemplo uma conexão derrubada antes do status). O plano o agrupa em "falha de conexão",
  membro provado pelo C4[refused] (`URLError`, `update.py:106-107`).

## Test policy rows

verified at c9e4e65 para três linhas:

- "Ponto de entrada", porque a evidência do `checks.md:186` mudou para 10 caminhos;
- "Decide, sem fronteira", porque o lock ganhou prova;
- "Instrumentação", porque o merge tocou `tests/test_doctor.py`.

As outras linhas são carried from ec22a31.

Linhas de `docs/.specs/features/agent-run-notify/checks.md` (`## Test policy`), aplicadas sem mudança.

| Row | Files it classifies | Required proof | Expectation met |
| --- | --- | --- | --- |
| Decide, alcançado através de uma fronteira | `update.py`: `newer` (C3 + `check_update_available_boundary`), `ask` (C18 + C15/C17), `installer` (C9 + C19/C25), frescor (C1/C2, um caso por linha na fronteira) | fronteira e própria camada, um caso por linha | yes |
| Decide, sem fronteira | `update.py`: `task_running` (C26, 6 casos na própria camada; C27 na fronteira); `_take_lock` (C30: vivo, morto, ilegível, todos pela CLI) | própria camada, um caso por linha | yes - o lock tem os 3 casos de conteúdo provados pela fronteira, acima do exigido |
| Ponto de entrada que não decide | `update.py`: `check`, `skip`, `later`, `apply` pela CLI (`cli.py`) | fronteira: entrada aceita, cada recusada, cada caminho de erro | yes - os 10 caminhos do `apply` têm prova (`tests/test_update.py:483,495,503,512,560,570,583,596,605,624`); timeout e `cannot run` chamam `update.apply()`, que a CLI devolve sem transformar (`src/grokbot_kit/cli.py:163`) |
| Instrumentação, repasse | `doctor.py` (`kit.update` e a linha `update:`) | nenhuma própria; coberto por quem consome | yes - C37, C38 (`tests/test_doctor.py:298-310,320-326`), verdes depois do merge com o arquivo inteiro (27 passed) |
| Integração com CLI real ou GitHub | `uv tool install`/`uv tool upgrade` reais | `-m integration` executado no box | yes - C10, C31 rodaram aqui com o `uv` real em c9e4e65; `pipx` real ausente desta máquina (declarado em checks.md) |

Swept: o `## Swept` do checks.md não tem linhas `existing`. As duas linhas `existing` do `Observable` do plano
conferem em c9e4e65:

- a seção `## Atualização` (`skills/grokbot-kit/SKILL.md:31`, sem mudança) é imperativa e curta como o resto da skill;
- o aviso de baixar a skill nova uma vez agora fica na seção `## [0.3.0] - 2026-10-21`, em `CHANGELOG.md:22-25`.

## Faults injected

verified at c9e4e65 para F8 e F9, que estão nas superfícies novas. F1 a F7 são carried from ec22a31: as superfícies
delas (`src/grokbot_kit/update.py`, `doctor.py`, `SKILL.md`) não mudaram em `ec22a31..HEAD`, e as provas que as mataram
seguem verdes em c9e4e65.

Rodada 3: worktree scratch em `c9e4e65`
(`/tmp/claude-1000/-home-rodrigo-projetos-pessoal-worktrees-grokbot-kit-kit-update/cfb9c49a-125d-4c99-a510-ee5f78f06b0d/scratchpad/verify-wt3`).
O `git status --porcelain` do tree real estava vazio antes. Depois, ainda vazio e idêntico, conferido com `diff`
(rodado antes de este relatório ser escrito). A scratch foi removida com `git worktree remove --force` e
`git worktree prune`, sem `git stash`. Cada fault foi revertida com `git checkout -- src` antes da seguinte.

| Mutation | Location | Killed |
| --- | --- | --- |
| F1: `ask` ignora `skipped` (removido `latest != skipped and`) | `src/grokbot_kit/update.py:66` | yes - `test_ask_table[True-9.0.0-None-False]` falhou (carried from 4cced4e) |
| F2: frescor usa sempre 24 h (erro deixa de valer 1 h) | `src/grokbot_kit/update.py:139` | yes - `test_check_fetches_when_stale[error-older-than-1h]` falhou (carried from 4cced4e) |
| F3: `<nova>` vem do `latest` do PyPI em vez de `<exe> --version` | `src/grokbot_kit/update.py:286` | yes - `test_apply_success_output_and_state` falhou (carried from ec22a31) |
| F4: linha `update:` do doctor condicionada a `latest` em vez de `update_available` | `src/grokbot_kit/doctor.py:172` | yes - `test_doctor_update_text_line` falhou (carried from 4cced4e) |
| F5: opção "Agora não" mapeada para `grokbot-kit update apply` | `skills/grokbot-kit/SKILL.md:42` | yes - `test_update_three_options` falhou (carried from 4cced4e) |
| F6: `cannot run` sai com `2` em vez de `1` | `src/grokbot_kit/update.py:281` | yes - `test_apply_installer_failed_not_found` falhou (carried from ec22a31) |
| F7: mensagem `cannot run <tool>:` trocada por `could not start <tool>:` | `src/grokbot_kit/update.py:281` | yes - `test_apply_installer_failed_not_found` falhou (carried from ec22a31) |
| F8: `if response.status != 200:` -> `if response.status >= 300:` (um 2xx qualquer passa a ser aceito) | `src/grokbot_kit/update.py:101` | yes - `test_check_failure_exit_zero_non_200` falhou em `tests/test_update.py:174` (`assert '9.0.0' is None`) |
| F9: lock ilegível tratado como dono vivo (`pid = 0` -> `return False`) | `src/grokbot_kit/update.py:233` | yes - `test_apply_lock_unreadable` falhou em `tests/test_update.py:642` (`assert 2 == 0`, stderr `another grokbot-kit update apply is running`) |

## Gate

verified at c9e4e65. Rodaram três comandos:

- `uv run pytest`: 616 passed, 0 failed, 18 deselected (`-m integration`). Inclui `tests/test_doctor.py` e
  `tests/test_workflows.py` depois do merge, e a versão `0.3.0` (`pyproject.toml:3`, `uv.lock:120`).
- `uv run pytest -m integration tests/integration/test_install.py -k "update_installer_uv or update_apply_uv" -v`:
  2 passed, 0 failed.
- `uv run pytest tests/test_doctor.py -q`: 27 passed.

Ranked gaps: nenhum que conte no veredito. Notas de precisão no artifact de checks:

1. (nota) O texto do C4 (`docs/.specs/features/kit-update/checks.md:34`) e a linha do Coverage do autor
   (`checks.md:152`, 7 membros) não nomeiam o 2xx ≠ 200. O membro está provado e com fault morta. Ver C4,
   `tests/test_update.py:170-176`.
2. (nota) O texto do C30 (`checks.md:116`) e a linha do lock (`checks.md:164`, 3 membros) não nomeiam o lock ilegível.
   O membro está provado e com fault morta. Ver C30, `tests/test_update.py:635-644`.
3. (nota, fora do plano como membro próprio) O `except OSError` genérico do fetch (`src/grokbot_kit/update.py:110-111`)
   não tem prova própria. O plano o agrupa em "falha de conexão", provado pelo C4[refused], e o código não mudou desde
   a rodada 1.
