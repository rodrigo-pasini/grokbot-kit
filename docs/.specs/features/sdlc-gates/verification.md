# sdlc-gates verification

**Verdict**: PASS
**Profile**: standard
**Diff range**: 15398f3..eaa574f
**Round**: 9 - scoped
**Verifier**: independent sub-agent (author != verifier)

Resumo: os 57 checks têm evidência localizada e as provas passam em `eaa574f` (`989 passed`). A AD-053 troca a door 6:
o `gate-humano.sh` sai e os gates humanos passam a ser regras de permissão do Claude Code no `.claude/settings.json`
(`ask` para merge, tag, release e `gh api` de proteção, environment, merge e releases; `allow` para `git push *` e
`gh pr create *`). O push para `main` fica com o hook git `pre-push` e com a proteção da `main` no GitHub. As AC 20-23
e os checks C26-C30 foram reescritos, e as AC 44-45 e 47-59 e os checks C57, C58 e C60-C74 saíram. Essa reescrita foi
autorizada pelo Rodrigo, e não a tratei como check removido ou enfraquecido. Conferi que `plan.md`, `checks.md`,
`AGENTS.md` e o par `CONTRIBUTING.md` / `docs/pt-BR/CONTRIBUTING.md` descrevem o mesmo desenho, e que nenhum arquivo
vivo cita o hook apagado como se ele existisse. Os 6 mutantes morrem. O C30 rodou contra o repositório real e saiu com
`0`.

Ficam quatro achados que não bloqueiam (ver `## Ranked gaps`). Nenhum quebra o contrato: o agente não faz merge,
release nem mudança de proteção sem o Rodrigo confirmar, e não põe código na `main` sem PR. O achado mais sério é o
N2: um push de tag escrito como refspec (`git push origin HEAD:refs/tags/v9.9.9`) ou a deleção de uma tag
(`git push origin :v0.6.0`) casa o `allow` `Bash(git push *)` e não casa nenhum `ask`. Assim o agente consegue criar
ou apagar uma tag `v*` no GitHub sem pedir. O publish no PyPI e o GitHub Release continuam esperando o Rodrigo, porque
o environment `pypi` tem ele como revisor obrigatório (conferido ao vivo). A correção é barata, e recomendo fazê-la
neste PR.

Escopo da rodada 9: `80f0a42` e `b07aa2a` mexem no hook que a AD-053 substituiu. `e59dce1` escreve a AD-053 e as specs.
`eaa574f` traz as permissões no `settings.json`, apaga o hook, cria as provas C26, C27 e C29 em
`tests/test_claude_hooks.py` e a C28 (`test_pre_push_refuses_main`) em `tests/test_sdlc.py`, e mexe nos docs. Fora as
specs e as lições, o intervalo `b852e33..eaa574f` toca `.claude/settings.json`, `.claude/hooks/gate-humano.sh`
(apagado), `AGENTS.md`, `CONTRIBUTING.md`, `docs/pt-BR/CONTRIBUTING.md`, `tests/test_claude_hooks.py` e
`tests/test_sdlc.py`. Não toca `tools/`, `.pre-commit-config.yaml`, `.claude/hooks/session-start.sh` nem os outros
arquivos de teste. Verifiquei por inteiro C26-C30 e C59. Verifiquei de novo C7 e C41-C43, porque a remoção do hook e as
22 linhas novas de `tests/test_sdlc.py` mexem neles, e os checks de doc C34-C37, C44, C48 e C52, porque o `AGENTS.md` e
o par `CONTRIBUTING` mudaram. O resto é `carried from b852e33`, com as provas rodadas de novo e as citações de
`tests/test_sdlc.py` acima da linha 211 deslocadas em +22.

Como as provas rodaram (`verified at eaa574f`):

- **Lote A**: uma invocação, `uv run pytest -rA -p no:cacheprovider` (a suíte inteira, que contém todas as provas pytest
  do `checks.md`), numa worktree de rascunho (`git worktree add --detach <scratchpad>/full9 HEAD`). A worktree tinha o
  `verification.md` versionado no lugar, que é o PASS da rodada 2, então `test_spec_plan_doc_criterion` validou um
  relatório PASS. Saída: `989 passed, 50 deselected in 202.25s`, exit `0`, nenhum `FAILED`. Cada teste aparece listado.
  Contagem `PASSED` das provas novas e tocadas: `test_settings_registers_hooks` 1, `test_settings_permissions_ask` 1,
  `test_settings_permissions_ask_covers` 12, `test_settings_permissions_allow` 1, `test_pre_push_refuses_main` 1,
  `test_pre_push_hook_blocks` 1, `test_commit_msg_merge_accepts` 6, `test_commit_msg_merge_rejects` 1,
  `test_pr_title_merge` 1, `test_session_start_*` 4, `test_spec_plan_doc_criterion` 1.
- **C25, C30, C32, C45**: comandos que não são pytest. Rodei C25 e C30 nesta rodada. C32 e C45 são
  `carried from b852e33`, e o intervalo não os toca (ver as linhas).

## Binding sources

`carried from b852e33`, com uma linha nova. Fora do perfil (`standard`).

| Source | Opened | Contradiction | Uncovered |
| --- | --- | --- | --- |
| doc `memory#agents-md` | não aberta (perfil standard); comportamento conferido pelo `claude` 2.1.312 real (C45) | none | - |
| decisões de 29/10/2026, review do PR #34 e AD-053 | via plano (`Problem`, `Out of scope`, `Landing` door 6, S3, S8) e `docs/.specs/STATE.md:59` | none | - |
| doc `code.claude.com/docs/en/permissions.md` (citada no pedido) | sim, lida nesta rodada | none: as regras usam a forma `Bash(cmd *)`; `ask` vale para qualquer subcomando, inclusive dentro de `$( )`; a ordem é deny → ask → allow; ` *` no fim aceita o comando sem argumento (o `matches` do teste segue isso) | - |

