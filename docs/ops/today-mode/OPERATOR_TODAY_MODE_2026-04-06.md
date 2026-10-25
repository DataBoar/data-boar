# Operator Today Mode — 2026-04-06 (Segunda-feira)

> Criado automaticamente no EOD de 2026-04-05 (madrugada).
> Referência: `docs/ops/today-mode/OPERATOR_TODAY_MODE_2026-04-05.md` (dia anterior)

---

## STATUS GERAL

Branch: main — sincronizado com origin.
Última sessão: madrugada 2026-04-04 → 2026-04-05.

---

## PENDÊNCIAS DO DIA ANTERIOR (carryover)

### LEGAL (detalhes em docs/private/)
- [ ] Pendencias juridicas: ver docs/private/ para checklist detalhado

### DATA BOAR / PRODUTO
- [x] **Commit e push** (ansible/, USAGE.md) — **feito** (2026-04-09): `origin/main` inclui deploy Ansible e doc; `USAGE.pt_BR` com seção Ansible em commit `docs(usage): …`.
- [ ] **Testar playbooks Ansible localmente** (se LAB-NODE-01 lab-op disponível)
      → `ansible-playbook site-full.yml --check -i inventory/hosts.ini`
- [x] **Adicionar seção Ansible ao USAGE.pt_BR.md** (sync EN→pt-BR) — **feito** (2026-04-09).
- [ ] **PLANS_TODO.md**: marcar Ansible como adicionado (H3/houseclean ou feature)
- [x] **Branding rename**: ADR 0014 — `pyproject` / docs em **`data-boar`** (PyPI publish quando agendado)
      → `docs/adr/ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md`

### REDES SOCIAIS / FOUNDER
- [ ] **Revisar posts LinkedIn e X revisados** (blobs + lab-op + milestones) e decidir se publica
- [ ] **Corporate-Entity-B**: aguardar kit de onboarding físico antes de atualizar LinkedIn

### INFRAESTRUTURA / HOMELAB
- [ ] **Adaptador USB-C do NVMe** — tentar montar disco clonado (verificar parafuso + partição)
- [ ] **VeraCrypt setup** — sequenciar conforme `docs/private/homelab/VERACRYPT_PRIVATE_REPO_SETUP.pt_BR.md`

---

## PRIORIDADES RECOMENDADAS PARA HOJE

1. ~~**COMMIT Ansible + USAGE.md**~~ / ~~**pt-BR sync do USAGE.md**~~ — concluído 2026-04-09.
2. **Verificar open PRs**: `gh pr list --state open`
3. **check-all**: `.\scripts\check-all.ps1` — confirmar que tudo verde
4. Se tiver energia: atualizar PLANS_TODO.md com status atual

---

## TIMINGS / LEMBRETES

- **Cadência de estudos (combinado):** 2× CWL + 1× IA por semana (ou 1× outro)
  → CWL: BTF → C3SA → seq. em `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` §3.2
- **Corporate-Entity-B**: não atualizar LinkedIn até receber kit físico
- **Corporate-Entity-C**: aguardar retorno de Portugal antes de follow-up

---

## REFERÊNCIAS RÁPIDAS

- Dossie privado: `docs/private/legal_dossier/`
- Carta CISO v4 (CVEs): `CARTA_DISCLOSURE_CISO_v4_CVEs.txt`
- Carta CISO v3 (Wazuh): `CARTA_DISCLOSURE_CISO_v3.txt`
- Ansible deploy: `deploy/ansible/README.md`
- ADR rename: `docs/adr/ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md`
- Plans: `docs/plans/PLANS_TODO.md`