"""Limits of the ``object_storage`` common layer (epic #2306, task 2306.2).

Source: ``docs/desenho/2306.md`` (revision 5), section 1 (limits, ``unlimited``, timeouts),
section 7 (``max_objects``, DEC-6) and section 8 (budget, per-object ceiling, failures with
``report_object_names``, DEC-11 and DEC-13). Cases ``D2306-25``, ``D2306-48`` ..
``D2306-52``, ``D2306-68``, ``D2306-69`` and ``D2306-74``.

D-68 runs the same limit scenarios with the S3 driver and with the toy driver and compares
the failures: the limit behaviour belongs to the common layer.
"""

from __future__ import annotations

import logging
import secrets
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.object_storage_dev_harness import (
    BUCKET,
    CPF_TXT,
    EXPECTED_PATHS,
    MIB,
    Harness,
    HostileFakeS3,
    LyingToyStore,
    capture_pinned_client,
    executive,
    ops,
    paths,
    s3_target,
    skipped_detail,
    toy_target,
)

LIMIT_MAX = {
    "max_objects": 1_000_000,
    "max_download_bytes": 107_374_182_400,
    "max_object_bytes": 2_147_483_648,
}


@pytest.fixture
def h(monkeypatch: pytest.MonkeyPatch) -> Harness:
    return Harness(monkeypatch)


def _small(n: int, ext: str = ".txt", size: int = 1) -> dict[str, bytes]:
    return {f"corpus/k{i:03d}{ext}": b"x" * size for i in range(n)}


# ----------------------------------------------------------------------------
# D-25: validation of the limits and of the timeouts
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("key", sorted(LIMIT_MAX))
@pytest.mark.parametrize("bad", ["10", True, 0, -1, "above"])
def test_D2306_25_limite_invalido_da_config_error(
    h: Harness, key: str, bad: Any
) -> None:
    """D2306-25: each limit with "10", True, 0, -1 or above the maximum -> config_error
    citing the key, and zero requests (never a silent adjustment)."""
    value = LIMIT_MAX[key] + 1 if bad == "above" else bad
    fake = h.s3()
    out = h.run(fake.transport, s3_target(**{key: value}))

    assert out.db.reasons() == ["config_error"]
    (detail,) = out.db.details("config_error")
    assert key in detail
    assert fake.requests == []
    h.control_scan()


def test_D2306_25_padrao_de_max_object_bytes_e_100_mib(h: Harness) -> None:
    """D2306-25 (default max_object_bytes = 100 MiB): a listed Size of 100 MiB + 1 is not
    fetched (too_large); a listed Size of exactly 100 MiB is fetched."""
    fake = h.s3({"corpus/grande.txt": b"x", "corpus/limite.txt": b"x"})
    fake.lie_size("corpus/grande.txt", 100 * MIB + 1, 1)
    fake.lie_size("corpus/limite.txt", 100 * MIB, 1)
    out = h.run(fake.transport, s3_target())

    assert fake.fetched == ["corpus/limite.txt"]
    assert "too_large=1" in skipped_detail(out.db)


def test_D2306_25_padrao_de_max_download_bytes_e_1_gib(h: Harness) -> None:
    """D2306-25 (default max_download_bytes = 1 GiB): with max_object_bytes unlimited, a
    listed Size above 1 GiB counts over_budget and is not fetched."""
    fake = h.s3({"corpus/enorme.txt": b"x"})
    fake.lie_size("corpus/enorme.txt", 1024 * MIB + 1, 1)
    out = h.run(fake.transport, s3_target(max_object_bytes="unlimited"))

    assert fake.fetched == []
    assert out.db.details("limit_reached") == [
        "max_download_bytes reached; 1 objects not downloaded"
    ]


def test_D2306_25_padrao_de_max_objects_e_10000(h: Harness) -> None:
    """D2306-25 (default max_objects = 10000): 10001 listed entries stop at 10000 with
    limit_reached (the keys are .exe, outside the filter, so nothing is downloaded)."""
    fake = h.s3(_small(10_001, ext=".exe"))
    out = h.run(fake.transport, s3_target())

    assert out.db.details("limit_reached") == [
        "max_objects reached (10000); listing stopped before the end of the prefix"
    ]
    assert ops(fake, "GetObject") == 0


