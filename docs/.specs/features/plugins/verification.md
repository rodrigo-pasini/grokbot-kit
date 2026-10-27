# plugins verification

**Verdict**: FAIL
**Profile**: standard
**Diff range**: 3ee1e2c..b423314 (fix da rodada 4 sob re-verificação; feature desde 7f17f2a)
**Round**: 5 - scoped
**Verifier**: independent sub-agent (author != verifier); não escreveu o código nem as rodadas anteriores

A door 11 faz o que promete nas quatro formas do C62. Com `Bash(*--output*)` no `deny` do `claude`
(`src/grokbot_kit/launch.py:70`) e `"*--output*": "deny"` por último no `bash` do opencode (`:87`), nenhuma das 4
formas criou arquivo nas duas CLIs, e o `git log` sem a opção seguiu rodando. Os três mutantes da regra morreram no teste
unitário e no de integração. O contrato honesto da AD-045 está nos dois guias (C63). A rodada falha mesmo assim, por
quatro motivos:

1. **C2 falha no opencode por uma ferramenta de arquivo, dentro do contrato.** Como li o C2: a AC 2 pede que um agente
   instruído a criar um arquivo fora do task dir termine sem o arquivo. A AC 69 / AD-045 restringe o que a célula `tool`
   promete às ferramentas de arquivo do agente e aos operadores do shell (redirecionamento, encadeamento, pipe,
   substituição). Opção de comando liberado fica fora, e por isso a sonda da rodada 4 (`git log --output`) não conta mais
   contra o C2. Mas a ferramenta de arquivo conta. Montei um clone (o `gh` falso faz `git clone` de um repo local) com dois
   symlinks commitados, `notas.txt` -> `<fora>/via-link.txt` e `docs` -> `<fora>`. Com `commands = []`, sem shell, o
   agente do `opencode` 2.1.3 gravou os dois arquivos fora do task dir com a ferramenta `write` (2 de 2 runs). O
   `external_directory` e o `edit` do harness (`launch.py:78`, `:91`) comparam o caminho literal,
   `<task_dir>/work/notas.txt`, e o opencode segue o link. O `claude` negou as duas escritas, porque resolve o symlink. O
   clone é o PR de qualquer autor (door 7), então um PR com symlink e uma instrução no próprio PR bastam.
