# Licensing — private operator layout (example)

This folder documents **where real issuer material lives** without committing it to GitHub.

## JWT signing (lab / homelab)

- **Public** repo: `scripts/issue_dev_license_jwt.py` reads an **Ed25519 private key** from environment variables or `--private-key-pem-file`.
- **Store keys only** under `docs/private/` (gitignored from `origin`) or another secure path outside the clone.
- **Never** paste PEMs into tracked files, issues, or PRs.

### Environment variables (example)

- `DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM_FILE` — path to private PEM
- `DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM` — inline PEM (CI or one-off only; prefer file)

Verification and runtime consumption of `.lic` files follow `docs/LICENSING_SPEC.md` (`licensing.mode: enforced`, embedded verify key; raw pubkey env overrides are rejected).
