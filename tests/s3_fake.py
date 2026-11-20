"""Simulated S3 for the ``object_storage`` reader tests (epic #2306, task 2306.3).

Source: ``docs/desenho/2306.md``, section 13 ("Costuras de teste e S3 simulado"). This is an
auxiliary module, not a test file. It talks only through ``httpx.MockTransport`` (no socket,
no external network, no container, no real credential) and speaks just enough S3 for the
cases of the design: ``ListObjectsV2`` and ``GetObject``, both addressing styles, SigV4
checking, pagination, ``encoding-type=url`` and the failure knobs of section 13.

Contract (kept stable for the acceptance tests; the dev may extend, never change):

- ``FakeS3(bucket, objects, host, addressing="virtual"|"path", region, page_size=1000,
  access_key_id, session_token=None, secret_access_key=None)``. ``host`` may carry a port
  (``minio.lab.example:9000``).
- ``.transport``: serves only ``host``. Any other host records a violation and answers 599.
- ``.requests``: ``Req(method, url, headers)`` per request; ``.operations``: ``"ListObjectsV2"``,
  ``"GetObject"`` or ``"other"`` per request; ``.fetched``: decoded keys asked by ``GetObject``.
- On each request the simulator checks the form of ``Authorization``, ``x-amz-date``,
  ``x-amz-content-sha256``, ``x-amz-security-token`` and ``Host``. A divergence answers
  ``403 SignatureDoesNotMatch`` (a wrong access key id answers ``InvalidAccessKeyId``) and is
  listed in ``.auth_failures``. With ``secret_access_key`` it also recomputes the signature
  (HMAC-SHA256, written here from the AWS specification, independent of the project code).
- The simulator records and never raises: ``.violations`` (unexpected host, query parameter
  outside ``list-type``/``prefix``/``max-keys``/``encoding-type``/``continuation-token``,
  query on ``GetObject``) must be empty at the end of a test.

Credentials are generated at run time with ``secrets.token_hex`` and the prefixes
``SYNTHAK``, ``SYNTHSK`` and ``SYNTHST``. No literal has the shape of a real key.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import json
import re
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator, Literal, NamedTuple
from xml.sax.saxutils import escape

import httpx

AWS_NS = "http://s3.amazonaws.com/doc/2006-03-01/"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
GOOD_IP = "1.1.1.1"
PRIVATE_IP = "10.0.0.5"
METADATA_IP = "169.254.169.254"
EVIL_HOST = "evil.example"
LISTING_LIMIT_BYTES = 16 * 1024 * 1024

_ALLOWED_LIST_PARAMS = frozenset(
    {"list-type", "prefix", "max-keys", "encoding-type", "continuation-token"}
)
_AUTH_RE = re.compile(
    r"^AWS4-HMAC-SHA256 Credential=(?P<key>[^/]+)/(?P<date>\d{8})/(?P<region>[^/]+)"
    r"/s3/aws4_request,\s*SignedHeaders=(?P<signed>[a-z0-9;-]+),\s*"
    r"Signature=(?P<sig>[0-9a-f]{64})$"
)
_AMZ_DATE_RE = re.compile(r"^\d{8}T\d{6}Z$")


# ----------------------------------------------------------------------------
# SigV4 written from the AWS specification (the independent oracle)
# ----------------------------------------------------------------------------


def uri_encode(value: str, *, keep_slash: bool) -> str:
    """AWS URI encoding: unreserved characters stay, everything else is ``%XX`` upper case."""
    return urllib.parse.quote(value, safe="-_.~" + ("/" if keep_slash else ""))


def canonical_query(raw_query: str) -> str:
    pairs: list[tuple[str, str]] = []
    if raw_query:
        for part in raw_query.split("&"):
            name, _, value = part.partition("=")
            pairs.append(
                (
                    uri_encode(urllib.parse.unquote_plus(name), keep_slash=False),
                    uri_encode(urllib.parse.unquote_plus(value), keep_slash=False),
                )
            )
    pairs.sort()
    return "&".join(f"{n}={v}" for n, v in pairs)


def canonical_request(
    method: str,
    raw_path: str,
    raw_query: str,
    headers: dict[str, str],
    signed_headers: list[str],
    payload_hash: str,
) -> str:
    uri = uri_encode(urllib.parse.unquote(raw_path), keep_slash=True) or "/"
    block = "".join(
        f"{name}:{' '.join(headers.get(name, '').split())}\n" for name in signed_headers
    )
    return "\n".join(
        [
            method,
            uri,
            canonical_query(raw_query),
            block,
            ";".join(signed_headers),
            payload_hash,
        ]
    )


def compute_signature(
    secret_access_key: str, region: str, amz_date: str, canonical_req: str
) -> str:
    day = amz_date[:8]

    def mac(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    k = mac(("AWS4" + secret_access_key).encode("utf-8"), day)
    for part in (region, "s3", "aws4_request"):
        k = mac(k, part)
    scope = f"{day}/{region}/s3/aws4_request"
    to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            scope,
            hashlib.sha256(canonical_req.encode("utf-8")).hexdigest(),
        ]
    )
    return hmac.new(k, to_sign.encode("utf-8"), hashlib.sha256).hexdigest()


def sign_get_headers(
    *,
    url: str,
    host_header: str,
    region: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str | None,
    amz_date: str,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    """A by-hand GET client for the simulator's own self-checks (not for the project)."""
    parts = urllib.parse.urlsplit(url)
    headers = {
        "host": host_header,
        "x-amz-content-sha256": EMPTY_SHA256,
        "x-amz-date": amz_date,
    }
    if session_token:
        headers["x-amz-security-token"] = session_token
    headers.update({k.lower(): v for k, v in (extra_headers or {}).items()})
    signed = sorted(headers)
    cr = canonical_request(
        "GET", parts.path, parts.query, headers, signed, EMPTY_SHA256
    )
    signature = compute_signature(secret_access_key, region, amz_date, cr)
    headers["authorization"] = (
        f"AWS4-HMAC-SHA256 Credential={access_key_id}/{amz_date[:8]}/{region}/s3/"
        f"aws4_request, SignedHeaders={';'.join(signed)}, Signature={signature}"
    )
    return headers


