# plugins verification

**Verdict**: FAIL
**Profile**: standard
**Diff range**: f69d5e3..4ac3c27 (fix da rodada 5 sob re-verificação; feature desde 7f17f2a)
**Round**: 6 - scoped
**Verifier**: independent sub-agent (author != verifier); não escreveu o código nem as rodadas anteriores

A door 12 fecha o caso da rodada 5. Um clone com symlink que sai de `work/` encerra a tarefa antes da CLI
(`src/grokbot_kit/run.py:303`, `:306-320`), e as bordas que testei direto na função se comportam bem: link pendente
absoluto ou relativo, cadeia, `/proc/self/cwd`, `..` e `../work2`. O C64 prova o claim, e o M7 e o M8 morreram nele. A
AC 70 reescrita e a frase da grafia estão nos dois guias e no CHANGELOG (C63, M12 morto). A rodada falha mesmo assim, por
quatro motivos:

1. **C2 falha no opencode por outro caminho da ferramenta de arquivo.** Num plugin sem entrada `repo`, o diretório de
   trabalho do agente é o `--cwd` (ou o cwd de quem chamou o `run`, `run.py:132`, `:257`), e ele fica fora do task dir.
   O opencode 2.1.3 só aplica `external_directory` (`launch.py:91`) a caminhos fora do projeto, e o projeto é o cwd. O
   `edit` é `"*": "allow"` (`launch.py:78`). Com `commands = []`, sem shell, a ferramenta `write` gravou
   `<cwd>/fora-cwd.txt` e `fora-rel.txt` nos 2 runs. O `claude` negou as duas escritas. Isso contradiz
   `docs/plugins.md:67` ("the agent writes only in the task directory") e o item `write` dos dois guias. O defeito vem de
   antes deste diff (`launch.py` não mudou), e a door 12 não o cobre porque não há clone. O briefing perguntou se o `--cwd`
   importa para o contrato. Importa: a AC 2 trata de qualquer arquivo fora do task dir, e a AC 69 põe as ferramentas de
   arquivo dentro do contrato. Os builtins têm entrada `repo` e não são afetados. Plugins de terceiros com só `text` ou
   `file` são.
2. **A forma literal da door 12 tem membros sem prova.** `plan.md:101` fixa "até 5 caminhos relativos, ordenados, e
   `(+N more)`". O C64 usa 2 links, um diretório e um arquivo, que o `os.walk` já entrega em ordem. Por isso sobreviveram
   o M10 (sem `found.sort()`) e o M11 (corte em 6, sem `(+N more)`). O M9 (sem o filtro de `.git`) também sobreviveu, mas é
   equivalente: um clone feito por `gh`/`git` não põe symlink em `.git/`.
3. **C50 e C53 seguem sem prova no box.** O diff não toca neles. Carried from f69d5e3.
4. **F7 segue vivo.** É o ramo `name` (opencode 1.19) do `skill_invoked`, que só o box exercita. Carried from bf98604.

Onde rodou cada prova. As provas de CI rodaram em `HEAD` = `4ac3c27` no host de dev. As provas `-m integration` (C2,
C61, C62) também rodaram no **host de dev, não no box**, com `claude` 2.1.312 (`sonnet`) e `opencode` 2.1.3
(`opencode/glm-5.3-flash-free`). O opencode bateu no limite gratuito às 23:05 UTC. Esperei o limite voltar e rodei as
provas e as sondas do opencode às 00:01 UTC, sem trocar para modelo pago.

Escopo. O diff `f69d5e3..4ac3c27` acrescenta `_links_outside` em `src/grokbot_kit/run.py:303-320` (door 12) e o C64
(`tests/test_run_plugin.py:326-348`). Emenda o C63 (`tests/test_plugin_docs.py:108-130`), o `plan.md` (door 12 em
`:101`, AC 70 e 71), o `checks.md` (C63, C64, Coverage), o `STATE.md` (AD-046), os dois guias e o CHANGELOG.
Re-verifiquei C2, C35, C57, C63 e C64, além das linhas de Coverage e de `Test policy` que o diff toca ou que estavam
abertas. O resto vem de f69d5e3.

