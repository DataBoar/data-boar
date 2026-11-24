"""Driver contract, registry and S3 driver of the ``object_storage`` reader (task 2306.1).

Source: ``docs/desenho/2306.md``, sections 0, 2, 5, 7, 10 and 11.

- ``test_D2306_64_*``: the driver registry (D2306-64). The conversion of the ``KeyError``
  into ``config_error`` belongs to the connector of task 2306.2 (D-24, A-19).
- ``test_extra_*``: tests beyond the D-n list, written before the code because task 2306.1
  implements these parts (``ResolvedCredentials``, ``S3Driver`` with the listing reader and
  the error table) while their D-n tests (D-40 .. D-47, D-56, D-57) drive the connector of
  task 2306.2. They exercise the driver alone, against the simulated S3 of
  ``tests/s3_fake.py`` with its independent SigV4 oracle. No network.
"""

from __future__ import annotations

import copy
import dataclasses
import operator
import pickle
import secrets
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import pytest

from connectors import object_storage_driver
from connectors.object_storage_driver import (
    DriverConfigError,
    DriverProtocolError,
    DriverSettings,
    ErrorClass,
    ListPage,
    ObjectEntry,
    PreparedGet,
    ResolvedCredentials,
    get_driver,
)
from connectors.object_storage_s3 import S3Driver, S3Settings
from connectors.s3_addressing import object_storage_host, resolve_location
from tests.object_storage_toy_driver import ToyDriver, register_toy_driver
from tests.s3_fake import AWS_NS, FakeS3, new_credentials

BUCKET = "databoar-sintetico"
REGION = "sa-east-1"
AWS_HOST = f"{BUCKET}.s3.{REGION}.amazonaws.com"
MINIO = "https://minio.lab.example:9000"
T0 = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)


def _marker() -> str:
    return "SYNTHMK" + secrets.token_hex(6)


@pytest.fixture
def registry_snapshot() -> Iterator[None]:
    saved = dict(object_storage_driver._REGISTRY)
    try:
        yield
    finally:
        object_storage_driver._REGISTRY.clear()
        object_storage_driver._REGISTRY.update(saved)


def _cfg(**extra: Any) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "name": "bucket-sintetico",
        "type": "object_storage",
        "driver": "s3",
        "bucket": BUCKET,
        "region": REGION,
    }
    cfg.update(extra)
    return cfg


def _compat(**extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "driver": "s3_compatible",
        "endpoint_url": MINIO,
        "region": "auto",
    }
    base.update(extra)
    return _cfg(**base)


COMPAT = S3Driver("s3_compatible")


def _creds(with_token: bool = True) -> tuple[Any, ResolvedCredentials]:
    raw = new_credentials(with_token=with_token)
    values = {
        "access_key_id_from_env": raw.access_key_id,
        "secret_access_key_from_env": raw.secret_access_key,
    }
    if raw.session_token:
        values["session_token_from_env"] = raw.session_token
    return raw, ResolvedCredentials(values)


# ----------------------------------------------------------------------------
# D2306-64: registry
# ----------------------------------------------------------------------------


def test_D2306_64_get_driver_s3_e_nomes_desconhecidos(registry_snapshot: None) -> None:
    driver = get_driver("s3")
    assert isinstance(driver, S3Driver)
    assert driver.name == "s3"
    compat = get_driver("s3_compatible")
    assert isinstance(compat, S3Driver)
    assert compat.name == "s3_compatible"

    for name in ("azure_blob", "gcs"):
        with pytest.raises(KeyError) as info:
            get_driver(name)
        assert info.value.args[0] == f"driver {name} is not available yet"

    mark = _marker()
    for name in ("x", "", "ftp", mark):
        with pytest.raises(KeyError) as info:
            get_driver(name)
        assert info.value.args[0] == "driver must be one of: s3, s3_compatible"


