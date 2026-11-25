"""Unit tests for the Azure Blob driver (issue #2307).

Mirrors tests/test_object_storage_driver.py: drives S3Driver's sibling AzureBlobDriver
through the StorageDriver contract with a MockTransport fake. No network, no real credential.
"""

from __future__ import annotations

import logging
import base64
import dataclasses
from datetime import datetime, timezone
from typing import Any

import pytest

from connectors.object_storage_driver import (
    DriverConfigError,
    DriverProtocolError,
    ErrorClass,
    ListPage,
    ObjectEntry,
    PreparedGet,
    ResolvedCredentials,
)
from connectors.object_storage_azure import AzureBlobDriver, AzureBlobSettings

ACCOUNT = "syntheticsa"
CONTAINER = "databoar-sintetico"
SUFFIX = "core.windows.net"
T0 = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)


def _synthetic_account_key() -> str:
    """Synthetic Azure account key, built at runtime (never a key-shaped literal in the repo)."""
    return base64.b64encode(b"test-key-" + b"synthetic\n").decode("ascii")


def _creds(**extra: str) -> ResolvedCredentials:
    values: dict[str, str] = {
        "account_name_from_env": ACCOUNT,
        "account_key_from_env": _synthetic_account_key(),  # synthetic, assembled at runtime
    }
    values.update(extra)
    return ResolvedCredentials(values)


def _cfg(**extra: Any) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "name": "azure-target",
        "type": "object_storage",
        "driver": "azure_blob",
        "account_name": ACCOUNT,
        "container_name": CONTAINER,
    }
    cfg.update(extra)
    return cfg


def test_settings_builds_frozen_settings() -> None:
    driver = AzureBlobDriver()
    settings = driver.settings(_cfg())
    assert isinstance(settings, AzureBlobSettings)
    assert settings.account_name == ACCOUNT
    assert settings.container_name == CONTAINER
    assert settings.endpoint_suffix == SUFFIX
    assert settings.sas_token is None
    assert settings.use_entra_id is False
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(settings, "account_name", "other")


def test_settings_rejects_wrong_driver_and_bad_container() -> None:
    driver = AzureBlobDriver()
    with pytest.raises(DriverConfigError):
        driver.settings(_cfg(driver="s3"))
    with pytest.raises(DriverConfigError):
        driver.settings(_cfg(container_name="Bad_NAME"))
    with pytest.raises(DriverConfigError):
        driver.settings(_cfg(container_name="ab"))  # too short
    with pytest.raises(KeyError):
        driver.settings(
            {"driver": "azure_blob"}
        )  # missing required keys are checked by common layer


def test_settings_auth_modes() -> None:
    driver = AzureBlobDriver()
    sas = driver.settings(
        _cfg(account_key_from_env=None, sas_token_from_env="sv=2020&sig=synthetic")
    )
    assert sas.sas_token == "sv=2020&sig=synthetic"
    assert sas.use_entra_id is False


@pytest.mark.parametrize(
    "entra_keys",
    [
        {
            "client_id_from_env": "cid",
            "client_secret_from_env": "sec",
            "tenant_id_from_env": "tid",
        },
        {"client_id_from_env": "cid"},
        {"tenant_id_from_env": "tid", "sas_token_from_env": "sv=2020&sig=x"},
    ],
)
@pytest.mark.parametrize("in_auth", [False, True])
def test_entra_id_keys_are_refused_until_2368(
    entra_keys: dict[str, str], in_auth: bool
) -> None:
    """#2370 N1: the driver never obtains an Entra ID token, so a target with
    Entra keys would send unauthenticated requests (a public container would
    scan anonymously and look "complete"). Refuse it at config time."""
    driver = AzureBlobDriver()
    cfg = _cfg(auth=dict(entra_keys)) if in_auth else _cfg(**entra_keys)
    with pytest.raises(DriverConfigError, match=r"Entra ID .*not supported.*#2368"):
        driver.settings(cfg)


def test_destination_and_display_path() -> None:
    driver = AzureBlobDriver()
    settings = driver.settings(_cfg())
    assert driver.destination(settings) == f"https://{ACCOUNT}.blob.{SUFFIX}"
    assert driver.destination_host(_cfg()) == f"{ACCOUNT}.blob.{SUFFIX}"
    assert driver.display_path(settings, "corpus/a.txt") == (
        f"azblob://{CONTAINER}/corpus/a.txt"
    )


def test_inventory_identity() -> None:
    driver = AzureBlobDriver()
    settings = driver.settings(_cfg())
    ident = driver.inventory_identity(settings)
    assert ident["product"] == "Azure Blob Storage"
    assert ident["engine"] == "azure_blob"
    assert ident["container"] == CONTAINER
    assert ident["account"] == ACCOUNT


