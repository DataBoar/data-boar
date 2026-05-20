<!-- plans-hub-summary: Hub de navegação para todas as camadas de tamper detection e integridade do produto -->

# Integridade e detecção de adulteração — hub de navegação

**English:** [INTEGRITY_HUB.md](INTEGRITY_HUB.md)

> **Para agentes (Claude / Cursor):**
>
> - Antes de implementar qualquer lógica de integridade: verifique se já existe neste hub.
> - Antes de criar um ADR novo de integridade: leia [ADR-0037](../adr/ADR-0037-data-boar-self-audit-log-governance.md), [ADR-0039](../adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) e [ADR-0051](../adr/ADR-0051-incremental-filesystem-scan-file-identity-fingerprint.md).
> - Em falha de hash em runtime: siga [INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md](INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md) e `core/runtime_trust.py` — prefira **Safe-Hold** / modo degradado; não contorne falhas em silêncio.
> - `scripts/inv-adr.ps1` cobre só **`docs/adr/`**; `scripts/evidence-hash-manifest.ps1` cobre evidências legais em **`docs/private/`** (gitignored).

> **Agente/Cursor:** leia esta página primeiro. Ela mapeia **onde** cada peça está. Não reescreva lógica de integridade sem conferir o que já existe aqui.

## Cadeia de confiança

Fonte → Build → Deploy → Runtime → Docs/ADR

| Etapa | Pontos de entrada |
| ----- | ----------------- |
| Fonte | Tags Git, commits assinados (política do operador) |
| Build | [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](../plans/PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md), evidência Rust determinística em [RELEASE_INTEGRITY.pt_BR.md](RELEASE_INTEGRITY.pt_BR.md) |
| Deploy | [docs/RELEASE_INTEGRITY.pt_BR.md](../RELEASE_INTEGRITY.pt_BR.md) (digest de licenciamento + manifesto opcional), [release-integrity-check.ps1](../../scripts/release-integrity-check.ps1) |
| Runtime | `core/runtime_trust.py`, [INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md](INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md) |
| Docs/ADR | `scripts/inv-adr.ps1`, [docs/adr/INVENTORY.txt](../adr/INVENTORY.txt) |

## Índice rápido por camada

### 1. Runtime do produto (Python)

| Módulo / doc | Papel |
| ------------ | ----- |
| [`core/runtime_trust.py`](../../core/runtime_trust.py) | Estado tinted, modo degradado quando checagens falham |
| [`core/licensing/integrity.py`](../../core/licensing/integrity.py) | Verificação de tier / manifesto de licença |
| [`core/maturity_assessment/integrity.py`](../../core/maturity_assessment/integrity.py) | Selo do maturity assessment (`DATA_BOAR_MATURITY_INTEGRITY_SECRET`) |
| [INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md](INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md) | Especificação de design para hashes opcionais na subida (alpha) |

### 2. Artefatos de release

| Doc / script | Papel |
| ------------ | ----- |
| [docs/RELEASE_INTEGRITY.pt_BR.md](../RELEASE_INTEGRITY.pt_BR.md) | **Doc público de produto** — tamper-evidence opcional para **licenciamento** (digest de build, manifesto assinado, ponteiros SBOM) |
| [RELEASE_INTEGRITY.pt_BR.md](RELEASE_INTEGRITY.pt_BR.md) | **Especificação operacional de release** — evidência Rust, throttling SRE, taxonomia GRC, checklist de release |
| [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](../plans/PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) | Roadmap de identidade de build e integridade de release mais forte |
| [release-integrity-check.ps1](../../scripts/release-integrity-check.ps1) | Script de verificação pós-release |
| [example-release-manifest.json](../../scripts/example-release-manifest.json) | Exemplo de schema de manifesto assinado |

### 3. Evidência (árvore privada — hashes legais / operador)

| Script | Papel |
| ------ | ----- |
| [evidence-hash-manifest.ps1](../../scripts/evidence-hash-manifest.ps1) | Manifesto SHA-256 / SHA-512 para arquivos em `docs/private/` (assinatura GPG detached fica com o operador) |

### 4. Integridade de docs e ADR

| Artefato | Papel |
| -------- | ----- |
| [inv-adr.ps1](../../scripts/inv-adr.ps1) | Inventário de ADRs com SHA-256 por arquivo e `InventoryHash` atestado |
| [docs/adr/INVENTORY.txt](../adr/INVENTORY.txt) | Manifesto gerado — verificar offline após `inv-adr.ps1` |
| `docs/adr/INVENTORY.txt.sig` | Assinatura SSH ed25519 detached (fluxo do operador; opcional até assinar) |

### 5. ADRs relacionados

| ADR | Escopo |
| --- | ----- |
| [ADR-0037](../adr/ADR-0037-data-boar-self-audit-log-governance.md) | Governança do log de autoauditoria (o que existe hoje vs lacunas) |
| [ADR-0039](../adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) | Retenção e postura de evidência em contextos regulados complexos |
| [ADR-0051](../adr/ADR-0051-incremental-filesystem-scan-file-identity-fingerprint.md) | Impressão digital de arquivo para scan incremental (não é tamper-evidence criptográfico) |

## Quando acionar Safe-Hold

- **Runtime:** Se checagens de integridade configuradas falharem na subida ou em caminhos protegidos, `core/runtime_trust.py` pode entrar em estado **tinted** / degradado — trate a saída como evidência de conformidade **não** plena até o operador restaurar bits conhecidos ou desabilitar o check de forma explícita no runbook.
- **Inventário de ADR:** Se `INVENTORY.txt` não bater com assinatura verificada ou hash regenerado via `inv-adr.ps1`, **não faça commit** de mudanças em ADR sem rerodar o script e alinhar com o mantenedor.

## `docs/RELEASE_INTEGRITY.md` vs `docs/ops/RELEASE_INTEGRITY.md` (resolvido)

Os arquivos compartilham o basename, mas são **propositalmente diferentes** — não é cópia desatualizada.

| Arquivo | Público | Conteúdo |
| ------- | ------- | -------- |
| [docs/RELEASE_INTEGRITY.pt_BR.md](../RELEASE_INTEGRITY.pt_BR.md) | Produto / integradores | Tamper-evidence de **licenciamento**: `_build_digest.txt`, `DATA_BOAR_EXPECTED_BUILD_DIGEST`, manifesto JSON opcional, links do workflow SBOM |
| [docs/ops/RELEASE_INTEGRITY.pt_BR.md](RELEASE_INTEGRITY.pt_BR.md) | Operadores / SRE | Especificação de **engenharia de release**: builds Rust determinísticos, disciplina de hash, throttling/resume, pesos GRC, checklist |

Há cross-links nos dois documentos e em [INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md](INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md). Comece aqui quando não souber qual arquivo usar.

## Navegação relacionada

- [hubs/INDEX.pt_BR.md](../hubs/INDEX.pt_BR.md) — mapa de hubs
- [SECURITY.pt_BR.md](../../SECURITY.pt_BR.md) — reporte de vulnerabilidades e artefatos de supply chain
- [CODE_PROTECTION_OPERATOR_PLAYBOOK.pt_BR.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.pt_BR.md) — endurecimento do operador (faixa Priority A)