## Checks

Proofs `verified at eaa574f` (lote A). C26-C30, C59, C7, C41-C43 e os checks de doc têm citações atualizadas. Os outros
são `carried from b852e33`, e as provas rodaram de novo.

| Check | Claim | Proof run | Evidence | Result |
| --- | --- | --- | --- | --- |
| C1 | `default_install_hook_types` e os 3 hooks criados | lote A `test_precommit_installs_three_hook_types` PASSED | `tests/test_sdlc.py:206` - `config["default_install_hook_types"] == ["pre-commit", "commit-msg", "pre-push"]`; `:209` - `(repo / ".git" / "hooks" / hook).is_file()` | PASS |
| C2 | hooks `sdlc-*` nas stages certas, mesmo `exclude` (carried) | lote A `test_precommit_hooks`, `test_sdlc_hooks_stages` PASSED | `tests/test_repo_files.py:150` - `hook["stages"] == [stage]`; `:151`; `:152`/`:137` - `hook.get("exclude") == PRECOMMIT_EXCLUDE` | PASS |
| C3 | 11 tipos, com/sem escopo, `!`, 100 caracteres -> `0` sem saída (carried) | lote A `test_commit_msg_accepts[*]` (45) PASSED | `tests/test_sdlc.py:99-100` - `returncode == 0`, `result.stdout == "" and result.stderr == ""`; `:91` - `len(first) == 100` | PASS |
| C4 | 6 rejeições, regex em stderr (carried) | lote A `test_commit_msg_rejects[*]` (6) PASSED | `tests/test_sdlc.py:109-110` - `returncode == 1`, `DOOR_3 in result.stderr` | PASS |
| C5 | `Co-authored-by` em 3 caixas -> `1` e a linha (carried) | lote A `test_commit_msg_coauthor[*]` (3) PASSED | `tests/test_sdlc.py:117-118` - `returncode == 1`, `line in result.stderr` | PASS |
| C6 | 3 aceitas, 6 recusadas com os 3 padrões (carried) | lote A `test_branch_pattern[*]` (9) PASSED | `tests/test_sdlc.py:171` - `returncode == 0`; `:174-176` - `returncode == 1`, `pattern in result.stderr` | PASS |
| C7 | `pre-push` real recusa `feat/sdlc`, aceita `feat/31/sdlc` (reverificado: o hook git em `.pre-commit-config.yaml:46-48` não mudou) | lote A `test_pre_push_hook_blocks` PASSED | `tests/test_sdlc.py:258-259` - `refused.returncode != 0`, `not remote_has("feat/sdlc")`; `:262-263` - `accepted.returncode == 0`, `remote_has("feat/31/sdlc")` | PASS |
| C8 | commit em `main` -> `1` com a mensagem (carried) | lote A `test_pre_commit_on_main` PASSED | `tests/test_sdlc.py:275-276` - `returncode == 1`, `MAIN_MSG in result.stderr` | PASS |
| C9 | clone principal: código listado; 6 caminhos livres; worktree linkada passa (carried) | lote A `test_pre_commit_main_clone` PASSED | `tests/test_sdlc.py:291-292`; `:299` - `allowed.returncode == 0`; `:306` - `linked.returncode == 0` | PASS |
| C10 | escape libera o clone, não `main` (carried) | lote A `test_pre_commit_allow_main_edit` PASSED | `tests/test_sdlc.py:315` - `.returncode == 0`; `:318-319` - `on_main.returncode == 1`, `MAIN_MSG in on_main.stderr` | PASS |
| C11 | sem subcomando / desconhecido -> `2` e uso (carried) | lote A `test_usage_exit_2[*]` (2) PASSED | `tests/test_sdlc.py:326-327` - `returncode == 2`, `"usage:" in result.stderr` | PASS |
| C12 | job `process`, triggers, `fetch-depth: 0`, `--base` = base SHA (carried) | lote A `test_process_job` PASSED | `tests/test_workflows.py:166`, `:168`, `:170`; `:174` - `step["env"][base.group(1)] == "${{ github.event.pull_request.base.sha }}"` | PASS |
| C13 | título/branch/corpo só por `env:` (carried) | lote A `test_process_job_no_expression_in_run` PASSED | `tests/test_workflows.py:183` - `expression not in run`; `:187` - `expression in values` | PASS |
| C14 | título fora da door 3 -> `1` nomeando; bom -> `0` (carried) | lote A `test_pr_title` PASSED | `tests/test_sdlc.py:493` - `ok.returncode == 0`; `:496-497` - `bad.returncode == 1`, `"ajusta coisa" in bad.stderr` | PASS |
| C15 | branch fora da door 2 -> `1` nomeando (carried) | lote A `test_pr_branch` PASSED | `tests/test_sdlc.py:514-515` - `returncode == 1`, `"feat/sdlc" in result.stderr` | PASS |
| C16 | coautor em commit (SHA) e no corpo (carried) | lote A `test_pr_coauthor` PASSED | `tests/test_sdlc.py:523-524` - `returncode == 1`, `sha in in_commit.stderr`; `:529-530` - `"body" in in_body.stderr.lower()` | PASS |
| C17 | `Closes/Fixes/Refs #31` passam; sem, `#32`, `#310` falham; dependabot/release sem link passam (carried) | lote A `test_pr_issue_link[*]` (8) PASSED | `tests/test_sdlc.py:552` - `(result.returncode == 0) is ok`; `:554` - `result.returncode == 1` | PASS |
| C18 | `spec` roda os 3 validadores com `--root docs` só para os presentes (carried) | lote A `test_spec_runs_validators` PASSED | `tests/test_sdlc.py:357` - `ok.returncode == 0`; `:362-363` - `returncode == 1`, `"validate_checks.py" in bad.stderr`; `:369` - `alone.returncode == 0`; `:378-380` - `bad_verification.returncode == 1`, `"validate_verification.py" in ...`, `"validate_checks.py" not in ...` | PASS |
| C19 | dois validadores falhando, os dois nomeados (carried) | lote A `test_spec_reports_every_failure` PASSED | `tests/test_sdlc.py:391-393` - `returncode == 1`, `"validate_plan.py" in result.stderr`, `"validate_checks.py" in ...` | PASS |
| C20 | `pr` roda `spec` só das features tocadas (carried) | lote A `test_pr_specs_of_touched_features` PASSED | `tests/test_sdlc.py:566` - `untouched.returncode == 0`; `:572-573` - `touched.returncode == 1`, `"nova" in touched.stderr and "validate_checks.py" in touched.stderr` | PASS |
| C21 | código sem `verification.md` -> `1` com a mensagem; com, passa; só pyproject/uv.lock/CHANGELOG passa (carried) | lote A `test_pr_requires_verification[*]` (2), `test_pr_requires_verification_not_for_release` PASSED | `tests/test_sdlc.py:583-584` - `missing.returncode == 1`, `NO_VERIFICATION in missing.stderr`; `:588` - `verified.returncode == 0`; `:603` - `result.returncode == 0` | PASS |
| C22 | `plan.md` tocado sem `**Approved**` logo abaixo do título -> `1`; data inválida -> `1`; intocado não reprova (carried) | lote A `test_pr_plan_approved` PASSED | `tests/test_sdlc.py:627` - `ok.returncode == 0`; `:630`, `:634` - `pr.run().returncode == 1`; `:639` - `not below.split("\n", 3)[2].startswith("**Approved**")`; `:641`, `:646` - `== 1` | PASS |
| C23 | `## Handoff` 40 -> `0`, 41 -> `1`, e `pr` reprova com 41 (carried) | lote A `test_state_handoff_limit` PASSED | `tests/test_sdlc.py:429` (40) e `:431` - `== 0`; `:433` - `== 1` (41); `:437` - `pr.run().returncode == 1` | PASS |
| C24 | 6 checks com `process`/`15368`, resto da door 11 (carried) | lote A `test_repo_settings_payloads_match_door_11` PASSED | `tests/test_repo_files.py:261` - `json.loads(read(".github/repo-settings/main-protection.json")) == MAIN_PROTECTION`, com `{"context": "process", "app_id": 15368}` em `:233` | PASS |
| C25 | o PR desta feature passa no `process` | comando do `checks.md` exatamente como escrito, rodado nesta rodada: exit `0` | `gh pr checks 34`: os 6 `SUCCESS` (`lint`, `typecheck`, `test (3.11)`, `test (3.12)`, `test (3.13)`, `process`) sobre o head `df8b3a4` do PR. **Push pendente**: o PR está 16 commits atrás de `HEAD` (`git rev-list --count df8b3a4..eaa574f` = 16), então o CI não rodou sobre `eaa574f`. Cobri a diferença reproduzindo o job em `eaa574f` na worktree de rascunho: `uv run python tools/sdlc.py pr --title "feat(sdlc): gates do fluxo de desenvolvimento conferidos por máquina" --branch feat/31/sdlc-gates --body-file <corpo atual do PR 34> --base 15398f38d4fa742178e914debf5e2d231f08eb82`, exit `0`, com o relatório da rodada 2 e depois com este no lugar (ver `## Gate`). O CI tem de rodar de novo depois do push. Ver também o N4 (o corpo do PR ainda descreve o hook apagado) | PASS |
| C26 | sem `PreToolUse` em `Bash`; `gate-worktree.sh` em `Edit/Write/MultiEdit/NotebookEdit`; `session-start.sh` em `SessionStart`; `gate-humano.sh` não existe (AC 23) | lote A `test_settings_registers_hooks` PASSED; M3 morre | `tests/test_claude_hooks.py:75` - `assert not commands("PreToolUse", "Bash")`; `:76` - `any("gate-worktree.sh" in c for c in commands("PreToolUse", "Edit/Write/MultiEdit/NotebookEdit"))`; `:78` - `any("session-start.sh" in c for c in session)`; `:79` - `not (ROOT / ".claude" / "hooks" / "gate-humano.sh").exists()`. No arquivo, o matcher separa os 4 nomes com barra vertical, que aqui aparece como `/` para não quebrar a tabela. Código: `.claude/settings.json:13-23` tem um só `PreToolUse`, com o matcher em `:15`; `ls .claude/hooks` = `gate-worktree.sh`, `session-start.sh` | PASS |
| C27 | `permissions.ask` é exatamente as 12 regras (AC 20) | lote A `test_settings_permissions_ask` PASSED, mais `test_settings_permissions_ask_covers[*]` (12), que o `-k settings_permissions_ask` também seleciona; M1 morre | `tests/test_claude_hooks.py:84` - `assert settings()["permissions"]["ask"] == ASK`, com `ASK` literal em `:31-44`, na mesma ordem e com o mesmo texto das 12 regras da C27; `:105` - `any(matches(rule, command) for rule in ASK), command` para 12 comandos concretos (`gh pr merge 34 --squash`, `git push --tags`, `git push origin v0.6.0`, `gh api graphql -f query=mutation{mergePullRequest}` ...). Código: `.claude/settings.json:30-43` | PASS |
| C28 | `git push origin main` e `HEAD:main` num clone com hooks saem `!= 0`, o remoto não ganha `main`, `branch main` sai `1` (AC 21) | lote A `test_pre_push_refuses_main` PASSED; M4 e M5 morrem | `tests/test_sdlc.py:226` - `result.returncode != 0, refspec` para `("main", "HEAD:main")` em `:222`; `:230` - `"refs/heads/main" not in heads` (de `git ls-remote --heads`); `:231` - `sdlc("branch", "main", cwd=tmp_path).returncode == 1`. O commit do teste usa `--no-verify` (`:221`), então a recusa vem do `pre-push`: o M5, que só pula `main` no `entry`, derruba a prova. Código: `.pre-commit-config.yaml:48` e `tools/sdlc.py:70-73` (`DOOR_2` em `:19-23` não aceita `main`). A claim escrita passa. O push com mais de um ref passa pelo hook: ver N1 | PASS |
| C29 | `permissions.allow` é exatamente `Bash(git push *)` e `Bash(gh pr create *)`, e nenhuma casa `gh pr merge 34`, `git tag v1`, `gh release create v1` (AC 22) | lote A `test_settings_permissions_allow` PASSED; M2 morre | `tests/test_claude_hooks.py:111` - `assert allow == ALLOW` (`ALLOW` em `:45`); `:113` - `not any(matches(rule, command) for rule in allow), command` para os 3 comandos; `:114-115` - `git push -u origin feat/31/x` casa o `allow` e nenhum `ask`. O `matches` (`:52-59`) é uma réplica, dentro do teste, do casamento descrito no doc oficial (`*` é qualquer texto, ` *` no fim aceita o comando sem argumento). Não é o Claude Code real: ver N3. Código: `.claude/settings.json:26-29` | PASS |
| C30 | proteção da `main` no GitHub: `enforce_admins`, PR obrigatório, sem force push nem deleção | comando do `checks.md` exatamente como escrito, rodado nesta rodada contra `rodrigo-pasini/grokbot-kit`: exit `0` | `gh api repos/rodrigo-pasini/grokbot-kit/branches/main/protection` com o `--jq` do `checks.md` (os 4 campos `enforce_admins.enabled`, `required_pull_request_reviews != null`, `allow_force_pushes.enabled`, `allow_deletions.enabled`) -> `true true false false`. Registro sem reprovar: a proteção ao vivo ainda tem 5 checks obrigatórios (`lint`, `typecheck`, `test (3.11..3.13)`), sem o `process`. É o esperado, porque o payload da C24 é aplicado pelo Rodrigo depois do merge (plano, Path 5) | PASS |
| C31 | `branch_pattern` e `handoff_skill` (carried) | lote A `test_worktree_handoff_config` PASSED | `tests/test_repo_files.py:416-417` | PASS |
| C32 | issues abertos para webhook e sandbox do Codex (`carried from b852e33`) | comando do `checks.md`, exit `0` na rodada 7; o intervalo não toca em issues | #32 e #33 abertos; citados em `tests/test_repo_files.py:432` | PASS |
| C33 | `## Handoff` cita `#32`/`#33`, sem `bwrap` nem `limites do webhook` (carried; o `STATE.md` só ganhou a linha da AD-053 em `## Decisions`) | lote A `test_state_handoff_cites_issues` PASSED | `tests/test_repo_files.py:432-434` | PASS |
| C34 | 4 seções; coluna do Rodrigo = plano, merge, tag (reverificado: o `## Autonomia` mudou só no parágrafo abaixo da tabela) | lote A `test_sections_and_autonomy` PASSED | `tests/test_agents_md.py:30` - `section(heading)` para as 4; `:35` - `len(cells) == 3`; `:37` - `len([c for c in cells if word in c.lower()]) == 1` para `plano`, `merge`, `tag` | PASS |
| C35 | `## Skills` e `## Ambiente` com os termos (reverificado) | lote A `test_skills_and_environment` PASSED | `tests/test_agents_md.py:44` - `needle in skills`; `:46` - `len(no_spec) == 1`; `:48`; `:50-51` | PASS |
| C36 | regras do antigo `CLAUDE.md` no `AGENTS.md` (reverificado) | lote A `test_carries_former_claude_md` PASSED | `tests/test_agents_md.py:65` - `needle in body` (6 termos, incluindo `gate-worktree.sh`) | PASS |
| C37 | `CONTRIBUTING.md` EN/pt-BR com `commit-msg`, `pre-push`, `process`, padrão, `Closes #` (reverificado: o parágrafo novo está em `CONTRIBUTING.md:73-76` e `docs/pt-BR/CONTRIBUTING.md:72-75`) | lote A `test_contributing_gates` PASSED | `tests/test_docs.py:342` - `needle in text`, com o laço em `:340-341` sobre as duas línguas | PASS |
| C38 | `state` sai `0` contra o repositório (carried) | lote A `test_state_handoff_within_limit` PASSED | `tests/test_repo_files.py:442` - `result.returncode == 0` | PASS |
| C39 | nenhum `CLAUDE.md` versionado (carried) | lote A `test_no_claude_md_tracked` PASSED | `tests/test_repo_files.py:454` - `files.stdout == ""` | PASS |
| C40 | `copy` sem `CLAUDE.local.md` (carried) | lote A `test_worktree_handoff_config` PASSED | `tests/test_repo_files.py:418` | PASS |
| C41 | sem `commit-msg` instala e reporta; com, não chama (reverificado; citação atualizada, o arquivo de teste perdeu as provas do hook apagado) | lote A `test_session_start_installs_hooks` PASSED | `tests/test_claude_hooks.py:158` - `calls.read_text(...).split() == [str(repo), "run", "pre-commit", "install"]`; `:159` - `"install" in context`; `:165` - `not calls.exists()`. O `SessionStart` segue registrado em `.claude/settings.json:3-12` (C26) | PASS |
| C42 | aviso com `CLAUDE.md` ou `CLAUDE.local.md`; sem, nada (reverificado) | lote A `test_session_start_warns_claude_md[*]` (2) PASSED | `tests/test_claude_hooks.py:175` - `CLAUDE_MD_WARNING not in clean`; `:179` - `CLAUDE_MD_WARNING in context.splitlines()` | PASS |
| C43 | install falhando: exit `0` e a linha diz que falhou (reverificado) | lote A `test_session_start_install_failure` PASSED | `tests/test_claude_hooks.py:187-189` - `result.returncode == 0`, `calls.exists()`, `"fail" in context.lower()` | PASS |
| C44 | `CONTRIBUTING.md` EN/pt-BR com `AGENTS.md`, `2.1.277`, `CLAUDE.local.md` (reverificado) | lote A `test_contributing_agents_md` PASSED | `tests/test_docs.py:349` - `needle in text`, em `:347` sobre `contributing_texts()` | PASS |
| C45 | `claude` real carrega o `AGENTS.md` e responde `150k` (`carried from b852e33`) | manual (host de dev); a rodada 7 reexecutou e obteve `150k`. `eaa574f` muda o parágrafo dos gates no `AGENTS.md`, mas não a linha `budget: 150k` nem a raiz | `docs/.specs/features/sdlc-gates/evidence/c45.txt:5` - `150k`, `:7` - `grep -q 150k: exit 0` | PASS |
| C46 | `DOOR_10_FILES` com `AGENTS.md`, sem `CLAUDE.md` (carried) | lote A `test_door_10_tree_files[*]` (22) PASSED | `tests/test_repo_files.py:300` - `"AGENTS.md",`; `:312` - `assert tracked(rel)` | PASS |
| C47 | prova C48 da model-setup-docs lê o `AGENTS.md`, mesmas asserções (carried) | lote A `test_agents_md_doc_rule` PASSED | `tests/test_docs.py:254`; `:256-258` | PASS |
| C48 | `## Documentação` com os termos (reverificado; a seção não mudou) | lote A `test_documentation_section` PASSED | `tests/test_agents_md.py:80` - `needle in docs` (7 termos); `:82`; `:83`; `:85-88` | PASS |
| C49 | checador acusa `run --timeout` em EN e pt-BR; repositório limpo (carried) | lote A `test_gate_reports_missing_flag`, `test_gate_flags_repo_clean` PASSED | `tests/test_docs.py:283`, `:288`; `:294` - `check_flags(ROOT, options) == []` | PASS |
| C50 | checador acusa `exit_code` em EN e pt-BR; 26 campos limpos (carried) | lote A `test_gate_reports_missing_event_field`, `test_gate_event_fields_repo_clean` PASSED | `tests/test_docs.py:301`, `:306`; `:313` - `len(fields) == 26`; `:314` | PASS |
| C51 | acusa `docs/x.md:3`, ignora `http(s)` e `#`; repositório limpo (carried) | lote A `test_gate_reports_broken_link`, `test_gate_links_repo_clean` PASSED | `tests/test_docs.py:326`; `:330` | PASS |
| C52 | só `README.md` ou só o par -> `1` nomeando os dois; os dois -> passa (reverificado; o próprio `eaa574f` muda o par `CONTRIBUTING` no mesmo commit, e a reprodução do `pr` em `eaa574f` sai com `0`) | lote A `test_pr_doc_pair[*]` (6), `test_pr_doc_pair_other_docs` PASSED | `tests/test_sdlc.py:666` - `(result.returncode == 0) is ok`; `:668` - `returncode == 1`; `:670` - `f"{name} changed" in result.stderr or f"pair {name}" in result.stderr`; `:672` - `rel in result.stderr`; `:680-681` | PASS |
| C53 | `feat`/`fix` sem `## [Unreleased]` -> `1`; `refactor`/`chore` passa (carried) | lote A `test_pr_changelog_unreleased[*]` (2), `..._not_for_other_types[*]` (2) PASSED | `tests/test_sdlc.py:689` - `== 0`; `:695-696` - `returncode == 1`, `"CHANGELOG.md" in result.stderr`; `:705` - `== 0` | PASS |
| C54 | `feat`/`fix` sem doc -> `1`; `Docs: n/a - <razão>` passa; razão vazia -> `1` (carried) | lote A `test_pr_docs_or_na[*]` (2) PASSED | `tests/test_sdlc.py:721` - `without.returncode == 1`; `:724` - `with_na.returncode == 0`; `:726` - `pr.run().returncode == 1` | PASS |
| C55 | `spec` exige critério de doc ou `Docs: n/a`; passa contra este plano | lote A `test_spec_plan_doc_criterion` PASSED, com o relatório PASS da rodada 2 no lugar; rodado de novo com este relatório no lugar: PASSED (ver `## Gate`) | `tests/test_sdlc.py:402` - `missing.returncode == 1`; `:405`, `:411` - `== 0`; `:414` - `this.returncode == 0` (`spec sdlc-gates` com `cwd=ROOT`) | PASS |
| C56 | item de doc do template com `Docs: n/a - <reason>` (carried) | lote A `test_pr_template_doc_item` PASSED | `tests/test_docs.py:267`; `:269` | PASS |
| C59 | `commit-msg` aceita as 6 mensagens de merge do git sem saída; recusa `Merge stuff` e merge com coautor; `pr --title "Merge branch 'main'"` -> `1` (AC 46; verificado por inteiro nesta rodada) | lote A `test_commit_msg_merge_accepts[*]` (6), `test_commit_msg_merge_rejects`, `test_pr_title_merge` PASSED; M6 morre | `tests/test_sdlc.py:137-138` - `result.returncode == 0`, `result.stdout == "" and result.stderr == ""`, parametrizado em `:121-132` com as 6 mensagens exatas da C59; `:143-144` - `loose.returncode == 1`, `DOOR_3 in loose.stderr` (`Merge stuff`); `:146-147` - `coauthor.returncode == 1`, `"Co-authored-by: X <x@y>" in coauthor.stderr`; `:505-506` - `result.returncode == 1`, `"Merge branch 'main'" in result.stderr`. Código: `tools/sdlc.py:26` (`GIT_MERGE`) e `:80` (só a primeira linha sai da door 3; o coautor segue conferido) | PASS |

