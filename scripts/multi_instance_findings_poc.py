#!/usr/bin/env python3
"""Phase 0 proof of concept for the multi-instance report hub (#2208).

Pulls ``GET /findings/csv`` (latest session) from several Data Boar nodes and merges the rows
into ONE CSV, adding the provenance the API does not emit today: ``node_id`` (an operator-chosen
label) and ``fetched_at_utc``. The unified findings CSV has no node/host column and ``session_id``
is local to each node, so a plain concatenation would lose where each row came from.

This is a documented PoC, NOT a centralization feature. Runbook:
``docs/ops/MULTI_INSTANCE_FINDINGS_CSV_POC.md``.

Usage::

    export DATA_BOAR_NODE_TOKEN_SITE_A=...   # only if that node has api.require_api_key
    uv run python scripts/multi_instance_findings_poc.py \\
        --node site-a=https://boar-a.example.internal:8088 \\
        --node site-b=http://127.0.0.1:8089 \\
        --out /secure/location/merged_findings.csv

Safety rules (kept deliberately small for the PoC):

* tokens come ONLY from environment variables (``DATA_BOAR_NODE_TOKEN_<NODE_ID>``), never argv;
* ``https`` is required, except for loopback hosts (lab/demo);
* redirects are never followed (a token must not travel to another host);
* node URLs and tokens are never printed or written to the output;
* the merged CSV may not be written inside this repository tree (it holds paths and hostnames).

Exit codes: 0 all nodes merged; 2 partial (some nodes failed, the rest were merged); 1 nothing
merged or invalid usage.
"""

from __future__ import annotations

import argparse
import csv
import io
import ipaddress
import os
import re
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import requests

_REPO_ROOT = Path(__file__).resolve().parents[1]
# Starts alphanumeric: a leading "-", "=", "+" or "@" would be a spreadsheet formula trigger.
_NODE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_REQUIRED_COLUMNS = frozenset({"session_id", "source_type", "sensitivity_level"})
PROVENANCE_COLUMNS = ("node_id", "fetched_at_utc")
TOKEN_ENV_PREFIX = "DATA_BOAR_NODE_TOKEN_"
DEFAULT_TIMEOUT_S = 30.0
DEFAULT_MAX_BYTES = 64 * 1024 * 1024


class NodeError(Exception):
    """Per-node failure. The message is a short, safe category (never a URL or token)."""


@dataclass(frozen=True)
class Node:
    node_id: str
    base_url: str


@dataclass
class NodeResult:
    node_id: str
    ok: bool
    rows: int = 0
    duplicates: int = 0
    detail: str = ""


def _is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def parse_node_spec(spec: str) -> Node:
    """Parse ``NODE_ID=URL`` and validate both halves."""
    node_id, sep, url = spec.partition("=")
    if not sep or not _NODE_ID_RE.match(node_id):
        raise ValueError(
            "--node must be NODE_ID=URL; NODE_ID is 1-64 chars of letters, digits, '_', '.', '-' "
            "and starts with a letter or digit"
        )
    parts = urlsplit(url)
    host = parts.hostname or ""
    if parts.scheme not in {"https", "http"} or not host:
        raise ValueError(f"node {node_id!r}: URL must be http(s) with a host")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError(
            f"node {node_id!r}: URL must not contain credentials, query or fragment "
            "(tokens go in the environment)"
        )
    if parts.scheme == "http" and not _is_loopback(host):
        raise ValueError(
            f"node {node_id!r}: plain http is allowed only for loopback hosts"
        )
    return Node(node_id=node_id, base_url=url.rstrip("/"))


def token_env_name(node_id: str) -> str:
    return TOKEN_ENV_PREFIX + re.sub(r"[^A-Za-z0-9]", "_", node_id).upper()


