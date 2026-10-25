# ADR 0077 — Filesystem scan does not honor client `.gitignore` (deliberate design)

- **Date (UTC):** 2026-06-30
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Accepted

### Status history

- 2026-06-30 — Accepted (audit closure GitHub #1080, RO-verified)

## Context

Research compared the filesystem connector to **ripgrep**'s `ignore` crate patterns (#1080). The connector has **no** `.gitignore` / `.boarignore` filtering today.

For a **compliance-oriented inventory** scanner, honoring a repository's `.gitignore` would **hide paths the data owner chose to exclude from version control** — often exactly where sensitive exports, dumps, or local caches live. That conflicts with **defensive scanning** and **shadow-data** discovery goals ([PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](../plans/PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md) narrative).

## Decision

1. **Default behaviour:** filesystem walks **do not** apply `.gitignore`, `.dockerignore`, or ad-hoc ignore globs unless a **future, explicit operator opt-in** is designed (separate plan/ADR).
2. **Optional future:** a clearly named config block (e.g. `file_scan.operator_exclude_globs`) may allow **operator-declared** skips for known noise paths — never silent inheritance of the client's VCS ignore rules.
3. **Document** in USAGE/SECURITY when operator docs next touch filesystem targets: scanning may traverse paths ignored by Git.

## Consequences

- **Positive:** Avoids false confidence ("green scan" because PII sat in gitignored folders).
- **Negative:** More files scanned; operators must scope `targets.path` and extensions deliberately.
- **Related fix (same issue, separate concern):** symlink loop guard and inode de-duplication — see `iter_scan_files` in `connectors/filesystem_connector.py` (#1080 🔴).

## References

- GitHub **#1080** (audit)
- [ADR 0051](ADR-0051-incremental-filesystem-scan-file-identity-fingerprint.md) — file identity metadata
