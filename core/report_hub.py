"""Multi-instance report hub (#2208).

A central instance **pulls** the findings of several Data Boar nodes through each node's existing API
(``/list``, ``/findings/{session_id}``, ``/about/json``) and consolidates them into one Excel report.

Design (ADR-0095):

* Every consolidated row carries provenance (``node_id``, ``node_version``, ``node_session_id``,
  ``fetched_at_utc``) and a stable ``dedupe_key`` built from the finding's content plus its node and
  session. Local row ids and session ids are **not** unique across nodes, so they never decide identity.
* Only **completed** sessions are consolidated. If a node's newest session is still running or failed,
  the hub falls back to its newest completed one and says so; a node without any completed session
  is reported, not merged.
* Evidence, not a legal conclusion. Findings are metadata only; paths and host names are already
  sensitive, so nothing here logs a URL, a token or a path.

The feature is Enterprise (``multi_instance_hub``, fail-closed in the tier map).
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

import requests

from report.excel_sanitizer import excel_sanitize_cell

FEATURE = "multi_instance_hub"
DEFAULT_TIMEOUT_S = 30.0
DEFAULT_MAX_BYTES = 64 * 1024 * 1024

_NODE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

FINDING_FIELDS = (
    "source_type",
    "target_name",
    "path",
    "file_name",
    "data_type",
    "schema_name",
    "table_name",
    "column_name",
    "sensitivity_level",
    "pattern_detected",
    "norm_tag",
    "ml_confidence",
)
PROVENANCE_FIELDS = ("node_id", "node_version", "node_session_id", "fetched_at_utc")
REPORT_COLUMNS = (*PROVENANCE_FIELDS, *FINDING_FIELDS, "dedupe_key")
# Identity of a finding inside one node and session: what and where, never local counters or scores.
_DEDUPE_FIELDS = (
    "source_type",
    "target_name",
    "path",
    "file_name",
    "data_type",
    "schema_name",
    "table_name",
    "column_name",
    "pattern_detected",
    "norm_tag",
)


class HubError(Exception):
    """Configuration or output problem. Messages never carry a URL, a token or a path."""


class NodeError(HubError):
    """A single node could not be read. The message is a short, safe category."""


@dataclass(frozen=True)
class HubNode:
    node_id: str
    base_url: str
    api_key_env: str = ""


def _is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _validate_url(node_id: str, url: str) -> str:
    parts = urlsplit(url)
    host = parts.hostname or ""
    if parts.scheme not in {"https", "http"} or not host:
        raise HubError(f"hub node {node_id!r}: url must be http(s) with a host")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise HubError(
            f"hub node {node_id!r}: url must not contain credentials, query or fragment "
            "(use api_key_from_env)"
        )
    if parts.scheme == "http" and not _is_loopback(host):
        raise HubError(
            f"hub node {node_id!r}: plain http is allowed only for loopback hosts"
        )
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None and (ip.is_link_local or ip.is_unspecified or ip.is_multicast):
        raise HubError(
            f"hub node {node_id!r}: link-local, unspecified and multicast hosts are refused"
        )
    return url.rstrip("/")


def parse_hub_nodes(cfg: Mapping[str, Any]) -> list[HubNode]:
    """Read and validate ``hub.nodes`` from the loaded config."""
    hub = cfg.get("hub") if isinstance(cfg.get("hub"), dict) else {}
    raw = hub.get("nodes")
    if not isinstance(raw, list) or not raw:
        raise HubError("hub.nodes is empty: configure at least one node")
    nodes: list[HubNode] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise HubError("each hub node must be a mapping with id and url")
        node_id = str(item.get("id") or "").strip()
        if not _NODE_ID_RE.match(node_id):
            raise HubError(
                "hub node id must be 1-64 characters of letters, digits, '_', '.', '-' "
                "and start with a letter or digit"
            )
        if node_id in seen:
            raise HubError(f"duplicate hub node id {node_id!r}")
        seen.add(node_id)
        base_url = _validate_url(node_id, str(item.get("url") or "").strip())
        nodes.append(
            HubNode(node_id, base_url, str(item.get("api_key_from_env") or "").strip())
        )
    return nodes


def _get_json(
    node: HubNode, path: str, *, token: str | None, timeout: float, max_bytes: int
) -> Any:
    url = f"{node.base_url}{path}"
    headers = {"Accept": "application/json"}
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
            if status in (401, 403):
                raise NodeError(f"authentication rejected (HTTP {status})")
            if status == 404:
                raise NodeError("not found on node (HTTP 404)")
            if status != 200:
                raise NodeError(f"unexpected HTTP {status}")
            for chunk in resp.iter_content(chunk_size=65536):
                total += len(chunk)
                if total > max_bytes:
                    raise NodeError("response larger than hub.max_bytes")
                chunks.append(chunk)
    except requests.Timeout:
        raise NodeError("timeout") from None
    except requests.exceptions.SSLError:
        raise NodeError("TLS error") from None
    except requests.RequestException:
        raise NodeError("connection error") from None
    try:
        return json.loads(b"".join(chunks).decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise NodeError("response is not valid JSON") from None


@dataclass
class NodeSnapshot:
    node_id: str
    status: str  # "ok" | "failed" | "no_completed_session"
    detail: str = ""
    node_version: str = ""
    session_id: str = ""
    session_status: str = ""
    fetched_at: str = ""
    findings: list[dict[str, Any]] = field(default_factory=list)


def _utc(now: Callable[[], datetime]) -> str:
    return now().astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_snapshot(
    node: HubNode,
    *,
    token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
    max_bytes: int = DEFAULT_MAX_BYTES,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> NodeSnapshot:
    """Read the newest **completed** session of one node. Never raises for a node-level problem."""
    fetched_at = _utc(now)
    try:
        listing = _get_json(
            node, "/list", token=token, timeout=timeout, max_bytes=max_bytes
        )
        sessions = listing.get("sessions") if isinstance(listing, dict) else None
        if not isinstance(sessions, list):
            raise NodeError("unexpected /list response")
        completed = [
            s
            for s in sessions
            if isinstance(s, dict) and s.get("status") == "completed"
        ]
        if not completed:
            return NodeSnapshot(
                node.node_id,
                "no_completed_session",
                "no completed scan session on node",
                fetched_at=fetched_at,
            )
        chosen = completed[0]
        session_id = str(chosen.get("session_id") or "")
        if not session_id:
            raise NodeError("completed session without session_id")
        note = ""
        if sessions and sessions[0] is not chosen:
            note = "newest session is not completed; using the newest completed one"
        data = _get_json(
            node,
            f"/findings/{quote(session_id, safe='')}",
            token=token,
            timeout=timeout,
            max_bytes=max_bytes,
        )
        rows = data.get("findings") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise NodeError("unexpected /findings response")
        version = ""
        try:
            about = _get_json(
                node, "/about/json", token=token, timeout=timeout, max_bytes=max_bytes
            )
            version = str(about.get("version") or "") if isinstance(about, dict) else ""
        except NodeError:
            version = ""  # the version is provenance, not a reason to drop the node
        return NodeSnapshot(
            node.node_id,
            "ok",
            note,
            version,
            session_id,
            "completed",
            fetched_at,
            [r for r in rows if isinstance(r, dict)],
        )
    except NodeError as exc:
        return NodeSnapshot(node.node_id, "failed", str(exc), fetched_at=fetched_at)


def dedupe_key(node_id: str, session_id: str, row: Mapping[str, Any]) -> str:
    """Stable identity: node + session + the finding's content, never a local counter."""
    parts = [
        node_id,
        session_id,
        *(str(row.get(f) if row.get(f) is not None else "") for f in _DEDUPE_FIELDS),
    ]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class Consolidation:
    findings: list[dict[str, Any]]
    nodes: list[NodeSnapshot]
    duplicates_removed: dict[str, int]
    generated_at: str

    @property
    def nodes_ok(self) -> int:
        return sum(1 for n in self.nodes if n.status == "ok")

    @property
    def exit_code(self) -> int:
        """0 all nodes consolidated, 2 partial, 1 nothing consolidated."""
        if self.nodes_ok == 0:
            return 1
        return 0 if self.nodes_ok == len(self.nodes) else 2

    def summary_lines(self) -> list[str]:
        lines = []
        for n in self.nodes:
            if n.status == "ok":
                count = sum(1 for r in self.findings if r["node_id"] == n.node_id)
                dup = self.duplicates_removed.get(n.node_id, 0)
                extra = f" note={n.detail}" if n.detail else ""
                lines.append(
                    f"node={n.node_id} status=OK session={n.session_id} findings={count} "
                    f"duplicates_removed={dup}{extra}"
                )
            else:
                lines.append(
                    f"node={n.node_id} status={n.status.upper()} reason={n.detail}"
                )
        lines.append(
            f"consolidated_findings={len(self.findings)} nodes_ok={self.nodes_ok}/{len(self.nodes)}"
        )
        return lines


