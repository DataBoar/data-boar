# Modo hoje do operador — 2026-05-14 (carryover + foco)

**English:** [OPERATOR_TODAY_MODE_2026-05-14.md](OPERATOR_TODAY_MODE_2026-05-14.md)

---

## Bloco 0 — Realidade de manhã (10–15 min)

1. **`origin/main`:** `git pull origin main` (CI em execução para os 10 commits de ontem — verificar).
2. **Dependabot:** 3 PRs open (#355 uv minor/patch, #348 hatchling, #347 chardet) + #346 ebcdic conflitante com DRAFTs #349–352. Avaliar na sessão `deps`.
3. **VeraCrypt Z:** fsync error no push privado de 2026-05-14 00:01. Verificar montagem e rodar `.\scripts\private-git-sync.ps1 -Push` novamente.
4. **Working tree:** `git status -sb` — deve estar limpo após ontem.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

---

## Carryover de 2026-05-13

### Pendências reais (apenas 2)

- [ ] **Evidência matriz DB Maestro (all-to-all)** — rodada consolidada com configs por host em `docs/private/homelab/reports/`. Corrigir NFS/CIFS antes de rodar (sudoers nas 3 máquinas ainda com erro `sudo: password required`).
- [ ] **Sprint closure pós-`1.7.4`** — escolher UMA: S3 CNPJ fase 5, S1 Bandit fase 3, ou S2 Scope import fase E. Rodar `feature` + `check-all`.

### Bugs Maestro confirmados (prioridade alta quando abrir sessão lab)

- [ ] **Bug 1 — SSH sem `ConnectTimeout`**: handlers sem `-o ConnectTimeout=15`. Afeta todos os hosts se rede instável.
- [ ] **Bug 2 — `benchmark-rc.yaml` passado como arg posicional** em `Handle-baremetal.ps1` / `Handle-docker.ps1` → smoke sai com exit 2.
- [ ] **Bug 3 — race condition `SleepBeforeCollect`**: 120s atual é paliativo. Sentinel file `$LC_BENCH_ROOT/.completao_done_$RUN_ID` + `Wait-CompletaoSmoke.ps1` correto.

### Social / editorial (ontem não foi feito)

- [ ] **L3 LinkedIn (lab-op Ansible)** — alvo era 2026-05-13; publicar e registar permalink.
- [ ] **X5 relaunch** — overdue (alvo era 2026-05-10); fio 6 tweets, validar com `uv run python scripts/social_x_thread_lengths.py`.

---

## O que foi feito ontem (2026-05-13)

**Qualidade e detecção:**
- 4 P0/P1 Gemini resolvidos (min_confidence docs, minor pt-BR, boar_fast_filter encoding, SQLite ACID)
- CPF/CNPJ FP gate + corpus 266 CPFs verificados + `cpf_fiscal_region()` (Provimento CNJ 63/2017)
- 40 testes + 140 subtests CPF verde
- 6 Warm Gemini resolvidos (CI postura, PII memória, locale "arquivo" fix, routing FP, merge additive, jurisdiction collision)
- **P1 fechado:** legacy dirs `utils/`, `scanners/`, `logging_custom/` fora de exclude (930 LOC cobertas)
- **P3 fechado:** B608 global skip → 10× `# nosec B608` inline com justificativa (qualquer B608 novo quebra CI)

**Docs / ADRs:**
- ADR-0050 melhorado (add_plan_metadata.py + gate new plans)
- Carryover limpo: 19 → 2 itens reais + 6 itens fechados por confirmação do operador

**Infra:**
- 10 commits pushed para origin/main; CI em execução
- Private sync: 18 arquivos, 3 lab remotes OK (Z: com erro fsync — verificar)

---

## Fim do dia de amanhã

- **`eod-sync`** + verificar se CI dos 10 commits ficou verde
- Se fizer Maestro: `private-stack-sync` depois da rodada para capturar reports
- `block-close` + VeraCrypt fix se Z: ainda em erro

