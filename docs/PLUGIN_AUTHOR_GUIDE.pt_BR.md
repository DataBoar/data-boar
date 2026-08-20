# Guia do autor de plugin — plugins YAML de padrões

**English:** [PLUGIN_AUTHOR_GUIDE.md](PLUGIN_AUTHOR_GUIDE.md)

Como ensinar ao Data Boar **novos formatos de detecção** sem alterar o código do núcleo. Esta é a porta de entrada para autores de padrões de terceiros / operadores (GitHub **#836**).

O **contrato** é o schema em disco: [`config/plugin_schema.yaml`](../config/plugin_schema.yaml). O validador é [`config/plugin_validator.py`](../config/plugin_validator.py) ([ADR-0052](adr/ADR-0052-yaml-plugin-system-centralized-schema.md)).

---

## Duas superfícies de plugin (não misture)

| Superfície | O que é | Executa código? | Guia |
| ---------- | ------- | --------------- | ---- |
| **Plugins YAML de padrões** (esta página) | Termos extras de regex / ML / DL carregados de YAML | **Não** | Você está aqui |
| **Remediação Enterprise L1** | `RemediationPlugin` em Python após o relatório | **Sim** (no processo) | [PLUGIN_SDK.pt_BR.md](PLUGIN_SDK.pt_BR.md) ([EN](PLUGIN_SDK.md)) |
| **Envelope language-neutral (L2/L3)** | Contrato sidecar / FFI — não é API YAML carregável hoje | n/a | [SDK.md](SDK.md) |

Plugins YAML **não** abrem sockets, não leem arquivos extras e não chamam conectores. Só acrescentam **o que o detector procura**.

---

## O que você pode e não pode tocar

**Pode:**

- Acrescentar ou sobrescrever regras **regex** (`name` + `pattern`, `norm_tag` opcional).
- Acrescentar termos **ML** / **DL** (`text` + `label` opcional).
- Opcionalmente anexar **metadados de autor** (`dga_classification`, `iso27001_controls`, `dmbok_area`) em itens regex. São **dicas para autores GRC**, não parecer jurídico, e **não** são copiados para as linhas de finding (o relatório segue expondo `pattern_detected` / `norm_tag`).

**Não pode:**

- Executar Python, shell ou Rust próprio.
- Alterar **alvos** de scan, **RBAC**, rotas da API ou modelos de relatório.
- Implementar **remediação** (tokenizar / mascarar / notificar) — isso é [PLUGIN_SDK.pt_BR.md](PLUGIN_SDK.pt_BR.md).
- Contornar o guarda **ReDoS** (#829): quantificadores ilimitados aninhados como `(a+)+` ou `(\w*)*` são rejeitados.

---

## Tier (honesto)

Arquivos YAML de padrões entram hoje como **config do operador** (Community / lab `Tier.OPEN`). **Não** há `require_feature("custom_detectors")` em `regex_overrides_file` / `patterns_plugin_file`.

`FEATURE_TIER_MAP["custom_detectors"]` é **Enterprise** como chave de produto **reservada** — **ainda não** é o gate desses YAML. Não diga ao autor que precisa de licença Enterprise só para enviar um arquivo de padrões.

Plugins de remediação **exigem** a feature **Enterprise** `remediation_plugin` (ou lab `OPEN`). Veja [PLUGIN_SDK.pt_BR.md](PLUGIN_SDK.pt_BR.md).

---

## Chaves de config

Prefira **um** arquivo unificado:

```yaml
# config.yaml
patterns_plugin_file: /data/my_patterns.yaml
```

As chaves legadas ainda funcionam (mesmos schemas, três arquivos): `regex_overrides_file`, `ml_patterns_file`, `dl_patterns_file`. Quando o arquivo unificado e uma chave legada cobrem a **mesma seção**, **`patterns_plugin_file` prevalece** nessa seção ([ADR-0052](adr/ADR-0052-yaml-plugin-system-centralized-schema.md)).

Comportamento campo a campo: [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) ([EN](SENSITIVITY_DETECTION.md)). Visão CLI/config: [USAGE.pt_BR.md](USAGE.pt_BR.md) ([EN](USAGE.md)).

---

## Exemplo unificado mínimo

```yaml
regex_patterns:
  - name: "RG_BR"
    pattern: "\\b\\d{1,2}\\.?\\d{3}\\.?\\d{3}-?[0-9Xx]\\b"
    norm_tag: "LGPD Art. 5"

ml_patterns:
  - text: "cpf"
    label: "sensitive"

dl_patterns:
  - text: "dado pessoal"
    label: "sensitive"
```

Uma lista maior de regex está em [`config/regex_overrides.example.yaml`](../config/regex_overrides.example.yaml). Use YAML com **aspas duplas** e barras invertidas escapadas (`\\b`, `\\d`).

Arquivos legados só de regex são uma **lista YAML** (sem wrapper `regex_patterns:`) — mesmos campos por item.

---

## Metadados GRC opcionais do autor (só itens regex)

Essas chaves ficam em itens **regex** (`config/plugin_schema.yaml`). São **metadados de autor**. O `config/plugin_validator.py` valida tipos e valores permitidos; o detector **não** as copia para as linhas de finding. O relatório segue expondo `pattern_detected` (o `name` da regra) e `norm_tag`. **Não** são parecer jurídico de DGA, certificação ISO 27001 nem avaliação DMBOK.

| Chave | Tipo | Valores / forma permitidos |
| ----- | ---- | -------------------------- |
| `dga_classification` | string | `shareable`, `restricted_sharing`, `no_sharing` |
| `iso27001_controls` | lista de strings | IDs do Anexo A ISO/IEC **27001:2022** (ex.: `A.5.12`, `A.5.33`, `A.8.3`, `A.8.11`). **2013** `A.8.2.1` mapeia para **2022** `A.5.12`, não para 2022 `A.8.2`. |
| `dmbok_area` | string | `armazenamento_e_operacao`, `integracao_e_interoperabilidade`, `seguranca_dados` |

Itens ML / DL **não** declaram essas chaves no schema. Chaves extras nesses itens são **ignoradas** (validador aditivo). Elas **também não** aparecem nos findings.

```yaml
regex_patterns:
  - name: "HEALTH_PLAN_ID"
    pattern: "\\bHP-\\d{8}\\b"
    norm_tag: "LGPD Art. 5 II"
    dga_classification: no_sharing
    iso27001_controls:
      - A.5.33
      - A.8.11
    dmbok_area: seguranca_dados
```

Dicas típicas no schema: saúde / categoria especial → `A.5.33` + `A.8.11`; acesso / credencial → `A.8.3`; classificação de PI armazenado → `A.5.12`. Armazenamento / arquivos → `armazenamento_e_operacao`; APIs / fluxos → `integracao_e_interoperabilidade`; PI sem classificação → `seguranca_dados`.

---

## Contrato de regex seguro (ReDoS)

O validador percorre o padrão e **rejeita repetição ilimitada aninhada** (star-height > 1), a mesma classe dos linters `safe-regex`: `(a+)+`, `([a-z]+)*`, `(x{2,})+`.

Ainda válidos:

- `?` limitado (0-ou-1), ex.: `(\\+55\\s?)?` para prefixo de país opcional.
- Metacaracteres escapados (`\\+`, `\\(`).
- Quantificadores dentro de classes de caracteres (`[+*]`).

Itens inválidos emitem `PluginValidationWarning` e são **ignorados**; a varredura **continua** (não descarta o arquivo inteiro em silêncio).

---

## Validar antes da varredura

Ainda **não** há CLI `validate-plugin` no produto (fase posterior). No clone:

```bash
uv run python -c "from config.plugin_validator import validate_plugin_file; r = validate_plugin_file('my_patterns.yaml', 'unified_plugin_file'); print(r.valid); print('\\n'.join(r.issues))"
```

Use `plugin_type="regex_patterns"` para um arquivo-lista legado. `--validate-config` também mostra avisos do validador quando o caminho unificado está definido.

---

## Relacionado

- Schema: [`config/plugin_schema.yaml`](../config/plugin_schema.yaml)
- Como detectar: [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md)
- Parceiros de remediação: [PLUGIN_SDK.pt_BR.md](PLUGIN_SDK.pt_BR.md)
- Hub de contrato (L2/L3): [SDK.md](SDK.md)
- Índice: [README.pt_BR.md](README.pt_BR.md)

**Índice da documentação:** [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
