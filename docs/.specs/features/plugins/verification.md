# plugins verification

**Verdict**: FAIL
**Profile**: standard
**Diff range**: 813224d..d8ffbe2 (fix da rodada 3 sob re-verificação; feature desde 7f17f2a)
**Round**: 4 - scoped
**Verifier**: independent sub-agent (author != verifier); não escreveu o código nem as rodadas anteriores

A door 10 faz o que promete. Com `"*>*": "deny"` por último no `bash` do opencode
(`src/grokbot_kit/launch.py:81`), os 7 escapes de shell do C61 não criaram arquivo nas duas CLIs (`opencode` 4 de 4,
`claude` 2 de 2), e o C2 do opencode passou 4 de 4. Os dois mutantes da regra morreram no teste unitário e no de
integração. A rodada falha por três motivos:

1. **C2 segue vermelho, agora por outro caminho e nas duas CLIs.** Testei um escape que o conjunto de 7 não tem: a
   opção de escrita do próprio comando liberado. Instruído a rodar `git log -1 --format=%h --output=<fora>/opt` com
   `commands = ["git log"]` (o mesmo `CAPS_WRITE` do C2), o agente criou `<fora>/opt` no `claude` 2.1.311 e no
   `opencode` 2.1.3. Não há `>`, então a door 10 não pega. O `Bash(git log *)` do `claude` também libera o comando.
   `git diff` e `git show` têm o mesmo `--output`, e os dois estão nos `commands` do `code-review` e do `bug-verify`.
   Então o `write = "task-dir"` não está imposto em nenhuma CLI para plugin com esses prefixos. Isso contradiz a célula
   `write` = `tool` da door 8 e a frase do CHANGELOG `0.4.1` "`claude` was not affected".
2. **C50 e C53 seguem sem prova no box.** Nada mudou desde a rodada 3: o diff não toca neles, e o Verifier não viu
   nenhuma rodada no box. Mantenho o julgamento da rodada 3.
3. **F7 segue vivo.** O ramo `name` (opencode 1.19) do `skill_invoked`, em `tests/integration/test_plugin_caps.py:102-110`,
   não mudou e só se prova no box. Carried from bf98604.

Onde rodou cada prova. As provas de CI rodaram em `HEAD` = `d8ffbe2` no host de dev. As provas `-m integration` também
rodaram no **host de dev, não no box**, com `claude` 2.1.311 (`sonnet`) e `opencode` 2.1.3
(`opencode/glm-5.3-flash-free`). O box (`opencode` 1.19.3) só é acessível pelo bot, e nada desta rodada foi provado
nele.

Escopo. O diff `813224d..d8ffbe2` muda uma linha de `src/` (`launch.py:80-81`, door 10). Acrescenta a asserção de
ordem ao C36 (`tests/test_launch_plugin.py:111-127`) e o C61 (`tests/integration/test_plugin_caps.py:160-183`), e
emenda o `plan.md` (door 10 em `:99`, AC 68 em `:220`), o `checks.md` (C36, C61, cabeçalho, Coverage), o `STATE.md`
(AD-044 em `:50`, handoff), os dois guias e o CHANGELOG. Re-verifiquei C2, C36, C57 e C61, mais as linhas de Coverage e
de `Test policy` que o diff toca ou que estavam abertas. O resto vem de `bf98604`.

## Binding sources


Carried from 7a6d41b. O passo 1 só roda no perfil `ui`. O diff não mexe numa interface com tela, e o que mudou na
interface de linha de comando foi só o prompt passado ao agente, que o C60 cobre. Li a door 9 (`plan.md:98`), a AC 67
(`plan.md:218`) e a AD-043 (`docs/.specs/STATE.md:49`) e comparei com o texto do C60 e com o código. Os textos das
seis linhas, a condição de cada uma e a ordem batem.

| Source | Opened | Contradiction | Uncovered |
| --- | --- | --- | --- |
| `docs/.specs/features/plugins/design.md` (binding) | yes - local file (round 1) | none | - |

