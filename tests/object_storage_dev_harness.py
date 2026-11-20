"""Dev harness of the ``object_storage`` common-layer tests (epic #2306, task 2306.2).

Not a test file. Shared by ``tests/test_object_storage_connector.py``,
``tests/test_object_storage_limits.py``, ``tests/test_object_storage_coverage.py`` and
``tests/test_object_storage_tier.py`` (cases ``D2306-22`` .. ``D2306-80`` of
``docs/desenho/2306.md``).

It drives the connector only through the seams of section 13 (``_transport``, ``_sleep``,
``_now``), the driver registry and ``connectors.url_guard``. The QA helpers
(``tests/s3_fake.py``, ``tests/object_storage_toy_driver.py``) are used as they are; the two
subclasses below add hostile behaviour the D cases need and the QA simulator does not offer
(reported to the PM as a gap for the QA): a listing body replaced as a whole (D-42), a
server that returns more entries than ``max-keys`` (D-48) and a toy provider that lies about
the size (D-68).

No network, no real credential: credentials are generated at run time with greppable markers
(``SYNTHAK``/``SYNTHSK``/``SYNTHST``), and the synthetic personal data is the corpus already used
by the acceptance tests.
"""

from __future__ import annotations

import json
import re
import tempfile
import urllib.parse
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Literal, NamedTuple

import httpx

from connectors import object_storage_driver
from connectors.object_storage_driver import ListPage, ObjectEntry
from tests.object_storage_toy_driver import (
    TOY_HOST,
    TOY_TOKEN_ENV,
    ToyDriver,
    ToyStore,
    new_toy_token,
)
from tests.s3_fake import (
    EVIL_HOST,
    GOOD_IP,
    Creds,
    FakeClock,
    FakeDB,
    FakeS3,
    RegexScanner,
    install_fake_dns,
    new_credentials,
)

BUCKET = "databoar-sintetico"
REGION = "sa-east-1"
AWS_HOST = f"{BUCKET}.s3.{REGION}.amazonaws.com"
MINIO_HOST = "minio.lab.example"
MINIO_ENDPOINT = f"https://{MINIO_HOST}:9000"
TARGET_NAME = "bucket-sintetico"
TOY_CONTAINER = "caixa-sintetica"

ENV_AK = "DATA_BOAR_S3_ACCESS_KEY_ID"
ENV_SK = "DATA_BOAR_S3_SECRET_ACCESS_KEY"
ENV_ST = "DATA_BOAR_S3_SESSION_TOKEN"

CPF_TXT = b"Cliente cadastrado: CPF 123.456.789-09, ficha 77.\n"
PLAIN_TXT = b"Ata da reuniao: revisar o cronograma do galpao.\n"
EMAIL_CSV = b"nome,contato\nPessoa Teste,pessoa.teste@exemplo.com\n"
MIB = 1024 * 1024


def corpus() -> dict[str, bytes]:
    """Same synthetic bucket as A-1: only ``corpus/`` is in scope."""
    return {
        "corpus/a.txt": CPF_TXT,
        "corpus/b.txt": PLAIN_TXT,
        "corpus/sub/c.csv": EMAIL_CSV,
        "outro/d.txt": CPF_TXT,
    }


# Revision 6 (R6-6): the generic keys of the coverage block of an inventory row.
COVERAGE_KEYS = frozenset(
    {
        "coverage",
        "listing_complete",
        "objects_listed",
        "objects_scanned",
        "objects_not_scanned",
        "bytes_not_scanned",
        "objects_unknown_size",
        "not_scanned_by_reason",
        "limits_disabled",
    }
)

EXPECTED_PATHS = {f"s3://{BUCKET}/corpus/a.txt", f"s3://{BUCKET}/corpus/sub/c.csv"}


def connector_module() -> Any:
    import connectors.object_storage_connector as mod

    return mod


def s3_target(**overrides: Any) -> dict[str, Any]:
    target: dict[str, Any] = {
        "name": TARGET_NAME,
        "type": "object_storage",
        "driver": "s3",
        "bucket": BUCKET,
        "region": REGION,
        "prefix": "corpus/",
        "auth": {
            "access_key_id_from_env": ENV_AK,
            "secret_access_key_from_env": ENV_SK,
            "session_token_from_env": ENV_ST,
        },
    }
    target.update(overrides)
    return target


def compat_target(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "driver": "s3_compatible",
        "endpoint_url": MINIO_ENDPOINT,
        "region": "us-east-1",
        "allow_private_networks": True,
    }
    base.update(overrides)
    return s3_target(**base)


def toy_target(**overrides: Any) -> dict[str, Any]:
    target: dict[str, Any] = {
        "name": TARGET_NAME,
        "type": "object_storage",
        "driver": "toy",
        "host": TOY_HOST,
        "container": TOY_CONTAINER,
        "prefix": "corpus/",
        "auth": {"token_from_env": TOY_TOKEN_ENV},
    }
    target.update(overrides)
    return target


