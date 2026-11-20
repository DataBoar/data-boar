"""Dev tests D2306-1 .. D2306-8 and D2306-76 .. D2306-78: S3 addressing, task 2306.1.

Source: ``docs/desenho/2306.md`` revision 4, sections 1, 2 and 2a and the TDD specification
(``connectors/s3_addressing.py``; drivers ``s3`` and ``s3_compatible``). Pure functions,
no network. Every error message must be fixed text: the tests feed values that carry a
run-time marker and check the marker never comes back in ``str(exc)``.
"""

from __future__ import annotations

import ast
import secrets
from pathlib import Path
from typing import Any

import pytest

from connectors.s3_addressing import (
    S3ConfigError,
    S3Location,
    object_storage_host,
    resolve_location,
    validate_prefix,
)

BUCKET = "databoar-sintetico"
DOTTED = "databoar.sintetico"
REGION = "sa-east-1"
MINIO = "https://minio.lab.example:9000"


def _marker() -> str:
    return "SYNTHMK" + secrets.token_hex(6)


def _cfg(**extra: Any) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "name": "bucket-sintetico",
        "type": "object_storage",
        "driver": "s3",
        "bucket": BUCKET,
        "region": REGION,
    }
    for key, value in extra.items():
        if value is _DROP:
            cfg.pop(key, None)
        else:
            cfg[key] = value
    return cfg


_DROP = object()


def _compat(**extra: Any) -> dict[str, Any]:
    """A ``driver: s3_compatible`` target (endpoint_url required, generic region rule)."""
    base: dict[str, Any] = {
        "driver": "s3_compatible",
        "endpoint_url": MINIO,
        "region": "us-east-1",
    }
    base.update(extra)
    return _cfg(**base)


def _refused(cfg: dict[str, Any], *, secret: str | None = None) -> S3ConfigError:
    with pytest.raises(S3ConfigError) as info:
        resolve_location(cfg)
    if secret is not None:
        assert secret not in str(info.value)
        assert secret not in repr(info.value)
    return info.value


def test_D2306_1_driver_s3_usa_estilo_virtual_na_aws() -> None:
    loc = resolve_location(_cfg())
    assert loc == S3Location(
        host=f"{BUCKET}.s3.{REGION}.amazonaws.com",
        port=None,
        host_header=f"{BUCKET}.s3.{REGION}.amazonaws.com",
        base_path="",
        addressing="virtual",
        region=REGION,
    )


def test_D2306_2_driver_s3_com_bucket_com_ponto_e_recusado() -> None:
    err = _refused(_cfg(bucket=DOTTED))
    assert str(err) == "bucket names with dots are not supported by driver s3"


def test_D2306_3_s3_compatible_usa_caminho_e_host_header_com_porta() -> None:
    loc = resolve_location(_compat())
    assert loc.host == "minio.lab.example"
    assert loc.port == 9000
    assert loc.host_header == "minio.lab.example:9000"
    assert loc.base_path == f"/{BUCKET}"
    assert loc.addressing == "path"
    assert loc.region == "us-east-1"
    assert resolve_location(_compat(addressing_style="path")) == loc
    # A bucket with a dot is fine in path style.
    assert resolve_location(_compat(bucket=DOTTED)).base_path == f"/{DOTTED}"

    for endpoint in (
        "https://minio.lab.example:443",
        "https://minio.lab.example",
        "https://minio.lab.example/",
        "https://MINIO.Lab.Example:443/",
    ):
        loc = resolve_location(_compat(endpoint_url=endpoint, region="auto"))
        assert loc.host == "minio.lab.example", endpoint
        assert loc.port is None, endpoint
        assert loc.host_header == "minio.lab.example", endpoint
        assert loc.base_path == f"/{BUCKET}", endpoint
        assert loc.addressing == "path", endpoint


@pytest.mark.parametrize(
    "bucket",
    [
        "Databoar-sintetico",  # upper case
        "databoar_sintetico",  # underscore
        "ab",  # 2 characters
        "a" * 64,  # 64 characters
        "databoar..sintetico",
        "databoar.-sintetico",
        "databoar-.sintetico",
        "192.168.10.20",  # IPv4 shape
        "-databoar",
        "databoar-",
        "",
        None,
        123,
        ["databoar-sintetico"],
    ],
)
@pytest.mark.parametrize("driver", ["s3", "s3_compatible"])
def test_D2306_4_bucket_invalido_e_recusado(bucket: Any, driver: str) -> None:
    cfg = _cfg(bucket=bucket) if driver == "s3" else _compat(bucket=bucket)
    _refused(cfg)


