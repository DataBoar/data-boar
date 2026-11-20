"""Black-box acceptance tests for task 2306 (``object_storage`` reader, driver ``s3``).

Source: ``docs/desenho/2306.md`` (revision 2), section "Especificacao para a aceitacao do
QA" (cases ``A2306-1`` .. ``A2306-24``). Task 2306.3, written before the implementation.

Black-box rules: the connector is driven only through its public contract (config ->
``run()``, findings, failures, inventory, report workbook, logs) against the simulated S3 in
``tests/s3_fake.py``. No network, no container, no real credential, only synthetic data.
Credentials are built at run time (``SYNTHAK``/``SYNTHSK``/``SYNTHST`` plus random hex).

Pending marker (the design, "Marca de pendente"): ``xfail(strict=True)``.

- ``raises=NotImplementedError`` for the behavioural tests. The helper ``connector_class``
  converts into ``NotImplementedError`` only the ``ModuleNotFoundError`` whose ``name`` is
  ``connectors.object_storage_connector``; any other import or setup error stays an error.
- ``raises=AssertionError`` for the config, registry and tier tests (A-8, A-9, A-17, A-18),
  written with plain ``assert`` (no ``pytest.raises``) in the order the design fixes, so the
  first assertion fails on today's code.

A passing marked test is ``XPASS(strict)`` and breaks the run, so the commit that makes a
test pass removes its mark in the same commit. Which commit removes which mark is fixed in
the design: A-8 and A-9 leave with the loader ``feat:`` of 2306.1; A-17 and A-18 with the
registered skeleton of 2306.2; the other A cases with the ``feat:`` that makes each pass, and
A-23 and A-24 with the report-coverage ``feat:`` (section 14).

The last section (``Self-checks of the simulator``) is NOT pending: it proves the simulator
itself (``tests/s3_fake.py``) and the toy backend (``tests/object_storage_toy_driver.py``),
because the pending cases cannot run their bodies until the connector exists.

Contradictions between A-7 and A-21/A-22 and the rest of the design are noted on A-7.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, NamedTuple

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from defusedxml import ElementTree as DefusedET
from openpyxl import load_workbook

from tests.object_storage_toy_driver import (
    TOY_AUTH_HEADER,
    ToyStore,
    new_toy_token,
    toy_blob_url,
    toy_list_url,
    toy_parse_listing,
)
from tests.s3_fake import (
    EMPTY_SHA256,
    EVIL_HOST,
    GOOD_IP,
    METADATA_IP,
    PRIVATE_IP,
    Creds,
    FakeClock,
    FakeDB,
    FakeS3,
    RegexScanner,
    canonical_request,
    compute_signature,
    install_fake_dns,
    new_credentials,
    sign_get_headers,
    uri_encode,
)

BUCKET = "databoar-sintetico"
REGION = "sa-east-1"
AWS_HOST = f"{BUCKET}.s3.{REGION}.amazonaws.com"
MINIO_HOST = "minio.lab.example"
MINIO_ENDPOINT = f"https://{MINIO_HOST}:9000"
TARGET_NAME = "bucket-sintetico"

ENV_AK = "DATA_BOAR_S3_ACCESS_KEY_ID"
ENV_SK = "DATA_BOAR_S3_SECRET_ACCESS_KEY"
ENV_ST = "DATA_BOAR_S3_SESSION_TOKEN"

A_TXT = b"Cliente cadastrado: CPF 123.456.789-09, ficha 77.\n"
B_TXT = b"Ata da reuniao: revisar o cronograma do galpao.\n"
C_CSV = b"nome,contato\nPessoa Teste,pessoa.teste@exemplo.com\n"
PII_TXT = b"Funcionario: CPF 987.654.321-00, matricula 12.\n"

EXPECTED_PATHS = {
    f"s3://{BUCKET}/corpus/a.txt",
    f"s3://{BUCKET}/corpus/sub/c.csv",
}
MIB = 1024 * 1024


def corpus() -> dict[str, bytes]:
    """The synthetic bucket of A-1: two prefixes, only ``corpus/`` is in scope."""
    return {
        "corpus/a.txt": A_TXT,
        "corpus/b.txt": B_TXT,
        "corpus/sub/c.csv": C_CSV,
        "outro/d.txt": PII_TXT,
    }


def pending(case: str) -> pytest.MarkDecorator:
    return pytest.mark.xfail(
        strict=True,
        raises=NotImplementedError,
        reason=f"2306 pending: {case} (connector not implemented yet)",
    )


def pending_assert(case: str) -> pytest.MarkDecorator:
    return pytest.mark.xfail(
        strict=True,
        raises=AssertionError,
        reason=f"2306 pending: {case} (loader/registry/tier not wired yet)",
    )


def connector_class() -> type:
    """Import the connector; only its own absence means "pending"."""
    try:
        import connectors.object_storage_connector as mod
    except ModuleNotFoundError as exc:
        if exc.name == "connectors.object_storage_connector":
            raise NotImplementedError("2306: connector module missing") from exc
        raise
    return mod.ObjectStorageConnector


# ----------------------------------------------------------------------------
# Harness
# ----------------------------------------------------------------------------


def make_target(**overrides: Any) -> dict[str, Any]:
    """A valid AWS ``object_storage`` target with obviously fake values."""
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


def minio_target(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "endpoint_url": MINIO_ENDPOINT,
        "region": "us-east-1",
        "allow_private_networks": True,
    }
    base.update(overrides)
    return make_target(**base)


class Outcome(NamedTuple):
    db: FakeDB
    clock: FakeClock
    connector: Any


def scan(
    fake: FakeS3,
    target: dict[str, Any] | None = None,
    *,
    db: FakeDB | None = None,
) -> Outcome:
    db = db if db is not None else FakeDB()
    clock = FakeClock()
    # The import is the last step: everything above runs for real even today.
    cls = connector_class()
    conn = cls(
        target_config=target if target is not None else make_target(),
        scanner=RegexScanner(),
        db_manager=db,
        _transport=fake.transport,
        _sleep=clock.sleep,
        _now=clock.now,
    )
    conn.run()
    return Outcome(db, clock, conn)


def paths(db: FakeDB) -> set[str]:
    return {f["path"] for f in db.findings}


def list_requests(fake: FakeS3) -> list[Any]:
    return [
        r
        for r, op in zip(fake.requests, fake.operations, strict=True)
        if op == "ListObjectsV2"
    ]


@pytest.fixture
def creds(monkeypatch: pytest.MonkeyPatch) -> Creds:
    c = new_credentials()
    monkeypatch.setenv(ENV_AK, c.access_key_id)
    monkeypatch.setenv(ENV_SK, c.secret_access_key)
    monkeypatch.setenv(ENV_ST, c.session_token or "")
    return c


@pytest.fixture
def make_fake(monkeypatch: pytest.MonkeyPatch, creds: Creds):
    ips: dict[str, list[str]] = {EVIL_HOST: [GOOD_IP]}
    made: list[FakeS3] = []

    def factory(
        objects: dict[str, bytes] | None = None,
        *,
        host: str = AWS_HOST,
        addressing: str = "virtual",
        region: str = REGION,
        ip: str = GOOD_IP,
        **kw: Any,
    ) -> FakeS3:
        fake = FakeS3(
            BUCKET,
            corpus() if objects is None else objects,
            host,
            addressing,  # type: ignore[arg-type]
            region,
            access_key_id=creds.access_key_id,
            session_token=creds.session_token,
            secret_access_key=creds.secret_access_key,
            **kw,
        )
        ips[fake.hostname] = [ip]
        install_fake_dns(monkeypatch, ips)
        made.append(fake)
        return fake

    yield factory
    for fake in made:
        # Unexpected host, a parameter the design forbids, a request the simulator would
        # refuse for its form (Authorization, date, body hash, token, Host): the simulator
        # records, never raises, and a clean run leaves both lists empty.
        assert fake.violations == [], fake.violations
        assert fake.auth_failures == [], fake.auth_failures


def run_with_report(
    fake: FakeS3, target: dict[str, Any], tmp_path: Path
) -> tuple[Outcome, Any]:
    """Run the connector against a real ``LocalDBManager`` and build the report workbook."""
    from core.database import LocalDBManager
    from report.generator import generate_report

    mgr = LocalDBManager(str(tmp_path / "audit_s3.db"))
    try:
        sid = "session-s3-acceptance"
        mgr.set_current_session_id(sid)
        mgr.create_session_record(sid)
        out = scan(fake, target, db=FakeDB(real=mgr))
        mgr.finish_session(sid)
        report = generate_report(mgr, sid, output_dir=str(tmp_path), config={})
        assert report is not None
        return out, load_workbook(report)
    finally:
        mgr.dispose()


def sheet_rows(wb: Any, name: str) -> list[dict[str, Any]]:
    assert name in wb.sheetnames, (name, wb.sheetnames)
    ws = wb[name]
    headers = [c.value for c in ws[1]]
    return [
        dict(zip(headers, [c.value for c in row], strict=False))
        for row in ws.iter_rows(min_row=2)
    ]


def workbook_text(wb: Any) -> str:
    cells: list[str] = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            cells.extend(str(c.value) for c in row if c.value is not None)
    return "\n".join(cells)


def coverage_row(wb: Any, target_name: str = TARGET_NAME) -> dict[str, Any]:
    rows = [r for r in sheet_rows(wb, "Target coverage") if r["Target"] == target_name]
    assert len(rows) == 1, rows
    return rows[0]


def report_info_value(wb: Any, field: str) -> list[str]:
    return [
        str(r["Value"])
        for r in sheet_rows(wb, "Report info")
        if r.get("Field") == field
    ]


# ----------------------------------------------------------------------------
# Behavioural cases (NotImplementedError-pending)
# ----------------------------------------------------------------------------


@pending("A2306-1")
def test_A2306_1_prefixo_gera_achados_so_dos_arquivos_com_dado(make_fake):
    """A2306-1 (prefix corpus/; a.txt e sub/c.csv; nada de b.txt nem de outro/d.txt)."""
    scanner = RegexScanner()
    assert scanner.scan_file_content(A_TXT.decode(), "a.txt") is not None
    assert scanner.scan_file_content(C_CSV.decode(), "c.csv") is not None
    assert scanner.scan_file_content(B_TXT.decode(), "b.txt") is None

    fake = make_fake()
    out = scan(fake)

    assert paths(out.db) == EXPECTED_PATHS
    assert all(p.startswith(f"s3://{BUCKET}/corpus/") for p in paths(out.db))
    assert not any(f["path"].endswith("b.txt") for f in out.db.findings)
    assert not any("outro" in f["path"] for f in out.db.findings)
    assert {f["source_type"] for f in out.db.findings} == {"filesystem"}
    assert out.db.failures == []
    listings = list_requests(fake)
    assert listings, "no listing was requested"
    for req in listings:
        assert "prefix=corpus%2F" in req.raw_query.split("&"), req.raw_query
    assert not any("outro" in r.path for r in fake.requests)


@pending("A2306-2")
def test_A2306_2_minio_por_caminho_com_rede_privada_autorizada(make_fake):
    """A2306-2 (endpoint_url https; allow_private_networks; 10.0.0.5; tudo no caminho)."""
    fake = make_fake(
        host=f"{MINIO_HOST}:9000",
        addressing="path",
        region="us-east-1",
        ip=PRIVATE_IP,
    )
    out = scan(fake, minio_target())

    assert paths(out.db) == EXPECTED_PATHS
    assert out.db.failures == []
    assert fake.requests, "no request reached the endpoint"
    assert {r.host for r in fake.requests} == {MINIO_HOST}
    assert all(r.path.startswith(f"/{BUCKET}") for r in fake.requests)


@pending("A2306-3")
def test_A2306_3_inventario_e_achados_no_relatorio(make_fake, tmp_path):
    """A2306-3 (LocalDBManager + generate_report; tipo de origem e produto certos)."""
    fake = make_fake()
    out, wb = run_with_report(fake, make_target(), tmp_path)

    assert paths(out.db) == EXPECTED_PATHS
    rows = [
        r for r in sheet_rows(wb, "Data source inventory") if r["Target"] == TARGET_NAME
    ]
    assert len(rows) == 1, rows
    row = rows[0]
    assert row["Source type"] == "object_storage"
    assert row["Product"] == "Amazon S3"
    assert f"bucket={BUCKET}" in row["Inventory details (executive)"]
    fs_text = "\n".join(
        str(v) for r in sheet_rows(wb, "Filesystem findings") for v in r.values()
    )
    for expected in EXPECTED_PATHS:
        assert expected in fs_text


@pending("A2306-4")
def test_A2306_4_max_objects_limita_e_avisa(make_fake):
    """A2306-4 (30 objetos, max_objects 10: no maximo 10 considerados e limit_reached)."""
    objects = {f"corpus/obj-{i:02d}.txt": B_TXT for i in range(30)}
    fake = make_fake(objects)
    out = scan(fake, make_target(max_objects=10))

    assert fake.operations.count("GetObject") == 10
    assert len(fake.fetched) == 10
    assert "limit_reached" in out.db.reasons()
    assert any("max_objects" in d for d in out.db.details("limit_reached"))
    assert "max-keys=10" in list_requests(fake)[0].raw_query.split("&")


@pending("A2306-5")
def test_A2306_5_max_download_bytes_corta_o_terceiro(make_fake):
    """A2306-5 (3 objetos de 40 bytes, teto 100: 2 baixados e limit_reached)."""
    body = "Cliente: CPF 123.456.789-09".ljust(39).encode() + b"\n"
    assert len(body) == 40
    objects = {f"corpus/obj-{c}.txt": body for c in "abc"}
    fake = make_fake(objects)
    out = scan(fake, make_target(max_download_bytes=100))

    assert fake.operations.count("GetObject") == 2
    assert len(out.db.findings) == 2
    assert "limit_reached" in out.db.reasons()
    assert any("max_download_bytes" in d for d in out.db.details("limit_reached"))


@pending("A2306-6")
def test_A2306_6_timeout_esgotado_nao_espera_de_verdade(make_fake):
    """A2306-6 (ReadTimeout sempre, timeout 5: unreachable, sleep [1, 2, 4], sem achados)."""
    fake = make_fake()
    fake.network_error(None, kind="read_timeout")
    out = scan(fake, make_target(timeout=5))

    assert len(fake.requests) == 4  # a primeira tentativa e tres repeticoes
    assert out.clock.sleeps == [1, 2, 4]
    assert "unreachable" in out.db.reasons()
    assert out.db.findings == []
    assert fake.operations.count("GetObject") == 0


@pending("A2306-7")
def test_A2306_7_objeto_acima_de_max_object_bytes_nao_e_pedido(make_fake):
    """A2306-7 (2 MiB, max_object_bytes 1 MiB; nunca pedido; contado como too_large).

    Contradicao no desenho: o A2306-7 diz que a falha ``too_large`` cita
    ``s3://databoar-sintetico/corpus/<nome>`` com a config padrao, mas a secao 7, a secao
    8 passo 7 (DEC-11) e o A2306-21 dizem que, sem ``report_object_names: true``, nao ha
    falha por objeto e o nome nao aparece. Este teste cobre so o que as duas leituras
    tem em comum (objeto nao pedido, nenhum achado, ``too_large=1`` no resumo ``skipped``);
    a clausula "cita s3://..." e o A2306-22, com a opcao ligada.
    """
    big = PII_TXT + b" " * (2 * MIB - len(PII_TXT))
    assert len(big) == 2 * MIB
    fake = make_fake({"corpus/grande.txt": big})
    out = scan(fake, make_target(max_object_bytes=MIB))

    assert fake.requests, "the listing was never requested"
    assert fake.fetched == []
    assert out.db.findings == []
    skipped = out.db.details("skipped")
    assert skipped, out.db.failures
    assert any("too_large=1" in d for d in skipped)


def _config_with(target: dict[str, Any]) -> dict[str, Any]:
    return {"targets": [target], "api": {}, "report": {"output_dir": "."}}


@pending_assert("A2306-8")
def test_A2306_8_nome_de_variavel_sem_prefixo_e_recusado(monkeypatch):
    """A2306-8 (access_key_id_from_env: S3_KEY, sem o prefixo do #1977, da ValueError)."""
    from config.loader import normalize_config

    monkeypatch.setenv("S3_KEY", "SYNTHAK" + "0" * 16)
    monkeypatch.setenv(ENV_SK, "SYNTHSK" + "0" * 32)
    target = make_target(
        auth={
            "access_key_id_from_env": "S3_KEY",
            "secret_access_key_from_env": ENV_SK,
        }
    )
    err = None
    try:
        normalize_config(_config_with(target))
    except Exception as exc:  # noqa: BLE001 - the assertion below fixes the type
        err = exc
    assert isinstance(err, ValueError)


@pending_assert("A2306-9")
def test_A2306_9_segredo_em_texto_no_yaml_e_recusado_sem_ecoar_o_valor(monkeypatch):
    """A2306-9 (secret_access_key no alvo: ValueError com o nome da chave, sem o valor)."""
    from config.loader import normalize_config

    marker = "SYNTHSK-" + new_credentials().secret_access_key
    monkeypatch.setenv(ENV_AK, "SYNTHAK" + "0" * 16)
    monkeypatch.setenv(ENV_SK, "SYNTHSK" + "0" * 32)
    target = make_target(secret_access_key=marker)
    err = None
    try:
        normalize_config(_config_with(target))
    except Exception as exc:  # noqa: BLE001 - the assertions below fix the type
        err = exc
    assert isinstance(err, ValueError)
    assert "secret_access_key" in str(err)
    assert marker not in str(err)


@pending("A2306-10")
@pytest.mark.parametrize("empty_env", [ENV_AK, ENV_SK])
def test_A2306_10_variavel_vazia_na_varredura_e_config_error(
    make_fake, monkeypatch, empty_env
):
    """A2306-10 (variavel referenciada definida como vazia: config_error, zero requisicoes)."""
    fake = make_fake()
    monkeypatch.setenv(empty_env, "")
    out = scan(fake)

    assert "config_error" in out.db.reasons()
    assert fake.requests == []
    assert out.db.findings == []


@pending("A2306-11")
def test_A2306_11_credencial_da_aws_no_ambiente_nunca_e_usada(make_fake, monkeypatch):
    """A2306-11 (so AWS_*; DATA_BOAR_* vazias: zero requisicoes e config_error)."""
    decoys = new_credentials()
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", decoys.access_key_id)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", decoys.secret_access_key)
    fake = make_fake()
    monkeypatch.setenv(ENV_AK, "")
    monkeypatch.setenv(ENV_SK, "")
    out = scan(fake)

    assert "config_error" in out.db.reasons()
    assert fake.requests == []
    assert out.db.findings == []
    for marker in (decoys.access_key_id, decoys.secret_access_key):
        assert marker not in out.db.as_text()


