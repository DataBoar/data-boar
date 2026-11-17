"""Microsoft identity (Azure AD) token endpoint host allowlist (#2007).

HubSpot uses a fixed vendor API host before attaching secrets (#1607). Power BI and
Dataverse POST client secrets to ``auth.token_url``; IP pinning alone does not block
a public attacker host. Only ``login.microsoftonline.com`` is allowlisted today.
"""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlparse

_MICROSOFT_TOKEN_HOST_TAG = "#2007"
_ALLOWLISTED_LOGIN_HOST = "login.microsoftonline.com"


def assert_allowlisted_microsoft_token_url(
    url: str,
    allowed_hosts: Iterable[str] | None = None,
    *,
    label: str = "auth.token_url",
) -> None:
    """Refuse token exchange to login hosts outside the allowlist.

    Without ``allowed_hosts`` the #2007 behaviour is unchanged: only
    ``login.microsoftonline.com``. A caller that reads its allowlist from the target
    YAML (sovereign clouds, ``sharepoint_online``) passes it explicitly; an empty
    allowlist refuses every host.
    """
    if allowed_hosts is None:
        allowed = {_ALLOWLISTED_LOGIN_HOST}
    else:
        allowed = {str(h).strip().lower() for h in allowed_hosts if str(h).strip()}
    shown = ", ".join(repr(h) for h in sorted(allowed)) or "<none>"
    parsed = urlparse((url or "").strip())
    if parsed.scheme.lower() != "https":
        raise ValueError(
            f"{label} must use https:// and host {shown} ({_MICROSOFT_TOKEN_HOST_TAG})."
        )
    host = (parsed.hostname or "").lower()
    if host not in allowed:
        raise ValueError(
            f"{label} host {host!r} is not allowlisted; expected "
            f"{shown} ({_MICROSOFT_TOKEN_HOST_TAG})."
        )
    if parsed.username or parsed.password:
        raise ValueError(
            f"{label} must not include userinfo ({_MICROSOFT_TOKEN_HOST_TAG})."
        )
