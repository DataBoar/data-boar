# License Studio (operator issuer — private repo)

The Go **license issuance** tool moved out of this public tree on **2026-06-25**.

| What | Where |
| ---- | ----- |
| **Operator issuer (Go)** | Private repo **`FabioLeitao/license-studio`** — clone with `gh repo clone FabioLeitao/license-studio` |
| **Client enforcement** | Stays here: `core/licensing/`, `license-pub-v1.pem`, ADR-0063/0064 |
| **Dev JWT helper (Python)** | Stays here: `scripts/issue_dev_license_jwt.py` + `docs/ops/QA_LOCAL_LICENSE.md` |

Never commit signing keys, audit DBs, or issuance blobs to **`origin`**.

See also: [LICENSING_SPEC.md](../LICENSING_SPEC.md), [CODE_PROTECTION_OPERATOR_PLAYBOOK.md](CODE_PROTECTION_OPERATOR_PLAYBOOK.md), [CURSOR_ECOSYSTEM_ONBOARDING.md](CURSOR_ECOSYSTEM_ONBOARDING.md).
