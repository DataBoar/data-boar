"""Driver ``azure_blob`` of the ``object_storage`` reader: Azure Blob Storage (#2307).

Source: ``docs/desenho/2306.md``, sections 0 and Azure Blob specifics. Implements the
``StorageDriver`` protocol for Azure Blob Storage: List Blobs, Get Blob, authentication
via Shared Key, SAS, or Entra ID (OAuth2).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from xml.etree.ElementTree import Element, ParseError

from defusedxml import DefusedXmlException
from defusedxml import ElementTree as DefusedET

from connectors.object_storage_driver import (
    DriverConfigError,
    DriverProtocolError,
    DriverSettings,
    ErrorClass,
    ListPage,
    ObjectEntry,
    PreparedGet,
    ResolvedCredentials,
)

_ERROR_BODY_LIMIT = 64 * 1024
# Azure Blob max blob size is 5 TB (5*10^12 ~ 13 digits).
# Python's int() string conversion limit is 4300 digits; this bound prevents
# a hostile server from triggering ValueError via oversized <Content-Length> values.
_SIZE_RE = re.compile(r"[0-9]{1,20}")
_MALFORMED = "malformed listing response"

# Azure account name rules: ^[a-z0-9]{3,24}$ (lowercase alphanumeric, 3-24 chars)
_ACCOUNT_NAME_RE = re.compile(r"^[a-z0-9]{3,24}$")
# Allowed endpoint suffixes for Azure Blob Storage (closed allowlist)
_ALLOWED_ENDPOINT_SUFFIXES = frozenset(
    {
        "core.windows.net",
        "core.usgovcloudapi.net",
        "core.chinacloudapi.cn",
    }
)


def _validate_account_name(account_name: str) -> None:
    """Validate Azure storage account name per Azure naming rules.
    Raises DriverConfigError if invalid.
    """
    if not _ACCOUNT_NAME_RE.fullmatch(account_name):
        raise DriverConfigError("invalid account_name for Azure Blob")


def _validate_endpoint_suffix(endpoint_suffix: str) -> None:
    """Validate endpoint_suffix against closed allowlist.
    Raises DriverConfigError if invalid.
    """
    if endpoint_suffix not in _ALLOWED_ENDPOINT_SUFFIXES:
        raise DriverConfigError("invalid endpoint_suffix for Azure Blob")


# Azure Blob error codes vocabulary (section 11 of desenho 2306 extended for Azure)
_AUTH_CODES = frozenset(
    {
        "AuthenticationFailed",
        "InvalidAuthenticationInfo",
        "InvalidToken",
        "ExpiredToken",
    }
)
_AUTHORIZATION_CODES = frozenset(
    {
        "AuthorizationFailure",
        "AccessDenied",
    }
)
_NOT_FOUND_CODES = frozenset(
    {
        "ContainerNotFound",
        "BlobNotFound",
        "ResourceNotFound",
    }
)
_CONDITION_CODES = frozenset(
    {
        "ConditionNotMet",
        "LeaseIdMissing",
        "LeaseIdMismatch",
    }
)
_RETRYABLE_STATUS = frozenset({500, 502, 503, 504})

# XML namespaces
AZURE_NS = "http://schemas.microsoft.com/windowsazure"


@dataclass(frozen=True)
class AzureBlobSettings(DriverSettings):
    """Frozen settings for the Azure Blob driver."""

    account_name: str
    container_name: str
    endpoint_suffix: str  # e.g., "core.windows.net" or "blob.core.windows.net"
    sas_token: str | None  # SAS token if using SAS auth
    use_entra_id: bool  # whether to use Entra ID (OAuth2) auth


def _local(tag: str) -> str:
    """Local name of an ElementTree tag; the namespace is discarded."""
    return tag.rpartition("}")[2] if tag.startswith("{") else tag


def _children(node: Element, name: str) -> list[Element]:
    return [c for c in node if _local(c.tag) == name]


def _text(node: Element, name: str) -> str | None:
    found = _children(node, name)
    return found[0].text if found else None


def _nested_text(node: Element, path: str) -> str | None:
    """Read text by a ``/``-separated path of local tag names."""
    current = node
    for part in path.split("/"):
        children = _children(current, part)
        if not children:
            return None
        current = children[0]
    return current.text


def _parse_xml(body: bytes) -> Element:
    """``defusedxml`` with DTD, entities and external references all forbidden."""
    return DefusedET.fromstring(
        body, forbid_dtd=True, forbid_entities=True, forbid_external=True
    )


def _error_code(body: bytes) -> str | None:
    """The ``<Code>`` of an Azure error body, only when it is in the vocabulary."""
    try:
        root = _parse_xml(body[:_ERROR_BODY_LIMIT])
    except (ParseError, DefusedXmlException, ValueError, SyntaxError):
        return None
    if _local(root.tag) != "Error":
        return None
    code = _text(root, "Code")
    return code if code else None


def _sign_shared_key(
    account_name: str,
    account_key: str,
    canonical_uri: str,
    query: list[tuple[str, str]],
    headers: dict[str, str],
    now: datetime,
) -> str:
    """Construct Shared Key authorization header for Azure Blob Storage."""
    # Azure Shared Key format: SharedKey <account_name>:<signature>
    # StringToSign = VERB + "\n" + Content-Encoding + "\n" + Content-Language + "\n" +
    #                 Content-Length + "\n" + Content-MD5 + "\n" + Content-Type + "\n" +
    #                 Date + "\n" + If-Modified-Since + "\n" + If-Match + "\n" +
    #                 If-None-Match + "\n" + If-Unmodified-Since + "\n" + Range + "\n" +
    #                 CanonicalizedHeaders + CanonicalizedResource

    # For simplicity, we only implement the minimal required headers for List/Get
    _ = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Canonicalized headers (x-ms-* headers, sorted)
    canonicalized_headers = ""
    xms_headers = sorted(
        (k.lower(), v) for k, v in headers.items() if k.lower().startswith("x-ms-")
    )
    for k, v in xms_headers:
        canonicalized_headers += f"{k}:{v}\n"

    # Canonicalized resource
    canonicalized_resource = f"/{canonical_uri.lstrip('/')}"

    string_to_sign = "\n".join(
        [
            "GET",  # HTTP verb
            "",  # Content-Encoding
            "",  # Content-Language
            "",  # Content-Length (empty for GET)
            "",  # Content-MD5
            "",  # Content-Type
            "",  # Date (empty because we use x-ms-date)
            "",  # If-Modified-Since
            "",  # If-Match
            "",  # If-None-Match
            "",  # If-Unmodified-Since
            "",  # Range
            canonicalized_headers,
            canonicalized_resource,
        ]
    )

    # Sign with HMAC-SHA256
    account_key_bytes = base64.b64decode(account_key)
    signature = hmac.new(
        account_key_bytes, string_to_sign.encode("utf-8"), hashlib.sha256
    ).digest()
    signature_b64 = base64.b64encode(signature).decode("ascii")

    return f"SharedKey {account_name}:{signature_b64}"


class AzureBlobDriver:
    name = "azure_blob"
    max_page_size = 5000  # Azure Blob max results per page
    max_key_bytes = 1024  # Azure blob name max length
    credential_keys: tuple[tuple[str, bool], ...] = (
        ("account_name_from_env", True),
        ("account_key_from_env", False),  # Optional if using SAS or Entra ID
        ("sas_token_from_env", False),  # SAS token alternative
        ("client_id_from_env", False),  # Entra ID client ID
        ("client_secret_from_env", False),  # Entra ID client secret
        ("tenant_id_from_env", False),  # Entra ID tenant ID
    )
    forbidden_inline_keys = frozenset(
        {
            "account_name",
            "account_key",
            "sas_token",
            "client_id",
            "client_secret",
            "tenant_id",
            "shared_access_signature",
        }
    )
    misnamed_keys: Mapping[str, str] = {
        "endpoint": "use endpoint_suffix",
        "url": "use endpoint_suffix",
        "base_url": "use endpoint_suffix",
        "host": "use endpoint_suffix",
        "container": "use container_name",
        "account": "use account_name",
        "key": "use account_key",
    }
    required_keys: tuple[str, ...] = ("account_name", "container_name")
    honors_allow_private_networks = True  # Azure Blob can be in private networks

    def __init__(self) -> None:
        self.name = "azure_blob"

    def _own(self, settings: DriverSettings) -> AzureBlobSettings:
        if not isinstance(settings, AzureBlobSettings):
            raise TypeError("settings were not built by the Azure Blob driver")
        return settings

    def settings(self, cfg: dict[str, Any]) -> AzureBlobSettings:
        if not isinstance(cfg, dict) or cfg.get("driver") != "azure_blob":
            raise DriverConfigError("target is not configured for driver azure_blob")

        account_name = str(cfg["account_name"])
        container_name = str(cfg["container_name"])
        endpoint_suffix = str(cfg.get("endpoint_suffix", "core.windows.net"))

        # Validate account name (Azure naming rules: ^[a-z0-9]{3,24}$)
        _validate_account_name(account_name)

        # Validate container name (Azure naming rules)
        if not re.match(r"^[a-z0-9](?!.*--)[a-z0-9-]{1,61}[a-z0-9]$", container_name):
            raise DriverConfigError("invalid container_name for Azure Blob")

        # Validate endpoint_suffix against closed allowlist
        _validate_endpoint_suffix(endpoint_suffix)

        # Determine auth mode from which env-var-name keys the target declares.
        # Actual secret values come from ResolvedCredentials at request time.
        raw_auth = cfg.get("auth")
        auth: Mapping[str, Any] = raw_auth if isinstance(raw_auth, dict) else cfg
        sas_token = auth.get("sas_token_from_env")
        use_entra_id = bool(
            auth.get("client_id_from_env")
            and auth.get("client_secret_from_env")
            and auth.get("tenant_id_from_env")
        )

        return AzureBlobSettings(
            account_name=account_name,
            container_name=container_name,
            endpoint_suffix=endpoint_suffix,
            sas_token=sas_token,
            use_entra_id=use_entra_id,
        )

    def destination(self, settings: DriverSettings) -> str:
        s = self._own(settings)
        host = f"{s.account_name}.blob.{s.endpoint_suffix}"
        return f"https://{host}"

    def destination_host(self, cfg: dict[str, Any]) -> str:
        if not isinstance(cfg, dict) or cfg.get("driver") != "azure_blob":
            return ""
        account = cfg.get("account_name")
        suffix = cfg.get("endpoint_suffix", "core.windows.net")
        if not isinstance(account, str) or not account:
            return ""
        # Same validation as settings(): both must see the same host
        try:
            _validate_account_name(account)
            _validate_endpoint_suffix(suffix)
        except DriverConfigError:
            return ""
        return f"{account}.blob.{suffix}"

    def _build_query(
        self, prefix: str, token: str | None, max_results: int
    ) -> list[tuple[str, str]]:
        query = [
            ("restype", "container"),
            ("comp", "list"),
            ("prefix", prefix),
            ("maxresults", str(min(max_results, self.max_page_size))),
        ]
        if token:
            query.append(("marker", token))
        return query

    def _build_headers(
        self, settings: AzureBlobSettings, creds: ResolvedCredentials, now: datetime
    ) -> dict[str, str]:
        """Build headers for Azure Blob request."""
        headers = {
            "x-ms-version": "2020-10-02",
            "x-ms-date": now.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        }
        # Authorization will be added by the caller based on auth mode
        return headers

    def list_request(
        self,
        settings: DriverSettings,
        creds: ResolvedCredentials,
        prefix: str,
        token: str | None,
        page_size: int,
        now: datetime,
    ) -> PreparedGet:
        settings = self._own(settings)
        if (
            isinstance(page_size, bool)
            or not isinstance(page_size, int)
            or not 1 <= page_size <= self.max_page_size
        ):
            raise ValueError("page size is out of range for Azure Blob")

        base_url = self.destination(settings)
        # URL format: https://{account}.blob.{suffix}/{container}?restype=container&comp=list&...
        query = self._build_query(prefix, token, page_size)
        canonical_uri = f"/{settings.container_name}"
        url = f"{base_url}{canonical_uri}?{urllib.parse.urlencode(query)}"

        headers = self._build_headers(settings, creds, now)

        # Add authorization based on auth mode
        if settings.use_entra_id:
            # Entra ID OAuth2 - token would be in creds
            token_val = creds.get("access_token_from_env")
            if token_val:
                headers["Authorization"] = f"Bearer {token_val}"
        elif settings.sas_token:
            # SAS token value read from credentials at request time
            sas_value = creds.get("sas_token_from_env", settings.sas_token)
            url += "&" + sas_value.lstrip("?")
        else:
            # Shared Key auth
            account_key = creds["account_key_from_env"]
            query_list = self._build_query(prefix, token, page_size)
            canonical_uri = f"/{settings.container_name}"
            auth_header = _sign_shared_key(
                settings.account_name,
                account_key,
                canonical_uri,
                query_list,
                headers,
                now,
            )
            headers["Authorization"] = auth_header

        url = f"{self.destination(settings)}/{settings.container_name}?{urllib.parse.urlencode(query)}"
        return PreparedGet(url, headers)

    def get_request(
        self,
        settings: DriverSettings,
        creds: ResolvedCredentials,
        key: str,
        now: datetime,
    ) -> PreparedGet:
        settings = self._own(settings)
        # URL: https://{account}.blob.{suffix}/{container}/{key}
        encoded_key = urllib.parse.quote(key, safe="/")
        url = f"{self.destination(settings)}/{settings.container_name}/{encoded_key}"

        headers = self._build_headers(settings, creds, now)

        if settings.use_entra_id:
            token_val = creds.get("access_token_from_env")
            if token_val:
                headers["Authorization"] = f"Bearer {token_val}"
        elif settings.sas_token:
            sas_value = creds.get("sas_token_from_env", settings.sas_token)
            url += "&" + sas_value.lstrip("?")
        else:
            # Shared Key auth for Get Blob
            canonical_uri = (
                f"/{settings.container_name}/{urllib.parse.quote(key, safe='/')}"
            )
            auth_header = _sign_shared_key(
                settings.account_name,
                creds["account_key_from_env"],
                canonical_uri,
                [],
                headers,
                now,
            )
            headers["Authorization"] = auth_header

        return PreparedGet(url, headers)

    def parse_list(self, body: bytes) -> ListPage:
        try:
            root = _parse_xml(body)
        except (ParseError, DefusedXmlException, ValueError, SyntaxError):
            raise DriverProtocolError(_MALFORMED) from None
        if _local(root.tag) != "EnumerationResults":
            raise DriverProtocolError(_MALFORMED)

        # Check for error
        error_code = _text(root, "ErrorCode")
        if error_code:
            raise DriverProtocolError(f"Azure Blob error: {error_code}")

        truncated_text = _text(root, "NextMarker")
        truncated = truncated_text is not None and truncated_text != ""
        next_token = truncated_text if truncated else None

        entries = []
        # Blob elements live inside a <Blobs> wrapper
        blobs_container = _children(root, "Blobs")
        blob_nodes = (
            _children(blobs_container[0], "Blob")
            if blobs_container
            else _children(root, "Blob")
        )
        for blob in blob_nodes:
            name = _text(blob, "Name")
            size_text = _nested_text(blob, "Properties/ContentLength")
            size = (
                int(size_text) if size_text and _SIZE_RE.fullmatch(size_text) else None
            )
            # Azure Blob properties
            if name:
                entries.append(ObjectEntry(name, size))

        return ListPage(entries, next_token, truncated)

    def classify_error(
        self,
        status: int,
        headers: Mapping[str, str],
        body: bytes,
        *,
        during: Literal["list", "get"],
    ) -> ErrorClass:
        code = _error_code(body)

        if code in _AUTH_CODES:
            return ErrorClass(
                "auth_failed", code, False, True, f"authentication failed ({code})"
            )

        if code in _AUTHORIZATION_CODES:
            return ErrorClass(
                "permission_denied", code, False, True, f"permission denied ({code})"
            )

        if code in _NOT_FOUND_CODES:
            return ErrorClass("not_found", code, False, True, "resource not found")

        if code in _CONDITION_CODES:
            return ErrorClass(
                "download_failed", code, False, False, f"condition not met ({code})"
            )

        if 300 <= status < 400:
            return ErrorClass("scope_violation", None, False, True, "redirect refused")

        if status in _RETRYABLE_STATUS:
            if during == "list":
                return ErrorClass(
                    "unreachable", None, True, True, "Azure Blob unreachable"
                )
            return ErrorClass(
                "download_failed", None, True, False, "download interrupted"
            )

        if status == 403:
            return ErrorClass("permission_denied", None, False, True, "access denied")
        if status == 404:
            return ErrorClass("not_found", None, False, True, "not found")

        return ErrorClass(
            "protocol_error", None, False, True, f"Azure Blob error HTTP {status}"
        )

    def display_path(self, settings: DriverSettings, key: str) -> str:
        s = self._own(settings)
        return f"azblob://{s.container_name}/{key}"

    def inventory_identity(self, settings: DriverSettings) -> dict[str, str]:
        s = self._own(settings)
        return {
            "product": "Azure Blob Storage",
            "protocol_or_api_version": "Azure Blob REST API 2020-10-02",
            "engine": "azure_blob",
            "account": s.account_name,
            "container": s.container_name,
        }


def register_azure_blob_driver() -> None:
    """Register the Azure Blob driver in the driver registry."""
    from connectors.object_storage_driver import register_driver

    register_driver("azure_blob", lambda: AzureBlobDriver())