Rodada 4 (carried from bf98604): o diff não toca em interface com tela. Li a door 10 (`plan.md:99`), a AC 68
(`plan.md:220`) e a AD-044 (`docs/.specs/STATE.md:50`) contra o código (`launch.py:81`) e o C36/C61. A ordem e o
padrão batem.

## Checks

Proofs re-run at d8ffbe2. Os resultados de C2, C36, C57 e C61 foram verificados em d8ffbe2. As citações de
`tests/integration/test_plugin_caps.py` (+26 linhas depois de `:157`) e de `tests/test_launch_plugin.py` foram
atualizadas. As demais linhas vêm de bf98604 (rodada 3), com as provas de CI re-rodadas e verdes em d8ffbe2.

Rodada de CI em lote: `uv run pytest <os 11 arquivos de CI do checks.md> -k "<os 56 nomes -k>" -v` saiu com exit 0,
**136 passed** e 160 deselected. Cada um dos 56 nomes teve pelo menos uma linha `PASSED`, entre elas os 5 casos de
`harness_per_cli_and_capability`.
Integração 1: `GROKBOT_KIT_IT_CLAUDE_MODEL=sonnet GROKBOT_KIT_IT_OPENCODE_MODEL=opencode/glm-5.3-flash-free uv run pytest -m integration tests/integration/test_plugin_caps.py -k "shell_escape_denied or write_outside_denied" -v -rs`: exit 0, **4 passed, 2 skipped** (codex, `needs` em `:39`). Host de dev.
Integrações 2-4: o mesmo, com `-k "(shell_escape_denied or write_outside_denied) and opencode"`, mais 3 vezes: 2 passed cada, exit 0. No total, C2 `[opencode]` passou 4 de 4 e C61 `[opencode]` passou 4 de 4.
Integração 5 (worktree scratch, código de `HEAD`): `-k "(probe_git_output_option and opencode) or (shell_escape_denied and claude)"`: C61 `[claude]` PASSED (2 de 2 na rodada) e a sonda `[opencode]` FAILED (`['opt'] == []`). Antes, só a sonda `[claude]` também deu FAILED. Uma primeira tentativa da sonda com `--format=x` foi inconclusiva: o git recusa `x` como formato antes de abrir o arquivo. Host de dev.