def test_D2306_64_lista_da_mensagem_vem_do_registro(registry_snapshot: None) -> None:
    register_toy_driver()
    assert isinstance(get_driver("toy"), ToyDriver)
    with pytest.raises(KeyError) as info:
        get_driver("x")
    assert info.value.args[0] == "driver must be one of: s3, s3_compatible, toy"
    with pytest.raises(KeyError) as info:
        get_driver("azure_blob")
    assert info.value.args[0] == "driver azure_blob is not available yet"


def test_D2306_64_registro_guarda_fabrica_e_cria_instancia_nova(
    registry_snapshot: None,
) -> None:
    calls: list[int] = []

    def factory() -> Any:
        calls.append(1)
        return ToyDriver()

    object_storage_driver.register_driver("toy", factory)
    assert calls == []  # registering never instantiates
    first, second = get_driver("toy"), get_driver("toy")
    assert calls == [1, 1]
    assert first is not second


def test_D2306_64_importar_o_registro_nao_importa_o_driver_s3() -> None:
    import subprocess
    import sys

    code = (
        "import sys, connectors.object_storage_driver as d\n"
        "assert 'connectors.object_storage_s3' not in sys.modules\n"
        "assert 'botocore' not in sys.modules\n"
        "assert 'connectors.s3_sigv4' not in sys.modules\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert result.returncode == 0, result.stderr


# ----------------------------------------------------------------------------
# Extra: ResolvedCredentials (section 0, revision 3)
# ----------------------------------------------------------------------------


def test_extra_resolved_credentials_le_por_nome_e_nao_mostra_valores() -> None:
    raw, creds = _creds(with_token=False)
    assert creds["access_key_id_from_env"] == raw.access_key_id
    assert creds.get("session_token_from_env") is None
    assert "session_token_from_env" not in creds
    assert sorted(creds) == ["access_key_id_from_env", "secret_access_key_from_env"]
    assert len(creds) == 2
    for text in (repr(creds), str(creds), f"{creds}", f"{creds!r}"):
        assert raw.access_key_id not in text
        assert raw.secret_access_key not in text
        assert text.startswith("<ResolvedCredentials redacted keys=")
        assert "access_key_id_from_env" in text


def test_extra_resolved_credentials_copia_o_mapa_recebido() -> None:
    raw = new_credentials(with_token=False)
    source = {"access_key_id_from_env": raw.access_key_id}
    creds = ResolvedCredentials(source)
    source["access_key_id_from_env"] = "changed"
    assert creds["access_key_id_from_env"] == raw.access_key_id
    with pytest.raises(TypeError):
        operator.setitem(creds, "access_key_id_from_env", "x")


def test_extra_resolved_credentials_sem_igualdade_por_valor_nem_pickle() -> None:
    raw = new_credentials(with_token=False)
    values = {"access_key_id_from_env": raw.access_key_id}
    a, b = ResolvedCredentials(values), ResolvedCredentials(dict(values))
    assert a != b
    assert a == a
    assert a != dict(values)
    with pytest.raises(TypeError):
        pickle.dumps(a)
    with pytest.raises(TypeError):
        copy.copy(a)


def test_extra_resolved_credentials_clear_apaga_os_valores() -> None:
    raw, creds = _creds(with_token=True)
    creds.clear()
    assert len(creds) == 0
    assert "secret_access_key_from_env" not in creds
    with pytest.raises(KeyError):
        creds["secret_access_key_from_env"]


# ----------------------------------------------------------------------------
# Extra: S3Driver settings, destination and identity
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("variant", ["s3", "s3_compatible"])
def test_extra_s3_driver_declara_o_contrato(variant: Any) -> None:
    driver = S3Driver(variant)
    assert driver.name == variant
    assert driver.max_page_size == 1000
    assert driver.max_key_bytes == 1024
    assert driver.credential_keys == (
        ("access_key_id_from_env", True),
        ("secret_access_key_from_env", True),
        ("session_token_from_env", False),
    )
    assert {
        "access_key_id",
        "secret_access_key",
        "session_token",
        "aws_access_key_id",
        "aws_secret_access_key",
        "aws_session_token",
    } <= driver.forbidden_inline_keys


def test_extra_s3_settings_congelado_e_igual_ao_enderecamento() -> None:
    driver = S3Driver()
    settings = driver.settings(_cfg())
    assert isinstance(settings, S3Settings)
    assert isinstance(settings, DriverSettings)
    assert settings.bucket == BUCKET
    assert settings.region == REGION
    assert settings.endpoint_url is None
    assert settings.location == resolve_location(_cfg())
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(settings, "bucket", "other")

    endpoint = COMPAT.settings(_compat())
    assert isinstance(endpoint, S3Settings)
    assert endpoint.endpoint_url == MINIO
    assert endpoint.location == resolve_location(_compat())
    assert endpoint.location.addressing == "path"


def test_extra_s3_settings_invalido_vira_driver_config_error_sem_ecoar() -> None:
    mark = _marker()
    for driver, cfg in (
        (S3Driver(), _cfg(bucket=f"Bad_{mark}")),
        (S3Driver(), _cfg(endpoint_url=f"https://{mark}.example")),
        (COMPAT, _compat(endpoint_url=f"https://u:{mark}@minio.lab.example")),
        (COMPAT, _compat(endpoint=f"https://{mark}.example")),
        (COMPAT, _compat(addressing_style=mark)),
        (S3Driver(), _cfg(prefix=f"/{mark}")),
        # The driver name in cfg must match the variant (no silent switch).
        (S3Driver(), _compat()),
        (COMPAT, _cfg()),
    ):
        with pytest.raises(DriverConfigError) as info:
            driver.settings(cfg)
        assert mark not in str(info.value)
        assert mark not in repr(info.value)


def test_extra_s3_destino_unico_e_host_para_o_loader() -> None:
    driver = S3Driver()
    assert driver.destination(driver.settings(_cfg())) == f"https://{AWS_HOST}"
    assert (
        COMPAT.destination(COMPAT.settings(_compat()))
        == "https://minio.lab.example:9000"
    )
    assert (
        COMPAT.destination(COMPAT.settings(_compat(addressing_style="virtual")))
        == f"https://{BUCKET}.minio.lab.example:9000"
    )
    for drv, cfg in (
        (driver, _cfg()),
        (COMPAT, _compat()),
        (COMPAT, _compat(addressing_style="virtual")),
    ):
        assert drv.destination_host(cfg) == object_storage_host(cfg) != ""
    assert driver.destination_host(_cfg(bucket="x_y")) == ""
    assert driver.destination_host(_cfg(endpoint_url=MINIO)) == ""
    assert COMPAT.destination_host(_compat(endpoint_url=None)) == ""


def test_extra_s3_caminho_exibido_e_identidade_do_inventario() -> None:
    driver = S3Driver()
    aws = driver.settings(_cfg())
    compat = COMPAT.settings(_compat())
    for drv, settings in ((driver, aws), (COMPAT, compat)):
        assert (
            drv.display_path(settings, "corpus/sub/a b.txt")
            == f"s3://{BUCKET}/corpus/sub/a b.txt"
        )
    assert driver.inventory_identity(aws) == {
        "product": "Amazon S3",
        "protocol_or_api_version": "S3 ListObjectsV2",
        "engine": "s3",
        "bucket": BUCKET,
        "region": REGION,
        "addressing": "virtual",
    }
    # D2306-78: an AWS host behind s3_compatible is accepted and stays S3-compatible.
    on_aws = COMPAT.settings(
        _compat(endpoint_url="https://s3.sa-east-1.amazonaws.com", region=REGION)
    )
    assert COMPAT.inventory_identity(on_aws)["product"] == "S3-compatible"
    assert COMPAT.inventory_identity(compat) == {
        "product": "S3-compatible",
        "protocol_or_api_version": "S3 ListObjectsV2",
        "engine": "s3",
        "bucket": BUCKET,
        "region": "auto",
        "addressing": "path",
        "endpoint_host": "minio.lab.example",
    }


# ----------------------------------------------------------------------------
# Extra: S3Driver requests, signed and accepted by the simulator's oracle
# ----------------------------------------------------------------------------

HARD_KEYS = [
    "corpus/a.txt",
    "corpus/a b+c%d.txt",
    "corpus/ação/日本/😀.txt",
    "corpus/[1]#?=&~.txt",
    "corpus//dup.txt",
    "corpus/.oculto.txt",
    "corpus/..x.txt",
    "corpus/x.",
    "corpus/a\x01.txt",
]


@pytest.mark.parametrize("with_token", [True, False])
@pytest.mark.parametrize("mode", ["virtual", "compat-virtual", "endpoint"])
def test_extra_s3_listagem_paginada_e_download_assinados(
    mode: str, with_token: bool
) -> None:
    raw, creds = _creds(with_token=with_token)
    driver = S3Driver()
    if mode == "virtual":
        cfg, host, addressing, region = _cfg(), AWS_HOST, "virtual", REGION
    elif mode == "compat-virtual":
        driver = COMPAT
        cfg = _compat(
            endpoint_url="https://store.lab.example",
            addressing_style="virtual",
            region="us-east-1",
        )
        host, addressing, region = f"{BUCKET}.store.lab.example", "virtual", "us-east-1"
    else:
        driver = COMPAT
        cfg = _compat(region="us-east-1")
        host, addressing, region = "minio.lab.example:9000", "path", "us-east-1"
    bucket = cfg["bucket"]
    objects = {k: f"data:{k}".encode() for k in HARD_KEYS}
    objects["outro/fora.txt"] = b"out of prefix"
    fake = FakeS3(
        bucket,
        objects,
        host=host,
        addressing=addressing,
        region=region,
        page_size=2,
        access_key_id=raw.access_key_id,
        session_token=raw.session_token,
        secret_access_key=raw.secret_access_key,
    )
    settings = driver.settings(cfg)
    listed: list[ObjectEntry] = []
    token: str | None = None
    pages = 0
    with httpx.Client(transport=fake.transport, follow_redirects=False) as client:
        while True:
            prep = driver.list_request(settings, creds, "corpus/", token, 2, T0)
            assert isinstance(prep, PreparedGet)
            assert prep.url.startswith(driver.destination(settings) + "/")
            resp = client.get(prep.url, headers=prep.headers)
            assert resp.status_code == 200, (fake.auth_failures, resp.text)
            page = driver.parse_list(resp.content)
            assert isinstance(page, ListPage)
            listed.extend(page.entries)
            pages += 1
            if not page.truncated:
                break
            assert page.next_token
            token = page.next_token
        for entry in listed:
            prep = driver.get_request(settings, creds, entry.key, T0)
            got = client.get(prep.url, headers=prep.headers)
            assert got.status_code == 200, (entry.key, fake.auth_failures)
            assert got.content == objects[entry.key]
    assert sorted(e.key for e in listed) == sorted(HARD_KEYS)
    assert all(e.size == len(objects[e.key]) for e in listed)
    assert pages == 5
    assert fake.auth_failures == []
    assert fake.violations == []
    assert sorted(fake.fetched) == sorted(HARD_KEYS)
    for req in fake.requests:
        assert req.method == "GET"
        assert req.host == host.partition(":")[0]
    for req in fake.requests[:pages]:
        query = dict(p.split("=", 1) for p in req.raw_query.split("&"))
        assert query["list-type"] == "2"
        assert query["prefix"] == "corpus%2F"
        assert query["max-keys"] == "2"
        assert query["encoding-type"] == "url"
        assert "delimiter" not in query
    assert "continuation-token" not in fake.requests[0].raw_query
    assert all("continuation-token=" in r.raw_query for r in fake.requests[1:pages])


def test_extra_s3_requisicao_nao_carrega_segredo() -> None:
    raw, creds = _creds(with_token=True)
    driver = S3Driver()
    settings = driver.settings(_cfg())
    for prep in (
        driver.list_request(settings, creds, "corpus/", None, 1000, T0),
        driver.get_request(settings, creds, "corpus/a.txt", T0),
    ):
        flat = prep.url + " ".join(f"{k}:{v}" for k, v in prep.headers.items())
        assert raw.secret_access_key not in flat
        assert raw.access_key_id not in prep.url
        assert str(raw.session_token) not in prep.url


# ----------------------------------------------------------------------------
# Extra: listing reader (section 7)
# ----------------------------------------------------------------------------


def _listing(
    contents: str,
    *,
    ns: str | None = AWS_NS,
    truncated: str = "false",
    token: str | None = None,
    encoding: str | None = "url",
) -> bytes:
    xmlns = f' xmlns="{ns}"' if ns else ""
    parts = [f'<?xml version="1.0" encoding="UTF-8"?><ListBucketResult{xmlns}>']
    parts.append(f"<Name>{BUCKET}</Name>")
    if encoding:
        parts.append(f"<EncodingType>{encoding}</EncodingType>")
    parts.append(f"<IsTruncated>{truncated}</IsTruncated>")
    if token is not None:
        parts.append(f"<NextContinuationToken>{token}</NextContinuationToken>")
    parts.append(contents)
    parts.append("</ListBucketResult>")
    return "".join(parts).encode("utf-8")


def _item(key: str, size: str | None) -> str:
    size_xml = "" if size is None else f"<Size>{size}</Size>"
    return f"<Contents><Key>{key}</Key>{size_xml}</Contents>"


def test_extra_parse_list_decodifica_com_unquote_plus() -> None:
    driver = S3Driver()
    body = _listing(
        _item("corpus/a+b%2Bc%25d.txt", "3") + _item("corpus/x%26y.txt", "0"),
        truncated="true",
        token="tok+/=",
    )
    page = driver.parse_list(body)
    assert page == ListPage(
        [ObjectEntry("corpus/a b+c%d.txt", 3), ObjectEntry("corpus/x&y.txt", 0)],
        "tok+/=",
        True,
    )


def test_extra_parse_list_sem_encoding_type_usa_a_chave_como_veio() -> None:
    page = S3Driver().parse_list(_listing(_item("corpus/a+b.txt", "1"), encoding=None))
    assert page.entries == [ObjectEntry("corpus/a+b.txt", 1)]
    assert page.next_token is None
    assert page.truncated is False


def test_extra_parse_list_sem_namespace_e_aceito() -> None:
    page = S3Driver().parse_list(_listing(_item("corpus/a.txt", "5"), ns=None))
    assert page.entries == [ObjectEntry("corpus/a.txt", 5)]


@pytest.mark.parametrize("size", [None, "-1", "abc", "1.5", "", " 7"])
def test_D2306_82_entrada_sem_size_valido_vira_chave_none(size: str | None) -> None:
    body = _listing(
        _item("corpus/ok-1.txt", "4")
        + _item("corpus/a.txt", size)
        + _item("corpus/ok-2.txt", "0")
    )
    page = S3Driver().parse_list(body)
    assert page.entries == [
        ObjectEntry("corpus/ok-1.txt", 4),
        ObjectEntry(None, None),
        ObjectEntry("corpus/ok-2.txt", 0),
    ]


def test_D2306_82_size_com_muitos_digitos_vira_chave_none() -> None:
    """Size with 5000 digits should be treated as malformed (int() would overflow),
    not raise ValueError. The entry should become ObjectEntry(None, None)."""
    size_5000 = "1" + "0" * 4999  # 5000 digits
    body = _listing(
        _item("corpus/ok-1.txt", "4")
        + _item("corpus/a.txt", size_5000)
        + _item("corpus/ok-2.txt", "0")
    )
    page = S3Driver().parse_list(body)
    assert page.entries == [
        ObjectEntry("corpus/ok-1.txt", 4),
        ObjectEntry(None, None),
        ObjectEntry("corpus/ok-2.txt", 0),
    ]


@pytest.mark.parametrize(
    "raw_key", ["corpus/%FF.txt", "corpus/%C3.txt", "corpus/%ZZ%E9.txt"]
)
def test_D2306_82_chave_que_nao_decodifica_vira_none(raw_key: str) -> None:
    body = _listing(
        _item("corpus/ok-1.txt", "4")
        + _item(raw_key, "3")
        + _item("corpus/ok-2.txt", "1")
    )
    page = S3Driver().parse_list(body)
    assert page.entries == [
        ObjectEntry("corpus/ok-1.txt", 4),
        ObjectEntry(None, 3),
        ObjectEntry("corpus/ok-2.txt", 1),
    ]


@pytest.mark.parametrize(
    "body",
    [
        b'<?xml version="1.0"?><ListBucketResult><Name>x</Name><Contents><Key>a',
        b"not xml at all",
        b"",
        _listing(_item("corpus/a.txt", "1"), truncated="maybe"),
        # D2306-42 (revision 5 arbitration): a DOCTYPE without any entity is refused too.
        (
            b'<?xml version="1.0"?><!DOCTYPE ListBucketResult>'
            b"<ListBucketResult><IsTruncated>false</IsTruncated>"
            b"<Contents><Key>a</Key><Size>1</Size></Contents></ListBucketResult>"
        ),
        # D2306-42: wrong root element, with and without the AWS namespace.
        b"<Error><IsTruncated>false</IsTruncated></Error>",
        _listing(_item("corpus/a.txt", "1")).replace(
            b"ListBucketResult", b"ListAllMyBucketsResult"
        ),
        (
            b'<?xml version="1.0"?><!DOCTYPE ListBucketResult [<!ENTITY boom "boom">]>'
            b"<ListBucketResult><IsTruncated>false</IsTruncated>"
            b"<Contents><Key>&boom;</Key><Size>1</Size></Contents></ListBucketResult>"
        ),
        (
            b'<?xml version="1.0"?><!DOCTYPE ListBucketResult [<!ENTITY ext SYSTEM '
            b'"file:///etc/hostname">]><ListBucketResult><IsTruncated>false'
            b"</IsTruncated><Contents><Key>&ext;</Key><Size>1</Size></Contents>"
            b"</ListBucketResult>"
        ),
    ],
)
def test_extra_parse_list_resposta_ruim_e_driver_protocol_error(body: bytes) -> None:
    with pytest.raises(DriverProtocolError) as info:
        S3Driver().parse_list(body)
    assert str(info.value) == "malformed listing response"


def test_D2306_85_namespace_nao_muda_a_leitura_da_listagem() -> None:
    """Section 7, revision 5 arbitration: elements are read by local name only, so the
    AWS namespace, no namespace and any other namespace give the same page."""
    contents = (
        _item("corpus/a+b%2Bc.txt", "3")
        + _item("corpus/%FF.txt", "2")
        + _item("corpus/sem-size.txt", None)
    )
    driver = S3Driver()
    pages = [
        driver.parse_list(_listing(contents, ns=ns, truncated="true", token="t+/="))
        for ns in (AWS_NS, None, "http://example.invalid/ns")
    ]
    expected = ListPage(
        [
            ObjectEntry("corpus/a b+c.txt", 3),
            ObjectEntry(None, 2),
            ObjectEntry(None, None),
        ],
        "t+/=",
        True,
    )
    assert pages == [expected, expected, expected]


# ----------------------------------------------------------------------------
# Extra: S3 error table (sections 6 and 11)
# ----------------------------------------------------------------------------


def _error_body(code: str, extra: str = "") -> bytes:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><Error><Code>{code}</Code>'
        f"<Message>m</Message>{extra}<RequestId>R1</RequestId></Error>"
    ).encode()


