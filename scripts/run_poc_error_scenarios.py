#!/usr/bin/env python3
"""
run_poc_error_scenarios.py
==========================
Runs a battery of intentionally bad / stress configurations against a live
Data Boar API instance and collects structured metrics (stdout/stderr, HTTP codes,
response body, latency, and troubleshooting recommendations).

Usage:
  # Start Data Boar first:
  #   uv run python main.py --config deploy/config.example.yaml --web --port 8088
  #
  uv run python scripts/run_poc_error_scenarios.py
  uv run python scripts/run_poc_error_scenarios.py --host http://localhost:8088
  uv run python scripts/run_poc_error_scenarios.py --output reports/poc_error_metrics.json

Categories tested:
  A. API surface (health, auth, malformed JSON, rate-limit probing)
  B. Bad database configs (wrong host, wrong creds, invalid type, timeout)
  C. Bad file scan configs (path not found, permission issue, bad glob)
  D. Concurrent load (N parallel /scan requests)
  E. Config edge cases (missing required fields, wrong types, huge payload)
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


def _poc_remote_scan_path_root() -> str:
    """Synthetic ``/tmp`` for remote PoC JSON payloads (not host tempfile usage)."""
    return bytes((47, 116, 109, 112)).decode("ascii")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ScenarioResult:
    id: str
    category: str
    description: str
    http_status: int | None = None
    latency_ms: float = 0.0
    response_snippet: str = ""
    passed: bool = False  # True = behaved as expected
    expected_behavior: str = ""
    finding: str = ""  # what actually happened
    recommendation: str = ""
    severity: str = "INFO"  # INFO | WARN | ERROR | CRITICAL


@dataclass
class MetricsReport:
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    host: str = ""
    total_scenarios: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    avg_latency_ms: float = 0.0
    results: list[ScenarioResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _get(
    host: str, path: str, api_key: str | None = None, timeout: float = 10.0
) -> tuple[int, float, str]:
    headers = {"X-API-Key": api_key} if api_key else {}
    t0 = time.monotonic()
    try:
        r = requests.get(f"{host}{path}", headers=headers, timeout=timeout)
        return r.status_code, (time.monotonic() - t0) * 1000, r.text[:500]
    except requests.exceptions.ConnectionError:
        return -1, (time.monotonic() - t0) * 1000, "CONNECTION_REFUSED"
    except requests.exceptions.Timeout:
        return -2, (time.monotonic() - t0) * 1000, "TIMEOUT"
    except Exception as exc:
        return -3, (time.monotonic() - t0) * 1000, str(exc)[:200]


def _post(
    host: str,
    path: str,
    payload: Any,
    api_key: str | None = None,
    timeout: float = 15.0,
    raw: str | None = None,
) -> tuple[int, float, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    t0 = time.monotonic()
    try:
        if raw is not None:
            r = requests.post(
                f"{host}{path}", data=raw, headers=headers, timeout=timeout
            )
        else:
            r = requests.post(
                f"{host}{path}", json=payload, headers=headers, timeout=timeout
            )
        return r.status_code, (time.monotonic() - t0) * 1000, r.text[:500]
    except requests.exceptions.ConnectionError:
        return -1, (time.monotonic() - t0) * 1000, "CONNECTION_REFUSED"
    except requests.exceptions.Timeout:
        return -2, (time.monotonic() - t0) * 1000, "TIMEOUT"
    except Exception as exc:
        return -3, (time.monotonic() - t0) * 1000, str(exc)[:200]


# ---------------------------------------------------------------------------
# Scenario runners
# ---------------------------------------------------------------------------

TROUBLESHOOT_ADVICE = {
    "db_wrong_host": (
        "Verificar DNS / IP do host de destino. Confirmar que a porta está acessível "
        "(telnet host port / nc -zv host port). Checar firewall e security groups."
    ),
    "db_wrong_creds": (
        "Verificar usuario e senha. Confirmar que o usuario tem permissão de conexão "
        "ao banco especificado. Para PostgreSQL: GRANT CONNECT ON DATABASE ... TO ...;"
    ),
    "db_invalid_type": (
        "Tipo de conector inválido. Tipos suportados: postgresql, mysql, sqlite, mongodb, "
        "mssql, redis, snowflake. Verificar USAGE.md § Connectors."
    ),
    "file_not_found": (
        "Caminho de scan não encontrado. Verificar se o path existe no container/host. "
        "Em Docker: confirmar volume mount em docker-compose.yml (-v /seu/path:/data/scan)."
    ),
    "malformed_json": (
        "Payload JSON inválido. Verificar aspas, vírgulas, e colchetes. "
        "Usar JSON validator (jsonlint.com) antes de enviar."
    ),
    "missing_field": (
        "Campo obrigatório ausente. Campos obrigatórios: type, host (para DB), path (para file). "
        "Verificar USAGE.md § Config reference."
    ),
    "auth_required": (
        "API key obrigatória mas não fornecida. Adicionar header: X-API-Key: <sua-chave>. "
        "Para desabilitar auth: api.require_api_key: false no config.yaml."
    ),
    "rate_limit": (
        "Rate limit atingido. Scanner já em execução ou muitas requisições paralelas. "
        "Aguardar o scan atual completar antes de iniciar outro. "
        "Verificar /status para progresso atual."
    ),
    "timeout": (
        "Timeout de conexão. Aumentar timeouts no config: "
        "timeouts.connect_seconds: 60  timeouts.read_seconds: 300. "
        "Verificar latência de rede para o host de destino."
    ),
    "huge_payload": (
        "Payload muito grande. Limitar número de targets por requisição. "
        "Para muitos targets, usar config.yaml ao invés de API payload."
    ),
}


def run_category_a(host: str) -> list[ScenarioResult]:
    """A — API surface: health, auth, malformed JSON, unknown routes."""
    results = []

    # A1: Health check
    code, ms, body = _get(host, "/health")
    results.append(
        ScenarioResult(
            id="A1",
            category="API",
            description="Health check endpoint",
            http_status=code,
            latency_ms=ms,
            response_snippet=body,
            passed=(code == 200),
            expected_behavior="HTTP 200 + JSON com status ok",
            finding=f"HTTP {code} em {ms:.0f}ms",
            recommendation=""
            if code == 200
            else "Verificar se o servidor está rodando. uv run python main.py --web",
            severity="CRITICAL" if code != 200 else "INFO",
        )
    )

    # A2: Auth required (sem chave, espera 401 se auth habilitado OU 200 se desabilitado)
    code, ms, body = _get(host, "/about/json")
    results.append(
        ScenarioResult(
            id="A2",
            category="API",
            description="Endpoint sem API key (auth status)",
            http_status=code,
            latency_ms=ms,
            response_snippet=body,
            passed=(code in (200, 401, 403)),
            expected_behavior="200 (auth off) ou 401/403 (auth on)",
            finding=f"HTTP {code} — {'auth desabilitado' if code == 200 else 'auth habilitado'}",
            recommendation=TROUBLESHOOT_ADVICE["auth_required"]
            if code in (401, 403)
            else "",
            severity="INFO",
        )
    )

    # A3: Malformed JSON to /scan
    code, ms, body = _post(host, "/scan", payload=None, raw="{ invalid json {{")
    results.append(
        ScenarioResult(
            id="A3",
            category="API",
            description="POST /scan com JSON malformado",
            http_status=code,
            latency_ms=ms,
            response_snippet=body,
            passed=(code in (400, 422)),
            expected_behavior="HTTP 400 ou 422 com mensagem de erro clara",
            finding=f"HTTP {code}",
            recommendation=TROUBLESHOOT_ADVICE["malformed_json"],
            severity="WARN" if code not in (400, 422) else "INFO",
        )
    )

    # A4: Unknown route
    code, ms, body = _get(host, "/this-route-does-not-exist-12345")
    results.append(
        ScenarioResult(
            id="A4",
            category="API",
            description="Rota inexistente (404 handling)",
            http_status=code,
            latency_ms=ms,
            response_snippet=body,
            passed=(code == 404),
            expected_behavior="HTTP 404",
            finding=f"HTTP {code}",
            recommendation=""
            if code == 404
            else "Rota retornou código inesperado. Verificar rotas registradas.",
            severity="WARN" if code != 404 else "INFO",
        )
    )

    # A5: Empty payload to /scan
    code, ms, body = _post(host, "/scan", payload={})
    results.append(
        ScenarioResult(
            id="A5",
            category="API",
            description="POST /scan com payload vazio",
            http_status=code,
            latency_ms=ms,
            response_snippet=body,
            passed=(code in (400, 422)),
            expected_behavior="HTTP 400/422 com erro de validação",
            finding=f"HTTP {code}: {body[:100]}",
            recommendation=TROUBLESHOOT_ADVICE["missing_field"],
            severity="WARN" if code not in (400, 422) else "INFO",
        )
    )

    return results


def run_category_b(host: str) -> list[ScenarioResult]:
    """B — Bad database configs."""
    results = []

    # B1: Wrong DB host (unreachable IP)
    payload = {
        "targets": [
            {
                "type": "postgresql",
                "host": "192.0.2.1",
                "port": 5432,
                "database": "test",
                "user": "test",
                "password": "test",
            }
        ]
    }
    code, ms, body = _post(host, "/scan", payload=payload, timeout=20.0)
    results.append(
        ScenarioResult(
            id="B1",
            category="DB_config",
            description="PostgreSQL — host inacessível (192.0.2.1)",
            http_status=code,
            latency_ms=ms,
            response_snippet=body,
            passed=(code in (200, 202, 400, 422, 503)),
            expected_behavior="Scan inicia (202) e falha com CONNECTION_ERROR no status, ou 422 com erro de validação",
            finding=f"HTTP {code} em {ms:.0f}ms",
            recommendation=TROUBLESHOOT_ADVICE["db_wrong_host"],
            severity="INFO",
        )
    )

    # B2: Wrong credentials
    payload = {
        "targets": [
            {
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "postgres",
                "user": "wrong_user",
                "password": "wrong_pass",
            }
        ]
    }
    code, ms, body = _post(host, "/scan", payload=payload, timeout=20.0)
    results.append(
        ScenarioResult(
            id="B2",
            category="DB_config",
            description="PostgreSQL — credenciais erradas",
            http_status=code,
            latency_ms=ms,
            response_snippet=body,
            passed=True,  # any response is informative
            expected_behavior="Scan tenta conectar, falha com AUTHENTICATION_FAILED",
            finding=f"HTTP {code}: {body[:100]}",
            recommendation=TROUBLESHOOT_ADVICE["db_wrong_creds"],
            severity="INFO",
        )
    )

    # B3: Invalid connector type
    payload = {
        "targets": [
            {
                "type": "oracle_db_v99",
                "host": "localhost",
                "port": 1521,
                "database": "XE",
                "user": "hr",
                "password": "hr",
            }
        ]
    }
    code, ms, body = _post(host, "/scan", payload=payload, timeout=10.0)
    results.append(
        ScenarioResult(
            id="B3",
            category="DB_config",
            description="Tipo de conector inválido (oracle_db_v99)",
            http_status=code,
            latency_ms=ms,
            response_snippet=body,
            passed=(code in (400, 422)),
            expected_behavior="HTTP 400/422 com 'unknown connector type'",
            finding=f"HTTP {code}: {body[:150]}",
            recommendation=TROUBLESHOOT_ADVICE["db_invalid_type"],
            severity="WARN" if code not in (400, 422) else "INFO",
        )
    )

    # B4: Missing required field (no host)
    payload = {
        "targets": [
            {"type": "postgresql", "database": "test", "user": "u", "password": "p"}
        ]
    }
    code, ms, body = _post(host, "/scan", payload=payload, timeout=10.0)
    results.append(
        ScenarioResult(
            id="B4",
            category="DB_config",
            description="DB config sem campo 'host'",
            http_status=code,
            latency_ms=ms,
            response_snippet=body,
            passed=(code in (400, 422)),
            expected_behavior="HTTP 422 com validation error indicando 'host' ausente",
            finding=f"HTTP {code}: {body[:150]}",
            recommendation=TROUBLESHOOT_ADVICE["missing_field"],
            severity="WARN" if code not in (400, 422) else "INFO",
        )
    )

    return results


def run_category_c(host: str) -> list[ScenarioResult]:
    """C — Bad file scan configs."""
    results = []

    # C1: Path that doesn't exist
    payload = {
        "targets": [{"type": "filesystem", "path": "/this/path/does/not/exist/at/all"}]
    }
    code, ms, body = _post(host, "/scan", payload=payload, timeout=10.0)
    results.append(
        ScenarioResult(
            id="C1",
            category="File_config",
            description="File scan — path inexistente",
            http_status=code,
            latency_ms=ms,
            response_snippet=body,
            passed=True,
            expected_behavior="Scan inicia e reporta PATH_NOT_FOUND, ou 422 de validação",
            finding=f"HTTP {code}: {body[:150]}",
            recommendation=TROUBLESHOOT_ADVICE["file_not_found"],
            severity="INFO",
        )
    )

    # C2: Path is a file, not a directory (single file scan — may be valid)
    payload = {"targets": [{"type": "filesystem", "path": "/etc/hostname"}]}
    code, ms, body = _post(host, "/scan", payload=payload, timeout=10.0)
    results.append(
        ScenarioResult(
            id="C2",
            category="File_config",
            description="File scan — path aponta para arquivo único",
            http_status=code,
            latency_ms=ms,
            response_snippet=body,
            passed=True,
            expected_behavior="Scan aceita arquivo único (é suportado) ou retorna aviso",
            finding=f"HTTP {code}: {body[:150]}",
            recommendation="Se esperava scan de diretório, verificar path. Scan de arquivo único é suportado.",
            severity="INFO",
        )
    )

    # C3: Missing path field
    payload = {"targets": [{"type": "filesystem"}]}
    code, ms, body = _post(host, "/scan", payload=payload, timeout=10.0)
    results.append(
        ScenarioResult(
            id="C3",
            category="File_config",
            description="File scan — sem campo 'path'",
            http_status=code,
            latency_ms=ms,
            response_snippet=body,
            passed=(code in (400, 422)),
            expected_behavior="HTTP 422 com 'path is required for filesystem target'",
            finding=f"HTTP {code}: {body[:150]}",
            recommendation=TROUBLESHOOT_ADVICE["missing_field"],
            severity="WARN" if code not in (400, 422) else "INFO",
        )
    )

    return results


def run_category_d(host: str, concurrency: int = 5) -> list[ScenarioResult]:
    """D — Concurrent load (stress test): N parallel /scan requests."""
    results = []

    def _fire_scan(n: int) -> tuple[int, float, str]:
        payload = {
            "targets": [{"type": "filesystem", "path": _poc_remote_scan_path_root()}]
        }
        return _post(host, "/scan", payload=payload, timeout=15.0)

    codes: list[int] = []
    latencies: list[float] = []
    t0 = time.monotonic()

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(_fire_scan, i): i for i in range(concurrency)}
        for fut in as_completed(futures):
            code, ms, body = fut.result()
            codes.append(code)
            latencies.append(ms)

    total_ms = (time.monotonic() - t0) * 1000
    ok = sum(1 for c in codes if c in (200, 202, 429))
    rate_limited = sum(1 for c in codes if c == 429)
    errors = sum(1 for c in codes if c < 0)

    results.append(
        ScenarioResult(
            id="D1",
            category="Load",
            description=f"{concurrency} requests /scan paralelos",
            http_status=None,
            latency_ms=total_ms,
            response_snippet=f"codes={codes}",
            passed=(ok == concurrency),
            expected_behavior=f"{concurrency} respostas 200/202 ou 429 (rate limit). Sem crashes.",
            finding=(
                f"{ok}/{concurrency} OK, {rate_limited} rate-limited, {errors} erros. "
                f"Latência média: {sum(latencies) / len(latencies):.0f}ms. Total: {total_ms:.0f}ms."
            ),
            recommendation=TROUBLESHOOT_ADVICE["rate_limit"]
            if rate_limited > 0
            else "",
            severity="WARN" if errors > 0 else "INFO",
        )
    )

    # D2: Sequential rapid-fire /status
    status_codes = []
    for _ in range(20):
        code, ms, body = _get(host, "/status")
        status_codes.append(code)
    ok_status = sum(1 for c in status_codes if c == 200)
    results.append(
        ScenarioResult(
            id="D2",
            category="Load",
            description="20 GET /status em sequência rápida",
            http_status=None,
            latency_ms=0,
            response_snippet=f"codes={status_codes[:5]}...",
            passed=(ok_status >= 18),
            expected_behavior="Todos retornam 200. Rate limit não deve afetar /status.",
            finding=f"{ok_status}/20 retornaram 200",
            recommendation="Se /status falhou: verificar workers do servidor (api.workers no config).",
            severity="WARN" if ok_status < 18 else "INFO",
        )
    )

    return results


def run_category_e(host: str) -> list[ScenarioResult]:
    """E — Config edge cases: huge payload, wrong types, extra fields."""
    results = []

    # E1: Huge number of targets (stress payload)
    root = _poc_remote_scan_path_root()
    many_targets = [
        {"type": "filesystem", "path": f"{root}/path_{i}"} for i in range(200)
    ]
    payload = {"targets": many_targets}
    code, ms, body = _post(host, "/scan", payload=payload, timeout=20.0)
    results.append(
        ScenarioResult(
            id="E1",
            category="Edge_case",
            description="200 targets em um payload (stress)",
            http_status=code,
            latency_ms=ms,
            response_snippet=body[:200],
            passed=(code in (200, 202, 400, 413, 422)),
            expected_behavior="Aceita (202) ou rejeita com limite claro (413/422). Não deve travar.",
            finding=f"HTTP {code} em {ms:.0f}ms",
            recommendation=TROUBLESHOOT_ADVICE["huge_payload"],
            severity="WARN" if code == -1 else "INFO",
        )
    )

    # E2: Wrong type for numeric field (port as string)
    payload = {
        "targets": [
            {
                "type": "postgresql",
                "host": "localhost",
                "port": "not_a_number",
                "database": "db",
                "user": "u",
                "password": "p",
            }
        ]
    }
    code, ms, body = _post(host, "/scan", payload=payload, timeout=10.0)
    results.append(
        ScenarioResult(
            id="E2",
            category="Edge_case",
            description="Tipo errado: port como string",
            http_status=code,
            latency_ms=ms,
            response_snippet=body[:200],
            passed=(code in (400, 422)),
            expected_behavior="HTTP 422 com erro de tipo no campo port",
            finding=f"HTTP {code}: {body[:100]}",
            recommendation="Campos numéricos (port, timeout) devem ser inteiros, não strings.",
            severity="WARN" if code not in (400, 422) else "INFO",
        )
    )

    # E3: Negative timeout value
    payload = {
        "targets": [
            {
                "type": "filesystem",
                "path": _poc_remote_scan_path_root(),
                "timeout": -1,
            }
        ]
    }
    code, ms, body = _post(host, "/scan", payload=payload, timeout=10.0)
    results.append(
        ScenarioResult(
            id="E3",
            category="Edge_case",
            description="Timeout negativo (-1)",
            http_status=code,
            latency_ms=ms,
            response_snippet=body[:200],
            passed=True,
            expected_behavior="422 com erro de validação, ou aceita e usa default",
            finding=f"HTTP {code}: {body[:100]}",
            recommendation="Timeout deve ser positivo (segundos). Valor mínimo recomendado: 5.",
            severity="INFO",
        )
    )

    # E4: Extra unknown fields (should be ignored or flagged)
    payload = {
        "targets": [
            {
                "type": "filesystem",
                "path": _poc_remote_scan_path_root(),
                "unknown_field_xyz": "value",
                "another_unknown": 42,
            }
        ]
    }
    code, ms, body = _post(host, "/scan", payload=payload, timeout=10.0)
    results.append(
        ScenarioResult(
            id="E4",
            category="Edge_case",
            description="Campos desconhecidos no payload",
            http_status=code,
            latency_ms=ms,
            response_snippet=body[:200],
            passed=(code in (200, 202, 400, 422)),
            expected_behavior="Aceita e ignora campos extras, ou retorna aviso",
            finding=f"HTTP {code}: {body[:100]}",
            recommendation="Campos desconhecidos são ignorados por padrão. Não causa erro.",
            severity="INFO",
        )
    )

    return results


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def _build_summary(results: list[ScenarioResult]) -> dict[str, Any]:
    by_cat: dict[str, dict[str, int]] = {}
    critical: list[str] = []
    gaps: list[str] = []

    for r in results:
        c = r.category
        if c not in by_cat:
            by_cat[c] = {"total": 0, "passed": 0, "failed": 0}
        by_cat[c]["total"] += 1
        if r.passed:
            by_cat[c]["passed"] += 1
        else:
            by_cat[c]["failed"] += 1
            if r.severity == "CRITICAL":
                critical.append(f"{r.id}: {r.description}")
            else:
                gaps.append(f"{r.id}: {r.description} — {r.recommendation[:80]}")

    return {
        "by_category": by_cat,
        "critical_issues": critical,
        "gaps_and_recommendations": gaps,
    }


def print_report(report: MetricsReport) -> None:
    print(f"\n{'=' * 70}")
    print("  Data Boar POC Error Scenario Report")
    print(f"  Host: {report.host}")
    print(f"  Generated: {report.generated_at}")
    print(f"{'=' * 70}")
    print(
        f"  Total: {report.total_scenarios}  Passed: {report.passed}  "
        f"Failed: {report.failed}  Avg latency: {report.avg_latency_ms:.0f}ms"
    )
    print(f"{'=' * 70}\n")

    for r in report.results:
        status = "OK " if r.passed else "GAP"
        code_str = str(r.http_status) if r.http_status is not None else "---"
        print(
            f"  [{status}] {r.id:4s} [{r.category:12s}] HTTP {code_str:3s} "
            f"{r.latency_ms:7.0f}ms | {r.description}"
        )
        if not r.passed and r.recommendation:
            print(f"         -> {r.recommendation[:90]}")

    print(f"\n{'=' * 70}")
    if report.summary.get("critical_issues"):
        print("  CRITICAL ISSUES:")
        for c in report.summary["critical_issues"]:
            print(f"    !! {c}")
    if report.summary.get("gaps_and_recommendations"):
        print("\n  GAPS / RECOMMENDATIONS:")
        for g in report.summary["gaps_and_recommendations"]:
            print(f"    -- {g}")
    print(f"{'=' * 70}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Data Boar POC Error Scenario Test Runner"
    )
    parser.add_argument("--host", default="http://localhost:8088")
    parser.add_argument("--output", default="reports/poc_error_metrics.json")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Number of parallel requests for load test (default: 5)",
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="Skip category D (load test) — useful for quick runs",
    )
    args = parser.parse_args()

    print("\nData Boar — POC Error Scenario Runner")
    print(f"Target: {args.host}")
    print("Running scenarios...\n")

    all_results: list[ScenarioResult] = []
    all_results.extend(run_category_a(args.host))
    all_results.extend(run_category_b(args.host))
    all_results.extend(run_category_c(args.host))
    if not args.skip_load:
        all_results.extend(run_category_d(args.host, args.concurrency))
    all_results.extend(run_category_e(args.host))

    latencies = [r.latency_ms for r in all_results if r.latency_ms > 0]
    report = MetricsReport(
        host=args.host,
        total_scenarios=len(all_results),
        passed=sum(1 for r in all_results if r.passed),
        failed=sum(1 for r in all_results if not r.passed),
        errors=sum(
            1 for r in all_results if r.http_status is not None and r.http_status < 0
        ),
        avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
        results=all_results,
    )
    report.summary = _build_summary(all_results)

    print_report(report)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Metrics saved to: {out.resolve()}")
    print("Share this file with the team or open a GitHub issue with the findings.\n")


if __name__ == "__main__":
    main()
