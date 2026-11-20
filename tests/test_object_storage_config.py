"""Dev tests D2306-15 .. D2306-21 and D2306-66: loader and ``--validate-config`` gate.

Source: ``docs/desenho/2306.md``, section 3 ("Credenciais e loader", revision 2) and the TDD
specification. Task 2306.1. Only ``config.loader.normalize_config`` and
``main._validate_config_and_exit`` are driven; no network.

Every secret-looking value is built at run time with a ``SYNTH*`` marker, and each refusal
checks the marker never comes back in the message.
"""

from __future__ import annotations

import secrets
from collections.abc import Iterator
from typing import Any

import pytest

from config.loader import normalize_config
from connectors import object_storage_driver
from tests.object_storage_toy_driver import TOY_HOST, register_toy_driver
from tests.s3_fake import new_credentials

BUCKET = "databoar-sintetico"
REGION = "sa-east-1"
AWS_HOST = f"{BUCKET}.s3.{REGION}.amazonaws.com"
ENV_AK = "DATA_BOAR_S3_ACCESS_KEY_ID"
ENV_SK = "DATA_BOAR_S3_SECRET_ACCESS_KEY"
ENV_ST = "DATA_BOAR_S3_SESSION_TOKEN"
STRICT = "DATA_BOAR_CREDENTIAL_STRICT"
OPERATOR_HOSTS = "DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS"

# Section 3, step 1 (the S3 list; revision 2 = common list + driver list).
FORBIDDEN_S3 = [
    "access_key_id",
    "secret_access_key",
    "session_token",
    "aws_access_key_id",
    "aws_secret_access_key",
    "aws_session_token",
    "profile",
    "credentials",
    "pass",
    "password",
    "user",
    "username",
    "token",
    "client_secret",
    "api_key",
    "pass_from_env",
    "password_from_env",
    "user_from_env",
    "token_from_env",
    "client_secret_from_env",
    "api_key_from_env",
]


def _marker() -> str:
    return "SYNTHMK" + secrets.token_hex(6)


def _s3_target(**extra: Any) -> dict[str, Any]:
    target: dict[str, Any] = {
        "name": "bucket-sintetico",
        "type": "object_storage",
        "driver": "s3",
        "bucket": BUCKET,
        "region": REGION,
        "auth": {
            "access_key_id_from_env": ENV_AK,
            "secret_access_key_from_env": ENV_SK,
            "session_token_from_env": ENV_ST,
        },
    }
    target.update(extra)
    return target


def _config(target: dict[str, Any]) -> dict[str, Any]:
    return {"targets": [target], "api": {}, "report": {"output_dir": "."}}


def _set_env(monkeypatch: pytest.MonkeyPatch, auth: dict[str, Any]) -> list[str]:
    """Define every referenced variable with a synthetic value; return the values."""
    creds = new_credentials(with_token=True)
    by_key = {
        "access_key_id_from_env": creds.access_key_id,
        "secret_access_key_from_env": creds.secret_access_key,
        "session_token_from_env": str(creds.session_token),
    }
    for key, name in auth.items():
        if isinstance(name, str) and name.strip() and key.endswith("_from_env"):
            monkeypatch.setenv(name.strip(), by_key.get(key, str(creds.session_token)))
    return list(by_key.values())


def _load(monkeypatch: pytest.MonkeyPatch, target: dict[str, Any]) -> dict[str, Any]:
    _set_env(monkeypatch, target.get("auth") or {})
    return normalize_config(_config(target))


def _refused(
    monkeypatch: pytest.MonkeyPatch, target: dict[str, Any], *, secret: str = ""
) -> str:
    top = {k: v for k, v in target.items() if k.endswith("_from_env")}
    _set_env(monkeypatch, {**top, **(target.get("auth") or {})})
    with pytest.raises(ValueError) as info:
        normalize_config(_config(target))
    message = str(info.value)
    if secret:
        assert secret not in message
    return message


@pytest.fixture
def toy_registered() -> Iterator[None]:
    """Snapshot the driver registry; each test registers the toy driver itself."""
    saved = dict(object_storage_driver._REGISTRY)
    try:
        yield
    finally:
        object_storage_driver._REGISTRY.clear()
        object_storage_driver._REGISTRY.update(saved)


