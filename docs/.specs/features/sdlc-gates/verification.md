# sdlc-gates verification

**Verdict**: PASS
**Profile**: standard
**Diff range**: 15398f3..9d14ce3
**Round**: 2 - scoped
**Verifier**: independent sub-agent (author != verifier)

Resumo: 56 de 56 checks provados com evidência localizada em `9d14ce3`. As lacunas da rodada 1 estão fechadas:
C18 (`validate_verification.py`), C22 (posição do `**Approved**`), o par `CONTRIBUTING.md` da AC 39 e o conteúdo
enumerado do `AGENTS.md` das AC 26 e 35. Os três mutantes que sobreviveram na rodada 1 (F1, F2, F3) agora morrem, e os
dois mutantes novos, sobre as asserções que o fix acrescentou (F2b, F6), também.

Escopo da rodada 2: o fix é `9d14ce3` ("test(sdlc): fecha as lacunas da rodada 1 do Verifier") e mexe só em
`tests/test_sdlc.py` e `tests/test_agents_md.py` (`git diff 53f7ffb..9d14ce3`: +40 -4). Nenhum código de produto mudou.
Reverifiquei os vereditos que não eram PASS (C18, C22, as 4 linhas de Coverage com membro sem prova), atualizei as
citações dos dois arquivos tocados e reinjetei os faults nas superfícies que o fix tocou ou criou. O resto vem da
rodada 1 e está marcado `carried from 53f7ffb`. Como a regra manda, as provas rodaram inteiras de novo em `9d14ce3`.

Como as provas rodaram (`verified at 9d14ce3`):

- **Lote A** (uma invocação, `-rA`, cada teste listado individualmente): mesmo comando da rodada 1, com a alternação
  `-k` dos 56 nomes de prova. Resultado: `172 passed, 1 failed, 60 deselected`. O único que falhou foi
  `test_spec_plan_doc_criterion`, porque roda `tools/sdlc.py spec sdlc-gates` contra a árvore real e lia o
  `verification.md` FAIL da rodada 1 (`validate_verification.py` sai com `1` para FAIL, que é o comportamento certo).
  Depois de escrever este relatório, rodei de novo:
  `uv run pytest -rA tests/test_sdlc.py -k spec_plan_doc_criterion`, que deu `1 passed` (ver `## Gate`).
- **Suíte inteira** em `9d14ce3`: ver `## Gate`.
- **C25, C32, C45**: comandos não-pytest, rodados de novo nesta rodada (ver as linhas).

## Binding sources

`carried from 53f7ffb`. Fora do perfil (`standard`); o fix não tocou a interface.

| Source | Opened | Contradiction | Uncovered |
| --- | --- | --- | --- |
| doc `memory#agents-md` | não aberta (perfil standard); comportamento conferido pelo `claude` 2.1.312 real (C45) | none | - |
| decisões de 29/10/2026 | via plano (`Problem`, `Out of scope`, `Assumptions`) | none | - |

## Checks

Proofs `verified at 9d14ce3` (lote A). Citações de `tests/test_sdlc.py` e `tests/test_agents_md.py` atualizadas para
`9d14ce3`; as dos outros arquivos não mudaram (o fix não os tocou) e são `carried from 53f7ffb`. Os números de linha
de `tests/test_sdlc.py` abaixo da linha 300 também não mudaram.