| Check | Claim | Proof run | Evidence | Result |
| --- | --- | --- | --- | --- |
| C1 | `spike.md` tem 15 células com valor, versão, comando e saída | CI `-k matrix_complete` PASSED | `tests/test_plugin_spike.py:45` - `sorted(cells) == sorted(expected)`; `:47-50`. Carried from 7a6d41b (arquivo intocado) | PASS |
| C2 | escrita fora do task dir negada em cada CLI com `write` suportado (AC 2: agente instruído a criar um arquivo fora do task dir) | integração `test_write_outside_denied[claude]` PASSED 1/1; `[opencode]` PASSED 4/4; `[codex]` SKIPPED. **Sonda do Verifier** (teste só na worktree scratch, mesmo `spike_plugin`, `CAPS_WRITE` com `commands = ["git log"]`, mesmo `run_plugin`): o agente instruído a rodar `git log -1 --format=%h --output=<fora>/opt` → `[claude]` **FAILED**, `[opencode]` **FAILED** | `tests/integration/test_plugin_caps.py:156` - `assert not outside.exists(), event` (verde). A sonda usa a mesma asserção de C61 (`:183`, `sorted(p.name for p in outside.iterdir()) == []`) e falhou com `assert ['opt'] == []` nas duas CLIs: o `--output` do próprio `git log` cria o arquivo fora do task dir, sem `>`. O `claude` resumiu "Não foi negado: o comando git log foi executado"; o `opencode`, "foi aceito pelo shell (prefixo `git log` permitido)". O git saiu 128 (repo sem commit), mas o arquivo já tinha sido criado (0 bytes); num repo com commits ele recebe o log, e um arquivo existente é truncado. A door 10 (`src/grokbot_kit/launch.py:81`) fecha só os operadores do shell; a regra `"<prefixo> *": "allow"` (`:81`, e `Bash(<prefixo> *)` no `claude`, `:65`) continua deixando a opção de escrita do próprio comando liberado. Host de dev, `claude` 2.1.311 e `opencode` 2.1.3 | FAIL |
| C3 | comando fora de `commands` não roda | integração `test_command_outside_denied[claude]`, `[opencode]` PASSED | `tests/integration/test_plugin_caps.py:197` - `assert not (task_dir / "spike-cmd").exists(), event`. Host de dev (citação atualizada em d8ffbe2; resultado carried from bf98604) | PASS |
| C4 | hook ou plugin do workspace não dispara | integração `test_workspace_config_ignored[claude]`, `[opencode]` PASSED | `tests/integration/test_plugin_caps.py:212-213` - `not marker.exists()` / `not (task_dir / "spike-hook").exists()`. Host de dev (citação atualizada em d8ffbe2; resultado carried from bf98604) | PASS |
| C5 | a skill do plugin carrega (`spike-skill-ok`) | integração `test_plugin_skill_loaded[claude]`, `[opencode]` PASSED | `tests/integration/test_plugin_caps.py:223` - `(event["status"], ...["word"]) == ("ok", "spike-skill-ok")`; `:224` `skill_invoked(...)`, que agora lê o evento como JSON e aceita `id` (2.x) ou `name` (1.19) em `:102-107`. Host de dev, opencode 2.1.3: só o ramo `id` foi exercitado (F6 morto, F7 vivo) (citação atualizada em d8ffbe2; resultado carried from bf98604) | PASS |
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
| C36 | tabela de harness por CLI, mais `"*>*": "deny"` por último no `bash` do opencode (door 10) | CI `-k harness_per_cli_and_capability` 5 PASSED (`_claude`, `_opencode[2-args0]`, `[1-args1]`, `[None-args2]`, `_codex`) | `tests/test_launch_plugin.py:62`, `:74` (claude); `:107-124` - igualdade do `OPENCODE_CONFIG_CONTENT` com `"bash": {"*": "deny", "git": "allow", "git *": "allow", "gh pr view": "allow", "gh pr view *": "allow", "*>*": "deny"}` (`:111-118`); `:127` - `list(bash.items())[-1] == ("*>*", "deny")`, que prova a ordem que a igualdade de dict não prova; `:136` codex `ValueError`. Verified at d8ffbe2; M1 e M2 mortos | PASS |
| C37 | `claude` real end to end | integração `test_run_plugin_claude_end_to_end` PASSED, `claude` 2.1.311. Host de dev, prova movida para ele pela AD-042 e pelo cabeçalho do S3 | `tests/integration/test_plugin_caps.py:260-264` - `not outside.exists() and not home_outside.exists()`; `not (task_dir/"spike-cmd").exists()`; `not marker.exists()`; `word == "spike-skill-ok"`; `skill_invoked("claude", ...)` (citação atualizada em d8ffbe2; resultado carried from bf98604) | PASS |
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
| C57 | guias en e pt-BR: seções, matriz, aviso, links cruzados | CI `-k guide_sections` [en], [pt-BR] PASSED | `tests/test_plugin_docs.py:71-72` - aviso e link para a outra língua antes da primeira seção; `:96` matriz = `plugin.matrix()`; `:104-105` exemplo = arquivos do builtin. O parágrafo novo está nas duas línguas (`docs/plugins.md:74-77`, `docs/pt-BR/plugins.md:74-77`), dentro da seção do manifesto, com o mesmo conteúdo. O claim não o exige e nenhum teste o assere. Em d8ffbe2 o diff acrescenta o parágrafo da door 10 nas duas línguas, na seção de capacidades, com o mesmo conteúdo (`docs/plugins.md:99-100`, `docs/pt-BR/plugins.md:99-101`); `guide_sections` [en] e [pt-BR] PASSED de novo; nenhum teste assere o parágrafo novo, o que o C57 não exige. Verified at d8ffbe2 | PASS |
| C58 | `doctor --json` `plugins`, problemas, aviso do `gh` | CI PASSED | `tests/test_doctor.py:334`, `:344-347`, `:353`, `:356`. Carried | PASS |
| C59 | entrega do evento de plugin: 200, 401, 500 | CI 3 PASSED | `tests/test_run_plugin.py:532-538` | PASS |
| C60 | prompt do plugin + linha em branco + bloco `## Ambiente desta tarefa` com o texto exato, nas duas variações | CI `-k environment_block` PASSED (`test_environment_block_from_capabilities`) | `tests/test_run_plugin.py:161` - `prompt.endswith(".\n\n" + environment_block(task_dir))`, com o bloco literal em `:124-131` (prefixos `` `git`, `gh pr view` ``, um comando por chamada, leitura, `Você só escreve dentro de {task_dir}.`, negação, sem linha de rede porque `network = "on"`); `:170-178` - igualdade exata para `commands = []`, `write = "none"`, `network = "off"`: `O shell não aceita nenhum comando.`, leitura, `Você só escreve o arquivo de resultado, {task_dir/'result.json'}.`, `Sem acesso à rede.`, negação, sem a linha do comando por chamada | PASS |
| C61 | para cada CLI com `commands` suportado, 7 escapes do shell (`>`, `>>`, `2>`, `;`, `&&`, `\|`, `$(...)`) com `commands = ["git log"]` não criam arquivo fora do task dir | integração `test_shell_escape_denied[claude]` PASSED 2/2; `[opencode]` PASSED 4/4; `[codex]` SKIPPED (`needs`, `:39`). Host de dev | `tests/integration/test_plugin_caps.py:183` - `assert sorted(p.name for p in outside.iterdir()) == [], event["result"]`, com os 7 comandos literais em `:167-175`. Não vacuidade: o `result.json` dos runs inspecionados diz que os 7 foram negados (`claude`: "Todos os 7 comandos foram negados pelo shell (modo don't ask)"; `opencode`: "Todos os 7 comandos foram negados pelo controle de permissões do shell (permission rejected)"). Com a regra removida (M1) ou antes dos prefixos (M2), `[opencode]` falhou com 3 arquivos (`append`, ...): a prova discrimina. O claim é verdadeiro nos 7 membros; o conjunto é que está incompleto (ver C2 e Coverage). Verified at d8ffbe2 | PASS |

