"""Self-check of the simulated Graph used by the 2206.1 acceptance tests.

These tests exercise only ``tests/m365_fake_graph.py`` (no connector). They keep the
simulator honest: an acceptance test that passes against a broken simulator proves nothing.
"""

from __future__ import annotations

import httpx
import pytest

from tests.m365_fake_graph import (
    DEFAULT_DOWNLOAD_HOST,
    EVIL_HOST,
    GRAPH_HOST,
    LOGIN_HOST,
    SECRET,
    TEST_CLIENT_ID,
    USER_CODE,
    FakeGraph,
    File,
    Folder,
    RegexScanner,
)

DEVICE = "urn:ietf:params:oauth:grant-type:device_code"
BASE = f"https://{GRAPH_HOST}/v1.0/me/drive"


def _client(fake: FakeGraph) -> httpx.Client:
    return httpx.Client(transport=fake.transport, follow_redirects=False)


def _login(fake: FakeGraph, client: httpx.Client) -> dict[str, str]:
    dc = client.post(
        f"https://{LOGIN_HOST}/consumers/oauth2/v2.0/devicecode",
        data={"client_id": TEST_CLIENT_ID, "scope": "x"},
    ).json()
    assert dc["user_code"] == USER_CODE
    tok = client.post(
        f"https://{LOGIN_HOST}/consumers/oauth2/v2.0/token",
        data={
            "grant_type": DEVICE,
            "client_id": TEST_CLIENT_ID,
            "device_code": dc["device_code"],
        },
    )
    return tok.json()


def _tree() -> dict:
    return {
        "Pasta": {
            "a.txt": "x",
            "sub": {"c.txt": "y"},
            "atalho": Folder({"z.txt": "z"}, remote=True),
        },
        "Pasta2": {"s.txt": "s"},
    }


def test_device_script_pending_then_ok_and_secret_markers() -> None:
    fake = FakeGraph(_tree(), device_script=["pending", "ok"])
    with _client(fake) as c:
        dc = c.post(
            f"https://{LOGIN_HOST}/consumers/oauth2/v2.0/devicecode", data={}
        ).json()
        body = {
            "grant_type": DEVICE,
            "client_id": TEST_CLIENT_ID,
            "device_code": dc["device_code"],
        }
        url = f"https://{LOGIN_HOST}/consumers/oauth2/v2.0/token"
        first = c.post(url, data=body)
        assert first.status_code == 400
        assert first.json()["error"] == "authorization_pending"
        second = c.post(url, data=body)
        assert second.status_code == 200
        assert second.json()["access_token"].startswith(SECRET)
        assert second.json()["refresh_token"].startswith(SECRET)
    assert fake.violations == []


@pytest.mark.parametrize(
    ("step", "error", "codes"),
    [
        ("declined", "authorization_declined", True),
        ("expired", "expired_token", True),
        ("bad_code", "bad_verification_code", True),
        ("invalid_client", "invalid_client", [7000218]),
        ("slow_down", "slow_down", False),
    ],
)
def test_device_script_error_steps(step: str, error: str, codes: object) -> None:
    fake = FakeGraph(_tree(), device_script=[step])
    with _client(fake) as c:
        out = _login(fake, c)
    assert out["error"] == error
    if isinstance(codes, list):
        assert out["error_codes"] == codes
    assert (len(out.get("error_codes", [])) > 0) is bool(codes)
    assert SECRET in out["error_description"]


def test_graph_requires_current_bearer_and_serves_resolution() -> None:
    fake = FakeGraph(_tree())
    with _client(fake) as c:
        assert c.get(f"{BASE}/root:/Pasta").status_code == 401
        assert fake.violations == ["graph request without Authorization"]
        fake.violations.clear()
        tok = _login(fake, c)
        h = {"Authorization": f"Bearer {tok['access_token']}"}
        ok = c.get(f"{BASE}/root:/Pasta", headers=h)
        assert ok.status_code == 200 and "folder" in ok.json()
        assert ok.json()["parentReference"]["driveId"] == fake.drive_id
        assert c.get(f"{BASE}/root:/Nada", headers=h).status_code == 404
        assert (
            c.get(
                f"{BASE}/root:/Pasta", headers={"Authorization": "Bearer nope"}
            ).status_code
            == 401
        )
        # Unsupported shapes are violations (the reader must walk by item id).
        c.get(f"{BASE}/root/children", headers=h)
        c.get(f"{BASE}/search(q='x')", headers=h)
    assert len(fake.violations) == 2


