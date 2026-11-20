"""Dev tests of task 2306.1: httpx premises, SigV4 wrapper and credential isolation.

Source: ``docs/desenho/2306.md``, section 5 (option B of P-1: ``botocore.auth.S3SigV4Auth``
only signs) and the TDD specification:

- D2306-0a .. D2306-0c: premises about httpx and the pinned client, against a local HTTP
  server on ``127.0.0.1``. They do not use project code under test (paths are built with the
  independent encoder of ``tests/s3_fake.py``), so they pass before the implementation.
- D2306-0e, D2306-0f: no implicit AWS credential chain; the DEBUG log of ``botocore.auth``
  never reaches a handler.
- D2306-9 .. D2306-14: ``uri_encode`` and ``sign_get``.

No external network. Credentials are synthetic and built at run time
(``tests.s3_fake.new_credentials``). The signature is checked against the independent
SigV4 oracle of ``tests/s3_fake.py`` (written from the AWS specification).
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import sys
import threading
import traceback
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import httpx
import pytest

from connectors import s3_sigv4
from connectors.object_storage_driver import ResolvedCredentials
from connectors.object_storage_s3 import S3Driver
from connectors.s3_sigv4 import (
    BOTOCORE_AUTH_LOG_FILTER,
    BOTOCORE_AUTH_LOGGER,
    sign_get,
    uri_encode,
)
from connectors.url_guard import build_pinned_httpx_client
from tests import s3_fake
from tests.s3_fake import FakeS3, canonical_request, compute_signature, new_credentials

BUCKET = "databoar-sintetico"
REGION = "sa-east-1"
AWS_HOST = f"{BUCKET}.s3.{REGION}.amazonaws.com"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
T0 = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)

_AUTH_RE = re.compile(
    r"^AWS4-HMAC-SHA256 Credential=(?P<key>[^/]+)/(?P<scope>\d{8}/[^/]+/s3/aws4_request),"
    r"\s*SignedHeaders=(?P<signed>[a-z0-9;-]+),\s*Signature=(?P<sig>[0-9a-f]{64})$"
)

# 40 keys with the characters the design lists (space, &, +, %, ~, [, ], #, ?, =, accents,
# //, emoji) and other reserved or non-ASCII characters.
_SPECIALS = [
    " ",
    "&",
    "+",
    "%",
    "~",
    "[",
    "]",
    "#",
    "?",
    "=",
    "ç",
    "ã",
    "é",
    "日本",
    "😀",
    "//",
    "%20",
    "%2F",
    "+%2B",
    "'",
    '"',
    "!",
    "$",
    "(",
    ")",
    "*",
    ",",
    ";",
    ":",
    "@",
    "^",
    "`",
    "{",
    "}",
    "|",
    "\\",
    "<",
    ">",
    "€",
    "ñ",
]
KEYS_40 = [f"corpus/k{i}{s}x.txt" for i, s in enumerate(_SPECIALS)]


# ----------------------------------------------------------------------------
# Local HTTP server that records the raw request target and headers
# ----------------------------------------------------------------------------


class _Recorder(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        server: Any = self.server
        server.seen.append((self.path, {k.lower(): v for k, v in self.headers.items()}))
        body = b"ok"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


@pytest.fixture
def local_server() -> Iterator[Any]:
    srv: Any = ThreadingHTTPServer(("127.0.0.1", 0), _Recorder)
    srv.seen = []
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield srv
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(5)


def _send_raw(server: Any, target: str) -> tuple[str, dict[str, str]]:
    port = server.server_address[1]
    # PinnedIPTransport is not a context manager: close the client explicitly.
    client = build_pinned_httpx_client(
        host_to_ips={"fake.test": ["127.0.0.1"]}, follow_redirects=False
    )
    try:
        resp = client.get(f"http://fake.test:{port}{target}")
        assert resp.status_code == 200
    finally:
        client.close()
    assert server.seen, "server saw no request"
    return server.seen.pop()


# ----------------------------------------------------------------------------
# Premises (pass before the implementation)
# ----------------------------------------------------------------------------


def test_D2306_0a_httpx_envia_caminho_e_query_byte_a_byte(local_server: Any) -> None:
    assert len(KEYS_40) == 40
    for key in KEYS_40:
        path = f"/{BUCKET}/" + s3_fake.uri_encode(key, keep_slash=True)
        query = "list-type=2&prefix=" + s3_fake.uri_encode(key, keep_slash=False)
        target = f"{path}?{query}"
        seen_target, _headers = _send_raw(local_server, target)
        assert seen_target == target, key


def test_D2306_0b_httpx_normaliza_so_segmento_ponto_ou_ponto_ponto(
    local_server: Any,
) -> None:
    changed = [
        f"/{BUCKET}/corpus/./x.txt",
        f"/{BUCKET}/corpus/../x.txt",
        f"/{BUCKET}/./x.txt",
        f"/{BUCKET}/corpus/..",
    ]
    for target in changed:
        seen_target, _ = _send_raw(local_server, target)
        assert seen_target != target, target
    kept = [
        f"/{BUCKET}/corpus/a%01.txt",
        f"/{BUCKET}/corpus/a%09.txt",
        f"/{BUCKET}/corpus/a%0A.txt",
        f"/{BUCKET}/corpus/a%7F.txt",
        f"/{BUCKET}/corpus/.hidden",
        f"/{BUCKET}/corpus/..x",
        f"/{BUCKET}/corpus/x.",
        f"/{BUCKET}/corpus/.oculto.txt",
    ]
    for target in kept:
        seen_target, _ = _send_raw(local_server, target)
        assert seen_target == target, target


def test_D2306_0c_host_header_traz_a_porta_fora_de_80_e_443(local_server: Any) -> None:
    port = local_server.server_address[1]
    assert port not in (80, 443)
    _target, headers = _send_raw(local_server, f"/{BUCKET}?list-type=2")
    assert headers["host"] == f"fake.test:{port}"


# ----------------------------------------------------------------------------
# D2306-0e: no implicit credential chain, no socket
# ----------------------------------------------------------------------------

_AUDIT: dict[str, Any] = {"on": False, "opened": [], "connects": []}
_AUDIT_INSTALLED: list[bool] = []


def _audit_hook(event: str, args: tuple[Any, ...]) -> None:
    if not _AUDIT["on"]:
        return
    if event == "open" and args:
        _AUDIT["opened"].append(str(args[0]))
    elif event == "socket.connect" and len(args) > 1:
        _AUDIT["connects"].append(str(args[1]))


def _arm_audit() -> None:
    # sys.addaudithook cannot be removed: install once, switch with a flag.
    if not _AUDIT_INSTALLED:
        sys.addaudithook(_audit_hook)
        _AUDIT_INSTALLED.append(True)
    _AUDIT["opened"].clear()
    _AUDIT["connects"].clear()
    _AUDIT["on"] = True


def _s3_cfg(**extra: Any) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "name": "bucket-sintetico",
        "type": "object_storage",
        "driver": "s3",
        "bucket": BUCKET,
        "region": REGION,
    }
    cfg.update(extra)
    return cfg


def test_D2306_0e_nenhuma_cadeia_de_credencial_implicita_nem_socket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    good = new_credentials(with_token=True)
    decoy = new_credentials(with_token=True)
    decoy_ini = (
        "[default]\n"
        f"aws_access_key_id = {decoy.access_key_id}\n"
        f"aws_secret_access_key = {decoy.secret_access_key}\n"
        f"aws_session_token = {decoy.session_token}\n"
    )
    home = tmp_path / "home"
    (home / ".aws").mkdir(parents=True)
    decoys = [
        tmp_path / "decoy-credentials",
        tmp_path / "decoy-config",
        home / ".aws" / "credentials",
        home / ".aws" / "config",
    ]
    for path in decoys:
        path.write_text(decoy_ini, encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", decoy.access_key_id)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", decoy.secret_access_key)
    monkeypatch.setenv("AWS_SESSION_TOKEN", str(decoy.session_token))
    monkeypatch.setenv("AWS_PROFILE", "default")
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(decoys[0]))
    monkeypatch.setenv("AWS_CONFIG_FILE", str(decoys[1]))
    monkeypatch.setenv("DATA_BOAR_S3_ACCESS_KEY_ID", good.access_key_id)
    monkeypatch.setenv("DATA_BOAR_S3_SECRET_ACCESS_KEY", good.secret_access_key)
    monkeypatch.setenv("DATA_BOAR_S3_SESSION_TOKEN", str(good.session_token))

    objects = {"corpus/a.txt": b"alpha", "corpus/sub/b c.csv": b"beta"}
    fake = FakeS3(
        BUCKET,
        objects,
        host=AWS_HOST,
        region=REGION,
        access_key_id=good.access_key_id,
        session_token=good.session_token,
        secret_access_key=good.secret_access_key,
    )
    creds = ResolvedCredentials(
        {
            "access_key_id_from_env": os.environ["DATA_BOAR_S3_ACCESS_KEY_ID"],
            "secret_access_key_from_env": os.environ["DATA_BOAR_S3_SECRET_ACCESS_KEY"],
            "session_token_from_env": os.environ["DATA_BOAR_S3_SESSION_TOKEN"],
        }
    )
    driver = S3Driver()
    _arm_audit()
    try:
        # sign_get alone, then a full list + get through the simulator.
        sign_get(
            host_header=AWS_HOST,
            canonical_uri="/",
            query=[("list-type", "2")],
            region=REGION,
            access_key_id=creds["access_key_id_from_env"],
            secret_access_key=creds["secret_access_key_from_env"],
            session_token=creds["session_token_from_env"],
            now=T0,
        )
        settings = driver.settings(_s3_cfg())
        with httpx.Client(transport=fake.transport, follow_redirects=False) as client:
            prep = driver.list_request(settings, creds, "corpus/", None, 1000, T0)
            resp = client.get(prep.url, headers=prep.headers)
            assert resp.status_code == 200, resp.text
            page = driver.parse_list(resp.content)
            assert sorted(e.key for e in page.entries) == sorted(objects)
            for entry in page.entries:
                prep = driver.get_request(settings, creds, entry.key, T0)
                got = client.get(prep.url, headers=prep.headers)
                assert got.status_code == 200, entry.key
                assert got.content == objects[entry.key]
    finally:
        _AUDIT["on"] = False

    decoy_paths = {str(p) for p in decoys}
    opened_decoys = [p for p in _AUDIT["opened"] if p in decoy_paths]
    assert opened_decoys == []
    assert _AUDIT["connects"] == []
    assert fake.auth_failures == []
    assert fake.violations == []
    assert len(fake.requests) == 1 + len(objects)
    for req in fake.requests:
        match = _AUTH_RE.match(req.headers["authorization"])
        assert match is not None
        assert match.group("key") == good.access_key_id
        assert req.headers["x-amz-security-token"] == good.session_token
        flat = " ".join(f"{k}:{v}" for k, v in req.headers.items()) + req.url
        for value in (
            decoy.access_key_id,
            decoy.secret_access_key,
            str(decoy.session_token),
        ):
            assert value not in flat


# ----------------------------------------------------------------------------
# D2306-0f: botocore.auth DEBUG never reaches a handler
# ----------------------------------------------------------------------------


def _sign_with_session(creds: s3_fake.Creds) -> tuple[str, dict[str, str]]:
    return sign_get(
        host_header=AWS_HOST,
        canonical_uri="/corpus/a.txt",
        query=[],
        region=REGION,
        access_key_id=creds.access_key_id,
        secret_access_key=creds.secret_access_key,
        session_token=creds.session_token,
        now=T0,
    )


def _signature_of(headers: dict[str, str]) -> str:
    lower = {k.lower(): v for k, v in headers.items()}
    match = _AUTH_RE.match(lower["authorization"])
    assert match is not None
    return match.group("sig")


def _leaks(records: list[logging.LogRecord], secrets_: list[str]) -> list[str]:
    found = []
    for rec in records:
        text = rec.getMessage() + (rec.exc_text or "")
        found.extend(s for s in secrets_ if s in text)
    return found


def test_D2306_0f_log_debug_do_botocore_auth_nunca_chega_a_um_handler(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    creds = new_credentials(with_token=True)
    caplog.set_level(logging.DEBUG)
    auth_logger = logging.getLogger(BOTOCORE_AUTH_LOGGER)
    levels_before = (
        logging.getLogger().level,
        logging.getLogger("botocore").level,
        auth_logger.level,
    )

    _query, headers = _sign_with_session(creds)
    signature = _signature_of(headers)
    watched = [creds.secret_access_key, str(creds.session_token), signature]

    assert [r for r in caplog.records if r.name.startswith(BOTOCORE_AUTH_LOGGER)] == []
    assert _leaks(caplog.records, watched) == []
    assert BOTOCORE_AUTH_LOG_FILTER in auth_logger.filters
    # The filter never changes any logger level.
    assert (
        logging.getLogger().level,
        logging.getLogger("botocore").level,
        auth_logger.level,
    ) == levels_before

    # Negative control: without the filter the same signing leaks into the log, which
    # proves the assertions above can fail.
    monkeypatch.setattr(s3_sigv4, "install_botocore_log_filter", lambda: None)
    auth_logger.removeFilter(BOTOCORE_AUTH_LOG_FILTER)
    try:
        caplog.clear()
        _query, headers = _sign_with_session(creds)
        unfiltered = [
            r for r in caplog.records if r.name.startswith(BOTOCORE_AUTH_LOGGER)
        ]
        assert unfiltered != []
        assert str(creds.session_token) in " ".join(r.getMessage() for r in unfiltered)
    finally:
        auth_logger.addFilter(BOTOCORE_AUTH_LOG_FILTER)


# ----------------------------------------------------------------------------
# D2306-9 .. D2306-14: uri_encode and sign_get
# ----------------------------------------------------------------------------


def test_D2306_9_uri_encode_segue_a_regra_da_aws() -> None:
    unreserved = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~"
    assert uri_encode(unreserved, keep_slash=False) == unreserved
    assert uri_encode(" ", keep_slash=False) == "%20"
    assert uri_encode("+", keep_slash=False) == "%2B"
    assert uri_encode("%", keep_slash=False) == "%25"
    assert uri_encode("é", keep_slash=False) == "%C3%A9"
    assert uri_encode("a/b", keep_slash=True) == "a/b"
    assert uri_encode("a/b", keep_slash=False) == "a%2Fb"
    assert uri_encode("😀", keep_slash=True) == "%F0%9F%98%80"
    # Same result as the independent encoder for every ASCII character and the keys.
    samples = [chr(c) for c in range(128)] + KEYS_40 + ["ação/日本//x"]
    for value in samples:
        for keep in (True, False):
            assert uri_encode(value, keep_slash=keep) == s3_fake.uri_encode(
                value, keep_slash=keep
            ), (value, keep)


def _sign(
    *,
    creds: s3_fake.Creds,
    query: list[tuple[str, str]] | None = None,
    canonical_uri: str = "/",
    host_header: str = AWS_HOST,
    region: str = REGION,
    now: datetime = T0,
) -> tuple[str, dict[str, str]]:
    raw_query, headers = sign_get(
        host_header=host_header,
        canonical_uri=canonical_uri,
        query=query if query is not None else [],
        region=region,
        access_key_id=creds.access_key_id,
        secret_access_key=creds.secret_access_key,
        session_token=creds.session_token,
        now=now,
    )
    return raw_query, {k.lower(): v for k, v in headers.items()}


def test_D2306_10_query_ordenada_pelo_nome_codificado_com_valor_vazio() -> None:
    creds = new_credentials(with_token=False)
    raw_query, _headers = _sign(
        creds=creds,
        query=[
            ("prefix", "corpus/a b+c"),
            ("max-keys", "10"),
            ("list-type", "2"),
            ("encoding-type", "url"),
            ("continuation-token", ""),
        ],
    )
    assert raw_query == (
        "continuation-token=&encoding-type=url&list-type=2&max-keys=10"
        "&prefix=corpus%2Fa%20b%2Bc"
    )


def test_D2306_11_signed_headers_exatos_com_e_sem_sessao() -> None:
    _q, headers = _sign(creds=new_credentials(with_token=False))
    match = _AUTH_RE.match(headers["authorization"])
    assert match is not None
    assert match.group("signed") == "host;x-amz-content-sha256;x-amz-date"
    assert "x-amz-security-token" not in headers

    with_token = new_credentials(with_token=True)
    _q, headers = _sign(creds=with_token)
    match = _AUTH_RE.match(headers["authorization"])
    assert match is not None
    assert match.group("signed") == (
        "host;x-amz-content-sha256;x-amz-date;x-amz-security-token"
    )
    assert headers["x-amz-security-token"] == with_token.session_token


def test_D2306_12_hash_do_corpo_e_o_do_corpo_vazio() -> None:
    for creds in (new_credentials(with_token=False), new_credentials()):
        _q, headers = _sign(creds=creds)
        assert headers["x-amz-content-sha256"] == EMPTY_SHA256


def test_D2306_13_relogio_injetado_define_data_escopo_e_assinatura() -> None:
    creds = new_credentials(with_token=True)
    query = [("list-type", "2"), ("prefix", "corpus/a b")]
    uri = "/" + uri_encode("corpus/ação+[1].txt", keep_slash=True)
    raw_query, headers = _sign(creds=creds, query=query, canonical_uri=uri)
    assert headers["x-amz-date"] == "20261120T120000Z"
    match = _AUTH_RE.match(headers["authorization"])
    assert match is not None
    assert match.group("key") == creds.access_key_id
    assert match.group("scope") == f"20261120/{REGION}/s3/aws4_request"

    # The signature is the one the independent SigV4 oracle computes.
    signed = match.group("signed").split(";")
    oracle_headers = dict(headers)
    oracle_headers["host"] = AWS_HOST
    cr = canonical_request("GET", uri, raw_query, oracle_headers, signed, EMPTY_SHA256)
    assert match.group("sig") == compute_signature(
        creds.secret_access_key, REGION, headers["x-amz-date"], cr
    )

    # One second later the signature changes; a clock far from the wall clock is honoured.
    _q2, later = _sign(
        creds=creds, query=query, canonical_uri=uri, now=T0 + timedelta(seconds=1)
    )
    assert later["x-amz-date"] == "20261120T120001Z"
    assert _signature_of(later) != match.group("sig")
    _q3, old = _sign(
        creds=creds,
        query=query,
        canonical_uri=uri,
        now=datetime(2020, 2, 29, 23, 59, 59, tzinfo=timezone.utc),
    )
    assert old["x-amz-date"] == "20200229T235959Z"


def test_D2306_14_segredo_nao_sai_em_cabecalho_nem_em_excecao() -> None:
    creds = new_credentials(with_token=True)
    for host in (AWS_HOST, "minio.lab.example:9000"):
        raw_query, headers = _sign(creds=creds, host_header=host)
        flat = raw_query + " ".join(f"{k}:{v}" for k, v in headers.items())
        assert creds.secret_access_key not in flat

    for bad_region in ("", "sa east 1", "sa-east-1\n", "x" * 200):
        with pytest.raises(ValueError) as info:
            _sign(creds=creds, region=bad_region)
        text = "".join(traceback.format_exception(info.value))
        chain: BaseException | None = info.value
        while chain is not None:
            text += repr(chain) + str(chain) + repr(getattr(chain, "args", ()))
            chain = chain.__cause__ or chain.__context__
        assert creds.secret_access_key not in text
        assert creds.access_key_id not in text
        assert str(creds.session_token) not in text