| Check | Claim | Proof run | Evidence | Result |
| --- | --- | --- | --- | --- |
| C1 | `default_install_hook_types` e os 3 hooks criados | lote A `test_precommit_installs_three_hook_types` PASSED | `tests/test_sdlc.py:177` - `config["default_install_hook_types"] == ["pre-commit", "commit-msg", "pre-push"]`; `:180` - `(repo / ".git" / "hooks" / hook).is_file()` | PASS |
| C2 | hooks `sdlc-*` nas stages certas, mesmo `exclude` | lote A `test_precommit_hooks`, `test_sdlc_hooks_stages` PASSED | `tests/test_repo_files.py:150` - `hook["stages"] == [stage]`; `:151` - `command in hook["entry"]`; `:152`/`:137` - `hook.get("exclude") == PRECOMMIT_EXCLUDE` | PASS |
| C3 | 11 tipos, com/sem escopo, `!`, 100 caracteres -> `0` sem saída | lote A `test_commit_msg_accepts[*]` (45) PASSED | `tests/test_sdlc.py:99-100` - `returncode == 0`, `result.stdout == "" and result.stderr == ""`; `:91` - `len(first) == 100` | PASS |
| C4 | 6 rejeições, regex em stderr | lote A `test_commit_msg_rejects[*]` (6) PASSED | `tests/test_sdlc.py:109-110` - `returncode == 1`, `DOOR_3 in result.stderr`; 101 caracteres em `:105` | PASS |
| C5 | `Co-authored-by` em 3 caixas -> `1` e a linha | lote A `test_commit_msg_coauthor[*]` (3) PASSED | `tests/test_sdlc.py:117-118` - `returncode == 1`, `line in result.stderr` | PASS |
| C6 | 3 aceitas, 6 recusadas com os 3 padrões | lote A `test_branch_pattern[*]` (9) PASSED | `tests/test_sdlc.py:142` - `returncode == 0`; `:145-147` - `returncode == 1`, `pattern in result.stderr` para cada `DOOR_2` | PASS |
| C7 | `pre-push` real recusa `feat/sdlc`, aceita `feat/31/sdlc` | lote A `test_pre_push_hook_blocks` PASSED | `tests/test_sdlc.py:207-208` - `refused.returncode != 0`, `not remote_has("feat/sdlc")`; `:211-212` - `accepted.returncode == 0`, `remote_has("feat/31/sdlc")` | PASS |
| C8 | commit em `main` -> `1` com a mensagem | lote A `test_pre_commit_on_main` PASSED | `tests/test_sdlc.py:224-225` - `returncode == 1`, `MAIN_MSG in result.stderr` | PASS |
| C9 | clone principal: código listado; 6 caminhos livres; worktree linkada passa | lote A `test_pre_commit_main_clone` PASSED | `tests/test_sdlc.py:240-241`; `:248` - `allowed.returncode == 0`; `:255` - `linked.returncode == 0` | PASS |
| C10 | escape libera o clone, não `main` | lote A `test_pre_commit_allow_main_edit` PASSED | `tests/test_sdlc.py:264` - `.returncode == 0`; `:267-268` - `on_main.returncode == 1`, `MAIN_MSG in on_main.stderr` | PASS |
| C11 | sem subcomando / desconhecido -> `2` e uso | lote A `test_usage_exit_2[*]` (2) PASSED | `tests/test_sdlc.py:275-276` - `returncode == 2`, `"usage:" in result.stderr` | PASS |
| C12 | job `process`, triggers, `fetch-depth: 0`, `--base` = base SHA | lote A `test_process_job` PASSED | `tests/test_workflows.py:166`, `:168`, `:170`; `:174` - `step["env"][base.group(1)] == "${{ github.event.pull_request.base.sha }}"` | PASS |
| C13 | título/branch/corpo só por `env:` | lote A `test_process_job_no_expression_in_run` PASSED | `tests/test_workflows.py:183` - `expression not in run`; `:187` - `expression in values` | PASS |
| C14 | título fora da door 3 -> `1` nomeando; bom -> `0` | lote A `test_pr_title` PASSED | `tests/test_sdlc.py:442` - `ok.returncode == 0`; `:445-446` - `bad.returncode == 1`, `"ajusta coisa" in bad.stderr` | PASS |
| C15 | branch fora da door 2 -> `1` nomeando | lote A `test_pr_branch` PASSED | `tests/test_sdlc.py:454-455` - `returncode == 1`, `"feat/sdlc" in result.stderr` | PASS |
| C16 | coautor em commit (SHA) e no corpo | lote A `test_pr_coauthor` PASSED | `tests/test_sdlc.py:463-464` - `returncode == 1`, `sha in in_commit.stderr`; `:469-470` - `"body" in in_body.stderr.lower()` | PASS |
| C17 | `Closes/Fixes/Refs #31` passam; sem, `#32`, `#310` falham; dependabot/release sem link passam | lote A `test_pr_issue_link[*]` (8) PASSED | `tests/test_sdlc.py:492` - `(result.returncode == 0) is ok`; `:494` - `result.returncode == 1` | PASS |
| C18 | `spec` roda os 3 validadores com `--root docs` só para os presentes | lote A `test_spec_runs_validators` PASSED; F1 agora morre | `tests/test_sdlc.py:306` - `ok.returncode == 0`; `:311-312` - `returncode == 1`, `"validate_checks.py" in bad.stderr`; `:318` - `alone.returncode == 0` (só `plan.md`); novo `:327-329` - `bad_verification.returncode == 1`, `"validate_verification.py" in bad_verification.stderr`, `"validate_checks.py" not in bad_verification.stderr` | PASS |
| C19 | dois validadores falhando, os dois nomeados | lote A `test_spec_reports_every_failure` PASSED | `tests/test_sdlc.py:340-342` - `returncode == 1`, `"validate_plan.py" in ...`, `"validate_checks.py" in ...` | PASS |
| C20 | `pr` roda `spec` só das features tocadas | lote A `test_pr_specs_of_touched_features` PASSED | `tests/test_sdlc.py:506` - `untouched.returncode == 0`; `:512-513` - `touched.returncode == 1`, `"nova" in ... and "validate_checks.py" in ...` | PASS |
| C21 | código sem `verification.md` -> `1` com a mensagem; com, passa; só pyproject/uv.lock/CHANGELOG passa | lote A `test_pr_requires_verification[*]` (2), `test_pr_requires_verification_not_for_release` PASSED | `tests/test_sdlc.py:523-524` - `missing.returncode == 1`, `NO_VERIFICATION in missing.stderr`; `:528` - `verified.returncode == 0`; `:543` - `result.returncode == 0` | PASS |
| C22 | `plan.md` tocado sem `**Approved**` logo abaixo do título -> `1`; data inválida -> `1`; intocado não reprova | lote A `test_pr_plan_approved` PASSED; F3 agora morre | `tests/test_sdlc.py:567` - `ok.returncode == 0` (velho sem marcador, intocado); `:570` - `== 1` (sem a linha); `:574` - `== 1` (`amanhã`); novo `:579` - `not below.split("\n", 3)[2].startswith("**Approved**")` (a linha existe, mas fora do lugar) e `:581` - `pr.run().returncode == 1`; `:586` - `== 1` (velho alterado) | PASS |
| C23 | `## Handoff` 40 -> `0`, 41 -> `1`, e `pr` reprova com 41 | lote A `test_state_handoff_limit` PASSED | `tests/test_sdlc.py:378` (40) e `:380` - `== 0`; `:382` - `== 1` (41); `:386` - `pr.run().returncode == 1` | PASS |
| C24 | 6 checks com `process`/`15368`, resto da door 11 | lote A `test_repo_settings_payloads_match_door_11` PASSED | `tests/test_repo_files.py:261` - `json.loads(read(".github/repo-settings/main-protection.json")) == MAIN_PROTECTION`, com `{"context": "process", "app_id": 15368}` em `:233` | PASS |
| C25 | o PR desta feature passa no `process` | comando do `checks.md` exatamente como escrito, rodado de novo: exit 0 | `gh pr checks 34`: `process pass`, run `40881199531` sobre o head `53f7ffb` do PR. **`9d14ce3` ainda não está no PR** (`headRefOid` = `53f7ffb`), então o CI não rodou sobre ele. Cobri a diferença reproduzindo o job em `9d14ce3`: `uv run python tools/sdlc.py pr --title "<título do PR 34>" --branch feat/31/sdlc-gates --body-file <corpo do PR 34> --base 15398f3...`, que saiu com exit 0 (ver `## Gate`). `9d14ce3` só mexe em `tests/`, e nenhuma regra do `pr` lê `tests/`. O CI tem de rodar de novo quando `9d14ce3` e este relatório forem para o PR | PASS |
| C26 | `gate-humano.sh` em `PreToolUse`/`Bash`; `gate-worktree.sh` mantido; `SessionStart` | lote A `test_settings_registers_hooks` PASSED | `tests/test_claude_hooks.py:72`, `:73`, `:75` | PASS |
| C27 | 7 comandos -> `ask` com motivo | lote A `test_gate_humano_ask[*]` (7) PASSED | `tests/test_claude_hooks.py:93-94` - `kind == "ask"`, `reason.strip()` | PASS |
| C28 | push para `main`, `HEAD:main`, sem refspec em `main`, composto -> `deny` | lote A `test_gate_humano_deny[*]` (3), `test_gate_humano_deny_current_main` PASSED | `tests/test_claude_hooks.py:102` - `[0] == "deny"`; `:117` - `decision("git push", repo)[0] == "deny"` | PASS |
| C29 | push de branch da door 2 e `gh pr create` -> `allow`; `feat/sdlc` não | lote A `test_gate_humano_allow[*]` (2), `test_gate_humano_allow_not_outside_door_2` PASSED | `tests/test_claude_hooks.py:125` - `[0] == "allow"`; `:129` - `[0] != "allow"` | PASS |
| C30 | 3 comandos neutros -> `0` e stdout vazio | lote A `test_gate_humano_neutral[*]` (3) PASSED | `tests/test_claude_hooks.py:141-142` | PASS |
| C31 | `branch_pattern` e `handoff_skill` | lote A `test_worktree_handoff_config` PASSED | `tests/test_repo_files.py:416-417` | PASS |
| C32 | issues abertos para webhook e sandbox do Codex | comando do `checks.md`, rodado de novo: exit 0 | #32 "Measure the routine webhook limits ..." e #33 "Codex sandbox (bwrap) does not start on the box", ambos `open`; citados em `tests/test_repo_files.py:432` | PASS |
| C33 | `## Handoff` cita `#32`/`#33`, sem `bwrap` nem `limites do webhook` | lote A `test_state_handoff_cites_issues` PASSED | `tests/test_repo_files.py:432-434` | PASS |
| C34 | 4 seções; coluna do Rodrigo = plano, merge, tag | lote A `test_sections_and_autonomy` PASSED | `tests/test_agents_md.py:15` - `f"## {heading}" in lines`; `:35` - `len(cells) == 3`; `:37` - uma célula por palavra | PASS |
| C35 | `## Skills` e `## Ambiente` com os termos | lote A `test_skills_and_environment` PASSED | `tests/test_agents_md.py:44` - `needle in skills` (`tlc-spec-lean`, `tlc-discover`, `## Intent`, `tools/sdlc.py spec`, `--root docs`); novo `:46` - `len(no_spec) == 1` e `:48` - `kind in no_spec[0][0]` para `dependências`, `docs`, `release`; `:50-51` - `opencode-go`, `box.*só pelo bot` | PASS |
| C36 | regras do antigo `CLAUDE.md` no `AGENTS.md` | lote A `test_carries_former_claude_md` PASSED | `tests/test_agents_md.py:65` - `needle in body` (6 termos) | PASS |
| C37 | `CONTRIBUTING.md` EN/pt-BR com hooks, `process`, padrão, `Closes #` | lote A `test_contributing_gates` PASSED | `tests/test_docs.py:342` - `needle in text` | PASS |
| C38 | `state` sai `0` contra o repositório | lote A `test_state_handoff_within_limit` PASSED | `tests/test_repo_files.py:442` - `result.returncode == 0` | PASS |
| C39 | nenhum `CLAUDE.md` versionado | lote A `test_no_claude_md_tracked` PASSED | `tests/test_repo_files.py:454` - `files.stdout == ""` | PASS |
| C40 | `copy` sem `CLAUDE.local.md` | lote A `test_worktree_handoff_config` PASSED | `tests/test_repo_files.py:418` | PASS |
| C41 | sem `commit-msg` instala e reporta; com, não chama | lote A `test_session_start_installs_hooks` PASSED | `tests/test_claude_hooks.py:185-186`; `:192` - `not calls.exists()` | PASS |
| C42 | aviso com `CLAUDE.md` ou `CLAUDE.local.md`; sem, nada | lote A `test_session_start_warns_claude_md[*]` (2) PASSED | `tests/test_claude_hooks.py:202` - `not in clean`; `:206` - `CLAUDE_MD_WARNING in context.splitlines()` | PASS |
| C43 | install falhando: exit `0` e a linha diz que falhou | lote A `test_session_start_install_failure` PASSED | `tests/test_claude_hooks.py:214-216` | PASS |
| C44 | `CONTRIBUTING.md` EN/pt-BR com `AGENTS.md`, `2.1.277`, `CLAUDE.local.md` | lote A `test_contributing_agents_md` PASSED | `tests/test_docs.py:349` | PASS |
| C45 | `claude` real carrega o `AGENTS.md` e responde `150k` | manual (host de dev), `carried from 53f7ffb` | `docs/.specs/features/sdlc-gates/evidence/c45.txt:5` - `150k`, `:7` - `grep -q 150k: exit 0`; na rodada 1 reexecutei, também com `claude -p --tools ""`, e a resposta foi `150k`. `9d14ce3` não toca no `AGENTS.md` nem na raiz | PASS |
| C46 | `DOOR_10_FILES` com `AGENTS.md`, sem `CLAUDE.md` | lote A `test_door_10_tree_files[*]` (22) PASSED | `tests/test_repo_files.py:300` - `"AGENTS.md",`; `:312` - `assert tracked(rel)`; nenhum `CLAUDE.md` em `:282-305` | PASS |
| C47 | prova C48 da model-setup-docs lê o `AGENTS.md`, mesmas asserções | lote A `test_agents_md_doc_rule` PASSED | `tests/test_docs.py:254`; `:256-258` | PASS |
| C48 | `## Documentação` com os termos | lote A `test_documentation_section` PASSED | `tests/test_agents_md.py:80` - `needle in docs` (7 termos); novo `:82` - `"inglês" in flat and "5 primeiras linhas" in flat`; `:83` - regex `Fora da regra: \`docs/\.specs/\`.*\`AGENTS\.md\`.*\`CHANGELOG\.md\`.*SKILL\.md`; `:85-88` - as 4 linhas da tabela, cada uma com o destino | PASS |
| C49 | checador acusa `run --timeout` em EN e pt-BR; repositório limpo | lote A `test_gate_reports_missing_flag`, `test_gate_flags_repo_clean` PASSED | `tests/test_docs.py:283`, `:288`; `:294` - `check_flags(ROOT, options) == []` | PASS |
| C50 | checador acusa `exit_code` em EN e pt-BR; 26 campos limpos | lote A `test_gate_reports_missing_event_field`, `test_gate_event_fields_repo_clean` PASSED | `tests/test_docs.py:301`, `:306`; `:313` - `len(fields) == 26`; `:314` | PASS |
| C51 | acusa `docs/x.md:3`, ignora `http(s)` e `#`; repositório limpo | lote A `test_gate_reports_broken_link`, `test_gate_links_repo_clean` PASSED | `tests/test_docs.py:326`; `:330` | PASS |
| C52 | só `README.md` ou só o par -> `1` nomeando os dois; os dois -> passa | lote A `test_pr_doc_pair[*]` (6), `test_pr_doc_pair_other_docs` PASSED | `tests/test_sdlc.py:606` - `(result.returncode == 0) is ok`; `:608` - `returncode == 1`; `:610` - `f"{name} changed" in ... or f"pair {name}" in ...`; `:612` - `rel in result.stderr` para `name` e `docs/pt-BR/{name}`. Agora parametrizado para `README.md` e `CONTRIBUTING.md` | PASS |
| C53 | `feat`/`fix` sem `## [Unreleased]` -> `1`; `refactor`/`chore` passa | lote A `test_pr_changelog_unreleased[*]` (2), `..._not_for_other_types[*]` (2) PASSED | `tests/test_sdlc.py:629` - `== 0`; `:635-636` - `returncode == 1`, `"CHANGELOG.md" in result.stderr`; `:645` - `== 0` | PASS |
| C54 | `feat`/`fix` sem doc -> `1`; `Docs: n/a - <razão>` passa; razão vazia -> `1` | lote A `test_pr_docs_or_na[*]` (2) PASSED | `tests/test_sdlc.py:661` - `without.returncode == 1`; `:664` - `with_na.returncode == 0`; `:666` - `== 1` | PASS |
| C55 | `spec` exige critério de doc ou `Docs: n/a`; passa contra este plano | lote A: falhou só pela leitura do `verification.md` FAIL da rodada 1; rodado de novo depois deste relatório: PASSED | `tests/test_sdlc.py:351` - `missing.returncode == 1`; `:354`, `:360` - `== 0`; `:363` - `this.returncode == 0` (`spec sdlc-gates` com `cwd=ROOT`) | PASS |
| C56 | item de doc do template com `Docs: n/a - <reason>` | lote A `test_pr_template_doc_item` PASSED | `tests/test_docs.py:267`; `:269` | PASS |

