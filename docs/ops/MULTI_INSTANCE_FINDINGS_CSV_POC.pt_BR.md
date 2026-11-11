# CSV de findings multi-instância (prova de conceito da Fase 0)

**English:** [MULTI_INSTANCE_FINDINGS_CSV_POC.md](MULTI_INSTANCE_FINDINGS_CSV_POC.md)

**O que é:** um script pequeno, [`scripts/multi_instance_findings_poc.py`](../../scripts/multi_instance_findings_poc.py),
que busca `GET /findings/csv` de várias instâncias do Data Boar e junta as linhas em um único CSV,
acrescentando a proveniência que a API não emite (`node_id`, `fetched_at_utc`).

**O que não é:** uma funcionalidade de centralização. É um paliativo documentado para revisão
consolidada enquanto o modo hub é desenhado (plano: `docs/plans/PLAN_MULTI_INSTANCE_REPORT_HUB.md`,
issue #2208). Não apresente isso a ninguém como "gestão central".

## Por que um script é necessário

O CSV unificado de findings **não tem coluna de nó ou host**, e o `id` é um contador local de
cada nó. Concatenar CSVs de dois nós perde de onde cada linha veio. Numa verificação com duas
instâncias `--demo` sintéticas e isoladas, **todos os 26 valores de `id` se repetiram** entre os nós.

## Pré-requisitos

- Cada nó expõe a API para a máquina que roda o script (`https`; `http` simples só é aceito para
  loopback em laboratório/demo).
- Se um nó exige `api.require_api_key`, coloque a chave em uma **variável de ambiente** chamada
  `DATA_BOAR_NODE_TOKEN_<NODE_ID>` (letras e dígitos do id em maiúsculas, demais caracteres
  trocados por `_`; `site-a` vira `DATA_BOAR_NODE_TOKEN_SITE_A`). Tokens nunca são aceitos na
  linha de comando.

## Como rodar

```bash
export DATA_BOAR_NODE_TOKEN_SITE_A='...'      # só se esse nó exigir chave
uv run python scripts/multi_instance_findings_poc.py \
  --node site-a=https://boar-a.example.internal:8088 \
  --node site-b=https://boar-b.example.internal:8088 \
  --out /local/seguro/merged_findings.csv
```

| Opção | Significado |
| ----- | ----------- |
| `--node NODE_ID=URL` | Repita por nó. `NODE_ID` é um rótulo que você escolhe (letras, dígitos, `_`, `.`, `-`; começa com letra ou dígito). |
| `--out CAMINHO` | CSV mesclado. Precisa ficar **fora** da árvore do repositório; arquivo existente é recusado sem `--overwrite`. Criado com modo `0600`. |
| `--timeout`, `--max-bytes` | Limites por nó (padrão: 30 s, 64 MiB). |

Colunas de saída: `node_id`, `fetched_at_utc` e depois as colunas do nó. As linhas são
deduplicadas por `(node_id, session_id, id)`. Cada nó contribui apenas com a **última sessão**.

Códigos de saída: `0` todos os nós mesclados, `2` alguns nós falharam (o restante foi mesclado),
`1` nada mesclado ou uso inválido. As falhas saem por nó, sem imprimir URLs nem tokens
(`timeout`, `connection error`, `authentication rejected (HTTP 401/403)`, `no scan session on node
(HTTP 404)`, `redirect received (not followed)`, `unexpected CSV header`).

## Notas de segurança

- O CSV mesclado contém **caminhos e nomes de host**, que são sensíveis. Guarde em local cifrado e
  com controle de acesso, e nunca faça commit dele.
- Redirecionamentos nunca são seguidos, então um token não pode ser repassado a outro host.
- Este PoC não verifica a identidade do nó além do TLS: escolha os rótulos `NODE_ID` com cuidado.

## Como verificar localmente com dados sintéticos

Duas instâncias `--demo` no mesmo host **não podem compartilhar o diretório temporário**: ambas
usam `<tmp>/data_boar_demo`, e iniciar a segunda derrubou a primeira na nossa verificação (HTTP 500
em `/findings/csv`, `unable to open database file`). Dê a cada uma o seu próprio `TMPDIR`:

```bash
mkdir -p /tmp/boar-a /tmp/boar-b
TMPDIR=/tmp/boar-a uv run python main.py --demo --port 8101 &
TMPDIR=/tmp/boar-b uv run python main.py --demo --port 8102 &
# espere as duas responderem 200 em /findings/csv e então:
uv run python scripts/multi_instance_findings_poc.py \
  --node demo-a=http://127.0.0.1:8101 --node demo-b=http://127.0.0.1:8102 \
  --out /tmp/merged_demo.csv
```

Observado em 2026-11-11 (corpus sintético, duas instâncias): `demo-a` 26 linhas, `demo-b` 26 linhas,
52 linhas mescladas, saída `0`. Esses números descrevem apenas o corpus de demonstração; não dizem
nada sobre desempenho ou capacidade com dados reais.

## Limites

Apenas a última sessão de cada nó; sem agendamento; sem deduplicação entre nós do mesmo arquivo
visto por dois nós (decisão de modelagem da fase hub); sem saída em Excel.
