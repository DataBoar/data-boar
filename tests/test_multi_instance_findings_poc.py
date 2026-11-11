"""Tests for the multi-instance findings CSV PoC (#2208 Phase 0), with simulated nodes."""

from __future__ import annotations

import importlib.util
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "multi_instance_findings_poc.py"
)
_spec = importlib.util.spec_from_file_location("multi_instance_findings_poc", _PATH)
assert _spec and _spec.loader
poc = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = poc  # dataclasses resolves string annotations via sys.modules
_spec.loader.exec_module(poc)

HEADER = (
    "id,session_id,source_type,target_name,path,file_name,data_type,schema_name,table_name,"
    "column_name,sensitivity_level,pattern_detected,norm_tag,ml_confidence,source_mtime_ns,"
    "source_size,content_fingerprint,created_at"
)


def _csv(rows: list[tuple[str, str]]) -> str:
    """Synthetic findings: (id, session_id) pairs; no real data."""
    lines = [HEADER]
    for rid, sid in rows:
        lines.append(
            f"{rid},{sid},filesystem,t,/synthetic/{rid}.txt,{rid}.txt,CPF,,,,HIGH,x,LGPD,,,,,"
            "2026-01-01"
        )
    return "\r\n".join(lines) + "\r\n"


@contextmanager
def _node(
    body: str = "", status: int = 200, location: str | None = None
) -> Iterator[tuple[str, list[dict]]]:
    seen: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            seen.append({"path": self.path, "key": self.headers.get("X-API-Key")})
            self.send_response(status)
            if location:
                self.send_header("Location", location)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            data = body.encode()
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", seen
    finally:
        server.shutdown()
        server.server_close()