def test_D2306_4_bucket_ausente_e_recusado_sem_ecoar_valor() -> None:
    _refused(_cfg(bucket=_DROP))
    _refused(_compat(bucket=_DROP))
    mark = _marker().lower()
    _refused(_cfg(bucket=f"x_{mark}"), secret=mark)
    _refused(_compat(bucket=f"x_{mark}"), secret=mark)


def test_D2306_4_bucket_nos_limites_validos_e_aceito() -> None:
    for bucket in ("abc", "a" * 63, "a-b-c", "0databoar9"):
        assert resolve_location(_cfg(bucket=bucket)).region == REGION
    for bucket in ("abc", "a" * 63, "a.b-c.d", "0databoar9"):
        assert resolve_location(_compat(bucket=bucket)).base_path == f"/{bucket}"


@pytest.mark.parametrize(
    "region",
    [
        "cn-north-1",
        "cn-northwest-1",
        "us-east-1/x",
        "evil.example",
        "auto",
        "",
        None,
        7,
    ],
)
def test_D2306_5_regiao_invalida_no_driver_s3_e_recusada(region: Any) -> None:
    _refused(_cfg(region=region))


def test_D2306_5_regiao_ausente_e_recusada_e_no_s3_compatible_auto_e_aceita() -> None:
    _refused(_cfg(region=_DROP))
    _refused(_compat(region=_DROP))
    for region in ("us-east-1", "sa-east-1", "eu-central-2", "ap-southeast-1"):
        assert resolve_location(_cfg(region=region)).region == region
    for region in ("auto", "us-east-1", "garage", "r1"):
        assert resolve_location(_compat(region=region)).region == region
    for region in ("", "a" * 33, "us_east_1", "-auto", "auto-", "Auto", None):
        _refused(_compat(region=region))


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://minio.lab.example:9000",
        "ftp://minio.lab.example",
        "https://minio.lab.example:9000/x",
        "https://minio.lab.example:9000/?a=1",
        "https://minio.lab.example:9000/#frag",
        "https://:9000",
        "https://",
        "https://minio.lab.example:0",
        "https://minio.lab.example:65536",
        "minio.lab.example:9000",
        "",
        123,
        None,
    ],
)
def test_D2306_6_endpoint_url_invalido_e_recusado(endpoint: Any) -> None:
    _refused(_compat(endpoint_url=endpoint))


def test_D2306_6_endpoint_com_userinfo_e_recusado_sem_ecoar() -> None:
    mark = _marker()
    err = _refused(
        _compat(endpoint_url=f"https://user:{mark}@minio.lab.example:9000"),
        secret=mark,
    )
    assert "endpoint_url" in str(err)


@pytest.mark.parametrize("key", ["endpoint", "url", "base_url", "host"])
def test_D2306_6_chave_de_destino_com_outro_nome_e_recusada(key: str) -> None:
    mark = _marker()
    # A second destination key is never ignored, even with endpoint_url present.
    err = _refused(_compat(**{key: f"https://{mark}.example"}), secret=mark)
    assert "use endpoint_url" in str(err)
    # Driver s3 refuses it too (there it can never become a destination).
    _refused(_cfg(**{key: f"https://{mark}.example"}), secret=mark)


@pytest.mark.parametrize(
    "prefix",
    [
        "/corpus/",
        "corpus/\x00/",
        "corpus/\x1f",
        "corpus/\x7f",
        "corpus\n",
        ".",
        "..",
        "./corpus/",
        "corpus/../x/",
        "corpus/./x/",
        "corpus/..",
        "a" * 1025,
        "ç" * 513,  # 1026 bytes in UTF-8
        None,
        5,
        ["corpus/"],
    ],
)
def test_D2306_7_prefixo_invalido_e_recusado(prefix: Any) -> None:
    with pytest.raises(S3ConfigError):
        validate_prefix(prefix)


def test_D2306_7_prefixos_validos_sao_aceitos_como_vieram() -> None:
    for prefix in ("", "corpus/", "a b/ç/", ".hidden/", "..x/", "x./", "a" * 1024):
        assert validate_prefix(prefix) == prefix
    assert validate_prefix("ç" * 512) == "ç" * 512  # exactly 1024 bytes


def test_D2306_7_prefixo_invalido_nao_ecoa_o_valor() -> None:
    mark = _marker()
    with pytest.raises(S3ConfigError) as info:
        validate_prefix(f"/{mark}")
    assert mark not in str(info.value)


