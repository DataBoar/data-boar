# Today-mode do operador — 2026-06-17 (três frentes: Vault → Maestro → gate de release)

**English:** [OPERATOR_TODAY_MODE_2026-06-17.md](OPERATOR_TODAY_MODE_2026-06-17.md)

**Nota:** Plano combinado com o operador + o auditor read-only (Claude Code) + o Cursor, cada um no seu tempo e sidequests. Três frentes, duas delas encadeadas: **A (Vault, warm-up isolado) → B (Maestro smoke → completão) → C (gate de release #406, alimentado pelo B)**. O detalhe operacional completo (hostnames de lab, especificidades de Vault/iPhone) fica no **mapa privado**, não neste arquivo versionado.

**Âncora `main`:** `69549bd9` — **#917** (atestação SSHSIG + âncora de confiança `allowed_signers`, ADR-0056) mergeado. Ontem também entraram **#913** (issuer #910 com passphrase de chave cifrada) e **#909** (ADR-0069, trava `rpds-py<2026`).

**Mapa privado (detalhe completo):** `docs/private/ops/NEXT_SESSION_MAP_3_FRONTS_VAULT_MAESTRO_GATE.pt_BR.md`

---

## Bloco 0 — Realidade da manhã (10–15 min)

Rode **`carryover-sweep`** / **`./scripts/operator-day-ritual.sh -Mode Morning`** (ou `.ps1`). Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · confirme `ci.yml` verde no `main` (`69549bd9`).
2. **PRs abertos:** `gh pr list --state open` — quatro do Dependabot (veja carryover abaixo); **fora** das três frentes.
3. **Stack privada:** se `docs/private/` mudou de madrugada, `./scripts/private-git-sync.sh -Push` (ou `.ps1`).

**Fila contínua:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)

---

## Prioridade — as três frentes (combinado)

### A — Sync do Vault (warm-up isolado, fora do gate)

- O caminho P2P do LiveSync foi abandonado; pivô para **CouchDB self-hosted** num host de lab com bastante disco livre.
- **Pré-requisito:** `podman logout docker.io` antes de subir o container.
- CouchDB no ar → plugin Self-hosted LiveSync no laptop e no celular → isso fecha de quebra a task pendente **vault → celular**.
- Independente do gate — bom como warm-up de manhã, com o auditor read-only.
- Especificidades operacionais (hostnames, caminhos, celular) → **mapa privado**.

### B — Benchmarking do Maestro (smoke → rodada pra-valer → handoff completão)

- Ramp: **micro-bench smoke** (sanity rápido, por host, cenários cada vez mais completos/complexos) → **uma rodada pra-valer** (operador interpreta/dirige a análise — completão é **read-only** para o auditor; o Cursor executa o `pwsh`) → **handoff** para o completão multi-host sob o Maestro.
- **Primeiro completão de verdade depois** dos ajustes recentes no repo + Maestro — em especial o novo **Handler Capo** para **validação de enforcement de JWT** (defesa comercial). O completão ainda **não** foi rodado pra valer; esta é a primeira passada real.
- Capture Lessons Learned (timeouts, latência, FP/FN vs verdade sintética, confiança em caminhos reais) para o arquivo oficial.

### C — Gate de release #406 ("finalmente?")

Enquadramento honesto: **prontos para tentar**, sabendo que o gate é **fail-closed** e existe para dizer o que falta. Bloqueadores conhecidos a confirmar antes/durante:

- **G1 (único blocker de conteúdo conhecido):** `py7zr` + `nfs-utils` no host de lab Void.
- `boar_fast_filter` compilado nos quatro hosts de lab.
- Bug `$HOME=root` nos ensure scripts.
- **Regra de ouro:** a **primeira rodada do gate é SEM licença** — fail-closed **tem que falhar** (= teste #1). Nunca exigir `dev.lic` primeiro; a licença só entra na **segunda** rodada. Matriz de três eixos (enforcement / permissões por tier / FP-FN).
- Só depois do gate passar: bump `1.7.4-rc → 1.7.4`, CHANGELOG, Docker Hub, GitHub Release.

**Sequência:** A (rápida, isolada) → B (smoke → completão) → C (gate, alimentado pelo B).

---

## Carryover — secundário (não são as três frentes)

- [ ] **Fila Dependabot (slice `deps`):** **#915** (`hatchling >=1.30.1`), **#914** (grupo `uv-minor-patch` ×12), **#912** (`SonarSource/sonarqube-scan-action` 8.1.0→8.2.0), **#911** (`github/codeql-action` 4.36.0→4.36.2). Aplicar local + validar conforme `.cursor/skills/dependabot-recommendations/SKILL.md` — **não mergear às cegas** (a quebra do `rpds-py` CalVer em 2026-06-16 é o aviso; a trava `rpds-py<2026` + o ignore no `dependabot.yml` já protegem). Não bloqueia o gate.
- [ ] Itens rolantes: [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) (LAB-OP #756 disco do host de lab, evidência da matriz de DB do Maestro, etc.).

---

## Fim do dia (2026-06-17)

- `eod-sync` + `private-stack-sync` se a stack privada mudou.
- Registre as Lessons Learned do Maestro/gate (`lab-lessons`) se uma rodada de completão fechou.
- Caminho do checklist de amanhã: `OPERATOR_TODAY_MODE_2026-06-18.md` (criar no próximo `eod-sync` se faltar).

---

## Referências rápidas

- Mapa privado (detalhe completo): `docs/private/ops/NEXT_SESSION_MAP_3_FRONTS_VAULT_MAESTRO_GATE.pt_BR.md`
- Palavras-chave de sessão: `.cursor/rules/session-mode-keywords.mdc` (`today-mode`, `carryover-sweep`, `eod-sync`, `completao`, `lab-lessons`, `deps`)
- Runbook do completão: `docs/ops/LAB_COMPLETAO_RUNBOOK.md` · regra de workflow: `.cursor/rules/lab-completao-workflow.mdc`
- Gate de release: issue **#406**; ordem de release: `.cursor/rules/release-publish-sequencing.mdc`
- Ritual Dependabot: `.cursor/skills/dependabot-recommendations/SKILL.md`
