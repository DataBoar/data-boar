"""Dev tests of task 2306.1: httpx premises and the project's own SigV4 (GET only).

Source: ``docs/desenho/2306.md`` revision 5, section 5 (option A of P-1, operator decision:
own signature with ``hmac``/``hashlib``, no third-party signer) and the TDD specification:

- D2306-0a .. D2306-0c: premises about httpx and the pinned client, against a local HTTP
  server on ``127.0.0.1``. They do not use project code under test (paths are built with the
  independent encoder of ``tests/s3_fake.py``), so they pass before the implementation.
- D2306-0d: the three S3 signing examples published by AWS, then hard keys where
  ``sign_get`` and the independent verifier of ``tests/s3_fake.py`` must agree.
- D2306-9 .. D2306-14: ``uri_encode`` and ``sign_get``, clock from the ``now`` argument.

No external network. Credentials are synthetic and built at run time
(``tests.s3_fake.new_credentials``). The AWS documentation secret of D-0d is never written
in this repository: it comes from the helper of ``tests/s3_fake.py`` (QA), built at run time.
"""

from __future__ import annotations

import hashlib
import re
import threading
import traceback
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

from hypothesis import given, settings
from hypothesis import strategies as st

from connectors.s3_sigv4 import (
    sign_get,
    uri_encode,
)
from connectors.url_guard import build_pinned_httpx_client
from tests import s3_fake
from tests.s3_fake import canonical_request, compute_signature, new_credentials

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
# D2306-0d: AWS published examples and agreement with the independent verifier
# ----------------------------------------------------------------------------

# "Examples: Signature Calculations" of "Authenticating Requests: Using the Authorization
# Header (AWS Signature Version 4)", S3 API reference (design fact P19). The access key id
# does not enter the signature, so a synthetic one is used. The documentation secret is
# provided at run time by the QA helper (never a literal in this repository).
AWS_DOC_HOST = "examplebucket.s3.amazonaws.com"
AWS_DOC_REGION = "us-east-1"
AWS_DOC_NOW = datetime(2013, 5, 24, 0, 0, 0, tzinfo=timezone.utc)
AWS_DOC_VECTORS = [
    (
        "/test.txt",
        [],
        {"range": "bytes=0-9"},
        "host;range;x-amz-content-sha256;x-amz-date",
        "f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41",
    ),
    (
        "/",
        [("lifecycle", "")],
        None,
        "host;x-amz-content-sha256;x-amz-date",
        "fea454ca298b7da1c68078a5d1bdbfbbe0d65c699e0f91ac7a200a0136783543",
    ),
    (
        "/",
        [("max-keys", "2"), ("prefix", "J")],
        None,
        "host;x-amz-content-sha256;x-amz-date",
        "34b48302e7b5fa45bde8084f4b7868a86f0a534bc59db6670ed5711ef69dc6f7",
    ),
]


def _signature_of(headers: dict[str, str]) -> str:
    lower = {k.lower(): v for k, v in headers.items()}
    match = _AUTH_RE.match(lower["authorization"])
    assert match is not None
    return match.group("sig")


@pytest.mark.parametrize(
    ("uri", "query", "extra", "signed", "expected"), AWS_DOC_VECTORS
)
def test_D2306_0d_vetores_publicados_pela_aws(
    uri: str,
    query: list[tuple[str, str]],
    extra: dict[str, str] | None,
    signed: str,
    expected: str,
) -> None:
    secret = s3_fake.aws_doc_example_secret()
    access_key_id = new_credentials(with_token=False).access_key_id
    _raw_query, headers = sign_get(
        host_header=AWS_DOC_HOST,
        canonical_uri=uri,
        query=query,
        region=AWS_DOC_REGION,
        access_key_id=access_key_id,
        secret_access_key=secret,
        session_token=None,
        now=AWS_DOC_NOW,
        extra_headers=extra,
    )
    lower = {k.lower(): v for k, v in headers.items()}
    match = _AUTH_RE.match(lower["authorization"])
    assert match is not None
    assert match.group("key") == access_key_id
    assert match.group("scope") == "20130524/us-east-1/s3/aws4_request"
    assert match.group("signed") == signed
    assert match.group("sig") == expected
    assert lower["x-amz-date"] == "20130524T000000Z"
    if extra:
        assert lower["range"] == "bytes=0-9"


def _verifier_signature(
    creds: s3_fake.Creds, uri: str, raw_query: str, headers: dict[str, str]
) -> str:
    lower = {k.lower(): v for k, v in headers.items()}
    match = _AUTH_RE.match(lower["authorization"])
    assert match is not None
    signed = match.group("signed").split(";")
    lower["host"] = AWS_HOST
    cr = canonical_request("GET", uri, raw_query, lower, signed, EMPTY_SHA256)
    return compute_signature(creds.secret_access_key, REGION, lower["x-amz-date"], cr)