@pytest.mark.parametrize(
    ("extra", "connect", "read"),
    [
        ({"timeout": 5}, 5, 5),
        ({}, 25, 90),
        ({"connect_timeout_seconds": 3, "read_timeout_seconds": 40}, 3, 40),
    ],
)
def test_D2306_25_timeout_por_requisicao(
    h: Harness,
    monkeypatch: pytest.MonkeyPatch,
    extra: dict[str, Any],
    connect: int,
    read: int,
) -> None:
    """D2306-25 (timeouts): without the normalised keys and with timeout: 5, connect 5 and
    read 5; with none of the keys, 25 and 90; the normalised keys win."""
    fake = h.s3()
    seen = capture_pinned_client(monkeypatch, fake.transport)
    out = h.run(None, s3_target(**extra))

    assert len(seen) == 1
    assert seen[0]["timeout"] == httpx.Timeout(
        connect=connect, read=read, write=read, pool=connect
    )
    assert paths(out.db) == EXPECTED_PATHS


@pytest.mark.parametrize(
    "extra",
    [
        {"read_timeout_seconds": 301},
        {"connect_timeout_seconds": 0},
        {"timeout": 301},
    ],
)
def test_D2306_25_timeout_fora_da_faixa_da_config_error(
    h: Harness, extra: dict[str, Any]
) -> None:
    """D2306-25: a timeout outside 1..300 (read_timeout_seconds 301, for instance) gives
    config_error and zero requests."""
    fake = h.s3()
    out = h.run(fake.transport, s3_target(**extra))

    assert out.db.reasons() == ["config_error"]
    assert fake.requests == []


# ----------------------------------------------------------------------------
# D-48 to D-52
# ----------------------------------------------------------------------------


def test_D2306_48_max_objects_corta_a_listagem(h: Harness) -> None:
    """D2306-48: 25 keys and max_objects: 10 -> one listing with max-keys=10, at most 10
    objects considered and limit_reached; 10 keys and an untruncated answer -> no
    limit_reached; a server returning 15 entries for max-keys=10 with IsTruncated=false ->
    10 considered and limit_reached."""
    fake = h.s3(_small(25))
    out = h.run(fake.transport, s3_target(max_objects=10))
    lists = [
        r for r, op in zip(fake.requests, fake.operations) if op == "ListObjectsV2"
    ]
    assert len(lists) == 1
    assert "max-keys=10" in lists[0].raw_query.split("&")
    assert len(fake.fetched) == 10
    assert out.db.details("limit_reached") == [
        "max_objects reached (10); listing stopped before the end of the prefix"
    ]

    fake = h.s3(_small(10))
    out = h.run(fake.transport, s3_target(max_objects=10))
    assert len(fake.fetched) == 10
    assert "limit_reached" not in out.db.reasons()

    fake = h.s3(_small(15), cls=HostileFakeS3)
    fake.overshoot = 5
    out = h.run(fake.transport, s3_target(max_objects=10))
    assert len(fake.fetched) == 10
    assert out.db.details("limit_reached") == [
        "max_objects reached (10); listing stopped before the end of the prefix"
    ]


def _named(tag: str, n: int) -> dict[str, bytes]:
    return {f"corpus/{tag}-{i:03d}.txt": b"xy" for i in range(n)}