## Coverage

Verified at d8ffbe2 nas linhas cuja autoridade o diff tocou: os escapes, as doors e a matriz. As outras são carried
from bf98604.

| Set (size) | Recomputed from | Member -> proof | Unproven |
| --- | --- | --- | --- |
| escapes do shell por prefixo liberado (7 no `checks.md`; 8 recomputados) - verified at d8ffbe2 | não o código do kit: o shell (operadores de redirecionamento, encadeamento, pipe e substituição) e as opções de escrita dos próprios comandos liberados (`git log`/`git diff`/`git show` `--output=<arquivo>`, nos `commands` do `code-review` e do `bug-verify`, `src/grokbot_kit/assets/plugins/*/grokbot-kit.toml`) | `>` `>>` `2>` `;` `&&` pipe `$(...)`: C61 `:183`, nas duas CLIs. `git log --output=<fora>`: sem check; a sonda do Verifier o criou nas duas CLIs | `--output=<arquivo>` de um comando liberado (`git log`, e pelo mesmo mecanismo `git diff` e `git show`): escreve fora do task dir em `claude` e `opencode`. O conjunto do `checks.md` só enumera operadores do shell, que a door 10 cobre |
| bloco de ambiente: variações (2), com 3 ramos binários - carried from bf98604 | door 9 (`plan.md:98`) e `environment()` (`src/grokbot_kit/plugin.py:298-315`) | `commands` não vazio / vazio: C60 `:161` / `:173`. `write` `task-dir` / `none`: C60 `:161` (via `:129`) / `:175`. `network` diferente de `off` / `off`: C60 `:161` (sem a linha) / `:176`. Linhas fixas (leitura, negação): nas duas variações. Separador `\n\n` e posição no fim: C27 `:148-151`, C31 `:271-273`, C60. Os 6 lados dos 3 ramos estão cobertos, e F1-F5 confirmam | - |
| variáveis do prompt (4) - carried from bf98604 | door 2 | `{pr}`, `{workspace}`, `{result_file}`, `{task_dir}` C27 `:148-151` (igualdade exata); `{<entrada file>}` C31 `:271-273` | - |
| doors do plano (10) - verified at d8ffbe2 | `plan.md` Landing (`:90-99`) | 1-9 como na rodada 3 (8: C1, C8, C34, C36, C37 e, para a imposição, C2-C5). 10: C36 (`tests/test_launch_plugin.py:111-118`, `:127`) e C61 (`tests/integration/test_plugin_caps.py:183`) | door 8, célula `write` = `tool` de `claude` e `opencode`: o C2 caiu de novo, agora pela opção `--output` do `git log` liberado (sonda do Verifier nas duas CLIs)
| matriz CLIs × capacidades (15) - verified at d8ffbe2 | `assets/capabilities.json`, `spike.md` | C1/C8 sobre as 15. Imposição no host de dev: claude write C2, C61, commands C3, workspace_config C4, skills C5, C37; opencode write C2 (4/4), C61, commands C3, workspace_config C4, skills C5 (ramo `id`). Network sem célula suportada (C6). Codex sem nenhuma. C3-C5 carried from bf98604 | `claude`/`write` e `opencode`/`write`: a sonda `git log --output=<fora>` criou o arquivo nas duas
| plugins próprios (2) - carried from bf98604 | plan S5/S6 | `code-review`: C47, C48, C49 e C50 no host de dev. `bug-verify`: C51, C52, C49 `[bug-verify]` e C53 no host de dev | `code-review` posta e re-revisa (C50) e `bug-verify` reproduz (C53) **no box**: provados só no host de dev |
| recusas do manifesto e do layout - carried from bf98604 | código (`PluginError(` em `src/grokbot_kit/plugin.py`) | o gap da rodada 2 (`_table`, `plugin.py:110`, "must be a table") está fechado: `capabilities_nao_tabela` em `tests/test_plugin_manifest.py:129`, selecionado pelo `-k manifest_rules` do C19 e com PASSED nesta rodada. Os demais membros vêm da rodada 2 | - |
| webhook statuses (3) - carried from 7a6d41b | plan Surface + `sinks.py` | C59 | - |
| saídas de `plugin list`/`show`/`add`/`rm` - carried from 7a6d41b | plan Surface | C9-C26 | - |
| recusas do `run --plugin` (exit 2) - carried from 7a6d41b | AC 27-32 | C29, C30, C32, C33, C34 | - |
| `kind` (3), URLs da door 7 (6), `source` (3) - carried from 7a6d41b | doors 2, 7, 3 | C27, C28, C30, C31; C27-C29; C9, C14, C17 | - |
| predicado de tarefa rodando (7) - carried from 7a6d41b | AC 25 | C25 | - |
| resultado inválido (5) + precedência (7) - carried from 7a6d41b | AC 43-45 | C42, C43, C44 | - |

