# Smoke: WebAuthn JSON RP (operator / CI subset)

**Portuguese (Brazil):** [SMOKE_WEBAUTHN_JSON.pt_BR.md](SMOKE_WEBAUTHN_JSON.pt_BR.md)

**Plan:** [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](../plans/PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) Phase **1a**; **ADR:** [0033](../adr/ADR-0033-webauthn-open-relying-party-json-endpoints.md).

**Scope:** Automated **pytest** coverage for optional **`/auth/webauthn/*`** JSON endpoints (no browser / no authenticator required). Full **FIDO2** ceremonies with a real passkey remain a **manual** integration check outside this subset.

---

## Autonomous smoke (any machine with the repo)

From the repo root (Windows):

```powershell
.\scripts\smoke-webauthn-json.ps1
```

Full gate before merge remains **`.\scripts\check-all.ps1`** (not replaced by this script).

### What this proves

| Area | Covered by |
| ---- | ---------- |
| Disabled config returns **404** on `/auth/webauthn/*` | `test_webauthn_disabled_returns_404` |
| Enabled + secret: **registration/options** returns `options` + `state` | `test_webauthn_registration_options_returns_options_and_state` |
| **GET /status** shape | `test_webauthn_status_shows_registered_zero` |
| **authentication/options** without credentials → **404** | `test_webauthn_authentication_options_404_when_no_credentials` |
| Second **registration** when a credential exists → **403** | `test_webauthn_registration_options_403_when_credential_exists` |
| **verify** with bad `state` → **400** | `test_webauthn_registration_verify_rejects_bad_state` |
| **logout** | `test_webauthn_logout_returns_ok` |
| Enabled without **`DATA_BOAR_WEBAUTHN_TOKEN_SECRET`** → startup **RuntimeError** | `test_startup_fails_when_enabled_without_secret` |
| Cookie sign/verify helpers | `tests/test_webauthn_session_cookie.py` |

---

## Manual integration (optional)

1. Set **`api.webauthn.enabled: true`**, **`api.webauthn.origin`** / **`rp_id`** to match your HTTPS origin, and **`DATA_BOAR_WEBAUTHN_TOKEN_SECRET`** before **`main.py --web`**.
1. Use a **small front-end** or devtools to run WebAuthn against the JSON endpoints; align with [USAGE.md](../USAGE.md) and [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md).
1. **HTML dashboard** is **not** gated by this cookie until **[#86](https://github.com/FabioLeitao/data-boar/issues/86)** Phase **1b+**.