# ----------------------------------------------------------------------------
# Small test doubles shared by the acceptance tests
# ----------------------------------------------------------------------------


# Synthetic access key id for the AWS documentation vectors (the signature does not depend
# on it); deliberately without the shape of a real key id.
DOC_EXAMPLE_ACCESS_KEY_ID = "SYNTHAK" + "0" * 16


def aws_doc_example_secret() -> str:
    """The example secret of the AWS SigV4 documentation, assembled at run time.

    Accepted repo practice (no literal with the shape of a secret in the file).
    """
    return "wJalrXUtnFEMI/K7MDENG/" + "bPxRfiCYEXAMPLEKEY"


class Creds(NamedTuple):
    access_key_id: str
    secret_access_key: str
    session_token: str | None


def new_credentials(*, with_token: bool = True) -> Creds:
    """Synthetic credentials, different on every call, with greppable markers."""
    return Creds(
        "SYNTHAK" + secrets.token_hex(8).upper(),
        "SYNTHSK" + secrets.token_hex(16),
        ("SYNTHST" + secrets.token_hex(16)) if with_token else None,
    )


class FakeClock:
    """Injectable ``_now`` / ``_sleep``: sleeping advances time, never waits."""

    def __init__(self) -> None:
        self.start = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)
        self.elapsed = 0.0
        self.sleeps: list[float] = []

    def now(self) -> datetime:
        return self.start + timedelta(seconds=self.elapsed)

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.elapsed += seconds