## Coverage

As 4 linhas que tinham membro sem prova estão `verified at 9d14ce3`. As outras são `carried from 53f7ffb`: o fix não
tocou a autoridade de nenhuma delas (as doors, as AC, `build_parser()`, `event.v1.json`).

| Set (size) | Recomputed from | Member -> proof | Unproven |
| --- | --- | --- | --- |
| subcomandos do `tools/sdlc.py` (6) - carried | door 1 | `commit-msg` C3-C5 · `branch` C6 · `pre-commit` C8-C10 · `pr` C14-C23, C52-C54 · `spec` C18-C19, C55 · `state` C23, C38 | - |
| exit codes do `tools/sdlc.py` (3) - carried | door 1 | `0` C3 · `1` C4 · `2` C11 | - |
| hook types instalados (3) - carried | AC 1 | os 3 em C1 | - |
| tipos da door 3 (11) - carried | regex da door 3 | os 11 em C3 | - |
| rejeições da primeira linha (6) - carried | C4 sobre a door 3 | os 6 em C4 | - |
| formas da door 2 (3 aceitas + recusa) - carried | regex da door 2 | C6, C7 | - |
| caminhos livres no clone principal (6) - carried | AC 7 | os 6 em C9 | - |
| regras do `pre-commit` (3) - carried | AC 6-8 | C8 · C9 · C10 | - |
| triggers do job `process` (4) - carried | AC 10 | os 4 em C12 | - |
| regras do `pr` (12) - verified at 9d14ce3 | AC 11-18, 39-41 | título C14 · branch C15 · coautor em commit e no corpo C16 · link C17 · specs tocadas C20 · `verification.md` C21 · `**Approved**` (presença, data e agora posição, `tests/test_sdlc.py:579-581`) C22 · `Handoff` C23 · par C52 · `CHANGELOG.md` C53 · doc ou `Docs: n/a` C54 | - |
| docs pareados do `pr` (3) - verified at 9d14ce3 | AC 39 (`README.md`, `CONTRIBUTING.md`, `docs/<x>.md`) | `README.md` C52 · `CONTRIBUTING.md` C52 (params novos, `test_pr_doc_pair[changed3..5]`; F2 e F2b morrem) · `docs/<x>.md` `test_pr_doc_pair_other_docs` (`tests/test_sdlc.py:620-621`, roda no `-k pr_doc_pair` da C52) | - |
| palavras do link (3) - carried | door 7 | os 3 em C17 | - |
| validadores do `spec` (4) - verified at 9d14ce3 | AC 15, AC 42 | `validate_plan` C19 · `validate_checks` C18 · `validate_verification` C18 (`tests/test_sdlc.py:327-329`; F1 morre) · critério de doc C55 | - |
| decisões do `gate-humano.sh` (4) - carried | door 6 | C27 · C28 · C29 · C30 | - |
| comandos `ask` (6) - carried | door 6, AC 20 | os 6 (7 casos) em C27 | - |
| formas `deny` (3) - carried | AC 21 | C28 (`tests/test_claude_hooks.py:102`, `:117`) | - |
| formas `allow` (2) - carried | AC 22 | C29 | - |
| saídas do hook de sessão (4) - carried | AC 9, AC 32 | C41 · C41 · C43 · C42 | - |
| seções do `AGENTS.md` (5) - carried | AC 26, AC 35 | C34 · C35 · C48 | - |
| conteúdo enumerado do `AGENTS.md` (AC 26: 4 rotas + raiz `docs`; AC 35: 5 itens + tabela de 4 linhas) - verified at 9d14ce3 | AC 26, AC 35 | rotas `tlc-spec-lean`, `tlc-discover`, `## Intent` e "dependências, docs, release -> sem spec" C35 (`tests/test_agents_md.py:44-48`) · raiz `--root docs` e `tools/sdlc.py spec` C35 (`:44`) · inglês primeiro, `docs/pt-BR/`, 5 primeiras linhas, mesmo commit, fora da regra, escape `Docs: n/a -` C48 (`:80-83`) · tabela de 4 linhas C48 (`:85-88`); F6 morre | - |
| opções longas do parser (28) - carried | `build_parser()`, recontado: 28 | C49 (`tests/test_docs.py:294`) | - |
| campos do evento (26) - carried | `event.v1.json`, recontado: 26 | C50 (`tests/test_docs.py:313-314`) | - |
| arquivos com links checados (4 grupos) - carried | AC 38 | C51 | - |
| doors (9) - verified at 9d14ce3 | `## Landing` | 1 C2, C11 · 2 C6 · 3 C3, C4 · 4 C12, C24, C25 · 5 C22 (posição agora provada) · 6 C26-C30 · 7 C17 · 8 C39, C45 · 9 C48, C54, C55 | - |

