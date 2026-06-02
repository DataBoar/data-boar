"""
Runtime license guard: open mode (default) vs enforced commercial token verification.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jwt

from core.licensing.feature_gate import FeatureCheckResult, check_feature
from core.licensing.fingerprint import compute_machine_fingerprint
from core.licensing.runtime_feature_tier import map_dbtier_string_to_tier
from core.licensing.tier_features import Tier
from core.licensing.integrity import (
    check_build_digest_expected,
    verify_manifest_optional,
)
from core.licensing.verify import (
    decode_license_jwt,
    load_ed25519_public_key_pem,
    load_public_key_from_path,
    load_revocation_ids,
    utc_now_ts,
)


@dataclass
class LicenseContext:
    """Snapshot for logs, API, and report info."""

    state: str
    mode: str
    customer_id: str = ""
    customer_name: str = ""
    environment: str = ""
    license_id: str = ""
    expires_at_iso: str = ""
    grace_until_iso: str = ""
    issuer_id: str = ""
    key_id: str = ""
    trial: bool = False
    max_report_rows: int = 0
    machine_fingerprint: str = ""
    detail: str = ""
    watermark: str = ""
    # Product tier hint from JWT (`dbtier` claim) when mode is enforced — see LICENSING_SPEC.md
    dbtier: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "license_state": self.state,
            "license_mode": self.mode,
            "customer_id": self.customer_id or None,
            "customer_name": self.customer_name or None,
            "environment": self.environment or None,
            "license_id": self.license_id or None,
            "expires_at": self.expires_at_iso or None,
            "grace_until": self.grace_until_iso or None,
            "issuer_id": self.issuer_id or None,
            "trial": self.trial,
            "watermark": self.watermark or None,
            "dbtier": self.dbtier or None,
        }


_guard_instance: LicenseGuard | None = None


def get_license_guard(config: dict[str, Any] | None = None) -> LicenseGuard:
    """Singleton guard for process lifetime (config merged once per first call)."""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = LicenseGuard(config or {})
    return _guard_instance


def reset_license_guard_for_tests() -> None:
    """Clear singleton (tests only)."""
    global _guard_instance
    _guard_instance = None


class LicenseGuard:
    """
    Evaluates licensing mode and optional JWT. Default: open (no blocking).
    """

    def __init__(self, config: dict[str, Any]) -> None:
        lc = (config.get("licensing") or {}) if isinstance(config, dict) else {}
        env_mode = (os.environ.get("DATA_BOAR_LICENSE_MODE") or "").strip().lower()
        if env_mode in ("open", "enforced"):
            mode = env_mode
        else:
            mode = str(lc.get("mode", "open")).strip().lower()
        if mode not in ("open", "enforced"):
            mode = "open"
        self.mode = mode
        self._config = config
        self._lc = lc
        self._context: LicenseContext | None = None
        self._evaluate()

    def _evaluate(self) -> None:
        mfp = compute_machine_fingerprint()
        if self.mode == "open":
            self._context = LicenseContext(
                state="OPEN",
                mode="open",
                machine_fingerprint=mfp,
                detail="enforcement_disabled",
                watermark="",
            )
            return

        ok_digest, digest_msg = check_build_digest_expected()
        if not ok_digest:
            self._context = LicenseContext(
                state="TAMPERED",
                mode="enforced",
                machine_fingerprint=mfp,
                detail=digest_msg,
                watermark="UNAUTHORIZED_BUILD",
            )
            return

        manifest_path = (
            os.environ.get("DATA_BOAR_RELEASE_MANIFEST_PATH")
            or self._lc.get("manifest_path")
            or ""
        ).strip()
        ok_man, man_msg = verify_manifest_optional(manifest_path or None)
        if not ok_man:
            self._context = LicenseContext(
                state="TAMPERED",
                mode="enforced",
                machine_fingerprint=mfp,
                detail=man_msg,
                watermark="UNAUTHORIZED_BUILD",
            )
            return

        pem_env = (os.environ.get("DATA_BOAR_LICENSE_PUBLIC_KEY_PEM") or "").strip()
        key_path = (
            os.environ.get("DATA_BOAR_LICENSE_PUBLIC_KEY_PATH")
            or self._lc.get("public_key_path")
            or ""
        ).strip()
        lic_path = (
            os.environ.get("DATA_BOAR_LICENSE_PATH")
            or self._lc.get("license_path")
            or ""
        ).strip()
        rev_path = (
            os.environ.get("DATA_BOAR_LICENSE_REVOCATION_PATH")
            or self._lc.get("revocation_list_path")
            or ""
        ).strip()

        if not pem_env and not key_path:
            self._context = LicenseContext(
                state="UNLICENSED",
                mode="enforced",
                machine_fingerprint=mfp,
                detail="missing_public_key",
                watermark="NO_VERIFY_KEY",
            )
            return

        try:
            if pem_env:
                pub = load_ed25519_public_key_pem(pem_env)
            else:
                pub = load_public_key_from_path(key_path)
        except Exception as e:
            self._context = LicenseContext(
                state="INVALID",
                mode="enforced",
                machine_fingerprint=mfp,
                detail=f"public_key_load_error:{e}",
                watermark="INVALID_KEY_MATERIAL",
            )
            return

        if not lic_path or not Path(lic_path).is_file():
            self._context = LicenseContext(
                state="UNLICENSED",
                mode="enforced",
                machine_fingerprint=mfp,
                detail="missing_license_file",
                watermark="NO_LICENSE",
            )
            return

        try:
            raw = Path(lic_path).read_text(encoding="utf-8").strip()
            claims = decode_license_jwt(raw, pub)
        except jwt.PyJWTError as e:
            self._context = LicenseContext(
                state="INVALID",
                mode="enforced",
                machine_fingerprint=mfp,
                detail=f"jwt_error:{e}",
                watermark="INVALID_TOKEN",
            )
            return
        except Exception as e:
            self._context = LicenseContext(
                state="INVALID",
                mode="enforced",
                machine_fingerprint=mfp,
                detail=f"read_error:{e}",
                watermark="INVALID_TOKEN",
            )
            return

        revoked = load_revocation_ids(rev_path or None)
        lic_id = str(claims.get("sub", ""))
        if lic_id and lic_id in revoked:
            self._context = LicenseContext(
                state="REVOKED",
                mode="enforced",
                license_id=lic_id,
                machine_fingerprint=mfp,
                detail="license_revoked",
                watermark="REVOKED",
            )
            return

        now = utc_now_ts()
        exp = float(claims.get("exp", 0))
        grace_until = claims.get("dbgrace")
        try:
            grace_ts = float(grace_until) if grace_until is not None else 0.0
        except (TypeError, ValueError):
            grace_ts = 0.0

        exp_iso = _ts_iso(exp)
        grace_iso = _ts_iso(grace_ts) if grace_ts else ""

        token_mfp = str(claims.get("dbmfp", "") or "").strip().lower()
        # Non-empty dbmfp binds the license to one fingerprint (deployment/host).
        if token_mfp and mfp.lower() != token_mfp:
            self._context = LicenseContext(
                state="MACHINE_MISMATCH",
                mode="enforced",
                license_id=lic_id,
                customer_id=str(claims.get("dbcid", "") or ""),
                customer_name=str(claims.get("dbcname", "") or ""),
                environment=str(claims.get("dbenv", "") or ""),
                expires_at_iso=exp_iso,
                grace_until_iso=grace_iso,
                issuer_id=str(claims.get("dbissuer", "") or ""),
                key_id=str(claims.get("dbkid", "") or ""),
                trial=bool(claims.get("dbtrial", False)),
                max_report_rows=int(claims.get("dbmaxrows", 0) or 0),
                machine_fingerprint=mfp,
                detail="machine_fingerprint_mismatch",
                watermark="WRONG_HOST",
            )
            return

        bind_strict = bool(self._lc.get("machine_bind_strict")) or (
            os.environ.get("DATA_BOAR_LICENSE_MACHINE_STRICT", "").strip().lower()
            in ("1", "true", "yes")
        )
        if bind_strict and not token_mfp:
            self._context = LicenseContext(
                state="UNLICENSED",
                mode="enforced",
                machine_fingerprint=mfp,
                detail="machine_binding_required_but_missing_in_token",
                watermark="BINDING_REQUIRED",
            )
            return

        trial = bool(claims.get("dbtrial", False))
        max_rows = int(claims.get("dbmaxrows", 0) or 0)

        if now <= exp:
            state = "VALID"
        elif grace_ts and now <= grace_ts:
            state = "GRACE"
        else:
            state = "EXPIRED"

        wm = ""
        if trial:
            wm = "TRIAL_WATERMARK"
        if state == "EXPIRED":
            wm = "EXPIRED"

        self._context = LicenseContext(
            state=state,
            mode="enforced",
            license_id=lic_id,
            customer_id=str(claims.get("dbcid", "") or ""),
            customer_name=str(claims.get("dbcname", "") or ""),
            environment=str(claims.get("dbenv", "") or ""),
            expires_at_iso=exp_iso,
            grace_until_iso=grace_iso,
            issuer_id=str(claims.get("dbissuer", "") or ""),
            key_id=str(claims.get("dbkid", "") or ""),
            trial=trial,
            max_report_rows=max_rows,
            machine_fingerprint=mfp,
            detail="ok" if state in ("VALID", "GRACE") else state.lower(),
            watermark=wm,
            dbtier=str(claims.get("dbtier") or "").strip(),
        )

    @property
    def context(self) -> LicenseContext:
        assert self._context is not None
        return self._context

    def allows_scan(self) -> bool:
        c = self.context
        return c.state in ("OPEN", "VALID", "GRACE")

    def allows_full_report(self) -> bool:
        c = self.context
        if c.state == "OPEN":
            return True
        if c.state not in ("VALID", "GRACE"):
            return False
        if c.trial and c.max_report_rows > 0:
            return True  # report generated with cap (trial)
        if c.trial:
            return True
        return True

    def trial_cap_rows(self) -> int | None:
        """If trial with positive cap, return max rows; else None (no cap)."""
        c = self.context
        if c.state in ("OPEN", "VALID", "GRACE") and c.trial and c.max_report_rows > 0:
            return c.max_report_rows
        return None

    def product_tier_for_features(self) -> Tier:
        """Resolve product tier for feature gates (YAML, JWT, dev override)."""
        from core.licensing.runtime_feature_tier import get_runtime_tier_for_features

        return get_runtime_tier_for_features(self._config)

    def check_feature(self, feature: str) -> FeatureCheckResult:
        """Structured tier gate — does not raise on denial."""
        return check_feature(feature, self.product_tier_for_features())

    def is_allowed(self, feature: str) -> bool:
        return self.check_feature(feature).allowed

    @staticmethod
    def tier_from_dbtier_string(raw: str) -> Tier:
        """Map a tier label (fixtures / tests) to :class:`Tier`."""
        return map_dbtier_string_to_tier(raw)


def _ts_iso(ts: float) -> str:
    if ts <= 0:
        return ""
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.isoformat()
    except (OSError, ValueError, OverflowError):
        return ""