def test_list_request_builds_prepared_get() -> None:
    driver = AzureBlobDriver()
    settings = driver.settings(_cfg())
    prep = driver.list_request(settings, _creds(), "corpus/", None, 100, T0)
    assert isinstance(prep, PreparedGet)
    assert prep.url.startswith(f"https://{ACCOUNT}.blob.{SUFFIX}/{CONTAINER}?")
    assert "restype=container" in prep.url
    assert "comp=list" in prep.url
    assert "maxresults=100" in prep.url
    assert "x-ms-version" in prep.headers
    assert "Authorization" in prep.headers

    prep2 = driver.list_request(settings, _creds(), "corpus/", "marker-1", 100, T0)
    assert "marker=marker-1" in prep2.url

    with pytest.raises(ValueError):
        driver.list_request(settings, _creds(), "corpus/", None, 0, T0)


def test_get_request_builds_prepared_get() -> None:
    driver = AzureBlobDriver()
    settings = driver.settings(_cfg())
    prep = driver.get_request(settings, _creds(), "corpus/a b.txt", T0)
    assert isinstance(prep, PreparedGet)
    assert prep.url.startswith(
        f"https://{ACCOUNT}.blob.{SUFFIX}/{CONTAINER}/corpus/a%20b.txt"
    )
    assert "Authorization" in prep.headers


# Synthetic container SAS query string (no live credentials in repo).
_CONTAINER_SAS = (
    "sp=rl&st=2026-01-01T00%3A00%3A00Z&se=2027-01-01T00%3A00%3A00Z"
    "&spr=https&sv=2024-11-04&sr=c&sig=syntheticSasSignature"
)


def _sas_settings() -> AzureBlobSettings:
    driver = AzureBlobDriver()
    return driver.settings(
        _cfg(account_key_from_env=None, sas_token_from_env="DATA_BOAR_AZURE_SAS")
    )


def _sas_creds(token: str = _CONTAINER_SAS) -> ResolvedCredentials:
    return ResolvedCredentials(
        {
            "account_name_from_env": ACCOUNT,
            "sas_token_from_env": token,
        }
    )


def test_list_request_sas_url_includes_query_once_and_no_auth_header() -> None:
    driver = AzureBlobDriver()
    settings = _sas_settings()
    prep = driver.list_request(settings, _sas_creds(), "corpus/", None, 5, T0)
    assert "restype=container" in prep.url
    assert "comp=list" in prep.url
    assert "maxresults=5" in prep.url
    assert f"&{_CONTAINER_SAS}" in prep.url or prep.url.endswith(_CONTAINER_SAS)
    assert prep.url.count("sig=syntheticSasSignature") == 1
    assert "Authorization" not in prep.headers
    assert prep.url.index("?") < prep.url.index("sp=rl")
    assert "&sp=rl" in prep.url


def test_list_request_sas_strips_leading_question_on_token() -> None:
    driver = AzureBlobDriver()
    settings = _sas_settings()
    token = "?" + _CONTAINER_SAS
    prep = driver.list_request(settings, _sas_creds(token), "", None, 2, T0)
    assert prep.url.count("?") == 1
    assert "?restype=container" in prep.url
    assert prep.url.count("sig=syntheticSasSignature") == 1


def test_get_request_sas_url_uses_question_mark_and_no_auth_header() -> None:
    driver = AzureBlobDriver()
    settings = _sas_settings()
    prep = driver.get_request(settings, _sas_creds(), "corpus/blob.png", T0)
    assert prep.url.startswith(
        f"https://{ACCOUNT}.blob.{SUFFIX}/{CONTAINER}/corpus/blob.png?"
    )
    assert _CONTAINER_SAS in prep.url
    assert prep.url.count("?") == 1
    assert prep.url.count("sig=syntheticSasSignature") == 1
    assert "Authorization" not in prep.headers


def test_get_request_sas_strips_leading_question_on_token() -> None:
    driver = AzureBlobDriver()
    settings = _sas_settings()
    prep = driver.get_request(settings, _sas_creds("?" + _CONTAINER_SAS), "x.bin", T0)
    assert prep.url.count("?") == 1
    assert prep.url.endswith(_CONTAINER_SAS)


def test_sas_mode_missing_resolved_token_raises_driver_config_error() -> None:
    driver = AzureBlobDriver()
    settings = _sas_settings()
    creds = ResolvedCredentials({"account_name_from_env": ACCOUNT})
    with pytest.raises(DriverConfigError, match="sas_token_from_env"):
        driver.list_request(settings, creds, "corpus/", None, 5, T0)
    with pytest.raises(DriverConfigError, match="sas_token_from_env"):
        driver.get_request(settings, creds, "corpus/a.txt", T0)