## Test policy rows

As linhas vêm de `docs/.specs/features/agent-run-notify/checks.md`. Julguei de novo a de `launch.py`, arquivo que o
diff tocou, e a de integração, que estava não atendida. As outras são carried from bf98604.

| Row | Files it classifies | Required proof | Expectation met |
| --- | --- | --- | --- |
| Decides, reached across a boundary (carried from bf98604) | `plugin.py` regras do manifesto e `environment()` | fronteira C19, C27, C31, C60 (subprocesso `grokbot-kit run` com a CLI falsa) · camada própria `manifest_rules` | yes - o `_table` agora tem caso, e o bloco da door 9 é provado na fronteira com o texto exato |
| Decides, reached across a boundary (carried from 7a6d41b) | `plugin.py` predicado de tarefa rodando | C25 · C26 | yes |
| Decides, reached across a boundary (re-judged at d8ffbe2) | `launch.py` `plugin_harness` (door 10) | C36 (camada própria, igualdade e ordem) · C61, C2 (fronteira, CLIs reais) | yes para a regra que o diff acrescentou: as duas camadas a provam e M1/M2 morrem nas duas. A falha de imposição do `--output` é do C2/coverage, não desta linha |
| Decides, reached across a boundary (carried from 7a6d41b) | `terminal.py` classificação de plugin | C43/C44 · C42, C44 | yes |
| Entry point that does not decide (carried from bf98604) | `run.py` validação de entradas e montagem do prompt | fronteira C29-C34, C60 | yes |
| Instrumentation, pass-through (carried from 7a6d41b) | `doctor.py` plugins | C58 | yes |
| Integration with a real CLI or GitHub (re-judged at d8ffbe2) | `-m integration`: `test_plugin_caps.py`, `test_builtin_plugins.py` | `-m integration` no box, uma vez por CLI | not met: nesta rodada C2 e C61 rodaram no host de dev (`claude` 2.1.311, `opencode` 2.1.3), não no box (`opencode` 1.19.3). C50 e C53 seguem sem rodada no box vista pelo Verifier |

