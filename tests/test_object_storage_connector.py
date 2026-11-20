"""Common layer of the ``object_storage`` reader: validation, network, listing, download,
errors, findings, inventory and secrets (epic #2306, task 2306.2).

Source: ``docs/desenho/2306.md`` (revision 5 and the section 7 arbitration), sections 0, 1, 3,
6 to 12. Cases ``D2306-24``, ``D2306-26`` .. ``D2306-47``, ``D2306-53`` .. ``D2306-65``,
``D2306-67`` and the 2306.2 part of ``D2306-84``. The limit cases live in
``tests/test_object_storage_limits.py``, the coverage cases in
``tests/test_object_storage_coverage.py`` and the tier cases in
``tests/test_object_storage_tier.py``.

Driven only through the contract: ``ObjectStorageConnector(...).run()`` with the seams of
section 13, the driver registry and ``connectors.url_guard``; the simulated S3 is
``tests/s3_fake.py`` (with the subclasses of ``tests/object_storage_dev_harness.py``). Every
"nothing happened" check runs next to a positive control in the same test.
"""

from __future__ import annotations

import ast
import logging
import os
import re
import secrets
import urllib.parse
from pathlib import Path
from typing import Any, Literal

import pytest

from connectors import object_storage_driver
from connectors.object_storage_driver import ResolvedCredentials
from tests.object_storage_dev_harness import (
    AWS_HOST,
    BUCKET,
    CPF_TXT,
    EMAIL_CSV,
    EXPECTED_PATHS,
    MIB,
    MINIO_ENDPOINT,
    MINIO_HOST,
    PLAIN_TXT,
    REGION,
    TARGET_NAME,
    Harness,
    NoSizeToyDriver,
    SpyScanner,
    StreamingToyStore,
    capture_pinned_client,
    compat_target,
    connector_module,
    executive,
    ops,
    paths,
    s3_target,
    skipped_detail,
    toy_target,
)
from tests.object_storage_toy_driver import ToyDriver
from tests.s3_fake import (
    EVIL_HOST,
    GOOD_IP,
    METADATA_IP,
    PRIVATE_IP,
    _token_for,
)

ROOT = Path(__file__).resolve().parents[1]
CONNECTOR_FILE = ROOT / "connectors" / "object_storage_connector.py"


@pytest.fixture
def h(monkeypatch: pytest.MonkeyPatch) -> Harness:
    return Harness(monkeypatch)


def _marker(tag: str = "SYNTHMK") -> str:
    return tag + secrets.token_hex(6)


def _query(req: Any) -> dict[str, str]:
    return dict(urllib.parse.parse_qsl(req.raw_query, keep_blank_values=True))


def _list_reqs(fake: Any) -> list[Any]:
    return [
        r
        for r, op in zip(fake.requests, fake.operations, strict=True)
        if op == "ListObjectsV2"
    ]


# ----------------------------------------------------------------------------
# Driver selection (section 0, section 1)
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("driver", "message"),
    [
        (None, "driver must be one of: s3, s3_compatible"),
        ("ftp", "driver must be one of: s3, s3_compatible"),
        ("azure_blob", "driver azure_blob is not available yet"),
        ("gcs", "driver gcs is not available yet"),
    ],
)
def test_D2306_24_driver_ausente_ou_desconhecido_da_config_error(
    h: Harness, driver: str | None, message: str
) -> None:
    """D2306-24: driver absent, azure_blob, gcs or ftp -> config_error with the message of
    section 0 (revision 4) and zero requests."""
    fake = h.s3()
    target = s3_target()
    if driver is None:
        del target["driver"]
    else:
        target["driver"] = driver
    out = h.run(fake.transport, target)

    assert out.db.reasons() == ["config_error"]
    assert out.db.details("config_error") == [message]
    assert fake.requests == []
    assert out.db.findings == []
    h.control_scan()


def test_D2306_64_lista_da_mensagem_vem_do_registro(h: Harness) -> None:
    """D2306-64 (2306.2 part): the KeyError of get_driver becomes config_error, and the list
    in the message comes from the registry (the toy driver registered here is cited)."""
    store = h.toy({"corpus/a.txt": CPF_TXT})
    fake = h.s3()
    out = h.run(fake.transport, s3_target(driver="x"))

    assert out.db.details("config_error") == [
        "driver must be one of: s3, s3_compatible, toy"
    ]
    assert fake.requests == []
    assert store.requests == []
    ok = h.run(store.transport, toy_target())
    assert paths(ok.db) == {"toy://caixa-sintetica/corpus/a.txt"}


def test_D2306_84_camada_comum_recusa_so_as_misnamed_keys_do_driver(h: Harness) -> None:
    """D2306-84 (2306.2 part): the common layer refuses only the misnamed_keys of the
    target's driver, with "<key> is not accepted by driver <name>; <hint>"; the toy target
    with ``host`` runs."""
    cases = [
        (s3_target(host="minio.lab.example"), "host", "s3", "use endpoint_url"),
        (s3_target(endpoint="https://x.example"), "endpoint", "s3", "use endpoint_url"),
        (
            s3_target(endpoint_url=MINIO_ENDPOINT),
            "endpoint_url",
            "s3",
            "use driver s3_compatible",
        ),
        (
            compat_target(url="https://x.example"),
            "url",
            "s3_compatible",
            "use endpoint_url",
        ),
        (
            compat_target(base_url="https://x.example"),
            "base_url",
            "s3_compatible",
            "use endpoint_url",
        ),
    ]
    for target, key, driver, hint in cases:
        fake = h.s3()
        out = h.run(fake.transport, target)
        assert out.db.details("config_error") == [
            f"{key} is not accepted by driver {driver}; {hint}"
        ], key
        assert fake.requests == [], key
    store = h.toy({"corpus/a.txt": CPF_TXT})
    ok = h.run(store.transport, toy_target())
    assert ok.db.failures == []
    assert paths(ok.db) == {"toy://caixa-sintetica/corpus/a.txt"}
    bad = h.run(store.transport, toy_target(url="https://toy.lab.example"))
    assert bad.db.details("config_error") == [
        "url is not accepted by driver toy; use host"
    ]


