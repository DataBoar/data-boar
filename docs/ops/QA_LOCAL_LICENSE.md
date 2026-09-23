# QA with `licensing.mode: enforced` — local signed license

> **Idioma:** [Português (Brasil)](QA_LOCAL_LICENSE.pt_BR.md)

The env-based bypass (`DATA_BOAR_ENV=development` / `DEBUG=1` /
`DATA_BOAR_TIER_OVERRIDE`) was **removed** (#719). The **only** way to test
enforced mode is a real signed license. QA licenses are deliberately:

- **Short-lived** — 60 days by default (a leaked token dies on its own).
- **Machine-bound** — the `dbmfp` claim pins the license to one machine
  fingerprint; it refuses to run anywhere else (`MACHINE_MISMATCH`).
- **Enterprise tier by default** — full QA surface.

## 1. One-time key setup (issuer machine — operator)

Keep the Ed25519 **private** key outside Git (e.g. `~/.keys/data-boar/`).
See `docs/private.example/licensing/README.md` for key generation.

Runtime `LicenseGuard` verifies EdDSA, and also ML-DSA-65 when the token carries `dbmldsa_sig` (`decode_license_jwt_hybrid`). That ML-DSA key is the packaged anchor or an accepted rotation. `DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_*` fails closed (`untrusted_key_override`). Tokens without the claim stay Ed25519-only — see [LICENSING_SPEC.md](../LICENSING_SPEC.md).

### Optional: encrypted signing key (passphrase)

The signing key may be stored as an AES-encrypted PKCS#8 PEM. The issuer
(`scripts/issue_dev_license_jwt.py`) resolves the passphrase in this order:

1. **Env var** `DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD` — the
   non-interactive path for automation. Maestro (`Handle-LicensingMatrix.ps1`)
   runs head-less, so export it **before** running the handler:

   ```bash
   export DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD='your-passphrase'
   ```

2. **Interactive prompt** — in a TTY with no env var set, the issuer asks
   `License signing key passphrase:` and reads it without echo.
3. **Unencrypted key** — no passphrase needed (backward-compatible).

An encrypted key with neither the env var nor a TTY exits with an actionable
message (never a raw traceback).

## 2. Issue a license for THIS machine

```bash
uv run python scripts/issue_dev_license_jwt.py \
  --private-key-pem-file ~/.keys/data-boar/license-signing-v1-pkcs8.pem \
  --out ~/.keys/data-boar/qa-enterprise.lic
```

Defaults: `--dbtier enterprise --days 60 --dbmfp auto` (bound to the machine
that runs the command).

## 3. Issue for a tester's machine (remote)

The tester prints their fingerprint and sends it to the operator:

```bash
uv run python scripts/issue_dev_license_jwt.py --show-machine-fingerprint
```

The operator issues with the explicit fingerprint:

```bash
uv run python scripts/issue_dev_license_jwt.py \
  --private-key-pem-file ~/.keys/data-boar/license-signing-v1-pkcs8.pem \
  --dbmfp <tester-fingerprint-hex> \
  --out qa-tester.lic
```

Send only the `.lic` file — never the private key.

## 4. Install and run enforced

The official verify key is **embedded** in the install (`license-pub-v1.pem`).
A valid machine-bound `.lic` is enough — no pubkey env/config on a clean
install (#1331). A raw `DATA_BOAR_LICENSE_PUBLIC_KEY_*`, `DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_*`,
`licensing.public_key_path`, or `licensing.mldsa_public_key_path` fails closed
(`untrusted_key_override`, #1992).
Key rotation is `licensing.rotation_attestation_path`: both embedded anchors
must sign `data-boar/license-key-rotation/v1` plus the epoch.

```yaml
# config.yaml
licensing:
  mode: enforced
  license_path: /path/to/qa-enterprise.lic
```

Or via environment:

```bash
export DATA_BOAR_LICENSE_PATH=/path/to/qa-enterprise.lic
```

Check `GET /health` / `GET /about`: state must be **VALID** with
`dbtier: enterprise`. Without a valid license, enforced mode **fails closed**
(scans denied with 403/Safe-Hold) — see `docs/LICENSING_SPEC.md`.

## Notes

- Containers/VM pools: set a stable `DATA_BOAR_MACHINE_SEED` **before**
  printing the fingerprint and keep the same seed at runtime, or the
  fingerprint will not match.
- Maestro (`Handle-LicensingMatrix.ps1`) issues its three tier `.lic` files
  with the same 60-day, machine-bound defaults.
- Every enforcement decision lands on the `data_boar.licensing.audit` logger
  (`LICENSE_AUDIT` prefix).