@pytest.mark.parametrize(
    ("during", "status", "code", "expected"),
    [
        (
            "list",
            403,
            "AccessDenied",
            ("permission_denied", "AccessDenied", False, True),
        ),
        (
            "list",
            403,
            "AllAccessDisabled",
            ("permission_denied", "AllAccessDisabled", False, True),
        ),
        ("list", 404, "NoSuchBucket", ("not_found", "NoSuchBucket", False, True)),
        (
            "list",
            403,
            "InvalidAccessKeyId",
            ("auth_failed", "InvalidAccessKeyId", False, True),
        ),
        (
            "list",
            403,
            "SignatureDoesNotMatch",
            ("auth_failed", "SignatureDoesNotMatch", False, True),
        ),
        ("list", 400, "ExpiredToken", ("auth_failed", "ExpiredToken", False, True)),
        ("list", 400, "InvalidToken", ("auth_failed", "InvalidToken", False, True)),
        (
            "list",
            400,
            "TokenRefreshRequired",
            ("auth_failed", "TokenRefreshRequired", False, True),
        ),
        (
            "list",
            403,
            "RequestTimeTooSkewed",
            ("auth_failed", "RequestTimeTooSkewed", False, True),
        ),
        (
            "get",
            403,
            "SignatureDoesNotMatch",
            ("auth_failed", "SignatureDoesNotMatch", False, True),
        ),
        (
            "list",
            301,
            "PermanentRedirect",
            ("config_error", "PermanentRedirect", False, True),
        ),
        (
            "list",
            400,
            "AuthorizationHeaderMalformed",
            ("config_error", "AuthorizationHeaderMalformed", False, True),
        ),
        ("list", 503, "SlowDown", ("throttled", "SlowDown", True, True)),
        ("get", 403, "AccessDenied", ("download_failed", "AccessDenied", False, False)),
        ("get", 404, "NoSuchKey", ("download_failed", "NoSuchKey", False, False)),
        (
            "get",
            400,
            "InvalidRequest",
            ("download_failed", "InvalidRequest", False, False),
        ),
    ],
)
def test_extra_classify_error_segue_a_tabela(
    during: Any, status: int, code: str, expected: tuple[Any, ...]
) -> None:
    got = S3Driver().classify_error(status, {}, _error_body(code), during=during)
    assert isinstance(got, ErrorClass)
    assert tuple(got)[:4] == expected
    assert got.message


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_extra_classify_error_5xx_repete(status: int) -> None:
    driver = S3Driver()
    listing = driver.classify_error(
        status, {}, _error_body("InternalError"), during="list"
    )
    assert listing.retryable is True
    assert listing.ends_target is True
    assert listing.reason in ("unreachable", "throttled")
    if status != 503:
        assert listing.reason == "unreachable"
    got = driver.classify_error(status, {}, b"", during="get")
    assert (got.reason, got.retryable, got.ends_target) == (
        "download_failed",
        True,
        False,
    )


