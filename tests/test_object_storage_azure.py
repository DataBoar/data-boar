"""Unit tests for the Azure Blob driver (issue #2307).

Mirrors tests/test_object_storage_driver.py: drives S3Driver's sibling AzureBlobDriver
through the StorageDriver contract with a MockTransport fake. No network, no real credential.
"""

from __future__ import annotations

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
    entra = driver.settings(
        _cfg(
            account_key_from_env=None,
            client_id_from_env="cid",
            client_secret_from_env="sec",
            tenant_id_from_env="tid",
        )
    )
    assert entra.use_entra_id is True


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