class Outcome(NamedTuple):
    db: FakeDB
    clock: FakeClock
    connector: Any


class SpyScanner(RegexScanner):
    """``RegexScanner`` that records every ``scan_file_content`` call."""

    def __init__(self, hook: Callable[[str, Any], None] | None = None) -> None:
        self.calls: list[tuple[str, Any]] = []
        self._hook = hook

    def scan_file_content(self, content: str, file_path: Any) -> dict[str, Any] | None:
        self.calls.append((content, file_path))
        if self._hook is not None:
            self._hook(content, file_path)
        return super().scan_file_content(content, file_path)


class HostileFakeS3(FakeS3):
    """``FakeS3`` with two hostile behaviours the QA simulator does not have.

    ``listing_body``: every listing answers exactly these bytes (D-42).
    ``overshoot``: the listing returns ``overshoot`` entries more than the ``max-keys`` the
    client asked for (D-48); the request itself (and its signature) is unchanged.
    """

    listing_body: bytes | None = None
    overshoot: int = 0

    def _listing_xml(self, *args: Any, **kwargs: Any) -> bytes:
        if self.listing_body is not None:
            return self.listing_body
        return super()._listing_xml(*args, **kwargs)

    def _list(self, raw_query: str, headers: dict[str, str]) -> httpx.Response:
        if self.overshoot:
            raw_query = re.sub(
                r"(^|&)max-keys=(\d+)",
                lambda m: f"{m.group(1)}max-keys={int(m.group(2)) + self.overshoot}",
                raw_query,
            )
        return super()._list(raw_query, headers)


