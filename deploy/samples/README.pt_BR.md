# Arquivos de configuração de exemplo

**English:** [README.md](README.md)

Estes **arquivos** estão **versionados** no Git para quem está começando (jurídico, DPO, auditoria ou TI) poder partir de um modelo **completo e com padrões razoáveis**, sem juntar trechos espalhados pela documentação. O **mesmo roteiro** a partir de **`docs/`** está em **[docs/samples/README.pt_BR.md](../../docs/samples/README.pt_BR.md)** ([EN](../../docs/samples/README.md)).

| Arquivo | Finalidade |
| ------- | ---------- |
| **[config.starter-lgpd-eval.yaml](config.starter-lgpd-eval.yaml)** | **Ponto de partida recomendado** para jurídico, DPO, auditoria ou TI na primeira execução em laboratório ou on-prem: duas pastas fictícias de filesystem, um alvo estilo PostgreSQL (senha por variável de ambiente), timeouts, limite de taxa, termos mínimos de ML/DL, mais **blocos comentados** para recursos opcionais (arquivos compactados, `file_passwords`, `learned_patterns`, arquivos externos de padrões, `detection.cnpj_alphanumeric`, `connector_format_id_hint`, chave de API, dicas de jurisdição). **Comentários** listam grupos de sufixos suportados (texto, office, dados estruturados, mídia rica opcional, arquivos), alinhados a `connectors/filesystem_connector.py`. Substitua os caminhos e defina a variável de `pass_from_env`. |
| **[../config.example.yaml](../config.example.yaml)** | Modelo **mínimo** orientado a contêiner (`targets: []`, caminhos `/data`). Use quando só precisa do arquivo válido menor. |
| **[../scope_import.example.csv](../scope_import.example.csv)** | Cabeçalho CSV canônico para **`scripts/scope_import_csv.py`** quando os alvos vêm de planilha. |

**Não** faça commit do seu `config.yaml` real (pode conter caminhos internos e segredos). O **`.gitignore`** na raiz exclui nomes típicos locais; veja [CONTRIBUTING.md](../../CONTRIBUTING.md).

**YAML vs JSON:** Projetos novos devem usar **YAML**. O formato JSON legado (`databases` + `file_scan.directories`) **ainda é aceito** pelo carregador — veja **[../../config/README.md](../../config/README.md)**.