def test_shared_key_missing_account_key_raises_driver_config_error() -> None:
    driver = AzureBlobDriver()
    settings = driver.settings(_cfg())
    creds = ResolvedCredentials({"account_name_from_env": ACCOUNT})
    with pytest.raises(DriverConfigError, match="account_key_from_env"):
        driver.list_request(settings, creds, "corpus/", None, 5, T0)
    with pytest.raises(DriverConfigError, match="account_key_from_env"):
        driver.get_request(settings, creds, "corpus/a.txt", T0)


def test_shared_key_list_and_get_still_set_authorization() -> None:
    driver = AzureBlobDriver()
    settings = driver.settings(_cfg())
    list_prep = driver.list_request(settings, _creds(), "p/", None, 10, T0)
    get_prep = driver.get_request(settings, _creds(), "p/obj.txt", T0)
    assert list_prep.headers["Authorization"].startswith("SharedKey ")
    assert get_prep.headers["Authorization"].startswith("SharedKey ")
    assert "sig=syntheticSasSignature" not in list_prep.url


_AZURE_LIST = f'''<?xml version="1.0" encoding="utf-8"?>
<EnumerationResults ServiceEndpoint="https://{ACCOUNT}.blob.{SUFFIX}/" ContainerName="{CONTAINER}">
  <Prefix>corpus/</Prefix>
  <Blobs>
    <Blob><Name>corpus/a.txt</Name><Properties><ContentLength>51</ContentLength></Properties></Blob>
    <Blob><Name>corpus/b.txt</Name><Properties><ContentLength>3</ContentLength></Properties></Blob>
  </Blobs>
  <NextMarker>next-token</NextMarker>
</EnumerationResults>'''.encode()


def test_parse_list_reads_entries_and_token() -> None:
    driver = AzureBlobDriver()
    page = driver.parse_list(_AZURE_LIST)
    assert isinstance(page, ListPage)
    assert page.entries == [
        ObjectEntry("corpus/a.txt", 51),
        ObjectEntry("corpus/b.txt", 3),
    ]
    assert page.next_token == "next-token"
    assert page.truncated is True


def test_parse_list_last_page() -> None:
    xml = _AZURE_LIST.replace(b"<NextMarker>next-token</NextMarker>", b"")
    page = AzureBlobDriver().parse_list(xml)
    assert page.next_token is None
    assert page.truncated is False


def test_parse_list_malformed_raises_driver_protocol_error() -> None:
    for body in (b"not xml", b"<Error><Code>Bad</Code></Error>", b"<WrongRoot/>", b""):
        with pytest.raises(DriverProtocolError) as info:
            AzureBlobDriver().parse_list(body)
        assert str(info.value) == "malformed listing response"


def test_parse_list_oversized_size_becomes_none() -> None:
    big = "1" + "0" * 4999
    xml = _AZURE_LIST.replace(
        b"<ContentLength>51</ContentLength>",
        f"<ContentLength>{big}</ContentLength>".encode(),
    )
    page = AzureBlobDriver().parse_list(xml)
    assert page.entries[0] == ObjectEntry("corpus/a.txt", None)


def test_classify_error_table() -> None:
    driver = AzureBlobDriver()

    def error(code: str) -> bytes:
        return f"<Error><Code>{code}</Code><Message>m</Message></Error>".encode()

    got = driver.classify_error(403, {}, error("AuthenticationFailed"), during="list")
    assert isinstance(got, ErrorClass)
    assert got.reason == "auth_failed"
    assert got.ends_target is True

    got = driver.classify_error(403, {}, error("AuthorizationFailure"), during="list")
    assert got.reason == "permission_denied"

    got = driver.classify_error(404, {}, error("BlobNotFound"), during="get")
    assert got.reason == "not_found"

    got = driver.classify_error(503, {}, b"", during="list")
    assert got.reason == "unreachable"
    assert got.retryable is True

    got = driver.classify_error(302, {}, b"", during="list")
    assert got.reason == "scope_violation"

    got = driver.classify_error(400, {}, b"", during="get")
    assert got.reason == "protocol_error"


# --- INCREMENT 1: validation tests (should FAIL today) ---

_ALLOWED_SUFFIXES = frozenset(
    {
        "core.windows.net",
        "core.usgovcloudapi.net",
        "core.chinacloudapi.cn",
    }
)


