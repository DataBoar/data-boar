"""
Optional commercial licensing (open by default).

See docs/LICENSING_SPEC.md and docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.md.
"""

from core.licensing.errors import LicenseBlockedError
from core.licensing.guard import (
    LicenseContext,
    LicenseGuard,
    get_license_guard,
    reset_license_guard_for_tests,
)

__all__ = [
    "LicenseBlockedError",
    "LicenseContext",
    "LicenseGuard",
    "get_license_guard",
    "reset_license_guard_for_tests",
]