Linha `existing` do Swept (ciclo de vida dos dados), carried from 7a6d41b: `gc` apaga o task dir inteiro em
`src/grokbot_kit/gc.py:35`.

## Faults injected

Rodada 4 (verified at d8ffbe2): uma superfície nova, a regra `bash` do opencode em `src/grokbot_kit/launch.py:81`.
Cada fault rodou na worktree scratch (`git worktree add --detach <scratchpad>/mut-r4 HEAD`, venv própria) e foi revertido com
`git checkout -- src`, com `git diff --stat -- src` vazio depois. A scratch foi removida com `git worktree remove`. A
porcelain da worktree real estava vazia antes da rodada e continuou vazia depois de remover a scratch.

| Mutation | Location | Killed |
| --- | --- | --- |
| M1 - regra `"*>*": "deny"` removida do `bash` | `src/grokbot_kit/launch.py:81` | yes - C36 `tests/test_launch_plugin.py:107` (igualdade do config), 3 falhas: `opencode[2-args0]`, `[1-args1]`, `[None-args2]`; e C61 `test_shell_escape_denied[opencode]` real em `:183`, com 3 arquivos criados (`append`, ...) |
| M2 - `"*>*": "deny"` movida para antes dos prefixos (`{"*": "deny", "*>*": "deny", **prefixos}`) | `src/grokbot_kit/launch.py:81` | yes - C36 `tests/test_launch_plugin.py:127` (`AssertionError: assert ('gh pr view *', 'allow') == ('*>*', 'deny')`; a igualdade de dict em `:107` sozinha não mataria); e C61 `[opencode]` real em `:183`, 3 arquivos criados: no opencode vale a última regra que casa |
| (rodada 3, carried from bf98604) F1 - linha `Sem acesso à rede.` nunca emitida (`if caps["network"] == "off"` vira `if False`) | `src/grokbot_kit/plugin.py:313` | yes - `test_environment_block_from_capabilities` (C60) falhou; C27 e C31 passaram, como esperado (`network = "on"`) |
| (rodada 3, carried from bf98604) F2 - ramos de `write` trocados (`== "none"` vira `== "task-dir"`) | `src/grokbot_kit/plugin.py:309` | yes - C27, C31 e C60 falharam |
| (rodada 3, carried from bf98604) F3 - separador entre prompt e bloco `\n\n` vira `\n` | `src/grokbot_kit/plugin.py:324` | yes - C27, C31 e C60 falharam |
| (rodada 3, carried from bf98604) F4 - linha "Um comando por chamada, sem `;`, ..." removida | `src/grokbot_kit/plugin.py:304` | yes - C27, C31 e C60 falharam |
| (rodada 3, carried from bf98604) F5 - com `commands = []`, a linha `O shell não aceita nenhum comando.` some (`lines = []`) | `src/grokbot_kit/plugin.py:307` | yes - só C60 falhou (`:170`) |
| (rodada 3, carried from bf98604) F6 - `skill_invoked` do opencode só aceita `name` (tira o ramo `id` do 2.x) | `tests/integration/test_plugin_caps.py:107` | yes - `test_plugin_skill_loaded[opencode]` falhou em `:198` ("a palavra veio sem a CLI carregar a skill"), opencode 2.1.3 real |
| (rodada 3, carried from bf98604) F7 - `skill_invoked` do opencode só aceita `id` (tira o ramo `name` do 1.19) | `tests/integration/test_plugin_caps.py:107` | no - `test_plugin_skill_loaded[opencode]` PASSED: o host de dev tem o opencode 2.1.3, e só o opencode 1.19 do box exercita o ramo |

