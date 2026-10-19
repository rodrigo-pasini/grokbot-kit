# Project state

## Decisions

| ID | Decision | Rationale | Status | Date |
| --- | --- | --- | --- | --- |
| AD-001 | Projeto próprio, focado em integração Grok Bot; `hellolib/agent-notify` e `anotifier` são só prior art | decisão do Rodrigo | active | 2026-10-18 |
| AD-002 | Nome do projeto `grokbot-kit` (executável, pacote, env `GROKBOT_KIT_*`, schema, skill, repo) | decisão do Rodrigo; aceita o risco da marca xAI | active | 2026-10-18 |
| AD-003 | v1 suporta as três CLIs por completo, inclusive `needs_input` ao vivo no Codex | decisão do Rodrigo | active | 2026-10-18 |
| AD-004 | Uma skill `grokbot-kit` faz parte da entrega e leva o kit para outros Grok Bots | decisão do Rodrigo | active | 2026-10-18 |
| AD-005 | A única interface Grok Bot usada é o webhook trigger de routine; nenhuma outra API é presumida | é a única verificada | active | 2026-10-18 |
| AD-006 | Eventos para routines usam `grokbot-kit.event/v1`; a partir do pacote `1.0.0`, só mudanças aditivas na versão; em `0.x`, mudança incompatível é permitida com aviso no `CHANGELOG.md` | routines dependem dos nomes dos campos (door 2); decisão do Rodrigo em 19/10/2026 de manter liberdade antes do 1.0 | active | 2026-10-19 |
| AD-007 | Uma rota por `target`; segredos só em arquivos `0600`, nunca no config, chat ou logs | box compartilhado entre bots (door 3) | active | 2026-10-19 |
| AD-008 | O wrapper é a fonte do evento terminal; hooks só emitem `needs_input` | exit 0 não é sucesso; agente que cai não dispara hook (door 5) | active | 2026-10-19 |
| AD-009 | Python ≥ 3.11, zero dependências de runtime, instalado com `uv tool install --managed-python` (ou `pipx`); `emit` só com stdlib e imports sob demanda | decisão do Rodrigo; ambiente isolado resolve o box compartilhado (door 6) | active | 2026-10-18 |
| AD-010 | Codex roda num `CODEX_HOME` próprio do kit; `~/.claude` e `~/.codex` do usuário nunca são tocados | hooks por execução sem rodar hooks não revisados do usuário (door 7) | active | 2026-10-18 |
| AD-011 | Ids de modelo só entram nos tiers vindos da descoberta de cada CLI | nunca inventar modelo | active | 2026-10-19 |
| AD-012 | Licença MIT | decisão do Rodrigo; simplicidade, patente irrelevante aqui (door 9) | active | 2026-10-18 |
| AD-013 | Timeout por tier: `trivial` 30 min, `standard` 2 h, `complex` 4 h; `--timeout` prevalece | decisão do Rodrigo | active | 2026-10-18 |
| AD-014 | Entrega com 3 tentativas (1 s, 4 s) e comando `grokbot-kit redeliver <task_id>` | decisão do Rodrigo | active | 2026-10-18 |
| AD-015 | `summary` com até 2000 caracteres | decisão do Rodrigo | active | 2026-10-18 |
| AD-016 | Plugin opencode global, inerte fora de uma task, com `uninstall`; testar `OPENCODE_CONFIG` no build e trocar se funcionar | decisão do Rodrigo | active | 2026-10-18 |
| AD-017 | Um `needs_input` por permissão distinta | decisão do Rodrigo | active | 2026-10-18 |
| AD-018 | Task dirs guardados; limpeza manual `grokbot-kit gc --older-than 30d` | decisão do Rodrigo | active | 2026-10-18 |
| AD-019 | Slice S0 (repositório e configuração inicial) vem antes de todo código | decisão do Rodrigo (door 10) | active | 2026-10-18 |
| AD-020 | Repo `rodrigo-pasini/grokbot-kit` público; README em inglês (+ pt-BR opcional); `uv_build`; `mypy --strict`; PyPI por trusted publishing; `main` com PR + CI e 0 aprovações; Dependabot | confirmado pelo Rodrigo | active | 2026-10-18 |
| AD-021 | Contrato do webhook de routine: `POST https://api2.cursor.sh/automations/webhook/<routine-uuid>` com `Authorization: Bearer crsr_…` (segredo guarda só a key), corpo JSON cru, `User-Agent: grokbot-kit/<versão>`; `200` com `runUuid` é o recibo gravado no task dir; `401` e outros 4xx não têm retry | probe de 18/10/2026 18:38 BRT (`webhook-probe/probe-20261018T183849.json`) | active | 2026-10-18 |
| AD-022 | O S0 é executado pelo agente local do Rodrigo com `gh` autenticado, na ordem: precondições → commit local → `gh repo create` sem auto-init → `gh repo edit` → push → CI verde → proteção (`PUT .../branches/main/protection`, `enforce_admins: true`) → alertas e updates de segurança → environment `pypi` (revisor `rodrigo-pasini`, só tags `v*`) → verificação | door 11; comandos conferidos no manual do `gh` 2.102.0 e na REST API | active | 2026-10-19 |
| AD-023 | O S0 parte do repositório local existente: histórico (`79f430f`, `0c3e4a2`) preservado, scaffold em commits novos integrados com `git merge --ff-only`; `.claude/` e `.agents/` continuam versionados e públicos, excluídos do ruff e do pre-commit, com `NOTICE` creditando as skills `tlc-*` (CC-BY-4.0) e o gate de worktree documentado no `CONTRIBUTING.md`; specs originais em `docs/.specs/`, cópia gerada `docs/SPEC.md` no `.gitignore` | decisão do Rodrigo em 19/10/2026 (revista no mesmo dia): gate e skills viajam com cada clone e são revisados por PR; sem reescrever histórico (door 10) | active | 2026-10-19 |
| AD-024 | Aprovação para criar o repositório público `rodrigo-pasini/grokbot-kit` e executar as etapas do S0 no GitHub (C24-C36, C40) | "pode" explícito do Rodrigo na sessão de build do S0, depois do ff-merge do scaffold em `main` (`6cc87fc`) e das precondições C24/C25 verdes (AC 1) | active | 2026-10-19 |

## Handoff

**Feature**: agent-run-notify
**Where**: CHECKS escritos em 19/10/2026 - `checks.md` com 145 checks (profile `standard`), `validate_checks.py` 0 erros; plano com 124 ACs (ACs 120-124: sinks `file`, `ntfy`, `slack`)
**In progress**: nada
**Next step**: build do S0 numa worktree (`delegar-em-worktree`), com um builder; etapas do S0 que mexem no GitHub (C24-C36, C40) esperam o "pode" explícito do Rodrigo; Rodrigo cria o pending publisher no PyPI antes da primeira tag; spike com login do Codex (pergunta 2); medir limites do webhook no build (pergunta 1)
**Blockers**: pergunta 2 bloqueia o AC 57 e condiciona a AD-003; a primeira tag `v*` espera o pending publisher do PyPI (passo humano, AC 37)
**Uncommitted**: repositório local `grokbot-kit` em `main` com `79f430f` e `0c3e4a2`, sem remote; `rodrigo-pasini/grokbot-kit` não existe; nada foi criado no GitHub nem no PyPI
**Branch**: `main` (só docs/specs; código do S0 vai numa worktree)