@pending("A2306-12")
def test_A2306_12_destino_interno_e_recusado_sem_requisicao(make_fake):
    """A2306-12 (10.0.0.5 sem opt-in; metadados 169.254.169.254 mesmo com opt-in na AWS)."""
    fake = make_fake(
        host=f"{MINIO_HOST}:9000",
        addressing="path",
        region="us-east-1",
        ip=PRIVATE_IP,
    )
    out = scan(fake, minio_target(allow_private_networks=False))
    assert "scope_violation" in out.db.reasons()
    assert fake.requests == []
    assert out.db.findings == []

    aws = make_fake(ip=METADATA_IP)
    out2 = scan(aws, make_target(allow_private_networks=True))
    assert "scope_violation" in out2.db.reasons()
    assert aws.requests == []
    assert out2.db.findings == []


@pending("A2306-13")
def test_A2306_13_redirect_nao_e_seguido(make_fake):
    """A2306-13 (307 com Location em evil.example: nenhuma requisicao la, scope_violation)."""
    fake = make_fake()
    fake.redirect(307, location=f"https://{EVIL_HOST}/{BUCKET}/?list-type=2")
    out = scan(fake)

    assert fake.requests, "the first listing was never requested"
    assert [r for r in fake.requests if EVIL_HOST in r.url] == []
    assert {r.host for r in fake.requests} == {fake.hostname}
    assert "scope_violation" in out.db.reasons()
    assert out.db.findings == []