M1-M5 e F1-F5 das rodadas 2 e 3 não foram reinjetados, porque o diff não toca nas superfícies deles. F7 segue vivo
pelo motivo da rodada 3: o ramo só roda no `opencode` 1.19, do box.

## Gate

At d8ffbe2:
`uv run pytest -q` (suíte completa, markers padrão): 758 passed, 42 deselected, 0 failed.
`uv run pytest <11 arquivos> -k "<56 nomes>" -v`: 136 passed, 0 failed (exit 0).
`uv run pytest -m integration tests/integration/test_plugin_caps.py -k "shell_escape_denied or write_outside_denied"` (host de dev): 4 passed, 2 skipped; opencode repetido 3 vezes: 2 passed em cada.
Sonda `git log --output=<fora>` (só na scratch, host de dev): `claude` FAILED, `opencode` FAILED.
`uv run ruff check .`: All checks passed. `uv run mypy`: no issues found in 22 source files.

## Ranked gaps

1. **C2, door 8 (`write` = `tool` em `claude` e `opencode`), segurança.** Um prefixo liberado deixa passar a opção de
   escrita do próprio comando. `git log -1 --format=%h --output=<fora>/opt` criou o arquivo nas duas CLIs. Em
   `src/grokbot_kit/launch.py:65` (`Bash(<prefixo> *)`) e `:81` (`"<prefixo> *": "allow"`), a regra casa qualquer
   argumento. `git diff --output` e `git show --output` seguem o mesmo mecanismo e estão nos `commands` dos dois plugins
   próprios. Não os provei um a um. O conjunto "escapes do shell por prefixo liberado (7)" só enumera operadores do shell,
   e por isso o C61 fica verde com a brecha aberta. O CHANGELOG (`CHANGELOG.md:15-18`) e a AD-044 dizem que o `claude`
   não foi afetado, e a sonda desmente isso para esta classe de escape. Como corrigir (negar `*--output*`, restringir os
   prefixos, documentar como risco aceito, como já se faz com `pytest`) é decisão do usuário.
2. **C50 e C53 no box.** Seguem como na rodada 3: provados só no host de dev.
3. **F7 vivo.** É o ramo `name` do `skill_invoked`, que só o box exercita. Carried from bf98604.
4. **Test policy, linha de integração.** Nenhuma prova `-m integration` desta feature tem evidência de box.
5. **Observação (fora do veredito).** `"*>*"` também nega comando legítimo com `>` dentro de aspas, por exemplo
   `gh api ... --jq '.[] | select(.n > 1)'` ou `git log --format='%h > %s'` no `code-review`. O agente recebe
   negação e segue (door 9). O bloco da door 9 não menciona o `>`, e o C60 não mudou.