Lacuna de precisão nos checks, registrada sem reprovar: a AC 39 é mais larga que o texto da C52. A AC cobre
`README.md`, `CONTRIBUTING.md` e `docs/<x>.md`, mas a C52 só nomeia `README.md`. Agora a prova da C52 cobre os três
(dois pelos params, um por `test_pr_doc_pair_other_docs`), então o membro está provado. O texto do check, porém,
continua mais estreito que a AC e deveria ser alargado numa próxima revisão do `checks.md`. A mesma coisa vale, em menor
grau, para C35 e C48 em relação às AC 26 e 35: as provas agora vão além do claim escrito.

Outro registro, também sem reprovar: no param `test_pr_doc_pair[changed4]` (só `docs/pt-BR/CONTRIBUTING.md`), a
asserção de nome em `tests/test_sdlc.py:610-612` continuaria passando se o par apontado estivesse errado
(`docs/CONTRIBUTING.md`), porque `CONTRIBUTING.md` é substring dos dois caminhos. O mutante F2b, que faz exatamente
isso, morre assim mesmo pelo `changed5`. Fica como asserção frouxa, não como mutante sobrevivente.

Swept `existing` (`carried from 53f7ffb`): `tools/sdlc.py:46-52` só chama `git`; nenhum `gh`. Confere.