@pytest.mark.parametrize(
    "bad_account",
    [
        "SYNTHETICSA",  # uppercase
        "sa",  # too short (<3)
        "s" * 25,  # too long (>24)
        "syn/sa",  # contains "/"
        "syn@sa",  # contains "@"
        "syn.sa",  # contains "."
        "syn:sa",  # contains ":"
        "syn sa",  # contains whitespace
        "syn-sa",  # contains "-" (not in ^[a-z0-9]{3,24}$)
        "syn_sa",  # contains "_" (not in ^[a-z0-9]{3,24}$)
    ],
)
def test_settings_rejects_invalid_account_name(bad_account: str) -> None:
    """settings() must reject account_name not matching ^[a-z0-9]{3,24}$."""
    driver = AzureBlobDriver()
    with pytest.raises(DriverConfigError):
        driver.settings(_cfg(account_name=bad_account))


@pytest.mark.parametrize(
    "bad_suffix",
    [
        "evil.example",  # not in allowed list
        "core.windows.net/x",  # path traversal attempt
        "core.windows.net@evil",  # credential injection attempt
        "core.windows.net:443",  # port injection attempt
        "blob.core.windows.net",  # not in allowed list (full host)
        "core.windows.net.",  # trailing dot
        "core.windows.net..",  # double dot
        "",  # empty
    ],
)
def test_settings_rejects_invalid_endpoint_suffix(bad_suffix: str) -> None:
    """settings() must reject endpoint_suffix outside the closed allowlist."""
    driver = AzureBlobDriver()
    with pytest.raises(DriverConfigError):
        driver.settings(_cfg(endpoint_suffix=bad_suffix))


@pytest.mark.parametrize(
    "bad_account",
    [
        "SYNTHETICSA",
        "sa",
        "s" * 25,
        "syn/sa",
        "syn@sa",
        "syn.sa",
        "syn:sa",
        "syn sa",
        "syn-sa",
        "syn_sa",
    ],
)
def test_destination_host_rejects_invalid_account_name(bad_account: str) -> None:
    """destination_host() must reject account_name not matching ^[a-z0-9]{3,24}$ (returns empty string)."""
    driver = AzureBlobDriver()
    assert driver.destination_host(_cfg(account_name=bad_account)) == ""


@pytest.mark.parametrize(
    "bad_suffix",
    [
        "evil.example",
        "core.windows.net/x",
        "core.windows.net@evil",
        "core.windows.net:443",
        "blob.core.windows.net",
        "core.windows.net.",
        "core.windows.net..",
        "",
    ],
)
def test_destination_host_rejects_invalid_endpoint_suffix(bad_suffix: str) -> None:
    """destination_host() must reject endpoint_suffix outside the closed allowlist (returns empty string)."""
    driver = AzureBlobDriver()
    assert driver.destination_host(_cfg(endpoint_suffix=bad_suffix)) == ""


@pytest.mark.parametrize(
    "account,suffix",
    [
        ("syntheticsa", "core.windows.net"),
        ("myaccount123", "core.usgovcloudapi.net"),
        ("storageacc", "core.chinacloudapi.cn"),
    ],
)
def test_valid_account_and_suffix_give_expected_destination(
    account: str, suffix: str
) -> None:
    """Valid account_name and endpoint_suffix give exactly f'https://{account}.blob.{suffix}'."""
    driver = AzureBlobDriver()
    cfg = _cfg(account_name=account, endpoint_suffix=suffix)
    settings = driver.settings(cfg)
    expected_host = f"{account}.blob.{suffix}"
    expected_url = f"https://{expected_host}"
    assert driver.destination(settings) == expected_url
    assert driver.destination_host(cfg) == expected_host


def test_sas_signature_never_reaches_the_httpx_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """#2370 S8: the SAS token travels in the URL, and httpx logs each request URL
    at INFO. Once an azure_blob target is configured, the httpx log must show the
    host only, never the query with the signature."""
    driver = AzureBlobDriver()
    driver.settings(_cfg(auth={"sas_token_from_env": "DATA_BOAR_AZURE_SAS_TOKEN"}))
    url = (
        f"https://{ACCOUNT}.blob.core.windows.net/{CONTAINER}"
        "?restype=container&comp=list&sv=2022-11-02&sp=rl&sig=SYNTHETICSIG"
    )
    with caplog.at_level(logging.INFO, logger="httpx"):
        logging.getLogger("httpx").info('HTTP Request: GET %s "HTTP/1.1 200 OK"', url)
    assert "SYNTHETICSIG" not in caplog.text
    assert f"{ACCOUNT}.blob.core.windows.net" in caplog.text
