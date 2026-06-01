# Modo de hoje do operador — 2026-05-29 (carryover + foco efetivo)

**English:** [OPERATOR_TODAY_MODE_2026-05-29.md](OPERATOR_TODAY_MODE_2026-05-29.md)

**Nota:** Rascunhado no **eod-sync** após **2026-05-28** — o disco de um nó do lab é a primeira coisa a dimensionar antes do trabalho de produto. Detalhes específicos do host ficam numa nota privada **gitignored**.

**Âncora da `main`:** `2fdfbb11` — **#751** (maestro: redirect PS7 + bypass de locale) mergeado; texto de pitch 30/60/90 (deploy vs maturidade) na **`main`**. PRs abertos: **#664 #663 #662 #661 #660** (Dependabot), **#365** (kill-switch, draft), **#348** (Dependabot hatchling).

---

## Bloco 0 — Realidade da manhã (10–15 min)

Rode **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` se estiver atrás — confirme **`ci.yml`** verde na **`main`** antes de trabalho profundo.
2. **PRs abertos:** `gh pr list --state open` — lote Dependabot (#660–#664) mergear quando verde via **`.\scripts\pr-merge-when-green.ps1`**; pular **#365** enquanto **DRAFT**.
3. **Stack privado:** evidências enviadas no **eod-sync de 2026-05-28** (nota do disco do lab + relatórios complete_eval). Se `docs/private/` mudar durante a noite: **`.\scripts\private-git-sync.ps1 -Push`**.

**Fila contínua:** [CARRYOVER.md](CARRYOVER.md) · **Publicado:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

---

## COMECE AQUI — disco do nó do lab — #756

> **Comece pelo `du`/snapper (dimensionar) antes de qualquer limpeza.** Nome do host + dispositivo + achados estão na nota privada **gitignored** (datada **2026-05-28**) em `docs/private/homelab/`.

| Passo | Ação |
| ----- | ---- |
| 1 | SSH no nó do lab (host no manifesto privado); `/` é **btrfs**, raiz **~90%** (~10 G livres). `btrfs filesystem df /` → Data ~78,8 GiB usados. |
| 2 | **Precisa sudo com TTY** (`ssh -tt <nó>` ou local): `sudo snapper list-configs` · `sudo snapper -c root list` · `sudo btrfs subvolume list -t /`. |
| 3 | Se os snapshots do snapper forem o grosso: revisar datas, `sudo snapper -c root delete <faixa>`; também limpar o cache de pacotes da distro (Void: `sudo xbps-remove -O`). |
| 4 | Meta **≥ 20 G livres**; reconferir `btrfs filesystem df /`; `btrfs balance start -dusage=50 /` se "Data total" continuar inflado. |

---

## Carryover #756 (dois itens pendentes de 2026-05-28)

| # | Item | Estado | Próximo |
| - | ---- | ------ | ------- |
| 1 | **bw CLI num host do lab** | Instalado manualmente via `npm --prefix ~/.local` | Adicionar ao **playbook Ansible** (reprovisionamento idempotente) — ainda não feito |
| 2 | **disco do nó do lab ~90%** | Dimensionado: btrfs, ~78,8 GiB Data, ~10 G livres | Diagnóstico snapper/subvolume (sudo) → limpar para ≥ 20 G — ver nota privada |

**Ver também #753** — `docs/plans/PLAN_CMDB_CI_RELATIONSHIP_IMPORT.md` **pendente de criação** (confirmado ausente na `main`). Criar e rodar **`python scripts/plans_hub_sync.py --write`** quando for retomado.

---

## Foco sugerido (depois do disco do lab)

| Prioridade | Item | Notas |
| ---------- | ---- | ----- |
| **Lab** | #756 disco | Liberar espaço antes de qualquer completão/benchmark nesse nó |
| **Ops** | #756 bw CLI | Idempotência no Ansible — pequeno, fecha o ciclo |
| **Plans** | #753 | Criar `PLAN_CMDB_CI_RELATIONSHIP_IMPORT.md`; rodar `python scripts/plans_hub_sync.py --write` |
| **Deps** | #660–#664 | Lote Dependabot — mergear quando verde |

---

## Fim do dia (**2026-05-29**)

- **`eod-sync`** + **`private-stack-sync`** se o stack privado ou o hub social mudarem.
- Caminho do checklist de amanhã: **`OPERATOR_TODAY_MODE_2026-05-30.md`** (criar no próximo **eod-sync** se faltar).

---

## Referências rápidas

- Palavras-chave de sessão: **`.cursor/rules/session-mode-keywords.mdc`** (**`completao`**, **`eod-sync`**, **`private-stack-sync`**, **`homelab`**)
- Ritmo privado: `docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`
- Nota do disco do lab: gitignored em `docs/private/homelab/` (datada 2026-05-28)