## Coverage

As linhas da door 6 foram recalculadas a partir do `.claude/settings.json` e da proteção ao vivo (`verified at eaa574f`).
As outras são `carried from b852e33`, porque o intervalo não tocou a autoridade delas (as doors 1-5 e 7-9,
`build_parser()`, `event.v1.json`).

| Set (size) | Recomputed from | Member -> proof | Unproven |
| --- | --- | --- | --- |
| subcomandos do `tools/sdlc.py` (6) - carried | door 1 | `commit-msg` C3-C5, C59 · `branch` C6, C28 · `pre-commit` C8-C10 · `pr` C14-C23, C52-C54 · `spec` C18-C19, C55 · `state` C23, C38 | - |
| exit codes do `tools/sdlc.py` (3) - carried | door 1 | `0` C3 · `1` C4 · `2` C11 | - |
| hook types instalados (3) - carried | AC 1 | os 3 em C1 | - |
| tipos da door 3 (11) - carried | regex da door 3 | os 11 em C3 | - |
| rejeições da primeira linha (6) - carried | door 3 | os 6 em C4 | - |
| formas da door 2 (3 aceitas + recusa) - carried | `tools/sdlc.py:19-23` | C6, C7; `main` recusada C6, C28 | - |
| regras do `pre-commit` (3) - carried | AC 6-8 | C8 · C9 · C10 | - |
| triggers do job `process` (4) - carried | AC 10 | os 4 em C12 | - |
| regras do `pr` (12) - carried | AC 11-18, 39-41 | título C14 · branch C15 · coautor C16 · link C17 · specs tocadas C20 · `verification.md` C21 · `**Approved**` C22 · `Handoff` C23 · par C52 · `CHANGELOG.md` C53 · doc ou `Docs: n/a` C54 | - |
| palavras do link (3) - carried | door 7 | os 3 em C17 | - |
| validadores do `spec` (4) - carried | AC 15, 42 | `validate_plan` C19 · `validate_checks` C18 · `validate_verification` C18 · critério de doc C55 | - |
| regras `ask` (12) - verified at eaa574f | `.claude/settings.json:31-42`, recontado: 12 | as 12 por igualdade de lista em C27 (`tests/test_claude_hooks.py:84`); casamento por comando concreto em `test_settings_permissions_ask_covers` para 11 das 12 (`--follow-tags` só pela igualdade) | - |
| regras `allow` (2) - verified at eaa574f | `.claude/settings.json:27-28` | as 2 por igualdade em C29 (`:111`); não casam merge, tag, release (`:112-113`) | - |
| registros de hook do Claude Code (2 eventos, 1 matcher de `PreToolUse`) - verified at eaa574f | `.claude/settings.json:2-24` | `SessionStart` C26, C41 · `PreToolUse` `Edit/Write/MultiEdit/NotebookEdit` C26 · nenhum `Bash` C26 | - |
| barreiras do push para `main` (3) - verified at eaa574f | AC 21, door 6 | hook `pre-push` C28 (`main`, `HEAD:main`) · `tools/sdlc.py branch main` C28 · proteção no GitHub C30 (ao vivo) | - |
| mensagens de merge do git (5 formas, 6 casos) - verified at eaa574f | AC 46, `tools/sdlc.py:26` | `Merge branch` (2 casos) · `Merge branches` · `Merge remote-tracking branch` · `Merge tag` · `Merge commit`, todas em C59 | - |
| saídas do hook de sessão (4) - verified at eaa574f | AC 9, 32 | instala C41 · já instalado C41 · falha C43 · aviso C42 | - |
| seções do `AGENTS.md` (5) - verified at eaa574f | AC 26, 35 | `## Fluxo`, `## Autonomia` C34 · `## Skills`, `## Ambiente` C35 · `## Documentação` C48 | - |
| opções longas do parser (28) - carried | `build_parser()` | C49 | - |
| campos do evento (26) - carried | `event.v1.json` | C50 | - |
| doors (9) - verified at eaa574f | `## Landing` | 1 C2, C11 · 2 C6 · 3 C3, C4, C59 · 4 C12, C24, C25 · 5 C22 · 6 C26-C30 · 7 C17 · 8 C39, C45 · 9 C48, C54, C55 | - |