class FakeDB:
    """Stand-in for ``db_manager``. With ``real`` it also forwards to a ``LocalDBManager``."""

    def __init__(self, real: Any = None) -> None:
        self.real = real
        self.findings: list[dict[str, Any]] = []
        self.failures: list[tuple[str, str, str]] = []
        self.inventories: list[dict[str, Any]] = []

    def save_finding(self, source_type: str, **kwargs: Any) -> None:
        self.findings.append({"source_type": source_type, **kwargs})
        if self.real is not None:
            self.real.save_finding(source_type, **kwargs)

    def save_failure(
        self, target_name: str, reason: str, details: str | None = None
    ) -> None:
        self.failures.append((target_name, reason, details or ""))
        if self.real is not None:
            self.real.save_failure(target_name, reason, details)

    def save_data_source_inventory(
        self,
        target_name: str,
        source_type: str,
        product: str | None = None,
        product_version: str | None = None,
        protocol_or_api_version: str | None = None,
        transport_security: str | None = None,
        raw_details: str | None = None,
    ) -> None:
        self.inventories.append(
            {
                "target_name": target_name,
                "source_type": source_type,
                "product": product,
                "product_version": product_version,
                "protocol_or_api_version": protocol_or_api_version,
                "transport_security": transport_security,
                "raw_details": raw_details,
            }
        )
        if self.real is not None:
            self.real.save_data_source_inventory(
                target_name,
                source_type,
                product,
                product_version,
                protocol_or_api_version,
                transport_security,
                raw_details,
            )

    def reasons(self) -> list[str]:
        return [r for _, r, _ in self.failures]

    def details(self, reason: str) -> list[str]:
        return [d for _t, r, d in self.failures if r == reason]

    def inventory_json(self) -> dict[str, Any]:
        assert len(self.inventories) == 1, self.inventories
        return json.loads(self.inventories[0]["raw_details"])

    def as_text(self) -> str:
        return json.dumps(
            {
                "findings": self.findings,
                "failures": self.failures,
                "inventories": self.inventories,
            },
            default=str,
        )


_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")


class RegexScanner:
    """Deterministic detector (CPF, e-mail), same contract as ``scan_file_content``."""

    def scan_file_content(self, content: str, file_path: Any) -> dict[str, Any] | None:
        if _CPF.search(content or ""):
            pattern, norm = "LGPD_CPF", "LGPD Art. 5"
        elif _EMAIL.search(content or ""):
            pattern, norm = "EMAIL", "GDPR Art. 4(1)"
        else:
            return None
        return {
            "sensitivity_level": "HIGH",
            "pattern_detected": pattern,
            "norm_tag": norm,
            "ml_confidence": 100,
        }


def install_fake_dns(monkeypatch: Any, host_ips: dict[str, list[str]]) -> None:
    """Replace ``url_guard._resolve_host_ips`` with a fixed host -> IPs map (else ``OSError``)."""
    import connectors.url_guard as url_guard

    table = {h.lower(): list(ips) for h, ips in host_ips.items()}

    def resolve(host: str) -> list[Any]:
        ips = table.get(host.lower())
        if ips is None:
            raise OSError(f"synthetic DNS: no such host {host}")
        return [ipaddress.ip_address(ip) for ip in ips]

    monkeypatch.setattr(url_guard, "_resolve_host_ips", resolve)


# ----------------------------------------------------------------------------
# The simulator
# ----------------------------------------------------------------------------


class Req(NamedTuple):
    method: str
    url: str
    headers: dict[str, str]

    @property
    def host(self) -> str:
        return urllib.parse.urlsplit(self.url).hostname or ""

    @property
    def path(self) -> str:
        return urllib.parse.urlsplit(self.url).path

    @property
    def raw_query(self) -> str:
        return urllib.parse.urlsplit(self.url).query

    @property
    def signature(self) -> str | None:
        m = _AUTH_RE.match(self.headers.get("authorization", ""))
        return m.group("sig") if m else None


class _CountingStream(httpx.SyncByteStream):
    """Response body that counts the bytes actually pulled by the client."""

    def __init__(self, data: bytes, sink: list[int]) -> None:
        self._data = data
        self._sink = sink

    def __iter__(self) -> Iterator[bytes]:
        for i in range(0, len(self._data), 65536):
            chunk = self._data[i : i + 65536]
            self._sink.append(len(chunk))
            yield chunk


class _Entry(NamedTuple):
    key: str
    size: int | None
    raw: bool


def _token_for(offset: int) -> str:
    # The leading bytes make the base64 start with "+/", so the token needs real encoding.
    return base64.b64encode(b"\xfb\xff" + f"off={offset}".encode()).decode()


def _offset_of(token: str) -> int:
    raw = base64.b64decode(token, validate=True)
    if not raw.startswith(b"\xfb\xffoff="):
        raise ValueError("bad token")
    return int(raw[len(b"\xfb\xffoff=") :])