# ----------------------------------------------------------------------------
# D2306-15: #1977 prefix and reserved names
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("prefix", ["DATA_BOAR_", "REST_API_", "API_"])
def test_D2306_15_nomes_com_prefixo_do_1977_sao_aceitos(
    prefix: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _s3_target(
        auth={
            "access_key_id_from_env": f"{prefix}S3_AK",
            "secret_access_key_from_env": f"{prefix}S3_SK",
            "session_token_from_env": f"{prefix}S3_ST",
        }
    )
    out = _load(monkeypatch, target)
    assert out["targets"][0]["auth"]["access_key_id_from_env"] == f"{prefix}S3_AK"


@pytest.mark.parametrize(
    "key",
    ["access_key_id_from_env", "secret_access_key_from_env", "session_token_from_env"],
)
@pytest.mark.parametrize(
    "name", ["S3_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
)
def test_D2306_15_nome_sem_prefixo_e_recusado_citando_1977(
    key: str, name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _s3_target()
    target["auth"][key] = name
    message = _refused(monkeypatch, target)
    assert "#1977" in message
    assert key in message


@pytest.mark.parametrize(
    "key",
    ["access_key_id_from_env", "secret_access_key_from_env", "session_token_from_env"],
)
def test_D2306_15_nome_reservado_e_recusado(
    key: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _s3_target()
    target["auth"][key] = "DATA_BOAR_API_KEY"
    _refused(monkeypatch, target)


# ----------------------------------------------------------------------------
# D2306-16: inline credential keys, in the target and in auth
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("key", FORBIDDEN_S3)
@pytest.mark.parametrize("where", ["target", "auth"])
def test_D2306_16_chave_proibida_e_recusada_sem_ecoar_o_valor(
    key: str, where: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    mark = _marker()
    target = _s3_target()
    if where == "target":
        target[key] = mark
    else:
        target["auth"][key] = mark
    message = _refused(monkeypatch, target, secret=mark)
    assert key in message
    assert "#2306" in message
    assert "bucket-sintetico" in message


# ----------------------------------------------------------------------------
# D2306-17: required names
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key", ["access_key_id_from_env", "secret_access_key_from_env"]
)
@pytest.mark.parametrize("value", [None, "", "   ", 123])
def test_D2306_17_nome_obrigatorio_ausente_ou_vazio_e_recusado(
    key: str, value: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _s3_target()
    if value is None:
        del target["auth"][key]
    else:
        target["auth"][key] = value
    message = _refused(monkeypatch, target)
    assert key in message


def test_D2306_17_sem_auth_e_recusado(monkeypatch: pytest.MonkeyPatch) -> None:
    target = _s3_target()
    del target["auth"]
    _refused(monkeypatch, target)


def test_D2306_17_sem_session_token_carrega(monkeypatch: pytest.MonkeyPatch) -> None:
    target = _s3_target()
    del target["auth"]["session_token_from_env"]
    out = _load(monkeypatch, target)
    assert "session_token_from_env" not in out["targets"][0]["auth"]


# ----------------------------------------------------------------------------
# D2306-18: no value is copied into the config
# ----------------------------------------------------------------------------


def _walk(node: Any, path: str = "") -> Iterator[tuple[str, Any]]:
    if isinstance(node, dict):
        for k, v in node.items():
            yield f"{path}.{k}", k
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(node, (list, tuple, set)):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, node


def test_D2306_18_nenhum_valor_de_credencial_entra_no_dicionario(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _s3_target()
    values = _set_env(monkeypatch, target["auth"])
    out = normalize_config(_config(target))
    loaded = out["targets"][0]
    for forbidden in ("access_key_id", "secret_access_key", "session_token"):
        assert forbidden not in loaded
        assert forbidden not in loaded["auth"]
    for path, leaf in _walk(out):
        for value in values:
            assert value not in str(leaf), path


# ----------------------------------------------------------------------------
# D2306-19: strict host gate (DATA_BOAR_CREDENTIAL_STRICT=1)
# ----------------------------------------------------------------------------


def test_D2306_19_estrito_com_o_host_exato_carrega(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(STRICT, "1")
    monkeypatch.setenv(OPERATOR_HOSTS, f"other.example,{AWS_HOST}")
    out = _load(monkeypatch, _s3_target(allowed_hosts=[AWS_HOST]))
    assert out["targets"][0]["bucket"] == BUCKET

    endpoint = _s3_target(
        driver="s3_compatible",
        endpoint_url="https://minio.lab.example:9000",
        region="us-east-1",
        allowed_hosts=["minio.lab.example"],
    )
    monkeypatch.setenv(OPERATOR_HOSTS, "minio.lab.example")
    assert _load(monkeypatch, endpoint)["targets"][0]["bucket"] == BUCKET


def test_D2306_19_estrito_sem_o_host_na_lista_do_operador_e_recusado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(STRICT, "1")
    monkeypatch.setenv(OPERATOR_HOSTS, "other.example")
    _refused(monkeypatch, _s3_target(allowed_hosts=[AWS_HOST]))
    monkeypatch.delenv(OPERATOR_HOSTS)
    _refused(monkeypatch, _s3_target(allowed_hosts=[AWS_HOST]))


def test_D2306_19_estrito_com_allowed_hosts_sem_o_host_e_recusado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(STRICT, "1")
    monkeypatch.setenv(OPERATOR_HOSTS, AWS_HOST)
    _refused(monkeypatch, _s3_target(allowed_hosts=["other.example"]))
    # Section 3, step 4 uses assert_explicit_destination_allowlisted: the YAML entry is
    # required for every destination, not only the operator list.
    _refused(monkeypatch, _s3_target())


def test_D2306_19_estrito_com_bucket_invalido_falha_fechado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(STRICT, "1")
    monkeypatch.setenv(OPERATOR_HOSTS, f"{AWS_HOST},minio.lab.example")
    _refused(monkeypatch, _s3_target(bucket="Bad_Bucket", allowed_hosts=[AWS_HOST]))
    _refused(
        monkeypatch,
        _s3_target(
            driver="s3_compatible",
            endpoint_url="http://minio.lab.example",
            region="auto",
            allowed_hosts=["minio.lab.example"],
        ),
    )


def test_D2306_19_sem_modo_estrito_nao_confere_hosts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(STRICT, raising=False)
    monkeypatch.setenv(OPERATOR_HOSTS, "other.example")
    out = _load(monkeypatch, _s3_target())
    assert out["targets"][0]["bucket"] == BUCKET


# ----------------------------------------------------------------------------
# D2306-20: referenced variable unset -> UserWarning, not an error
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "name"),
    [
        ("access_key_id_from_env", ENV_AK),
        ("secret_access_key_from_env", ENV_SK),
        ("session_token_from_env", ENV_ST),
    ],
)
def test_D2306_20_variavel_nao_definida_gera_aviso(
    key: str, name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _s3_target()
    _set_env(monkeypatch, target["auth"])
    monkeypatch.delenv(name)
    with pytest.warns(UserWarning) as record:
        out = normalize_config(_config(target))
    assert out["targets"][0]["bucket"] == BUCKET
    texts = [str(w.message) for w in record]
    assert any(name in t and key in t for t in texts), texts


# ----------------------------------------------------------------------------
# D2306-21: --validate-config warns and masks the three names
# ----------------------------------------------------------------------------


def test_D2306_21_validate_config_avisa_e_mascara_os_tres_campos(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import core.connector_registry as registry
    import main

    mark = _marker()
    names = {
        "access_key_id_from_env": f"DATA_BOAR_{mark}_AK",
        "secret_access_key_from_env": f"DATA_BOAR_{mark}_SK",
        "session_token_from_env": f"DATA_BOAR_{mark}_ST",
    }
    for name in names.values():
        monkeypatch.delenv(name, raising=False)
    target = _s3_target(auth=dict(names))

    # The object_storage connector is registered only in task 2306.2; until then the
    # pre-flight would stop at "no connector registered". Resolve it here so the env-var
    # warnings (the subject of D-21) are exercised.
    original = registry.connector_for_target

    def resolve(t: dict[str, Any]) -> Any:
        if t.get("type") == "object_storage":
            return (object, ["name", "bucket"])
        return original(t)

    monkeypatch.setattr(registry, "connector_for_target", resolve)
    # A second, unknown target makes the pre-flight exit right after printing the
    # warnings (before any directory, SQLite or trust side effect).
    config = {
        "targets": [target, {"name": "probe-invalid", "type": "no_such_type"}],
    }
    with pytest.raises(SystemExit) as info:
        main._validate_config_and_exit(config, "inline.yaml")
    assert info.value.code == 1
    out = capsys.readouterr().out
    for key in names:
        assert f"auth.{key}='***' — env var not set" in out, out
    assert mark not in out


# ----------------------------------------------------------------------------
# D2306-66: the loader is driver-generic (toy driver)
# ----------------------------------------------------------------------------


def _toy_target(**extra: Any) -> dict[str, Any]:
    target: dict[str, Any] = {
        "name": "toy-1",
        "type": "object_storage",
        "driver": "toy",
        "host": TOY_HOST,
        "container": "caixa-1",
        "auth": {"token_from_env": "DATA_BOAR_TOY_TOKEN"},
    }
    target.update(extra)
    return target


def test_D2306_66_loader_usa_as_chaves_do_driver_de_brinquedo(
    toy_registered: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    register_toy_driver()
    out = _load(monkeypatch, _toy_target())
    assert out["targets"][0]["auth"] == {"token_from_env": "DATA_BOAR_TOY_TOKEN"}
    assert "token" not in out["targets"][0]["auth"]

    # Required credential key comes from the toy credential_keys.
    missing = _toy_target(auth={})
    assert "token_from_env" in _refused(monkeypatch, missing)

    # Inline keys forbidden only by the toy driver.
    for key in ("toy_token", "toy_secret"):
        mark = _marker()
        message = _refused(monkeypatch, _toy_target(**{key: mark}), secret=mark)
        assert key in message
        inside = _toy_target()
        inside["auth"][key] = mark
        message = _refused(monkeypatch, inside, secret=mark)
        assert key in message

    # Name without the #1977 prefix.
    message = _refused(monkeypatch, _toy_target(auth={"token_from_env": "TOY_TOKEN"}))
    assert "#1977" in message


def test_D2306_66_estrito_usa_o_destination_host_do_driver(
    toy_registered: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    register_toy_driver()
    monkeypatch.setenv(STRICT, "1")
    monkeypatch.setenv(OPERATOR_HOSTS, TOY_HOST)
    out = _load(monkeypatch, _toy_target(allowed_hosts=[TOY_HOST]))
    assert out["targets"][0]["host"] == TOY_HOST
    monkeypatch.setenv(OPERATOR_HOSTS, AWS_HOST)
    _refused(monkeypatch, _toy_target(allowed_hosts=[AWS_HOST]))


def test_secao3_driver_desconhecido_carrega_e_estrito_falha_fechado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Section 3, revision 2: an unknown driver does not fail the load (the connector
    records ``config_error`` at run time), but strict mode fails closed (empty
    destination group)."""
    target = _s3_target(driver="no_such_driver")
    monkeypatch.delenv(STRICT, raising=False)
    assert _load(monkeypatch, target)["targets"][0]["driver"] == "no_such_driver"
    monkeypatch.setenv(STRICT, "1")
    monkeypatch.setenv(OPERATOR_HOSTS, AWS_HOST)
    _refused(monkeypatch, _s3_target(driver="no_such_driver", allowed_hosts=[AWS_HOST]))


# ----------------------------------------------------------------------------
# D2306-83: credential keys of the driver are subtracted only at the auth level
# ----------------------------------------------------------------------------


def test_D2306_83_token_from_env_do_brinquedo_so_vale_em_auth(
    toy_registered: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    register_toy_driver()
    out = _load(monkeypatch, _toy_target())
    assert out["targets"][0]["auth"]["token_from_env"] == "DATA_BOAR_TOY_TOKEN"
    # At the target level nothing is subtracted: credentials live only in auth.
    message = _refused(monkeypatch, _toy_target(token_from_env="DATA_BOAR_TOY_TOKEN"))
    assert "token_from_env" in message
    # The S3 driver does not declare token_from_env: still refused in auth.
    target = _s3_target()
    target["auth"]["token_from_env"] = "DATA_BOAR_S3_TOKEN"
    message = _refused(monkeypatch, target)
    assert "token_from_env" in message
