# Plugin SDK — Enterprise remediation plugins (L1)

**Português (Brasil):** [PLUGIN_SDK.pt_BR.md](PLUGIN_SDK.pt_BR.md)

Guide for partners who implement **post-scan remediation** plugins against the host hook shipped in GitHub **#606** ([ADR-0059](adr/ADR-0059-remediation-plugin-architecture.md)).

**Scope of this document:** **L1 in-process Python** only (`RemediationPlugin`). Process isolation (L2) and language / sidecar contracts (L3) belong to epic **#865** — call them out as future evolution, not as APIs you can load today.

**Not this guide:** declarative **YAML pattern plugins** (custom regex / ML / DL terms) use `config/plugin_schema.yaml` and [ADR-0052](adr/ADR-0052-yaml-plugin-system-centralized-schema.md). Those teach the detector new shapes; they do **not** run remediation code.

---

## Overview

After a successful report generation path, the host may optionally load a third-party class that:

1. Reads a **findings JSONL** file (path provided by the host).
1. Performs partner-owned remediation (tokenize, mask, encrypt, notify, …).
1. Writes a **`remediation_report.json`** (or equivalent) and returns its `Path`.

The host never imports your business logic into core. You ship a Python module; the operator points YAML at `module.path:ClassName`.

| Piece | Location |
| ----- | -------- |
| Protocol + `PluginError` | `core/plugins/base.py` |
| Loader | `core/plugins/loader.py` → `load_remediation_plugin` |
| Fail-graceful host hook | `core/plugins/hook.py` → `maybe_run_remediation_hook` |
| Public exports | `core/plugins/__init__.py` |
| Tier gate | `remediation_plugin` → `Tier.ENTERPRISE` in `core/licensing/tier_features.py` |
| Example config | `deploy/config.example.yaml` (`remediation:` block) |

---

## Protocol (minimum interface)

`RemediationPlugin` is a `@runtime_checkable` `typing.Protocol`. Your class must provide:

| Member | Signature / type | Contract |
| ------ | ---------------- | -------- |
| `remediate` | `(self, findings_path: Path, config: dict) -> Path` | Read findings JSONL at `findings_path`. **Do not modify that file in place.** Return the path of the remediation report you wrote (conventionally `remediation_report.json`). |
| `name` | `@property` → `str` | Stable plugin id for Audit Trail. |
| `version` | `@property` → `str` | Plugin version string. |

`PluginError` is raised by the **loader** when the path format is wrong, the module cannot be imported, the class is missing, instantiation fails, or the instance is non-conformant. The host catches `PluginError` (and other exceptions from `remediate`) and **Safe-Holds** — the scan does **not** abort.

---

## What you receive and what you return

### `findings_path: Path`

