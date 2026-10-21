---
name: grokbot-kit
description: Instala e configura o grokbot-kit e delega tarefas a agentes de código headless, acordando a routine deste bot quando a tarefa termina ou precisa de permissão. Use quando o usuário disser "configurar grokbot-kit", "delegar para opencode/claude/codex" ou "rodar tarefa headless".
---

# grokbot-kit

O `grokbot-kit` roda uma tarefa num agente de código headless (`opencode`, `claude` ou `codex`) e, quando ela termina
ou esbarra numa permissão, acorda a routine deste bot com um evento JSON. Esta skill faz o setup na primeira vez e
depois delega as tarefas. O próximo passo é sempre um comando `grokbot-kit`.

Instalação desta skill: copie a pasta `skills/grokbot-kit/` do repositório `rodrigo-pasini/grokbot-kit` para o
diretório de workflows do Grok Bot; no box, `/home/box/agent-data/workflows/grokbot-kit/`.

## Regras

- Só chame `grokbot-kit`, `uv` ou `pipx` (para instalar o kit) e as CLIs oficiais `opencode`, `claude` e `codex`.
  Nada de editar o config à mão, `curl` ou scripts próprios.
- Nunca invente um id de modelo, um comando ou uma flag. Use só o que esta skill cita e o que o `--help` do
  `grokbot-kit` mostra; um id de modelo só existe depois que `grokbot-kit setup models refresh` o descobriu.
- Nunca peça que o usuário cole no chat uma API key, uma sender key ou uma URL secreta (a URL do webhook da routine
  é secreta). Segredo entra só por `grokbot-kit secret set <nome>`, com o valor na entrada padrão: lido pelas suas
  próprias ferramentas (a URL e a key de uma routine deste bot) ou pedido ao usuário num campo mascarado de
  segredos, que guarda o valor fora do chat. Nunca passe o valor como argumento, nunca o mostre, repita ou registre.
  Só sem campo mascarado peça que o usuário rode `grokbot-kit secret set <nome>` num terminal do box, que lê o
  valor sem eco.
- Se o usuário colar um segredo no chat ou mandar um print em que a key aparece: não grave o valor, não repita o
  valor, e avise que ele vazou e precisa regenerar a key no painel da routine (ou no painel de quem a emitiu) e
  gravar a nova com `grokbot-kit secret set <nome>` pelo campo mascarado de segredos.

## Setup (primeira vez)

### 1. Instalar o kit

Confira se o kit está no `PATH`:

```sh
grokbot-kit --version
```

Se `grokbot-kit` não estiver no `PATH` (o comando não existe), instale antes de qualquer outro passo com `uv tool install --managed-python grokbot-kit`
(ambiente isolado, com Python gerenciado pelo `uv`); sem `uv` no box, use `pipx install grokbot-kit`. Depois rode o
`grokbot-kit --version` de novo.

```sh
uv tool install --managed-python grokbot-kit
```

```sh
pipx install grokbot-kit
```

### 2. Ver o estado

```sh
grokbot-kit doctor --json
```

A saída diz o que já está feito: `setup.installed` (CLIs instaladas), `setup.default_cli`, o login de cada CLI, as
rotas e os segredos; `problems` lista o que corrigir, com o comando. Pule os passos que já estão feitos.

### 3. CLIs e login

Com `setup.installed` vazio no `grokbot-kit doctor --json`, faça uma única pergunta de múltipla escolha: quais CLIs instalar entre `opencode`,
`claude` e `codex` (o `opencode` tem modelos gratuitos e não exige login para eles).

Para cada CLI escolhida, instale com `grokbot-kit setup cli add <tool>`, que usa o instalador oficial:

```sh
grokbot-kit setup cli add <tool>
```

Com o `opencode`, instale também o plugin que avisa quando o agente pede permissão (fora de uma tarefa ele não faz
nada):

```sh
grokbot-kit install opencode
```

Depois, para cada CLI, pergunte o método de login: assinatura ou API key.

- Assinatura: peça que o usuário rode `grokbot-kit login <tool> --method subscription` num terminal do box e siga o
  que a CLI pedir.
- API key: peça a key no campo mascarado de segredos (nunca no chat) e grave-a pela entrada padrão de
  `grokbot-kit secret set <tool>-api-key`; depois rode `grokbot-kit login <tool> --method api-key`.

```sh
grokbot-kit login <tool> --method subscription
```

```sh
grokbot-kit login <tool> --method api-key
```

### 4. CLI padrão

Pergunte qual CLI usar quando o usuário não pedir nenhuma e grave a escolha:

```sh
grokbot-kit setup default <tool>
```

### 5. Modelos e tiers

Descubra os modelos de cada CLI instalada:

```sh
grokbot-kit setup models refresh
```

A saída lista `<tool>` e o id de cada modelo descoberto. Proponha ao usuário a tabela de tiers por CLI (`trivial`,
`standard`, `complex`, cada um com uma lista ordenada; o primeiro id vence) usando só ids da lista descoberta:

- coloque os modelos gratuitos do opencode primeiro em `trivial` e `standard` (são os ids que a lista do opencode
  marca com o sufixo `-free`);
- em `complex`, nunca ponha modelo gratuito (veja a rubrica).

Com a tabela confirmada, grave cada tier:

```sh
grokbot-kit setup tiers <tool> <tier> <id> [<id>...]
```

Se o usuário quiser no `claude` ou no `codex` um id que não está na lista, teste e grave com
`grokbot-kit setup models refresh <tool> --add <id>` antes de usá-lo; um id recusado não entra.

