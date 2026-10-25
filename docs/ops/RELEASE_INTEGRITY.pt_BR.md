# Data Boar | Especificação de Integridade e Segurança de Release

Este documento define os requisitos de integridade, segurança e resiliência das
releases do Data Boar, com foco explícito nos caminhos Pro+.

## 1) Integridade de código e binários

- A evidência de build determinístico do módulo Rust deve ser registrada em
  ambiente isolado.
- Binários gerados (`.pyd` / `.so`) e relatórios (`.pdf` / `.json`) devem ter hash
  SHA-256 para verificação pós-execução.
- Binários de produção devem aplicar stripping de símbolos de debug.

## 2) Resiliência operacional (SRE)

- O auto-throttling deve reduzir concorrência quando a latência média excede o
  `target_latency_ms` configurado.
- O estado do scan deve ser persistido com escrita atômica em `.data_boar_state.json`.
- A retomada após interrupção deve continuar do último offset/id validado.
- O pré-filtro em Rust deve se manter sem panic com entradas malformadas.

## 3) Taxonomia GRC e conformidade

- Achados de cartão de crédito só são válidos quando passam no Luhn (Mod 10).
- Base de pesos de risco:
  - Identificadores comuns: peso 10
  - Dados financeiros: peso 30
  - Dados sensíveis (LGPD Art. 5, II): peso 80
- Artefatos executivos devem incluir timestamp imutável e rastreabilidade por `scan_id`.

## 4) Checklist de integridade de release

- [ ] Evidência de build determinístico Rust registrada.
- [ ] Hashes SHA-256 gerados para binários e artefatos de relatório.
- [ ] Política de stripping aplicada aos binários distribuíveis.
- [ ] Comportamento de throttling validado sob pressão de latência sintética.
- [ ] Retomada por checkpoint validada após crash/interrupção simulada.
- [ ] Gate de Luhn validado para cartões válidos e inválidos.

## 5) Especificações relacionadas

- [INTEGRITY_HUB.pt_BR.md](INTEGRITY_HUB.pt_BR.md) ([EN](INTEGRITY_HUB.md)) — **comece aqui** para tamper detection, módulos de runtime, scripts e inventário ADR.
- [RELEASE_INTEGRITY.pt_BR.md](../RELEASE_INTEGRITY.pt_BR.md) ([EN](../RELEASE_INTEGRITY.md)) — tamper-evidence de **licenciamento** no produto (digest de build, manifesto opcional); escopo distinto desta spec ops de release.
- [INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md](INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md) ([EN](INTEGRITY_CHECK_ALPHA_LOGIC.md)) — defesa opcional de integridade em runtime (desenho).
- [SPRINT_GREAT_LEAP_POSTMORTEM.pt_BR.md](SPRINT_GREAT_LEAP_POSTMORTEM.pt_BR.md) ([EN](SPRINT_GREAT_LEAP_POSTMORTEM.md)) — métricas verificadas vs metas aspiracionais de lab.