@pending("A2306-14")
def test_A2306_14_chaves_hostis_nao_sao_pedidas(make_fake):
    """A2306-14 (../x, corpus/../x e outro/y injetadas: nada pedido, resumo conta os motivos)."""
    fake = make_fake({"corpus/ok.txt": A_TXT})
    fake.inject_keys(
        {
            "../segredo.txt": PII_TXT,
            "corpus/../x.txt": PII_TXT,
            "outro/y.txt": PII_TXT,
        }
    )
    out = scan(fake)

    assert fake.fetched == ["corpus/ok.txt"]  # a ancora: so a chave legitima
    assert paths(out.db) == {f"s3://{BUCKET}/corpus/ok.txt"}
    skipped = out.db.details("skipped")
    assert skipped, out.db.failures
    assert any("out_of_prefix=2" in d and "unsafe_key=1" in d for d in skipped)
    for hostile in ("segredo", "outro/y", "corpus/../x"):
        assert hostile not in out.db.as_text()


@pending("A2306-15")
def test_A2306_15_nenhum_segredo_em_log_saida_falha_achado_ou_inventario(
    make_fake, caplog, capsys
):
    """A2306-15 (A-1, A-13 e AccessDenied com eco, log em DEBUG: nenhum marcador vaza)."""
    caplog.set_level(logging.DEBUG)
    scenarios: list[tuple[FakeS3, Outcome]] = []

    fake1 = make_fake()
    scenarios.append((fake1, scan(fake1)))

    fake2 = make_fake()
    fake2.redirect(307, location=f"https://{EVIL_HOST}/x")
    scenarios.append((fake2, scan(fake2)))

    fake3 = make_fake()
    fake3.error_body_echo = True
    fake3.error_on("ListObjectsV2", status=403, code="AccessDenied")
    out3 = scan(fake3)
    assert "permission_denied" in out3.db.reasons()
    scenarios.append((fake3, out3))

    assert paths(scenarios[0][1].db) == EXPECTED_PATHS  # a varredura completa rodou
    signatures = {
        r.signature for fake, _ in scenarios for r in fake.requests if r.signature
    }
    assert len(signatures) >= 3, "no signature was captured"

    captured = capsys.readouterr()
    haystack = "\n".join(
        [caplog.text, captured.out, captured.err]
        + [
            out.db.as_text() + repr(out.connector) + str(out.connector)
            for _, out in scenarios
        ]
    )
    assert caplog.text, "nothing was logged at DEBUG"
    for marker in ("SYNTHAK", "SYNTHSK", "SYNTHST"):
        assert marker not in haystack, marker
    for sig in signatures:
        assert sig not in haystack
    auth_values = {
        r.headers["authorization"] for fake, _ in scenarios for r in fake.requests
    }
    assert auth_values
    for value in auth_values:
        assert value not in haystack