# ----------------------------------------------------------------------------
# Validation in the connector (section 1, section 3)
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        (
            {"verify_ssl": False},
            "TLS verification cannot be disabled for object_storage",
        ),
        ({"verify": False}, "TLS verification cannot be disabled for object_storage"),
        (
            {"headers": {"X-Custom": "1"}},
            "custom headers are not accepted for object_storage",
        ),
    ],
)
def test_D2306_26_tls_desligado_e_headers_dao_config_error(
    h: Harness, extra: dict[str, Any], message: str
) -> None:
    """D2306-26: verify_ssl: false, verify: false and headers: {...} -> config_error."""
    fake = h.s3()
    out = h.run(fake.transport, s3_target(**extra))

    assert out.db.details("config_error") == [message]
    assert fake.requests == []
    h.control_scan()


@pytest.mark.parametrize(
    "env_name, label",
    [
        ("DATA_BOAR_S3_ACCESS_KEY_ID", "auth.access_key_id_from_env"),
        ("DATA_BOAR_S3_SECRET_ACCESS_KEY", "auth.secret_access_key_from_env"),
        ("DATA_BOAR_S3_SESSION_TOKEN", "auth.session_token_from_env"),
    ],
)
@pytest.mark.parametrize(
    "shape, expected",
    [
        ("empty", "is empty"),
        ("blank", "is empty"),
        ("inner_space", "has invalid characters"),
        ("control", "has invalid characters"),
        ("non_ascii", "has invalid characters"),
    ],
)
def test_D2306_27_credencial_vazia_ou_invalida_da_config_error(
    h: Harness,
    monkeypatch: pytest.MonkeyPatch,
    env_name: str,
    label: str,
    shape: str,
    expected: str,
) -> None:
    """D2306-27 (revision 3): an empty value, or one with an inner space, a control or a
    non-ASCII character, gives config_error citing the key label, never the value, and zero
    requests; it holds for session_token_from_env when the key is in the target."""
    mark = _marker()
    value = {
        "empty": "",
        "blank": "   ",
        "inner_space": f"{mark} x",
        "control": f"{mark}\x01",
        "non_ascii": f"{mark}é",
    }[shape]
    monkeypatch.setenv(env_name, value)
    fake = h.s3()
    out = h.run(fake.transport, s3_target())

    assert out.db.details("config_error") == [f"credential from {label} {expected}"]
    assert mark not in out.db.as_text()
    assert fake.requests == []


