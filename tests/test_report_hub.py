"""Multi-instance report hub (#2208): provenance, dedupe, safe pulls and the consolidated workbook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

import pytest

from config.loader import normalize_config
from core.licensing.tier_features import FEATURE_TIER_MAP, Tier, is_feature_available
from core.report_hub import (
    REPORT_COLUMNS,
    HubError,
    HubNode,
    consolidate,
    dedupe_key,
    fetch_snapshot,
    parse_hub_nodes,
    run_hub_report,
)

ROOT = Path(__file__).resolve().parents[1]


def _finding(
    i: int, *, path: str | None = None, pattern: str = "CPF", sid: str = "S1"
) -> dict:
    """Synthetic finding. ``id`` is a per-node counter, as in the real API."""
    return {
        "id": i,
        "session_id": sid,
        "source_type": "filesystem",
        "target_name": "t1",
        "path": path or f"/synthetic/file{i}.txt",
        "file_name": (path or f"/synthetic/file{i}.txt").rsplit("/", 1)[-1],
        "data_type": pattern,
        "schema_name": None,
        "table_name": None,
        "column_name": None,
        "sensitivity_level": "HIGH",
        "pattern_detected": pattern,
        "norm_tag": "LGPD",
        "ml_confidence": None,
    }


def _session(sid: str, status: str = "completed") -> dict:
    return {"session_id": sid, "started_at": "2026-11-01T10:00:00", "status": status}


@contextmanager
def _node(
    sessions: list[dict],
    findings: dict[str, list[dict]],
    *,
    version: str = "1.8.0",
    api_key: str | None = None,
    redirect_to: str | None = None,
) -> Iterator[tuple[str, list[dict]]]:
    seen: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: object) -> None:
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            seen.append({"path": self.path, "key": self.headers.get("X-API-Key")})
            if redirect_to:
                self.send_response(302)
                self.send_header("Location", redirect_to)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if api_key and self.headers.get("X-API-Key") != api_key:
                return self._send(401, {"detail": "unauthorized"})
            if self.path == "/list":
                return self._send(200, {"sessions": sessions})
            if self.path.startswith("/findings/"):
                sid = unquote(self.path[len("/findings/") :])
                if sid in findings:
                    rows = findings[sid]
                    return self._send(
                        200, {"session_id": sid, "count": len(rows), "findings": rows}
                    )
                return self._send(404, {"detail": "not found"})
            if self.path == "/about/json":
                return self._send(200, {"name": "Data Boar", "version": version})
            return self._send(404, {"detail": "not found"})

        def log_message(self, *_a: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", seen
    finally:
        server.shutdown()
        server.server_close()


def _cfg(*nodes: tuple[str, str, str]) -> dict:
    return {
        "hub": {
            "nodes": [{"id": i, "url": u, "api_key_from_env": e} for i, u, e in nodes],
        }
    }


# --- provenance and dedupe -------------------------------------------------------------------


def test_colliding_ids_and_session_ids_across_nodes_stay_distinct() -> None:
    same = [
        _finding(1),
        _finding(2),
    ]  # same local ids and same session id on both nodes
    with (
        _node([_session("S1")], {"S1": same}) as (a, _),
        _node([_session("S1")], {"S1": same}) as (b, _),
    ):
        snaps = [fetch_snapshot(HubNode("a", a)), fetch_snapshot(HubNode("b", b))]
    cons = consolidate(snaps)
    assert len(cons.findings) == 4
    assert {r["node_id"] for r in cons.findings} == {"a", "b"}
    assert len({r["dedupe_key"] for r in cons.findings}) == 4
    assert all(
        r["node_version"] == "1.8.0" and r["node_session_id"] == "S1"
        for r in cons.findings
    )


def test_identical_rows_inside_one_node_are_deduplicated_and_counted() -> None:
    rows = [
        _finding(1, path="/x/a.txt"),
        _finding(2, path="/x/a.txt"),
    ]  # same content, different local id
    with _node([_session("S1")], {"S1": rows}) as (a, _):
        cons = consolidate([fetch_snapshot(HubNode("a", a))])
    assert len(cons.findings) == 1
    assert cons.duplicates_removed == {"a": 1}


def test_dedupe_key_ignores_local_counters_but_not_node_or_session() -> None:
    a, b = _finding(1, path="/x/a.txt"), _finding(99, path="/x/a.txt")
    assert dedupe_key("n", "S1", a) == dedupe_key("n", "S1", b)
    assert dedupe_key("n", "S1", a) != dedupe_key("m", "S1", a)
    assert dedupe_key("n", "S1", a) != dedupe_key("n", "S2", a)


# --- node problems ---------------------------------------------------------------------------


def test_node_down_is_reported_and_the_rest_is_consolidated() -> None:
    with _node([_session("S1")], {"S1": [_finding(1)]}) as (a, _):
        snaps = [
            fetch_snapshot(HubNode("a", a)),
            fetch_snapshot(HubNode("down", "http://127.0.0.1:9")),
        ]
    cons = consolidate(snaps)
    assert [n.status for n in cons.nodes] == ["ok", "failed"]
    assert cons.nodes[1].detail == "connection error"
    assert cons.exit_code == 2
    assert len(cons.findings) == 1


def test_incomplete_newest_session_falls_back_to_the_last_completed_one() -> None:
    sessions = [_session("S2", "running"), _session("S1", "completed")]
    with _node(
        sessions, {"S1": [_finding(1, sid="S1")], "S2": [_finding(7, sid="S2")]}
    ) as (a, _):
        snap = fetch_snapshot(HubNode("a", a))
    assert snap.status == "ok" and snap.session_id == "S1"
    assert "not completed" in snap.detail
    assert [r["id"] for r in snap.findings] == [1]


def test_node_without_any_completed_session_is_reported_not_merged() -> None:
    with _node([_session("S1", "running")], {}) as (a, _):
        snap = fetch_snapshot(HubNode("a", a))
    assert snap.status == "no_completed_session"
    assert consolidate([snap]).findings == []


def test_all_nodes_failing_raises_and_writes_nothing(tmp_path: Path) -> None:
    out = tmp_path / "hub.xlsx"
    with pytest.raises(HubError, match="no node could be consolidated"):
        run_hub_report(_cfg(("a", "http://127.0.0.1:9", "")), out)
    assert not out.exists()


def test_redirect_is_not_followed_and_the_token_is_not_forwarded() -> None:
    with _node([], {}, redirect_to="http://127.0.0.1:1/x") as (url, _):
        snap = fetch_snapshot(HubNode("a", url), token="tok")
    assert snap.status == "failed" and snap.detail == "redirect received (not followed)"


# --- secrets ---------------------------------------------------------------------------------


def test_token_comes_only_from_the_environment_and_never_leaks(tmp_path: Path) -> None:
    with _node([_session("S1")], {"S1": [_finding(1)]}, api_key="s3cr3t-token") as (
        url,
        seen,
    ):
        out = tmp_path / "hub.xlsx"
        cons = run_hub_report(
            _cfg(("a", url, "DATA_BOAR_HUB_KEY_A")),
            out,
            environ={"DATA_BOAR_HUB_KEY_A": "s3cr3t-token"},
        )
    assert cons.exit_code == 0
    assert all(call["key"] == "s3cr3t-token" for call in seen)
    blob = "\n".join(cons.summary_lines()) + out.read_bytes().decode("latin-1")
    assert "s3cr3t-token" not in blob
    assert "127.0.0.1" not in "\n".join(cons.summary_lines())  # URLs are never printed


def test_missing_token_is_reported_as_an_authentication_failure() -> None:
    with _node([_session("S1")], {"S1": []}, api_key="needed") as (url, _):
        snap = fetch_snapshot(HubNode("a", url))
    assert snap.status == "failed" and "authentication rejected" in snap.detail


# --- node configuration ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "node",
    [
        {"id": "a", "url": "http://example.com"},  # plain http only on loopback
        {"id": "a", "url": "https://user:pw@example.com"},  # credentials in the url
        {"id": "a", "url": "https://example.com/?k=v"},  # query in the url
        {"id": "a", "url": "ftp://example.com"},
        {"id": "a", "url": "https://169.254.169.254"},  # link-local (cloud metadata)
        {
            "id": "-x",
            "url": "https://example.com",
        },  # id could start a spreadsheet formula
        {"id": "", "url": "https://example.com"},
    ],
)
def test_invalid_nodes_are_rejected(node: dict) -> None:
    with pytest.raises(HubError):
        parse_hub_nodes({"hub": {"nodes": [node]}})


def test_empty_and_duplicate_nodes_are_rejected() -> None:
    with pytest.raises(HubError, match="empty"):
        parse_hub_nodes({"hub": {"nodes": []}})
    with pytest.raises(HubError, match="duplicate"):
        parse_hub_nodes(
            _cfg(("a", "https://x.example", ""), ("a", "https://y.example", ""))
        )


def test_https_and_loopback_http_are_accepted() -> None:
    nodes = parse_hub_nodes(
        _cfg(
            ("a", "https://boar.example.internal:8088/", ""),
            ("b", "http://[::1]:8088", ""),
        )
    )
    assert nodes[0].base_url == "https://boar.example.internal:8088"
    assert nodes[1].node_id == "b"


def test_config_loader_normalizes_the_hub_section() -> None:
    out = normalize_config(
        {
            "targets": [],
            "hub": {
                "nodes": [
                    {"id": " a ", "url": "https://x.example", "api_key_from_env": "K"},
                    "junk",
                ]
            },
        }
    )
    assert out["hub"]["nodes"] == [
        {"id": "a", "url": "https://x.example", "api_key_from_env": "K"}
    ]
    assert normalize_config({"targets": []})["hub"]["nodes"] == []


# --- workbook --------------------------------------------------------------------------------


def test_workbook_has_summary_findings_with_node_filter_and_notes(
    tmp_path: Path,
) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    with (
        _node(
            [_session("S1")], {"S1": [_finding(1), _finding(2, path="=cmd|calc")]}
        ) as (a, _),
        _node([_session("S1")], {"S1": [_finding(1)]}, version="1.8.1") as (b, _),
    ):
        out = tmp_path / "hub.xlsx"
        cons = run_hub_report(_cfg(("a", a, ""), ("b", b, "")), out)
    assert cons.exit_code == 0
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Summary", "Findings", "Notes"]
    findings = wb["Findings"]
    header = [c.value for c in findings[1]]
    assert header == list(REPORT_COLUMNS) and header[0] == "node_id"
    assert findings.max_row == 1 + 3
    assert findings.auto_filter.ref  # per-node filter
    assert {findings.cell(r, 1).value for r in range(2, findings.max_row + 1)} == {
        "a",
        "b",
    }
    assert {findings.cell(r, 2).value for r in range(2, findings.max_row + 1)} == {
        "1.8.0",
        "1.8.1",
    }
    paths = [
        findings.cell(r, header.index("path") + 1).value
        for r in range(2, findings.max_row + 1)
    ]
    assert "=cmd|calc" not in paths  # spreadsheet formulas are neutralised
    assert any(
        "evidence" in str(row[0].value).lower() for row in wb["Notes"].iter_rows()
    )
    assert (out.stat().st_mode & 0o777) == 0o600


def test_existing_output_needs_overwrite(tmp_path: Path) -> None:
    out = tmp_path / "hub.xlsx"
    out.write_text("old", encoding="utf-8")
    with _node([_session("S1")], {"S1": [_finding(1)]}) as (a, _):
        cfg = _cfg(("a", a, ""))
        with pytest.raises(HubError, match="already exists"):
            run_hub_report(cfg, out)
        assert out.read_text(encoding="utf-8") == "old"
        run_hub_report(cfg, out, overwrite=True)
    assert out.read_bytes()[:2] == b"PK"  # a real xlsx (zip)


# --- tier gate (Enterprise, fail-closed) -----------------------------------------------------


def test_the_hub_is_an_enterprise_feature_in_the_tier_map() -> None:
    assert FEATURE_TIER_MAP["multi_instance_hub"] is Tier.ENTERPRISE
    for tier in (Tier.COMMUNITY, Tier.STD, Tier.PRO, Tier.PRO_PLUS):
        assert not is_feature_available("multi_instance_hub", tier)
    for tier in (Tier.ENTERPRISE, Tier.PARTNER, Tier.OPEN):
        assert is_feature_available("multi_instance_hub", tier)


# --- CLI end to end --------------------------------------------------------------------------


def _write_cfg(tmp_path: Path, node_lines: list[str], *, licensing: str = "") -> Path:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "\n".join(
            [
                f"sqlite_path: {tmp_path / 'audit.db'}",
                "targets: []",
                licensing,
                "hub:",
                "  nodes:",
                *node_lines,
            ]
        ),
        encoding="utf-8",
    )
    return cfg


def _run_cli(cfg: Path, out: Path) -> subprocess.CompletedProcess[str]:
    """Run the CLI hermetically: no license from the developer's own config dir or environment."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("DATA_BOAR_")}
    env["XDG_CONFIG_HOME"] = str(
        out.parent / "xdg-empty"
    )  # default license lookup lives here
    return subprocess.run(
        [sys.executable, "main.py", "--config", str(cfg), "--hub-report", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_cli_consolidates_two_nodes(tmp_path: Path) -> None:
    with (
        _node([_session("S1")], {"S1": [_finding(1)]}) as (a, _),
        _node([_session("S1")], {"S1": [_finding(1)]}) as (b, _),
    ):
        cfg = _write_cfg(
            tmp_path, [f"    - {{id: a, url: '{a}'}}", f"    - {{id: b, url: '{b}'}}"]
        )
        out = tmp_path / "hub.xlsx"
        proc = _run_cli(cfg, out)
    assert proc.returncode == 0, proc.stderr
    assert "nodes_ok=2/2" in proc.stderr and "consolidated_findings=2" in proc.stderr
    assert out.exists()


def test_cli_reports_partial_and_total_failure_with_distinct_exit_codes(
    tmp_path: Path,
) -> None:
    with _node([_session("S1")], {"S1": [_finding(1)]}) as (a, _):
        cfg = _write_cfg(
            tmp_path,
            [
                f"    - {{id: a, url: '{a}'}}",
                "    - {id: down, url: 'http://127.0.0.1:9'}",
            ],
        )
        partial = _run_cli(cfg, tmp_path / "partial.xlsx")
    assert partial.returncode == 2 and "node=down status=FAILED" in partial.stderr
    cfg2 = _write_cfg(tmp_path, ["    - {id: down, url: 'http://127.0.0.1:9'}"])
    none = _run_cli(cfg2, tmp_path / "none.xlsx")
    assert none.returncode == 1 and not (tmp_path / "none.xlsx").exists()


def test_cli_is_blocked_by_the_tier_in_enforced_mode(tmp_path: Path) -> None:
    with _node([_session("S1")], {"S1": [_finding(1)]}) as (a, _):
        cfg = _write_cfg(
            tmp_path,
            [f"    - {{id: a, url: '{a}'}}"],
            licensing="licensing:\n  mode: enforced",
        )
        out = tmp_path / "hub.xlsx"
        proc = _run_cli(cfg, out)
    assert proc.returncode == 2 and "Licensing:" in proc.stderr
    assert not out.exists()


# --- credential gate and untrusted node text (security review follow-up) -----------------------


@pytest.mark.parametrize("env_name", ["PATH", "HOME", "bad name", "1BAD"])
def test_hub_node_env_credential_name_is_validated(env_name: str) -> None:
    with pytest.raises(ValueError):
        parse_hub_nodes(_cfg(("a", "https://x.example", env_name)))


def test_hub_node_env_credential_obeys_the_operator_host_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_BOAR_CREDENTIAL_STRICT", "1")
    monkeypatch.setenv("DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS", "good.example")
    monkeypatch.delenv("DATA_BOAR_CREDENTIAL_HOSTS_UNRESTRICTED", raising=False)
    parse_hub_nodes(_cfg(("a", "https://good.example", "DATA_BOAR_HUB_A_KEY")))
    with pytest.raises(ValueError, match="outside"):
        parse_hub_nodes(_cfg(("b", "https://evil.example", "DATA_BOAR_HUB_B_KEY")))
    # A node without a credential has nothing to exfiltrate: the gate does not apply.
    parse_hub_nodes(_cfg(("c", "https://evil.example", "")))


@pytest.mark.parametrize("bad", ["S1\x1b[2J", "S1\nfake=line", "x" * 200, "a b"])
def test_session_id_with_control_or_odd_characters_fails_the_node(bad: str) -> None:
    with _node([_session(bad)], {bad: [_finding(1, sid=bad)]}) as (a, _):
        snap = fetch_snapshot(HubNode("a", a))
    assert snap.status == "failed"
    assert snap.detail == "session_id has unexpected characters"
    assert bad not in "\n".join(consolidate([snap]).summary_lines())


def test_untrusted_version_is_dropped_not_printed() -> None:
    with _node([_session("S1")], {"S1": [_finding(1)]}, version="1.0\x1b]0;x\x07") as (
        a,
        _,
    ):
        snap = fetch_snapshot(HubNode("a", a))
    assert snap.status == "ok"
    assert snap.node_version == ""
