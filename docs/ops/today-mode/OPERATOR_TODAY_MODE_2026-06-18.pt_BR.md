# Today-mode do operador — 2026-06-18 (Maestro e2e "pra valer" → handoff pro Cursor)

**English:** [OPERATOR_TODAY_MODE_2026-06-18.md](OPERATOR_TODAY_MODE_2026-06-18.md)

**Nota:** Mesmo plano combinado com o operador + o auditor read-only (Claude Code) + o Cursor, cada um no seu tempo. As três frentes seguem — **A (Vault, warm-up isolado) → B (Maestro smoke → completão) → C (gate de release #406, alimentado pelo B)** — mas **o destaque de hoje é o B**: ontem (17) o Claude passou o dia em **micro-fixes do Maestro** (vários, como esperado); hoje ele tem a chance de uma **rodada end-to-end pra valer**, e depois deve vir o **handoff pro Cursor**. O detalhe operacional completo (hostnames de lab, especificidades de Vault/iPhone) fica no **mapa privado**, não neste arquivo versionado.

**Âncora `main`:** `139f754c` — o último merge de PR com CI verde foi o **#939** (`102cd74f`, tagline forensic-grade no README). A faxina de docs de ontem entrou: **#921** (glossário: provenance / cadeia SAST / DMBOK), **#923** (ignore do `mariadb` no pip-audit + follow-up #926), **#920** (glossário TAMPERED/TINTED), **#924/#925** (ADR-0070 + reorg de primers), **#927** (INVENTORY.sig re-assinado), **#928** (tabela TESTING), **#930** (chaves man5), **#933/#934/#936** (espelhos pt-BR, highlights 1.7.3, QUICKSTART), **#938** (audience-guide), **#939** (tagline README), além do Dependabot **#911** (codeql-action).

**Mapa privado (detalhe completo):** `docs/private/ops/NEXT_SESSION_MAP_3_FRONTS_VAULT_MAESTRO_GATE.pt_BR.md`

---

## Bloco 0 — Realidade da manhã (10–15 min)

Rode **`carryover-sweep`** / **`./scripts/operator-day-ritual.sh -Mode Morning`** (ou `.ps1`). Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · confirme `ci.yml` verde no `main` (`139f754c`).
2. **PRs abertos:** `gh pr list --state open` — **três** do Dependabot (#915, #914, #912); **fora** das três frentes, **segurados** até o handoff do Maestro (não perturbar o ambiente do bench).
3. **Stack privada:** se `docs/private/` mudou de madrugada, `./scripts/private-git-sync.sh -Push` (ou `.ps1`).

**Fila contínua:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)

---

## Prioridade — as três frentes (o B é o destaque de hoje)

### B — Maestro: rodada end-to-end pra valer, depois handoff pro Cursor (destaque)

- Ontem: o Claude (auditor read-only) rodou **micro-fixes do Maestro** — vários entraram; o bench está mais perto do que nunca de uma rodada de verdade.
- **Alvo de hoje:** uma **rodada e2e pra valer** — primeiro completão real depois dos ajustes recentes no repo + Maestro, em especial o novo **Handler Capo** para **validação de enforcement de JWT** (defesa comercial). O completão ainda **não** foi rodado pra valer.
- Papéis: o auditor **interpreta/dirige** a análise (completão é **read-only** para o Claude); o **Cursor executa o `pwsh`** quando o handoff chegar.
- **Handoff pro Cursor:** quando a rodada e2e estiver saudável, o Claude passa o completão multi-host sob o Maestro pro Cursor. O Cursor deve estar pronto para: rodar `lab-completao-orchestrate.ps1 -Privileged`, ler os logs em `docs/private/homelab/reports/` e alimentar a frente C.
- Capture Lessons Learned (timeouts, latência, FP/FN vs verdade sintética, confiança em caminhos reais) para o arquivo oficial (`lab-lessons`).

### A — Sync do Vault (warm-up isolado, fora do gate)

- **CouchDB self-hosted** num host de lab com bastante disco livre (o caminho P2P do LiveSync foi abandonado).
- **Pré-requisito:** `podman logout docker.io` antes de subir o container.
- CouchDB no ar → plugin Self-hosted LiveSync no laptop e no celular → fecha de quebra a task pendente **vault → celular**.
- Independente do gate — bom como warm-up enquanto a rodada do Maestro roda. Especificidades (hostnames, caminhos, celular) → **mapa privado**.

### C — Gate de release #406 (alimentado pelo B)

Enquadramento honesto: **prontos para tentar**, sabendo que o gate é **fail-closed** e existe para dizer o que falta. Bloqueadores conhecidos a confirmar antes/durante:

- **G1 (único blocker de conteúdo conhecido):** `py7zr` + `nfs-utils` no host de lab Void.
- `boar_fast_filter` compilado nos quatro hosts de lab.
- Bug `$HOME=root` nos ensure scripts.
- **Regra de ouro:** a **primeira rodada do gate é SEM licença** — fail-closed **tem que falhar** (= teste #1). Nunca exigir `dev.lic` primeiro; a licença só entra na **segunda** rodada. Matriz de três eixos (enforcement / permissões por tier / FP-FN).
- Só depois do gate passar: bump `1.7.4-rc → 1.7.4`, CHANGELOG, Docker Hub, GitHub Release.

**Sequência:** A (rápida, isolada) → B (rodada e2e → handoff) → C (gate, alimentado pelo B).

---

## Carryover — secundário (não são as três frentes)

- [ ] **Fila Dependabot (slice `deps`, SEGURADA até o handoff do Maestro):** **#915** (`hatchling >=1.30.1`), **#914** (grupo `uv-minor-patch` ×12), **#912** (`SonarSource/sonarqube-scan-action` 8.1→8.2 — **bloqueado**: o token do `gh` precisa do escopo `workflow`, ou mergear pela UI web). Aplicar local + validar conforme `.cursor/skills/dependabot-recommendations/SKILL.md` — **não mergear às cegas** (a quebra do `rpds-py` CalVer em 2026-06-16 é o aviso; a trava `rpds-py<2026` + o ignore no `dependabot.yml` já protegem). Não bloqueia o gate, e está **adiada** de propósito para o ambiente do bench ficar estável.
- [ ] **Revisão do ignore `mariadb` PYSEC-2026-217 (#926):** revisitar o ignore do `pip-audit` adicionado no #923 quando sair uma versão corrigida do `mariadb`.
- [ ] **Follow-up #685:** quando o `docs/primers/FORENSICS_AND_EVIDENCE_PRIMER.md` entregar, adicionar o link dele na nova tagline "forensic-grade" do README (adiado conforme a AC do #693).
- [ ] Itens rolantes: [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) (LAB-OP #756 disco do host de lab, evidência da matriz de DB do Maestro, etc.).

---

## Fim do dia (2026-06-18)

- `eod-sync` + `private-stack-sync` se a stack privada mudou.
- Registre as Lessons Learned do Maestro/gate (`lab-lessons`) se uma rodada de completão fechou — **especialmente** se a primeira rodada e2e pra valer rodou hoje.
- Caminho do checklist de amanhã: `OPERATOR_TODAY_MODE_2026-06-19.md` (criar no próximo `eod-sync` se faltar).

---

## Referências rápidas

- Mapa privado (detalhe completo): `docs/private/ops/NEXT_SESSION_MAP_3_FRONTS_VAULT_MAESTRO_GATE.pt_BR.md`
- Palavras-chave de sessão: `.cursor/rules/session-mode-keywords.mdc` (`today-mode`, `carryover-sweep`, `eod-sync`, `completao`, `lab-lessons`, `deps`)
- Runbook do completão: `docs/ops/LAB_COMPLETAO_RUNBOOK.md` · regra de workflow: `.cursor/rules/lab-completao-workflow.mdc`
- Gate de release: issue **#406**; ordem de release: `.cursor/rules/release-publish-sequencing.mdc`
- Ritual Dependabot: `.cursor/skills/dependabot-recommendations/SKILL.md`
