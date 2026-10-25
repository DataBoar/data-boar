# `security_audit` — local PII seed bundle (template)

**Tracked copy-me.** Real seeds and classification notes must live under **`docs/private/security_audit/`**, which is **gitignored** and **not** created by `git clone` of the public product repo.

## Bootstrap (any machine)

From repo root:

```bash
mkdir -p docs/private/security_audit
cp docs/private.example/security_audit/PII_LOCAL_SEEDS.example.txt docs/private/security_audit/PII_LOCAL_SEEDS.txt
# Edit PII_LOCAL_SEEDS.txt: one literal string per line for git pickaxe / fixed-string grep.
```

```powershell
New-Item -ItemType Directory -Force -Path docs/private/security_audit | Out-Null
Copy-Item docs/private.example/security_audit/PII_LOCAL_SEEDS.example.txt docs/private/security_audit/PII_LOCAL_SEEDS.txt
# Edit PII_LOCAL_SEEDS.txt: one literal string per line.
```

Optional: maintain **`PII_CONTEXT_DECISIONS_LOG.pt_BR.md`** (or another private log) next to the seeds file for `ACEITAVEL` vs `VAZAMENTO` notes.

## Batch pickaxe (save time and tokens)

After you maintain **`PII_LOCAL_SEEDS.txt`**, run from repo root (PowerShell):

```powershell
.\scripts\run-pii-local-seeds-pickaxe.ps1
```

Flags: **`-Quiet`** (only print seeds with hits), **`-Limit N`** (smoke test first N seeds). Same file format: one literal per line; `#` comments and blank lines ignored.

**Constraint split (do not duplicate work):** regex guards and `pii_history_guard.py` cover **pattern classes** (LinkedIn shape, `/home/`, `C:\Users\`, etc.). The seeds file is for **literals** (names, emails, org tokens) that automation cannot infer. Use the public guide greps for IP/CPF-style patterns instead of bloating seeds.

## Why Linux looked “broken”

Commands such as `grep docs/private/security_audit/PII_LOCAL_SEEDS.txt` fail with **No such file or directory** until you **copy** the example (or receive the real file from the maintainer’s private channel). This is expected on a fresh clone.

## References

- Public cadence and gates: **[docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md](../../ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md)** ([pt-BR](../../ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md))
- Policy: **[docs/PRIVATE_OPERATOR_NOTES.md](../../PRIVATE_OPERATOR_NOTES.md)**