## Test policy rows

`carried from 53f7ffb`, com as duas linhas reavaliadas porque o fix tocou `tests/test_sdlc.py`: continuam atendidas.

| Row | Files it classifies | Required proof | Expectation met |
| --- | --- | --- | --- |
| `tools/sdlc.py` decide e é alcançado por hook git e CI: subprocesso contra repositório git de teste, um caso por linha das tabelas (`pr` 12, `branch` 4, `pre-commit` 3) | `tools/sdlc.py`, `.pre-commit-config.yaml` | `tests/test_sdlc.py:35-43` roda o script como subprocesso contra repositórios em `tmp_path`; `pr` 12/12, `branch` 4/4, `pre-commit` 3/3; hook git real em C1, C7 | yes |
| hooks do Claude Code decidem e são alcançados por JSON em stdin: um caso por decisão | `.claude/hooks/gate-humano.sh`, `.claude/hooks/session-start.sh`, `.claude/settings.json` | `tests/test_claude_hooks.py:31-40`, `:159-170`; C27-C30, C41-C43 | yes |

## Faults injected

`verified at 9d14ce3` para F1, F2, F3, F2b e F6, numa worktree de rascunho nova (`git worktree add --detach
<scratchpad>/mut2 HEAD`). F4 e F5 são `carried from 53f7ffb`, porque o fix não tocou `tests/test_claude_hooks.py` nem
os hooks. Cada fault foi aplicado, a prova rodada sobre o arquivo de teste inteiro e o fault revertido com
`git checkout -- .`. O `git status --porcelain` da árvore real ficou igual antes e depois: só
`?? docs/.specs/features/sdlc-gates/verification.md`, sem diferença contra a baseline. O rascunho foi removido com
`git worktree remove --force`.

