"""Microsoft identity (Azure AD) token endpoint host allowlist (#2007).

HubSpot uses a fixed vendor API host before attaching secrets (#1607). Power BI and
Dataverse POST client secrets to ``auth.token_url``; IP pinning alone does not block
a public attacker host. Only ``login.microsoftonline.com`` is allowlisted today.
"""

from __future__ import annotations

from urllib.parse import urlparse

_MICROSOFT_TOKEN_HOST_TAG = "#2007"
_ALLOWLISTED_LOGIN_HOST = "login.microsoftonline.com"


def assert_allowlisted_microsoft_token_url(url: str) -> None:
    """Refuse client-credential token exchange to non-Microsoft login hosts."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme.lower() != "https":
        raise ValueError(
            "auth.token_url must use https:// and host "
            f"{_ALLOWLISTED_LOGIN_HOST!r} ({_MICROSOFT_TOKEN_HOST_TAG})."
        )
    host = (parsed.hostname or "").lower()
    if host != _ALLOWLISTED_LOGIN_HOST:
        raise ValueError(
            f"auth.token_url host {host!r} is not allowlisted; expected "
            f"{_ALLOWLISTED_LOGIN_HOST!r} ({_MICROSOFT_TOKEN_HOST_TAG})."
        )
    if parsed.username or parsed.password:
        raise ValueError(
            f"auth.token_url must not include userinfo ({_MICROSOFT_TOKEN_HOST_TAG})."
        )
