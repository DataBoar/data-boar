# Today mode do operador — 2026-08-15 (triage deps + sequências #1586)

**English:** [OPERATOR_TODAY_MODE_2026-08-15.md](OPERATOR_TODAY_MODE_2026-08-15.md)

**Manchete:** Carryover de manhã → triage **Dependabot** (Actions primeiro) → seguir sequências de pin TCP **#1586**. Cursor = executor; **Claude Code** = auditor RO token-aware; **Codex no nó de auditoria do lab** = segundo auditor opcional quando o slice estiver em PR.

**Relógio da workstation:** `2026-08-15` (−03).

---

## Bloco 0 — Realidade (fecho / próxima manhã)

1. **`main`:** `git fetch` + `git pull origin main` (pós-**#1591** pin Mongo, **#1593** urlsplit SQL, **#1572** zizmor-action).
2. **PRs abertas (produto / segurança):**
   - [#1594](https://github.com/DataBoar/data-boar/pull/1594) — conflito fail-closed em `HostResolutionPin` (**merge quando CI verde**; Security Agent pediu re-auditoria).
3. **Não reabrir:** pin Postgres **#1589** · pin Mongo **#1591** · teste urlsplit **#1593** (já em `main`).
4. - [ ] **`carryover-sweep` / `morning-readiness`** no início do próximo bloco · **`block-close`** / **`eod-sync`** nas fronteiras.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · Dia anterior: [OPERATOR_TODAY_MODE_2026-08-13.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-13.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Skim `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (Alvo **2026-08-15** / **2026-08-16**).

---

## Sequência sugerida

### A — Dependabot (`deps`) — em breve, sem merge às cegas

Triage com **`.cursor/skills/dependabot-recommendations/SKILL.md`** + **`SECURITY.md`**. Preferir bumps de **Actions** antes de majors Python.

| Ordem | PR | Notas |
| ----- | -- | ----- |
| 1 | [#1574](https://github.com/DataBoar/data-boar/pull/1574) codeql-action/init **4.37.6** | Patch Actions; MERGEABLE — baixo blast radius |
| 2 | [#1573](https://github.com/DataBoar/data-boar/pull/1573) setup-python **7.0.0** | Major Actions — ler changelog / matriz CI |
| 3 | [#1487](https://github.com/DataBoar/data-boar/pull/1487) reportlab **5** · [#1485](https://github.com/DataBoar/data-boar/pull/1485) webauthn **3** · [#1484](https://github.com/DataBoar/data-boar/pull/1484) pyarrow **25** | Majors uv — um de cada vez; `check-all` + smoke |

Auditor opcional: Claude Code (RO token-aware) ou **Codex no nó de auditoria do lab** no diff do Dependabot antes do merge.

### B — Sequências #1586 (depois / entre deps)

| Passo | Item | Notas |
| ----- | ---- | ----- |
| 0 | Landar **#1594** | Conflito de pin fail-closed |
| 1 | Pin Redis (subclass) | Próximo na matriz de design |
| 2 | MySQL / Oracle | Caso a caso; spike TLS |
| — | mssql | Adiado → [#1588](https://github.com/DataBoar/data-boar/issues/1588) |

**Papéis AI:** Cursor implementa; Claude Code audita token-aware; Codex no **nó de auditoria do lab** quando quiser segundo vendor (ADR-0062).

### C — Não padrão hoje

- Maestro **#32** preflight OTel (só se o foco lab ganhar de A/B)
- Ondas de pesquisa sem AIIDCOBPP + P*

---

## Carryover — linhas do dia

- [ ] Atualizar linha Dependabot no **CARRYOVER** (PRs de Actions)
- [ ] Mergear ou agendar **#1594**
- [ ] Triar **≥1** PR Dependabot (preferir **#1574**)
- [ ] Se sobrar energia: começar slice **Redis** #1586 **ou** estacionar com data
- [ ] Sem commit de produto sem `check-all` / CI verde nessa PR

---

## Fim do dia

- **`block-close`** + VeraCrypt (política privada) ao sair de bloco profundo
- **`eod-sync`** para git/gh/PR + ponteiro de amanhã
- Amanhã: **`OPERATOR_TODAY_MODE_2026-08-16.md`**

---

## Referências rápidas

- Issue [#1586](https://github.com/DataBoar/data-boar/issues/1586) · skill **dependabot-recommendations**
- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md` · ADR-0062
- Sessão: **`deps`**, **`feature`**, **`today-mode`**, **`carryover-sweep`**