@pytest.mark.parametrize("status", [301, 302, 307, 308])
def test_extra_classify_error_redirect_na_listagem(status: int) -> None:
    got = S3Driver().classify_error(
        status,
        {"Location": "https://evil.example/"},
        _error_body("TemporaryRedirect"),
        during="list",
    )
    assert got.retryable is False
    assert got.ends_target is True
    assert got.reason == "scope_violation"


def test_extra_classify_error_codigo_fora_do_vocabulario_nao_sai() -> None:
    driver = S3Driver()
    mark = _marker()
    for body in (
        _error_body("Xyz"),
        _error_body(mark),
        b"",
        b"<Error><Code>AccessDenied",
        b'<?xml version="1.0"?><!DOCTYPE e [<!ENTITY b "AccessDenied">]><Error><Code>&b;</Code></Error>',
        # The code past the 64 KiB read cap is never read.
        b"<Error><!--" + b"x" * (64 * 1024) + b"--><Code>AccessDenied</Code></Error>",
    ):
        got = driver.classify_error(400, {}, body, during="get")
        assert got.code is None
        assert mark not in repr(got)
        assert got.message == "S3 error HTTP 400"


def test_extra_classify_error_corpo_com_eco_nao_vaza_marcadores() -> None:
    raw = new_credentials(with_token=True)
    echo = (
        f"<AWSAccessKeyId>{raw.access_key_id}</AWSAccessKeyId>"
        f"<StringToSign>AWS4-HMAC-SHA256 {raw.session_token}</StringToSign>"
        f"<CanonicalRequest>GET / x-amz-security-token:{raw.session_token}</CanonicalRequest>"
    )
    got = S3Driver().classify_error(
        403, {}, _error_body("SignatureDoesNotMatch", echo), during="list"
    )
    assert got.code == "SignatureDoesNotMatch"
    for value in (raw.access_key_id, str(raw.session_token)):
        assert value not in repr(got)


