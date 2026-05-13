# Modo hoje do operador — 2026-05-13 (carryover + foco efetivo)

**English:** [OPERATOR_TODAY_MODE_2026-05-13.md](OPERATOR_TODAY_MODE_2026-05-13.md)

---

## Bloco 0 — Realidade de manhã (10–15 min)

Rode **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**.

1. **`origin/main`:** `git pull origin main` se estiver atrás.
2. **Working tree:** decide — commits, branch, stash.
3. **Git privado:** `.\scripts\private-git-sync.ps1 -Push` se houver fila nova.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (hub privado) — ~2 min

- [ ] **L3 LinkedIn (lab-op Ansible)** — **Alvo hoje (2026-05-13)**; rascunho em `docs/private/social_drafts/drafts/2026-04-23_linkedin_labop_ansible-docker-ce-e-swarm-no-t14-lab-op-.md` — publicar e registar permalink no hub.
- [ ] **X5 relaunch** — overdue (alvo era 2026-05-10); fio 6 tweets, validar com `uv run python scripts/social_x_thread_lengths.py` antes de postar.
- [ ] **L6 / W5 / T3 / IG3 / B1** — kit LLM incident; sequência esta semana (L6 hoje/amanhã, W5 quinta, T3+IG3 sexta, B1 qualquer dia).
- [ ] **P3b** — permalinks Facebook L1+L5 ainda pendentes; colher em Gerenciar Posts quando tiveres sessão Meta.

---

## Carryover de 2026-05-12

### Produto / repo

- [ ] **P1 — Gap Bandit/Ruff em dirs legacy** (`utils/`, `scanners/`, `db/`, `logging_custom/`): 16 arquivos .py excluídos de ambos os linters; `utils/notify.py`, `utils/regex_patterns.py`, `scanners/db_connector.py` são security-relevant. Próximo passo: remover `utils/` e `logging_custom/` de `exclude_dirs` no Bandit e correr `bandit -r . -c pyproject.toml -ll -ii` para ver o delta.
- [ ] **PLAN_SCAN_RUN_MANIFEST Slice 1** — implementação pendente (`_Run Summary` sheet no Excel); nenhuma feature code escrita ainda.
- [ ] **Engajamento A (Setor Jurídico)** — próximo passo: definir alvos de scan com ponto de contato técnico (Ivan); decidir qual conector usar na fase de exploração.
- [ ] **ADR-0050 backfill** — o script `scripts/add_plan_metadata.py` pode ser reaproveitado para novos plans; manter o padrão de header em qualquer `PLAN_*.md` novo.

### Maestro / benchmark — **bugs confirmados (prioridade alta)**

> Fonte: análise de código 2026-05-12. Veja `PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md`.

- [ ] **Bug 1 (crítico) — SSH sem `ConnectTimeout`**: todos os handlers e Maestro.ps1 fazem `ssh -q -o BatchMode=yes` sem timeout. Se um host tiver problema de rede, o processo fica em wait infinito. Fix: adicionar `-o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3` em **todos** os `ssh` dos handlers. Afeta: `Handle-baremetal.ps1:56`, `Handle-docker.ps1:58`, `Handle-web.ps1:98,172,186`, `Maestro.ps1:51`.
- [ ] **Bug 2 (crítico) — `benchmark-rc.yaml` passado como arg posicional desconhecido**: `Handle-baremetal.ps1` e `Handle-docker.ps1` passam `tests/config/benchmark-rc.yaml` diretamente para `lab-completao-host-smoke.sh`, que não reconhece arg posicional e **sai com exit 2 imediatamente**. Todo run `-Deep` em baremetal/docker falha silenciosamente; nenhum artefato é gerado. Fix: adicionar flag `--bench-config` ao smoke script e ao handler.
- [ ] **Bug 3 (race condition) — `-Collect` sem esperar async tmux**: `maestro-benchmark-ab.ps1` chama `-Collect` imediatamente após `-Deep`, mas o smoke está rodando em tmux de forma assíncrona. O `-Collect` tenta SCP de artefatos que ainda não existem. Fix: sentinel file (`$LC_BENCH_ROOT/.completao_done_$RUN_ID`) + `Wait-CompletaoSmoke.ps1`, ou `-SleepBeforeCollect 120` como paliativo.
- [ ] **Hybrid-173 como spec** — `scripts/lab-completao-orchestrate-hybrid-v173.ps1` e variantes plano-a..v têm medições que funcionaram. Estudar para portar `boar_fast_filter` import timing, detached tmux session create, e JSONL event stream para o Maestro moderno.
- [ ] **`boar_fast_filter` timing** — o PyO3 fix no v1.7.4-rc pode estar mais rápido que v1.7.3 mas nunca foi medido no Maestro. Após bugs 1–3 corrigidos, rodar `maestro-benchmark-ab.ps1 -BenchCompare` para confirmar.

### Novos plans criados esta sessão

- `PLAN_LOCUST_LOAD_TEST_INTEGRATION.md` — Locust como persona `loadtest` no Maestro (H2)
- `PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md` — bugs + full test matrix (H1)

### Backlog aberto (não urgent hoje, mas não esquecer)

- [ ] **B608 global Bandit skip** → migrar para `# nosec B608` inline nos connectors específicos; tirar do skip global (P3 hardening).
- [ ] **Plan ADR-0052 (manifest/schema ADR)** — defer após Slice 1 da feature implementado; criaremos o ADR quando o schema estiver estável.
- [ ] **private-stack-sync VeraCrypt (Z:)** — volume não montado ontem; confirmar sync bare na próxima sessão com Z: disponível.

### Social backlog (além do imediato)

- [ ] **L7 futuro** — post LinkedIn sobre "o que o Data Boar faz num engajamento de adequação LGPD" (narrativa de consultoria; depois do primeiro resultado real com Engajamento A).
- [ ] **Patreon** — atualizar tiers conforme modelo de open-core ficou mais claro; ver `PATREON_DATA_BOAR_PAGE_COPY.pt_BR.md`.

---

## Sessão de ontem — o que foi feito (2026-05-12)

ADRs 0046–0050 criados/melhorados; `.cursorrules` legacy migrado e deletado (guard em pre-commit); skill `linguistic-rigor-active-voice` criada; 55 `PLAN_*.md` públicos com metadata ADR-0050; 2 plans privados atualizados; README pitch + consulting slice; ENGAGEMENT_TRACKER privado; private sync completo (123 arquivos, 3 remotes).

---

## Fim do dia

- **`block-close`** + VeraCrypt ao terminar bloco.
- **`eod-sync`** para git/gh/PR + preparar `OPERATOR_TODAY_MODE_2026-05-14.md`.
