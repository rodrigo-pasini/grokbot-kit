# grokbot-kit

Kit de integração Grok Bot: delega tarefas a agentes de código headless (opencode, Claude Code, Codex) e acorda a
routine do Grok Bot certo quando a tarefa termina ou precisa de uma permissão.

> Read in English: [README.md](../../README.md)

**Estado:** `0.x`. Os comandos abaixo funcionam; o schema de evento `grokbot-kit.event/v1` ainda pode mudar, sempre
com uma entrada no [CHANGELOG](../../CHANGELOG.md).

## O que é

Um Grok Bot que delega uma tarefa longa a um agente headless hiberna enquanto o agente roda, e nada o acorda. O
código de saída sozinho não diz se a tarefa foi feita, falhou ou parou num pedido de permissão.

O `grokbot-kit` embrulha a execução do agente (`grokbot-kit run`), escuta os hooks nativos de cada agente e envia
exatamente um evento terminal (`completed`, `error` ou `timeout`) - mais um `needs_input` quando o agente esbarra numa
permissão - ao webhook trigger da routine do bot que delegou. Os outros bots não são acordados.

## Instalação

```sh
uv tool install --managed-python grokbot-kit
```

`pipx install grokbot-kit` também funciona. Para testar o que está na `main` antes do release:

```sh
uv tool install --managed-python git+https://github.com/rodrigo-pasini/grokbot-kit
```

Requer Linux e Python 3.11 ou mais novo (o `uv` gerencia o interpretador). O pacote não tem dependências de runtime.

## Começo rápido

### Com um Grok Bot

Mande esta mensagem ao bot. Ele instala a [skill](#skill-do-grok-bot) e conduz o setup com você: o kit, as CLIs e o
login delas, a CLI padrão, os tiers de modelo e a routine que os eventos do bot acordam. Troque `meubot` por um nome
curto para o bot (letras, dígitos, `.`, `_` e `-`).

```text
Instale a skill grokbot-kit e faça o setup do grokbot-kit neste box:
1. Baixe https://raw.githubusercontent.com/rodrigo-pasini/grokbot-kit/v0.2.0/skills/grokbot-kit/SKILL.md
   para /home/box/agent-data/workflows/grokbot-kit/SKILL.md (crie o diretório).
2. Leia essa skill e siga a seção "Setup (primeira vez)" do começo ao fim, um passo de cada vez,
   pulando o que o `grokbot-kit doctor --json` mostrar como já feito. Use "meubot" como nome deste bot.
3. Nunca me peça um segredo (API key, URL ou key da routine) no chat: me diga o comando
   `grokbot-kit secret set` e eu rodo num terminal do box.
4. No fim, rode `grokbot-kit doctor --json` e resuma o resultado e os problemas.
```

A skill pede que você crie a routine no painel do Grok Bot, com webhook trigger e o prompt de routine que ela
fornece. Copie a URL e a key da routine do painel só para o terminal do box, nunca para o chat ou um print. Com o
setup pronto, peça uma tarefa pequena, como "renomeie as variáveis de x.py": o bot escolhe o tier `trivial`, avisa a
escolha, e o resultado chega pela routine.

### À mão

```sh
grokbot-kit setup cli add opencode
grokbot-kit setup default opencode
grokbot-kit secret set meubot-url
grokbot-kit secret set meubot-key
grokbot-kit route add meubot --url-secret meubot-url --key-secret meubot-key
grokbot-kit route test meubot
grokbot-kit run --target meubot --label renomear-vars -- "Renomeie as variáveis de x.py"
```

## Skill do Grok Bot

`skills/grokbot-kit/` é uma skill para qualquer Grok Bot. Copie a pasta para o diretório de workflows do bot e ele
consegue instalar o kit, instalar e logar nas CLIs que você escolher, criar a rota para a própria routine e delegar
tarefas escolhendo CLI e modelo.

## Configuração

O config fica em `~/.config/grokbot-kit/config.toml`: CLIs instaladas e a padrão, tiers de modelo (`trivial`,
`standard`, `complex`) por CLI, timeout por tier e uma rota por bot. Cada task guarda saída, logs e eventos em
`~/.grokbot-kit/tasks/<task_id>/` até o `grokbot-kit gc` removê-la.

## Segurança

- Segredos (URL e key da routine, API keys) são gravados com `grokbot-kit secret set` em `~/.secrets/grokbot-kit/`
  com modo `0600`, nunca no config e nunca colados num chat.
- O `grokbot-kit` nunca escreve um segredo em log, stdout, stderr ou evento.
- `~/.claude/settings.json` e `~/.codex/` nunca são modificados; o Codex roda num `CODEX_HOME` próprio.

## Contribuindo

Veja [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Licença

[MIT](../../LICENSE). Material de terceiros neste repositório está listado em [NOTICE](../../NOTICE).
