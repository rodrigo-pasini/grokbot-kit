# sdlc-gates checks

Profile: standard
Plan: `docs/.specs/features/sdlc-gates/plan.md`

74 checks em 8 slices · 9 one-way doors · 0 open

Convenções das provas:

- `uv run pytest <arquivo> -k <nome>` roda no CI. As provas do `tools/sdlc.py` rodam o script como subprocesso
  (`python3 tools/sdlc.py ...`) contra um repositório git criado em `tmp_path` (commits, branches e arquivos de feature
  montados pelo teste), e as dos hooks do Claude Code alimentam o script com o JSON de `PreToolUse`/`SessionStart` em
  stdin.
- Prova de shell: o comando inteiro, que sai com `0` exatamente quando o check vale.
- Prova `manual (host de dev)`: roda uma vez no host de dev com o `claude` real; a saída vai para
  `docs/.specs/features/sdlc-gates/evidence/`.
- Seguem verdes, sem mudança de asserção além das duas emendas da AD-052 (C47), `tests/test_docs.py`,
  `tests/test_repo_files.py` e `tests/test_workflows.py` inteiros.

## Checks

### S1 - as regras de commit e branch falham no clone · 5 arquivos · ~25 KB · ~7k

**C1** - O `.pre-commit-config.yaml` declara `default_install_hook_types: [pre-commit, commit-msg, pre-push]`, e `uv run pre-commit install` num clone de teste cria `.git/hooks/pre-commit`, `.git/hooks/commit-msg` e `.git/hooks/pre-push` (AC 1)
Proof: `uv run pytest tests/test_sdlc.py -k precommit_installs_three_hook_types`

**C2** - Os hooks locais novos (`sdlc-pre-commit`, `sdlc-commit-msg`, `sdlc-pre-push`) chamam `tools/sdlc.py` nas stages `pre-commit`, `commit-msg` e `pre-push` e levam o mesmo `exclude` dos outros hooks (AC 1, door 1)
Proof: `uv run pytest tests/test_repo_files.py -k "precommit_hooks or sdlc_hooks_stages"`

**C3** - `tools/sdlc.py commit-msg <arquivo>` sai com `0` sem saída para cada um dos 11 tipos da door 3 (`feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`, `build`, `ci`, `style`, `revert`), com e sem escopo e com `!`, e para uma primeira linha de exatamente 100 caracteres (AC 4, door 3)
Proof: `uv run pytest tests/test_sdlc.py -k commit_msg_accepts`

**C4** - `tools/sdlc.py commit-msg` sai com `1` e imprime a regex da door 3 em stderr para `ajusta coisa`, `Feat: x`, `feat(Run): x`, `feat:x`, `feat: ` e uma primeira linha de 101 caracteres (AC 2, door 3)
Proof: `uv run pytest tests/test_sdlc.py -k commit_msg_rejects`

**C5** - `tools/sdlc.py commit-msg` sai com `1` e imprime a linha em stderr quando a mensagem tem `Co-Authored-By: X <x@y>`, `co-authored-by: X` ou `CO-AUTHORED-BY: X` em qualquer linha depois da primeira (AC 3)
Proof: `uv run pytest tests/test_sdlc.py -k commit_msg_coauthor`

**C6** - `tools/sdlc.py branch` sai com `0` para `feat/31/sdlc-gates`, `chore/release/0.6.0` e `dependabot/uv/ruff-0.17.3`, e sai com `1` imprimindo os três padrões da door 2 para `feat/sdlc-gates`, `feat/S3/x`, `feature/31/x`, `feat/31/Sdlc`, `chore/release/0.6` e `main` (AC 5, door 2)
Proof: `uv run pytest tests/test_sdlc.py -k branch_pattern`

**C7** - Num clone de teste com os hooks instalados, `git push` de uma branch `feat/sdlc` para um remoto local é recusado com exit diferente de `0` e o remoto não recebe a branch; `feat/31/sdlc` chega ao remoto (AC 5)
Proof: `uv run pytest tests/test_sdlc.py -k pre_push_hook_blocks`

**C8** - `tools/sdlc.py pre-commit` com a branch atual `main` sai com `1` e imprime `commit on main: create a <type>/<issue>/<slug> branch` (AC 6)
Proof: `uv run pytest tests/test_sdlc.py -k pre_commit_on_main`

**C9** - No clone principal de teste, numa branch da door 2, `tools/sdlc.py pre-commit` com `src/x.py` e `tests/t.py` staged sai com `1` listando os dois; com só `docs/a.md`, `.claude/b`, `.agents/c`, `.specs/d`, `CLAUDE.md` e `AGENTS.md` staged sai com `0`; numa worktree linkada do mesmo repositório, com `src/x.py` staged, sai com `0` (AC 7)
Proof: `uv run pytest tests/test_sdlc.py -k pre_commit_main_clone`