def test_D2306_8_object_storage_host_valido_e_invalido_sem_excecao() -> None:
    assert object_storage_host(_cfg()) == f"{BUCKET}.s3.{REGION}.amazonaws.com"
    assert object_storage_host(_compat(region="auto")) == "minio.lab.example"
    assert (
        object_storage_host(_compat(addressing_style="virtual"))
        == f"{BUCKET}.minio.lab.example"
    )
    invalid: list[dict[str, Any]] = [
        _cfg(bucket="Bad_Bucket"),
        _cfg(bucket=None),
        _cfg(bucket=DOTTED),
        _cfg(region="cn-north-1"),
        _cfg(endpoint_url=MINIO),
        _cfg(addressing_style="virtual"),
        _cfg(driver=_DROP),
        _cfg(driver="azure_blob"),
        _compat(endpoint_url=_DROP),
        _compat(endpoint_url="http://minio.lab.example"),
        _compat(endpoint_url=123),
        _compat(addressing_style="outro"),
        _compat(endpoint="https://evil.example"),
        _compat(host="evil.example"),
        {},
        {"bucket": BUCKET},
    ]
    for cfg in invalid:
        assert object_storage_host(cfg) == "", cfg


# ----------------------------------------------------------------------------
# Revision 4: two drivers (section 2a)
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "endpoint",
    [
        MINIO,
        "https://s3.sa-east-1.amazonaws.com",
        f"https://{BUCKET}.s3.{REGION}.amazonaws.com",
        "http://minio.lab.example",
        "",
        None,
    ],
)
def test_D2306_76_driver_s3_recusa_endpoint_url(endpoint: Any) -> None:
    mark = _marker()
    err = _refused(_cfg(endpoint_url=endpoint))
    assert str(err) == (
        "endpoint_url is not accepted by driver s3; use driver s3_compatible"
    )
    err = _refused(_cfg(endpoint_url=f"https://{mark}.example"), secret=mark)
    assert "use driver s3_compatible" in str(err)


@pytest.mark.parametrize("style", ["virtual", "path", "", None])
def test_D2306_76_driver_s3_recusa_addressing_style(style: Any) -> None:
    err = _refused(_cfg(addressing_style=style))
    assert "addressing_style" in str(err)


def test_D2306_77_s3_compatible_exige_endpoint_e_aceita_estilo_virtual() -> None:
    err = _refused(_compat(endpoint_url=_DROP))
    assert str(err) == "endpoint_url is required by driver s3_compatible"

    loc = resolve_location(
        _compat(endpoint_url="https://store.lab.example", addressing_style="virtual")
    )
    assert loc.host == f"{BUCKET}.store.lab.example"
    assert loc.host_header == f"{BUCKET}.store.lab.example"
    assert loc.base_path == ""
    assert loc.addressing == "virtual"
    loc = resolve_location(_compat(addressing_style="virtual"))
    assert loc.host_header == f"{BUCKET}.minio.lab.example:9000"
    assert loc.port == 9000

    # In virtual style a bucket with a dot would break the TLS host: refused.
    _refused(_compat(bucket=DOTTED, addressing_style="virtual"))
    mark = _marker()
    for style in ("outro", "Virtual", "", 1, None, mark):
        err = _refused(_compat(addressing_style=style), secret=mark)
        assert "addressing_style" in str(err)


def test_D2306_78_s3_compatible_nao_confere_host_da_aws() -> None:
    for endpoint in (
        "https://s3.sa-east-1.amazonaws.com",
        "https://s3.amazonaws.com",
        f"https://{BUCKET}.s3.{REGION}.amazonaws.com",
    ):
        loc = resolve_location(_compat(endpoint_url=endpoint, region=REGION))
        assert loc.host == endpoint.removeprefix("https://")
        assert loc.addressing == "path"
        assert loc.base_path == f"/{BUCKET}"


def _aws_literal_owners(path: Path) -> list[str]:
    """Names of the functions that hold a string literal with ``amazonaws.com``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    owners: list[str] = []

    def visit(node: ast.AST, owner: str) -> None:
        for child in ast.iter_child_nodes(node):
            name = owner
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = child.name
            if (
                isinstance(child, ast.Constant)
                and isinstance(child.value, str)
                and "amazonaws.com" in child.value
            ):
                owners.append(owner)
            visit(child, name)

    visit(tree, "<module>")
    return owners


def test_D2306_78_literal_amazonaws_so_na_montagem_do_host_do_driver_s3() -> None:
    root = Path(__file__).resolve().parents[1] / "connectors"
    addressing = root / "s3_addressing.py"
    tree = ast.parse(addressing.read_text(encoding="utf-8"))
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert "_aws_virtual_host" in names
    assert set(_aws_literal_owners(addressing)) <= {"_aws_virtual_host"}
    assert _aws_literal_owners(root / "object_storage_s3.py") == []
    # The builder really is the one that produces the s3 host.
    assert resolve_location(_cfg()).host == f"{BUCKET}.s3.{REGION}.amazonaws.com"