Consistência do desenho novo (pedida nesta rodada), conferida no texto:

- `plan.md`: Path 3 (`:45`), `Landing` door 6 (`:93`), AC 20-23 (`:146-149`), o independent test de S3, a S8 só com a
  AC 46, `Out of scope` e a linha de `Surface` "regras de permissão do Claude Code". As 12 regras `ask` e as 2 `allow`
  da door 6 e da AC 20/22 são as mesmas do `settings.json` e do `checks.md` C27/C29.
- `checks.md`: cabeçalho com `57 checks em 8 slices` (C1-C56 e C59 = 57, recontado), S3 com C26-C30, S8 com C59 e a
  tabela de Coverage com as linhas `regras ask (12)` e `barreiras do push para main (3)`.
- `AGENTS.md:35-40` e `CONTRIBUTING.md:73-76` / `docs/pt-BR/CONTRIBUTING.md:72-75` dizem a mesma coisa: `allow` para
  push e `gh pr create`, `ask` para merge, tag, release e proteção em qualquer trecho, e `main` recusada pelo `pre-push`
  e pela proteção.
- Nenhuma referência viva ao hook apagado. `git grep gate-humano` só acha a AD-053 (`docs/.specs/STATE.md:59`), as
  linhas históricas da AD-053 no plano (`plan.md:72`, `:93`), a AC 23 e a C26, que afirmam que ele **não** existe,
  `tests/test_claude_hooks.py:79`, que prova isso, e as lições L-014..L-022 (`docs/.specs/LESSONS.md`,
  `lessons.json`), que são histórico com evidência datada. Fora do repositório, o corpo do PR #34 ainda o descreve como
  vivo (N4).
