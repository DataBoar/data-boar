# Plugin author guide — YAML pattern plugins

**Português (Brasil):** [PLUGIN_AUTHOR_GUIDE.pt_BR.md](PLUGIN_AUTHOR_GUIDE.pt_BR.md)

How to teach Data Boar **new detection shapes** without changing core code. This is the missing front door for third-party / operator pattern authors (GitHub **#836**).

The **schema on disk** is the contract: [`config/plugin_schema.yaml`](../config/plugin_schema.yaml). The validator is [`config/plugin_validator.py`](../config/plugin_validator.py) ([ADR-0052](adr/ADR-0052-yaml-plugin-system-centralized-schema.md)).

---

## Two plugin surfaces (do not mix them)

| Surface | What it is | Runs code? | Guide |
| ------- | ---------- | ---------- | ----- |
| **YAML pattern plugins** (this page) | Extra regex / ML / DL **terms** loaded from YAML | **No** | You are here |
| **Enterprise remediation L1** | Python `RemediationPlugin` after the report | **Yes** (in-process) | [PLUGIN_SDK.md](PLUGIN_SDK.md) ([pt-BR](PLUGIN_SDK.pt_BR.md)) |
| **Language-neutral envelope (L2/L3)** | Sidecar / FFI contract — not a loadable YAML pattern API today | n/a | [SDK.md](SDK.md) |

YAML pattern plugins **do not** open sockets, read extra files, or call connectors. They only add **what the detector looks for**.

---

## What you can and cannot touch

**Can:**

- Add or override **regex** rules (`name` + `pattern`, optional `norm_tag`).
- Add **ML** / **DL** keyword terms (`text` + optional `label`).
- Optionally attach **author metadata** (`dga_classification`, `iso27001_controls`, `dmbok_area`) on regex items. Those fields are **hints for GRC authors**, not a legal opinion, and they are **not** copied onto finding rows (findings still expose `pattern_detected` / `norm_tag`).

**Cannot:**

- Execute Python, shell, or Rust of your own.
- Change scan **targets**, **RBAC**, API routes, or report templates.
- Implement **remediation** (tokenize / mask / notify) — that is [PLUGIN_SDK.md](PLUGIN_SDK.md).
- Bypass the **ReDoS** guard (#829): nested unbounded quantifiers such as `(a+)+` or `(\w*)*` are rejected.

---

## Tier (honest)

YAML pattern files load as **operator config** today (Community / `Tier.OPEN` lab). There is **no** runtime `require_feature("custom_detectors")` call on `regex_overrides_file` / `patterns_plugin_file`.

`FEATURE_TIER_MAP["custom_detectors"]` is **Enterprise** as a **reserved** product key — it is **not** the gate on these YAML files yet. Do not tell authors they need an Enterprise license only to ship a pattern file.

Remediation plugins **do** require the **Enterprise** feature `remediation_plugin` (or lab `OPEN`). See [PLUGIN_SDK.md](PLUGIN_SDK.md).

---

## Config keys

Prefer **one** unified file:

```yaml
# config.yaml
patterns_plugin_file: /data/my_patterns.yaml
```

Legacy keys still work (same schemas, three files): `regex_overrides_file`, `ml_patterns_file`, `dl_patterns_file`. When both the unified file and a legacy key supply the **same section**, **`patterns_plugin_file` wins** for that section ([ADR-0052](adr/ADR-0052-yaml-plugin-system-centralized-schema.md)).

Field-by-field detection behaviour: [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) ([pt-BR](SENSITIVITY_DETECTION.pt_BR.md)). CLI/config overview: [USAGE.md](USAGE.md) ([pt-BR](USAGE.pt_BR.md)).

---

## Minimal unified example

```yaml
regex_patterns:
  - name: "RG_BR"
    pattern: "\\b\\d{1,2}\\.?\\d{3}\\.?\\d{3}-?[0-9Xx]\\b"
    norm_tag: "LGPD Art. 5"

ml_patterns:
  - text: "cpf"
    label: "sensitive"

dl_patterns:
  - text: "dado pessoal"
    label: "sensitive"
```

Copy a larger regex list from [`config/regex_overrides.example.yaml`](../config/regex_overrides.example.yaml). Use **double-quoted** YAML and escaped backslashes (`\\b`, `\\d`).

Legacy regex-only files are a **YAML list** (no `regex_patterns:` wrapper) — same item fields.

---

## Optional GRC author metadata (regex items only)

These keys live on **regex** items (`config/plugin_schema.yaml`). They are **author metadata**. `config/plugin_validator.py` checks types and allowed values; the detector **does not** copy them onto finding rows. Reports still expose `pattern_detected` (the rule `name`) and `norm_tag` only. They are **not** a DGA legal opinion, an ISO 27001 certification, or a DMBOK assessment.

| Key | Type | Allowed values / shape |
| --- | ---- | ---------------------- |
| `dga_classification` | string | `shareable`, `restricted_sharing`, `no_sharing` |
| `iso27001_controls` | list of strings | ISO/IEC **27001:2022** Annex A IDs (e.g. `A.5.12`, `A.5.33`, `A.8.3`, `A.8.11`). **2013** `A.8.2.1` maps to **2022** `A.5.12`, not to 2022 `A.8.2`. |
| `dmbok_area` | string | `armazenamento_e_operacao`, `integracao_e_interoperabilidade`, `seguranca_dados` |

ML / DL items **do not** declare these keys in the schema. Extra keys on those items are **ignored** (additive validator). They still do **not** appear on findings.

```yaml
regex_patterns:
  - name: "HEALTH_PLAN_ID"
    pattern: "\\bHP-\\d{8}\\b"
    norm_tag: "LGPD Art. 5 II"
    dga_classification: no_sharing
    iso27001_controls:
      - A.5.33
      - A.8.11
    dmbok_area: seguranca_dados
```

Typical author hints in the schema: health / special-category → `A.5.33` + `A.8.11`; access / credential-like → `A.8.3`; stored PI classification → `A.5.12`. Storage / files → `armazenamento_e_operacao`; APIs / streams → `integracao_e_interoperabilidade`; unclassified PI → `seguranca_dados`.

---

## Safe regex contract (ReDoS)

The validator walks the pattern and **rejects nested unbounded repetition** (star-height > 1), the same class as common `safe-regex` linters: `(a+)+`, `([a-z]+)*`, `(x{2,})+`.

Still valid:

- Bounded `?` (0-or-1), e.g. `(\\+55\\s?)?` for an optional country prefix.
- Escaped metacharacters (`\\+`, `\\(`).
- Quantifiers inside character classes (`[+*]`).

Invalid items emit `PluginValidationWarning` and are **skipped**; the scan **continues** (not a silent discard of the whole file).

---

## Validate before a scan

There is **no** shipped `validate-plugin` CLI yet (queued as a later phase). From the repo:

```bash
uv run python -c "from config.plugin_validator import validate_plugin_file; r = validate_plugin_file('my_patterns.yaml', 'unified_plugin_file'); print(r.valid); print('\\n'.join(r.issues))"
```

Use `plugin_type="regex_patterns"` for a legacy list file. `--validate-config` also surfaces validator warnings when the unified path is set.

---

## Related

- Schema: [`config/plugin_schema.yaml`](../config/plugin_schema.yaml)
- Detection how-to: [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md)
- Remediation partners: [PLUGIN_SDK.md](PLUGIN_SDK.md)
- Contract hub (L2/L3): [SDK.md](SDK.md)
- Docs index: [README.md](README.md)

**Documentation index:** [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
