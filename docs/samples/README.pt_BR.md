# Amostras de configuração (ponto de entrada)

**English:** [README.md](README.md)

**Os arquivos oficiais ficam em `deploy/samples/`** no repositório (YAML e CSV versionados para copiar). Esta página existe para quem começa pela pasta **`docs/`** ainda encontrar o mesmo roteiro em um só lugar.

| O que você precisa | Onde ir |
| ------------------ | ------- |
| **Starter completo** (duas pastas + um banco + rate limit + termos ML/DL; blocos opcionais comentados + **catálogo de extensões**; para avaliadores e operadores) | [`deploy/samples/config.starter-lgpd-eval.yaml`](../deploy/samples/config.starter-lgpd-eval.yaml) |
| **Mínimo Docker / contêiner** (`targets: []`, caminhos `/data`) | [`deploy/config.example.yaml`](../deploy/config.example.yaml) |
| **Planilha → YAML de alvos** (importação de escopo) | [`deploy/scope_import.example.csv`](../deploy/scope_import.example.csv) + [ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md](../ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md) |
| **Por que existe `config/config.json`** | [`config/README.pt_BR.md`](../config/README.pt_BR.md) (só formato JSON legado) |

**Não** faça commit de um `config.yaml` real de produção (caminhos e segredos). O **`.gitignore`** na raiz exclui nomes típicos locais; veja [CONTRIBUTING.md](../../CONTRIBUTING.md).