@pending("A2306-16")
def test_A2306_16_so_get_e_so_listagem_e_download(make_fake):
    """A2306-16 (todos os metodos GET; operations so ListObjectsV2 e GetObject)."""
    fake = make_fake()
    scan(fake)

    assert fake.requests
    assert {r.method for r in fake.requests} == {"GET"}
    assert set(fake.operations) == {"ListObjectsV2", "GetObject"}
    for req, op in zip(fake.requests, fake.operations, strict=True):
        names = {
            urllib.parse.unquote_plus(p.partition("=")[0])
            for p in req.raw_query.split("&")
            if p
        }
        if op == "GetObject":
            assert names == set(), req.url
        else:
            assert "delimiter" not in names
            assert names <= {
                "list-type",
                "prefix",
                "max-keys",
                "encoding-type",
                "continuation-token",
            }


def _signed_license(tmp_path, dbtier: str) -> dict[str, Any]:
    from tests.hybrid_license_fixture import seal_enforced_test_token
    from tests.license_verify_pin import pin_embedded_ed25519_pem

    priv = Ed25519PrivateKey.generate()
    pub_pem = (
        priv.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
    )
    now = datetime.now(timezone.utc)
    token = seal_enforced_test_token(
        priv,
        jwt.encode(
            {
                "sub": "lic-object-storage",
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(days=1)).timestamp()),
                "dbtier": dbtier,
            },
            priv,
            algorithm="EdDSA",
        ),
    )
    lic = tmp_path / f"{dbtier}.lic"
    lic.write_text(token, encoding="utf-8")
    pin_embedded_ed25519_pem(pub_pem)
    return {"licensing": {"mode": "enforced", "license_path": str(lic)}}


