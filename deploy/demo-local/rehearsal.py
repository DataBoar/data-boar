"""Rehearsal engine for the local demo harness (#1447).

For each case: restart Boar with a one-target config (``boar.sh``), sample
memory every 2 s (``podman stats`` for containers, /proc RSS for a native
Boar) plus the cgroup ``memory.peak`` high-water mark, POST /scan, wait,
then compare findings with what the corpus/seeds were DESIGNED to contain.
Linux host tool; stdlib only. Never reads or prints a secret.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUDGET_MB = 300.0  # VPS budget for the target containers (Boar excluded)
SAMPLE_S = 2.0
SCAN_TIMEOUT_S = 300

_UNITS = {
    "b": 1,
    "kb": 1e3,
    "mb": 1e6,
    "gb": 1e9,
    "kib": 1024,
    "mib": 1024**2,
    "gib": 1024**3,
}

# Containers in priority order for the cut rule (SMB with archives comes first).
CONTAINER_PRIORITY = ["dbdl-smb", "dbdl-pg", "dbdl-redis", "dbdl-mongo", "dbdl-web"]


@dataclass
class Case:
    label: str
    only: str  # target name(s) rendered into the config
    container: str  # target container sampled
    variant: str = ""
    # Designed key findings: (kind, name-fragment, pattern-fragment).
    # kind "db": name = "table.column"; kind "fs": name = file_name.
    key: list[tuple[str, str, str]] = field(default_factory=list)
    exact_fs: int | None = None  # exact number of filesystem findings
    failures: list[tuple[str, str]] = field(default_factory=list)  # (reasons|, file)
    no_failures: bool = True
    note: str = ""


_CPF_EMAIL = "LGPD_CPF"
BUG_TARBZ2 = (
    "bug do conector SMB: o arquivo temporario usa so o ultimo sufixo (.bz2), "
    "entao o tar interno nao e lido e nada e reportado"
)
SMB_ALL = [
    ("fs", "cadastro.zip|cadastro.csv", _CPF_EMAIL),
    ("fs", "cadastro.tgz|cadastro.csv", _CPF_EMAIL),
    ("fs", "cadastro.tar.bz2|cadastro.csv", _CPF_EMAIL),
    ("fs", "protegido_demo.7z|cadastro.csv", _CPF_EMAIL),
]


def cases() -> list[Case]:
    smb = "Demo_SMB_Compressed"
    # SMB stages the archive in a temp file, so scan_failures.details names
    # `tmpXXXX.7z`, not protegido_demo.7z: match on the suffix.
    out = [
        Case(
            "Lab_Postgres (lab)",
            "Lab_Postgres",
            "dbdl-pg",
            key=[
                ("db", "lab_customers.national_id", "LGPD_CPF"),
                ("db", "lab_customers.contact_email", "EMAIL"),
                ("db", "lab_guardians.cpf", "LGPD_CPF"),
                ("db", "lab_guardians.email", "EMAIL"),
            ],
        ),
        Case(
            "SMB compactados (4 arquivos)",
            smb,
            "dbdl-smb",
            key=SMB_ALL,
            exact_fs=4,
            note=BUG_TARBZ2,
        ),
        Case(
            "SMB: 7z com senha",
            smb,
            "dbdl-smb",
            "7z-password",
            key=[SMB_ALL[3]],
            exact_fs=1,
        ),
        Case(
            "SMB: 7z SEM senha",
            smb,
            "dbdl-smb",
            "7z-no-password",
            exact_fs=0,
            failures=[("encrypted_no_password", ".7z")],
            no_failures=False,
        ),
        Case(
            "SMB: 7z senha errada",
            smb,
            "dbdl-smb",
            "7z-wrong-password",
            exact_fs=0,
            no_failures=False,
            failures=[("wrong_password|archive_read_error", ".7z")],
            note="py7zr 1.1.4 reports archive_read_error here",
        ),
        Case("SMB: zip", smb, "dbdl-smb", "zip", key=[SMB_ALL[0]], exact_fs=1),
        Case("SMB: tgz", smb, "dbdl-smb", "tgz", key=[SMB_ALL[1]], exact_fs=1),
        Case(
            "SMB: tar.bz2",
            smb,
            "dbdl-smb",
            "tar.bz2",
            key=[SMB_ALL[2]],
            exact_fs=1,
            note=BUG_TARBZ2,
        ),
        Case(
            "Lab_Redis",
            "Lab_Redis",
            "dbdl-redis",
            key=[("db", f"keys.u:{n}", "") for n in range(1001, 1007)],
        ),
        Case(
            "Lab_Mongo",
            "Lab_Mongo",
            "dbdl-mongo",
            key=[
                ("db", "lab_people.doc", "LGPD_CPF"),
                ("db", "lab_people.email", "EMAIL"),
            ],
        ),
        Case(
            "Supabase_Simulated (PG17 local)",
            "Supabase_Simulated",
            "dbdl-pg",
            key=[
                ("db", "clientes_sim.cpf", "LGPD_CPF"),
                ("db", "clientes_sim.email", "EMAIL"),
            ],
        ),
    ]
    if (HERE / "web.sh").exists():
        out += [
            Case(
                "WebDAV_Demo",
                "WebDAV_Demo",
                "dbdl-web",
                key=[("fs", "cadastro_webdav.csv", "LGPD_CPF")],
                exact_fs=1,
                note="webdavclient3 3.14.7 list(get_info=True) returns name=None/size, "
                "the connector reads name/content_length: silent zero, no failure",
            ),
            Case(
                "REST_Demo (/people)",
                "REST_Demo",
                "dbdl-web",
                key=[
                    ("app", "GET /people | cpf", "LGPD_CPF"),
                    ("app", "GET /people | email", "EMAIL"),
                ],
                note="REST findings are stored as application_findings",
            ),
        ]
    return out


# --------------------------------------------------------------------- helpers
def _run(cmd: list[str], timeout: int = 120) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:3])} failed: {r.stderr.strip()[-300:]}")
    return r.stdout


def _mb(text: str) -> float:
    """'12.3MB' / '1.2GiB' -> megabytes (10^6)."""
    t = text.strip().lower()
    i = len(t)
    while i and not (t[i - 1].isdigit() or t[i - 1] == "."):
        i -= 1
    return float(t[:i]) * _UNITS.get(t[i:] or "b", 1) / 1e6


_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _http(url: str, data: bytes | None = None) -> dict:
    """GET/POST JSON to the local Boar only: http(s) on a loopback host."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in _LOOPBACK_HOSTS:
        raise ValueError("rehearsal only talks to http(s) on loopback")
    req = urllib.request.Request(url, data=data)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    # B310: scheme and host are restricted to http(s) on loopback just above.
    with urllib.request.urlopen(req, timeout=20) as resp:  # nosec B310  # noqa: S310
        return json.loads(resp.read())