@pytest.mark.parametrize("names", [False, True])
def test_D2306_49_objeto_grande_demais(
    h: Harness, caplog: pytest.LogCaptureFixture, names: bool
) -> None:
    """D2306-49 (revision 2): Size above max_object_bytes -> no GetObject. Without
    report_object_names: no failure carries s3:// nor the object name, the skipped summary
    counts too_large=1 and the inventory has bytes_not_scanned equal to the listed Size.
    With report_object_names: true, one too_large failure with s3://<bucket>/<key>."""
    caplog.set_level(logging.DEBUG)
    mark = "SYNTHMK" + secrets.token_hex(6)
    key = f"corpus/{mark}.txt"
    fake = h.s3({key: CPF_TXT, "corpus/ok.txt": b"x"})
    target = s3_target(max_object_bytes=10)
    if names:
        target["report_object_names"] = True
    out = h.run(fake.transport, target)

    assert key not in fake.fetched
    assert "corpus/ok.txt" in fake.fetched
    assert "too_large=1" in skipped_detail(out.db)
    assert executive(out.db)["bytes_not_scanned"] == len(CPF_TXT)
    if names:
        (detail,) = out.db.details("too_large")
        assert detail.startswith(f"s3://{BUCKET}/{key}: ")
    else:
        assert out.db.details("too_large") == []
        failures = repr(out.db.failures)
        assert "s3://" not in failures
        assert mark not in failures
        assert mark not in repr(out.db.inventories)
        assert mark not in caplog.text


def test_D2306_50_orcamento_de_download(h: Harness) -> None:
    """D2306-50: 40, 40, 40 bytes and max_download_bytes: 100 -> two downloaded, the third
    over_budget and limit_reached "max_download_bytes reached; 1 objects not downloaded";
    40, 70, 20 -> the 70 is over_budget and the 20 is downloaded."""
    fake = h.s3({f"corpus/a{i}.txt": b"x" * 40 for i in range(3)})
    out = h.run(fake.transport, s3_target(max_download_bytes=100))
    assert fake.fetched == ["corpus/a0.txt", "corpus/a1.txt"]
    assert out.db.details("limit_reached") == [
        "max_download_bytes reached; 1 objects not downloaded"
    ]

    fake = h.s3(
        {
            "corpus/a0.txt": b"x" * 40,
            "corpus/a1.txt": b"x" * 70,
            "corpus/a2.txt": b"x" * 20,
        }
    )
    out = h.run(fake.transport, s3_target(max_download_bytes=100))
    assert fake.fetched == ["corpus/a0.txt", "corpus/a2.txt"]
    assert out.db.details("limit_reached") == [
        "max_download_bytes reached; 1 objects not downloaded"
    ]


@pytest.mark.parametrize(("declared", "actual"), [(10, 20), (20, 10)])
def test_D2306_51_tamanho_mentiroso_da_size_mismatch(
    h: Harness, declared: int, actual: int
) -> None:
    """D2306-51: the server sending more bytes than the listed Size, or fewer, gives
    size_mismatch, no finding from that object, and the temporary file is gone."""
    made = h.spy_mkdtemp()
    fake = h.s3({"corpus/a.txt": CPF_TXT, "corpus/ok.txt": CPF_TXT})
    fake.lie_size("corpus/a.txt", declared, actual)
    out = h.run(fake.transport, s3_target())

    assert "corpus/a.txt" in fake.fetched
    assert "size_mismatch=1" in skipped_detail(out.db)
    assert paths(out.db) == {f"s3://{BUCKET}/corpus/ok.txt"}
    assert made
    assert not any(Path(d).exists() for d in made)


def test_D2306_52_content_length_acima_do_teto_aborta_sem_ler(h: Harness) -> None:
    """D2306-52: a Content-Length above the ceiling aborts the read without consuming the
    body (the simulator counts the bytes delivered)."""
    fake = h.s3({"corpus/a.txt": CPF_TXT, "corpus/ok.txt": CPF_TXT})
    fake.content_length("corpus/a.txt", 10 * MIB)
    out = h.run(fake.transport, s3_target())

    assert "corpus/a.txt" in fake.fetched
    assert fake.delivered("corpus/a.txt") == 0
    assert fake.delivered("corpus/ok.txt") == len(CPF_TXT)
    assert "size_mismatch=1" in skipped_detail(out.db)


# ----------------------------------------------------------------------------
# D-68: the same limits with the toy driver
# ----------------------------------------------------------------------------


