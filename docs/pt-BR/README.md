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
1. Baixe https://github.com/rodrigo-pasini/grokbot-kit/releases/latest/download/SKILL.md (seguindo redirects)
   para /home/box/agent-data/workflows/grokbot-kit/SKILL.md (crie o diretório).
2. Leia essa skill e siga a seção "Setup (primeira vez)" do começo ao fim, um passo de cada vez,
   pulando o que o `grokbot-kit doctor --json` mostrar como já feito. Use "meubot" como nome deste bot.
3. Nunca me peça um segredo (API key, URL ou key da routine) no chat: leia você mesmo da routine
   ou me peça num campo mascarado de segredos, e passe pela entrada padrão do `grokbot-kit secret set`.
4. No fim, rode `grokbot-kit doctor --json` e resuma o resultado e os problemas.
```

O bot cria a routine, com webhook trigger e o prompt de routine da skill, ou pede que você a crie no painel do Grok
Bot. A URL e a key da routine ele lê sozinho ou pede uma a uma num campo mascarado de segredos, nunca no chat ou
num print. Com o setup pronto, peça uma tarefa pequena, como "renomeie as variáveis de x.py": o bot escolhe o tier `trivial`, avisa a
escolha, e o resultado chega pela routine.

<details>
<summary>Prints de um setup e de uma tarefa</summary>

**1. A mensagem e a escolha das CLIs**

![1. A mensagem e a escolha das CLIs](https://raw.githubusercontent.com/rodrigo-pasini/grokbot-kit/main/docs/images/quickstart/01-pedido-e-clis.png)

**2. opencode instalado, modelos gratuitos sem login**

![2. opencode instalado, modelos gratuitos sem login](https://raw.githubusercontent.com/rodrigo-pasini/grokbot-kit/main/docs/images/quickstart/02-login.png)

**3. Tiers de modelo e a routine criada pelo bot**

![3. Tiers de modelo e a routine criada pelo bot](https://raw.githubusercontent.com/rodrigo-pasini/grokbot-kit/main/docs/images/quickstart/03-tiers-e-routine.png)

**4. URL e key da routine pelo campo mascarado de segredos**

![4. URL e key da routine pelo campo mascarado de segredos](https://raw.githubusercontent.com/rodrigo-pasini/grokbot-kit/main/docs/images/quickstart/04-segredos.png)

**5. Uma tarefa delegada ao opencode, com o resultado de volta pela routine**

![5. Uma tarefa delegada ao opencode, com o resultado de volta pela routine](https://raw.githubusercontent.com/rodrigo-pasini/grokbot-kit/main/docs/images/quickstart/05-tarefa.png)

</details>

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