- Resíduo de texto, sem reprovar: o `## Test policy` do `checks.md` ainda diz "Os dois hooks do Claude Code decidem e
  são alcançados pelo JSON em stdin". Hoje só o `session-start.sh` é provado assim, e as permissões são provadas lendo o
  `settings.json`. O `## Handoff` do `checks.md` ainda conta "dois hooks" no tamanho. Os dois são texto de
  planejamento e não afirmam comportamento.

Swept `existing` (`verified at eaa574f`). O `authorization: C27, C28` do `checks.md` confere: as regras estão em
`.claude/settings.json:30-43`, e o `main` é recusado em `.pre-commit-config.yaml:48` -> `tools/sdlc.py:70-73`. As
lacunas de forma estão em N1 e N2. O `dependency failure` confere: `tools/sdlc.py` só chama `git` (carried).

## Test policy rows

`verified at eaa574f` para a linha que classifica arquivos tocados.

| Row | Files it classifies | Required proof | Expectation met |
| --- | --- | --- | --- |
| `tools/sdlc.py` decide e é alcançado por hook git e CI: subprocesso contra repositório git de teste, um caso por linha das tabelas (`pr` 12, `branch` 4, `pre-commit` 3) - carried, mais a C28 | `tools/sdlc.py`, `.pre-commit-config.yaml` | subprocesso em `tmp_path`; hook git real em C1, C7 e agora C28 (`tests/test_sdlc.py:213-231`, push real para um remoto bare) | yes |
| hooks do Claude Code decidem e são alcançados por JSON em stdin: um caso por decisão | `.claude/hooks/session-start.sh`, `.claude/settings.json` | `session-start.sh`: JSON em stdin, um caso por saída (C41-C43, `tests/test_claude_hooks.py:121-189`). `settings.json` não é mais um hook que decide, é configuração lida pelo Claude Code: provada pelo literal (igualdade de lista, C27/C29) e pelo casamento de regra no `matches` do teste, que reproduz o doc oficial. A fronteira real (o Claude Code pedindo confirmação) não tem prova automática (N3). Não há como pô-la num CI sem o `claude` interativo, e o doc oficial é a autoridade do casamento | yes |