class LyingToyStore(ToyStore):
    """``ToyStore`` whose listing declares ``declared[key]`` bytes for some blobs (D-68)."""

    def __init__(self, *args: Any, declared: dict[str, int], **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.declared = dict(declared)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        response = super()._handle(request)
        path = request.url.raw_path.decode("ascii").partition("?")[0]
        if response.status_code != 200 or not path.endswith("/list"):
            return response
        doc = json.loads(response.content)
        for item in doc["items"]:
            if item["name"] in self.declared:
                item["bytes"] = self.declared[item["name"]]
        return httpx.Response(200, json=doc)


class NoSizeToyDriver(ToyDriver):
    """Toy driver whose listing reports no size for valid keys (R6-2, D-86)."""

    def parse_list(self, body: bytes) -> ListPage:
        page = super().parse_list(body)
        entries = [
            ObjectEntry(e.key, None) if e.key is not None else e for e in page.entries
        ]
        return ListPage(entries, page.next_token, page.truncated)


class _CountingBody(httpx.SyncByteStream):
    def __init__(self, data: bytes, sink: list[int]) -> None:
        self._data = data
        self._sink = sink

    def __iter__(self) -> Iterator[bytes]:
        for i in range(0, len(self._data), 16):
            chunk = self._data[i : i + 16]
            self._sink.append(len(chunk))
            yield chunk


class StreamingToyStore(ToyStore):
    """``ToyStore`` whose blobs stream in 16-byte chunks, count the bytes the client pulls
    and may declare another ``Content-Length`` (R6-2, D-86)."""

    def __init__(
        self, *args: Any, content_lengths: dict[str, int] | None = None, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.content_lengths = dict(content_lengths or {})
        self._sinks: dict[str, list[int]] = {}

    def _handle(self, request: httpx.Request) -> httpx.Response:
        response = super()._handle(request)
        path = request.url.raw_path.decode("ascii").partition("?")[0]
        marker = f"/v1/{self.container}/blob/"
        if response.status_code != 200 or not path.startswith(marker):
            return response
        key = urllib.parse.unquote(path[len(marker) :], errors="strict")
        data = self.objects[key]
        sink = self._sinks.setdefault(key, [])
        length = self.content_lengths.get(key, len(data))
        return httpx.Response(
            200,
            headers={"Content-Length": str(length)},
            stream=_CountingBody(data, sink),
        )

    def delivered(self, key: str) -> int:
        return sum(self._sinks.get(key, []))


class Harness:
    """Credentials in the environment, a fixed DNS table and the connector runner."""

    def __init__(self, monkeypatch: Any, *, with_token: bool = True) -> None:
        self.mp = monkeypatch
        self.creds: Creds = new_credentials(with_token=with_token)
        monkeypatch.setenv(ENV_AK, self.creds.access_key_id)
        monkeypatch.setenv(ENV_SK, self.creds.secret_access_key)
        monkeypatch.setenv(ENV_ST, self.creds.session_token or "")
        self.toy_token = new_toy_token()
        monkeypatch.setenv(TOY_TOKEN_ENV, self.toy_token)
        self.ips: dict[str, list[str]] = {EVIL_HOST: [GOOD_IP]}
        install_fake_dns(monkeypatch, self.ips)
        self.fakes: list[FakeS3] = []
        self.mkdtemp_calls: list[str] = []

    def dns(self, host: str, ip: str | None) -> None:
        if ip is None:
            self.ips.pop(host.lower(), None)
        else:
            self.ips[host.lower()] = [ip]
        install_fake_dns(self.mp, self.ips)

    def s3(
        self,
        objects: dict[str, bytes] | None = None,
        *,
        host: str = AWS_HOST,
        addressing: Literal["virtual", "path"] = "virtual",
        region: str = REGION,
        ip: str | None = GOOD_IP,
        cls: type[FakeS3] = FakeS3,
        **kw: Any,
    ) -> Any:
        fake = cls(
            BUCKET,
            corpus() if objects is None else objects,
            host,
            addressing,
            region,
            access_key_id=self.creds.access_key_id,
            session_token=self.creds.session_token,
            secret_access_key=self.creds.secret_access_key,
            **kw,
        )
        self.dns(fake.hostname, ip)
        self.fakes.append(fake)
        return fake

    def minio(self, objects: dict[str, bytes] | None = None, **kw: Any) -> Any:
        kw.setdefault("ip", "10.0.0.5")
        return self.s3(
            objects,
            host=f"{MINIO_HOST}:9000",
            addressing="path",
            region="us-east-1",
            **kw,
        )

    def toy(
        self,
        objects: dict[str, bytes],
        *,
        driver: type = ToyDriver,
        store: type[ToyStore] = ToyStore,
        **kw: Any,
    ) -> Any:
        """A toy store and the toy driver in the registry (restored by ``monkeypatch``)."""
        self.mp.setitem(object_storage_driver._REGISTRY, "toy", driver)
        self.dns(TOY_HOST, GOOD_IP)
        return store(TOY_CONTAINER, objects, self.toy_token, **kw)

    def spy_mkdtemp(self) -> list[str]:
        """Record every ``tempfile.mkdtemp`` directory the connector creates."""
        real = tempfile.mkdtemp

        def spy(*args: Any, **kwargs: Any) -> str:
            made = real(*args, **kwargs)
            self.mkdtemp_calls.append(made)
            return made

        self.mp.setattr(tempfile, "mkdtemp", spy)
        return self.mkdtemp_calls

    def run(
        self,
        transport: Any,
        target: dict[str, Any],
        *,
        db: FakeDB | None = None,
        scanner: Any = None,
        clock: FakeClock | None = None,
        **kw: Any,
    ) -> Outcome:
        """Build the connector with the section 13 seams and run it once.

        ``transport=None`` leaves out ``_transport`` (the connector then builds the pinned
        client of ``connectors.url_guard``).
        """
        db = db if db is not None else FakeDB()
        clock = clock if clock is not None else FakeClock()
        seams: dict[str, Any] = {"_sleep": clock.sleep, "_now": clock.now}
        if transport is not None:
            seams["_transport"] = transport
        cls = connector_module().ObjectStorageConnector
        conn = cls(
            target_config=target,
            scanner=scanner if scanner is not None else RegexScanner(),
            db_manager=db,
            **kw,
            **seams,
        )
        conn.run()
        return Outcome(db, clock, conn)

    def control_scan(self) -> Outcome:
        """Positive control: a valid AWS scan of the corpus makes requests and finds A-1."""
        fake = self.s3()
        out = self.run(fake.transport, s3_target())
        assert fake.operations, "control scan made no request"
        assert {f["path"] for f in out.db.findings} == EXPECTED_PATHS
        return out


def capture_pinned_client(monkeypatch: Any, transport: Any) -> list[dict[str, Any]]:
    """Replace ``url_guard.build_pinned_httpx_client``; record its kwargs (D-25, D-29).

    The returned client runs on ``transport`` (the simulator), so no socket is opened.
    """
    import connectors.url_guard as url_guard

    seen: list[dict[str, Any]] = []

    def build(**kwargs: Any) -> httpx.Client:
        seen.append(kwargs)
        return httpx.Client(transport=transport, follow_redirects=False)

    monkeypatch.setattr(url_guard, "build_pinned_httpx_client", build)
    return seen


def paths(db: FakeDB) -> set[str]:
    return {f["path"] for f in db.findings}


def ops(fake: Any, name: str) -> int:
    return sum(1 for op in fake.operations if op == name)


def skipped_detail(db: FakeDB) -> str:
    details = db.details("skipped")
    assert len(details) == 1, db.failures
    return details[0]


def executive(db: FakeDB) -> dict[str, Any]:
    raw = db.inventory_json()
    assert "executive" in raw, raw
    return raw["executive"]


def exists(path: str) -> bool:
    return Path(path).exists()
