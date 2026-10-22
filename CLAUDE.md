# grokbot-kit

Kit de integração Grok Bot: delegar tarefas a agentes headless (opencode, Claude Code, Codex)
e acordar a routine do bot certo. Spec e decisões em `docs/` (`docs/SPEC.md` é cópia de leitura
gerada; os originais ficam em `docs/.specs/`).

## Gate de implementação (obrigatório)

**Antes de iniciar qualquer implementação, invoque a skill `delegar-em-worktree`.** Toda tarefa
de código roda numa worktree dedicada (`../worktrees/`, base `main`, branch `<tipo>/<id>/<slug>`);
o clone principal não recebe edição de código.

- O hook `.claude/hooks/gate-worktree.sh` (PreToolUse em Edit/Write) nega edições de código no
  clone principal. No clone principal só são editáveis `docs/`, `.specs/`, `.claude/`, `.agents/`,
  `CLAUDE.md` e `AGENTS.md`.
- Escrever arquivos via Bash não contorna o gate: é a mesma regra.
- Trabalho deliberado no clone principal: só com pedido explícito do usuário, rodando a sessão
  com `GROKBOT_KIT_ALLOW_MAIN_EDIT=1`.
- Config da skill: `.claude/worktree-handoff.json`.

## Skills do projeto

- `tlc-*` (tech-leads-club/agent-skills, spec-driven): instaladas por cópia; atualizar com
  `npx @tech-leads-club/agent-skills update` (lock em `.agents/.skill-lock.json`).
- `delegar-em-worktree`, `revisar-pr` (rodrigo-pasini/skills, commit `508cc3e`): cópia do repo.

## Idioma dos docs

- Todo doc para quem usa ou contribui com o projeto é escrito primeiro em inglês e tem a tradução em pt-BR em
  `docs/pt-BR/`, com o mesmo nome: `README.md` → `docs/pt-BR/README.md`, `docs/<doc>.md` → `docs/pt-BR/<doc>.md`.
  Logo abaixo do título, cada versão aponta para a outra (`Leia em português: ...` / `Read in English: ...`).
- Uma mudança num doc atualiza as duas versões no mesmo commit.
- Fora da regra: `docs/.specs/` (specs e decisões, em pt-BR), `CLAUDE.md`, `AGENTS.md`, o `CHANGELOG.md` (só em
  inglês) e o que o kit entrega ao bot (`skills/grokbot-kit/SKILL.md` e os prompts e skills dos plugins próprios),
  que seguem a língua do bot.
- Pendente: `CONTRIBUTING.md` existe só em pt-BR.

## Git

- Branch padrão `main`. Nunca adicionar `Co-Authored-By` nos commits.