### 6. Routine do bot

Este bot é acordado por uma routine com webhook trigger. Use como nome do bot (`<bot>`) um nome curto deste bot, só
com letras, dígitos, `.`, `_` e `-`.

Antes de tudo, avise: a key da routine (`crsr_…`) não pode aparecer em print, colagem ou mensagem, porque um print
vai para o chat e a key vaza (já aconteceu).

1. Crie uma routine para este bot com webhook trigger, usando o prompt de routine abaixo. Se suas ferramentas criam
   routines, crie você mesmo; senão, peça ao usuário: abra o painel do Grok Bot e crie a routine.
2. Grave a URL de "POST para" da routine com `grokbot-kit secret set <bot>-url` e depois a key `crsr_…` com
   `grokbot-kit secret set <bot>-key`, cada valor pela entrada padrão do comando, nesta ordem de preferência:
   - leia os dois valores da routine com suas próprias ferramentas, sem mostrá-los;
   - senão, peça cada um ao usuário num campo mascarado de segredos (ele copia do painel da routine e cola no campo);
   - só sem campo mascarado, peça que o usuário rode os dois comandos num terminal do box.
3. Crie a rota e teste a entrega:

```sh
grokbot-kit route add <bot> --url-secret <bot>-url --key-secret <bot>-key
```

```sh
grokbot-kit route test <bot>
```

O `route test` envia um evento `test` à routine. Exit `0` é entrega confirmada; exit `1` mostra o status HTTP (um
`401` é key errada: grave de novo com `grokbot-kit secret set <bot>-key`).

#### Prompt da routine

Proponha este prompt para a routine, trocando `<bot>` pelo nome deste bot:

```text
Você recebe um webhook do grokbot-kit. O campo `body` chega como texto: faça o parse dele como JSON.
Se o parse falhar ou o campo `schema` não for "grokbot-kit.event/v1", ignore o webhook.
Se o campo `target` não for "<bot>", ignore o evento: ele é de outro bot.
Senão, siga a skill grokbot-kit, seção "Quando um evento chega", com o evento lido.
```

## Tarefa

Toda tarefa vai a `grokbot-kit run` com `--target <este bot>` (o mesmo `<bot>` da rota) e um `--label` curto que
descreve a tarefa (letras, dígitos, `.`, `_` e `-`). Passe o diretório do projeto com `--cwd <dir>` e o prompt depois
de `--`. O `run` só termina quando o agente termina; o resultado chega pela routine, então não fique esperando. O
caminho do task dir sai em stderr.

Quando o usuário pede CLI e modelo:

```sh
grokbot-kit run --tool <cli> --model <id> --target <este bot> --label <rótulo> --cwd <dir> -- "<prompt>"
```

Omita `--tool` quando o usuário não pede uma CLI: o kit usa a CLI padrão.

Quando o usuário não pede modelo, classifique a tarefa em `trivial`, `standard` ou `complex` pela rubrica abaixo,
passe `--tier <tier>` e diga ao usuário a classe escolhida em uma linha (por exemplo: "Classifiquei como `trivial`:
renomear variáveis num arquivo.").

```sh
grokbot-kit run --tier <tier> --target <este bot> --label <rótulo> --cwd <dir> -- "<prompt>"
```

O tier também decide o timeout (`trivial` 30 min, `standard` 2 h, `complex` 4 h); `--timeout <duração>` (`30m`,
`2h`) prevalece.

### Rubrica de tiers

| Tier | Quando |
| --- | --- |
| `trivial` | mudança pequena e mecânica, sem decisão: renomear, formatar, corrigir um typo, ajustar uma linha |
| `standard` | trabalho comum de código: uma função, um teste, um bug localizado, uma refatoração contida |
| `complex` | revisão de segurança, decisões de arquitetura, checagem de fatos, e tudo o que toca produção, credenciais ou dados sensíveis |

Tarefas `complex` nunca vão a modelos gratuitos: sem modelo pedido, use `--tier complex`; se o usuário pedir um modelo
gratuito para uma delas, explique o motivo e proponha um id do tier `complex`. Na dúvida entre dois tiers, escolha o
maior.

## Quando um evento chega

A routine acorda este bot com o webhook. Faça o parse de `body` como JSON e leia `event`, `status`, `summary` e
`output_file` (a saída completa do agente; `log_file` tem o log do kit).

- `completed` com `status` `ok`: conte ao usuário o resultado a partir do `summary`.
- `error` (`failed` ou `interrupted`) e `timeout`: conte o que houve e o que o `summary` diz; ofereça rodar de novo.
- `needs_input` (`permission` ou `question`), ou `completed` com `status` `denied`: mostre ao usuário o que o agente
  pediu (`needs_input.tool_name` e `needs_input.detail`) e ofereça retomar com o comando de `resume_hint` depois de
  ajustar a permissão. Um `needs_input` chega enquanto a tarefa ainda roda; o evento final vem depois.
- `test`: é o `grokbot-kit route test`; só confirme que a rota funciona.

## Evento que não chegou

Se o usuário pergunta por uma tarefa cujo evento não chegou, veja o `undelivered.jsonl` no task dir da tarefa
(`~/.grokbot-kit/tasks/<task_id>/`): cada linha é uma entrega que falhou, com o motivo. Corrija a causa (rota ou key)
e ofereça reenviar com `grokbot-kit redeliver <task_id>`.

```sh
grokbot-kit redeliver <task_id>
```
