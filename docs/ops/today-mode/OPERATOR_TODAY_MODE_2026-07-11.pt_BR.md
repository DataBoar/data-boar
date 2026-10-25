# Today mode do operador - 2026-07-11 (gate do split docs + higiene trilho RBAC)

**English:** [OPERATOR_TODAY_MODE_2026-07-11.md](OPERATOR_TODAY_MODE_2026-07-11.md)

**Manchete:** split docs-only do two-tier gate pronto em **#1185**; RBAC segue canônico no **#1143**; **#1124** continua bloqueado após merge-main-in até follow-up do hash de inventário ADR.

---

## Bloco 0 - Realidade de manhã (10-15 min)

Rode **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Depois:

1. `git fetch` + `git status -sb` + deixar explícita a intenção da branch antes de editar.
2. Revisar checks do PR **#1185** e preparar trilho de decisão no gate do operador (sem auto-merge).
3. Manter o **#1143** intocado (trilho canônico RBAC draft) enquanto o split docs entra.
4. Confirmar **#1124** estacionado (sem caminho de force-push; merge-main-in já aplicado).
5. - [ ] **Block close (lab / VC):** ao pausar mais tarde, usar **`block-close`** e seguir política privada do VeraCrypt em `docs/private/homelab/OPERATOR_VERACRYPT_SESSION_POLICY*.md`.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)
**Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Olhar `docs/private/social_drafts/editorial/SOCIAL_HUB.md` para itens com alvo hoje/amanhã.

---

## Carryover - hoje

- [ ] **PR #1185** (`[P3][docs] docs(cursor): two-tier check-all gate`) - aguardando gate do operador e decisão de merge.
- [ ] **PR #1156** já fechado como superseded - manter trilha de auditoria ligada ao #1185 e #1143.
- [ ] **PR #1143** segue trilho canônico RBAC (draft) - não misturar com fatias docs-only.
- [ ] **PR #1124** continua bloqueado por CI (`tests/test_scripts.py::test_inv_adr_inventory_hash_matches_data_lines`) após merge-main-in; sem pedido de assinatura de tripwire no estado atual.

---

## Fim do dia

- Usar **`block-close`** para fronteira de bloco/lab e higiene do VeraCrypt.
- Usar **`eod-sync`** (ou `.\scripts\operator-day-ritual.ps1 -Mode Eod`) para refresh git/gh e ponte para amanhã.
- Preparar ou revisar **`OPERATOR_TODAY_MODE_2026-07-12.md`**.

---

## Referências rápidas

- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md`
- `.cursor/rules/session-mode-keywords.mdc`
- `docs/ops/COMMIT_AND_PR.pt_BR.md`
