# Modo hoje do operador — 2026-04-20 (sincronizar `main`, PyPI opcional, cadência lab)

**English:** [OPERATOR_TODAY_MODE_2026-04-20.md](OPERATOR_TODAY_MODE_2026-04-20.md)

**Tema:** o **`main` local tinha **dois commits** ainda não no `origin`** no EOD de 2026-04-19 (docs relógio/today-mode + empacotamento PyPI **Hatchling** / `pypi-publish.ps1` / ADR 0031). **Primeiro:** `git push origin main` quando fizer sentido (ou PR se batch diferente). **Opcional:** primeiro upload **PyPI** do pacote **`data-boar`** com **`UV_PUBLISH_TOKEN`** — ver **`CONTRIBUTING.pt_BR.md`** (*Publicação no PyPI*). **Cadência:** **–1L** / **`HOMELAB_VALIDATION.md`** quando houver tempo de hardware — não bloqueia o push.

---

## Bloco 0 — Manhã (10–15 min)

Roda **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Depois:

1. **`git fetch origin`** · **`git status -sb`** — confirmar se **`origin/main`** já absorveu os commits locais após o push.
2. **Privado empilhado:** se **`docs/private/`** mudou, **`.\scripts\private-git-sync.ps1`** (e **`-Push`** conforme hábito).

**Fila:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (hub privado) — ~2 min

- [ ] Olhar **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** por **Alvo** em **2026-04-20** — [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).

---

## Carryover — do EOD 2026-04-19

- [ ] **`git push origin main`** — publica commits de docs + packaging (confirmar **`check-all`** verde localmente se não correste antes do commit).
- [ ] **PyPI (opcional, superseded):** fluxo atual = dispatch OIDC (`pypi-publish.ps1 -Target testpypi|pypi`) — ver **`CONTRIBUTING.pt_BR.md`**; item histórico abaixo usava token.
- [ ] **`.vscode/`** — untracked no EOD; ignorar, gitignore ou commit **só** se for intencional.

---

## Fim do dia

- **`eod-sync`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Eod`**
- Reler ou criar **`OPERATOR_TODAY_MODE_2026-04-21.md`** a partir do template se precisar

---

## Referências rápidas

- **`docs/ops/CURSOR_AGENT_POLICY_HUB.pt_BR.md`** — “hoje” situacional + relógio da estação
- **`scripts/pypi-publish.ps1`** · **`CONTRIBUTING.pt_BR.md`** (PyPI)
- Atalhos: **`private-stack-sync`**, **`eod-sync`**
