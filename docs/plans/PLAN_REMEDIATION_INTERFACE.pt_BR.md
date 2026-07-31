# Plano: Interface de plugin de remediação pós-scan (Enterprise)

<!-- plans-hub-summary: Ponte Enterprise de remediação — export do manifest #649 entregue; esqueleto do hook #606 ainda aberto -->

**Status:** Ativo
**Data:** 2026-05-19
**Autores:** Fabio Leitao
**Prioridade:** H1

**Sincronizado com:** [PLANS_TODO.md](PLANS_TODO.md) · GitHub **#601** · **#606** · **#649**

**Relacionado:** [USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md](../use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md), [USE_CASE_TOKENIZED_FINDINGS.pt_BR.md](../use-cases/USE_CASE_TOKENIZED_FINDINGS.pt_BR.md), [PLAN_G_TIER.pt_BR.md](PLAN_G_TIER.pt_BR.md)

---

## Problema

**Discovery** e **reporting** open-core já existem; **remediação** (tokenizar, mascarar, criptografar no lugar) é específica de parceiro. Sem **contrato de plugin estável**, cada integração bifurca o core e quebra a narrativa de auditoria.

---

## Objetivo

Definir hook **Enterprise** pós-scan que:

1. Recebe **mapa estruturado de findings** (localização + `pii_type` + id estável).
1. Invoca **plugin de terceiro** registrado (tokenização, masking, pseudonimização, criptografia de campo).
1. Suporta **re-scan de verificação** e campos de **audit trail** documentados nos use cases.

**Modelo de IP:** tokenizador/remediador permanece **terceiro**; Data Boar detém discovery, orquestração e export de evidência.

---

## Fases

| Fase | Entregável | Status |
| ---- | ---------- | ------ |
| **0 – Docs** | Use cases + este plano | 🔄 Em progresso (**#602–605**, **#601**) |
| **1 – Export do remediation manifest** | CLI `--export-remediation-manifest` + JSON schema v1 (ponte para plugins terceiros) | ✅ **#649** |
| **1b – Esqueleto do hook** | Registro mínimo de plugin + driver no-op (`RemediationPlugin`) | ⬜ **#606** (ainda necessário antes de invocar plugin in-process) |
| **2 – Caminho de export** | Opção JSONL de findings tokenizados | ⬜ |
| **3 – Job de re-scan** | Verificação no escopo após plugin | ⬜ |

---

## Fora de escopo (fases 0–1)

- Entregar produto proprietário de HSM ou vault dentro do core.
- Substituir o jurídico em base legal para biometria ou pagamentos.

---

## Aceite (plano)

- [x] Docs de use case em `docs/use-cases/`
- [x] Export JSON do remediation manifest (`--session` + `--export-remediation-manifest`) — **#649**
- [ ] ADR de interface quando o formato estabilizar
- [ ] Hook em código conforme **#606**