def test_D2306_28_variaveis_aws_nunca_sao_lidas(
    h: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D2306-28: with AWS_* set to markers, empty DATA_BOAR_* give config_error and zero
    requests; valid DATA_BOAR_* sign with their own key id, and no AWS_* value reaches a
    request."""
    aws = {
        "AWS_ACCESS_KEY_ID": _marker("SYNTHAK"),
        "AWS_SECRET_ACCESS_KEY": _marker("SYNTHSK"),
        "AWS_SESSION_TOKEN": _marker("SYNTHST"),
        "AWS_PROFILE": _marker("SYNTHPR"),
    }
    for name, value in aws.items():
        monkeypatch.setenv(name, value)
    valid = dict(os.environ)

    for env in ("DATA_BOAR_S3_ACCESS_KEY_ID", "DATA_BOAR_S3_SECRET_ACCESS_KEY"):
        monkeypatch.setenv(env, "")
    fake = h.s3()
    out = h.run(fake.transport, s3_target())
    assert "config_error" in out.db.reasons()
    assert fake.requests == []

    for env in ("DATA_BOAR_S3_ACCESS_KEY_ID", "DATA_BOAR_S3_SECRET_ACCESS_KEY"):
        monkeypatch.setenv(env, valid[env])
    fake = h.s3()
    out = h.run(fake.transport, s3_target())
    assert paths(out.db) == EXPECTED_PATHS
    assert fake.requests
    for req in fake.requests:
        assert f"Credential={h.creds.access_key_id}/" in req.headers["authorization"]
        blob = req.url + repr(req.headers)
        for value in aws.values():
            assert value not in blob
    assert fake.auth_failures == []


# ----------------------------------------------------------------------------
# Network (section 6)
# ----------------------------------------------------------------------------


def test_D2306_29_cliente_com_pin_construido_uma_vez(
    h: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D2306-29: without the ``_transport`` seam the connector calls
    ``url_guard.build_pinned_httpx_client`` once, with host_to_ips == {host: guard IPs},
    follow_redirects=False and the httpx.Timeout of the target values."""
    import httpx

    fake = h.s3()
    seen = capture_pinned_client(monkeypatch, fake.transport)
    out = h.run(None, s3_target(timeout=7))

    assert len(seen) == 1, seen
    kwargs = seen[0]
    assert kwargs["host_to_ips"] == {AWS_HOST: [GOOD_IP]}
    assert kwargs["follow_redirects"] is False
    assert kwargs["timeout"] == httpx.Timeout(connect=7, read=7, write=7, pool=7)
    assert "verify" not in kwargs or kwargs["verify"] is True
    assert paths(out.db) == EXPECTED_PATHS


def test_D2306_30_endpoint_privado_so_com_allow_private_networks(h: Harness) -> None:
    """D2306-30: an endpoint_url resolving to 10.0.0.5 without allow_private_networks gives
    scope_violation and zero requests; with allow_private_networks: true the scan goes on."""
    fake = h.minio(ip=PRIVATE_IP)
    out = h.run(fake.transport, compat_target(allow_private_networks=False))
    assert out.db.reasons() == ["scope_violation"]
    assert fake.requests == []

    fake = h.minio(ip=PRIVATE_IP)
    out = h.run(fake.transport, compat_target(allow_private_networks=True))
    assert "scope_violation" not in out.db.reasons()
    assert paths(out.db) == EXPECTED_PATHS


def test_D2306_31_modo_aws_ignora_allow_private_networks(h: Harness) -> None:
    """D2306-31: driver s3 with the host resolving to 169.254.169.254 and
    allow_private_networks: true -> scope_violation and zero requests."""
    fake = h.s3(ip=METADATA_IP)
    out = h.run(fake.transport, s3_target(allow_private_networks=True))

    assert out.db.reasons() == ["scope_violation"]
    assert fake.requests == []
    h.control_scan()


def test_D2306_32_falha_de_dns_da_unreachable(h: Harness) -> None:
    """D2306-32: a DNS failure (the map raises OSError) -> unreachable and zero requests."""
    fake = h.s3(ip=None)
    out = h.run(fake.transport, s3_target())

    assert out.db.reasons() == ["unreachable"]
    assert fake.requests == []
    h.control_scan()


def test_D2306_33_varredura_completa_fala_com_um_host_so(h: Harness) -> None:
    """D2306-33: in a full scan every request goes to the same host, and the simulator
    records no violation."""
    fake = h.s3()
    out = h.run(fake.transport, s3_target())

    assert paths(out.db) == EXPECTED_PATHS
    assert fake.requests
    assert {r.host for r in fake.requests} == {AWS_HOST}
    assert fake.violations == []
    assert fake.auth_failures == []


def test_D2306_34_redirect_nunca_e_seguido(h: Harness) -> None:
    """D2306-34: 301 PermanentRedirect on the listing -> config_error "bucket is not in
    region ..."; 307 with Location on evil.example -> scope_violation and no request there."""
    fake = h.s3()
    fake.redirect(301, "PermanentRedirect")
    out = h.run(fake.transport, s3_target())
    assert out.db.reasons() == ["config_error"]
    assert out.db.details("config_error")[0].startswith("bucket is not in region")
    assert ops(fake, "GetObject") == 0

    fake = h.s3()
    fake.redirect(307, location=f"https://{EVIL_HOST}/databoar-sintetico/x")
    out = h.run(fake.transport, s3_target())
    assert out.db.reasons() == ["scope_violation"]
    assert out.db.details("scope_violation") == ["redirect refused"]
    assert fake.requests
    assert all(r.host == AWS_HOST for r in fake.requests)
    assert ops(fake, "GetObject") == 0


@pytest.mark.parametrize(
    ("retry_after", "expected"),
    [(None, [1, 2]), (7, [7]), (999, [60])],
)
def test_D2306_35_slowdown_espera_e_segue(
    h: Harness, retry_after: int | None, expected: list[int]
) -> None:
    """D2306-35: 503 SlowDown twice then 200 -> sleep [1, 2] and the scan completes;
    Retry-After: 7 -> [7]; Retry-After: 999 -> [60]."""
    fake = h.s3()
    fake.throttle(1 if retry_after is not None else 2, retry_after=retry_after)
    out = h.run(fake.transport, s3_target())

    assert out.clock.sleeps == expected
    assert paths(out.db) == EXPECTED_PATHS
    assert "throttled" not in out.db.reasons()


def test_D2306_36_5xx_esgotado_na_listagem_da_unreachable(h: Harness) -> None:
    """D2306-36: 500 four times on the listing -> unreachable, sleep [1, 2, 4] and no
    GetObject."""
    fake = h.s3()
    fake.throttle(4, status=500, code="InternalError", op="ListObjectsV2")
    out = h.run(fake.transport, s3_target())

    assert out.db.reasons() == ["unreachable"]
    assert out.clock.sleeps == [1, 2, 4]
    assert ops(fake, "ListObjectsV2") == 4
    assert ops(fake, "GetObject") == 0


@pytest.mark.parametrize(
    ("kind", "cls_name"), [("connect", "ConnectError"), ("read_timeout", "ReadTimeout")]
)
def test_D2306_37_erro_de_rede_esgotado_cita_so_a_classe(
    h: Harness, kind: Literal["connect", "read_timeout"], cls_name: str
) -> None:
    """D2306-37: ConnectError or ReadTimeout four times on the listing -> unreachable, the
    message carrying only the exception class name (never str(e) nor the URL)."""
    fake = h.s3()
    fake.network_error(4, kind=kind)
    out = h.run(fake.transport, s3_target())

    assert out.db.reasons() == ["unreachable"]
    (detail,) = out.db.details("unreachable")
    assert cls_name in detail
    assert "synthetic" not in detail
    assert AWS_HOST not in detail
    assert out.clock.sleeps == [1, 2, 4]


def test_D2306_38_objeto_esgotado_e_tres_seguidos(h: Harness) -> None:
    """D2306-38: one object exhausting the retries gives download_failed and the others are
    scanned; three objects in a row exhausted end the target with unreachable "endpoint
    stopped responding"."""
    fake = h.s3()
    fake.error_on("GetObject", key="corpus/a.txt", status=500, code="InternalError")
    out = h.run(fake.transport, s3_target(report_object_names=True))
    assert out.db.details("download_failed") and all(
        "corpus/a.txt" in d for d in out.db.details("download_failed")
    )
    assert paths(out.db) == {f"s3://{BUCKET}/corpus/sub/c.csv"}
    assert "unreachable" not in out.db.reasons()

    objects = {f"corpus/k{i}.txt": CPF_TXT for i in range(5)}
    fake = h.s3(objects)
    for i in range(3):
        fake.error_on("GetObject", key=f"corpus/k{i}.txt", status=503, code="SlowDown")
    out = h.run(fake.transport, s3_target())
    assert out.db.details("unreachable") == ["endpoint stopped responding"]
    assert "corpus/k3.txt" not in fake.fetched
    assert out.db.findings == []


def test_D2306_39_cada_tentativa_e_assinada_de_novo(h: Harness) -> None:
    """D2306-39: on a retry the second attempt carries another x-amz-date (the clock moved)
    and the simulator accepts it."""
    fake = h.s3()
    fake.throttle(1, op="ListObjectsV2")
    out = h.run(fake.transport, s3_target())

    lists = _list_reqs(fake)
    assert len(lists) >= 2
    assert lists[0].headers["x-amz-date"] != lists[1].headers["x-amz-date"]
    assert fake.auth_failures == []
    assert paths(out.db) == EXPECTED_PATHS


# ----------------------------------------------------------------------------
# Listing (section 7)
# ----------------------------------------------------------------------------


def test_D2306_40_paginacao_com_continuation_token(h: Harness) -> None:
    """D2306-40: 2500 keys and page 1000 -> 3 listings with max-keys=1000, the second and
    third with the continuation-token of the previous answer, encoding-type=url in all.
    (The keys are .exe, outside the extension filter, so nothing is downloaded.)"""
    objects = {f"corpus/k{i:05d}.exe": b"x" for i in range(2500)}
    fake = h.s3(objects)
    out = h.run(fake.transport, s3_target())

    lists = [_query(r) for r in _list_reqs(fake)]
    assert len(lists) == 3
    assert [q["max-keys"] for q in lists] == ["1000", "1000", "1000"]
    assert all(q["encoding-type"] == "url" for q in lists)
    assert all(q["list-type"] == "2" for q in lists)
    assert "continuation-token" not in lists[0]
    assert lists[1]["continuation-token"] == _token_for(1000)
    assert lists[2]["continuation-token"] == _token_for(2000)
    assert all("delimiter" not in q for q in lists)
    assert ops(fake, "GetObject") == 0
    assert executive(out.db)["objects_listed"] == 2500


@pytest.mark.parametrize("mode", ["missing_token", "repeat_token"])
def test_D2306_41_laco_de_paginacao_da_protocol_error(
    h: Harness, mode: Literal["missing_token", "repeat_token"]
) -> None:
    """D2306-41: IsTruncated=true without a token, or with a repeated token ->
    protocol_error "listing pagination loop"; the objects already listed are downloaded."""
    fake = h.s3()
    fake.pagination(mode)
    out = h.run(fake.transport, s3_target())

    assert out.db.details("protocol_error") == ["listing pagination loop"]
    assert paths(out.db) == EXPECTED_PATHS


_LISTING_OK_TAIL = (
    b"<ListBucketResult><IsTruncated>false</IsTruncated>"
    b"<Contents><Key>corpus/a.txt</Key><Size>51</Size></Contents></ListBucketResult>"
)


@pytest.mark.parametrize(
    "case",
    ["malformed", "doctype_entity", "doctype_plain", "external_entity", "wrong_root"],
)
def test_D2306_42_xml_ruim_da_protocol_error_e_nenhum_get(
    h: Harness, case: str
) -> None:
    """D2306-42 (revision 5 arbitration): malformed XML, any DOCTYPE (even without entity),
    internal or external entity, or a root whose local name is not ListBucketResult ->
    protocol_error and zero GetObject. A listing in another namespace is accepted (control)."""
    fake = h.s3()
    if case == "malformed":
        fake.malformed_xml = True
    elif case == "doctype_entity":
        fake.doctype_entity = True
    elif case == "doctype_plain":
        fake.raw_listing_body(
            b'<?xml version="1.0"?><!DOCTYPE ListBucketResult>' + _LISTING_OK_TAIL
        )
    elif case == "external_entity":
        fake.raw_listing_body(
            b'<?xml version="1.0"?><!DOCTYPE ListBucketResult [<!ENTITY ext SYSTEM '
            b'"file:///etc/hostname">]><ListBucketResult><IsTruncated>false'
            b"</IsTruncated><Contents><Key>&ext;</Key><Size>1</Size></Contents>"
            b"</ListBucketResult>"
        )
    else:
        fake.raw_listing_body(
            _LISTING_OK_TAIL.replace(b"ListBucketResult", b"ListAllMyBucketsResult")
        )
    out = h.run(fake.transport, s3_target())

    assert out.db.details("protocol_error") == ["malformed listing response"]
    assert ops(fake, "GetObject") == 0
    assert out.db.findings == []

    other = h.s3()
    other.namespace = "other"
    ok = h.run(other.transport, s3_target())
    assert paths(ok.db) == EXPECTED_PATHS
    assert "protocol_error" not in ok.db.reasons()


def test_D2306_43_listagem_acima_de_16_mib(h: Harness) -> None:
    """D2306-43: a listing body above 16 MiB -> protocol_error "listing response too
    large" and zero GetObject."""
    fake = h.s3()
    fake.oversized_listing = True
    out = h.run(fake.transport, s3_target())

    assert out.db.details("protocol_error") == ["listing response too large"]
    assert ops(fake, "GetObject") == 0


def test_D2306_44_encoding_type_url(h: Harness) -> None:
    """D2306-44: with EncodingType=url the key listed as corpus/a+b%2Bc%25d.txt is the
    object corpus/a b+c%d.txt; without EncodingType, corpus/a+b.txt is used literally."""
    fake = h.s3({"corpus/a b+c%d.txt": CPF_TXT})
    out = h.run(fake.transport, s3_target())
    assert fake.fetched == ["corpus/a b+c%d.txt"]
    assert paths(out.db) == {f"s3://{BUCKET}/corpus/a b+c%d.txt"}

    fake = h.s3({"corpus/a+b.txt": CPF_TXT})
    fake.encoding_type = None
    out = h.run(fake.transport, s3_target())
    assert fake.fetched == ["corpus/a+b.txt"]
    assert paths(out.db) == {f"s3://{BUCKET}/corpus/a+b.txt"}


@pytest.mark.parametrize("names", [False, True])
def test_D2306_45_chave_fora_do_prefixo_nunca_e_pedida_nem_nomeada(
    h: Harness, caplog: pytest.LogCaptureFixture, names: bool
) -> None:
    """D2306-45: keys injected outside the prefix are never fetched, the summary counts
    out_of_prefix, and no failure nor log carries them (not even with report_object_names)."""
    mark = _marker()
    caplog.set_level(logging.DEBUG)
    fake = h.s3()
    fake.inject_keys({f"outro/{mark}.txt": CPF_TXT, f"{mark}/x.txt": CPF_TXT})
    out = h.run(fake.transport, s3_target(report_object_names=names))

    assert not any(mark in k for k in fake.fetched)
    assert "out_of_prefix=2" in skipped_detail(out.db)
    assert mark not in out.db.as_text()
    assert mark not in caplog.text
    assert paths(out.db) == EXPECTED_PATHS


def test_D2306_46_unsafe_key_controle_e_chave_longa(h: Harness) -> None:
    """D2306-46: corpus/../x.txt and corpus/./x.txt are not fetched and give one unsafe_key
    failure each (report_object_names: true); corpus/a\\x01.txt IS fetched and its display
    path shows \\x01 as text; a key of 1025 bytes is not fetched and counts invalid_key;
    corpus/.oculto.txt and corpus/..x.txt are fetched."""
    long_key = "corpus/" + "k" * (1025 - len("corpus/") - len(".txt")) + ".txt"
    assert len(long_key.encode("utf-8")) == 1025
    objects = {
        "corpus/a\x01.txt": CPF_TXT,
        "corpus/.oculto.txt": CPF_TXT,
        "corpus/..x.txt": CPF_TXT,
    }
    fake = h.s3(objects)
    fake.inject_keys(
        {"corpus/../x.txt": CPF_TXT, "corpus/./x.txt": CPF_TXT, long_key: CPF_TXT}
    )
    out = h.run(fake.transport, s3_target(report_object_names=True))

    assert sorted(fake.fetched) == sorted(objects)
    unsafe = out.db.details("unsafe_key")
    assert len(unsafe) == 2
    assert any("corpus/../x.txt" in d for d in unsafe)
    assert any("corpus/./x.txt" in d for d in unsafe)
    summary = skipped_detail(out.db)
    assert "unsafe_key=2" in summary
    assert "invalid_key=1" in summary
    assert paths(out.db) == {
        f"s3://{BUCKET}/corpus/a\\x01.txt",
        f"s3://{BUCKET}/corpus/.oculto.txt",
        f"s3://{BUCKET}/corpus/..x.txt",
    }


def test_D2306_47_marcador_de_pasta_e_ignorado(h: Harness) -> None:
    """D2306-47: corpus/dir/ of size 0 -> no GetObject and no failure."""
    fake = h.s3({"corpus/dir/": b"", "corpus/a.txt": CPF_TXT})
    out = h.run(fake.transport, s3_target())

    assert fake.fetched == ["corpus/a.txt"]
    assert out.db.failures == []
    assert paths(out.db) == {f"s3://{BUCKET}/corpus/a.txt"}


# ----------------------------------------------------------------------------
# Download errors (section 8, section 11)
# ----------------------------------------------------------------------------


def test_D2306_53_erro_por_objeto_nao_para_o_alvo(h: Harness) -> None:
    """D2306-53: 403 AccessDenied on one object and 404 NoSuchKey on another give
    download_failed with the code each, and the others are scanned."""
    objects = {**_base(), "corpus/e.txt": CPF_TXT}
    fake = h.s3(objects)
    fake.error_on("GetObject", key="corpus/a.txt", status=403, code="AccessDenied")
    fake.error_on("GetObject", key="corpus/sub/c.csv", status=404, code="NoSuchKey")
    out = h.run(fake.transport, s3_target(report_object_names=True))

    failed = out.db.details("download_failed")
    assert len(failed) == 2
    assert any("corpus/a.txt" in d and "AccessDenied" in d for d in failed)
    assert any("corpus/sub/c.csv" in d and "NoSuchKey" in d for d in failed)
    assert paths(out.db) == {f"s3://{BUCKET}/corpus/e.txt"}
    assert "download_failed=2" in skipped_detail(out.db)

    fake = h.s3(objects)
    fake.error_on("GetObject", key="corpus/a.txt", status=403, code="AccessDenied")
    out = h.run(fake.transport, s3_target())
    assert out.db.details("download_failed") == []
    assert "download_failed=1" in skipped_detail(out.db)


def _base() -> dict[str, bytes]:
    return {
        "corpus/a.txt": CPF_TXT,
        "corpus/b.txt": PLAIN_TXT,
        "corpus/sub/c.csv": EMAIL_CSV,
    }


def test_D2306_54_temporario_0700_apagado_e_nome_local(h: Harness) -> None:
    """D2306-54: the temp dir has mode 0700; each file is deleted after its object and the
    dir at the end, even when the scanner raises; the local name is obj-<n><ext> for
    corpus/sub/a.txt."""
    made = h.spy_mkdtemp()
    seen: list[tuple[int, list[str]]] = []

    def look(_content: str, _path: Any) -> None:
        assert made, "no temp dir created with tempfile.mkdtemp"
        seen.append((os.stat(made[0]).st_mode & 0o777, sorted(os.listdir(made[0]))))

    fake = h.s3({"corpus/sub/a.txt": CPF_TXT, "corpus/sub/b.txt": PLAIN_TXT})
    out = h.run(fake.transport, s3_target(), scanner=SpyScanner(look))

    assert len(made) == 1
    assert len(seen) == 2
    for mode, files in seen:
        if os.name == "posix":
            assert mode == 0o700
        assert len(files) == 1
        assert re.fullmatch(r"obj-\d+\.txt", files[0]), files
    assert not Path(made[0]).exists()
    assert paths(out.db) == {f"s3://{BUCKET}/corpus/sub/a.txt"}

    class Boom(SpyScanner):
        def scan_file_content(self, content: str, file_path: Any) -> Any:
            raise RuntimeError("scanner exploded")

    made.clear()
    fake = h.s3({"corpus/sub/a.txt": CPF_TXT})
    h.run(fake.transport, s3_target(), scanner=Boom())
    assert len(made) == 1
    assert not Path(made[0]).exists()


def test_D2306_55_extensao_fora_do_filtro_nao_e_pedida(h: Harness) -> None:
    """D2306-55: a .exe outside the extension filter is never fetched."""
    fake = h.s3({"corpus/tool.exe": b"MZ", "corpus/a.txt": CPF_TXT})
    out = h.run(fake.transport, s3_target())

    assert fake.fetched == ["corpus/a.txt"]
    assert out.db.failures == []
    assert paths(out.db) == {f"s3://{BUCKET}/corpus/a.txt"}


@pytest.mark.parametrize(
    ("status", "code", "reason", "text"),
    [
        (403, "InvalidAccessKeyId", "auth_failed", "InvalidAccessKeyId"),
        (403, "SignatureDoesNotMatch", "auth_failed", "SignatureDoesNotMatch"),
        (400, "ExpiredToken", "auth_failed", "ExpiredToken"),
        (403, "RequestTimeTooSkewed", "auth_failed", "clock skew"),
        (403, "AccessDenied", "permission_denied", "AccessDenied"),
        (404, "NoSuchBucket", "not_found", "NoSuchBucket"),
        (
            400,
            "AuthorizationHeaderMalformed",
            "config_error",
            "bucket is not in region",
        ),
    ],
)
def test_D2306_56_mapeamento_de_erros_da_listagem(
    h: Harness, status: int, code: str, reason: str, text: str
) -> None:
    """D2306-56: the section 11 mapping on the listing; each of these ends the target (zero
    GetObject)."""
    fake = h.s3()
    fake.error_on("ListObjectsV2", status=status, code=code)
    out = h.run(fake.transport, s3_target())

    assert out.db.reasons() == [reason]
    (detail,) = out.db.details(reason)
    assert text in detail
    assert ops(fake, "GetObject") == 0
    assert out.clock.sleeps == []


def test_D2306_56_codigo_fora_do_vocabulario_nao_e_gravado(h: Harness) -> None:
    """D2306-56: a code outside the vocabulary (Xyz) gives "S3 error HTTP 400", without the
    code."""
    fake = h.s3()
    fake.error_on("ListObjectsV2", status=400, code="Xyz")
    out = h.run(fake.transport, s3_target())

    assert any(d == "S3 error HTTP 400" for _t, _r, d in out.db.failures)
    assert "Xyz" not in out.db.as_text()


def test_D2306_57_corpo_de_erro_com_eco_nao_vaza(
    h: Harness, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """D2306-57: with error_body_echo no marker reaches the failure details, the logs or
    the inventory."""
    caplog.set_level(logging.DEBUG)
    fake = h.s3()
    fake.error_body_echo = True
    fake.error_on("ListObjectsV2", status=403, code="AccessDenied")
    out = h.run(fake.transport, s3_target())

    assert out.db.reasons() == ["permission_denied"]
    captured = capsys.readouterr()
    haystack = out.db.as_text() + caplog.text + captured.out + captured.err
    for secret in (
        h.creds.access_key_id,
        h.creds.secret_access_key,
        h.creds.session_token or "unused",
    ):
        assert secret not in haystack
    for marker in ("SYNTHAK", "SYNTHSK", "SYNTHST", "StringToSign", "CanonicalRequest"):
        assert marker not in haystack


# ----------------------------------------------------------------------------
# Findings (section 9)
# ----------------------------------------------------------------------------


def test_D2306_58_texto_vai_ao_scanner_e_vira_achado_de_arquivo(h: Harness) -> None:
    """D2306-58 (text): a .txt with a synthetic CPF calls scanner.scan_file_content with
    the text and Path("a.txt"), and save_finding("filesystem", path="s3://.../corpus/a.txt",
    file_name="a.txt", data_type="TXT", ...)."""
    scanner = SpyScanner()
    fake = h.s3({"corpus/a.txt": CPF_TXT})
    out = h.run(fake.transport, s3_target(), scanner=scanner)

    assert len(scanner.calls) == 1
    content, file_path = scanner.calls[0]
    assert "123.456.789-09" in content
    assert file_path == Path("a.txt")
    assert len(out.db.findings) == 1
    finding = out.db.findings[0]
    assert finding["source_type"] == "filesystem"
    assert finding["target_name"] == TARGET_NAME
    assert finding["path"] == f"s3://{BUCKET}/corpus/a.txt"
    assert finding["file_name"] == "a.txt"
    assert finding["data_type"] == "TXT"
    assert finding["pattern_detected"] == "LGPD_CPF"
    for field in ("sensitivity_level", "norm_tag", "ml_confidence"):
        assert field in finding


def test_D2306_58_sqlite_passa_pelo_leitor_de_banco(
    h: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D2306-58 (sqlite): a .sqlite goes through _scan_sqlite_file_as_db (the connector
    module imports it, section 9)."""
    mod = connector_module()
    assert hasattr(mod, "_scan_sqlite_file_as_db")
    calls: list[Path] = []

    def fake_sqlite(path: Path, _scanner: Any, _limit: int) -> list[dict[str, Any]]:
        calls.append(path)
        return [
            {
                "file_name": "db.sqlite",
                "data_type": "SQLITE",
                "sensitivity_level": "HIGH",
                "pattern_detected": "LGPD_CPF",
                "norm_tag": "LGPD Art. 5",
                "ml_confidence": 100,
            }
        ]

    monkeypatch.setattr(mod, "_scan_sqlite_file_as_db", fake_sqlite)
    fake = h.s3({"corpus/db.sqlite": b"SQLite format 3\x00"})
    out = h.run(fake.transport, s3_target())

    assert len(calls) == 1
    assert paths(out.db) == {f"s3://{BUCKET}/corpus/db.sqlite"}


def test_D2306_58_zip_passa_pelo_leitor_de_compactados(
    h: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D2306-58 (zip): with scan_compressed a .zip goes through scan_archive_at_path with
    path_display equal to the s3:// path (the connector module imports it, section 9)."""
    import io
    import zipfile

    mod = connector_module()
    assert hasattr(mod, "scan_archive_at_path")
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(mod, "scan_archive_at_path", lambda **kw: calls.append(kw))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("dentro.txt", CPF_TXT)
    fake = h.s3({"corpus/pacote.zip": buf.getvalue()})
    h.run(
        fake.transport,
        s3_target(file_scan={"scan_compressed": True}),
    )

    assert len(calls) == 1
    assert calls[0]["path_display"] == f"s3://{BUCKET}/corpus/pacote.zip"
    assert calls[0]["target_name"] == TARGET_NAME


# ----------------------------------------------------------------------------
# Inventory (section 10)
# ----------------------------------------------------------------------------


def test_D2306_59_inventario_de_sucesso(h: Harness) -> None:
    """D2306-59 (success): exactly one inventory row with the fields of section 10."""
    fake = h.s3()
    out = h.run(fake.transport, s3_target())

    assert len(out.db.inventories) == 1
    row = out.db.inventories[0]
    assert row["target_name"] == TARGET_NAME
    assert row["source_type"] == "object_storage"
    assert row["product"] == "Amazon S3"
    assert row["product_version"] is None
    assert row["protocol_or_api_version"] == "S3 ListObjectsV2"
    assert row["transport_security"] == "tls=https"
    ex = executive(out.db)
    assert ex["engine"] == "s3"
    assert ex["bucket"] == BUCKET
    assert ex["prefix"] == "corpus/"
    assert ex["region"] == REGION
    assert ex["addressing"] == "virtual"
    assert "endpoint_host" not in ex
    assert ex["status"] == "completed"
    assert ex["objects_listed"] == 3
    assert ex["objects_downloaded"] == 3
    assert ex["bytes_downloaded"] == len(CPF_TXT) + len(PLAIN_TXT) + len(EMAIL_CSV)


def test_D2306_59_inventario_do_compativel(h: Harness) -> None:
    """D2306-59 (product): S3-compatible with endpoint_url, and the endpoint host."""
    fake = h.minio()
    out = h.run(fake.transport, compat_target())

    assert len(out.db.inventories) == 1
    assert out.db.inventories[0]["product"] == "S3-compatible"
    ex = executive(out.db)
    assert ex["engine"] == "s3_compatible"  # revision 6, R6-3: the registry name
    assert ex["endpoint_host"] == MINIO_HOST
    assert ex["addressing"] == "path"


def test_D2306_59_inventario_de_config_error_nao_ecoa_a_config(h: Harness) -> None:
    """D2306-59 (config_error): transport_security unknown, status failed:config_error and
    nothing else from the config (the userinfo marker of endpoint_url never shows)."""
    mark = _marker()
    endpoint = f"https://{mark}:{mark}x@{MINIO_HOST}:9000"
    fake = h.minio()
    out = h.run(fake.transport, compat_target(endpoint_url=endpoint))

    assert "config_error" in out.db.reasons()
    assert fake.requests == []
    assert len(out.db.inventories) == 1
    row = out.db.inventories[0]
    assert row["source_type"] == "object_storage"
    assert row["product"] is None
    assert row["product_version"] is None
    assert row["protocol_or_api_version"] is None
    assert row["transport_security"] == "unknown"
    raw = out.db.inventory_json()
    assert set(raw) == {"executive"}
    # Revision 6, R6-3: exact equality; the coverage block is always written, zeroed here,
    # and engine is the registry name of the driver.
    assert raw["executive"] == {
        "engine": "s3_compatible",
        "status": "failed:config_error",
        "coverage": "partial",
        "listing_complete": False,
        "objects_listed": 0,
        "objects_scanned": 0,
        "objects_not_scanned": 0,
        "bytes_not_scanned": 0,
        "objects_unknown_size": 0,
        "not_scanned_by_reason": {},
        "limits_disabled": [],
    }
    assert mark not in out.db.as_text()


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("\x01" + "S" * 99, "\\x01" + "S" * 44),
        # Revision 6, R6-7: the escape starts at position 46; cutting at 48 would split it,
        # so the whole escape goes.
        ("S" * 46 + "\x01" + "S" * 53, "S" * 46),
    ],
)
def test_D2306_59_server_header_cortado_e_saneado(
    h: Harness, header: str, expected: str
) -> None:
    """D2306-59 (server_header) and R6-7: sanitise first (non-printable -> \\xNN), then
    cut at 48 characters without splitting an escape."""
    fake = h.s3()
    fake.server_header = header
    out = h.run(fake.transport, s3_target())

    raw = out.db.inventory_json()
    assert raw["technical"]["server_header"] == expected


# ----------------------------------------------------------------------------
# Unexpected errors and secrets (section 12)
# ----------------------------------------------------------------------------


class _ExplodingToy(ToyDriver):
    marker = ""
    exc: type[BaseException] = RuntimeError

    def list_request(self, *args: Any, **kwargs: Any) -> Any:
        raise self.exc(self.marker)


def test_D2306_60_excecao_inesperada_vira_error_fixo(
    h: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D2306-60: an internal raising RuntimeError("SYNTHSK-...") gives the failure "error"
    with the fixed message naming RuntimeError, without the marker; run() does not raise.
    A KeyboardInterrupt goes up."""
    mark = _marker("SYNTHSK-")
    monkeypatch.setattr(_ExplodingToy, "marker", mark)
    store = h.toy({"corpus/a.txt": CPF_TXT}, driver=_ExplodingToy)
    out = h.run(store.transport, toy_target())

    assert out.db.details("error") == [
        "unexpected error in object_storage connector (RuntimeError)"
    ]
    assert mark not in out.db.as_text()
    assert len(out.db.inventories) == 1

    monkeypatch.setattr(_ExplodingToy, "exc", KeyboardInterrupt)
    with pytest.raises(KeyboardInterrupt):
        h.run(store.transport, toy_target())


def test_D2306_61_nenhum_segredo_em_log_saida_ou_repr(
    h: Harness, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """D2306-61: in a full scan with the root logger at DEBUG (httpx and httpcore too) the
    access key id, the secret, the session token and the Signature value appear nowhere:
    logs, stdout/stderr, failures, findings, inventory, repr(connector)."""
    caplog.set_level(logging.DEBUG)
    for name in ("httpx", "httpcore"):
        caplog.set_level(logging.DEBUG, logger=name)
    fake = h.s3()
    out = h.run(fake.transport, s3_target())

    assert paths(out.db) == EXPECTED_PATHS
    signatures = [r.signature for r in fake.requests if r.signature]
    assert signatures
    captured = capsys.readouterr()
    haystack = "\n".join(
        [
            caplog.text,
            captured.out,
            captured.err,
            out.db.as_text(),
            repr(out.connector),
            str(out.connector),
        ]
    )
    secrets_ = [h.creds.access_key_id, h.creds.secret_access_key]
    secrets_.append(h.creds.session_token or "unused")
    for value in secrets_ + signatures:
        assert value not in haystack


def test_D2306_62_so_get_e_so_as_duas_operacoes(h: Harness) -> None:
    """D2306-62: every request is GET, operations are only ListObjectsV2 and GetObject,
    and no query has acl, policy, location, versioning, tagging nor uploads."""
    fake = h.s3()
    out = h.run(fake.transport, s3_target())

    assert paths(out.db) == EXPECTED_PATHS
    assert fake.requests
    assert {r.method for r in fake.requests} == {"GET"}
    assert set(fake.operations) == {"ListObjectsV2", "GetObject"}
    forbidden = {"acl", "policy", "location", "versioning", "tagging", "uploads"}
    for req in fake.requests:
        assert not forbidden & set(_query(req)), req.url


class _SpyToy(ToyDriver):
    seen: list[ResolvedCredentials] = []

    def list_request(
        self, settings: Any, creds: ResolvedCredentials, *a: Any, **kw: Any
    ) -> Any:
        type(self).seen.append(creds)
        return super().list_request(settings, creds, *a, **kw)


def test_D2306_63_nenhuma_referencia_a_credencial_depois_do_run(
    h: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D2306-63: after run() the connector keeps no reference to the credentials: the
    ResolvedCredentials it handed the driver is cleared, and no attribute of the connector
    holds a credential value."""
    monkeypatch.setattr(_SpyToy, "seen", [])
    store = h.toy({"corpus/a.txt": CPF_TXT}, driver=_SpyToy)
    out = h.run(store.transport, toy_target())

    assert paths(out.db) == {"toy://caixa-sintetica/corpus/a.txt"}
    assert _SpyToy.seen
    for creds in _SpyToy.seen:
        assert len(creds) == 0
    assert out.connector._creds is None  # revision 6, R6-5
    for name, value in vars(out.connector).items():
        if isinstance(value, ResolvedCredentials):
            assert len(value) == 0, name
        assert h.toy_token not in repr(value), name

    fake = h.s3()
    out = h.run(fake.transport, s3_target())
    assert out.connector._creds is None
    blob = repr(vars(out.connector))
    for value in (h.creds.access_key_id, h.creds.secret_access_key):
        assert value not in blob


# ----------------------------------------------------------------------------
# Common layer and driver (section 0, DEC-10)
# ----------------------------------------------------------------------------


def test_D2306_65_camada_comum_nao_importa_driver_concreto() -> None:
    """D2306-65: object_storage_connector.py imports neither object_storage_s3,
    s3_addressing, s3_sigv4, botocore nor defusedxml (read with ast)."""
    tree = ast.parse(CONNECTOR_FILE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            imported.add(base)
            imported.update(f"{base}.{alias.name}" for alias in node.names)
    forbidden = (
        "object_storage_s3",
        "s3_addressing",
        "s3_sigv4",
        "botocore",
        "defusedxml",
    )
    for name in imported:
        for bad in forbidden:
            assert bad not in name.split("."), name


def test_D2306_67_driver_de_brinquedo_roda_na_camada_comum(
    h: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D2306-67: the toy driver (JSON listing, page of 2, toy:// path, fixed auth header)
    with 5 objects carrying a synthetic CPF -> 3 listings, 5 findings with toy:// paths, the
    inventory with the toy product and coverage complete; no S3 driver code runs."""

    def no_s3() -> Any:
        raise AssertionError("the S3 driver must not be built for a toy target")

    monkeypatch.setitem(object_storage_driver._REGISTRY, "s3", no_s3)
    monkeypatch.setitem(object_storage_driver._REGISTRY, "s3_compatible", no_s3)
    objects = {f"corpus/f{i}.txt": CPF_TXT for i in range(5)}
    store = h.toy(objects)
    out = h.run(store.transport, toy_target())

    lists = [r for r in store.requests if "/list?" in r[1]]
    assert len(lists) == 3
    assert store.violations == []
    assert paths(out.db) == {f"toy://caixa-sintetica/corpus/f{i}.txt" for i in range(5)}
    assert len(out.db.inventories) == 1
    assert out.db.inventories[0]["product"] == "ToyStore"
    assert out.db.inventories[0]["source_type"] == "object_storage"
    ex = executive(out.db)
    assert ex["coverage"] == "complete"
    assert ex["engine"] == "toy"
    assert out.db.failures == []


# ----------------------------------------------------------------------------
# Revision 6: valid key without size (R6-2) and required keys per driver (R6-8)
# ----------------------------------------------------------------------------


def test_D2306_86_chave_valida_sem_tamanho_baixa_com_teto(h: Harness) -> None:
    """D2306-86 (R6-2): with the toy driver reporting size=None, a small object is scanned;
    one larger than max_object_bytes aborts in the stream and counts too_large (never
    size_mismatch), with objects_unknown_size and 0 bytes in bytes_not_scanned; a
    Content-Length above the ceiling does not consume the body."""
    objects = {
        "corpus/a.txt": CPF_TXT,
        "corpus/b.txt": CPF_TXT * 3,
        "corpus/c.txt": CPF_TXT,
    }
    store = h.toy(
        objects,
        driver=NoSizeToyDriver,
        store=StreamingToyStore,
        content_lengths={"corpus/c.txt": 10 * MIB},
    )
    out = h.run(store.transport, toy_target(max_object_bytes=100))

    assert paths(out.db) == {"toy://caixa-sintetica/corpus/a.txt"}
    assert store.delivered("corpus/c.txt") == 0
    assert store.delivered("corpus/b.txt") < len(objects["corpus/b.txt"])
    ex = executive(out.db)
    assert ex["not_scanned_by_reason"] == {"too_large": 2}
    assert ex["objects_unknown_size"] == 2
    assert ex["bytes_not_scanned"] == 0
    assert ex["objects_scanned"] == 1
    summary = skipped_detail(out.db)
    assert "too_large=2" in summary
    assert "size_mismatch=0" in summary


def test_D2306_86_sem_tamanho_passar_do_saldo_e_over_budget(h: Harness) -> None:
    """D2306-86 (R6-2): without a size, passing the max_download_bytes balance in the stream
    counts over_budget, and the bytes read enter the budget."""
    objects = {"corpus/a.txt": CPF_TXT, "corpus/d.txt": CPF_TXT}
    store = h.toy(objects, driver=NoSizeToyDriver, store=StreamingToyStore)
    out = h.run(store.transport, toy_target(max_download_bytes=len(CPF_TXT) + 20))

    assert paths(out.db) == {"toy://caixa-sintetica/corpus/a.txt"}
    ex = executive(out.db)
    assert ex["not_scanned_by_reason"] == {"over_budget": 1}
    assert ex["objects_unknown_size"] == 1
    assert out.db.details("limit_reached") == [
        "max_download_bytes reached; 1 objects not downloaded"
    ]
    assert "size_mismatch" not in out.db.reasons()


def test_D2306_87_chaves_obrigatorias_por_driver(h: Harness) -> None:
    """D2306-87 (R6-8): REQUIRED_KEYS is generic (name, driver); each driver declares its
    required_keys, checked before settings(): a toy target without bucket runs; an s3 target
    without bucket (or region) gives config_error "missing required key: <key>" and zero
    requests."""
    from connectors.object_storage_driver import get_driver

    assert connector_module().REQUIRED_KEYS == ["name", "driver"]
    assert get_driver("s3").required_keys == ("bucket", "region")
    # Revision 6b: endpoint_url keeps its own driver message, so it is not a required key.
    assert get_driver("s3_compatible").required_keys == ("bucket", "region")
    for key in ("bucket", "region"):
        fake = h.s3()
        target = s3_target()
        del target[key]
        out = h.run(fake.transport, target)
        assert out.db.details("config_error") == [f"missing required key: {key}"], key
        assert fake.requests == [], key

    fake = h.minio()
    target = compat_target()
    del target["endpoint_url"]
    out = h.run(fake.transport, target)
    assert out.db.details("config_error") == [
        "endpoint_url is required by driver s3_compatible"
    ]
    assert fake.requests == []

    store = h.toy({"corpus/a.txt": CPF_TXT})
    target = toy_target()
    assert "bucket" not in target
    ok = h.run(store.transport, target)
    assert ok.db.failures == []
    assert paths(ok.db) == {"toy://caixa-sintetica/corpus/a.txt"}