@pytest.fixture
def clean_license_guard():
    import os

    from core.licensing.guard import reset_license_guard_for_tests

    reset_license_guard_for_tests()
    yield reset_license_guard_for_tests
    reset_license_guard_for_tests()
    os.environ.pop("DATA_BOAR_LICENSE_PUBLIC_KEY_PEM", None)


def _gate_error(cfg: dict[str, Any], reset) -> Exception | None:
    from core.connector_registry import require_connector_allowed

    reset()
    try:
        require_connector_allowed(cfg, {"type": "object_storage"})
    except Exception as exc:  # noqa: BLE001 - callers assert the type
        return exc
    return None


@pending_assert("A2306-17")
def test_A2306_17_tier_enterprise_fail_closed(tmp_path, clean_license_guard):
    """A2306-17 (so Enterprise, ou Tier.OPEN, usa o tipo novo)."""
    from core.connector_registry import tier_feature_for_target
    from core.licensing.errors import FeatureTierBlockedError

    assert (
        tier_feature_for_target({"type": "object_storage"})
        == "connector_object_storage"
    )
    err = _gate_error(_signed_license(tmp_path, "enterprise"), clean_license_guard)
    assert err is None
    err = _gate_error({"licensing": {"mode": "open"}}, clean_license_guard)
    assert err is None
    err = _gate_error(_signed_license(tmp_path, "pro"), clean_license_guard)
    assert isinstance(err, FeatureTierBlockedError)


@pending_assert("A2306-18")
def test_A2306_18_registro_resolve_o_conector_novo():
    """A2306-18 (connector_for_target devolve ObjectStorageConnector)."""
    import core.engine  # noqa: F401 - the engine imports the connector modules (registration)
    from core.connector_registry import connector_for_target

    resolved = connector_for_target({"type": "object_storage", "driver": "s3"})
    assert resolved is not None
    assert resolved[0].__name__ == "ObjectStorageConnector"


@pending("A2306-19")
def test_A2306_19_azure_blob_ainda_nao_existe(make_fake):
    """A2306-19 (driver azure_blob: config_error 'not available yet', zero requisicoes)."""
    fake = make_fake()
    out = scan(fake, make_target(driver="azure_blob"))

    assert "config_error" in out.db.reasons()
    assert any("not available yet" in d for d in out.db.details("config_error"))
    assert fake.requests == []
    assert out.db.findings == []


@pending("A2306-20")
def test_A2306_20_slowdown_com_retry_after_espera_e_segue(make_fake):
    """A2306-20 (503 SlowDown com Retry-After 7 na primeira listagem: sleep [7], mesmos achados)."""
    fake = make_fake()
    fake.throttle(1, retry_after=7, op="ListObjectsV2")
    out = scan(fake)

    assert out.clock.sleeps == [7]
    assert len(list_requests(fake)) >= 2  # a recusada e a que passou
    assert paths(out.db) == EXPECTED_PATHS
    assert out.db.failures == []


MARKER_NAME = "SYNTHNAME-" + "a1b2c3d4"


def _named_object() -> dict[str, bytes]:
    return {f"corpus/{MARKER_NAME}.txt": PII_TXT + b" " * 2048}