def test_children_paging_and_facets() -> None:
    files = {f"f{i:03d}.txt": "x" for i in range(5)}
    fake = FakeGraph({"P": files}, page_size=2)
    pid = fake.id_of("/P")
    with _client(fake) as c:
        h = {"Authorization": f"Bearer {_login(fake, c)['access_token']}"}
        seen: list[str] = []
        url: str | None = f"{BASE}/items/{pid}/children?$top=200"
        pages = 0
        while url:
            data = c.get(url, headers=h).json()
            seen += [v["name"] for v in data["value"]]
            url = data.get("@odata.nextLink")
            pages += 1
        assert pages == 3 and seen == sorted(files)

        tree = {
            "R": {
                "s": Folder({"in.txt": "q"}, remote=True),
                "p": Folder(package=True),
                "m": File("m", malware=True),
                "d": File("d", deleted=True),
                "o": File("o", drive_id="DRIVE-OTHER-9"),
            }
        }
        fake2 = FakeGraph(tree)
    with _client(fake2) as c2:
        h2 = {"Authorization": f"Bearer {_login(fake2, c2)['access_token']}"}
        vals = {
            v["name"]: v
            for v in c2.get(
                f"{BASE}/items/{fake2.id_of('/R')}/children", headers=h2
            ).json()["value"]
        }
    assert "remoteItem" in vals["s"] and "folder" in vals["s"]
    assert "package" in vals["p"] and "malware" in vals["m"] and "deleted" in vals["d"]
    assert vals["o"]["parentReference"]["driveId"] == "DRIVE-OTHER-9"


def test_knobs_forbid_throttle_expire_and_next_link() -> None:
    fake = FakeGraph(_tree())
    fake.forbid("/Pasta/sub")
    fake.throttle(1, retry_after=7)
    fake.expire_access_after(3)
    fake.next_link_override = f"https://{EVIL_HOST}/v1.0/x"
    with _client(fake) as c:
        h = {"Authorization": f"Bearer {_login(fake, c)['access_token']}"}
        pid = fake.id_of("/Pasta")
        thr = c.get(f"{BASE}/items/{pid}/children", headers=h)
        assert thr.status_code == 429 and thr.headers["Retry-After"] == "7"
        ok = c.get(f"{BASE}/items/{pid}/children", headers=h)
        assert ok.json()["@odata.nextLink"] == f"https://{EVIL_HOST}/v1.0/x"
        sub = c.get(f"{BASE}/items/{fake.id_of('/Pasta/sub')}", headers=h)
        assert sub.status_code == 403
        # Three authenticated calls served (429, 200, 403); the next one finds the token expired.
        assert c.get(f"{BASE}/items/{pid}", headers=h).status_code == 401
    assert fake.violations == []


def test_refresh_rotates_and_rejects_the_old_token() -> None:
    fake = FakeGraph(_tree())
    url = f"https://{LOGIN_HOST}/consumers/oauth2/v2.0/token"
    with _client(fake) as c:
        tok = _login(fake, c)
        r1 = c.post(
            url,
            data={"grant_type": "refresh_token", "refresh_token": tok["refresh_token"]},
        ).json()
        assert r1["refresh_token"] != tok["refresh_token"]
        old = c.post(
            url,
            data={"grant_type": "refresh_token", "refresh_token": tok["refresh_token"]},
        )
        assert old.json()["error"] == "invalid_grant"
        fake.refresh_fails = "invalid_grant"
        bad = c.post(
            url,
            data={"grant_type": "refresh_token", "refresh_token": r1["refresh_token"]},
        )
        assert bad.json()["error"] == "invalid_grant"
    assert fake.refresh_count == 1


def test_download_redirect_and_download_host_rules() -> None:
    fake = FakeGraph({"P": {"a.txt": "conteudo"}})
    item = fake.id_of("/P/a.txt")
    with _client(fake) as c:
        h = {"Authorization": f"Bearer {_login(fake, c)['access_token']}"}
        r = c.get(f"{BASE}/items/{item}/content", headers=h)
        assert r.status_code == 302
        loc = r.headers["Location"]
        assert loc.startswith(f"https://{DEFAULT_DOWNLOAD_HOST}/") and SECRET in loc
        assert c.get(loc).content == b"conteudo"
        assert fake.violations == []
        c.get(loc, headers=h)  # leaking Authorization to the download host
        assert fake.violations == ["Authorization sent to the download host"]
        fake.download_fail_first = True
        assert c.get(loc).status_code == 403
        assert c.get(loc).status_code == 200
        fake.direct_content = True
        assert c.get(f"{BASE}/items/{item}/content", headers=h).content == b"conteudo"


def test_unexpected_host_and_client_secret_are_violations() -> None:
    fake = FakeGraph(_tree())
    with _client(fake) as c:
        c.get(f"https://{EVIL_HOST}/x")
        c.post(
            f"https://{LOGIN_HOST}/consumers/oauth2/v2.0/devicecode",
            data={"client_id": TEST_CLIENT_ID, "client_secret": "x"},
        )
    assert fake.violations == [
        f"unexpected host: {EVIL_HOST}",
        "client_secret sent to the login endpoint",
    ]


def test_regex_scanner_is_deterministic() -> None:
    scanner = RegexScanner()
    assert (
        scanner.scan_file_content("CPF 123.456.789-09", "a.txt")["pattern_detected"]
        == "LGPD_CPF"
    )
    assert (
        scanner.scan_file_content("a@exemplo.com", "c.csv")["pattern_detected"]
        == "EMAIL"
    )
    assert (
        scanner.scan_file_content("ata de reuniao sem dados pessoais", "b.txt") is None
    )