## Binding sources

Carried from 7a6d41b. O passo 1 só roda no perfil `ui`, e o diff não mexe numa interface com tela.

| Source | Opened | Contradiction | Uncovered |
| --- | --- | --- | --- |
| `docs/.specs/features/plugins/design.md` (binding) | yes - local file (round 1) | none | - |

Rodada 6 (verified at 4ac3c27): li a door 12 (`plan.md:101`), as AC 70 e 71 e a AD-046 (`docs/.specs/STATE.md:52`).
Comparei com o código (`run.py:303-320`, `:396-400`), com o C63 e o C64, com os guias (`docs/plugins.md:55-56`,
`:100-101`, `:159`; `docs/pt-BR/plugins.md:55-56`, `:100-101`, `:158`) e com o CHANGELOG (`:18-22`). Mensagem, momento
(depois do checkout, antes da CLI), desfecho e "todas as CLIs" batem. O código cumpre "até 5", "ordenados" e
`(+N more)` (`run.py:318-320`), mas nenhum teste prova isso (motivo 2). O texto do guia `docs/plugins.md:67` promete mais
do que o opencode cumpre num plugin sem `repo` (motivo 1).

## Checks

Proofs re-run at 4ac3c27. Os resultados de C2, C35, C57, C63 e C64 foram verificados em 4ac3c27, e as citações de
`tests/test_run_plugin.py` e `tests/test_plugin_docs.py` foram atualizadas onde o diff as moveu. As demais linhas vêm de
f69d5e3, com as provas de CI re-rodadas e verdes em 4ac3c27. C3, C4, C5, C37, C49, C50 e C53 (integração) não foram
re-rodados, porque o diff não toca nos caminhos deles.

Rodada de CI: `uv run pytest -q -rA` (suíte completa) saiu com **761 passed**, 45 deselected e 0 failed. Cada um dos 58
nomes `-k` de prova de CI do `checks.md` (os 57 da rodada 5 e `symlink_outside_clone`) teve pelo menos uma linha `PASSED`
na saída.
Integração (worktree real, host de dev): `uv run pytest -m integration tests/integration/test_plugin_caps.py -k "<cli> and (output_option_denied or shell_escape_denied or write_outside_denied)"`. `claude`: 3 passed. `opencode` e `codex`: 3 passed, 3 skipped (codex, `needs` em `:39`).
Sondas (worktree scratch, com o código de `HEAD` e um arquivo só da scratch, `test_probe_r6.py`, que usa `spike_plugin`, `run_plugin` e `needs` do `test_plugin_caps.py`): `test_probe_dotdot_and_tilde` PASSED nas duas CLIs. `test_probe_cwd_write` PASSED no `[claude]` e FAILED no `[opencode]` nos 2 runs. Host de dev.