def _scenario(name: str) -> tuple[dict[str, bytes], dict[str, Any], dict[str, int]]:
    if name == "max_objects":  # D-48
        return _small(25), {"max_objects": 10}, {}
    if name == "max_download_bytes":  # D-50
        return (
            {f"corpus/a{i}.txt": b"x" * 40 for i in range(3)},
            {"max_download_bytes": 100},
            {},
        )
    # size_mismatch (D-51): the listing says 10 bytes, the body has len(CPF_TXT).
    return {"corpus/a.txt": CPF_TXT, "corpus/ok.txt": CPF_TXT}, {}, {"corpus/a.txt": 10}


@pytest.mark.parametrize("name", ["max_objects", "max_download_bytes", "size_mismatch"])
def test_D2306_68_limites_iguais_com_o_driver_de_brinquedo(
    h: Harness, name: str
) -> None:
    """D2306-68: the D-48, D-50 and D-51 cases with the toy driver give the same failures
    and counts as with the S3 driver: the limit behaviour is the common layer's."""
    objects, limits, lies = _scenario(name)
    fake = h.s3(objects)
    for key, declared in lies.items():
        fake.lie_size(key, declared, len(objects[key]))
    s3_out = h.run(fake.transport, s3_target(**limits))

    store = h.toy(objects, store=LyingToyStore, declared=lies)
    toy_out = h.run(store.transport, toy_target(**limits))

    assert s3_out.db.failures
    assert toy_out.db.failures == s3_out.db.failures
    s3_ex, toy_ex = executive(s3_out.db), executive(toy_out.db)
    for key in (
        "objects_not_scanned",
        "not_scanned_by_reason",
        "objects_downloaded",
        "objects_scanned",
    ):
        assert toy_ex[key] == s3_ex[key], key


# ----------------------------------------------------------------------------
# D-69 and D-74
# ----------------------------------------------------------------------------


def test_D2306_69_nomes_so_com_report_object_names(
    h: Harness, caplog: pytest.LogCaptureFixture
) -> None:
    """D2306-69: with report_object_names: true and 150 too_large objects, 100 per-object
    failures and the summary with too_large=150; with false, zero per-object failures and
    no object name in failures, log or inventory (names carry a marker)."""
    mark = "SYNTHMK" + secrets.token_hex(6)
    objects = _named(mark, 150)

    fake = h.s3(objects)
    out = h.run(fake.transport, s3_target(max_object_bytes=1, report_object_names=True))
    assert fake.fetched == []
    assert len(out.db.details("too_large")) == 100
    assert "too_large=150" in skipped_detail(out.db)

    caplog.clear()
    caplog.set_level(logging.DEBUG)
    fake = h.s3(objects)
    out = h.run(fake.transport, s3_target(max_object_bytes=1))
    assert out.db.details("too_large") == []
    assert "too_large=150" in skipped_detail(out.db)
    assert mark not in repr(out.db.failures)
    assert mark not in repr(out.db.inventories)
    assert mark not in caplog.text


@pytest.mark.parametrize("key", sorted(LIMIT_MAX))
def test_D2306_74_unlimited_desliga_o_limite_no_alvo(h: Harness, key: str) -> None:
    """D2306-74: each limit with "unlimited" stops cutting; limits_disabled names it.
    For max_objects: 25 keys are all considered, without limit_reached."""
    fake = h.s3(_small(25))
    out = h.run(fake.transport, s3_target(**{key: "unlimited"}))

    assert len(fake.fetched) == 25
    assert "limit_reached" not in out.db.reasons()
    ex = executive(out.db)
    assert key in ex["limits_disabled"]
    assert ex["coverage"] == "complete"


@pytest.mark.parametrize("key", sorted(LIMIT_MAX))
@pytest.mark.parametrize("bad", ["Unlimited", "none", None, 0])
def test_D2306_74_so_unlimited_exato_desliga(h: Harness, key: str, bad: Any) -> None:
    """D2306-74: "Unlimited", "none", null and 0 give config_error (no implicit "off")."""
    fake = h.s3()
    out = h.run(fake.transport, s3_target(**{key: bad}))

    assert out.db.reasons() == ["config_error"]
    assert fake.requests == []