def _cgroup_peak_fd(container: str):
    """Open memory.peak of a container cgroup and reset its watermark (kernel >= 6.12)."""
    try:
        cg = _run(
            ["podman", "inspect", container, "--format", "{{.State.CgroupPath}}"]
        ).strip()
        fh = open(f"/sys/fs/cgroup{cg}/memory.peak", "r+")  # noqa: SIM115
        fh.write("0")
        fh.flush()
        return fh
    except (OSError, RuntimeError):
        return None


def _read_peak_mb(fh) -> float | None:
    if fh is None:
        return None
    try:
        fh.seek(0)
        return int(fh.read().strip()) / 1e6
    except (OSError, ValueError):
        return None


def _tree_pids(root: int) -> list[int]:
    kids: dict[int, list[int]] = {}
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            ppid = int((p / "stat").read_text().rsplit(")", 1)[1].split()[1])
        except (OSError, IndexError, ValueError):
            continue
        kids.setdefault(ppid, []).append(int(p.name))
    out, stack = [], [root]
    while stack:
        pid = stack.pop()
        out.append(pid)
        stack.extend(kids.get(pid, []))
    return out


def _proc_kb(pid: int, key: str) -> int:
    try:
        for line in (Path("/proc") / str(pid) / "status").read_text().splitlines():
            if line.startswith(key + ":"):
                return int(line.split()[1])
    except OSError:
        pass
    return 0


class Sampler(threading.Thread):
    """Every 2 s: podman stats for the containers, RSS of the native Boar tree."""

    def __init__(self, containers: list[str], native_pid: int | None):
        super().__init__(daemon=True)
        self.containers = containers
        self.native_pid = native_pid
        self.peak: dict[str, float] = {}
        self.stop_evt = threading.Event()

    def run(self) -> None:
        while True:
            self.sample()
            if self.stop_evt.wait(SAMPLE_S):
                self.sample()
                return

    def sample(self) -> None:
        if self.containers:
            try:
                out = _run(
                    [
                        "podman",
                        "stats",
                        "--no-stream",
                        "--format",
                        "{{.Name}}|{{.MemUsage}}",
                        *self.containers,
                    ],
                    timeout=30,
                )
                for line in out.splitlines():
                    name, _, usage = line.partition("|")
                    mb = _mb(usage.split("/")[0])
                    self.peak[name] = max(self.peak.get(name, 0.0), mb)
            except (RuntimeError, ValueError, subprocess.TimeoutExpired):
                pass
        if self.native_pid:
            rss = sum(_proc_kb(p, "VmRSS") for p in _tree_pids(self.native_pid)) / 1e3
            self.peak["boar-native"] = max(self.peak.get("boar-native", 0.0), rss)