@pending("A2306-21")
def test_A2306_21_nome_do_objeto_nao_varrido_nao_vai_para_o_relatorio(
    make_fake, tmp_path, caplog, capsys
):
    """A2306-21 (sem report_object_names: o nome nao aparece em lugar nenhum)."""
    caplog.set_level(logging.DEBUG)
    fake = make_fake(_named_object())
    out, wb = run_with_report(fake, make_target(max_object_bytes=1024), tmp_path)

    assert fake.requests and fake.fetched == []
    skipped = out.db.details("skipped")
    assert any("too_large=1" in d for d in skipped), out.db.failures
    captured = capsys.readouterr()
    for place in (
        out.db.as_text(),
        caplog.text,
        captured.out,
        captured.err,
        workbook_text(wb),
    ):
        assert MARKER_NAME not in place


@pending("A2306-22")
def test_A2306_22_com_report_object_names_o_nome_aparece_na_falha(make_fake):
    """A2306-22 (report_object_names true: falha too_large cita s3://...)."""
    fake = make_fake(_named_object())
    out = scan(fake, make_target(max_object_bytes=1024, report_object_names=True))

    assert fake.fetched == []
    details = out.db.details("too_large")
    assert details, out.db.failures
    assert any(f"s3://{BUCKET}/corpus/{MARKER_NAME}.txt" in d for d in details)


@pending("A2306-23")
def test_A2306_23_cobertura_parcial_nunca_e_so_sem_achados(make_fake, tmp_path):
    """A2306-23 (2 MiB com CPF, limite 1 MiB: PARTIAL, 1 objeto e 2097152 bytes)."""
    big = PII_TXT + b" " * (2 * MIB - len(PII_TXT))
    fake = make_fake({"corpus/grande.txt": big})
    out, wb = run_with_report(fake, make_target(max_object_bytes=MIB), tmp_path)

    assert out.db.findings == []
    row = coverage_row(wb)
    assert row["Coverage"] == "PARTIAL"
    assert int(row["Objects not scanned"]) == 1
    assert int(row["Bytes not scanned"]) == 2 * MIB
    assert str(row["Note"]).startswith("No findings in the scanned part only")
    coverage = report_info_value(wb, "Coverage")
    assert len(coverage) == 1
    assert "PARTIAL" in coverage[0]


@pending("A2306-24")
def test_A2306_24_limite_desligado_por_alvo_com_unlimited(make_fake, tmp_path):
    """A2306-24 (max_object_bytes unlimited: baixa, ha achado, COMPLETE, limite citado)."""
    big = PII_TXT + b" " * (2 * MIB - len(PII_TXT))
    fake = make_fake({"corpus/grande.txt": big})
    out, wb = run_with_report(fake, make_target(max_object_bytes="unlimited"), tmp_path)

    assert fake.fetched == ["corpus/grande.txt"]
    assert paths(out.db) == {f"s3://{BUCKET}/corpus/grande.txt"}
    row = coverage_row(wb)
    assert row["Coverage"] == "COMPLETE"
    assert "max_object_bytes" in str(row["Limits disabled"])
    assert report_info_value(wb, "Coverage") == []


# ----------------------------------------------------------------------------
# Self-checks of the simulator and of the toy backend (NOT pending)
# ----------------------------------------------------------------------------

AMZ = "20261120T120000Z"


def _get(fake: FakeS3, creds: Creds, path: str, **override: Any) -> httpx.Response:
    url = f"https://{fake.host_header}{path}"
    headers = sign_get_headers(
        url=url,
        host_header=fake.host_header,
        region=fake.region,
        access_key_id=creds.access_key_id,
        secret_access_key=creds.secret_access_key,
        session_token=creds.session_token,
        amz_date=AMZ,
    )
    headers.update(override)
    with httpx.Client(transport=fake.transport) as client:
        return client.get(url, headers=headers)


def _keys(resp: httpx.Response) -> list[str]:
    root = DefusedET.fromstring(resp.content)
    return [
        urllib.parse.unquote_plus(el.text or "")
        for el in root.iter()
        if el.tag.endswith("Key")
    ]


def _fresh(**kw: Any) -> tuple[FakeS3, Creds]:
    c = new_credentials()
    objects = kw.pop("objects", {f"corpus/o{i}.txt": b"x" * (i + 1) for i in range(5)})
    host = kw.pop("host", AWS_HOST)
    fake = FakeS3(
        BUCKET,
        objects,
        host,
        kw.pop("addressing", "virtual"),
        kw.pop("region", REGION),
        access_key_id=c.access_key_id,
        session_token=c.session_token,
        secret_access_key=c.secret_access_key,
        **kw,
    )
    return fake, c


def test_selfcheck_sigv4_confere_com_o_exemplo_publicado_pela_aws():
    """The verifier reproduces the GET Object example of the AWS SigV4 documentation.

    The documented example secret is assembled at run time (no literal with the shape of a
    secret); the access key id is not part of the signature, so none is needed here.
    """
    secret = "wJalrXUtnFEMI/K7MDENG/" + "bPxRfiCYEXAMPLEKEY"
    headers = {
        "host": "examplebucket.s3.amazonaws.com",
        "range": "bytes=0-9",
        "x-amz-content-sha256": EMPTY_SHA256,
        "x-amz-date": "20130524T000000Z",
    }
    cr = canonical_request(
        "GET", "/test.txt", "", headers, sorted(headers), EMPTY_SHA256
    )
    sig = compute_signature(secret, "us-east-1", "20130524T000000Z", cr)
    assert sig == "f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41"


def test_selfcheck_uri_encode_segue_a_regra_da_aws():
    assert uri_encode("a b+c%d~é", keep_slash=True) == "a%20b%2Bc%25d~%C3%A9"
    assert uri_encode("a/b", keep_slash=True) == "a/b"
    assert uri_encode("a/b", keep_slash=False) == "a%2Fb"


