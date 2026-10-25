"""
Vendor-neutral WebAuthn Relying Party helpers (Phase 1 dashboard session).

Uses the open-source ``webauthn`` library (Duo Labs) for ceremonies; optional Bitwarden
Passwordless.dev or Microsoft-hosted flows are **not** required — any FIDO2/WebAuthn
authenticator can be used when ``api.webauthn.enabled`` is true.
"""