def fetch_findings_csv(
    node: Node,
    token: str | None,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> str:
    """Return the node's latest-session findings CSV text, or raise ``NodeError``."""
    url = f"{node.base_url}/findings/csv"
    headers = {"Accept": "text/csv"}
    if token:
        headers["X-API-Key"] = token
    session = requests.Session()
    if _is_loopback(urlsplit(url).hostname or ""):
        session.trust_env = (
            False  # never route lab/loopback traffic through an env proxy
        )
    chunks: list[bytes] = []
    total = 0
    try:
        with session.get(
            url, headers=headers, timeout=timeout, allow_redirects=False, stream=True
        ) as resp:
            status = resp.status_code
            if 300 <= status < 400:
                raise NodeError("redirect received (not followed)")
            if status == 404:
                raise NodeError("no scan session on node (HTTP 404)")
            if status in (401, 403):
                raise NodeError(f"authentication rejected (HTTP {status})")
            if status != 200:
                raise NodeError(f"unexpected HTTP {status}")
            for chunk in resp.iter_content(chunk_size=65536):
                total += len(chunk)
                if total > max_bytes:
                    raise NodeError("response larger than --max-bytes")
                chunks.append(chunk)
    except requests.Timeout:
        raise NodeError("timeout") from None
    except requests.exceptions.SSLError:
        raise NodeError("TLS error") from None
    except requests.RequestException:
        raise NodeError("connection error") from None
    try:
        return b"".join(chunks).decode("utf-8-sig")
    except UnicodeDecodeError:
        raise NodeError("response is not valid UTF-8") from None


def parse_findings_csv(text: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(text))
    fields = list(reader.fieldnames or [])
    if not _REQUIRED_COLUMNS.issubset(fields):
        raise NodeError("unexpected CSV header (not a Data Boar findings export)")
    rows = [{k: (v or "") for k, v in row.items() if k in fields} for row in reader]
    return fields, rows


def merge_nodes(
    nodes: Sequence[Node],
    fetch: Callable[[Node], str],
    *,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> tuple[list[str], list[dict[str, str]], list[NodeResult]]:
    """Fetch every node, tag rows with provenance and dedupe on (node_id, session_id, id)."""
    fieldnames: list[str] = list(PROVENANCE_COLUMNS)
    merged: list[dict[str, str]] = []
    results: list[NodeResult] = []
    seen: set[tuple[str, ...]] = set()
    for node in nodes:
        try:
            fields, rows = parse_findings_csv(fetch(node))
        except NodeError as exc:
            results.append(NodeResult(node.node_id, ok=False, detail=str(exc)))
            continue
        fetched_at = now().astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        for name in fields:
            if name not in fieldnames:
                fieldnames.append(name)
        added = dupes = 0
        for row in rows:
            row_id = row.get("id", "")
            key = (
                (node.node_id, row.get("session_id", ""), row_id)
                if row_id
                else (node.node_id, *[f"{k}={v}" for k, v in sorted(row.items())])
            )
            if key in seen:
                dupes += 1
                continue
            seen.add(key)
            merged.append(
                {"node_id": node.node_id, "fetched_at_utc": fetched_at, **row}
            )
            added += 1
        results.append(NodeResult(node.node_id, ok=True, rows=added, duplicates=dupes))
    return fieldnames, merged, results


def write_merged_csv(
    out: Path,
    fieldnames: Sequence[str],
    rows: Sequence[dict[str, str]],
    *,
    overwrite: bool,
) -> None:
    resolved = out.expanduser().resolve()
    if resolved == _REPO_ROOT or _REPO_ROOT in resolved.parents:
        raise ValueError(
            "--out must be outside the repository tree (the merged CSV holds paths and hostnames)"
        )
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if overwrite else os.O_EXCL)
    fd = os.open(resolved, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(fieldnames), restval="", lineterminator="\r\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--node",
        action="append",
        required=True,
        metavar="NODE_ID=URL",
        help="repeat per node",
    )
    parser.add_argument(
        "--out", required=True, type=Path, help="merged CSV path (outside repo)"
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument(
        "--overwrite", action="store_true", help="replace an existing --out file"
    )
    args = parser.parse_args(argv)

    try:
        nodes = [parse_node_spec(spec) for spec in args.node]
        if len({n.node_id for n in nodes}) != len(nodes):
            raise ValueError("duplicate NODE_ID in --node")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    def _fetch(node: Node) -> str:
        return fetch_findings_csv(
            node,
            os.environ.get(token_env_name(node.node_id)) or None,
            timeout=args.timeout,
            max_bytes=args.max_bytes,
        )

    fieldnames, rows, results = merge_nodes(nodes, _fetch)
    for res in results:
        if res.ok:
            print(
                f"node={res.node_id} status=OK rows={res.rows} duplicates={res.duplicates}",
                file=sys.stderr,
            )
        else:
            print(
                f"node={res.node_id} status=FAIL reason={res.detail}", file=sys.stderr
            )
    ok_nodes = sum(1 for r in results if r.ok)
    if ok_nodes == 0:
        print("error: no node could be merged; nothing written", file=sys.stderr)
        return 1
    try:
        write_merged_csv(args.out, fieldnames, rows, overwrite=args.overwrite)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(
        f"merged_rows={len(rows)} nodes_ok={ok_nodes}/{len(results)}", file=sys.stderr
    )
    return 0 if ok_nodes == len(results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