## Faults injected

`verified at eaa574f`, numa worktree de rascunho (`git worktree add --detach <scratchpad>/mut9 HEAD`), com um script que
aplica um mutante por vez. A prova mais estreita rodava, e `git checkout -- .` revertia o mutante (`git status
--porcelain` vazio no rascunho depois de cada um). O teto do `verify.md` é de 5. Injetei 6, porque o pedido desta rodada
inclui a superfície da C59, e cada um derruba uma prova diferente. O `git status --porcelain` da árvore real ficou igual
à baseline antes e depois (` M docs/.specs/features/sdlc-gates/verification.md`). Os rascunhos foram removidos com
`git worktree remove --force`.

| Mutation | Location | Killed |
| --- | --- | --- |
| M1: tira uma regra `ask` (`Bash(git tag *)`) | `.claude/settings.json:32` | yes - `test_settings_permissions_ask` failed (1 failed, 14 passed) |
| M2: acrescenta o `allow` `Bash(gh pr *)`, que casa `gh pr merge 34` | `.claude/settings.json:26-29` | yes - `test_settings_permissions_allow` failed |
| M3: registra de novo um `PreToolUse` em `Bash` apontando para `gate-humano.sh` | `.claude/settings.json:13-23` | yes - `test_settings_registers_hooks` failed |
| M4: `branch_problems` aceita `main` | `tools/sdlc.py:71` | yes - `test_pre_push_refuses_main` failed |
| M5: o `entry` do hook `pre-push` deixa passar `main` (um `test` do nome contra `main` antes do `exec python3 tools/sdlc.py branch ...`) | `.pre-commit-config.yaml:48` | yes - `test_pre_push_refuses_main` failed; `test_pre_push_hook_blocks` (C7) segue verde, o que mostra que a C28 tem asserção própria |
| M6: `GIT_MERGE` aceita qualquer `Merge ` | `tools/sdlc.py:26` | yes - `test_commit_msg_merge_rejects` failed (`Merge stuff`) |