**C10** - Com `GROKBOT_KIT_ALLOW_MAIN_EDIT=1`, o caso de `src/x.py` staged do C9 sai com `0`; o caso de `main` do C8 continua saindo com `1` (AC 8)
Proof: `uv run pytest tests/test_sdlc.py -k pre_commit_allow_main_edit`

**C11** - `tools/sdlc.py` sem subcomando ou com subcomando desconhecido sai com `2` e imprime o uso em stderr (door 1)
Proof: `uv run pytest tests/test_sdlc.py -k usage_exit_2`

### S2 - o CI recusa um PR fora do processo · 5 arquivos · ~30 KB · ~8k

**C12** - O `ci.yml` tem o job `process` com `name: process`, disparado em `pull_request` com `types` `opened`, `edited`, `synchronize` e `reopened`, `actions/checkout` com `fetch-depth: 0`, e um passo que roda `tools/sdlc.py pr` com `--base` igual ao SHA base do PR (AC 10, door 4)
Proof: `uv run pytest tests/test_workflows.py -k process_job`

**C13** - No job `process`, o título, a branch e o corpo do PR chegam ao `run` só por `env:` (nenhum `${{ github.event.pull_request.title }}`, `...body` ou `github.head_ref` dentro de um `run:`) (AC 10)
Proof: `uv run pytest tests/test_workflows.py -k process_job_no_expression_in_run`

**C14** - `tools/sdlc.py pr` sai com `1` nomeando o título para o título `ajusta coisa`, e com `0` para `feat(ci): job process` com o resto do PR em dia (AC 11)
Proof: `uv run pytest tests/test_sdlc.py -k pr_title`

**C15** - `tools/sdlc.py pr --branch feat/sdlc` sai com `1` nomeando a branch (AC 12)
Proof: `uv run pytest tests/test_sdlc.py -k pr_branch`

**C16** - `tools/sdlc.py pr` sai com `1` nomeando o SHA quando um commit entre `--base` e `HEAD` tem `Co-authored-by:`, e com `1` nomeando o corpo quando é o corpo que tem (AC 13)
Proof: `uv run pytest tests/test_sdlc.py -k pr_coauthor`

**C17** - Com a branch `feat/31/x`, o corpo com `Closes #31`, `Fixes #31` ou `Refs #31` passa; sem nenhum, com `Closes #32` ou com `Closes #310`, `tools/sdlc.py pr` sai com `1`; com a branch `dependabot/uv/x` ou `chore/release/0.6.0`, o corpo sem link passa (AC 14, door 7)
Proof: `uv run pytest tests/test_sdlc.py -k pr_issue_link`

**C18** - `tools/sdlc.py spec <f>` roda `validate_plan.py`, `validate_checks.py` e `validate_verification.py` com `--root docs` só para os arquivos presentes em `docs/.specs/features/<f>/`; com um `checks.md` sem `Profile:` sai com `1` nomeando `validate_checks.py`, e com os três válidos sai com `0` (AC 15)
Proof: `uv run pytest tests/test_sdlc.py -k spec_runs_validators`

**C19** - Com dois validadores falhando, `tools/sdlc.py spec <f>` nomeia os dois em stderr (não para no primeiro) e sai com `1` (AC 15)
Proof: `uv run pytest tests/test_sdlc.py -k spec_reports_every_failure`

**C20** - `tools/sdlc.py pr` roda `spec <f>` para cada feature `<f>` com arquivo mudado no PR, e só para elas: uma feature intocada com `checks.md` inválido não reprova o PR (AC 15)
Proof: `uv run pytest tests/test_sdlc.py -k pr_specs_of_touched_features`

**C21** - Um PR que muda `src/a.py` ou `skills/b.md` sem mudar nenhum `docs/.specs/features/*/verification.md` sai com `1` e imprime `src/ or skills/ changed without a verification.md`; mudando um `verification.md` válido, passa; um PR que muda só `pyproject.toml`, `uv.lock` e `CHANGELOG.md` passa (AC 16)
Proof: `uv run pytest tests/test_sdlc.py -k pr_requires_verification`

**C22** - Um PR que adiciona ou altera um `plan.md` sem a linha `**Approved**: AAAA-MM-DD` logo abaixo do título sai com `1`; com `**Approved**: 2026-10-29`, passa; com `**Approved**: amanhã`, sai com `1`; um `plan.md` sem a linha e não tocado pelo PR não reprova (AC 17, door 5)
Proof: `uv run pytest tests/test_sdlc.py -k pr_plan_approved`

