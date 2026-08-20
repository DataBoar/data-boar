# Plugin SDK — plugins de remediação Enterprise (L1)

**English:** [PLUGIN_SDK.md](PLUGIN_SDK.md)

Guia para parceiros que implementam plugins de **remediação pós-scan** contra o hook do host entregue no GitHub **#606** ([ADR-0059](adr/ADR-0059-remediation-plugin-architecture.md)).

**Escopo deste documento:** apenas **L1 in-process Python** (`RemediationPlugin`). Isolamento de processo (L2) e contratos de linguagem / sidecar (L3) ficam no épico **#865** — cite como evolução futura, não como API carregável hoje.

**Fora deste guia:** plugins **YAML de padrões** (regex / termos ML / DL) usam `config/plugin_schema.yaml` e a [ADR-0052](adr/ADR-0052-yaml-plugin-system-centralized-schema.md). How-to do autor: [PLUGIN_AUTHOR_GUIDE.pt_BR.md](PLUGIN_AUTHOR_GUIDE.pt_BR.md) ([EN](PLUGIN_AUTHOR_GUIDE.md)). Eles ensinam novos formatos ao detector; **não** executam código de remediação.

---

## Visão geral

Após o caminho feliz de geração de relatório, o host pode carregar opcionalmente uma classe de terceiro que:

1. Lê um arquivo **JSONL de findings** (path fornecido pelo host).
1. Executa a remediação do parceiro (tokenizar, mascarar, criptografar, notificar, …).
1. Grava um **`remediation_report.json`** (ou equivalente) e devolve o `Path`.

O host não importa a lógica de negócio no core. Você entrega um módulo Python; o operador aponta o YAML para `module.path:ClassName`.

| Peça | Local |
| ---- | ----- |
| Protocol + `PluginError` | `core/plugins/base.py` |
| Loader | `core/plugins/loader.py` → `load_remediation_plugin` |
| Hook fail-graceful | `core/plugins/hook.py` → `maybe_run_remediation_hook` |
| Export público | `core/plugins/__init__.py` |
| Gate de tier | `remediation_plugin` → `Tier.ENTERPRISE` em `core/licensing/tier_features.py` |
| Config de exemplo | `deploy/config.example.yaml` (bloco `remediation:`) |

---

## Protocol (interface mínima)

`RemediationPlugin` é um `typing.Protocol` com `@runtime_checkable`. Sua classe precisa oferecer:

| Membro | Assinatura / tipo | Contrato |
| ------ | ----------------- | -------- |
| `remediate` | `(self, findings_path: Path, config: dict) -> Path` | Lê o JSONL em `findings_path`. **Não modifique esse arquivo in-place.** Devolva o path do relatório de remediação que você escreveu (por convenção `remediation_report.json`). |
| `name` | `@property` → `str` | Id estável do plugin para o Audit Trail. |
| `version` | `@property` → `str` | String de versão do plugin. |

`PluginError` é levantada pelo **loader** quando o formato do path está errado, o módulo não importa, a classe falta, a instanciação falha ou a instância é non-conformant. O host captura `PluginError` (e outras exceções de `remediate`) e faz **Safe-Hold** — o scan **não** aborta.

---

## O que recebe e o que devolve

### `findings_path: Path`