## Regressões e brechas

Sondas, todas em rascunho, com o `matches` do teste e com pushes reais para um remoto bare num clone com os hooks:

- `git push origin feat/31/x main` (dois refs) -> exit `0`, e o remoto ganha `refs/heads/main`. O `pre-commit` só passa
  ao hook o primeiro ref que tem commits a enviar (`pre_commit/commands/hook_impl.py`, `_pre_push_ns`, que retorna no
  primeiro), então o `sdlc-pre-push` confere `feat/31/x` e não `main` (N1). `--all` e `--mirror` têm a mesma forma.
  `git push --no-verify origin main` pula o hook por definição. Nos três, quem barra é a proteção (C30).
- `git push origin HEAD:refs/tags/v9.9.9` -> exit `0`, e o remoto ganha a tag. Pelo `matches`, a forma casa o `allow`
  `Bash(git push *)` e nenhum `ask` (o `Bash(git push * refs/tags/*)` exige espaço antes de `refs/`). O mesmo vale para
  `git push origin :v0.6.0` e `git push origin :refs/tags/v0.6.0` (deleção de tag), e para `git push --mirror` (N2).
  Casam o `ask`: `git push --delete origin v0.6.0`, `git push origin tag v1`, `git push origin v0.6.0`.
- Formas alternativas que não casam nenhuma lista: `git -C . tag v1`, `gh pr -R o/r merge 34` e
  `gh api repos/o/r/rulesets`. No modo default, o Claude Code pede confirmação (Bash fora do `allow` e fora dos
  read-only). No auto mode quem decide é o classificador, e no `bypassPermissions` nada pergunta. O doc oficial diz isso
  da regra `ask`: "isn't a security boundary around the program". É o limite que a AD-053 aceitou.
