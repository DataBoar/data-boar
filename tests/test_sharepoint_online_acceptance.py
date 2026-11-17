"""Black-box acceptance tests for task 2206.1 (``sharepoint_online`` Graph reader, delegated).

Source: ``docs/desenho/2206.1.md``, section "Especificacao para a aceitacao do QA"
(cases ``A2206.1-1`` .. ``A2206.1-18``). Written before the implementation.

Black-box rules: the connector is driven only through its public contract (config ->
``run()`` / ``list_scope()``, findings, failures, prompt stream, logs) against the
simulated Graph in ``tests/m365_fake_graph.py``. No network, no tenant, no real
credential, only synthetic data.

Pending marker: every test is ``xfail(strict=True)``. ``raises=NotImplementedError`` for
the behavioural tests (the helper ``connector_class`` converts only the missing
``connectors.sharepoint_online_connector`` module into ``NotImplementedError``; any other
import or setup error stays an error). ``raises=AssertionError`` for the config, registry
and tier tests (A-15, A-16a, A-16b, A-18), written with plain ``assert`` in the order the
design fixes, so the first assertion fails on today's code. The dev removes each mark when
the test passes (a passing marked test is ``XPASS(strict)`` and fails the run).
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, NamedTuple

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.m365_fake_graph import (
    EVIL_HOST,
    LEAK_MARKERS,
    OTHER_DRIVE_ID,
    SECRET,
    TEST_CLIENT_ID,
    USER_CODE,
    VERIFICATION_URI,
    FakeClock,
    FakeDB,
    FakeGraph,
    File,
    Folder,
    RegexScanner,
    TtyStream,
    install_fake_dns,
    make_target,
)

ROOT = "/DataBoar-Sintetico"
PREFIX = f"onedrive:{ROOT}"

A_TXT = "Cliente cadastrado: CPF 123.456.789-09, ficha 77.\n"
B_TXT = "Ata da reuniao: revisar o cronograma do galpao.\n"
C_CSV = "nome,contato\nPessoa Teste,pessoa.teste@exemplo.com\n"
PII_TXT = "Funcionario: CPF 987.654.321-00, matricula 12.\n"

EXPECTED_PATHS = {f"{PREFIX}/a.txt", f"{PREFIX}/sub/c.csv"}


def pending(case: str) -> pytest.MarkDecorator:
    return pytest.mark.xfail(
        strict=True,
        raises=NotImplementedError,
        reason=f"2206.1 pending: {case} (connector not implemented yet)",
    )


def pending_assert(case: str) -> pytest.MarkDecorator:
    return pytest.mark.xfail(
        strict=True,
        raises=AssertionError,
        reason=f"2206.1 pending: {case} (registry/loader/tier not wired yet)",
    )


def connector_class() -> type:
    """Import the connector; only its own absence means "pending"."""
    try:
        import connectors.sharepoint_online_connector as mod
    except ModuleNotFoundError as exc:
        if exc.name == "connectors.sharepoint_online_connector":
            raise NotImplementedError("2206.1: connector module missing") from exc
        raise
    return mod.SharePointOnlineConnector


# ----------------------------------------------------------------------------
# Harness
# ----------------------------------------------------------------------------


def base_tree(**inside: Any) -> dict[str, Any]:
    """The synthetic OneDrive: the target folder plus decoys outside it."""
    target = {"a.txt": A_TXT, "b.txt": B_TXT, "sub": {"c.csv": C_CSV}}
    target.update(inside)
    return {
        "DataBoar-Sintetico": target,
        # Sibling whose name starts with the target's name (prefix confusion).
        "DataBoar-Sintetico2": {"segredo.txt": PII_TXT},
        "Documentos": {"pessoal.txt": PII_TXT},
    }


class Outcome(NamedTuple):
    db: FakeDB
    clock: FakeClock
    stream: io.StringIO
    connector: Any

    @property
    def prompt(self) -> str:
        return self.stream.getvalue()


def _build(
    fake: FakeGraph,
    target: dict[str, Any] | None,
    interactive: bool,
    tty: bool,
    with_sinks: bool,
) -> tuple[Any, FakeDB, FakeClock, io.StringIO]:
    db = FakeDB()
    clock = FakeClock()
    stream: io.StringIO = TtyStream() if tty else io.StringIO()
    kwargs: dict[str, Any] = {
        "target_config": target if target is not None else make_target(),
        "scanner": RegexScanner() if with_sinks else None,
        "db_manager": db if with_sinks else None,
        "_transport": fake.transport,
        "_sleep": clock.sleep,
        "_monotonic": clock.monotonic,
        "_prompt_stream": stream,
        "_interactive": interactive,
    }
    # The import is the last step: everything above runs for real even today.
    cls = connector_class()
    return cls(**kwargs), db, clock, stream


def scan(
    fake: FakeGraph,
    target: dict[str, Any] | None = None,
    *,
    interactive: bool = True,
    tty: bool = True,
) -> Outcome:
    conn, db, clock, stream = _build(fake, target, interactive, tty, True)
    conn.run()
    return Outcome(db, clock, stream, conn)


def scope(fake: FakeGraph, target: dict[str, Any] | None = None) -> list[Any]:
    conn, _db, _clock, _stream = _build(fake, target, True, True, False)
    return conn.list_scope()


def paths(db: FakeDB) -> set[str]:
    return {f["path"] for f in db.findings}


def failure_details(db: FakeDB, reason: str) -> list[str]:
    return [d for _t, r, d in db.failures if r == reason]


def ids_in_requests(fake: FakeGraph, ids: set[str]) -> list[str]:
    return [r.url for r in fake.requests if any(i in r.url for i in ids)]


@pytest.fixture
def make_fake(monkeypatch: pytest.MonkeyPatch):
    made: list[FakeGraph] = []

    def factory(tree: dict[str, Any] | None = None, **kw: Any) -> FakeGraph:
        fake = FakeGraph(base_tree() if tree is None else tree, **kw)
        install_fake_dns(monkeypatch, fake)
        made.append(fake)
        return fake

    yield factory
    for fake in made:
        # Unexpected host, secret to the login endpoint, Authorization to the download
        # host, a Graph shape the design forbids: the simulator records, never raises.
        assert fake.violations == [], fake.violations


# ----------------------------------------------------------------------------
# Behavioural cases
# ----------------------------------------------------------------------------


@pending("A2206.1-1")
def test_A2206_1_1_pasta_sintetica_gera_achados_so_dos_arquivos_com_dado(make_fake):
    """A2206.1-1 (device code pendente e depois concluido; so a pasta configurada)."""
    scanner = RegexScanner()
    assert scanner.scan_file_content(A_TXT, "a.txt") is not None
    assert scanner.scan_file_content(C_CSV, "c.csv") is not None
    assert scanner.scan_file_content(B_TXT, "b.txt") is None

    fake = make_fake(device_script=["pending", "ok"])
    out = scan(fake)

    assert paths(out.db) == EXPECTED_PATHS
    assert not any(f["path"].endswith("b.txt") for f in out.db.findings)
    assert {f["file_name"] for f in out.db.findings} == {"a.txt", "c.csv"}
    assert {f["source_type"] for f in out.db.findings} == {"filesystem"}
    assert out.db.failures == []
    assert USER_CODE in out.prompt and VERIFICATION_URI in out.prompt
    assert len(fake.token_requests) == 2  # one pending, one ok
    assert all("authorization" in r.headers for r in fake.graph_requests())


@pending("A2206.1-2")
def test_A2206_1_2_pasta_irma_nunca_e_tocada(make_fake):
    """A2206.1-2 (travessia por id, sem confundir prefixo de nome)."""
    fake = make_fake()
    out = scan(fake)

    outside = fake.ids_under("/DataBoar-Sintetico2") | fake.ids_under("/Documentos")
    assert ids_in_requests(fake, outside) == []
    assert not any(
        "Sintetico2" in r.url or "Documentos" in r.url for r in fake.requests
    )
    assert paths(out.db) == EXPECTED_PATHS
    assert not any(
        "segredo" in f["path"] or "pessoal" in f["path"] for f in out.db.findings
    )


@pending("A2206.1-3")
def test_A2206_1_3_pasta_raiz_invalida_e_recusada_sem_rede(make_fake):
    """A2206.1-3 (root_folder igual a /, com .. ou ausente)."""
    absent = make_target()
    del absent["root_folder"]
    for target in (
        make_target(root_folder="/"),
        make_target(root_folder="/a/../b"),
        absent,
    ):
        fake = make_fake()
        out = scan(fake, target)
        assert "config_error" in out.db.reasons(), target.get("root_folder")
        assert out.db.findings == []
        assert fake.requests == []


@pending("A2206.1-4")
def test_A2206_1_4_atalho_para_outro_drive_nao_e_baixado(make_fake):
    """A2206.1-4 (remoteItem: nada de listagem interna, download ou achado)."""
    inside = {
        "atalho-externo": Folder({"vazado.txt": PII_TXT}, remote=True),
        "atalho-arquivo.txt": File(PII_TXT, remote=True),
    }
    fake = make_fake(base_tree(**inside))
    out = scan(fake)

    shortcut_ids = fake.ids_under(f"{ROOT}/atalho-externo") | {
        fake.id_of(f"{ROOT}/atalho-arquivo.txt")
    }
    assert ids_in_requests(fake, shortcut_ids) == []
    assert paths(out.db) == EXPECTED_PATHS

    fake2 = make_fake(base_tree(**inside))
    entries = {e.display_path: e for e in scope(fake2)}
    for name in ("atalho-externo", "atalho-arquivo.txt"):
        entry = entries[f"{PREFIX}/{name}"]
        assert entry.skipped_reason
    assert entries[f"{PREFIX}/a.txt"].skipped_reason in (None, "")


@pending("A2206.1-5")
def test_A2206_1_5_login_negado(make_fake):
    """A2206.1-5 (declined: aviso mostrado, auth_failed, nada ao Graph)."""
    fake = make_fake(device_script=["declined"])
    out = scan(fake)
    assert "auth_failed" in out.db.reasons()
    assert USER_CODE in out.prompt
    assert fake.graph_requests() == []
    assert out.db.findings == []


@pending("A2206.1-6")
def test_A2206_1_6_codigo_expirado(make_fake):
    """A2206.1-6 (expired: auth_failed, nada ao Graph)."""
    fake = make_fake(device_script=["expired"])
    out = scan(fake)
    assert "auth_failed" in out.db.reasons()
    assert fake.graph_requests() == []
    assert out.db.findings == []


@pending("A2206.1-7")
def test_A2206_1_7_sem_sessao_interativa_falha_na_hora(make_fake):
    """A2206.1-7 (auth_required, zero requisicoes ao login) e a segunda condicao (terminal)."""
    fake = make_fake()
    out = scan(fake, interactive=False)
    assert "auth_required" in out.db.reasons()
    assert fake.login_requests() == []
    assert fake.requests == []
    assert out.clock.sleeps == []

    # Contrato, secao 4, condicao 2: modo interativo, mas o aviso nao e um terminal.
    fake2 = make_fake()
    out2 = scan(fake2, interactive=True, tty=False)
    assert "auth_required" in out2.db.reasons()
    assert fake2.requests == []


@pending("A2206.1-8")
def test_A2206_1_8_token_vence_no_meio_da_varredura(make_fake):
    """A2206.1-8 (401 -> refresh -> mesmos achados do A-1)."""
    fake = make_fake()
    fake.expire_access_after(2)
    out = scan(fake)
    assert fake.refresh_count >= 1
    assert paths(out.db) == EXPECTED_PATHS
    assert out.db.failures == []


@pending("A2206.1-9")
def test_A2206_1_9_403_na_raiz_encerra_e_403_em_subpasta_segue(make_fake):
    """A2206.1-9 (permission_denied na raiz; so na subpasta, o resto continua)."""
    fake = make_fake()
    fake.forbid(ROOT)
    out = scan(fake)
    assert "permission_denied" in out.db.reasons()
    assert out.db.findings == []

    fake2 = make_fake()
    fake2.forbid(f"{ROOT}/sub")
    out2 = scan(fake2)
    assert paths(out2.db) == {f"{PREFIX}/a.txt"}
    details = failure_details(out2.db, "permission_denied")
    assert details
    assert any(f"{ROOT}/sub" in d for d in details)


@pending("A2206.1-10")
def test_A2206_1_10_429_com_retry_after_espera_e_segue(make_fake):
    """A2206.1-10 (Retry-After: 7 na primeira listagem)."""
    fake = make_fake()
    fake.throttle(1, retry_after=7)
    out = scan(fake)
    assert 7 in out.clock.sleeps
    assert paths(out.db) == EXPECTED_PATHS


@pending("A2206.1-11")
def test_A2206_1_11_paginacao_nextlink_450_arquivos(make_fake):
    """A2206.1-11 (450 arquivos, pagina de 200)."""
    many = {f"p{i:03d}.txt": A_TXT for i in range(450)}
    fake = make_fake(
        {"DataBoar-Sintetico": many},
        page_size=200,
    )
    out = scan(fake)
    assert len(out.db.findings) == 450
    assert len(paths(out.db)) == 450
    listings = [r for r in fake.graph_requests() if "/children" in r.url]
    assert len(listings) >= 3


@pending("A2206.1-12")
def test_A2206_1_12_nextlink_para_host_estranho_e_recusado(make_fake):
    """A2206.1-12 (nada sai para evil.example; scope_violation)."""
    fake = make_fake()
    fake.next_link_override = f"https://{EVIL_HOST}/v1.0/me/drive/items/X/children"
    out = scan(fake)
    assert fake.requests_to(EVIL_HOST) == []
    assert "scope_violation" in out.db.reasons()


@pending("A2206.1-13a")
def test_A2206_1_13a_download_normal_sem_authorization_no_host_pre_autenticado(
    make_fake,
):
    """A2206.1-13 (a): Authorization so no Graph, nunca no host de download."""
    fake = make_fake()
    out = scan(fake)
    assert paths(out.db) == EXPECTED_PATHS
    downloads = fake.download_requests()
    assert len(downloads) >= 3  # a.txt, b.txt, c.csv
    assert all("authorization" not in r.headers for r in downloads)
    content_calls = [r for r in fake.graph_requests() if r.path.endswith("/content")]
    assert content_calls
    assert all("authorization" in r.headers for r in content_calls)


@pending("A2206.1-13b")
def test_A2206_1_13b_location_em_host_estranho_e_recusada(make_fake):
    """A2206.1-13 (b): Location fora da allowlist."""
    fake = make_fake()
    fake.location_override = f"https://{EVIL_HOST}/{SECRET}x?tempauth={SECRET}y"
    out = scan(fake)
    assert fake.requests_to(EVIL_HOST) == []
    assert "scope_violation" in out.db.reasons()
    assert out.db.findings == []


@pending("A2206.1-13c")
def test_A2206_1_13c_host_de_download_que_resolve_para_ip_interno_e_recusado(make_fake):
    """A2206.1-13 (c): host da allowlist resolvendo para link-local, mesmo com opt-in de rede privada."""
    fake = make_fake()
    fake.host_ips[fake.download_host] = ["169.254.169.254"]
    out = scan(fake, make_target(allow_private_networks=True))
    assert fake.download_requests() == []
    assert "scope_violation" in out.db.reasons()
    assert out.db.findings == []


@pending("A2206.1-14")
def test_A2206_1_14_segredo_nunca_vaza(make_fake, caplog, capsys):
    """A2206.1-14 (logs em DEBUG, saida, falhas, achados, repr; UCODE-1 so no aviso)."""
    caplog.set_level(logging.DEBUG)
    outcomes: list[Outcome] = []

    fake = make_fake(device_script=["pending", "ok"])  # A-1
    outcomes.append(scan(fake))

    fake = make_fake()  # A-8
    fake.expire_access_after(2)
    outcomes.append(scan(fake))

    fake = make_fake()  # A-12
    fake.next_link_override = f"https://{EVIL_HOST}/v1.0/me/drive/items/X/children"
    outcomes.append(scan(fake))

    fake = make_fake()  # A-13 (Location estranha)
    fake.location_override = f"https://{EVIL_HOST}/{SECRET}x?tempauth={SECRET}y"
    outcomes.append(scan(fake))

    fake = make_fake()  # A-13 (host de download interno)
    fake.host_ips[fake.download_host] = ["169.254.169.254"]
    outcomes.append(scan(fake, make_target(allow_private_networks=True)))

    captured = capsys.readouterr()
    assert outcomes[0].prompt  # the human prompt did appear
    for marker in LEAK_MARKERS:
        assert marker not in caplog.text, marker
        assert marker not in captured.out + captured.err, marker
        for out in outcomes:
            assert marker not in out.db.as_text(), marker
            assert marker not in out.prompt, marker
            assert marker not in repr(out.connector) + str(out.connector), marker
    assert USER_CODE in outcomes[0].prompt
    assert USER_CODE not in caplog.text
    assert USER_CODE not in captured.out + captured.err
    for out in outcomes:
        assert USER_CODE not in out.db.as_text()


@pending("A2206.1-17")
def test_A2206_1_17_app_only_ainda_nao_existe(make_fake):
    """A2206.1-17 (auth.mode app_only: config_error citando #2262)."""
    fake = make_fake()
    target = make_target()
    target["auth"] = {**target["auth"], "mode": "app_only"}
    out = scan(fake, target)
    assert "config_error" in out.db.reasons()
    assert any("#2262" in d for d in failure_details(out.db, "config_error"))
    assert fake.requests == []


@pending("REQ-2261-outro-drive")
def test_REQ_2261_item_de_outro_drive_dentro_da_pasta_e_ignorado(make_fake):
    """Requisito da #2261 sem numero A no desenho (D2206.1-29): item com outro driveId."""
    inside = {"estranho.txt": File(PII_TXT, drive_id=OTHER_DRIVE_ID)}
    fake = make_fake(base_tree(**inside))
    out = scan(fake)
    stranger = {fake.id_of(f"{ROOT}/estranho.txt")}
    assert ids_in_requests(fake, stranger) == []
    assert paths(out.db) == EXPECTED_PATHS


# ----------------------------------------------------------------------------
# Config, registry and tier cases (AssertionError-pending; plain asserts only)
# ----------------------------------------------------------------------------


def _config_with(auth: dict[str, Any]) -> dict[str, Any]:
    return {
        "targets": [
            {
                "name": "onedrive-sintetico",
                "type": "sharepoint_online",
                "auth": auth,
                "root_folder": ROOT,
            }
        ],
        "api": {},
        "report": {"output_dir": "."},
    }


@pending_assert("A2206.1-16a")
def test_A2206_1_16a_client_id_vem_da_variavel_de_ambiente(monkeypatch):
    """A2206.1-16a (auth.client_id_from_env vira auth.client_id)."""
    from config.loader import normalize_config

    monkeypatch.setenv("M365_CLIENT_ID", TEST_CLIENT_ID)
    cfg = normalize_config(
        _config_with(
            {
                "mode": "delegated",
                "tenant": "consumers",
                "client_id_from_env": "M365_CLIENT_ID",
            }
        )
    )
    assert cfg["targets"][0]["auth"].get("client_id") == TEST_CLIENT_ID


@pending_assert("A2206.1-16b")
def test_A2206_1_16b_gate_estrito_exige_login_e_graph(monkeypatch):
    """A2206.1-16b (DATA_BOAR_CREDENTIAL_STRICT=1 sem graph.microsoft.com: ValueError)."""
    from config.loader import normalize_config

    monkeypatch.setenv("M365_CLIENT_ID", TEST_CLIENT_ID)
    monkeypatch.setenv("DATA_BOAR_CREDENTIAL_STRICT", "1")
    monkeypatch.setenv(
        "DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS", "login.microsoftonline.com"
    )
    err = None
    try:
        normalize_config(
            _config_with(
                {
                    "mode": "delegated",
                    "tenant": "consumers",
                    "client_id_from_env": "M365_CLIENT_ID",
                }
            )
        )
    except Exception as exc:  # noqa: BLE001 - the assertion below fixes the type
        err = exc
    assert isinstance(err, ValueError)


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
                "sub": "lic-sharepoint-online",
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
        require_connector_allowed(cfg, {"type": "sharepoint_online"})
    except Exception as exc:  # noqa: BLE001 - callers assert the type
        return exc
    return None


@pending_assert("A2206.1-15")
def test_A2206_1_15_tier_enterprise_fail_closed(tmp_path, clean_license_guard):
    """A2206.1-15 (so Enterprise, ou Tier.OPEN, usa o tipo novo)."""
    from core.connector_registry import tier_feature_for_target
    from core.licensing.errors import FeatureTierBlockedError

    assert (
        tier_feature_for_target({"type": "sharepoint_online"})
        == "connector_sharepoint_online"
    )

    err = _gate_error(_signed_license(tmp_path, "enterprise"), clean_license_guard)
    assert err is None
    err = _gate_error({"licensing": {"mode": "open"}}, clean_license_guard)
    assert err is None
    err = _gate_error(_signed_license(tmp_path, "pro"), clean_license_guard)
    assert isinstance(err, FeatureTierBlockedError)
    err = _gate_error(_signed_license(tmp_path, "community"), clean_license_guard)
    assert isinstance(err, FeatureTierBlockedError)


@pending_assert("A2206.1-18")
def test_A2206_1_18_registro_resolve_o_conector_novo():
    """A2206.1-18 (o tipo novo resolve para a classe nova, nao para o SharePoint on-prem)."""
    import core.engine  # noqa: F401 - the engine imports the connector modules (registration)
    from core.connector_registry import connector_for_target

    resolved = connector_for_target({"type": "sharepoint_online"})
    assert resolved is not None
    assert resolved[0].__name__ == "SharePointOnlineConnector"
    on_prem = connector_for_target({"type": "sharepoint"})
    if on_prem is not None:  # extra "shares" installed; otherwise it does not register
        assert on_prem[0] is not resolved[0]