def test_selfcheck_listagem_virtual_pagina_e_decodifica_chaves():
    fake, c = _fresh(objects={"corpus/a b+c%d.txt": b"1", "corpus/z.txt": b"22"})
    fake.page_size = 1
    first = _get(
        fake, c, "/?list-type=2&prefix=corpus%2F&max-keys=1000&encoding-type=url"
    )
    assert first.status_code == 200
    assert _keys(first) == ["corpus/a b+c%d.txt"]
    assert b"%2B" in first.content and b"+" in first.content  # quote_plus format
    token = DefusedET.fromstring(first.content)
    nxt = [e.text for e in token.iter() if e.tag.endswith("NextContinuationToken")][0]
    assert nxt and nxt.startswith("+/")  # needs real percent-encoding in the query
    second = _get(
        fake,
        c,
        "/?continuation-token="
        + uri_encode(nxt, keep_slash=False)
        + "&encoding-type=url&list-type=2&max-keys=1000&prefix=corpus%2F",
    )
    assert second.status_code == 200 and _keys(second) == ["corpus/z.txt"]
    assert fake.operations == ["ListObjectsV2", "ListObjectsV2"]
    assert fake.violations == [] and fake.auth_failures == []


def test_selfcheck_estilo_por_caminho_com_porta_e_bucket_errado():
    fake, c = _fresh(
        host="minio.lab.example:9000", addressing="path", region="us-east-1"
    )
    assert fake.host_header == "minio.lab.example:9000"
    ok = _get(fake, c, f"/{BUCKET}?list-type=2&prefix=corpus%2F")
    assert ok.status_code == 200 and len(_keys(ok)) == 5
    got = _get(fake, c, f"/{BUCKET}/corpus/o1.txt")
    assert got.status_code == 200 and got.content == b"xx"
    assert fake.fetched == ["corpus/o1.txt"]
    wrong = _get(fake, c, "/outro-bucket?list-type=2&prefix=")
    assert wrong.status_code == 404 and b"NoSuchBucket" in wrong.content
    assert fake.violations == [] and fake.auth_failures == []


def test_selfcheck_host_estranho_e_violacao_599():
    fake, c = _fresh()
    url = f"https://{EVIL_HOST}/x"
    with httpx.Client(transport=fake.transport) as client:
        resp = client.get(url)
    assert resp.status_code == 599
    assert len(fake.violations) == 1 and EVIL_HOST in fake.violations[0]


def test_selfcheck_autenticacao_malformada_ou_errada_devolve_403():
    fake, c = _fresh()
    path = "/?list-type=2&prefix=corpus%2F"
    assert _get(fake, c, path).status_code == 200
    assert fake.auth_failures == []

    bad_form = _get(fake, c, path, authorization="Bearer nope")
    assert bad_form.status_code == 403 and b"SignatureDoesNotMatch" in bad_form.content
    no_token = _get(fake, c, path, **{"x-amz-security-token": ""})
    assert no_token.status_code == 403
    other = new_credentials()
    wrong_secret = _get(
        fake, Creds(c.access_key_id, other.secret_access_key, c.session_token), path
    )
    assert (
        wrong_secret.status_code == 403
        and b"SignatureDoesNotMatch" in wrong_secret.content
    )
    wrong_key = _get(
        fake, Creds(other.access_key_id, c.secret_access_key, c.session_token), path
    )
    assert wrong_key.status_code == 403 and b"InvalidAccessKeyId" in wrong_key.content
    assert len(fake.auth_failures) == 4


def test_selfcheck_throttle_com_retry_after_e_rede_que_falha():
    fake, c = _fresh()
    fake.throttle(2, retry_after=7)
    path = "/?list-type=2&prefix="
    first = _get(fake, c, path)
    assert first.status_code == 503 and first.headers["Retry-After"] == "7"
    assert b"SlowDown" in first.content
    assert _get(fake, c, path).status_code == 503
    assert _get(fake, c, path).status_code == 200

    fake.network_error(1, kind="read_timeout")
    with pytest.raises(httpx.ReadTimeout):
        _get(fake, c, path)
    assert _get(fake, c, path).status_code == 200
    fake.network_error(None, kind="connect")
    with pytest.raises(httpx.ConnectError):
        _get(fake, c, path)
    assert len(fake.requests) == 6 and fake.operations.count("ListObjectsV2") == 6


def test_selfcheck_redirects():
    fake, c = _fresh()
    fake.redirect(307, location=f"https://{EVIL_HOST}/x")
    resp = _get(fake, c, "/?list-type=2&prefix=")
    assert (
        resp.status_code == 307 and resp.headers["Location"] == f"https://{EVIL_HOST}/x"
    )
    fake.redirect(301, code="PermanentRedirect")
    moved = _get(fake, c, "/?list-type=2&prefix=")
    assert moved.status_code == 301 and b"PermanentRedirect" in moved.content


def test_selfcheck_chaves_injetadas_aparecem_em_toda_listagem():
    fake, c = _fresh(objects={"corpus/ok.txt": b"1"})
    fake.inject_keys({"../segredo.txt": b"s", "outro/y.txt": b"y"})
    fake.inject_keys(["%E0%A4%A"], raw=True)
    resp = _get(fake, c, "/?list-type=2&prefix=corpus%2F&encoding-type=url")
    root = DefusedET.fromstring(resp.content)
    raw_keys = [e.text for e in root.iter() if e.tag.endswith("Key")]
    assert raw_keys[0] == "corpus/ok.txt"
    assert urllib.parse.unquote_plus(raw_keys[1]) == "../segredo.txt"
    assert "%E0%A4%A" in raw_keys  # not decodable on purpose
    with pytest.raises(UnicodeDecodeError):
        urllib.parse.unquote_plus("%E0%A4%A", errors="strict")
    got = _get(fake, c, "/outro/y.txt")
    assert got.status_code == 200 and got.content == b"y"