- Sonda no `claude` real (2.1.312), num clone de rascunho sem remoto: `claude -p --permission-mode default` pediu
  `cd . && git tag v0.0.0-verifier-probe`. A resposta foi bloqueada ("Claude requested permissions to use Bash, but you
  haven't granted it yet"), e a tag não foi criada. A sonda bate com o `ask`, mas não discrimina: em `-p` sem `allow`,
  qualquer Bash que não é read-only também seria bloqueado. Ela mostrou mais uma coisa: num workspace sem a confiança
  aceita, o Claude Code ignora as 2 regras `allow` do projeto (aviso no stderr), mas não as `ask`. Isso só pesa para a
  autonomia, não para os gates.

## Gate

`verified at eaa574f`:

- `uv run pytest -rA -p no:cacheprovider` na worktree de rascunho em `eaa574f`, com o relatório PASS da rodada 2 no
  lugar: `989 passed, 50 deselected in 202.25s`, exit `0`.
- Com este relatório copiado para a worktree de rascunho: `uv run pytest -rA -p no:cacheprovider tests/test_sdlc.py -k
  spec_plan_doc_criterion` -> `PASSED tests/test_sdlc.py::test_spec_plan_doc_criterion`, `1 passed`.
- Reprodução do job `process` em `eaa574f` (C25): `uv run python tools/sdlc.py pr --title "feat(sdlc): gates do fluxo
  de desenvolvimento conferidos por máquina" --branch feat/31/sdlc-gates --body-file <corpo atual do PR 34> --base
  15398f38d4fa742178e914debf5e2d231f08eb82`: exit `0` com o relatório da rodada 2 e exit `0` com este.
- `gh pr checks 34`: os 6 `SUCCESS`, no head `df8b3a4` do PR (push pendente).
- C30: exit `0` (`true true false false`).
- `python3 .claude/skills/tlc-spec-lean/scripts/validate_verification.py sdlc-gates --root docs`: exit `0`.

## Ranked gaps

Nenhum bloqueia o merge. Medidos pelo risco ao contrato (o agente não faz merge, tag, release nem mudança de proteção
sem o Rodrigo confirmar, e não põe código na `main` sem PR):

1. **N2 - criar ou apagar uma tag `v*` por refspec não pede confirmação** (contrato "tag"; AC 20 cumprida na letra).
   `git push origin HEAD:refs/tags/v9.9.9`, `git push origin :v0.6.0`, `git push origin :refs/tags/v0.6.0` e
   `git push --mirror` casam `Bash(git push *)` (`.claude/settings.json:27`) e nenhuma regra de `:31-42`. A tag `v*`
   dispara o `release.yml`. O job `build` roda, e o `publish` (PyPI e GitHub Release) espera aprovação no environment
   `pypi`, que tem o Rodrigo como revisor obrigatório (conferido ao vivo: `protection_rules` `required_reviewers`
   `rodrigo-pasini`). Não há ruleset de tag (`gh api .../rulesets` vazio). O pior caso é uma tag criada ou apagada no
   GitHub, recuperável pelo clone local, sem publicação. Correção barata, recomendada neste PR: acrescentar ao `ask`
   `Bash(git push *:refs/tags/*)`, `Bash(git push * :*)` e `Bash(git push *--mirror*)`, e ao C27 e ao
   `test_settings_permissions_ask_covers` os três comandos. Não bloqueio porque o release, que é o que a AD-050 protege,
   continua com o Rodrigo.
2. **N1 - o `pre-push` só confere o primeiro ref** (AC 21 diz mais do que a primeira barreira entrega).
   `git push origin feat/31/x main` põe `main` num remoto sem proteção. O `entry` em `.pre-commit-config.yaml:48` só vê
   o `PRE_COMMIT_REMOTE_BRANCH` que o `pre-commit` escolhe (o primeiro ref com commits). No GitHub, a proteção da `main`
   (C30, `enforce_admins` ligado, PR obrigatório) rejeita esse push, como rejeita o `--no-verify`. Então "código na
   `main` sem PR" não acontece no repositório real. É lacuna de precisão da AC 21 e da C28, que prova só as formas de
   um ref. Saídas: reescrever a AC 21 dizendo que o `pre-push` cobre o push de um ref e que a proteção é a barreira
   final, ou trocar o `entry` por um hook que leia todas as linhas do stdin do `pre-push`. Não bloqueia.
3. **N3 - as provas da door 6 param antes do Claude Code real.** C27 e C29 provam o literal do `settings.json` e o
   casamento por uma réplica do algoritmo do doc (`tests/test_claude_hooks.py:52-59`). Se o Claude Code casasse de
   outro jeito, as provas seguiriam verdes. A sonda no `claude` real bate, mas não discrimina. Formas alternativas
   (`git -C . tag`, `gh pr -R o/r merge`) dependem do modo de permissão, o limite que a AD-053 aceitou. Não bloqueia.
4. **N4 - o corpo do PR #34 ainda descreve o `gate-humano.sh` como vivo** (linha 10: "push para `main` negado"). Precisa
   ser atualizado no push que fecha a C25. Junto com ele: o texto residual do `## Test policy` e do `## Handoff` do
   `checks.md` (ver `## Coverage`). Não bloqueia.

C25 segue como **push pendente**: o head do PR é `df8b3a4`, 16 commits atrás de `eaa574f`, e o CI tem de ficar verde de
novo depois do push.