- Forma: JSON delimitado por linha (**JSONL**), um objeto de finding por linha.
- Path: `{report.output_dir}/findings_{session_id}.jsonl`.
- **Fiação do host (#1443):** após o relatório, `maybe_run_remediation_hook(..., db_manager=...)` escreve esse arquivo a partir do SQLite com a mesma taxonomia **só de metadados** de `remediation_targets` do `--export-remediation-manifest` (#649) — chaves como `finding_id`, `source_type`, `connection_ref`, `schema`, `table`, `column`, `pii_type`, `suggested_profile` (sem samples de PII brutos).
- **Somente leitura:** copie ou faça stream; nunca reescreva o arquivo de findings in-place.
- Sessão desconhecida/vazia → o host pula (Safe-Hold); o scan ainda conclui.

### `config: dict`

- Passado do YAML `remediation.config` **como está** (pode ser `{}`).
- Use para chaves do parceiro (endpoints, aliases de chave, dry-run). Não espere segredos do Data Boar salvo o que o operador colocar nesse dict / env que seu plugin ler.

### Valor de retorno: `Path`

- Path absoluto ou relativo do artefato de relatório de remediação que você criou.
- Nome típico: `remediation_report.json` ao lado do findings (sua escolha — devolva o path que você escreveu).

---

## Exemplo mínimo funcional (Python)

```python
# myorg/stealthizer.py
from __future__ import annotations

import json
from pathlib import Path

class StealthizerPlugin:
    """Classe mínima conforme RemediationPlugin (L1)."""

    @property
    def name(self) -> str:
        return "myorg-stealthizer"

    @property
    def version(self) -> str:
        return "0.1.0"

    def remediate(self, findings_path: Path, config: dict) -> Path:
        # Somente leitura: stream dos findings; não reescreva findings_path.
        findings: list[dict] = []
        if findings_path.is_file():
            with findings_path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        findings.append(json.loads(line))

        report = {
            "plugin": self.name,
            "version": self.version,
            "findings_seen": len(findings),
            "actions": [],  # parceiro preenche: tokenized, masked, notified, ...
            "config_keys": sorted(config.keys()),
        }
        out = findings_path.parent / "remediation_report.json"
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return out
```

Instale o pacote no mesmo ambiente Python do Data Boar (ou coloque o módulo no `PYTHONPATH`).

---

## Registrar na config

De `deploy/config.example.yaml`:

```yaml
# Enterprise tier — post-scan remediation plugin (optional)
# Requires licensing.effective_tier: enterprise (or OPEN for dev/lab).
# plugin format: "module.path:ClassName"
remediation:
  enabled: false
  plugin: null           # e.g. "myorg.stealthizer:StealthizerPlugin"
  verify_after: true     # stub log até re-scan completo (#653)
  config: {}             # passado as-is para plugin.remediate()
```

Checklist do operador:

1. `remediation.enabled: true`.
1. `remediation.plugin: "myorg.stealthizer:StealthizerPlugin"`.
1. `licensing.effective_tier: enterprise` no lab, **ou** OPEN (sem `effective_tier`) para liberar gates no lab open-core.
1. Opções do parceiro em `remediation.config`.

Formato do loader: estritamente `module.path:ClassName` (`rsplit(":", 1)`). Sem `:` → `PluginError`.

---

## Gate de tier

| Tier em runtime | `remediation_plugin` |
| --------------- | -------------------- |
| **OPEN** (lab / sem tier comercial) | Disponível (bypass) |
| **ENTERPRISE** | Disponível |
| **COMMUNITY** / **PRO** | Skip — aviso em stderr; sem exceção; scan segue |

Chave: `"remediation_plugin"` em `FEATURE_TIER_MAP` (`Tier.ENTERPRISE`). Tier de runtime: `get_runtime_tier_for_features(config)`.

---

## Comportamento fail-graceful do host

`maybe_run_remediation_hook(config, session_id, db_manager=None)`:

- No-op se `remediation.enabled` for false / ausente.
- Community/Pro → log de skip em stderr; retorna.
- Com `db_manager`: escreve `findings_{session_id}.jsonl` e chama `remediate`.
- Sem `db_manager` e JSONL ausente → skip (stderr); não inventa path fantasma.
- Falhas de load / `remediate` → `[remediation] plugin error: …` em stderr; **nunca** propaga para o worker de scan.
- Com `verify_after` true e remediate ok, loga
  `[remediation] post-remediation verification pending (see #653)`
  (somente stub).

---

## Testar localmente

### 1) Chamada direta (funciona hoje — recomendado)

```bash
# Em um venv com data-boar + seu plugin importável:
uv run python - <<'PY'
from pathlib import Path
from myorg.stealthizer import StealthizerPlugin

findings = Path("/tmp/findings_demo.jsonl")
findings.write_text(
    '{"finding_id":"f1","path":"/data/a.csv","pii_type":"EMAIL"}\n',
    encoding="utf-8",
)
report = StealthizerPlugin().remediate(findings, {"dry_run": True})
print(report, report.read_text(encoding="utf-8"))
PY
```

### 2) Conformidade via loader

```python
from core.plugins import load_remediation_plugin, PluginError

plugin = load_remediation_plugin("myorg.stealthizer:StealthizerPlugin")
assert plugin.name and plugin.version
```

Testes no repo: `tests/test_plugin_loader.py` (load válido, formato inválido, non-conformant → `PluginError`, skip de tier).

### 3) Hook do host com YAML (opt-in)

Você pode habilitar `remediation:` e rodar um scan / regenerate-report. **Até o #1443**, trate a invocação automática como **fiação em finalização**: o hook pode passar um path de findings que ainda não existe. Prefira `remediate()` direto para demos funcionais de parceiro.

---

## Segurança (fronteira de trust L1)

- O plugin roda **no mesmo processo Python** do Data Boar (L1). Trate como **código totalmente confiável** naquele host: pode ler memória, FS e rede no que o usuário do processo permitir.
- **Não** carregue wheels de terceiros não auditados em hosts Enterprise de produção sem revisão de supply-chain (pin, hash, índice privado).
- Evolução recomendada (**#865**): sandbox L2 / sidecar L3 para isolar código do parceiro. Este SDK **não** oferece esse isolamento hoje.
- Findings e relatórios de remediação são confidenciais mesmo como “só metadata” — mantenha-os na tenancy do cliente.

---

## Exemplos de caso de uso (IP do parceiro)

| Caso de uso | O que `remediate` tipicamente faz |
| ----------- | --------------------------------- |
| **Tokenização FPE** | Mapa de coordenadas → tokens com preservação de formato via HSM/vault do parceiro; log de ações no relatório |
| **Masking** | Sobrescreve ou prepara cópias mascaradas nos paths mapeados; nunca reescreve o JSONL de findings |
| **Criptografia de campo** | Criptografa payloads de coluna/arquivo; registra refs de ciphertext no relatório |
| **Notificação** | Abre tickets / webhooks a partir das localizações; relatório = recibos de entrega |

Discovery e reporting ficam no Data Boar; o **como** remediar fica no IP do parceiro. Storyboard: [USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md](use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md).

---

## Documentos relacionados

- [USAGE.pt_BR.md](USAGE.pt_BR.md) ([EN](USAGE.md)) — CLI/config do operador; seção Enterprise de remediação
- [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) ([EN](TECH_GUIDE.md)) — install, config, extensibilidade
- [ADR-0059](adr/ADR-0059-remediation-plugin-architecture.md) — L1 protocol-based, fail-graceful, gate Enterprise
- [ADR-0052](adr/ADR-0052-yaml-plugin-system-centralized-schema.md) — plugins YAML de **padrão** (outra superfície)
- [use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md](use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md) ([EN](use-cases/USE_CASE_SCAN_AND_REMEDIATE.md))
- [use-cases/USE_CASE_TOKENIZED_FINDINGS.pt_BR.md](use-cases/USE_CASE_TOKENIZED_FINDINGS.pt_BR.md) ([EN](use-cases/USE_CASE_TOKENIZED_FINDINGS.md))
- GitHub **#606** (hook), **#611** (este guia), **#1443** (fiação do findings path), **#653** (verify_after), épico **#865** (L2/L3)