- Intended shape: newline-delimited JSON (**JSONL**), one finding object per line (location metadata such as path / table / column / finding id — exact keys depend on the export the host wires).
- **Read-only:** copy or stream; never rewrite the findings file in place.
- **Honesty — automatic wiring (follow-up #1443):** the post-scan hook currently builds
  `{report.output_dir}/findings_{session_id}.jsonl`
  by convention. **That path is not yet written by the normal scan pipeline.** With `remediation.enabled: true`, a plugin may receive a path to a **missing** file until #1443 lands. Fail-graceful still protects the scan. For development **today**, call `remediate()` yourself with a findings file **you** provide (see [Test locally](#test-locally)).

### `config: dict`

- Passed through from YAML `remediation.config` **as-is** (may be `{}`).
- Use for partner keys (API endpoints, key aliases, dry-run flags). Do not expect Data Boar secrets unless the operator put them in that dict / env your plugin reads.

### Return value: `Path`

- Absolute or relative path to the remediation report artifact you created.
- Typical name: `remediation_report.json` next to the findings file (your choice — return whatever path you wrote).

---

## Minimal working example (Python)

```python
# myorg/stealthizer.py
from __future__ import annotations

import json
from pathlib import Path

class StealthizerPlugin:
    """Minimal RemediationPlugin-conformant class (L1)."""

    @property
    def name(self) -> str:
        return "myorg-stealthizer"

    @property
    def version(self) -> str:
        return "0.1.0"

    def remediate(self, findings_path: Path, config: dict) -> Path:
        # Read-only: stream findings; do not rewrite findings_path.
        findings: list[dict] = []
        if findings_path.is_file():
            with findings_path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        findings.append(json.loads(line))

        report = {
            "plugin": self.name,
            "version": self.version,
            "findings_seen": len(findings),
            "actions": [],  # partner fills: tokenized, masked, notified, ...
            "config_keys": sorted(config.keys()),
        }
        out = findings_path.parent / "remediation_report.json"
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return out
```

Install the package on the same Python environment as Data Boar (or put the module on `PYTHONPATH`).

---

## Register in config

From `deploy/config.example.yaml`:

```yaml
# Enterprise tier — post-scan remediation plugin (optional)
# Requires licensing.effective_tier: enterprise (or OPEN for dev/lab).
# plugin format: "module.path:ClassName"
remediation:
  enabled: false
  plugin: null           # e.g. "myorg.stealthizer:StealthizerPlugin"
  verify_after: true     # stub log until full re-scan (#653)
  config: {}             # passed as-is to plugin.remediate()
```

Operator checklist:

1. Set `remediation.enabled: true`.
1. Set `remediation.plugin: "myorg.stealthizer:StealthizerPlugin"`.
1. Set `licensing.effective_tier: enterprise` for lab simulation, **or** leave OPEN (no `effective_tier`) so all feature gates pass in open-core lab mode.
1. Put partner options under `remediation.config`.

Loader format is strictly `module.path:ClassName` (`rsplit(":", 1)`). Missing `:` → `PluginError`.

---

## Tier gate

| Runtime tier | `remediation_plugin` |
| ------------ | -------------------- |
| **OPEN** (lab / no commercial tier) | Available (bypass) |
| **ENTERPRISE** | Available |
| **COMMUNITY** / **PRO** | Skipped — stderr warning; no exception; scan continues |

Feature key: `"remediation_plugin"` in `FEATURE_TIER_MAP` (`Tier.ENTERPRISE`). Runtime tier comes from `get_runtime_tier_for_features(config)`.

---

## Fail-graceful host behaviour

`maybe_run_remediation_hook(config, session_id)`:

- No-op when `remediation.enabled` is false / missing.
- Community/Pro → log skip to stderr; return.
- Load / `remediate` failures → `[remediation] plugin error: …` on stderr; **never** raises into the scan worker.
- When `verify_after` is true and remediate succeeded, logs
  `[remediation] post-remediation verification pending (see #653)`
  (stub only).

---

## Test locally

### 1) Direct call (works today — recommended)

```bash
# From a venv with data-boar + your plugin importable:
uv run python - <<'PY'
from pathlib import Path
from myorg.stealthizer import StealthizerPlugin

findings = Path("/tmp/findings_demo.jsonl")
findings.write_text(
    '{"finding_id":"f1","path":"/data/a.csv","pii_type":"EMAIL"}\n',
    encoding="utf-8",
)
report = StealthizerPlugin().remediate(findings, {"dry_run": True})
print(report, report.read_text(encoding="utf-8"))
PY
```

### 2) Loader conformance

```python
from core.plugins import load_remediation_plugin, PluginError

plugin = load_remediation_plugin("myorg.stealthizer:StealthizerPlugin")
assert plugin.name and plugin.version
```

Repo tests: `tests/test_plugin_loader.py` (valid load, bad format, non-conformant → `PluginError`, tier skip).

### 3) Host hook with YAML (opt-in)

You can enable `remediation:` and run a normal scan / regenerate-report path. **Until #1443**, treat automatic invocation as **wiring in progress**: the hook may pass a findings path that does not exist yet. Prefer direct `remediate()` for functional partner demos.

---

## Security (L1 trust boundary)

- The plugin runs **in the same Python process** as Data Boar (L1). Treat it as **fully trusted code** for that host: it can read memory, filesystem, and network as the process user allows.
- **Do not** load untrusted third-party wheels into production Enterprise hosts without supply-chain review (pin, hash, private index).
- Recommended evolution (**#865**): L2 sandbox / L3 sidecar so partner code is isolated. This SDK does **not** provide that isolation today.
- Findings and remediation reports are confidential even when they are “only metadata” — keep them inside the customer tenancy.

---

## Example use cases (partner IP)

| Use case | What `remediate` typically does |
| -------- | -------------------------------- |
| **FPE tokenization** | Map finding coordinates → format-preserving tokens via partner HSM/vault; write action log to report |
| **Masking** | Overwrite or stage masked copies at mapped paths; never rewrite the findings JSONL |
| **Field encryption** | Encrypt column/file payloads; record ciphertext refs in the report |
| **Notification** | Open tickets / webhooks from finding locations; remediation report = delivery receipts |

Discovery and reporting stay in Data Boar; **how** you remediate stays partner IP. Product storyboard: [USE_CASE_SCAN_AND_REMEDIATE.md](use-cases/USE_CASE_SCAN_AND_REMEDIATE.md).

---

## Related docs

- [USAGE.md](USAGE.md) ([pt-BR](USAGE.pt_BR.md)) — operator CLI/config; Enterprise remediation section
- [TECH_GUIDE.md](TECH_GUIDE.md) ([pt-BR](TECH_GUIDE.pt_BR.md)) — install, config, extensibility
- [ADR-0059](adr/ADR-0059-remediation-plugin-architecture.md) — protocol-based L1, fail-graceful, Enterprise-gated
- [ADR-0052](adr/ADR-0052-yaml-plugin-system-centralized-schema.md) — YAML **pattern** plugins (different surface)
- [use-cases/USE_CASE_SCAN_AND_REMEDIATE.md](use-cases/USE_CASE_SCAN_AND_REMEDIATE.md) ([pt-BR](use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md))
- [use-cases/USE_CASE_TOKENIZED_FINDINGS.md](use-cases/USE_CASE_TOKENIZED_FINDINGS.md) ([pt-BR](use-cases/USE_CASE_TOKENIZED_FINDINGS.pt_BR.md))
- GitHub **#606** (hook), **#611** (this guide), **#1443** (findings path wiring), **#653** (verify_after), epic **#865** (L2/L3)
