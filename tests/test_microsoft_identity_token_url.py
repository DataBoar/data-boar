"""Microsoft token URL allowlist (#2007) — parsing edges before client_secret POST.

Power BI / Dataverse already cover the default template URL and a generic
attacker host. These cases pin the helper itself: scheme, userinfo, and
suffix lookalikes must not reach pinned_httpx_request.
"""

from __future__ import annotations

import pytest

from connectors.microsoft_identity import assert_allowlisted_microsoft_token_url

_OK = "https://login.microsoftonline.com/tenant/oauth2/v2.0/token"


@pytest.mark.parametrize(
    "url",
    [
        _OK,
        "HTTPS://LOGIN.MICROSOFTONLINE.COM/tenant/oauth2/v2.0/token",
        "https://login.microsoftonline.com:443/tenant/oauth2/v2.0/token",
        f" {_OK} ",
    ],
)
def test_allowlisted_microsoft_login_hosts_pass(url: str) -> None:
    assert_allowlisted_microsoft_token_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://login.microsoftonline.com/tenant/oauth2/v2.0/token",
        "https://stolen:secret@login.microsoftonline.com/oauth2/v2.0/token",
        "https://login.microsoftonline.com@attacker.example/oauth2/v2.0/token",
        "https://login.microsoftonline.com.attacker.example/oauth2/v2.0/token",
        "https://login.microsoftonline.us/tenant/oauth2/v2.0/token",
        "https://attacker.example/oauth/token",
        "",
        "   ",
    ],
)
def test_non_allowlisted_microsoft_token_urls_fail_closed(url: str) -> None:
    with pytest.raises(ValueError, match="#2007"):
        assert_allowlisted_microsoft_token_url(url)


def test_userinfo_on_microsoft_login_host_does_not_post_secret() -> None:
    """Userinfo would otherwise keep hostname allowlisted while leaking creds in the URL."""
    with pytest.raises(ValueError, match="userinfo"):
        assert_allowlisted_microsoft_token_url(
            "https://stolen:secret@login.microsoftonline.com/oauth2/v2.0/token"
        )