P11_KEYS = [
    "corpus/a b.txt",
    "corpus/a+b.txt",
    "corpus/a%b.txt",
    "corpus/a~b.txt",
    "corpus/[1].txt",
    "corpus/#?=&.txt",
    "corpus/ação.txt",
    "corpus//dup.txt",
    "corpus/.oculto.txt",
    "corpus/a\x01.txt",
    *KEYS_40,
]


def _agree(creds: s3_fake.Creds, key: str) -> None:
    uri = "/" + s3_fake.uri_encode(key, keep_slash=True)
    query = [("prefix", key), ("list-type", "2"), ("continuation-token", key + "+/=")]
    raw_query, headers = sign_get(
        host_header=AWS_HOST,
        canonical_uri=uri,
        query=query,
        region=REGION,
        access_key_id=creds.access_key_id,
        secret_access_key=creds.secret_access_key,
        session_token=creds.session_token,
        now=T0,
    )
    assert _signature_of(headers) == _verifier_signature(creds, uri, raw_query, headers)


def test_D2306_0d_chaves_dificeis_concordam_com_o_verificador_do_simulado() -> None:
    for with_token in (False, True):
        creds = new_credentials(with_token=with_token)
        for key in P11_KEYS:
            _agree(creds, key)


_SEGMENT = st.text(min_size=1, max_size=12).filter(
    lambda s: s not in (".", "..") and "/" not in s
)


@settings(max_examples=150, deadline=None)
@given(segments=st.lists(_SEGMENT, min_size=1, max_size=4), double=st.booleans())
def test_D2306_0d_chaves_geradas_concordam_com_o_verificador(
    segments: list[str], double: bool
) -> None:
    key = ("//" if double else "/").join(segments)
    _agree(new_credentials(with_token=True), key)


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
    extra_headers: dict[str, str] | None = None,
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
        extra_headers=extra_headers,
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

    # extra_headers are signed too (name lower-cased, value stripped).
    plain = new_credentials(with_token=False)
    _q, headers = _sign(creds=plain, extra_headers={"Range": "  bytes=0-9 "})
    match = _AUTH_RE.match(headers["authorization"])
    assert match is not None
    assert match.group("signed") == "host;range;x-amz-content-sha256;x-amz-date"
    assert headers["range"] == "bytes=0-9"
    _q, headers = _sign(creds=with_token, extra_headers={"range": "bytes=0-9"})
    match = _AUTH_RE.match(headers["authorization"])
    assert match is not None
    assert match.group("signed") == (
        "host;range;x-amz-content-sha256;x-amz-date;x-amz-security-token"
    )


@pytest.mark.parametrize(
    "extra_headers",
    [
        {"Host": "evil.example"},
        {"authorization": "AWS4-HMAC-SHA256 Credential=forged"},
        {"X-Amz-Date": "20130524T000000Z"},
        {"x-amz-content-sha256": "0" * 64},
        {"range": "bytes=0-9", "RANGE": "bytes=0-99"},
        {"": "bytes=0-9"},
        {"x-amz-meta-owner": "operator"},
    ],
)
def test_D2306_11_extra_headers_reservados_ou_duplicados_sao_recusados(
    extra_headers: dict[str, str],
) -> None:
    """Reserved, x-amz-*, empty, or duplicate extra header names must not be signed.

    A colliding extra header would otherwise override Host / Authorization / X-Amz-Date
    or inject an unsigned-looking x-amz-* name into SignedHeaders.
    """
    creds = new_credentials(with_token=True)
    with pytest.raises(ValueError, match="extra header name is not accepted") as info:
        _sign(creds=creds, extra_headers=extra_headers)
    text = "".join(traceback.format_exception(info.value))
    assert creds.secret_access_key not in text
    assert creds.secret_access_key not in str(info.value)


def test_D2306_11_extra_header_com_controle_no_valor_e_recusado() -> None:
    creds = new_credentials(with_token=False)
    # Newlines are collapsed by SigV4 header canonicalization; DEL is not.
    with pytest.raises(ValueError, match="extra header value is invalid"):
        _sign(creds=creds, extra_headers={"range": "bytes=0-9\x7f"})


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

    # A clock without a time zone is refused, without the secret in the message.
    with pytest.raises(ValueError) as info:
        _sign(creds=creds, now=datetime(2026, 11, 20, 12, 0, 0))
    assert creds.secret_access_key not in str(info.value)
    assert creds.secret_access_key not in repr(info.value)


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
