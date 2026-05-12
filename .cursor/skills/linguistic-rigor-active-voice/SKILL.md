---
name: linguistic-rigor-active-voice
description: Checklist for enforcing NASA-style active voice, LCM Level 1/2 verbs, and canonical Data Boar lexicon stability in code, docs, commit messages, and PR reviews. Use when writing or reviewing docstrings, module comments, PowerShell CBH, Python function names, technical docs, or any prose produced for this repo.
---

# Linguistic Rigor — Active Voice and Lexicon Stability

Policy source: `persona-rigor.mdc` + `linguistic-rigor-and-performance.mdc` (both `alwaysApply: true`).
This skill provides a **practical checklist** for use during writing and PR review.

---

## 1. Voice gate — find and replace

**Forbidden (passive voice) — flag and rewrite:**

| Passive (forbidden) | Active replacement |
|---|---|
| "foram feitos" | "O sistema executou" / "O script gerou" |
| "é permitido" | "O gate permite" / "O operador pode" |
| "são aplicados" | "O módulo aplica" / "O detector impõe" |
| "Os logs são gerados" | "O sistema gera logs" |
| "É processado" | "O conector processa" |

Rule: the **subject** must be a concrete actor (module, script, gate, operator) performing the action — never the action itself happening to an unnamed subject.

---

## 2. LCM Level 1–2 — verb precision for code descriptions

Use **Level 1/2 Linguistic Category Model** verbs when describing code behavior in docstrings, CBH headers, and commit messages. These describe **concrete, observable actions**:

- ✅ `executes`, `validates`, `emits`, `filters`, `samples`, `raises`, `returns`, `inserts`, `truncates`
- ❌ `handles`, `manages`, `deals with`, `processes things`, `helps` (vague; no observable action)

**Applying to Python docstrings:**

```python
# Bad (LCM Level 3 — abstract)
def sample_column(conn, col):
    """Handles column sampling."""

# Good (LCM Level 1 — concrete observable action)
def sample_column(conn, col):
    """Executes a non-null sample query against *col* and returns up to N rows."""
```

**Applying to PowerShell CBH `.SYNOPSIS`:**

```powershell
# Bad
# .SYNOPSIS Manages lab connections.

# Good
# .SYNOPSIS Establishes an SSH session to the lab host and returns the exit code.
```

---

## 3. Canonical lexicon — four frozen terms

These four terms are **never renamed, aliased, or replaced** in any operator- or customer-facing surface (reports, docs, CLI output, marketing copy):

| Term | Canonical meaning |
|---|---|
| **Data Sniffing** | Discovery and sampling pass |
| **Deep Boring** | Structured compliance-report depth |
| **Safe-Hold** | Safe suspension state — scan halted due to missing or insufficient evidence |
| **Audit Trail** | Immutable session and finding record; evidence chain for compliance reporting |

Breaking-change contract for these terms: **ADR-0048**.

---

## 4. Review checklist

When reviewing a PR, docstring addition, or doc update, run through:

- [ ] No passive constructions in technical narrative or docstrings
- [ ] Every code description names a concrete actor and a Level 1/2 verb
- [ ] None of the four canonical terms are renamed or paraphrased in customer-facing output
- [ ] New product terms added to `docs/GLOSSARY.md` + `docs/GLOSSARY.pt_BR.md` before use (ADR-0048 §5)
- [ ] PowerShell scripts: `.NAME`, `.SYNOPSIS`, `.DESCRIPTION` in CBH reflect current behavior (ADR-0048 §6)

---

## References

- [`persona-rigor.mdc`](../../.cursor/rules/persona-rigor.mdc)
- [`linguistic-rigor-and-performance.mdc`](../../.cursor/rules/linguistic-rigor-and-performance.mdc)
- [ADR-0048 — Operator-facing taxonomy and naming contract preservation](../../docs/adr/ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md)