def test_selfcheck_error_on_com_eco_e_marcadores_no_corpo():
    fake, c = _fresh()
    fake.error_body_echo = True
    fake.error_on(
        "GetObject", key="corpus/o0.txt", status=403, code="AccessDenied", times=1
    )
    denied = _get(fake, c, "/corpus/o0.txt")
    assert denied.status_code == 403 and b"AccessDenied" in denied.content
    body = denied.text
    assert c.access_key_id in body
    assert "StringToSign" in body and "x-amz-security-token" in body
    assert c.session_token in body  # the echo is what the connector must never log
    assert _get(fake, c, "/corpus/o0.txt").status_code == 200  # times=1 used up
    assert _get(fake, c, "/corpus/o1.txt").status_code == 200
    missing = _get(fake, c, "/corpus/nada.txt")
    assert missing.status_code == 404 and b"NoSuchKey" in missing.content


def test_selfcheck_tamanho_mentiroso_e_content_length_e_bytes_entregues():
    fake, c = _fresh(objects={"corpus/a.txt": b"a" * 10, "corpus/b.txt": b"b" * 10})
    fake.lie_size("corpus/a.txt", declared=4, actual=25)
    fake.lie_size("corpus/b.txt", declared=None, actual=10)
    listing = _get(fake, c, "/?list-type=2&prefix=corpus%2F")
    text = listing.text
    assert "<Size>4</Size>" in text and text.count("<Size>") == 1
    got = _get(fake, c, "/corpus/a.txt")
    assert len(got.content) == 25 and fake.delivered("corpus/a.txt") == 25
    fake.content_length("corpus/b.txt", 10**9)
    big = _get(fake, c, "/corpus/b.txt")
    assert big.headers["Content-Length"] == str(10**9)


def test_selfcheck_botoes_de_listagem_defeituosa():
    fake, c = _fresh(page_size=2)
    q = "/?list-type=2&prefix=corpus%2F&encoding-type=url"
    fake.pagination("missing_token")
    miss = DefusedET.fromstring(_get(fake, c, q).content)
    assert [e.text for e in miss.iter() if e.tag.endswith("IsTruncated")] == ["true"]
    assert not [e for e in miss.iter() if e.tag.endswith("NextContinuationToken")]
    fake.pagination("repeat_token")
    rep1 = _get(fake, c, q).text
    token = re.search(r"<NextContinuationToken>([^<]+)<", rep1).group(1)
    rep2 = _get(
        fake, c, q + "&continuation-token=" + uri_encode(token, keep_slash=False)
    ).text
    assert f"<NextContinuationToken>{token}<" in rep2
    fake.pagination(None)
    fake.namespace = None
    assert "xmlns" not in _get(fake, c, q).text
    fake.namespace = "other"
    assert "example.invalid" in _get(fake, c, q).text
    fake.encoding_type = None
    assert "EncodingType" not in _get(fake, c, q).text
    fake.malformed_xml = True
    with pytest.raises(Exception):  # noqa: B017,PT011 - any parser error is the point
        DefusedET.fromstring(_get(fake, c, q).content)
    fake.malformed_xml = False
    fake.doctype_entity = True
    assert b"<!DOCTYPE" in _get(fake, c, q).content
    fake.doctype_entity = False
    fake.oversized_listing = True
    assert len(_get(fake, c, q).content) > 16 * MIB
    fake.server_header = "Outro"
    fake.oversized_listing = False
    assert _get(fake, c, q).headers["Server"] == "Outro"


def test_selfcheck_operacao_other_e_parametro_inesperado_sao_violacoes():
    fake, c = _fresh()
    resp = _get(fake, c, "/?acl")
    assert resp.status_code == 400
    assert fake.operations == ["other"] and len(fake.violations) == 1
    _get(fake, c, "/?list-type=2&prefix=&delimiter=%2F")
    assert any("delimiter" in v for v in fake.violations)


def test_selfcheck_dns_falso_devolve_ips_e_recusa_o_resto(monkeypatch):
    import connectors.url_guard as url_guard

    install_fake_dns(monkeypatch, {"minio.lab.example": [PRIVATE_IP]})
    assert [str(i) for i in url_guard._resolve_host_ips("MINIO.lab.example")] == [
        PRIVATE_IP
    ]
    with pytest.raises(OSError):
        url_guard._resolve_host_ips("desconhecido.example")


def test_selfcheck_backend_de_brinquedo_pagina_de_2_exige_cabecalho_e_decodifica():
    token = new_toy_token()
    objects = {f"corpus/f{i}.txt": f"dado {i}".encode() for i in range(5)}
    objects["corpus/a b.txt"] = b"espaco"
    store = ToyStore("brinquedo", objects, token)
    auth = {TOY_AUTH_HEADER: token}
    seen: list[str] = []
    cursor: str | None = None
    with httpx.Client(transport=store.transport) as client:
        for _ in range(10):
            resp = client.get(
                toy_list_url(store.host, "brinquedo", "corpus/", cursor, 100),
                headers=auth,
            )
            assert resp.status_code == 200
            entries, cursor, truncated = toy_parse_listing(resp.content)
            assert len(entries) <= 2
            seen += [k for k, _ in entries]
            if not truncated:
                break
        assert len(seen) == 6 and seen == sorted(objects)
        blob = client.get(
            toy_blob_url(store.host, "brinquedo", "corpus/a b.txt"), headers=auth
        )
        assert blob.content == b"espaco"
        unauth = client.get(toy_list_url(store.host, "brinquedo", "", None, 2))
        assert unauth.status_code == 401
    with pytest.raises(ValueError):
        toy_parse_listing(b'{"items": 3}')
    assert store.violations == []