| Mutation | Location | Killed |
| --- | --- | --- |
| F1: tira `validate_verification.py` de `SPEC_FILES` | `tools/sdlc.py:36` | yes - `test_spec_runs_validators` failed em `tests/test_sdlc.py:327` (1 failed, 103 passed) |
| F2: `CONTRIBUTING.md` deixa de ser doc pareado, nos dois sentidos | `tools/sdlc.py:184`, `:189` | yes - `test_pr_doc_pair[changed3-False]` e `[changed5-True]` failed |
| F3: `**Approved**` aceito em qualquer linha depois do título | `tools/sdlc.py:200` | yes - `test_pr_plan_approved` failed em `tests/test_sdlc.py:581` |
| F2b (superfície nova): só o sentido `docs/pt-BR/CONTRIBUTING.md` -> `docs/CONTRIBUTING.md` errado | `tools/sdlc.py:189` | yes - `test_pr_doc_pair[changed5-True]` failed em `tests/test_sdlc.py:606` |
| F6 (superfície nova, asserções do `AGENTS.md`): tira a rota "dependências, docs, release -> sem spec" e o "5 primeiras linhas" | `AGENTS.md:46`, `:83` | yes - `test_skills_and_environment` e `test_documentation_section` failed |
| F4: push que alcança `main` devolve `ask` em vez de `deny` (carried from 53f7ffb) | `.claude/hooks/gate-humano.sh:49` | yes |
| F5: aviso só para `CLAUDE.md`, não para `CLAUDE.local.md` (carried from 53f7ffb) | `.claude/hooks/session-start.sh:24` | yes |