| Check | Claim | Proof run | Evidence | Result |
| --- | --- | --- | --- | --- |
| C1 | `spike.md` tem 15 células com valor, versão, comando e saída | CI `-k matrix_complete` PASSED | `tests/test_plugin_spike.py:45` - `sorted(cells) == sorted(expected)`; `:47-50`. Carried from 7a6d41b (arquivo intocado) | PASS |
| C2 | escrita fora do task dir negada em cada CLI com `write` suportado (AC 2, com o escopo da AC 69 / AD-045) | integração `test_write_outside_denied[claude]` PASSED, `[opencode]` PASSED, `[codex]` SKIPPED (`needs`, `:39`), host de dev, em 4ac3c27. **Sondas do Verifier** (só na scratch): `..` e `~` pela ferramenta de escrita, negados nas duas CLIs; escrita no diretório de trabalho de um plugin sem entrada `repo` (`--cwd`), `[claude]` negada e `[opencode]` **gravou 2 de 2 runs** | `tests/integration/test_plugin_caps.py:156` - `assert not outside.exists(), event` (verde). O caso da rodada 5 (symlink commitado no clone) não chega mais ao agente: `_clone` devolve `_links_outside(workspace)` (`src/grokbot_kit/run.py:303`) e o `run` encerra antes de lançar a CLI (`run.py:397-400`); provado pelo C64. Mas a sonda `test_probe_cwd_write[opencode]` falhou com `assert ['fora-cwd.txt', 'fora-rel.txt'] == []`: num plugin sem entrada `repo`, o cwd do agente é o `--cwd` (ou o cwd de quem chamou), fora do task dir (`run.py:132`, `:257`). O opencode só aplica `external_directory` (`src/grokbot_kit/launch.py:91`) a caminho fora do projeto, e o projeto é o cwd; o `edit` é `"*": "allow"` (`launch.py:78`). A ferramenta `write` gravou `<cwd>/fora-cwd.txt` e `fora-rel.txt` com status ok, sem shell (`commands = []`). Contradiz `docs/plugins.md:67` ("the agent writes only in the task directory") e `:159`. O `claude` negou as duas ("modo don't ask"). Defeito anterior a este diff (`launch.py` intocado), achado agora. Host de dev, `opencode` 2.1.3 | FAIL |
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
| C35 | falha de clone vira evento `agent_error` | CI `-k clone_failure_event` PASSED em 4ac3c27 | `tests/test_run_plugin.py:317` - `not kit.record.exists()`; `:319` - `outcome(event) == ("error","failed","agent_error")`; `:320` - `"Could not resolve to a Repository" in event["summary"]`. O diff trocou o `return None` final de `_clone` por `return _links_outside(workspace)` (`src/grokbot_kit/run.py:303`); o caminho de falha do `gh` (`:300-302`) não mudou. Verified at 4ac3c27 | PASS |
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
| C57 | guias en e pt-BR: seções, matriz, aviso, links cruzados | CI `-k guide_sections` [en], [pt-BR] PASSED em 4ac3c27 | `tests/test_plugin_docs.py:71-72`, `:96` matriz = `plugin.matrix()`, `:104-105` exemplo = arquivos do builtin. O diff acrescenta a frase do symlink nas entradas (`docs/plugins.md:55-56`, `docs/pt-BR/plugins.md:55-56`), a frase do literal na matriz (`:100-101` nas duas) e reescreve o item `write` do exemplo (`docs/plugins.md:159`, `docs/pt-BR/plugins.md:158`), igual nas duas línguas. Seções, matriz e links não mudaram. Verified at 4ac3c27 | PASS |
| C58 | `doctor --json` `plugins`, problemas, aviso do `gh` | CI PASSED | `tests/test_doctor.py:334`, `:344-347`, `:353`, `:356`. Carried | PASS |
| C59 | entrega do evento de plugin: 200, 401, 500 | CI 3 PASSED | `tests/test_run_plugin.py:532-538` | PASS |
| C60 | prompt do plugin + linha em branco + bloco `## Ambiente desta tarefa` com o texto exato, nas duas variações | CI `-k environment_block` PASSED (`test_environment_block_from_capabilities`) | `tests/test_run_plugin.py:161` - `prompt.endswith(".\n\n" + environment_block(task_dir))`, com o bloco literal em `:124-131` (prefixos `` `git`, `gh pr view` ``, um comando por chamada, leitura, `Você só escreve dentro de {task_dir}.`, negação, sem linha de rede porque `network = "on"`); `:170-178` - igualdade exata para `commands = []`, `write = "none"`, `network = "off"`: `O shell não aceita nenhum comando.`, leitura, `Você só escreve o arquivo de resultado, {task_dir/'result.json'}.`, `Sem acesso à rede.`, negação, sem a linha do comando por chamada | PASS |
| C61 | 7 escapes do shell (`>`, `>>`, `2>`, `;`, `&&`, `\|`, `$(...)`) com `commands = ["git log"]` não criam arquivo fora do task dir | integração `test_shell_escape_denied[claude]` PASSED, `[opencode]` PASSED, `[codex]` SKIPPED. Host de dev | `tests/integration/test_plugin_caps.py:183` - `assert sorted(p.name for p in outside.iterdir()) == [], event["result"]`. Re-run at b423314 (a door 11 não deveria mudar nada aqui, e não mudou) | PASS |
| C62 | `--output` de comando liberado (4 formas) negado e `git log -1 --format=%h` sem `--output` roda | integração `test_output_option_denied[claude]` PASSED, `[opencode]` PASSED, `[codex]` SKIPPED (`needs`, `:39`). Host de dev | `tests/integration/test_plugin_caps.py:217` - `assert sorted(p.name for p in outside.iterdir()) == [], event["result"]`, com as 4 formas literais em `:200-205`; `:218` - `event["result"]["head"] == head`, que prova que o prefixo segue rodando (não vacuidade). Com M3 (claude) e M4/M5 (opencode) a mesma asserção `:217` falhou com `['diff', 'log', 'log-espaco', 'show']`: a prova discrimina. O claim vale nas 4 formas; o conjunto é que não fecha a opção escrita com aspas (ver Coverage). Verified at b423314 | PASS |
| C63 | a seção da matriz tem a frase do contrato, a da grafia (`Another spelling, such as quotes, gets around it.` / `Outra grafia, como aspas, contorna a regra.`) e cita `>` e `--output` (AC 69, AC 70 reescrita) | CI `-k write_contract` [en], [pt-BR] PASSED em 4ac3c27 | `tests/test_plugin_docs.py:127` - `assert contract in matrix`; `:128` - `assert spelling in matrix`, com as frases literais em `:114-120`; `:129` `"`>`" in matrix`; `:130` `"`--output`" in matrix`. Frases em `docs/plugins.md:100-101`, `docs/pt-BR/plugins.md:100-101`; CHANGELOG `:18-19`. M12 morto. Precisão: a frase en ficou "Both rules match the literal text: Another spelling ... gets around it" (maiúscula depois de dois-pontos, `it` para duas regras), moldada à string do teste; o CHANGELOG diz `them`. Verified at 4ac3c27 | PASS |
| C64 | clone com `fora.txt` -> `/etc/hostname` e `docs` -> `..` não lança a CLI e entrega `error`/`failed`/`agent_error` com `summary` exato; só com o interno `leia.txt` -> `README.md`, lança (AC 71, door 12) | CI `-k symlink_outside_clone` PASSED em 4ac3c27 | `tests/test_run_plugin.py:333-334` - `returncode == 0` e `kit.record.exists()` com o link interno; `:343` `returncode == 1`; `:344` `assert not kit.record.exists()`; `:347` `outcome(event) == ("error", "failed", "agent_error")`; `:348` `event["summary"] == "the clone has symbolic links that point outside it: docs, fora.txt"`. Código: `src/grokbot_kit/run.py:306-320`. M7 e M8 mortos aqui. O claim vale como escrito; a forma literal da door 12 (`plan.md:101`) pede ainda "até 5 caminhos ... ordenados, e `(+N more)`", e nada prova isso (M10 e M11 sobreviveram, ver Coverage) | PASS |

