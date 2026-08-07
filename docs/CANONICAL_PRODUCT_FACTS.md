# Canonical product facts (anti-invention)

**Português (Brasil):** [CANONICAL_PRODUCT_FACTS.pt_BR.md](CANONICAL_PRODUCT_FACTS.pt_BR.md)

Terse source of truth for humans and coding agents. Prefer **links** over restating long guides. Not marketing copy.

**Related:** [QUICKSTART.md](../QUICKSTART.md) · [USAGE.md](USAGE.md) · site [windows.html](https://databoar.com.br/windows.html) · issue [#1470](https://github.com/DataBoar/data-boar/issues/1470) · guard `tests/test_canonical_product_facts.py`

---

## 1. Official identity

| Item | Canonical value |
| ---- | --------------- |
| Product name | Data Boar |
| CLI / executable | `data-boar` |
| PyPI package | `data-boar` |
| **GitHub repository** | [https://github.com/DataBoar/data-boar](https://github.com/DataBoar/data-boar) |
| Institutional site | [https://databoar.com.br](https://databoar.com.br) (also [data-boar.com](https://data-boar.com)) |
| Non-tech Windows page | [https://databoar.com.br/windows.html](https://databoar.com.br/windows.html) |
| **Docker Hub image** (optional path only) | [`fabioleitao/data_boar`](https://hub.docker.com/r/fabioleitao/data_boar) — **image namespace ≠ GitHub org** |

**Not canonical as the GitHub repo:** the legacy personal-namespace path that still redirects (org + repo slug above is the current home). Do not cite the old personal path as current.

---

## 2. Happy-path — Windows / non-tech

1. Prefer the site guide: [windows.html](https://databoar.com.br/windows.html).
2. Native install (until a product MSI/winget package ships): `pipx install data-boar`.
3. Run the executable: `data-boar`.
4. Safe first contact (synthetic demo, no real data): `data-boar --demo`.
5. **Docker is optional** — advanced / TI path. **Not required** for the native Windows path. Do not present Docker as the only or default path for non-technical users.
6. Deepen in the repo after demo: [QUICKSTART.md](../QUICKSTART.md) → [USAGE.md](USAGE.md). Business narrative stays on the **site**; this repo stays **how to run**.

---

## 3. Product contract (doctrine)

- **Deterministic-first / zero-LLM-default** for the core detection path.
- **Local-first** — scan on the operator machine; no cloud mandate.
- **HITL** for merge, publish, and high-blast-radius decisions.
- **Evidence ≠ legal conclusion** — outputs are technical signals for triage, not certification or legal advice.
- **Overclaim-safe** — no universal coverage claims; no “we certify LGPD/compliance”.
- **Site = business**; **repo = technical**. Link; do not duplicate long marketing pages here.

---

## 4. Capability facts often hallucinated

| Invented or stale claim | Fact |
| ----------------------- | ---- |
| Config key `pastas_para_varrer` | **Does not exist** (fabricated). Real YAML key for scan targets: **`targets:`**. |
| CLI `databoarscan --path` | **Does not exist**. Use **`data-boar`**. |
| Docker required / only path for non-tech | **False**. Docker is **optional**. |
| Encrypted or password-protected archive members are silently skipped | **False**. Via [#828](https://github.com/DataBoar/data-boar/issues/828) they record **`scan_failures`** with reasons `encrypted_no_password` / `wrong_password` — **reported, not dropped**. Source: `core/archives.py` (`iter_archive_members`, `classify_zip_member_read_failure`). |
| Current GitHub home is the legacy personal-namespace clone path | **Stale**. Canonical: **`DataBoar/data-boar`**. |

---

## 5. For agents — do not invent

1. Read **this file** before asserting install, CLI, config keys, or identity URLs.
2. Prefer links to [windows.html](https://databoar.com.br/windows.html), [QUICKSTART.md](../QUICKSTART.md), and [USAGE.md](USAGE.md) over invented YAML or CLI names.
3. Never invent certifications, legal outcomes, or “universal” discovery coverage.
4. If unsure → say **unknown**; do not fill gaps with plausible fiction.
5. Keep **`fabioleitao/data_boar`** labeled as the **Docker Hub image**, never as the GitHub repository.

---

## 6. Light regression guard

Offline pytest: `tests/test_canonical_product_facts.py` (this slice anchors the guard **on these FACTS files**). Broader README/QUICKSTART policing is a **later** slice under [#1470](https://github.com/DataBoar/data-boar/issues/1470).
