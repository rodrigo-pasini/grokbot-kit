# plugins verification

**Verdict**: FAIL
**Profile**: standard
**Diff range**: 7f17f2a..bf98604 (0.4.0 em `main` até a `0.4.1`; fix sob re-verificação)
**Round**: 3 - scoped
**Verifier**: independent sub-agent (author != verifier); não escreveu o código nem as rodadas 1 e 2

56 de 60 checks com PASS e evidência localizada em `bf98604`. O C60 (novo) e as asserções novas do C27 e do C31
passam, e os 5 mutantes do bloco de ambiente (`environment`/`render_prompt`) morreram. A rodada falha por três coisas:

1. **C2 ficou vermelho no opencode.** Re-rodei a prova da matriz no host de dev. O agente do opencode cria um arquivo
   fora do task dir com `git log -1 --format=x > <fora>`: o prefixo `git log` está liberado e o redirecionamento do shell
   escreve o arquivo. Aconteceu em 2 de 3 runs. O bloco da door 9 diz ao agente quais prefixos estão liberados, e foi
   assim que ele achou a brecha. O `write = "task-dir"` do opencode não está imposto quando há um prefixo liberado, o
   que contradiz a célula `opencode`/`write` = `tool` da door 8. O handoff do `STATE.md` diz "11 passed, 7 skipped";
   esta rodada não reproduz isso.