def _run(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = poc.main(args)
    return code, capsys.readouterr().err


def test_merge_adds_provenance_and_keeps_colliding_session_ids(
    tmp_path: Path, capsys
) -> None:
    out = tmp_path / "merged.csv"
    with (
        _node(_csv([("1", "S1"), ("2", "S1")])) as (url_a, _),
        _node(_csv([("1", "S1")])) as (
            url_b,
            _,
        ),
    ):
        code, err = _run(
            ["--node", f"a={url_a}", "--node", f"b={url_b}", "--out", str(out)], capsys
        )
    assert code == 0
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("node_id,fetched_at_utc,id,session_id")
    assert (
        len(lines) == 4
    )  # header + 2 rows from a + 1 row from b (same id + session_id kept apart)
    assert sum(1 for line in lines[1:] if line.startswith("a,")) == 2
    assert sum(1 for line in lines[1:] if line.startswith("b,")) == 1
    assert "merged_rows=3 nodes_ok=2/2" in err


def test_node_down_is_reported_and_others_still_merged(tmp_path: Path, capsys) -> None:
    out = tmp_path / "merged.csv"
    with _node(_csv([("1", "S1")])) as (url_a, _):
        # nothing listens on port 9 on loopback
        code, err = _run(
            [
                "--node",
                f"a={url_a}",
                "--node",
                "down=http://127.0.0.1:9",
                "--out",
                str(out),
            ],
            capsys,
        )
    assert code == 2
    assert "node=down status=FAIL reason=connection error" in err
    assert "127.0.0.1" not in err  # URLs are never printed
    assert out.exists()


def test_token_comes_from_env_and_never_appears_in_output(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.setenv("DATA_BOAR_NODE_TOKEN_SITE_A", "s3cr3t-token")
    out = tmp_path / "merged.csv"
    with _node(_csv([("1", "S1")])) as (url, seen):
        code, err = _run(["--node", f"site-a={url}", "--out", str(out)], capsys)
    assert code == 0
    assert seen[0]["key"] == "s3cr3t-token"
    assert seen[0]["path"] == "/findings/csv"
    assert "s3cr3t-token" not in err
    assert "s3cr3t-token" not in out.read_text(encoding="utf-8")


def test_redirect_is_not_followed_and_token_is_not_forwarded(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.setenv("DATA_BOAR_NODE_TOKEN_A", "tok")
    with (
        _node(_csv([("9", "S9")])) as (target, target_seen),
        _node("", 302, f"{target}/findings/csv") as (url, _),
    ):
        code, err = _run(
            ["--node", f"a={url}", "--out", str(tmp_path / "m.csv")], capsys
        )
    assert code == 1
    assert "redirect received (not followed)" in err
    assert target_seen == []


def test_unexpected_header_and_404_are_failures(tmp_path: Path, capsys) -> None:
    with _node("a,b\r\n1,2\r\n") as (bad, _), _node("not found", 404) as (empty, _):
        code, err = _run(
            [
                "--node",
                f"bad={bad}",
                "--node",
                f"empty={empty}",
                "--out",
                str(tmp_path / "m.csv"),
            ],
            capsys,
        )
    assert code == 1
    assert "unexpected CSV header" in err
    assert "HTTP 404" in err
    assert not (tmp_path / "m.csv").exists()


def test_duplicate_rows_from_same_node_are_deduped() -> None:
    body = _csv([("1", "S1"), ("1", "S1")])
    node = poc.Node("a", "http://127.0.0.1:1")
    _, rows, results = poc.merge_nodes([node], lambda _n: body)
    assert len(rows) == 1
    assert results[0].duplicates == 1


@pytest.mark.parametrize(
    "spec",
    [
        "nourl",
        "=cmd=http://127.0.0.1:1",
        "-x=http://127.0.0.1:1",
        "a=http://example.com",  # plain http only on loopback
        "a=https://user:pw@example.com",  # credentials in URL
        "a=https://example.com/?k=v",  # query in URL
        "a=ftp://example.com",
    ],
)
def test_invalid_node_specs_are_rejected(spec: str) -> None:
    with pytest.raises(ValueError):
        poc.parse_node_spec(spec)


def test_https_node_and_loopback_http_are_accepted() -> None:
    node = poc.parse_node_spec("a=https://boar.example.internal:8088/")
    assert node.base_url == "https://boar.example.internal:8088"
    assert poc.parse_node_spec("b=http://localhost:8088").node_id == "b"
    assert poc.parse_node_spec("c=http://[::1]:8088").node_id == "c"


def test_duplicate_node_ids_and_repo_output_are_refused(tmp_path: Path, capsys) -> None:
    code, err = _run(
        [
            "--node",
            "a=http://127.0.0.1:1",
            "--node",
            "a=http://127.0.0.1:2",
            "--out",
            str(tmp_path / "m.csv"),
        ],
        capsys,
    )
    assert code == 1 and "duplicate NODE_ID" in err
    inside_repo = (
        Path(poc.__file__).resolve().parents[1] / "merged_should_not_exist.csv"
    )
    with _node(_csv([("1", "S1")])) as (url, _):
        code, err = _run(["--node", f"a={url}", "--out", str(inside_repo)], capsys)
    assert code == 1 and "outside the repository tree" in err
    assert not inside_repo.exists()


def test_existing_out_requires_overwrite(tmp_path: Path, capsys) -> None:
    out = tmp_path / "m.csv"
    out.write_text("old", encoding="utf-8")
    with _node(_csv([("1", "S1")])) as (url, _):
        code, _err = _run(["--node", f"a={url}", "--out", str(out)], capsys)
        assert code == 1 and out.read_text(encoding="utf-8") == "old"
        code, _err = _run(
            ["--node", f"a={url}", "--out", str(out), "--overwrite"], capsys
        )
    assert code == 0 and out.read_text(encoding="utf-8").startswith("node_id,")


def test_response_over_max_bytes_is_a_failure(tmp_path: Path, capsys) -> None:
    with _node(_csv([("1", "S1")])) as (url, _):
        code, err = _run(
            [
                "--node",
                f"a={url}",
                "--out",
                str(tmp_path / "m.csv"),
                "--max-bytes",
                "50",
            ],
            capsys,
        )
    assert code == 1 and "larger than --max-bytes" in err


def test_merged_csv_neutralises_formula_cells_and_header_names(tmp_path: Path) -> None:
    """CWE-1236: node-supplied cells and extra column names must not open as formulas."""
    out = tmp_path / "merged.csv"
    names = ["node_id", "path", "=HYPERLINK(1)"]
    rows = [
        {"node_id": "a", "path": "=cmd|' /C calc'!A0", "=HYPERLINK(1)": "@SUM(1)"},
        {"node_id": "a", "path": "-2+3", "=HYPERLINK(1)": "ok"},
    ]
    poc.write_merged_csv(out, names, rows, overwrite=False)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "node_id,path,'=HYPERLINK(1)"
    for line in lines[1:]:
        for cell in line.split(","):
            assert not cell.startswith(("=", "+", "-", "@"))
    assert "'=cmd|" in lines[1] and "'@SUM(1)" in lines[1]
    assert "'-2+3" in lines[2]
