"""Tests for Cloudflare GraphQL → edge metrics exporter (#1599)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
import pytest

from core.cloudflare_edge_metrics import (
    QUERY_HTTP_REQUESTS_ADAPTIVE_V1,
    QUERY_VERSION,
    SERVICE_NAME,
    build_variables,
    compute_window,
    extract_series,
    load_fixture,
    normalize_cache_status,
    normalize_series,
    parse_hostname_allowlist,
    points_as_jsonable,
    post_graphql,
    redact_headers_for_log,
    resolve_credentials_from_env,
    status_class,
    write_watermark,
)

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "cloudflare"
    / "http_requests_adaptive_groups.json"
)


def test_query_targets_adaptive_groups_and_eyeball_contract() -> None:
    assert "httpRequestsAdaptiveGroups" in QUERY_HTTP_REQUESTS_ADAPTIVE_V1
    assert "clientRequestHTTPHost" in QUERY_HTTP_REQUESTS_ADAPTIVE_V1
    assert "edgeResponseStatus" in QUERY_HTTP_REQUESTS_ADAPTIVE_V1
    assert "cacheStatus" in QUERY_HTTP_REQUESTS_ADAPTIVE_V1
    # Must not request high-PII dimensions.
    for banned in (
        "clientIP",
        "clientRequestPath",
        "clientRequestQuery",
        "clientRequestReferer",
        "userAgent",
        "cookie",
    ):
        assert banned not in QUERY_HTTP_REQUESTS_ADAPTIVE_V1


def test_status_and_cache_normalization() -> None:
    assert status_class(200) == "2xx"
    assert status_class(404) == "4xx"
    assert status_class(503) == "5xx"
    assert status_class(None) == "unknown"
    assert normalize_cache_status("hit") == "HIT"
    assert normalize_cache_status("weird-value") == "OTHER"


def test_fixture_normalize_with_allowlist() -> None:
    payload = load_fixture(FIXTURE)
    series = extract_series(payload)
    window = compute_window(
        now=datetime(2026, 8, 16, 20, 0, tzinfo=UTC),
        lookback=timedelta(hours=2),
        lag=timedelta(0),
    )
    batch = normalize_series(
        series,
        window=window,
        hostname_allowlist=parse_hostname_allowlist("databoar.com.br"),
    )
    assert batch.query_version == QUERY_VERSION
    assert batch.raw_group_count == 3
    assert batch.dropped_hostname_count == 1
    hosts = {p.attributes["http.host"] for p in batch.points}
    assert hosts == {"databoar.com.br"}
    assert all(p.attributes["service.name"] == SERVICE_NAME for p in batch.points)
    assert all(
        p.attributes["telemetry.source"] == "cloudflare-graphql" for p in batch.points
    )
    metrics = {p.metric for p in batch.points}
    assert "cloudflare.edge.http.requests" in metrics
    assert "cloudflare.edge.http.visits" in metrics
    assert "cloudflare.edge.http.response_bytes" in metrics
    classes = {
        p.attributes["http.status_class"]
        for p in batch.points
        if p.metric == "cloudflare.edge.http.requests"
    }
    assert classes == {"2xx", "4xx"}


def test_points_json_notes_not_traces() -> None:
    payload = load_fixture(FIXTURE)
    window = compute_window(
        now=datetime(2026, 8, 16, 20, 0, tzinfo=UTC), lag=timedelta(0)
    )
    batch = normalize_series(extract_series(payload), window=window)
    blob = points_as_jsonable(batch)
    assert "not distributed traces" in blob["note"].lower()
    assert "faro" in blob["note"].lower()


def test_build_variables_half_open_window_and_eyeball() -> None:
    window = compute_window(
        now=datetime(2026, 8, 16, 12, 0, tzinfo=UTC),
        lookback=timedelta(hours=1),
        lag=timedelta(minutes=5),
    )
    variables = build_variables(zone_id="zone-abc", window=window, limit=100)
    assert variables["zoneTag"] == "zone-abc"
    assert variables["start"].endswith("Z")
    assert variables["end"].endswith("Z")
    assert variables["limit"] == 100
    with pytest.raises(ValueError, match="eyeball"):
        build_variables(zone_id="zone-abc", window=window, eyeball_only=False)


def test_watermark_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "wm.txt"
    end = datetime(2026, 8, 16, 11, 55, tzinfo=UTC)
    write_watermark(path, end)
    text = path.read_text(encoding="utf-8").strip()
    assert text == "2026-08-16T11:55:00Z"
    window = compute_window(
        now=datetime(2026, 8, 16, 13, 0, tzinfo=UTC),
        watermark=datetime.fromisoformat(text.replace("Z", "+00:00")),
        overlap=timedelta(minutes=5),
        lag=timedelta(minutes=5),
    )
    assert window.start < window.end


def test_credentials_require_zone_scoped() -> None:
    with pytest.raises(ValueError, match="CLOUDFLARE_ZONE_ID"):
        resolve_credentials_from_env({"CLOUDFLARE_API_TOKEN": "x"})
    with pytest.raises(ValueError, match="not implemented"):
        resolve_credentials_from_env(
            {
                "CLOUDFLARE_API_TOKEN": "x",
                "CLOUDFLARE_ALLOW_ALL_ZONES_FOR_LOCAL_TEST": "1",
            }
        )
    token, zone = resolve_credentials_from_env(
        {"CLOUDFLARE_API_TOKEN": "tok", "CLOUDFLARE_ZONE_ID": "zid"}
    )
    assert token == "tok" and zone == "zid"


def test_redact_authorization_header() -> None:
    redacted = redact_headers_for_log(
        {"Authorization": "Bearer secret", "Accept": "application/json"}
    )
    assert redacted["Authorization"] == "<redacted>"
    assert redacted["Accept"] == "application/json"


def test_post_graphql_retries_on_429(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    class _Resp:
        def read(self) -> bytes:
            return json.dumps(
                {"data": {"viewer": {"zones": []}}, "errors": None}
            ).encode()

        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    def fake_urlopen(req: object, timeout: float = 0) -> _Resp:  # noqa: ARG001
        calls["n"] += 1
        if calls["n"] == 1:
            import urllib.error

            raise urllib.error.HTTPError(
                url="https://api.cloudflare.com/client/v4/graphql",
                code=429,
                msg="rate",
                hdrs={"Retry-After": "0"},  # type: ignore[arg-type]
                fp=None,
            )
        return _Resp()

    sleeps: list[float] = []
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    out = post_graphql(
        query="{ viewer { zones { __typename } } }",
        variables={},
        token="test-token",
        max_retries=2,
        sleep_fn=lambda s: sleeps.append(s),
    )
    assert out["data"]["viewer"]["zones"] == []
    assert calls["n"] == 2
    assert sleeps


def test_cli_fixture_dry_run(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.cloudflare_graphql_otel_export import main

    rc = main(["--fixture", str(FIXTURE), "--dry-run", "--no-watermark"])
    assert rc == 0
    captured = capsys.readouterr().out
    out = json.loads(captured)
    assert out["service_name"] == SERVICE_NAME
    assert out["points"]
    assert "Bearer" not in captured