def _native_hwm_mb(pid: int) -> float:
    return sum(_proc_kb(p, "VmHWM") for p in _tree_pids(pid)) / 1e3


def _db_rows(db: Path, sql: str, args: tuple = ()) -> list[tuple]:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10)
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def _iso(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


# ------------------------------------------------------------------- run a case
def run_case(case: Case, a: argparse.Namespace, boar_container: str) -> dict:
    # --mode is restricted to two choices; forward a literal, never argv text.
    mode_literal = "native" if a.mode == "native" else "container"
    sh = [str(HERE / "boar.sh"), "restart", mode_literal, case.only]
    if case.variant:
        sh.append(case.variant)
    subprocess.run(sh, check=True, capture_output=True, timeout=300)
    native_pid = None
    if a.mode == "native":
        native_pid = int((Path(a.state) / "boar.pid").read_text().strip())
    watch = [case.container] + ([boar_container] if a.mode == "container" else [])
    peaks_fd = {c: _cgroup_peak_fd(c) for c in watch}
    sampler = Sampler(watch, native_pid)
    sampler.start()
    t0 = time.monotonic()
    started = _http(f"{a.boar_url}/scan", b"{}")
    sid = started["session_id"]
    status = "timeout"
    while time.monotonic() - t0 < SCAN_TIMEOUT_S:
        time.sleep(0.5)
        sess = [
            s for s in _http(f"{a.boar_url}/list")["sessions"] if s["session_id"] == sid
        ]
        if sess and sess[0].get("finished_at"):
            status = sess[0]["status"]
            break
    wall = time.monotonic() - t0
    sampler.stop_evt.set()
    sampler.join(timeout=30)
    sess = [
        s for s in _http(f"{a.boar_url}/list")["sessions"] if s["session_id"] == sid
    ][0]
    dur = (
        (_iso(sess["finished_at"]) - _iso(sess["started_at"])).total_seconds()
        if sess.get("finished_at")
        else wall
    )

    db = Path(a.state) / "data" / "audit_results.db"
    dbf = _db_rows(
        db,
        "SELECT table_name, column_name, pattern_detected FROM database_findings WHERE session_id=?",
        (sid,),
    )
    fsf = _db_rows(
        db,
        "SELECT file_name, pattern_detected FROM filesystem_findings WHERE session_id=?",
        (sid,),
    )
    appf = _db_rows(
        db,
        "SELECT file_name, pattern_detected FROM application_findings WHERE session_id=?",
        (sid,),
    )
    fails = _db_rows(
        db, "SELECT reason, details FROM scan_failures WHERE session_id=?", (sid,)
    )

    cg_peak = _read_peak_mb(peaks_fd.get(case.container))
    # Conservative headline: the larger of the 2 s podman-stats samples (no page
    # cache) and the cgroup high-water mark (includes page cache).
    target_peak = max(sampler.peak.get(case.container, 0.0), cg_peak or 0.0)
    if a.mode == "container":
        boar_cg = _read_peak_mb(peaks_fd.get(boar_container))
        boar_peak = max(sampler.peak.get(boar_container, 0.0), boar_cg or 0.0)
    else:
        boar_peak = max(
            sampler.peak.get("boar-native", 0.0), _native_hwm_mb(native_pid)
        )
        boar_cg = None
    for fh in peaks_fd.values():
        if fh:
            fh.close()

    # --- verdict against the DESIGNED expectation ---
    problems: list[str] = []
    found_keys = 0
    for kind, name, pat in case.key:
        if kind == "db":
            hit = any(f"{t}.{c}" == name and pat in (p or "") for t, c, p in dbf)
        elif kind == "app":
            hit = any(f == name and pat in (p or "") for f, p in appf)
        else:
            hit = any(f == name and pat in (p or "") for f, p in fsf)
        found_keys += hit
        if not hit:
            problems.append(f"missing {name}")
    if case.exact_fs is not None and len(fsf) != case.exact_fs:
        problems.append(f"fs findings {len(fsf)} != {case.exact_fs}")
    for reasons, fname in case.failures:
        if not any(r in reasons.split("|") and fname in d for r, d in fails):
            problems.append(f"failure {reasons} not recorded for {fname}")
    if case.no_failures and fails:
        problems.append(f"{len(fails)} unexpected failure(s)")
    if status != "completed":
        problems.append(f"status={status}")
    found_total = len(dbf) + len(fsf) + len(appf)
    exp_txt = f"{len(case.key)} chave" if case.key else "0"
    if case.exact_fs is not None:
        exp_txt = f"{case.exact_fs} (exato)"
    if case.failures:
        exp_txt += " + falha " + case.failures[0][0].split("|")[0]
    reasons_seen = ",".join(sorted({r for r, _ in fails})) or "-"
    return {
        "label": case.label,
        "container": case.container,
        "target_mb": target_peak,
        "target_cg_mb": cg_peak,
        "boar_mb": boar_peak,
        "boar_cg_mb": boar_cg,
        "seconds": dur,
        "found": found_total,
        "keys": f"{found_keys}/{len(case.key)}",
        "failures": reasons_seen,
        "expected": exp_txt,
        "ok": not problems,
        "problems": problems,
        "note": case.note,
    }


# ----------------------------------------------------------------------- report
def build_report(rows: list[dict], a: argparse.Namespace) -> str:
    peak: dict[str, float] = {}
    for r in rows:
        peak[r["container"]] = max(peak.get(r["container"], 0.0), r["target_mb"])
    # cut rule: keep containers in priority order while the running sum <= budget
    decision, running = {}, 0.0
    for c in CONTAINER_PRIORITY:
        if c not in peak:
            continue
        if running + peak[c] <= BUDGET_MB:
            running += peak[c]
            decision[c] = "MANTER"
        else:
            decision[c] = "CORTAR"
    boar_peak = max((r["boar_mb"] for r in rows), default=0.0)
    lines = [
        f"# Ensaio do demo local ({a.mode}) - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Supabase_Simulated e um PostgreSQL 17 LOCAL (simulado); nao mede a latencia (~20 ms) do Supabase real.",
        "",
        "| alvo | RAM pico MB (alvo) | RAM pico MB (Boar) | tempo s | achados | esperado | veredito |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for r in rows:
        verdict = "OK" if r["ok"] else "FALHOU: " + "; ".join(r["problems"])
        if not r["ok"] and r["note"]:
            verdict += f" ({r['note']})"
        if r["failures"] != "-":
            verdict += f" [falhas: {r['failures']}]"
        if decision.get(r["container"]) == "CORTAR":
            verdict += " | CORTAR (orcamento)"
        lines.append(
            f"| {r['label']} | {r['target_mb']:.0f} | {r['boar_mb']:.0f} | {r['seconds']:.1f} "
            f"| {r['found']} | {r['expected']} | {verdict} |"
        )
    lines += [
        "",
        "## Regra de corte (orcamento da VPS: soma dos containers de alvo, sem o Boar, <= "
        f"{BUDGET_MB:.0f} MB de pico)",
        "",
        "| container | pico MB | acumulado MB | decisao |",
        "| --- | ---: | ---: | --- |",
    ]
    acc = 0.0
    for c in CONTAINER_PRIORITY:
        if c in peak:
            if decision[c] == "MANTER":
                acc += peak[c]
            lines.append(f"| {c} | {peak[c]:.0f} | {acc:.0f} | {decision[c]} |")
    total_all = sum(peak.values())
    lines += [
        "",
        f"- Soma dos containers de alvo (todos): {total_all:.0f} MB; dentro do orcamento: {acc:.0f} MB.",
        f"- Pico do Boar ({a.mode}): {boar_peak:.0f} MB. RAM total do cenario leve (alvos + Boar): "
        f"{total_all + boar_peak:.0f} MB.",
    ]
    if a.up_seconds:
        lines.append(
            f"- Tempo de subida do `up.sh` (down + up, imagens em cache): {a.up_seconds} s."
        )
    lines += [
        "",
        "Colunas de RAM: pico = maior valor entre `podman stats` (amostra a cada 2 s) e o `memory.peak` do cgroup "
        "(inclui cache de pagina). No modo native, o Boar e o RSS da arvore de processos.",
        "Achados: total no scan (colunas/arquivos); esperado: achados-chave previstos pelo corpus/seeds, "
        "conferidos um a um.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["container", "native"])
    ap.add_argument("--state", required=True)
    ap.add_argument("--boar-url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--up-seconds", default="")
    a = ap.parse_args()
    rows = []
    for c in cases():
        try:
            rows.append(run_case(c, a, "dbdl-boar"))
        except Exception as exc:  # noqa: BLE001 - report and keep going
            rows.append(
                {
                    "label": c.label,
                    "container": c.container,
                    "target_mb": 0.0,
                    "target_cg_mb": None,
                    "boar_mb": 0.0,
                    "boar_cg_mb": None,
                    "seconds": 0.0,
                    "found": 0,
                    "keys": "0/0",
                    "failures": "-",
                    "expected": "-",
                    "ok": False,
                    "problems": [f"error: {str(exc)[:120]}"],
                    "note": "",
                }
            )
    # Leave the full scenario ready (all targets) after the one-target runs.
    subprocess.run(
        [
            str(HERE / "boar.sh"),
            "restart",
            "native" if a.mode == "native" else "container",
        ],
        check=False,
        capture_output=True,
    )
    text = build_report(rows, a)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    os.environ.setdefault("LC_ALL", "C")
    raise SystemExit(main())