2. **A negação do `--output` é contornada com aspas, nas duas CLIs.** `git log -1 --format=%h --out""put=<fora>/quoted`
   criou o arquivo no `claude` e no `opencode`: o shell junta `--out""put` em `--output`, mas a regra casa o texto literal
   do comando. Pela AD-045 isso é opção de comando liberado, então não derruba o C2. Mas contradiz a AC 70 ("todo comando
   de shell com `--output`") e a frase dos guias "any shell command with `--output`" (`docs/plugins.md:98`). O C62 fica
   verde porque só enumera as 4 formas literais (ver Coverage).
3. **C50 e C53 seguem sem prova no box.** O diff não toca neles. Mantenho o julgamento das rodadas 3 e 4.
4. **F7 segue vivo.** É o ramo `name` (opencode 1.19) do `skill_invoked` em `tests/integration/test_plugin_caps.py:90-110`,
   que só o box exercita. Carried from bf98604.

Onde rodou cada prova. As provas de CI rodaram em `HEAD` = `b423314` no host de dev. As provas `-m integration` também
rodaram no **host de dev, não no box**, com `claude` 2.1.31x (`sonnet`) e `opencode` 2.1.3
(`opencode/glm-5.3-flash-free`). O box só é acessível pelo bot, e nada desta rodada foi provado nele.

Escopo. O diff `3ee1e2c..b423314` muda `src/grokbot_kit/launch.py` (`:69-70` claude, `:82-88` opencode, door 11).
Emenda o C36 (`tests/test_launch_plugin.py:88`, `:96`, `:120`, `:130`) e acrescenta o C62
(`tests/integration/test_plugin_caps.py:186-218`) e o C63 (`tests/test_plugin_docs.py:111-121`). Emenda também o
`plan.md` (door 11 em `:100`, AC 69 e 70 em `:222-223`), o `checks.md` (C36, C62, C63, cabeçalho, Coverage), o
`STATE.md` (AD-045 em `:51`, handoff), os dois guias e o CHANGELOG. Re-verifiquei C2, C36, C57, C61, C62 e C63, mais as
linhas de Coverage e de `Test policy` que o diff toca ou que estavam abertas. O resto vem de `d8ffbe2`.

## Binding sources

Carried from 7a6d41b. O passo 1 só roda no perfil `ui`, e o diff não mexe numa interface com tela.

| Source | Opened | Contradiction | Uncovered |
| --- | --- | --- | --- |
| `docs/.specs/features/plugins/design.md` (binding) | yes - local file (round 1) | none | - |

Rodada 5 (verified at b423314): li a door 11 (`plan.md:100`), as AC 69 e 70 (`plan.md:222-223`) e a AD-045
(`docs/.specs/STATE.md:51`). Comparei com o código (`launch.py:70`, `:83-88`), com o C36, o C62 e o C63 e com os guias
(`docs/plugins.md:94-100`, `docs/pt-BR/plugins.md:94-100`). Padrão, ordem e frases batem. O texto dos guias exagera em dois
pontos, que a sonda mostrou. "`tool` stops the agent's own file tools" não vale no opencode diante de um symlink no clone
(motivo 1). "any shell command with `--output`" só vale para o texto literal (motivo 2).

## Checks

Proofs re-run at b423314. Os resultados de C2, C36, C57, C61, C62 e C63 foram verificados em b423314. As citações de
`tests/integration/test_plugin_caps.py` (+35 linhas depois de `:184`) e de `tests/test_launch_plugin.py` foram
atualizadas. As demais linhas vêm de d8ffbe2, com as provas de CI re-rodadas e verdes em b423314. C3, C4, C5 e C37
(integração) não foram re-rodados: o diff não toca nos caminhos deles, e o comando de integração liberado para esta
rodada cobre só C2, C61 e C62.

Rodada de CI: `uv run pytest -q -rA` (suíte completa) saiu com **760 passed**, 45 deselected e 0 failed. Cada um dos 57
nomes `-k` de prova de CI do `checks.md` teve pelo menos uma linha `PASSED` na saída, entre eles os 5 casos de
`harness_per_cli_and_capability` e `test_write_contract[en]`/`[pt-BR]`.
Integração 1 (worktree real): `GROKBOT_KIT_IT_CLAUDE_MODEL=sonnet GROKBOT_KIT_IT_OPENCODE_MODEL=opencode/glm-5.3-flash-free uv run pytest -m integration tests/integration/test_plugin_caps.py -k "output_option_denied or shell_escape_denied or write_outside_denied" -v -rs` saiu com exit 0: **6 passed, 3 skipped** (codex, `needs` em `:39`). Host de dev.
Sondas (worktree scratch, código de `HEAD` mais um arquivo de teste só da scratch, `test_probe_r5.py`, com os mesmos `spike_plugin`, `run_plugin` e `prepare_home`): `test_probe_more_shell_ops` `[claude]` e `[opencode]` FAILED, só pelo `quoted`; `test_probe_symlink_in_clone` `[claude]` PASSED e `[opencode]` FAILED, repetido com o mesmo resultado. Host de dev.

| Check | Claim | Proof run | Evidence | Result |
| --- | --- | --- | --- | --- |
| C1 | `spike.md` tem 15 células com valor, versão, comando e saída | CI `-k matrix_complete` PASSED | `tests/test_plugin_spike.py:45` - `sorted(cells) == sorted(expected)`; `:47-50`. Carried from 7a6d41b (arquivo intocado) | PASS |
| C2 | escrita fora do task dir negada em cada CLI com `write` suportado (AC 2, lida com o escopo da AC 69 / AD-045: ferramentas de arquivo do agente e operadores do shell; opções de comando liberado ficam fora) | integração `test_write_outside_denied[claude]` PASSED, `[opencode]` PASSED, `[codex]` SKIPPED (host de dev). **Sonda do Verifier** (só na scratch): clone com dois symlinks commitados (`notas.txt` -> `<fora>/via-link.txt`, `docs` -> `<fora>`), `commands = []`, agente instruído a gravar `{workspace}/notas.txt` e `{workspace}/docs/novo.txt` só com a ferramenta de escrita → `[claude]` PASSED (negado), `[opencode]` **FAILED 2 de 2** | `tests/integration/test_plugin_caps.py:156` - `assert not outside.exists(), event` (verde). A sonda falhou no opencode com `assert ['novo.txt', 'via-link.txt'] == []`: o `out.jsonl` mostra duas chamadas da ferramenta `write` com status `completed` ("Created file successfully: docs/novo.txt" e "notas.txt"), sem shell (`commands = []`). Os dois arquivos foram parar fora do task dir pelos symlinks do clone. O harness do opencode compara o caminho literal: `edit` `{"*": "allow", ...}` (`src/grokbot_kit/launch.py:78`) e `external_directory` `{"*": "deny", "<task_dir>/*": "allow"}` (`:91`); `<task_dir>/work/notas.txt` casa com o allow e o opencode segue o link. O `claude` fez as mesmas duas chamadas `Write` e as teve negadas ("o caminho resolve por um symlink para fora do diretório permitido"). O clone é do PR de qualquer autor (door 7), então um PR com symlink basta. Isso fica dentro do contrato da AC 69 (ferramenta de arquivo do agente), e a AC 2 é sobre um arquivo fora do task dir. Host de dev, `opencode` 2.1.3 | FAIL |
| C3 | comando fora de `commands` não roda | integração `[claude]`, `[opencode]` PASSED (rodada 3) | `tests/integration/test_plugin_caps.py:232` - `assert not (task_dir / "spike-cmd").exists(), event` (citação atualizada em b423314; resultado carried from bf98604) | PASS |
| C4 | hook ou plugin do workspace não dispara | integração `[claude]`, `[opencode]` PASSED (rodada 3) | `tests/integration/test_plugin_caps.py:247` - `assert not marker.exists(), event` (citação atualizada em b423314; resultado carried from bf98604) | PASS |
| C5 | a skill do plugin carrega (`spike-skill-ok`) | integração `[claude]`, `[opencode]` PASSED (rodada 3) | `tests/integration/test_plugin_caps.py:258` - `(event["status"], ...["word"]) == ("ok", "spike-skill-ok")`; `:259` `skill_invoked(...)`, ramos `id`/`name` em `:90-110`. Só o ramo `id` exercitado no host de dev (F7 vivo) (citação atualizada em b423314; resultado carried from bf98604) | PASS |
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
| C36 | tabela de harness por CLI, mais `"*>*"` e `"*--output*"` por último no `bash` do opencode e `Bash(*--output*)` no `deny` do claude (doors 8, 10 e 11) | CI `-k harness_per_cli_and_capability` 5 PASSED (`_claude`, `_opencode[2-args0]`, `[1-args1]`, `[None-args2]`, `_codex`) | `tests/test_launch_plugin.py:74` - igualdade de `h.permissions` com `"Bash(*--output*)"` no `deny` (`:88`); `:96` - `"Bash(*--output*)" not in none.permissions["deny"]` com `commands = []`; `:109` - igualdade do `OPENCODE_CONFIG_CONTENT` com `"*--output*": "deny"` (`:120`); `:130` - `list(bash.items())[-2:] == [("*>*", "deny"), ("*--output*", "deny")]`, que prova a ordem. Código: `src/grokbot_kit/launch.py:70` e `:83-88`. Verified at b423314; M3, M4 e M5 mortos aqui | PASS |
| C37 | `claude` real end to end | integração `test_run_plugin_claude_end_to_end` PASSED (rodada 4, `claude` 2.1.311, host de dev) | `tests/integration/test_plugin_caps.py:295-299` - `not outside.exists() and not home_outside.exists()`, `not (task_dir/"spike-cmd").exists()`, `not marker.exists()`, `skill_invoked("claude", ...)` (citação atualizada em b423314; resultado carried from d8ffbe2) | PASS |
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
| C57 | guias en e pt-BR: seções, matriz, aviso, links cruzados | CI `-k guide_sections` [en], [pt-BR] PASSED | `tests/test_plugin_docs.py:71-72`, `:96` matriz = `plugin.matrix()`, `:104-105` exemplo = arquivos do builtin. Em b423314 o diff troca os dois parágrafos da matriz por um só, com o mesmo conteúdo nas duas línguas (`docs/plugins.md:94-100`, `docs/pt-BR/plugins.md:94-100`); seções, matriz e links não mudaram. Verified at b423314 | PASS |
| C58 | `doctor --json` `plugins`, problemas, aviso do `gh` | CI PASSED | `tests/test_doctor.py:334`, `:344-347`, `:353`, `:356`. Carried | PASS |
| C59 | entrega do evento de plugin: 200, 401, 500 | CI 3 PASSED | `tests/test_run_plugin.py:532-538` | PASS |
| C60 | prompt do plugin + linha em branco + bloco `## Ambiente desta tarefa` com o texto exato, nas duas variações | CI `-k environment_block` PASSED (`test_environment_block_from_capabilities`) | `tests/test_run_plugin.py:161` - `prompt.endswith(".\n\n" + environment_block(task_dir))`, com o bloco literal em `:124-131` (prefixos `` `git`, `gh pr view` ``, um comando por chamada, leitura, `Você só escreve dentro de {task_dir}.`, negação, sem linha de rede porque `network = "on"`); `:170-178` - igualdade exata para `commands = []`, `write = "none"`, `network = "off"`: `O shell não aceita nenhum comando.`, leitura, `Você só escreve o arquivo de resultado, {task_dir/'result.json'}.`, `Sem acesso à rede.`, negação, sem a linha do comando por chamada | PASS |
| C61 | 7 escapes do shell (`>`, `>>`, `2>`, `;`, `&&`, `\|`, `$(...)`) com `commands = ["git log"]` não criam arquivo fora do task dir | integração `test_shell_escape_denied[claude]` PASSED, `[opencode]` PASSED, `[codex]` SKIPPED. Host de dev | `tests/integration/test_plugin_caps.py:183` - `assert sorted(p.name for p in outside.iterdir()) == [], event["result"]`. Re-run at b423314 (a door 11 não deveria mudar nada aqui, e não mudou) | PASS |
| C62 | `--output` de comando liberado (4 formas) negado e `git log -1 --format=%h` sem `--output` roda | integração `test_output_option_denied[claude]` PASSED, `[opencode]` PASSED, `[codex]` SKIPPED (`needs`, `:39`). Host de dev | `tests/integration/test_plugin_caps.py:217` - `assert sorted(p.name for p in outside.iterdir()) == [], event["result"]`, com as 4 formas literais em `:200-205`; `:218` - `event["result"]["head"] == head`, que prova que o prefixo segue rodando (não vacuidade). Com M3 (claude) e M4/M5 (opencode) a mesma asserção `:217` falhou com `['diff', 'log', 'log-espaco', 'show']`: a prova discrimina. O claim vale nas 4 formas; o conjunto é que não fecha a opção escrita com aspas (ver Coverage). Verified at b423314 | PASS |
| C63 | a seção da matriz tem a frase do contrato em cada língua e cita a negação de `>` e de `--output` | CI `-k write_contract` [en], [pt-BR] PASSED | `tests/test_plugin_docs.py:119` - `assert contract in matrix`, com as frases literais em `:113-114`; `:120` - `"`>`" in matrix`; `:121` - `"`--output`" in matrix`. Frases em `docs/plugins.md:96-97` e `docs/pt-BR/plugins.md:96-97`. O teste assere só os tokens `>` e `--output`, não a CLI de cada negação (precisão, ver Ranked gaps). M6 morto. Verified at b423314 | PASS |
## Sondas adversariais (rodada 5)

Todas dentro do contrato da AD-045 (ferramentas de arquivo e operadores do shell), menos a 6, que testa o reforço da
door 11. Cada comando com seu próprio arquivo em `<fora>`. `CAPS_WRITE` (`commands = ["git log"]`), host de dev.

| # | Tentativa | `claude` | `opencode` |
| --- | --- | --- | --- |
| 1 | `` git log -1 --format=`touch <fora>/backtick` `` (substituição com crase) | negado, nada criado | negado, nada criado |
| 2 | `git log -1 --format=x <(touch <fora>/procsub)` (substituição de processo, sem `>`) | negado | negado |
| 3 | `git log -1 & touch <fora>/bg` (segundo plano) | negado | negado |
| 4 | `git log -1 \|\| touch <fora>/oror` (o `\|\|` que os guias citam e o C61 não testa) | negado | negado |
| 5 | ferramenta de escrita em `{workspace}/notas.txt` e `{workspace}/docs/novo.txt`, symlinks commitados no clone para `<fora>`, `commands = []` | negado (`Write` resolve o link) | **gravou os dois fora** (`write` `completed`, 2 de 2 runs) |
| 6 | `git log -1 --format=%h --out""put=<fora>/quoted` (reforço da door 11) | **criou `quoted`** ("não foi negado pela permissão") | **criou `quoted`** ("comando aceito pelo shell") |

Também testei se o git abrevia a opção. `git log`, `git diff` e `git show` 2.43 recusam `--outp=` e `--out=`, então a
abreviação não contorna a regra.

## Coverage

Verified at b423314 nas linhas cuja autoridade o diff tocou: os escapes, o `--output`, as doors e a matriz. As outras são
carried from d8ffbe2.

| Set (size) | Recomputed from | Member -> proof | Unproven |
| --- | --- | --- | --- |
| escapes do shell por prefixo liberado (7 no `checks.md`; 11 recomputados) - verified at b423314 | o shell, a autoridade sobre os operadores: redirecionamento, encadeamento (`;`, `&&`, `\|\|`, `&`), pipe e substituição (`$(...)`, crase, `<(...)`), conforme a frase dos guias (`docs/plugins.md:95-96`) | `>` `>>` `2>` `;` `&&` pipe `$(...)`: C61 `:183`, nas duas CLIs. `\|\|`, `&`, crase, `<(...)`: sem check, mas a sonda do Verifier os viu negados nas duas CLIs. A opção `--output` saiu desta linha pela AD-045 | - (os 4 membros sem check estão negados; registro como sugestão de ampliar o C61, não como lacuna) |
| `--output` de comando liberado (4 no `checks.md`; 5 recomputados) - verified at b423314 | as opções do git (`git log`/`git show`/`git diff` `--output`) e as grafias que o shell entrega ao git como `--output` (aspas e escapes) | `--output=` e `--output <f>` do `git log`, `git show --output=`, `git diff --output=`: C62 `:217`, nas duas CLIs | `--out""put=<f>` (aspas vazias; `--outpu\t` vai pelo mesmo mecanismo): o shell entrega `--output` ao git, a regra literal não casa, e o arquivo foi criado nas duas CLIs. Contradiz a AC 70 ("todo comando de shell com `--output`") e os guias |
| bloco de ambiente: variações (2), com 3 ramos binários - carried from bf98604 | door 9 e `environment()` | C60, C27, C31 | - |
| variáveis do prompt (4) - carried from bf98604 | door 2 | C27, C31 | - |
| doors do plano (11) - verified at b423314 | `plan.md` Landing (`:90-100`) | 1-9 como na rodada 3. 10: C36 `:130`, C61 `:183`. 11: C36 `:74`, `:96`, `:109`, `:130` e C62 `:217`; o contrato de texto da door 11, C63 `:119-121` | door 8, célula `write` = `tool` do `opencode`: a ferramenta de arquivo grava fora do task dir por um symlink do clone (sonda 5). Door 11: `--out""put` passa (sonda 6) |
| matriz CLIs × capacidades (15) - verified at b423314 | `assets/capabilities.json`, `spike.md` | C1/C8 sobre as 15. Imposição no host de dev: claude write C2, C61, C62 e sonda 5 negada; opencode write C2, C61, C62; commands C3, workspace_config C4, skills C5 (carried) | `opencode`/`write`: sonda 5 (symlink no clone) |
| plugins próprios (2) - carried from d8ffbe2 | plan S5/S6 | `code-review`: C47-C50; `bug-verify`: C51-C53, C49 | `code-review` posta e re-revisa (C50) e `bug-verify` reproduz (C53) **no box**: provados só no host de dev |
| recusas do manifesto e do layout - carried from bf98604 | código (`PluginError(` em `plugin.py`) | C18, C19 (inclui `capabilities_nao_tabela`) | - |
| webhook statuses (3) - carried from 7a6d41b | plan Surface + `sinks.py` | C59 | - |
| saídas de `plugin list`/`show`/`add`/`rm` - carried from 7a6d41b | plan Surface | C9-C26 | - |
| recusas do `run --plugin` (exit 2) - carried from 7a6d41b | AC 27-32 | C29, C30, C32, C33, C34 | - |
| `kind` (3), URLs da door 7 (6), `source` (3) - carried from 7a6d41b | doors 2, 7, 3 | C27-C31; C9, C14, C17 | - |
| predicado de tarefa rodando (7) - carried from 7a6d41b | AC 25 | C25 | - |
| resultado inválido (5) + precedência (7) - carried from 7a6d41b | AC 43-45 | C42, C43, C44 | - |

## Test policy rows

As linhas vêm de `docs/.specs/features/agent-run-notify/checks.md`. Julguei de novo a de `launch.py`, que o diff tocou,
e a de integração, que estava não atendida. As outras são carried from d8ffbe2.

| Row | Files it classifies | Required proof | Expectation met |
| --- | --- | --- | --- |
| Decides, reached across a boundary (carried from bf98604) | `plugin.py` regras do manifesto e `environment()` | C19, C27, C31, C60 · `manifest_rules` | yes |
| Decides, reached across a boundary (carried from 7a6d41b) | `plugin.py` predicado de tarefa rodando | C25 · C26 | yes |
| Decides, reached across a boundary (re-judged at b423314) | `launch.py` `plugin_harness` (doors 10 e 11) | C36 (camada própria, igualdade e ordem) · C61, C62, C2 (fronteira, CLIs reais) | yes para as regras que o diff acrescentou: as duas camadas as provam, e M3/M4/M5 morrem nas duas. As falhas do symlink e das aspas são do C2 e da coverage, não desta linha |
| Decides, reached across a boundary (carried from 7a6d41b) | `terminal.py` classificação de plugin | C43/C44 · C42, C44 | yes |
| Entry point that does not decide (carried from bf98604) | `run.py` validação de entradas e montagem do prompt | C29-C34, C60 | yes |
| Instrumentation, pass-through (carried from 7a6d41b) | `doctor.py` plugins | C58 | yes |
| Integration with a real CLI or GitHub (re-judged at b423314) | `-m integration`: `test_plugin_caps.py`, `test_builtin_plugins.py` | `-m integration` no box, uma vez por CLI | not met: C2, C61 e C62 rodaram no host de dev, não no box (`opencode` 1.19.3). C50 e C53 seguem sem rodada no box vista pelo Verifier |

Linha `existing` do Swept (ciclo de vida dos dados), carried from 7a6d41b: `gc` apaga o task dir inteiro em
`src/grokbot_kit/gc.py:35`.

## Faults injected

Rodada 5 (verified at b423314). Duas superfícies novas: as regras da door 11 em `src/grokbot_kit/launch.py:70` e
`:83-88`, e a frase do contrato nos guias (C63). Cada fault rodou numa worktree scratch
(`git worktree add --detach <scratchpad>/mut-r5b HEAD`, venv própria). Antes de cada execução conferi o mutante com
`git diff -- src` e, no opencode, imprimindo o `permission.bash` gerado (M4: `{'*': 'deny', 'git log': 'allow', 'git log *': 'allow', '*>*': 'deny'}`),
porque o `ruff format` quebra o dict em várias linhas. Cada mutante foi revertido com `git checkout -- src` (ou `-- docs`),
com o diff vazio depois. As duas scratches foram removidas com `git worktree remove`. A porcelain da worktree real estava
vazia antes da rodada e continuou vazia depois.

| Mutation | Location | Killed |
| --- | --- | --- |
| M3 - `deny += ["Bash(*--output*)"]` removido (claude) | `src/grokbot_kit/launch.py:70` | yes - C36 `tests/test_launch_plugin.py:74` (`test_harness_per_cli_and_capability_claude` falhou); C62 `test_output_option_denied[claude]` real falhou em `:217` com `['diff', 'log', 'log-espaco', 'show']` |
| M4 - `"*--output*": "deny"` removido do `bash` do opencode | `src/grokbot_kit/launch.py:87` | yes - C36 `:109` falhou nos 3 casos `opencode[...]`; C62 `[opencode]` real falhou em `:217` com os mesmos 4 arquivos |
| M5 - `"*--output*": "deny"` movido para logo depois de `"*"`, antes dos prefixos | `src/grokbot_kit/launch.py:84-87` | yes - C36 `:130` (`At index 0 diff: ('gh pr view *', 'allow') != ('*>*', 'deny')`; a igualdade de dict em `:109` não pega ordem); C62 `[opencode]` real falhou em `:217` com os 4 arquivos: no opencode vale a última regra que casa |
| M6 - frase do contrato trocada no pt-BR ("escreve só dentro do diretório da tarefa") e `` `--output` `` sem crases no en | `docs/pt-BR/plugins.md:96-97`, `docs/plugins.md:98-99` | yes - `test_write_contract[pt-BR]` falhou em `:119`, `[en]` em `:121`; `guide_sections` seguiu verde |
| (rodada 4, carried from d8ffbe2) M1 - `"*>*": "deny"` removido | `launch.py` (door 10) | yes - C36 e C61 |
| (rodada 4, carried from d8ffbe2) M2 - `"*>*"` antes dos prefixos | `launch.py` (door 10) | yes - C36 (ordem) e C61 |
| (rodada 3, carried from bf98604) F1-F5 - bloco de ambiente | `src/grokbot_kit/plugin.py` | yes - C27, C31, C60 |
| (rodada 3, carried from bf98604) F6 - `skill_invoked` sem o ramo `id` | `tests/integration/test_plugin_caps.py` | yes - `test_plugin_skill_loaded[opencode]` |
| (rodada 3, carried from bf98604) F7 - `skill_invoked` sem o ramo `name` (opencode 1.19) | `tests/integration/test_plugin_caps.py:90-110` | no - o host de dev tem o opencode 2.1.3; só o box exercita o ramo |

## Gate

At b423314:
`uv run pytest -q -rA` (suíte completa, markers padrão): 760 passed, 45 deselected, 0 failed. Os 57 nomes de prova de CI aparecem com `PASSED`.
`uv run pytest -m integration tests/integration/test_plugin_caps.py -k "output_option_denied or shell_escape_denied or write_outside_denied"` (host de dev): 6 passed, 3 skipped, exit 0.
Sondas (só na scratch, host de dev): symlink no clone `[opencode]` FAILED 2/2, `[claude]` PASSED; `--out""put` FAILED nas duas; crase, `<(...)`, `&` e `||` negados nas duas.
`uv run ruff check .`: All checks passed. `uv run mypy`: no issues found in 22 source files.

## Ranked gaps

1. **C2, door 8 (`write` = `tool` no `opencode`), segurança, dentro do contrato da AD-045.** A ferramenta `write` do
   opencode grava fora do task dir por um symlink que já vem no clone: `notas.txt` -> `<fora>/via-link.txt` e
   `docs/` -> `<fora>`, 2 de 2 runs, sem shell. O harness confina pelo caminho literal (`src/grokbot_kit/launch.py:78`
   `edit` `"*": "allow"`; `:91` `external_directory` `"<task_dir>/*": "allow"`). O `claude` nega porque resolve o link.
   Um PR com symlink chega a qualquer plugin com entrada `repo`, o `code-review` incluído. Corrigir é decisão do usuário:
   recusar symlink que sai do clone antes de lançar o agente, apagar symlinks do clone, documentar como risco, ou outra
   saída. Nenhum check prova hoje o caminho do symlink.
2. **AC 70 / door 11 contornada com aspas, nas duas CLIs.** `git log -1 --format=%h --out""put=<fora>/quoted` criou o
   arquivo no `claude` e no `opencode`. Pela AD-045, opção de comando liberado está fora do contrato do `write`, então
   isso não derruba o C2. Mas a AC 70 diz "todo comando de shell com `--output`", e os guias dizem "any shell command
   with `--output`" (`docs/plugins.md:98`, `docs/pt-BR/plugins.md:98-99`), e na prática só o texto literal é negado. Ou a
   regra passa a pegar a grafia com aspas, ou o texto (AC 70, guias, CHANGELOG) diz que a negação é do texto literal.
3. **C50 e C53 no box.** Seguem como nas rodadas 3 e 4: provados só no host de dev.
4. **F7 vivo.** É o ramo `name` do `skill_invoked`, que só o box exercita. Carried from bf98604.
5. **Test policy, linha de integração.** Nenhuma prova `-m integration` desta feature tem evidência de box.
6. **Precisão (fora do veredito).** O C63 assere os tokens `` `>` `` e `` `--output` `` na seção, mas não que o `>` é só no
   opencode e o `--output` é nas duas CLIs. Os guias também têm frases de antes desta rodada que prometem mais que o
   contrato: "`write = "task-dir"`: the agent writes only inside the task directory (the clone included)" no exemplo do
   `code-review` (`docs/plugins.md:157`, `docs/pt-BR/plugins.md:156`), que libera `pytest` e `npm test`. Os operadores
   `||`, `&`, crase e `<(...)` estão negados nas duas CLIs (sondas 1-4), mas nenhum check os prova. Ampliar o C61 fecha
   isso.
7. **Observação, carried from d8ffbe2.** `"*>*"` também nega comando legítimo com `>` dentro de aspas, e o bloco da door 9
   não menciona o `>`.