# ----------------------------------------------------------------------------
# D2306-81: fixed driver messages; D2306-84: misnamed keys of the S3 driver
# ----------------------------------------------------------------------------

S3_TABLE_CODES = [
    ("list", 403, "AccessDenied"),
    ("list", 403, "AllAccessDisabled"),
    ("list", 404, "NoSuchBucket"),
    ("list", 403, "InvalidAccessKeyId"),
    ("list", 403, "SignatureDoesNotMatch"),
    ("list", 400, "ExpiredToken"),
    ("list", 400, "InvalidToken"),
    ("list", 400, "TokenRefreshRequired"),
    ("list", 403, "RequestTimeTooSkewed"),
    ("list", 301, "PermanentRedirect"),
    ("list", 400, "AuthorizationHeaderMalformed"),
    ("list", 503, "SlowDown"),
    ("get", 403, "AccessDenied"),
    ("get", 404, "NoSuchKey"),
    ("get", 400, "InvalidRequest"),
]


@pytest.mark.parametrize(("during", "status", "code"), S3_TABLE_CODES)
def test_D2306_81_mensagem_fixa_sem_trecho_do_corpo_nem_do_cabecalho(
    during: Any, status: int, code: str
) -> None:
    mark = _marker()
    body = _error_body(code, f"<Detail>{mark}</Detail><HostId>{mark}</HostId>")
    headers = {"x-amz-request-id": mark, "Server": mark, "Location": f"https://{mark}/"}
    driver = S3Driver()
    got = driver.classify_error(status, headers, body, during=during)
    assert isinstance(got.message, str)
    assert got.message
    assert mark not in got.message
    assert mark not in repr(got)
    # Same input, same text: the message is fixed, not built from the response.
    again = driver.classify_error(
        status, {"x-amz-request-id": "other"}, _error_body(code), during=during
    )
    assert again.message == got.message
    if code == "RequestTimeTooSkewed":
        assert "clock skew between this host and the server" in got.message
    if code in ("PermanentRedirect", "AuthorizationHeaderMalformed"):
        assert "bucket is not in region" in got.message
    if during == "get" and code in ("AccessDenied", "NoSuchKey", "InvalidRequest"):
        assert code in got.message


def test_D2306_81_frases_do_s3_so_existem_no_modulo_do_driver_s3() -> None:
    root = Path(__file__).resolve().parents[1] / "connectors"
    phrases = ("bucket is not in region", "clock skew")
    s3_text = (root / "object_storage_s3.py").read_text(encoding="utf-8")
    for phrase in phrases:
        assert phrase in s3_text
    for name in ("object_storage_driver.py", "object_storage_connector.py"):
        path = root / name
        if not path.exists():  # the connector module arrives in task 2306.2
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            assert phrase not in text, (name, phrase)


def test_D2306_84_misnamed_keys_do_s3_e_do_s3_compatible() -> None:
    hint = "use endpoint_url"
    assert dict(S3Driver("s3").misnamed_keys) == {
        "endpoint": hint,
        "url": hint,
        "base_url": hint,
        "host": hint,
        "endpoint_url": "use driver s3_compatible",
    }
    assert dict(S3Driver("s3_compatible").misnamed_keys) == {
        "endpoint": hint,
        "url": hint,
        "base_url": hint,
        "host": hint,
    }
    # The toy driver keeps using ``host``: it is not one of its misnamed keys.
    assert "host" not in getattr(ToyDriver, "misnamed_keys", {})
