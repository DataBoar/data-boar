# Today mode do operador - 2026-07-12 (carryover-sweep + fila deps)

**English:** [OPERATOR_TODAY_MODE_2026-07-12.md](OPERATOR_TODAY_MODE_2026-07-12.md)

**Manchete:** `carryover-sweep` executado; PR **#1209** mergeado em `main`; fila ativa agora e triagem de Dependabot + compromissos da fila viva.

---

## Bloco 0 - Realidade de manhã (10-15 min)

Status do `carryover-sweep` (ja executado):

- Estado da branch: `fix/prefilter-recall-parity-1198...origin/fix/prefilter-recall-parity-1198`
- PRs abertos: **#1178**, **#1107**, **#975**
- CI mais recente em `main`: run mais novo em andamento depois do merge do **#1209**
- Arquivo today-mode de hoje: agora presente

Depois:

1. **Sincronizar com a branch canonica:** `git checkout main && git pull origin main`.
2. **Higiene de branch:** se nao houver mais trabalho em `fix/prefilter-recall-parity-1198`, encerrar branch local apos o sync.
3. **Triagem deps (fatias finas):** decidir ordem e estrategia para **#1178**, **#1107**, **#975** (modo `deps`; sem merge cego).
4. **Alinhamento de carryover:** revisar [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) e escolher um item de varios dias para avancar hoje.
5. - [ ] **Block close (lab / VC):** ao pausar mais tarde, usar `block-close` e seguir politica privada VeraCrypt em `docs/private/homelab/OPERATOR_VERACRYPT_SESSION_POLICY*.md`.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)
**Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Olhar `docs/private/social_drafts/editorial/SOCIAL_HUB.md` para linhas com alvo hoje/amanha.

---

## Carryover - hoje

- [ ] **Fila Dependabot:** triagem/plano para **#1178**, **#1107**, **#975**.
- [ ] **Carryover de longo curso:** manter avanco em um item ativo de [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) (Maestro/private stack ou fila de seguranca).
- [ ] **Fronteira de sync privado:** se notas privadas mudarem hoje, agendar `private-stack-sync` antes do fechamento final.

---

## Fim do dia

- Usar `block-close` para fronteira de bloco/lab e higiene VeraCrypt.
- Usar `eod-sync` (ou `.\scripts\operator-day-ritual.ps1 -Mode Eod`) para refresh git/gh e ponte para amanha.
- Preparar ou revisar `OPERATOR_TODAY_MODE_2026-07-13.pt_BR.md`.

---

## Referencias rapidas

- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md`
- `.cursor/rules/session-mode-keywords.mdc`
- `docs/ops/COMMIT_AND_PR.pt_BR.md`

