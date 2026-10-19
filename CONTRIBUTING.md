# Contribuindo com o grokbot-kit

## Test policy

> Copiada de `docs/.specs/features/agent-run-notify/checks.md` e aprovada como diretriz do repositório.

O repositório não tem guia de testes: nada diz que nível prova que código nem quanto do espaço de entrada uma prova precisa afirmar. Estas linhas são o padrão deste build.

| Code | Required proofs | Coverage expectation |
| --- | --- | --- |
| Decide, alcançado através de uma fronteira (CLI ou HTTP) | uma na fronteira (subprocesso `grokbot-kit` ou receptor HTTP local) **e** uma na própria camada | o contrato na fronteira; um caso afirmado por linha da tabela de decisão na própria camada |
| Decide, sem fronteira | uma na própria camada | um caso afirmado por linha da tabela de decisão |
| Ponto de entrada que não decide | uma na fronteira | entrada aceita, cada entrada recusada, cada caminho de erro |
| Instrumentação, repasse | nenhuma própria | coberto pela prova de quem a consome |
| Integração com CLI real ou GitHub | `-m integration` no box (ou comando `gh`) | o hook ou a configuração dispara de verdade, uma vez por CLI |

Evidência (ainda não há código; tabelas de decisão contadas no plano):

- derivação do status terminal (AC 43-45): 8 linhas (ok, 2 de denied, 5 de error) e 1 regra de precedência → decide, alcançado pela CLI
- classificação da resposta HTTP (AC 68-72, 123): 7 classes por sink → decide, alcançado por HTTP
- resolução de tool/modelo/tier/timeout (AC 78-83): 6 pontos de decisão → decide
- normalização dos hooks no `emit` (AC 54-58): 4 fontes e 1 regra de dedupe → decide, alcançado pela CLI
- predicado do `gc` (AC 101): 4 casos → decide
- montagem do argv por tool (AC 40-42): 3 linhas → decide (mapping com mais de uma linha)
- análogo no repositório: nenhum ainda (projeto novo); o mais próximo por forma é `.claude/skills/revisar-pr/scripts/conferir-achados.py` com `test-conferir-achados.py`, provado na própria camada

Custo: cerca de 45 provas na própria camada em 12 arquivos de teste, mais 9 provas `-m integration` no box. Sem estas linhas, 6 tabelas de decisão seriam provadas só pelo caminho que um teste de ponta a ponta atravessa.