**C23** - `tools/sdlc.py state` sai com `0` com um `## Handoff` de 40 linhas e com `1` com 41 (contadas do título da seção até o próximo `## ` ou o fim), e `tools/sdlc.py pr` reprova com o `STATE.md` de 41 (AC 18)
Proof: `uv run pytest tests/test_sdlc.py -k state_handoff_limit`

**C24** - O `.github/repo-settings/main-protection.json` tem 6 checks em `required_status_checks.checks`, os 5 de hoje e `{"context": "process", "app_id": 15368}`, e o resto do payload igual ao da door 11 (AC 19, door 4)
Proof: `uv run pytest tests/test_repo_files.py -k repo_settings_payloads`

**C25** - O próprio PR desta feature passa no job `process` do CI (AC 10-18)
Proof: `gh pr checks "$(gh pr list --head "$(git branch --show-current)" --json number --jq '.[0].number')" --json name,state --jq '.[] | select(.name=="process") | .state' | grep -qx SUCCESS`

### S3 - o agente faz push e abre PR, e para no merge e na tag · 3 arquivos · ~12 KB · ~3k

**C26** - O `.claude/settings.json` registra `.claude/hooks/gate-humano.sh` em `PreToolUse` com `matcher` `Bash`, e mantém o `gate-worktree.sh` em `Edit|Write|MultiEdit|NotebookEdit` (AC 20-23, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k settings_registers_hooks`

**C27** - `gate-humano.sh` devolve `hookSpecificOutput.permissionDecision` `ask` com `permissionDecisionReason` não vazio para `gh pr merge 30 --squash`, `git tag v0.6.0`, `git push origin v0.6.0`, `git push --tags`, `gh release create v0.6.0` e `gh api -X PUT repos/o/r/branches/main/protection`, `gh api repos/o/r/environments/pypi` (AC 20, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_ask`

**C28** - `gate-humano.sh` devolve `deny` para `git push origin main`, `git push origin HEAD:main` e, num repositório de teste com a branch atual `main`, `git push`; e para um comando composto `git status && git push origin main` (AC 21, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_deny`

**C29** - `gate-humano.sh` devolve `allow` para `git push -u origin feat/31/sdlc-gates` e `gh pr create --title "feat(ci): x" --body-file b.md`, e não devolve `allow` para `git push -u origin feat/sdlc` (AC 22, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_allow`

**C30** - `gate-humano.sh` sai com `0` e stdout vazio para `git status`, `uv run pytest` e `gh pr view 30` (AC 23)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_neutral`

### S4 - o backlog vive em GitHub Issues · 2 arquivos · ~40 KB · ~10k

**C31** - O `.claude/worktree-handoff.json` tem `branch_pattern` `<tipo>/<issue>/<slug>` e `handoff_skill` `tlc-spec-lean` (AC 24)
Proof: `uv run pytest tests/test_repo_files.py -k worktree_handoff_config`

**C32** - Existem issues abertos no `rodrigo-pasini/grokbot-kit` para os limites do webhook e para o sandbox do Codex no box (AC 25)
Proof: `test "$(gh issue list --repo rodrigo-pasini/grokbot-kit --state open --search 'in:title webhook' --json number --jq length)" -ge 1 && test "$(gh issue list --repo rodrigo-pasini/grokbot-kit --state open --search 'in:title sandbox codex' --json number --jq length)" -ge 1`

**C33** - O `## Handoff` do `STATE.md` cita as duas pendências só como `#<n>` e não tem mais as palavras `bwrap` nem `limites do webhook` (AC 25)
Proof: `uv run pytest tests/test_repo_files.py -k state_handoff_cites_issues`

### S5 - as regras do fluxo estão num lugar só · 4 arquivos · ~30 KB · ~8k

**C34** - O `AGENTS.md` tem as seções `## Fluxo`, `## Autonomia`, `## Skills` e `## Ambiente`; `## Autonomia` tem uma tabela cuja coluna do Rodrigo lista exatamente aprovar o plano, merge e tag (AC 26)
Proof: `uv run pytest tests/test_agents_md.py -k sections_and_autonomy`

**C35** - A seção `## Skills` do `AGENTS.md` cita `tlc-spec-lean`, `tlc-discover`, `## Intent` e `tools/sdlc.py spec`, e `## Ambiente` cita o box só pelo bot e `opencode-go` (AC 26)
Proof: `uv run pytest tests/test_agents_md.py -k skills_and_environment`

**C36** - O `AGENTS.md` tem o gate da worktree (`gate-worktree.sh`, `GROKBOT_KIT_ALLOW_MAIN_EDIT=1`), as skills do projeto com o commit `508cc3e`, a regra de não pôr `Co-Authored-By` e o `profile: standard` / `budget: 150k` do `tlc-spec-lean` (AC 27)
Proof: `uv run pytest tests/test_agents_md.py -k carries_former_claude_md`

**C37** - O `CONTRIBUTING.md` e o `docs/pt-BR/CONTRIBUTING.md` citam `commit-msg`, `pre-push`, o job `process`, o padrão `<type>/<issue>/<slug>` (pt-BR: `<tipo>/<issue>/<slug>`) e `Closes #` (AC 28)
Proof: `uv run pytest tests/test_docs.py -k contributing_gates`

**C38** - `tools/sdlc.py state` sai com `0` contra o `docs/.specs/STATE.md` do repositório (AC 29)
Proof: `uv run pytest tests/test_repo_files.py -k state_handoff_within_limit` (roda `python3 tools/sdlc.py state` contra o repositório)

### S6 - um só arquivo de instruções · 6 arquivos · ~30 KB · ~8k

**C39** - `git ls-files CLAUDE.md .claude/CLAUDE.md CLAUDE.local.md` não lista nada (AC 30, door 8)
Proof: `uv run pytest tests/test_repo_files.py -k no_claude_md_tracked`

**C40** - O `copy` do `.claude/worktree-handoff.json` não tem `CLAUDE.local.md` (AC 31)
Proof: `uv run pytest tests/test_repo_files.py -k worktree_handoff_config`

**C41** - O hook de início de sessão (`.claude/hooks/session-start.sh`, registrado em `SessionStart` no `.claude/settings.json`), num repositório de teste sem `.git/hooks/commit-msg`, roda `uv run pre-commit install` (stub no `PATH` que registra a chamada) e devolve em `hookSpecificOutput.additionalContext` uma linha com o resultado; com o hook já presente, não chama o stub (AC 9)
Proof: `uv run pytest tests/test_claude_hooks.py -k session_start_installs_hooks`

**C42** - O mesmo hook, com `CLAUDE.md` ou com `CLAUDE.local.md` na raiz do repositório de teste, devolve em `additionalContext` a linha `CLAUDE.md or CLAUDE.local.md found: AGENTS.md is not loaded; move its content to AGENTS.md`; sem os dois, a linha não aparece (AC 32)
Proof: `uv run pytest tests/test_claude_hooks.py -k session_start_warns_claude_md`

**C43** - O hook de início de sessão sai com `0` mesmo quando o `uv run pre-commit install` falha (stub com exit `1`), e a linha diz que falhou (AC 9)
Proof: `uv run pytest tests/test_claude_hooks.py -k session_start_install_failure`

**C44** - O `CONTRIBUTING.md` e o `docs/pt-BR/CONTRIBUTING.md` citam `AGENTS.md`, `2.1.277` e `CLAUDE.local.md` (AC 33)
Proof: `uv run pytest tests/test_docs.py -k contributing_agents_md`

**C45** - Uma sessão nova do `claude` real na raiz do repositório carrega o `AGENTS.md`: `claude -p "Qual o budget do tlc-spec-lean neste projeto? Responda só o valor."` responde `150k` (AC 30, door 8)
Proof: manual (host de dev): `claude -p "Qual o budget do tlc-spec-lean neste projeto? Responda só o valor." | grep -q 150k`, saída em `evidence/c45.txt`

**C46** - `DOOR_10_FILES` em `tests/test_repo_files.py` tem `AGENTS.md` e não tem `CLAUDE.md` (AC 34)
Proof: `uv run pytest tests/test_repo_files.py -k door_10_tree_files`

**C47** - A prova C48 da model-setup-docs lê a regra de doc do `AGENTS.md` (`test_agents_md_doc_rule`), com as mesmas asserções de `README.md`, inglês, pt-BR e `critério de doc` (AC 34)
Proof: `uv run pytest tests/test_docs.py -k agents_md_doc_rule`

### S7 - a doc é cobrada por máquina · 10 arquivos · ~70 KB · ~18k

**C48** - O `AGENTS.md` tem `## Documentação` com `docs/pt-BR/`, `mesmo commit`, `CHANGELOG.md`, `## [Unreleased]`, `docs/plugins.md`, a doc do evento e `Docs: n/a -` (AC 35, door 9)
Proof: `uv run pytest tests/test_agents_md.py -k documentation_section`

**C49** - O checador do `tests/test_docs.py` acusa `run --timeout` quando a opção some só do `README.md` e dos `docs/*.md` (cópia em `tmp_path`), e acusa `run --timeout` quando some só dos `docs/pt-BR/*.md`; contra o repositório, todas as opções longas de todos os subcomandos (menos `--help`) aparecem nas duas línguas (AC 36)
Proof: `uv run pytest tests/test_docs.py -k "gate_reports_missing_flag or gate_flags_repo_clean"`

**C50** - O checador acusa `exit_code` quando o campo some dos docs em inglês e quando some dos em pt-BR; contra o repositório, os 26 campos de `properties` do `event.v1.json` aparecem entre crases nas duas línguas (AC 37)
Proof: `uv run pytest tests/test_docs.py -k "gate_reports_missing_event_field or gate_event_fields_repo_clean"`

**C51** - O checador acusa `docs/x.md:3` para um link `[a](nao-existe.md)` na linha 3 de um doc de teste, ignora `http(s)://` e âncoras `#`, e não acusa nada contra o repositório (AC 38)
Proof: `uv run pytest tests/test_docs.py -k "gate_reports_broken_link or gate_links_repo_clean"`

**C52** - `tools/sdlc.py pr` sai com `1` nomeando `README.md` e `docs/pt-BR/README.md` quando o PR muda só o primeiro, e também quando muda só o segundo; passa quando muda os dois (AC 39)
Proof: `uv run pytest tests/test_sdlc.py -k pr_doc_pair`

**C53** - Um PR `feat` ou `fix` que muda `src/` sem mudar a seção `## [Unreleased]` do `CHANGELOG.md` sai com `1` (inclusive quando muda só uma seção de versão antiga); um PR `refactor` ou `chore` com a mesma mudança passa (AC 40)
Proof: `uv run pytest tests/test_sdlc.py -k pr_changelog_unreleased`

**C54** - Um PR `feat` ou `fix` que muda `src/` sem mudar `README.md` nem `docs/*.md` sai com `1`; com a linha `Docs: n/a - só refatora o parser` no corpo, passa; com `Docs: n/a - ` (razão vazia), sai com `1` (AC 41, door 9)
Proof: `uv run pytest tests/test_sdlc.py -k pr_docs_or_na`

**C55** - `tools/sdlc.py spec <f>` sai com `1` para um `plan.md` cujo `## Criteria` não cita `README.md` nem `docs/` e que não tem `Docs: n/a - <razão>`; passa com um dos dois; e passa contra o `plan.md` desta feature (AC 42, door 9)
Proof: `uv run pytest tests/test_sdlc.py -k spec_plan_doc_criterion`

**C56** - O item de doc do `.github/pull_request_template.md` tem `README.md`, `docs`, `pt-BR` e `Docs: n/a - <reason>` (AC 43)
Proof: `uv run pytest tests/test_docs.py -k pr_template_doc_item`

### S8 - achados do review do PR #34 · 4 arquivos · ~25 KB · ~7k

**C57** - `gate-humano.sh` devolve `deny` para `git push origin "main"`, `git push origin 'HEAD:main'`, `GIT_DIR=.git git push origin main`, `env git push origin main`, `command git push origin main` e `/usr/bin/git push origin main` (AC 44, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_deny_disguised`

**C58** - `gate-humano.sh` devolve `ask` para `git push origin $(echo main)`, ``git push origin `echo main` ``, `bash -c "git push origin main"`, `sudo git push origin main` e `xargs gh pr merge`, e segue sem saída para `git status`, `uv run pytest` e `gh pr view 30` (AC 45, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k "gate_humano_ask_unparsed or gate_humano_neutral"`

**C59** - `tools/sdlc.py commit-msg` sai com `0` sem saída para `Merge branch 'main' into feat/31/x`, `Merge branch 'main' of github.com:o/r into feat/31/x`, `Merge branches 'a' and 'b'`, `Merge remote-tracking branch 'origin/main' into feat/31/x`, `Merge tag 'v0.6.0'` e `Merge commit 'abc123'`; sai com `1` para `Merge stuff` e para um merge com linha `Co-authored-by:`; e `tools/sdlc.py pr --title "Merge branch 'main'"` sai com `1` (AC 46, door 3)
Proof: `uv run pytest tests/test_sdlc.py -k "commit_msg_merge or pr_title_merge"`

**C60** - `gate-humano.sh` devolve `ask` para `sudo git tag v1`, `bash -c "gh release create v1"` e `xargs gh api repos/o/r/branches/main/protection` (AC 45, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_ask_unparsed_verbs`

**C61** - `gate-humano.sh` não devolve `allow` para `GIT_DIR=x/.git git push origin HEAD`, `GIT_WORK_TREE=x git push origin feat/31/x`, `git -C x push origin HEAD`, `git --git-dir=x/.git push origin feat/31/x` e `git --work-tree=x push origin feat/31/x`, e devolve `deny` para `git -C x push origin main` (AC 47, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_other_repo`

**C62** - `gate-humano.sh` sai com `0` e stdout vazio para `git commit -m "fix: a; git push origin main"`, `git commit -m "docs: gate | git tag"` e `git commit -m 'a && git push origin main'`, e segue devolvendo `deny` para `git status && git push origin main` (AC 48, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_quoted_separators`

**C63** - `gate-humano.sh` devolve `deny` para `\git push origin main`, `git push origin ma\in`, `(git push origin main)`, `(cd x && git push origin main)` e `git push origin main&` (AC 49, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_deny_escaped`

**C64** - `gate-humano.sh` devolve `ask` para `echo $(git push origin main)`, `x=$(git push origin main)` e ``echo `git push origin main` `` (AC 50, door 6; era `deny` até a rodada 6, quando a AC 50 passou a falhar fechado com `ask`)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_substitution`

**C65** - `gate-humano.sh` sai sem saída para `git commit -m "a || git push origin main"` e `git commit -m "a & git push origin main"`, e devolve `deny` para `git commit -m \" ; git push origin main` (aspas escapadas não abrem aspas) (AC 48, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_quoted_more`

**C66** - `gate-humano.sh` devolve `deny` para `git --git-dir x/.git push origin main`, `git --work-tree x push origin main` e `git --namespace n push origin main`; não devolve `allow` para `git --git-dir x/.git push origin feat/31/x`; e devolve `ask` para `git -c alias.p=push p origin main` (AC 51, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_spaced_options`

**C67** - `gate-humano.sh` devolve `ask` para `git push --follow-tags origin feat/31/x`, `git push --tags origin main` não sai mais fraco que `deny`, `gh pr -R o/r merge 34`, `gh api -X PUT repos/o/r/pulls/34/merge`, `gh api repos/o/r/releases` e `gh api -X DELETE repos/o/r/git/refs/heads/x`; e não devolve `allow` para `git push -uf origin feat/31/x` (AC 52, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_more_ask`

**C68** - `gate-humano.sh` devolve `deny` para `git -C $(pwd) push origin main`, `git push $(git remote) main`, `git push $(echo origin) main` e `git push origin $(true) main`; e `ask` para ``x=`git push origin main` ``, `git commit -m "$(git push origin main)"`, ``git commit -m "`git push origin main`"``, `echo $(echo $(git push origin main))`, `echo $(git push origin main $(true))`, `echo $(git push origin main; echo $(date))`, ``echo `echo $(git push origin main)` `` e `x=$(git push origin "$(echo main)")` (AC 53, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_substitution_args`

**C69** - `gate-humano.sh` devolve `deny` para `git --config-env core.x=Y push origin main`; não devolve `allow` para `git --namespace=n push origin feat/31/x` nem para `git push -ud origin feat/31/x`; devolve `ask` para `gh pr --repo o/r merge 34`, `git -c Alias.p=push p origin main`, `git --config-env alias.p=X p origin main` e `gh api graphql -f query=mutation{mergePullRequest}` (AC 51, 52, 54, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_round5`

**C70** - `gate-humano.sh` não devolve `deny` para ``git commit -m 'fix: `git push origin main` x'``, `rg -n '$(git push origin main)' docs` e um `git commit -F -` com heredoc `<<'EOF'` cujo texto cita `git push origin main`; e devolve `ask` para `git --config-env=alias.p=X p origin main` e `gh api graphql -f query=mutation{enablePullRequestAutoMerge}` (AC 55, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_round6`

**C71** - `gate-humano.sh` sai com `0` e stdout vazio para um `printf` com texto entre aspas simples que cita `git push origin main` e `gh pr merge` seguido de `git commit -q -F`, para `gh issue comment 35 --body "cita git push e gh release"`, para `cat > f.md <<'EOF'` com corpo que cita `git push origin main`, para `git push -u origin feat/31/x 2>&1 | tail -3`, para `gh pr create` com `--body "$(cat <<'EOF' ... EOF)"` cujo corpo cita `git push` e `merge`, e para `grep -rn "git push" docs`; e devolve `ask` para `bash <<'EOF'` com `git push origin main` no corpo e para `printf 'git push origin main' | sh` (AC 56, AC 53, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_autonomy`

**C72** - `gate-humano.sh` devolve `deny` para um `git push origin main` depois de `cat <<E'OF'` sem linha de fim, de `cat <<"E"OF` ... `EOF`, de `cat <<END-X` ... `END-X`, de `cat <<END.X` ... `END.X`, de `echo $((1<<2))` e de `(( x = 1 << 2 ))` (AC 57, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_heredoc_end`

**C73** - `gate-humano.sh` sai sem saída para `git commit -m` com texto de várias linhas entre aspas simples, entre aspas duplas e num `"$(cat <<'EOF' ... EOF)"` em que uma linha é `git push origin main`, `gh pr merge 34` ou `git tag v1`; devolve `deny` para `echo "a` + quebra + `b" && git push origin main` e, com a branch atual `main`, para `git push origin 2>/dev/null`; e devolve `ask` para `echo "$(echo ")"; git push origin main)"`, `printf 'git push origin main' | "$SHELL"`, `printf 'git push origin main' > x.sh && . ./x.sh` e `eval "git push origin main"` (AC 58, AC 53, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_multiline`

**C74** - `gate-humano.sh` devolve `deny` para `git push origin main>/dev/null`, `git push origin main>&2` e `git push origin HEAD:main>log`, e `ask` para `git push origin {main,}`, `git rebase -x "git push origin main" HEAD~1`, `git submodule foreach git push origin main` e `git bisect run sh -c "git push origin main"` (AC 59, door 6)
Proof: `uv run pytest tests/test_claude_hooks.py -k gate_humano_glued`

## Coverage

| Set (size) | Member -> proof | Unproven |
| --- | --- | --- |
| hook types instalados (3) | `pre-commit` C1 · `commit-msg` C1 · `pre-push` C1 | - |
| tipos da door 3 (11) | os 11 em C3, table-driven | - |
| rejeições da primeira linha (6) | sem tipo C4 · tipo em maiúscula C4 · escopo em maiúscula C4 · sem espaço C4 · descrição vazia C4 · 101 caracteres C4 | - |
| formas da door 2 (4) | `<tipo>/<n>/<slug>` C6 · `chore/release/<semver>` C6 · `dependabot/` C6 · recusa C6, C7 | - |
| regras do `pre-commit` (3) | `main` C8 · clone principal C9 · escape C10 | - |
| exit codes do `tools/sdlc.py` (3) | `0` C3 · `1` C4 · `2` C11 | - |
| regras do `pr` (12) | título C14 · branch C15 · coautor em commit C16 · coautor no corpo C16 · link do issue C17 · validadores C20 · `verification.md` C21 · `**Approved**` C22 · `Handoff` C23 · par de doc C52 · `CHANGELOG.md` C53 · doc ou `Docs: n/a` C54 | - |
| palavras do link (3) | `Closes` C17 · `Fixes` C17 · `Refs` C17 | - |
| validadores do `spec` (4) | `validate_plan` C18 · `validate_checks` C18 · `validate_verification` C18 · critério de doc C55 | - |
| decisões do `gate-humano.sh` (4) | `ask` C27 · `deny` C28 · `allow` C29 · nada C30 | - |
| comandos `ask` (6) | `gh pr merge` C27 · `git tag` C27 · push de tag C27 · `--tags` C27 · `gh release` C27 · `gh api` protection/environments C27 | - |
| disfarces de push para `main` (6) | aspas C57 · `HEAD:main` entre aspas C57 · `VAR=valor` C57 · `env` C57 · `command` C57 · caminho do binário C57 | - |
| comandos que o gate não lê (5) | `$(...)` C58 · crase C58 · `bash -c` C58 · `sudo` C58 · `xargs` C58 | - |
| verbos do ramo de falha fechada (5) | `push` C58 · `merge` C58 · `tag` C60 · `release` C60 · `api` C60 | - |
| redirecionamentos de repositório (5) | `GIT_DIR=` C61 · `GIT_WORK_TREE=` C61 · `-C` C61 · `--git-dir` C61 · `--work-tree` C61 | - |
| separadores dentro de aspas (3) | ponto e vírgula C62 · barra vertical C62 · `&&` C62 | - |
| escapes do comando (4) | barra invertida C63 · subshell C63 · segundo plano C63 · `cd` no subshell C63 | - |
| substituições (3) | `$( )` em `echo` C64 · `$( )` em atribuição C64 · crase C64 | - |
| opções com valor separado (4) | `--git-dir` C66 · `--work-tree` C66 · `--namespace` C66 · `-c alias.` C66 | - |
| pedidos novos de confirmação (6) | `--follow-tags` C67 · `--tags` com `main` C67 · `gh pr -R ... merge` C67 · `gh api .../merge` C67 · `gh api .../releases` C67 · `gh api .../git/refs` C67 | - |
| substituição nos argumentos do push (4) | `-C $(...)` C68 · remoto por `$(...)` C68 · remoto por `$(echo)` C68 · `$(true)` antes da ref C68 | - |
| substituição em outro lugar (8) | crase em atribuição C68 · `$( )` entre aspas C68 · crase entre aspas C68 · `$( )` aninhado C68 · `$( )` depois da ref C68 · `;` dentro do `$( )` C68 · `$( )` dentro de crase C68 · `$( )` entre aspas dentro de `$( )` C68 | - |
| texto que o bash não substitui (3) | aspas simples com crase C70 · aspas simples com `$( )` C70 · heredoc `'EOF'` C70 | - |
| texto citado sem ser executado (6) | `printf` com aspas simples C71 · `--body` com aspas duplas C71 · heredoc `'EOF'` C71 · push com redirecionamento e tail C71 · heredoc dentro de `$( )` C71 · `grep` com aspas duplas C71 | - |
| texto passado a um shell (2) | `bash <<'EOF'` C71 · printf para sh C71 | - |
| heredoc sem fim achado (6) | aspas no meio C72 · aspas no começo C72 · hífen C72 · ponto C72 · `$(( ))` C72 · `(( ))` C72 | - |
| texto de várias linhas (3) | aspas simples C73 · aspas duplas C73 · heredoc dentro de `$( )` C73 | - |
| redirecionamento e chaves no refspec (4) | `main>/dev/null` C74 · `main>&2` C74 · `HEAD:main>log` C74 · `{main,}` C74 | - |
| subcomandos que rodam shell (3) | `rebase -x` C74 · `submodule foreach` C74 · `bisect run` C74 | - |
| mensagens de merge do git (5) | `Merge branch` C59 · `Merge branches` C59 · `Merge remote-tracking branch` C59 · `Merge tag` C59 · `Merge commit` C59 | - |
| saídas do hook de sessão (4) | instala C41 · já instalado C41 · falha C43 · aviso `CLAUDE.md` C42 | - |
| seções do `AGENTS.md` (5) | `## Fluxo` C34 · `## Autonomia` C34 · `## Skills` C35 · `## Ambiente` C35 · `## Documentação` C48 | - |
| gates do `test_docs.py` novos (3) | flags C49 · campos do evento C50 · links C51 | - |
| doors (9) | 1 C2, C11 · 2 C6 · 3 C3, C4, C59 · 4 C12, C24 · 5 C22 · 6 C26-C30, C57, C58, C60-C74 · 7 C17 · 8 C39, C45 · 9 C48, C54, C55 | - |

- Checks que cruzam a fronteira real: C7 (push num remoto local), C25 (CI do GitHub), C32 (issues no GitHub), C45
  (sessão real do `claude`)
- Nenhum outro check afirma mais do que o caso que a prova exercita

## Test policy

Segue a do `CONTRIBUTING.md` (copiada da agent-run-notify), sem linha nova: o `tools/sdlc.py` decide e é alcançado por
uma fronteira (o hook git e o CI), então é provado como subprocesso contra um repositório git de teste, um caso por
linha das tabelas de decisão (`pr`: 12 regras; `branch`: 4 formas; `pre-commit`: 3 regras). Os dois hooks do Claude
Code decidem e são alcançados pelo JSON em stdin: provados assim, um caso por decisão.

## Swept

- validation: C3, C4, C6, C22 (formato da data), C54 (razão vazia)
- failure modes: C19 (todos os validadores que falharam aparecem), C43 (falha do install não derruba a sessão)
- idempotency: C41 (com o hook já instalado, não reinstala)
- authorization: C27, C28 (merge, tag, release e proteção ficam com o Rodrigo; push para `main` negado)
- concurrency: n/a - cada hook e o job `process` leem o estado do repositório uma vez, sem escrita compartilhada
- data lifecycle: C33, C38 (o `## Handoff` do `STATE.md` fica limitado a 40 linhas e as pendências saem para issues)
- dependency failure: C43 (`pre-commit` ausente ou falhando); o CI sem `gh` não é usado — o `pr` só lê o git e arquivos
- state transitions: C22 (plano aprovado antes do PR), C21 (feature com código só entra verificada)
- observability: C4, C15, C16, C19, C52 (cada falha nomeia a regra e o arquivo, commit ou corpo)

## Handoff

Tamanho, a partir de `wc -c`: arquivos lidos ou tocados que já existem somam ~110 KB (`cli.py`, os dois READMEs, os dois
`CONTRIBUTING.md`, `CLAUDE.md`, `AGENTS.md`, `STATE.md`, `ci.yml`, `test_docs.py`, `test_repo_files.py`,
`test_workflows.py`) ≈ 28k; os arquivos novos (`tools/sdlc.py`, `tests/test_sdlc.py`, `tests/test_claude_hooks.py`,
`tests/test_agents_md.py`, dois hooks, `docs/event.md` e o par) ≈ 25k. Total ~55k, sob o budget de 150k — um builder.

- Mechanism: one builder