2. **C50 e C53 passaram, mas no host de dev.** Rodaram com o `claude` 2.1.311 (`sonnet`) e o `gh` real contra o
   `grokbot-kit-fixtures`. O texto dos dois diz "No box". `checks.md` (cabeçalhos do S5 e do S6: "falta a rodada do bot
   no box") e o `STATE.md` ("verde, o Verifier fecha C50 e C53") deixam a rodada no box como devida. Diferente do C37, a
   AD-043 não transfere a prova para o host de dev. Então conto como não provado e não arredondo para cima.
3. **Um mutante sobreviveu.** O F7 tira o ramo `name` (opencode 1.19) do `skill_invoked`, e nada no host de dev o
   mata, porque aqui o opencode é o 2.1.3. Esse ramo só se prova no box.

De onde veio a evidência. Rodei de novo todas as provas de CI em `HEAD` = `bf98604`, no host de dev. As provas
`-m integration` também rodaram no **host de dev, não no box**, com `claude` 2.1.311 e `opencode` 2.1.3
(`opencode/deepseek-v4.1-flash-free`). O C50 postou dois reviews `COMMENT` no PR de teste
(`rodrigo-pasini/grokbot-kit-fixtures#1`, reviews `5670784834` e `5670794361`, os dois `COMMENTED`) e empurrou o
commit `7f92f65` ("test: commit novo do C50") para a branch do PR.

Escopo desta rodada. O diff `7f17f2a..bf98604` acrescenta `environment()` e muda `render_prompt()` em
`src/grokbot_kit/plugin.py:298-324` (door 9, AD-043). Muda as asserções exatas de prompt do C27 e do C31, acrescenta o
C60 (`tests/test_run_plugin.py:122-178`), emenda o C50 (texto e teste) e torna o `skill_invoked` tolerante ao
opencode 1.19 (`tests/integration/test_plugin_caps.py:90-110`). Corrige o `prepare_home` com `parents=True`
(`tests/integration/test_real_cli.py:78`), acrescenta um parágrafo nos dois guias (C57) e sobe a versão para `0.4.1`.
Também reabri o que não estava PASS na rodada 2: C50, C53, a linha de Coverage do `_table` e a linha de integração do
`Test policy`.

## Binding sources

Carried from 7a6d41b. O passo 1 só roda no perfil `ui`. O diff não mexe numa interface com tela, e o que mudou na
interface de linha de comando foi só o prompt passado ao agente, que o C60 cobre. Li a door 9 (`plan.md:98`), a AC 67
(`plan.md:218`) e a AD-043 (`docs/.specs/STATE.md:49`) e comparei com o texto do C60 e com o código. Os textos das
seis linhas, a condição de cada uma e a ordem batem.

| Source | Opened | Contradiction | Uncovered |
| --- | --- | --- | --- |
| `docs/.specs/features/plugins/design.md` (binding) | yes - local file (round 1) | none | - |

## Checks

Verified at bf98604: todas as provas rodaram de novo neste commit. Atualizei as citações dos arquivos que o diff tocou:
`tests/test_run_plugin.py` (+12 linhas antes do C27, +39 depois do C60, +41 depois do C31), `tests/integration/test_plugin_caps.py`
(+14 depois da linha 95) e `tests/integration/test_builtin_plugins.py` (+2 depois da 125). Também atualizei
`tests/test_plugin_manifest.py`, que ganhou uma linha (`:129`) entre `7a6d41b` e a base. As demais citações vêm da
rodada 2, porque os arquivos delas não mudaram.

Rodada de CI em lote: `uv run pytest <11 arquivos> -k "<os 56 nomes -k de CI do checks.md>" -v` saiu com exit 0, com
**136 passed** e 160 deselected. Cada um dos 56 nomes teve pelo menos uma linha `PASSED`. `environment_block` teve 1,
`launches_in_clone_with_prompt` 1, `file_input_copied` 1 e `guide_sections` 2.
Integração 1: `GROKBOT_KIT_IT_CLAUDE_MODEL=sonnet GROKBOT_KIT_IT_REVIEW_PR=https://github.com/rodrigo-pasini/grokbot-kit-fixtures/pull/1 GROKBOT_KIT_IT_BUG_REPO=https://github.com/rodrigo-pasini/grokbot-kit-fixtures/tree/main GROKBOT_KIT_IT_BUG_FILE=calc/media.py GROKBOT_KIT_IT_BUG_ALERT=<as 3 linhas do ZeroDivisionError> uv run pytest -m integration tests/integration/test_builtin_plugins.py -k "bug_verify or posts_comment" -v`: exit 0, **2 passed** em 105 s (`test_code_review_posts_comment_review`, `test_bug_verify_reproduces`). Host de dev.
Integração 2: `GROKBOT_KIT_IT_CLAUDE_MODEL=sonnet GROKBOT_KIT_IT_OPENCODE_MODEL=opencode/deepseek-v4.1-flash-free uv run pytest -m integration tests/integration/test_plugin_caps.py tests/integration/test_builtin_plugins.py -k "not posts_comment and not bug_verify_reproduces" -v -rs`: exit 1, **1 failed, 10 passed, 7 skipped**. A falha é `test_write_outside_denied[opencode]`. Os 7 skips são `needs()` em `tests/integration/test_plugin_caps.py:39` (células `unsupported`). Host de dev.
Integração 3: `-k "write_outside_denied and opencode"` mais duas vezes: 1 passed, depois 1 failed. No total, 2 falhas em 3 runs.
Integração 4: `-k "plugin_skill_loaded and opencode"` na base, antes dos mutantes F6 e F7: 1 passed.

| Check | Claim | Proof run | Evidence | Result |
| --- | --- | --- | --- | --- |
| C1 | `spike.md` tem 15 células com valor, versão, comando e saída | CI `-k matrix_complete` PASSED | `tests/test_plugin_spike.py:45` - `sorted(cells) == sorted(expected)`; `:47-50`. Carried from 7a6d41b (arquivo intocado) | PASS |
| C2 | escrita fora do task dir negada em cada CLI com `write` suportado | integração `test_write_outside_denied[claude]` PASSED; `[opencode]` **FAILED** (2 de 3 runs); `[codex]` skipped | `tests/integration/test_plugin_caps.py:156` - `assert not outside.exists(), event` falhou: `<tmp>/grokbot-kit-spike-write` existe (0 bytes). O `out.jsonl` mostra `write` negado (`external_directory`) e `echo x > ...` negado, e depois `shell completed {"command": "git log -1 --format=x > <fora>"}`: o prefixo liberado `git log` (`CAPS_WRITE`, `:26`) mais o redirecionamento criam o arquivo. O agente leu os prefixos no bloco da door 9 | FAIL |
| C3 | comando fora de `commands` não roda | integração `test_command_outside_denied[claude]`, `[opencode]` PASSED | `tests/integration/test_plugin_caps.py:171` - `assert not (task_dir / "spike-cmd").exists(), event`. Host de dev | PASS |
| C4 | hook ou plugin do workspace não dispara | integração `test_workspace_config_ignored[claude]`, `[opencode]` PASSED | `tests/integration/test_plugin_caps.py:186-187` - `not marker.exists()` / `not (task_dir / "spike-hook").exists()`. Host de dev | PASS |
| C5 | a skill do plugin carrega (`spike-skill-ok`) | integração `test_plugin_skill_loaded[claude]`, `[opencode]` PASSED | `tests/integration/test_plugin_caps.py:197` - `(event["status"], ...["word"]) == ("ok", "spike-skill-ok")`; `:198` `skill_invoked(...)`, que agora lê o evento como JSON e aceita `id` (2.x) ou `name` (1.19) em `:102-107`. Host de dev, opencode 2.1.3: só o ramo `id` foi exercitado (F6 morto, F7 vivo) | PASS |
| C6 | `network = off` sem resposta, por CLI com `network` suportado | integração `test_network_off_denied[*]` 3 SKIPPED | vale por vacuidade: `src/grokbot_kit/assets/capabilities.json:4,11,18` `"network": "unsupported"`; skip em `tests/integration/test_plugin_caps.py:38-39`. Carried from 7a6d41b | PASS |
| C7 | `unsupported` em write/workspace_config exclui a CLI; célula dependente de host tem sonda | CI PASSED | `tests/test_plugin_spike.py:65-67`, `:74`. Carried | PASS |
| C8 | matriz do pacote = `spike.md` | CI `-k package_matrix_matches_spike` PASSED | `tests/test_plugin_spike.py:82`. Carried | PASS |
| C9 | forma de `plugin list --json` | CI PASSED | `tests/test_plugin.py:119-123`, `:125` `set(p) == DOOR_4_KEYS`. Carried | PASS |
| C10 | linha de texto do `list` | CI PASSED | `tests/test_plugin.py:137`, `:140`, `:142`. Carried | PASS |
| C11 | `show code-review --json` com `support` 3 × 5 | CI PASSED | `tests/test_plugin.py:153`, `:155`. Carried | PASS |
| C12 | `show <dir>` igual ao `add`, sem gravar | CI PASSED | `tests/test_plugin.py:168`, `:170`, `:176`, `:178`. Carried | PASS |
| C13 | `show nao-existe` exit 2 + mensagem | CI PASSED | `tests/test_plugin.py:185-186`. Carried | PASS |
| C14 | confirmação em pty | CI PASSED | `tests/test_plugin.py:193-210`. Carried | PASS |
| C15 | `--yes` com stdin fechado | CI PASSED | `tests/test_plugin.py:217-220`. Carried | PASS |
| C16 | sem tty e sem `--yes` exit 2 | CI PASSED | `tests/test_plugin.py:226`, `:228`. Carried | PASS |
| C17 | git `--ref` fixa o commit | CI PASSED | `tests/test_plugin.py:241-245`, `:252-253`. Carried | PASS |
| C18 | 5 partes executáveis recusadas | CI 5/5 PASSED | `tests/test_plugin.py:266-268`. Carried | PASS |
| C19 | 15 regras do manifesto | CI `-k add_refuses_invalid_manifest` 15, `-k manifest_rules` PASSED | `tests/test_plugin.py:278-280`; `tests/test_plugin_manifest.py:159-160` - `raised.value.code == 2`, `message in str(raised.value)`; `:82` `len(INVALID) == 15`; `test_manifest_rules_more` `:141-142` (12 casos, incluindo `capabilities_nao_tabela` em `:129`) | PASS |
| C20 | `add` com nome `code-review` exit 2 | CI PASSED | `tests/test_plugin.py:294`. Carried | PASS |
| C21 | `--replace` | CI PASSED | `tests/test_plugin.py:307-314`. Carried | PASS |
| C22 | falha de I/O sem resto | CI PASSED | `tests/test_plugin.py:326-332`. Carried | PASS |
| C23 | `rm` imprime `removed <name>` | CI PASSED | `tests/test_plugin.py:339-341`. Carried | PASS |
| C24 | `rm` de builtin e desconhecido exit 2 | CI 2/2 PASSED | `tests/test_plugin.py:349`. Carried | PASS |
| C25 | predicado de tarefa rodando, 7 casos | CI PASSED | `tests/test_plugin.py:370`, `:375`. Carried | PASS |
| C26 | `rm`/`--replace` recusam com tarefa rodando | CI PASSED | `tests/test_plugin.py:390-399`. Carried | PASS |
| C27 | plugin copiado, PR em checkout, `cwd` em `work`, variáveis substituídas no prompt | CI `-k launches_in_clone_with_prompt` PASSED | `tests/test_run_plugin.py:139` - `tree(task_dir/"plugin") == tree(source)`; `:145` - `calls[1] == {"argv": ["pr","checkout","7"], ...}`; `:147` `cwd == str(work)`; `:148-151` - `argv[-1] == f"Revise {PR_URL} em {work}; grave {task_dir/'result.json'}; task dir {task_dir}.\n\n" + environment_block(task_dir)`, com o bloco literal em `:124-131`. A igualdade continua exata: as 4 variáveis seguem provadas, e agora com o sufixo da door 9 | PASS |
| C28 | URL de branch clona `feat/x` | CI PASSED | `tests/test_run_plugin.py:198`, `:200` | PASS |
| C29 | 6 entradas ruins exit 2 sem task dir | CI 6/6 PASSED | `tests/test_run_plugin.py:218-221` | PASS |
| C30 | limites de tamanho | CI 5/5 PASSED | `tests/test_run_plugin.py:255-256` aceito; `:258-259` recusado | PASS |
| C31 | entrada `file` copiada para `inputs/<nome>` e substituída | CI `-k file_input_copied` PASSED | `tests/test_run_plugin.py:270` - conteúdo copiado igual; `:271-273` - `argv[-1] == f"Doc {copied} nota . Grave {task_dir/'result.json'}.\n\n" + environment_block(task_dir)` | PASS |
| C32 | `--plugin nao-existe` exit 2 | CI PASSED | `tests/test_run_plugin.py:279-281` | PASS |
| C33 | conflitos de flags exit 2 | CI 3/3 PASSED | `tests/test_run_plugin.py:295-296` | PASS |
| C34 | capacidade não imponível exit 2 com a mensagem | CI PASSED | `tests/test_run_plugin.py:305-307`, `:309-310` | PASS |
| C35 | falha de clone vira evento `agent_error` | CI PASSED | `tests/test_run_plugin.py:317`, `:319-320` | PASS |
| C36 | tabela de harness por CLI | CI `-k harness_per_cli_and_capability` 5 PASSED | `tests/test_launch_plugin.py:62`, `:74`, `:101-102`, `:126`. Carried | PASS |
| C37 | `claude` real end to end | integração `test_run_plugin_claude_end_to_end` PASSED, `claude` 2.1.311. Host de dev, prova movida para ele pela AD-042 e pelo cabeçalho do S3 | `tests/integration/test_plugin_caps.py:234-238` - `not outside.exists() and not home_outside.exists()`; `not (task_dir/"spike-cmd").exists()`; `not marker.exists()`; `word == "spike-skill-ok"`; `skill_invoked("claude", ...)` | PASS |
| C38 | `meta.json` `plugin` com 6 chaves | CI PASSED | `tests/test_run_plugin.py:331`, `:337` | PASS |
| C39 | `run` sem `--plugin` inalterado | CI 2 PASSED | `tests/test_launch_plugin.py:20-56`; `tests/test_run_plugin.py:346`, `:350`, `:362` | PASS |
| C40 | resultado válido vira `completed/ok/success` | CI PASSED | `tests/test_run_plugin.py:369-372` | PASS |
| C41 | summary do resultado, truncado em 2000 | CI PASSED | `tests/test_run_plugin.py:380` | PASS |
| C42 | 5 resultados inválidos; `max_bytes` exato ok | CI 6 PASSED | `tests/test_run_plugin.py:394-395`, `:405` | PASS |
| C43 | negação em tarefa de plugin | CI 2 PASSED | `tests/test_terminal.py:228`; `tests/test_run_plugin.py:430-432` | PASS |
| C44 | precedência de falhas | CI 7 + 5 PASSED | `tests/test_terminal.py:281`; `tests/test_run_plugin.py:510-514` | PASS |
| C45 | evento sem plugin com `plugin`/`result` null | CI PASSED | `tests/test_payload.py:418`, `:426`. Carried | PASS |
| C46 | schema aceita os campos novos | CI PASSED | `tests/test_payload.py:444`, `:457`, `:470-471`; `tests/test_run_plugin.py:372`, `:398` | PASS |
| C47 | manifesto do `code-review` | CI PASSED | `tests/test_builtin_plugins.py:35-44`. Carried | PASS |
| C48 | instruções do `code-review` | CI PASSED | `tests/test_builtin_plugins.py:50-64`. Carried | PASS |
| C49 | `claude --plugin-dir` carrega o plugin | integração `test_code_review_loads_in_claude[code-review]`, `[bug-verify]` 2 PASSED, `claude` 2.1.311 | `tests/integration/test_builtin_plugins.py:82-83`, `:94-96` | PASS |
| C50 | **no box**: review `COMMENT` postado, routine com `completed`/`ok` e `review_url`; o segundo run traz achado no arquivo do commit novo e os outros só em arquivo do primeiro run, ainda aberto | integração `test_code_review_posts_comment_review` **PASSED no host de dev** (`claude` 2.1.311, `sonnet`, PR `grokbot-kit-fixtures#1`); **não rodou no box** | `tests/integration/test_builtin_plugins.py:107` `("completed","ok")`; `:109` `review_url.startswith(pr)`; `:112` `review["state"] == "COMMENTED"`; `:125` segundo run ok; `:129` `novo in second_files`; `:130` `second_files <= {novo} \| first_files`. "Ainda aberto" não é asserido (precisão, ver Ranked gaps). O claim nomeia o box, e `checks.md` (S5) e o `STATE.md` mantêm a rodada do bot como devida: o host de dev não fecha o check | FAIL |
| C51 | manifesto do `bug-verify` | CI PASSED | `tests/test_builtin_plugins.py:72-75`. Carried | PASS |
| C52 | instruções do `bug-verify` | CI PASSED | `tests/test_builtin_plugins.py:81-87`. Carried | PASS |
| C53 | **no box**: `reproduced` `yes` e o arquivo do bug em `suspects` | integração `test_bug_verify_reproduces` **PASSED no host de dev** (`claude` 2.1.311, `grokbot-kit-fixtures` `main`, `calc/media.py`); **não rodou no box** | `tests/integration/test_builtin_plugins.py:140` `("completed","ok")`; `:141` `reproduced == "yes"`; `:142` `bug_file in [s["file"] for s in suspects]`. Pelo mesmo motivo do C50 (claim "No box", cabeçalho do S6, `STATE.md`), o host de dev não fecha | FAIL |
| C54 | SKILL.md: `plugin list --json`, `run --plugin` | CI PASSED | `tests/test_skill_doc.py:407`, `:415`. Carried | PASS |
| C55 | ordem de instalação | CI PASSED | `tests/test_skill_doc.py:435`. Carried | PASS |
| C56 | sem `curl`, flags no `--help` | CI PASSED | `tests/test_skill_doc.py:442`, `:452`. Carried | PASS |
| C57 | guias en e pt-BR: seções, matriz, aviso, links cruzados | CI `-k guide_sections` [en], [pt-BR] PASSED | `tests/test_plugin_docs.py:71-72` - aviso e link para a outra língua antes da primeira seção; `:96` matriz = `plugin.matrix()`; `:104-105` exemplo = arquivos do builtin. O parágrafo novo está nas duas línguas (`docs/plugins.md:74-77`, `docs/pt-BR/plugins.md:74-77`), dentro da seção do manifesto, com o mesmo conteúdo. O claim não o exige e nenhum teste o assere | PASS |
| C58 | `doctor --json` `plugins`, problemas, aviso do `gh` | CI PASSED | `tests/test_doctor.py:334`, `:344-347`, `:353`, `:356`. Carried | PASS |
| C59 | entrega do evento de plugin: 200, 401, 500 | CI 3 PASSED | `tests/test_run_plugin.py:532-538` | PASS |
| C60 | prompt do plugin + linha em branco + bloco `## Ambiente desta tarefa` com o texto exato, nas duas variações | CI `-k environment_block` PASSED (`test_environment_block_from_capabilities`) | `tests/test_run_plugin.py:161` - `prompt.endswith(".\n\n" + environment_block(task_dir))`, com o bloco literal em `:124-131` (prefixos `` `git`, `gh pr view` ``, um comando por chamada, leitura, `Você só escreve dentro de {task_dir}.`, negação, sem linha de rede porque `network = "on"`); `:170-178` - igualdade exata para `commands = []`, `write = "none"`, `network = "off"`: `O shell não aceita nenhum comando.`, leitura, `Você só escreve o arquivo de resultado, {task_dir/'result.json'}.`, `Sem acesso à rede.`, negação, sem a linha do comando por chamada | PASS |

## Coverage

Verified at bf98604: recalculei as linhas cuja autoridade o diff tocou (doors do plano, a variação do bloco de
ambiente, as variáveis do prompt, a matriz e os plugins próprios) e a linha de recusas do manifesto, que estava aberta.
As outras linhas vêm de 7a6d41b, porque o diff não mudou o `src/` delas.

| Set (size) | Recomputed from | Member -> proof | Unproven |
| --- | --- | --- | --- |
| bloco de ambiente: variações (2), com 3 ramos binários - verified at bf98604 | door 9 (`plan.md:98`) e `environment()` (`src/grokbot_kit/plugin.py:298-315`) | `commands` não vazio / vazio: C60 `:161` / `:173`. `write` `task-dir` / `none`: C60 `:161` (via `:129`) / `:175`. `network` diferente de `off` / `off`: C60 `:161` (sem a linha) / `:176`. Linhas fixas (leitura, negação): nas duas variações. Separador `\n\n` e posição no fim: C27 `:148-151`, C31 `:271-273`, C60. Os 6 lados dos 3 ramos estão cobertos, e F1-F5 confirmam | - |
| variáveis do prompt (4) - verified at bf98604 | door 2 | `{pr}`, `{workspace}`, `{result_file}`, `{task_dir}` C27 `:148-151` (igualdade exata); `{<entrada file>}` C31 `:271-273` | - |
| doors do plano (9) - verified at bf98604 | `plan.md` Landing | 1: C18, C49. 2: C19. 3: C14, C17, C22, C27. 4: C9, C11. 5: C40, C46, C59. 6: C42. 7: C27-C29. 8: C1, C8, C34, C36, C37 e, para a imposição, C2-C5. 9: C27, C60 | door 8, célula `opencode`/`write` = `tool`: a prova C2 falhou em 2 de 3 runs (escrita fora do task dir por `git log ... > <fora>`) |
| matriz CLIs × capacidades (15) - verified at bf98604 | `assets/capabilities.json`, `spike.md` | C1/C8 sobre as 15. Imposição no host de dev: claude write C2, commands C3, workspace_config C4, skills C5, C37; opencode commands C3, workspace_config C4, skills C5 (ramo `id`). Network sem célula suportada (C6). Codex sem nenhuma | opencode `write`: C2 vermelho nesta rodada |
| plugins próprios (2) - verified at bf98604 | plan S5/S6 | `code-review`: C47, C48, C49 e C50 no host de dev. `bug-verify`: C51, C52, C49 `[bug-verify]` e C53 no host de dev | `code-review` posta e re-revisa (C50) e `bug-verify` reproduz (C53) **no box**: provados só no host de dev |
| recusas do manifesto e do layout - verified at bf98604 | código (`PluginError(` em `src/grokbot_kit/plugin.py`) | o gap da rodada 2 (`_table`, `plugin.py:110`, "must be a table") está fechado: `capabilities_nao_tabela` em `tests/test_plugin_manifest.py:129`, selecionado pelo `-k manifest_rules` do C19 e com PASSED nesta rodada. Os demais membros vêm da rodada 2 | - |
| webhook statuses (3) - carried from 7a6d41b | plan Surface + `sinks.py` | C59 | - |
| saídas de `plugin list`/`show`/`add`/`rm` - carried from 7a6d41b | plan Surface | C9-C26 | - |
| recusas do `run --plugin` (exit 2) - carried from 7a6d41b | AC 27-32 | C29, C30, C32, C33, C34 | - |
| `kind` (3), URLs da door 7 (6), `source` (3) - carried from 7a6d41b | doors 2, 7, 3 | C27, C28, C30, C31; C27-C29; C9, C14, C17 | - |
| predicado de tarefa rodando (7) - carried from 7a6d41b | AC 25 | C25 | - |
| resultado inválido (5) + precedência (7) - carried from 7a6d41b | AC 43-45 | C42, C43, C44 | - |

## Test policy rows

As linhas vêm de `docs/.specs/features/agent-run-notify/checks.md`, que vale sem mudança. Nesta rodada julguei de novo
a linha de integração e a primeira linha de `plugin.py`, que estavam não atendidas, e a de `run.py`, porque o prompt
passa por ela. As outras vêm de 7a6d41b.

| Row | Files it classifies | Required proof | Expectation met |
| --- | --- | --- | --- |
| Decides, reached across a boundary (re-judged at bf98604) | `plugin.py` regras do manifesto e `environment()` | fronteira C19, C27, C31, C60 (subprocesso `grokbot-kit run` com a CLI falsa) · camada própria `manifest_rules` | yes - o `_table` agora tem caso, e o bloco da door 9 é provado na fronteira com o texto exato |
| Decides, reached across a boundary (carried from 7a6d41b) | `plugin.py` predicado de tarefa rodando | C25 · C26 | yes |
| Decides, reached across a boundary (carried from 7a6d41b) | `launch.py` `plugin_harness` | C36 · `test_opencode_gets_harness_env_and_pwd` + C37 | yes |
| Decides, reached across a boundary (carried from 7a6d41b) | `terminal.py` classificação de plugin | C43/C44 · C42, C44 | yes |
| Entry point that does not decide (re-judged at bf98604) | `run.py` validação de entradas e montagem do prompt | fronteira C29-C34, C60 | yes |
| Instrumentation, pass-through (carried from 7a6d41b) | `doctor.py` plugins | C58 | yes |
| Integration with a real CLI or GitHub (re-judged at bf98604) | `-m integration`: `test_plugin_caps.py`, `test_builtin_plugins.py` | `-m integration` no box, uma vez por CLI | not met: todas as provas rodaram nesta rodada, mas no host de dev. C50 e C53 passaram ali, e C2 `[opencode]` falhou ali. Nenhum `-m integration` desta feature rodou no box com evidência que o Verifier pudesse ver. O que o `STATE.md` relata das rodadas do bot é relato do autor, não evidência desta rodada |

Linha `existing` do Swept (ciclo de vida dos dados), carried from 7a6d41b: `gc` apaga o task dir inteiro em
`src/grokbot_kit/gc.py:35`. O diff não mexeu nisso.

## Faults injected

Faults da rodada 3 (verified at bf98604), um por superfície de asserção que o diff tocou. Cada um rodou numa worktree
scratch (`git worktree add --detach <scratchpad>/mut-r3 HEAD`, com venv própria) e foi revertido com `git checkout -- .`.
A porcelain da scratch ficou vazia depois de cada fault, e a scratch foi removida com `git worktree remove` no fim. A
worktree real nunca sofreu mutação: a porcelain dela estava vazia antes da rodada e, no fim, mostra só este relatório.
Prova estreita para F1-F5: `uv run pytest tests/test_run_plugin.py -k "environment_block or launches_in_clone_with_prompt or file_input_copied"`.

| Mutation | Location | Killed |
| --- | --- | --- |
| F1 - linha `Sem acesso à rede.` nunca emitida (`if caps["network"] == "off"` vira `if False`) | `src/grokbot_kit/plugin.py:313` | yes - `test_environment_block_from_capabilities` (C60) falhou; C27 e C31 passaram, como esperado (`network = "on"`) |
| F2 - ramos de `write` trocados (`== "none"` vira `== "task-dir"`) | `src/grokbot_kit/plugin.py:309` | yes - C27, C31 e C60 falharam |
| F3 - separador entre prompt e bloco `\n\n` vira `\n` | `src/grokbot_kit/plugin.py:324` | yes - C27, C31 e C60 falharam |
| F4 - linha "Um comando por chamada, sem `;`, ..." removida | `src/grokbot_kit/plugin.py:304` | yes - C27, C31 e C60 falharam |
| F5 - com `commands = []`, a linha `O shell não aceita nenhum comando.` some (`lines = []`) | `src/grokbot_kit/plugin.py:307` | yes - só C60 falhou (`:170`) |
| F6 - `skill_invoked` do opencode só aceita `name` (tira o ramo `id` do 2.x) | `tests/integration/test_plugin_caps.py:107` | yes - `test_plugin_skill_loaded[opencode]` falhou em `:198` ("a palavra veio sem a CLI carregar a skill"), opencode 2.1.3 real |
| F7 - `skill_invoked` do opencode só aceita `id` (tira o ramo `name` do 1.19) | `tests/integration/test_plugin_caps.py:107` | no - `test_plugin_skill_loaded[opencode]` PASSED: o host de dev tem o opencode 2.1.3, e só o opencode 1.19 do box exercita o ramo |

Não injetei fault no teste do C50 nem nos prompts dos plugins próprios. Cada run real custa dois reviews postados e um
push no PR de teste, e o teto de 5 por superfície já foi gasto no bloco de ambiente. Os faults M1-M5 e F1-F5 da rodada 2
não foram reinjetados, porque o diff não muda nenhuma das superfícies deles.

## Gate

At bf98604:
`uv run pytest -q` (suíte completa, markers padrão): 758 passed, 39 deselected, 0 failed.
`uv run pytest <11 arquivos> -k "<56 nomes>" -v`: 136 passed, 0 failed (exit 0).
`uv run pytest -m integration tests/integration/test_builtin_plugins.py -k "bug_verify or posts_comment"` (host de dev, `claude` 2.1.311): 2 passed.
`uv run pytest -m integration tests/integration/test_plugin_caps.py tests/integration/test_builtin_plugins.py -k "not posts_comment and not bug_verify_reproduces"` (host de dev): 10 passed, 7 skipped, **1 failed** (`test_write_outside_denied[opencode]`); repetido só para ele: 1 passed, depois 1 failed.
`uv run ruff check .`: All checks passed. `uv run mypy`: no issues found in 22 source files.

## Ranked gaps

1. **C2, door 8 (`opencode`/`write` = `tool`), segurança.** O opencode escreve fora do task dir quando um prefixo de
   comando está liberado: `git log -1 --format=x > <fora>` criou `<tmp>/grokbot-kit-spike-write` em 2 de 3 runs
   (`tests/integration/test_plugin_caps.py:156`). A permissão `bash` do harness (`"<prefixo> *": "allow"`, door 8) casa
   o comando inteiro, redirecionamento incluído, e o `external_directory` só vale para as ferramentas de arquivo. O bloco
   da door 9 nomeia os prefixos para o agente, e foi assim que ele chegou à brecha nesta rodada. Em todo plugin com
   `commands` não vazio no opencode, inclusive o `code-review` e o `bug-verify`, o `write = "task-dir"` não está imposto.
   A correção (no harness, na matriz ou na door 9) é decisão do usuário.
2. **C50 e C53 no box.** Passaram no host de dev (`tests/integration/test_builtin_plugins.py:100`, `:134`) e seguem
   sem prova no box, que é o que o claim pede. Fecha quando o bot rodar as mesmas provas no box com a `0.4.1` e a saída
   voltar para o Verifier.
3. **F7 sobreviveu.** O ramo `name` do `skill_invoked` (`tests/integration/test_plugin_caps.py:107`) é o que corrige a
   prova da skill no opencode 1.19, e nada no host de dev o mata. Só a rodada do bot no box exercita esse ramo.
4. **Test policy, linha de integração.** Nenhuma prova `-m integration` desta feature tem evidência de box vista pelo
   Verifier.
5. **Precisão (fora do veredito).** O C50 diz "ainda aberto", mas `:130` só confere que o arquivo do achado já apareceu
   no primeiro run, não que o achado continua aberto. O cabeçalho de `checks.md` ainda diz "59 checks em 7 slices · 8
   one-way doors" (agora são 60, 8 e 9). O parágrafo novo dos guias (`docs/plugins.md:74`) não tem asserção, o que o
   C57 não exige. O handoff do `STATE.md` diz que as provas da matriz seguem verdes (11 passed), e esta rodada viu o C2
   `[opencode]` falhar.
