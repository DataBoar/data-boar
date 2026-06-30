# OPA tier drift — isolated Rego prototype (#1079)

**Not wired to CI or runtime.** Demonstrates that connector/feature tier rules
from ADR-0027 / `FEATURE_TIER_MAP` can be expressed in Rego for a future
**drift linter** (ADR-0076).

## Layout

| File | Purpose |
| --- | --- |
| `tier_policy.rego` | Sample `min_tier` decisions for connector features |
| `tier_policy_test.rego` | `opa test` style cases (run manually with OPA CLI if installed) |
| `manifest_snapshot.example.json` | Illustrative export shape from Python registry |

## Manual check (optional, operator machine)

```bash
# Requires OPA CLI locally — NOT a repo dependency
opa test research/licensing/opa_tier_drift_prototype/
```

## Out of scope

- Modifying `core/licensing/*` runtime
- Adding OPA to `pyproject.toml` or Docker image
- Enforcing JWT / Ed25519 / `LicenseGuard` behaviour

See [ADR-0076](../../../docs/adr/ADR-0076-opa-rego-ci-tier-drift-linter-not-runtime.md).