## Sondas adversariais (rodada 6)

Todas dentro do contrato da AD-045, ferramentas de arquivo do agente. Host de dev.

| # | Tentativa | Resultado |
| --- | --- | --- |
| 1 | `_links_outside` direto (CI venv): link pendente absoluto (`/tmp/nao-existe/novo.txt`) e relativo (`../../nao-existe/novo.txt`) | recusados: `realpath` não estrito resolve o alvo que ainda não existe, então um alvo criado depois não escapa |
| 2 | cadeia `a -> b -> /etc`; `a -> /proc/self/cwd`; `a -> ../work2/x` (armadilha de prefixo); `a -> ..`; `a -> ../result.json` | recusados; `is_relative_to` compara componentes, não prefixo de texto |
| 3 | `a -> .`, `sub/a -> ../README.md`, `g -> .git`, laço `a <-> b`, `a -> a` | aceitos, sem saída: alvo interno, ou laço que dá `ELOOP` na escrita |
| 4 | link fora dentro de `sub/.git/` | recusado: o filtro de `.git` é só no topo. Um `.git` aninhado não entra num commit (o git recusa o caminho) |
| 5 | link fora em `.git/` do topo | ignorado pelo filtro; um clone por `gh`/`git` não cria symlink ali (M9 equivalente) |
| 6 | link fora dentro de um diretório sem permissão de leitura | ignorado: o `os.walk` engole o erro (`onerror=None`). O checkout do git não cria diretório sem leitura (o git só guarda 644/755 de arquivo), então não é alcançável por um PR. Registro como robustez |
| 7 | diretório interno com link fora dentro (`real/x -> /etc`, `alias -> real`) | recusado (`real/x`); o `os.walk` não segue `alias` e vê o link na origem |
| 8 | symlink criado depois do clone pelo `gh pr checkout` | coberto: a varredura roda depois do último passo (`run.py:303`), e o `gh pr checkout` é o último |
| 9 | hard link; diferença de caixa | não se aplica: o git não guarda hard link, e o caminho no Linux distingue caixa |
| 10 | symlink criado durante a tarefa por um comando liberado (`git checkout <commit antigo> -- link`, `pytest` rodando código do repo) e seguido depois pela ferramenta de arquivo | não rodei. Dos builtins, só o `pytest`/`npm test`/`go test`/`cargo test` do `bug-verify` alcança isso, e esses rodam o código do repo, que pela AD-045 escreve onde quiser. Os prefixos `git log`/`git diff`/`git show`/`git blame` não criam symlink, e o `--output` é negado. Um plugin com prefixo `git` amplo já fica fora do contrato. Nada novo |
| 11 | ferramenta de escrita em `{task_dir}/../fora-dotdot.txt`, `{task_dir}/sub/../../fora-dotdot2.txt`, `~/fora-til.txt` | `claude` negou os três ("resolveu o caminho ... fora dos diretórios permitidos"); `opencode` negou os três (`Permission denied: external_directory`) |
| 12 | plugin sem `repo` (`--cwd` = `<tmp>/work`): ferramenta de escrita em `{workspace}/fora-cwd.txt` e `fora-rel.txt` | `claude` negou os dois (modo don't ask). **`opencode` gravou os dois, 2 de 2 runs** (motivo 1) |

## Coverage

Verified at 4ac3c27 nas linhas cuja autoridade o diff tocou: symlinks no clone, doors, matriz e `--output`. As outras
são carried from f69d5e3.

| Set (size) | Recomputed from | Member -> proof | Unproven |
| --- | --- | --- | --- |
| symlinks no clone (3 no `checks.md`; 3 recomputados) - verified at 4ac3c27 | o que o git guarda num symlink (alvo absoluto ou relativo, existente ou não) e a door 12 | alvo absoluto fora: C64 `:348` (`fora.txt`); relativo fora: C64 (`docs` -> `..`); interno: C64 `:333-334`. Pendente e cadeia: só a sonda 1-2 | - (pendente e cadeia saem do mesmo `realpath`) |
| forma do `summary` da door 12 (4) - verified at 4ac3c27 | `plan.md:101`: prefixo e caminhos relativos, ordenados, até 5, `(+N more)` | prefixo e caminhos relativos: C64 `:348` | ordenação (M10 sobreviveu: com 1 diretório e 1 arquivo, o `os.walk` já entrega em ordem); corte em 5 e `(+N more)` (M11 sobreviveu: o C64 tem 2 links) |
| `--output` de comando liberado (4 no `checks.md`) - verified at 4ac3c27 | AC 70 reescrita: o texto literal `--output` | as 4 formas literais: C62 `:217`, nas duas CLIs (re-run em 4ac3c27). A grafia com aspas saiu do conjunto pela AD-046, e os guias e o CHANGELOG dizem que ela contorna (C63 `:128`) | - |
| escapes do shell por prefixo liberado (7; 11 recomputados) - carried from f69d5e3 | o shell | `>` `>>` `2>` `;` `&&` pipe `$(...)`: C61 (re-run em 4ac3c27, verde nas duas CLIs). `\|\|`, `&`, crase, `<(...)`: negados nas sondas da rodada 5, sem check | - |
| diretório de trabalho do agente (2) - verified at 4ac3c27 | `run.py:257`: o clone em `<task_dir>/work` (entrada `repo`) ou o cwd (`--cwd`, sem `repo`) | clone: C2 e C64. cwd: o C2 escreve fora do cwd e do task dir, e não testa o cwd | cwd fora do task dir: o opencode grava nele pela ferramenta `write` (sonda 12) |
| doors do plano (12) - verified at 4ac3c27 | `plan.md` Landing (`:90-101`) | 1-11 como na rodada 5. 12: C64 `:343-348` | door 12: ordem, corte e `(+N more)` (linha acima). Door 8, célula `write` = `tool` do `opencode`: escrita no cwd de plugin sem `repo` (sonda 12) |
| matriz CLIs × capacidades (15) - verified at 4ac3c27 | `assets/capabilities.json`, `spike.md` | C1/C8 sobre as 15. Imposição no host de dev: claude write C2, C61, C62 e sondas 11-12 negadas; opencode write C2, C61, C62 e sonda 11; commands C3, workspace_config C4, skills C5 (carried) | `opencode`/`write`: sonda 12 |
| bloco de ambiente: variações (2), com 3 ramos binários - carried from bf98604 | door 9 e `environment()` | C60, C27, C31 | - |
| variáveis do prompt (4) - carried from bf98604 | door 2 | C27, C31 | - |
| plugins próprios (2) - carried from f69d5e3 | plan S5/S6 | `code-review`: C47-C50; `bug-verify`: C51-C53, C49 | `code-review` posta e re-revisa (C50) e `bug-verify` reproduz (C53) **no box**: provados só no host de dev |
| recusas do manifesto e do layout - carried from bf98604 | código (`PluginError(` em `plugin.py`) | C18, C19 (inclui `capabilities_nao_tabela`) | - |
| webhook statuses (3) - carried from 7a6d41b | plan Surface + `sinks.py` | C59 | - |
| saídas de `plugin list`/`show`/`add`/`rm` - carried from 7a6d41b | plan Surface | C9-C26 | - |
| recusas do `run --plugin` (exit 2) - carried from 7a6d41b | AC 27-32 | C29, C30, C32, C33, C34 | - |
| `kind` (3), URLs da door 7 (6), `source` (3) - carried from 7a6d41b | doors 2, 7, 3 | C27-C31; C9, C14, C17 | - |
| predicado de tarefa rodando (7) - carried from 7a6d41b | AC 25 | C25 | - |
| resultado inválido (5) + precedência (7) - carried from 7a6d41b | AC 43-45 | C42, C43, C44 | - |

## Test policy rows

As linhas vêm de `docs/.specs/features/agent-run-notify/checks.md`. Julguei de novo a de `run.py`, que o diff tocou, e
a de integração, que não estava atendida. As outras são carried from f69d5e3.

| Row | Files it classifies | Required proof | Expectation met |
| --- | --- | --- | --- |
| Decides, reached across a boundary (carried from bf98604) | `plugin.py` regras do manifesto e `environment()` | C19, C27, C31, C60 · `manifest_rules` | yes |
| Decides, reached across a boundary (carried from 7a6d41b) | `plugin.py` predicado de tarefa rodando | C25 · C26 | yes |
| Decides, reached across a boundary (carried from f69d5e3) | `launch.py` `plugin_harness` (doors 10 e 11) | C36 · C61, C62, C2 | yes para as regras das doors 10 e 11. A escrita no cwd (sonda 12) é falha do C2 e da coverage |
| Decides, reached across a boundary (re-judged at 4ac3c27) | `run.py` `_links_outside` (door 12) | C64, na fronteira (subprocesso `grokbot-kit run`, `gh` falso, CLI falsa) | not met: a decisão de recusar está provada (M7 e M8 mortos), mas a forma do `summary` que a door fixa (ordem, corte, `(+N more)`) não está (M10 e M11 vivos) |
| Decides, reached across a boundary (carried from 7a6d41b) | `terminal.py` classificação de plugin | C43/C44 · C42, C44 | yes |
| Entry point that does not decide (re-judged at 4ac3c27) | `run.py` validação de entradas e montagem do prompt | C29-C35, C60 | yes: o C35 segue verde com o `return` novo de `_clone` |
| Instrumentation, pass-through (carried from 7a6d41b) | `doctor.py` plugins | C58 | yes |
| Integration with a real CLI or GitHub (re-judged at 4ac3c27) | `-m integration`: `test_plugin_caps.py`, `test_builtin_plugins.py` | `-m integration` no box, uma vez por CLI | not met: C2, C61 e C62 rodaram no host de dev, não no box. C50 e C53 seguem sem rodada no box vista pelo Verifier |

Linha `existing` do Swept (ciclo de vida dos dados), carried from 7a6d41b: `gc` apaga o task dir inteiro em
`src/grokbot_kit/gc.py:35`.

## Faults injected

Rodada 6 (verified at 4ac3c27). Duas superfícies novas: `_links_outside` (`src/grokbot_kit/run.py:306-320`) e a frase
da grafia nos guias (C63). Cada fault rodou numa worktree scratch (`git worktree add --detach <scratchpad>/mut-r6 HEAD`
e, para o M12, `mut-r6b`, cada uma com venv própria). Antes de cada execução conferi o mutante com
`git diff -U0 -- src` e, no M12, com um `assert` de que o texto original estava no arquivo. Reverti cada um com
`git checkout -- src` (ou `-- docs`) e conferi o diff vazio. As duas scratches foram removidas com `git worktree remove`.
A porcelain da worktree real estava vazia antes e continuou vazia depois. Narrowest proof: `uv run pytest
tests/test_run_plugin.py tests/test_plugin.py` (81 testes) e, no M12, `tests/test_plugin_docs.py`.

| Mutation | Location | Killed |
| --- | --- | --- |
| M7 - `_links_outside` devolve sempre `None` (`return None` no início) | `src/grokbot_kit/run.py:308` | yes - C64 `test_symlink_outside_clone` falhou (1 failed, 80 passed) |
| M8 - sem a checagem do `realpath`: `if path.is_symlink():` | `src/grokbot_kit/run.py:314` | yes - C64 falhou na metade do link interno (`:333`, `returncode == 0`) |
| M9 - sem o filtro de `.git` (`dirnames[:] = ...` vira `pass`) | `src/grokbot_kit/run.py:311` | no - 81 passed. Equivalente para entrada alcançável: um clone por `gh`/`git` não tem symlink em `.git/` (sonda 5) |
| M10 - sem `found.sort()` | `src/grokbot_kit/run.py:318` | no - 81 passed. O `os.walk` entrega `docs` (diretório) antes de `fora.txt` (arquivo), então o C64 não distingue |
| M11 - corte em 6 e `(+N more)` só acima de 99 | `src/grokbot_kit/run.py:319-320` | no - 81 passed. O C64 tem 2 links |
| M12 - frase da grafia trocada ("Other spellings, such as" / "Grafias diferentes, como aspas,") | `docs/plugins.md:100`, `docs/pt-BR/plugins.md:100` | yes - `test_write_contract[en]` e `[pt-BR]` falharam em `:128`; `guide_sections` seguiu verde |
| (rodada 5, carried from f69d5e3) M3-M6 - door 11 e frase do contrato | `launch.py:70`, `:83-88`; guias | yes - C36, C62, C63 |
| (rodada 4, carried from d8ffbe2) M1, M2 - door 10 | `launch.py` | yes - C36 e C61 |
| (rodada 3, carried from bf98604) F1-F6 | `plugin.py`, `test_plugin_caps.py` | yes |
| (rodada 3, carried from bf98604) F7 - `skill_invoked` sem o ramo `name` (opencode 1.19) | `tests/integration/test_plugin_caps.py:90-110` | no - o host de dev tem o opencode 2.1.3; só o box exercita o ramo |

## Gate

At 4ac3c27:
`uv run pytest -q -rA` (suíte completa, markers padrão): 761 passed, 45 deselected, 0 failed. Os 58 nomes de prova de CI aparecem com `PASSED`.
`uv run pytest -m integration tests/integration/test_plugin_caps.py -k "... and (output_option_denied or shell_escape_denied or write_outside_denied)"` (host de dev): claude 3 passed; opencode 3 passed e codex 3 skipped. Exit 0 nas duas.
Sondas (só na scratch, host de dev): `..`/`~` negados nas duas CLIs; escrita no cwd de plugin sem `repo` negada no `claude` e FAILED no `[opencode]`, 2 de 2.
`uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 96 files already formatted. `uv run mypy`: no issues found in 22 source files.

## Ranked gaps

1. **C2, door 8 (`write` = `tool` no `opencode`), segurança, dentro do contrato da AD-045.** Num plugin sem entrada
   `repo`, a ferramenta `write` do opencode grava no diretório de trabalho do agente, o `--cwd` ou o cwd de quem chamou o
   `run`, que fica fora do task dir. Foram 2 de 2 runs, sem shell. O `external_directory` (`launch.py:91`) não vale dentro
   do projeto, e o `edit` é `"*": "allow"` (`:78`). Contradiz `docs/plugins.md:67` e `:159` (e os equivalentes em pt-BR).
   O `claude` nega. Os builtins não são afetados, porque têm `repo`. Corrigir é decisão do usuário: por exemplo, o `edit`
   do opencode com `"*": "deny"` e allow só em `<task_dir>/*` (a mesma forma do ramo `write = "none"`), rodar o agente
   do opencode com cwd dentro do task dir, ou dizer nos docs que no opencode um plugin sem `repo` escreve no `--cwd`.
2. **Door 12, forma do `summary` sem prova.** Ordem, corte em 5 e `(+N more)` (`plan.md:101`, `run.py:318-320`)
   sobrevivem ao M10 e ao M11. O C64 precisa de mais de 5 links, com nomes que o `os.walk` não entregue já em ordem
   (por exemplo, arquivos `b` e `a` e um diretório `c`).
3. **C50 e C53 no box.** Seguem como nas rodadas 3 a 5: provados só no host de dev.
4. **F7 vivo.** É o ramo `name` do `skill_invoked`, que só o box exercita. Carried from bf98604.
5. **Test policy, linha de integração.** Nenhuma prova `-m integration` desta feature tem evidência de box.
6. **M9 equivalente (fora do veredito por si só).** O filtro de `.git` não muda nada para um clone real. Remover a
   menção a `.git/` da door 12 ou aceitar o mutante como equivalente são as duas saídas.
7. **Precisão (fora do veredito).** A frase en "Both rules match the literal text: Another spelling, such as quotes, gets
   around it." (`docs/plugins.md:100-101`) usa maiúscula depois dos dois-pontos e `it` para duas regras, para casar com
   a string do C63. O CHANGELOG diz `them`. Os erros de listagem dentro do clone são engolidos pelo `os.walk`
   (`onerror=None`, sonda 6), e um PR não alcança isso.
8. **Observação, carried from f69d5e3.** `"*>*"` também nega comando legítimo com `>` dentro de aspas. Os operadores
   `||`, `&`, crase e `<(...)` estão negados mas sem check.