def consolidate(
    snapshots: list[NodeSnapshot],
    *,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Consolidation:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    removed: dict[str, int] = {}
    for snap in snapshots:
        if snap.status != "ok":
            continue
        for raw in snap.findings:
            key = dedupe_key(snap.node_id, snap.session_id, raw)
            if key in seen:
                removed[snap.node_id] = removed.get(snap.node_id, 0) + 1
                continue
            seen.add(key)
            row: dict[str, Any] = {
                "node_id": snap.node_id,
                "node_version": snap.node_version,
                "node_session_id": snap.session_id,
                "fetched_at_utc": snap.fetched_at,
            }
            row.update({f: raw.get(f) for f in FINDING_FIELDS})
            row["dedupe_key"] = key
            rows.append(row)
    return Consolidation(rows, snapshots, removed, _utc(now))


_NOTES = (
    "This workbook consolidates metadata-only findings pulled from several Data Boar instances.",
    "It is technical evidence to support a review, not a legal conclusion.",
    "Only the newest COMPLETED scan session of each node is consolidated.",
    "Each row keeps its node and session. Local row ids and session ids are not unique across nodes.",
    "dedupe_key = hash of node, session and the finding's content (what and where).",
    "Paths and host names are sensitive: store and share this file accordingly.",
)


def write_report_xlsx(
    path: Path, cons: Consolidation, *, overwrite: bool = False
) -> None:
    """Write the consolidated workbook (Summary, Findings with a per-node filter, Notes)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    out = Path(path)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if overwrite else os.O_EXCL)
    try:
        fd = os.open(out, flags, 0o600)
    except FileExistsError:
        raise HubError(
            "output file already exists (use --hub-overwrite to replace it)"
        ) from None
    except OSError:
        raise HubError("cannot create the output file") from None

    wb = Workbook()
    summary = wb.active
    summary.title = "Summary"
    summary.append(["Multi-instance report hub", f"generated {cons.generated_at}"])
    summary["A1"].font = Font(bold=True)
    summary.append([])
    header = [
        "node_id",
        "status",
        "detail",
        "node_version",
        "session_id",
        "session_status",
        "findings",
        "duplicates_removed",
        "fetched_at_utc",
    ]
    summary.append(header)
    for cell in summary[3]:
        cell.font = Font(bold=True)
    for n in cons.nodes:
        count = sum(1 for r in cons.findings if r["node_id"] == n.node_id)
        summary.append(
            [
                excel_sanitize_cell(v)
                for v in (
                    n.node_id,
                    n.status,
                    n.detail,
                    n.node_version,
                    n.session_id,
                    n.session_status,
                    count,
                    cons.duplicates_removed.get(n.node_id, 0),
                    n.fetched_at,
                )
            ]
        )

    sheet = wb.create_sheet("Findings")
    sheet.append(list(REPORT_COLUMNS))
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in cons.findings:
        sheet.append([excel_sanitize_cell(row.get(c)) for c in REPORT_COLUMNS])
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    notes = wb.create_sheet("Notes")
    for line in _NOTES:
        notes.append([line])

    with os.fdopen(fd, "wb") as handle:
        wb.save(handle)


def run_hub_report(
    cfg: Mapping[str, Any],
    out: Path,
    *,
    overwrite: bool = False,
    fetch: Callable[..., NodeSnapshot] = fetch_snapshot,
    environ: Mapping[str, str] | None = None,
) -> Consolidation:
    """Pull every configured node, consolidate and write the workbook.

    Raises ``HubError`` when the configuration is invalid, when no node could be consolidated, or
    when the output cannot be written. A partial result (some nodes failed) is returned normally;
    check ``Consolidation.exit_code``.
    """
    env = os.environ if environ is None else environ
    hub = cfg.get("hub") if isinstance(cfg.get("hub"), dict) else {}
    timeout = float(hub.get("timeout_seconds") or DEFAULT_TIMEOUT_S)
    max_bytes = int(hub.get("max_bytes") or DEFAULT_MAX_BYTES)
    snapshots = [
        fetch(
            node,
            token=(env.get(node.api_key_env) or None) if node.api_key_env else None,
            timeout=timeout,
            max_bytes=max_bytes,
        )
        for node in parse_hub_nodes(cfg)
    ]
    cons = consolidate(snapshots)
    if cons.nodes_ok == 0:
        raise HubError("no node could be consolidated; nothing written")
    write_report_xlsx(out, cons, overwrite=overwrite)
    return cons
