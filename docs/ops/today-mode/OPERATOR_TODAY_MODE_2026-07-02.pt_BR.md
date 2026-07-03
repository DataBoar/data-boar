# Today mode do operador — 2026-07-02 (Housekeeping bestiário · Maestro · PRs)

**English:** [OPERATOR_TODAY_MODE_2026-07-02.md](OPERATOR_TODAY_MODE_2026-07-02.md)

**Manchete:** Retomar **housekeeping do ecossistema bestial** (uma besta por vez) → **#2 Maestro** (`set-remote` + branch UMADR) → merge **#1122** / **#1124** quando verde → opcional: commit do wrapper **`beastie-ecosystem-sync`** no `data-boar`.

**Âncora `main` (EOD 2026-07-02):** pós-**#1120**; **`pyproject.toml`** = **`1.7.4.post1`**. **Estável publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md).

**Ontem (sessão 2026-07-01):** inventário honesto + roster reconciliado; **Homing Robin** birth-triplet ADR commit **local** (`ahead 1`, push pendente).

---

## Bloco 0 — Realidade da manhã (10–15 min)

Rodar **`carryover-sweep`** / **`morning-readiness`**. Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · `gh run list --workflow ci.yml --branch main --limit 1`.
2. **PRs abertos (produto):** **#1122** · **#1124** — `gh pr checks` antes de merge.
3. **Sync bestiário:** `./scripts/beastie-ecosystem-sync.sh status` (ou `maestro homing-robin`).
4. **Stack privado (opcional):** `docs/private/commercial/bestiais/` **untracked** — **`private-stack-sync`** só se quiser versionar; roster Obsidian já atualizado.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Inventário:** `docs/private/commercial/bestiais/BEASTIE_INVENTORY_HONEST_2026-07-01.pt_BR.md`

### Social / editorial (~2 min)

- [ ] Passar **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** — [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).

---

## Prioridades

| Ordem | Trilha | Intenção | Notas |
| ----- | ------ | -------- | ----- |
| **1** | **Maestro** | `set-remote maestro` · fechar branch `docs/umadr-genesis-and-reference-stub` | Remote **FabioLeitao** · **AHEAD+2** |
| **2** | **Homing Robin** | `git push` no clone local (commit **770e804**) | Remote já **DataBoar** |
| **3** | **PRs data-boar** | Merge **#1122** + **#1124** | Branch: `docs/adr-0073-band-fix-start-at-1` |
| **4** | **Wrapper** | Commit `beastie-ecosystem-sync.{sh,ps1}` | |
| **5** | **Próximas bestas** | Quati → Crow → Rikki | UMADR só aditivo |
| **6** | **Adiar** | `set-remote` em lote nos skeletons · Dependabot RED | |

---

## Carryover — hoje

- [ ] Push **homing-robin**.
- [ ] **Maestro** drift + branch.
- [ ] **#1122** / **#1124**.
- [ ] Opcional: `private-stack-sync` do inventário.

---

## Fim do dia

- **`eod-sync`** + **`private-stack-sync`** se couber.
- Próximo: **`OPERATOR_TODAY_MODE_2026-07-03.md`**.