## Gate

`verified at 9d14ce3`:

- `uv run pytest -q` em `9d14ce3`: `1 failed, 987 passed, 50 deselected in 200.55s`. A única falha foi `test_spec_plan_doc_criterion`, rodado com o `verification.md` FAIL da rodada 1 ainda no lugar (ele valida este relatório). Com este relatório no lugar, o teste passa (linha seguinte), e nenhum outro teste lê o `verification.md`. O total é 988 testes, contra 985 na rodada 1: são os 3 params novos de `test_pr_doc_pair`.
- `uv run pytest -rA tests/test_sdlc.py -k spec_plan_doc_criterion` depois deste relatório: `PASSED tests/test_sdlc.py::test_spec_plan_doc_criterion`, `1 passed`.
- Reprodução local do job `process` em `9d14ce3` (C25): `uv run python tools/sdlc.py pr --title "feat(sdlc): gates do fluxo de desenvolvimento conferidos por máquina" --branch feat/31/sdlc-gates --body-file <corpo do PR 34> --base 15398f38d4fa742178e914debf5e2d231f08eb82`, com exit `0` e este relatório no lugar. Com o relatório FAIL da rodada 1, saía com `1` nomeando `validate_verification.py`, o que é o esperado.
- `gh pr checks 34`: os 6 `pass`, no head `53f7ffb` do PR.
- `python3 .claude/skills/tlc-spec-lean/scripts/validate_verification.py sdlc-gates --root docs`: exit `0`, `validate_verification: 0 error(s), 0 warning(s) across [sdlc-gates]`.