class FakeS3:
    def __init__(
        self,
        bucket: str,
        objects: dict[str, bytes],
        host: str,
        addressing: Literal["virtual", "path"] = "virtual",
        region: str = "us-east-1",
        page_size: int = 1000,
        access_key_id: str = "",
        session_token: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        self.bucket = bucket
        self.objects = dict(objects)
        host_part, _, port = host.partition(":")
        self.hostname = host_part.lower()
        self.port = int(port) if port else None
        self.addressing = addressing
        self.region = region
        self.page_size = page_size
        self.access_key_id = access_key_id
        self.session_token = session_token
        self.secret_access_key = secret_access_key
        # Observation.
        self.requests: list[Req] = []
        self.operations: list[str] = []
        self.fetched: list[str] = []
        self.violations: list[str] = []
        self.auth_failures: list[str] = []
        self._delivered_sinks: dict[str, list[list[int]]] = {}
        # Plain attributes the tests may flip.
        self.server_header = "FakeS3"
        self.malformed_xml = False
        self.doctype_entity = False
        self.oversized_listing = False
        self.encoding_type: Literal["url"] | None = "url"
        # Any namespace is an ACCEPTED listing (design rev. 5, D-78: read by local name).
        self.namespace: Literal["aws", "other"] | None = "aws"
        self.error_body_echo = False
        self.pagination_mode: Literal["missing_token", "repeat_token"] | None = None
        # Knobs with state.
        self._error_rules: list[dict[str, Any]] = []
        self._throttle: dict[str, Any] | None = None
        self._network: dict[str, Any] | None = None
        self._lies: dict[str, tuple[int | None, int]] = {}
        self._content_lengths: dict[str, int] = {}
        self._injected: dict[str, bytes] = {}
        self._injected_raw: list[str] = []
        self._redirect: dict[str, Any] | None = None
        self.transport = httpx.MockTransport(self._handle)

    # -- identity ----------------------------------------------------------

    @property
    def host(self) -> str:
        """Hostname the simulator serves (without port)."""
        return self.hostname

    @property
    def host_header(self) -> str:
        if self.port in (None, 80, 443):
            return self.hostname
        return f"{self.hostname}:{self.port}"

    # -- knobs ---------------------------------------------------------------

    def error_on(
        self,
        op: str,
        key: str | None = None,
        status: int = 403,
        code: str = "AccessDenied",
        times: int | None = None,
    ) -> None:
        self._error_rules.append(
            {"op": op, "key": key, "status": status, "code": code, "left": times}
        )

    def throttle(
        self,
        n: int,
        status: int = 503,
        code: str = "SlowDown",
        retry_after: int | str | None = None,
        op: str | None = None,
    ) -> None:
        self._throttle = {
            "left": n,
            "status": status,
            "code": code,
            "retry_after": retry_after,
            "op": op,
        }

    def network_error(
        self, n: int | None = None, kind: Literal["connect", "read_timeout"] = "connect"
    ) -> None:
        """Raise the httpx exception in the transport for the next ``n`` requests (all if None)."""
        self._network = {"left": n, "kind": kind}

    def lie_size(self, key: str, declared: int | None, actual: int) -> None:
        """Listing says ``declared`` (None omits ``Size``); the body has ``actual`` bytes."""
        self._lies[key] = (declared, actual)

    def content_length(self, key: str, value: int) -> None:
        self._content_lengths[key] = value

    def inject_keys(
        self, keys: dict[str, bytes] | list[str], *, raw: bool = False
    ) -> None:
        """Hostile listing: these keys show up in every listing, whatever the prefix.

        With ``raw=True`` the text goes into the XML as given (even when it is not a valid
        URL-encoded key); such entries cannot be fetched.
        """
        items = keys.items() if isinstance(keys, dict) else [(k, b"x") for k in keys]
        for key, content in items:
            if raw:
                self._injected_raw.append(key)
            else:
                self._injected[key] = content

    def pagination(self, mode: Literal["missing_token", "repeat_token"] | None) -> None:
        self.pagination_mode = mode

    def redirect(
        self, status: int, code: str | None = None, location: str | None = None
    ) -> None:
        """Every listing answers this redirect (a 301 carries ``code`` in the body)."""
        self._redirect = {"status": status, "code": code, "location": location}

    # -- request handling -------------------------------------------------

    def _violate(self, text: str) -> None:
        self.violations.append(text)

    def _classify(self, raw_path: str, raw_query: str) -> tuple[str, str | None, bool]:
        """Return (operation, decoded key for GetObject, bucket_ok)."""
        try:
            if self.addressing == "virtual":
                rest = raw_path[1:] if raw_path.startswith("/") else raw_path
                bucket_ok = True
            else:
                head = "/" + urllib.parse.quote(self.bucket, safe="-_.~")
                bucket_ok = raw_path == head or raw_path.startswith(head + "/")
                if bucket_ok:
                    rest = raw_path[len(head) :]
                    rest = rest[1:] if rest.startswith("/") else rest
                else:
                    rest = ""
            names = {
                urllib.parse.unquote_plus(p.partition("=")[0])
                for p in raw_query.split("&")
                if p
            }
            if rest == "":
                if "list-type" in names:
                    return "ListObjectsV2", None, bucket_ok
                return "other", None, bucket_ok
            if raw_query:
                return "other", None, bucket_ok
            return "GetObject", urllib.parse.unquote(rest, errors="strict"), bucket_ok
        except (UnicodeDecodeError, ValueError):
            return "other", None, True

    def _handle(self, request: httpx.Request) -> httpx.Response:
        headers = {k.lower(): v for k, v in request.headers.items()}
        self.requests.append(Req(request.method, str(request.url), headers))
        raw = request.url.raw_path.decode("ascii")
        raw_path, _, raw_query = raw.partition("?")

        if request.url.host.lower() != self.hostname:
            self.operations.append("other")
            self._violate(f"request to unexpected host {request.url.host}")
            return self._error(599, "UnexpectedHost", {})
        if request.method != "GET":
            self.operations.append("other")
            return self._error(405, "MethodNotAllowed", {})

        op, key, bucket_ok = self._classify(raw_path, raw_query)
        self.operations.append(op)

        net = self._network
        if net is not None and (net["left"] is None or net["left"] > 0):
            if net["left"] is not None:
                net["left"] -= 1
            if net["kind"] == "read_timeout":
                raise httpx.ReadTimeout("synthetic read timeout", request=request)
            raise httpx.ConnectError("synthetic connect error", request=request)

        thr = self._throttle
        if thr is not None and thr["left"] > 0 and thr["op"] in (None, op):
            thr["left"] -= 1
            extra = {}
            if thr["retry_after"] is not None:
                extra["Retry-After"] = str(thr["retry_after"])
            return self._error(thr["status"], thr["code"], headers, extra)

        if op == "other":
            if raw_query:
                self._violate(f"unsupported request: ?{raw_query}")
            return self._error(400, "InvalidRequest", headers)

        if op == "ListObjectsV2":
            for part in raw_query.split("&"):
                name = urllib.parse.unquote_plus(part.partition("=")[0])
                if name not in _ALLOWED_LIST_PARAMS:
                    self._violate(f"listing with unexpected parameter {name!r}")

        bad = self._check_auth(raw_path, raw_query, headers)
        if bad is not None:
            code, why = bad
            self.auth_failures.append(why)
            return self._error(
                403, code, headers, raw_path=raw_path, raw_query=raw_query
            )

        if op == "ListObjectsV2" and self._redirect is not None:
            red = self._redirect
            extra = {"Location": red["location"]} if red["location"] else {}
            return self._error(
                red["status"], red["code"] or "TemporaryRedirect", headers, extra
            )

        if not bucket_ok:
            return self._error(404, "NoSuchBucket", headers)

        for rule in self._error_rules:
            if rule["op"] != op or (rule["key"] is not None and rule["key"] != key):
                continue
            if rule["left"] is not None:
                if rule["left"] <= 0:
                    continue
                rule["left"] -= 1
            return self._error(
                rule["status"],
                rule["code"],
                headers,
                raw_path=raw_path,
                raw_query=raw_query,
            )

        if op == "ListObjectsV2":
            return self._list(raw_query, headers)
        return self._get(key or "", headers)

    # -- auth ---------------------------------------------------------------

    def _check_auth(
        self, raw_path: str, raw_query: str, headers: dict[str, str]
    ) -> tuple[str, str] | None:
        m = _AUTH_RE.match(headers.get("authorization", ""))
        if not m:
            return "SignatureDoesNotMatch", "malformed Authorization header"
        if m.group("key") != self.access_key_id:
            return "InvalidAccessKeyId", "access key id differs"
        amz_date = headers.get("x-amz-date", "")
        if not _AMZ_DATE_RE.match(amz_date) or amz_date[:8] != m.group("date"):
            return (
                "SignatureDoesNotMatch",
                "x-amz-date missing or not the credential day",
            )
        if m.group("region") != self.region:
            return "SignatureDoesNotMatch", "credential region differs"
        expected = ["host", "x-amz-content-sha256", "x-amz-date"]
        if self.session_token:
            expected.append("x-amz-security-token")
        if (
            "range" in headers
        ):  # an extra header the client sends must be signed (rev. 5)
            expected.append("range")
        expected.sort()
        if m.group("signed") != ";".join(expected):
            return "SignatureDoesNotMatch", f"SignedHeaders is {m.group('signed')}"
        if headers.get("x-amz-content-sha256") != EMPTY_SHA256:
            return (
                "SignatureDoesNotMatch",
                "x-amz-content-sha256 is not the empty body hash",
            )
        if self.session_token:
            if headers.get("x-amz-security-token") != self.session_token:
                return "SignatureDoesNotMatch", "session token missing or different"
        elif "x-amz-security-token" in headers:
            return "SignatureDoesNotMatch", "session token sent without a session"
        if headers.get("host") != self.host_header:
            return "SignatureDoesNotMatch", "Host header differs"
        if self.secret_access_key is not None:
            cr = canonical_request(
                "GET", raw_path, raw_query, headers, expected, EMPTY_SHA256
            )
            want = compute_signature(self.secret_access_key, self.region, amz_date, cr)
            if not hmac.compare_digest(want, m.group("sig")):
                return (
                    "SignatureDoesNotMatch",
                    "signature differs from the recomputed one",
                )
        return None

    # -- responses ----------------------------------------------------------

    def _error(
        self,
        status: int,
        code: str,
        req_headers: dict[str, str],
        extra: dict[str, str] | None = None,
        *,
        raw_path: str = "/",
        raw_query: str = "",
    ) -> httpx.Response:
        body = [
            '<?xml version="1.0" encoding="UTF-8"?><Error>',
            f"<Code>{escape(code)}</Code><Message>{escape(code)}</Message>",
            f"<RequestId>REQ{len(self.requests):06d}</RequestId>",
        ]
        if status == 301:
            body.append(f"<Endpoint>other.{self.hostname}</Endpoint>")
        if self.error_body_echo:
            m = _AUTH_RE.match(req_headers.get("authorization", ""))
            key_id = m.group("key") if m else self.access_key_id
            signed = m.group("signed").split(";") if m else []
            cr = canonical_request(
                "GET", raw_path, raw_query, req_headers, signed, EMPTY_SHA256
            )
            sts = "AWS4-HMAC-SHA256\n" + req_headers.get("x-amz-date", "") + "\n" + cr
            body.append(f"<AWSAccessKeyId>{escape(key_id)}</AWSAccessKeyId>")
            body.append(f"<StringToSign>{escape(sts)}</StringToSign>")
            body.append(f"<CanonicalRequest>{escape(cr)}</CanonicalRequest>")
            if m:
                body.append(f"<SignatureProvided>{m.group('sig')}</SignatureProvided>")
        body.append("</Error>")
        data = "".join(body).encode("utf-8")
        out = {"Content-Type": "application/xml", "Server": self.server_header}
        out.update(extra or {})
        return httpx.Response(status, headers=out, stream=_CountingStream(data, []))

    def _entries(self, prefix: str) -> list[_Entry]:
        entries = [
            _Entry(k, self._listed_size(k), False)
            for k in sorted(self.objects, key=lambda s: s.encode("utf-8"))
            if k.startswith(prefix)
        ]
        entries += [_Entry(k, len(v), False) for k, v in self._injected.items()]
        entries += [_Entry(k, 1, True) for k in self._injected_raw]
        return entries

    def _listed_size(self, key: str) -> int | None:
        if key in self._lies:
            return self._lies[key][0]
        return len(self.objects[key])

    def _list(self, raw_query: str, headers: dict[str, str]) -> httpx.Response:
        params = dict(urllib.parse.parse_qsl(raw_query, keep_blank_values=True))
        prefix = params.get("prefix", "")
        try:
            wanted = int(params.get("max-keys", "1000"))
        except ValueError:
            return self._error(400, "InvalidArgument", headers)
        maxkeys = max(1, min(wanted, self.page_size, 1000))
        offset = 0
        if "continuation-token" in params:
            try:
                offset = _offset_of(params["continuation-token"])
            except (ValueError, base64.binascii.Error):
                return self._error(400, "InvalidArgument", headers)
        entries = self._entries(prefix)
        page = entries[offset : offset + maxkeys]
        truncated = offset + maxkeys < len(entries)
        token_out = _token_for(offset + maxkeys) if truncated else None
        if self.pagination_mode == "missing_token":
            truncated, token_out = True, None
        elif self.pagination_mode == "repeat_token":
            truncated, token_out = True, _token_for(maxkeys)
        encoded = self.encoding_type == "url" and params.get("encoding-type") == "url"
        body = self._listing_xml(page, prefix, maxkeys, truncated, token_out, encoded)
        sink: list[int] = []
        return httpx.Response(
            200,
            headers={
                "Content-Type": "application/xml",
                "Server": self.server_header,
                "x-amz-request-id": f"REQ{len(self.requests):06d}",
            },
            stream=_CountingStream(body, sink),
        )

    def _listing_xml(
        self,
        page: list[_Entry],
        prefix: str,
        maxkeys: int,
        truncated: bool,
        token_out: str | None,
        encoded: bool,
    ) -> bytes:
        if self.malformed_xml:
            return (
                b'<?xml version="1.0"?><ListBucketResult><Name>x</Name><Contents><Key>a'
            )
        ns = {
            "aws": f' xmlns="{AWS_NS}"',
            "other": ' xmlns="http://example.invalid/ns"',
            None: "",
        }[self.namespace]

        def text(value: str) -> str:
            return (
                escape(urllib.parse.quote_plus(value, safe="/"))
                if encoded
                else escape(value)
            )

        out = ['<?xml version="1.0" encoding="UTF-8"?>']
        if self.doctype_entity:
            out.append('<!DOCTYPE ListBucketResult [<!ENTITY boom "boom">]>')
        out.append(f"<ListBucketResult{ns}>")
        if self.oversized_listing:
            out.append("<!--" + "x" * (LISTING_LIMIT_BYTES + 4096) + "-->")
        out.append(f"<Name>{escape(self.bucket)}</Name><Prefix>{text(prefix)}</Prefix>")
        out.append(f"<KeyCount>{len(page)}</KeyCount><MaxKeys>{maxkeys}</MaxKeys>")
        if encoded:
            out.append("<EncodingType>url</EncodingType>")
        out.append(f"<IsTruncated>{'true' if truncated else 'false'}</IsTruncated>")
        if token_out:
            out.append(
                f"<NextContinuationToken>{escape(token_out)}</NextContinuationToken>"
            )
        if self.doctype_entity:
            out.append("<Contents><Key>&boom;</Key><Size>1</Size></Contents>")
        for e in page:
            key_xml = escape(e.key) if e.raw else text(e.key)
            size_xml = "" if e.size is None else f"<Size>{e.size}</Size>"
            out.append(
                f"<Contents><Key>{key_xml}</Key>"
                f"<LastModified>2026-11-20T12:00:00.000Z</LastModified>"
                f'<ETag>"synthetic"</ETag>{size_xml}'
                f"<StorageClass>STANDARD</StorageClass></Contents>"
            )
        out.append("</ListBucketResult>")
        return "".join(out).encode("utf-8")

    def _get(self, key: str, headers: dict[str, str]) -> httpx.Response:
        self.fetched.append(key)
        if key in self.objects:
            data = self.objects[key]
        elif key in self._injected:
            data = self._injected[key]
        else:
            return self._error(404, "NoSuchKey", headers)
        if key in self._lies:
            actual = self._lies[key][1]
            data = (data + b"\0" * actual)[:actual]
        sink: list[int] = []
        out = {
            "Content-Type": "application/octet-stream",
            "Server": self.server_header,
            "Content-Length": str(self._content_lengths.get(key, len(data))),
        }
        self._delivered_sinks.setdefault(key, []).append(sink)
        return httpx.Response(200, headers=out, stream=_CountingStream(data, sink))

    def delivered(self, key: str) -> int:
        """Bytes the client really pulled for ``key`` (summed over the requests for it)."""
        return sum(sum(s) for s in self._delivered_sinks.get(key, []))
