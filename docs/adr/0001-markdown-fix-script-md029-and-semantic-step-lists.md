# ADR 0001: Markdown fix script, MD029, and semantic step lists

**Status:** Accepted
**Date:** 2026-03-25
**Authors:** Fabio Leitao

---

## Context

The project enforces SonarQube- and markdownlint-style rules on `.md` and `.mdc` files via **`tests/test_markdown_lint.py`**. Contributors run **`scripts/fix_markdown_sonar.py`** to auto-fix many violations (MD007, MD009, MD012, MD029, MD031, MD032, MD034, MD036, MD047, MD060, etc.) before CI.

**MD029** (ordered list style) is implemented in the fix script as **all items use the `1.` prefix** (1/1/1 style). That satisfies consistent-list-style checks and keeps diffs simple when items are inserted or reordered.

Some documents use **semantic** ordered lists where readers expect **1. 2. 3.** (e.g. procedures, PR checklists). Normalizing those lists to **1. 1. 1.** hurts readability until someone restores explicit numbering.

## Decision

1. **Keep** MD029 normalization in **`fix_markdown_sonar.py`** as the default behaviour for bulk fixes and CI alignment.
1. **Document** that after running the fix script, authors must **manually restore 1. 2. 3.** where the list is a true sequence of steps (not an unordered set of bullets in disguise).
1. **Do not** (for now) add heuristic “detect step lists” logic in the script; the maintenance cost and false positives outweigh the benefit while the contributor base is small. Revisit if doc churn becomes painful (see alternatives below).

## Consequences

- **Positive:** One mechanical rule for ordered lists; fewer Sonar/markdownlint debates; easy to explain in CONTRIBUTING and Cursor rules.
- **Negative:** Extra manual pass after `fix_markdown_sonar.py` on step-heavy docs; reviewers should spot **1. 1. 1.** in procedures before merge.
- **Alternatives recorded for the future:** (a) skip MD029 in the script for specific file globs or contexts; (b) disable MD029 in lint and fix only where reported; (c) smarter script heuristics for consecutive numbered steps.

## References

- `scripts/fix_markdown_sonar.py` (header and MD029 implementation)
- [CONTRIBUTING.md](../../CONTRIBUTING.md) — Docs bullet (MD029 + manual restore)
- [.cursor/rules/markdown-lint.mdc](../../.cursor/rules/markdown-lint.mdc)
- [QUALITY_WORKFLOW_RECOMMENDATIONS.md](../QUALITY_WORKFLOW_RECOMMENDATIONS.md) — §6
