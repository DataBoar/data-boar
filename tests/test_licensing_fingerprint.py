from __future__ import annotations

from core.licensing.fingerprint import compute_machine_fingerprint


def test_machine_fingerprint_is_stable_for_same_seed_and_host(monkeypatch):
    monkeypatch.setenv("DATA_BOAR_MACHINE_SEED", "seed-A")
    monkeypatch.setattr("socket.gethostname", lambda: "host-1")

    a = compute_machine_fingerprint()
    b = compute_machine_fingerprint()

    assert a == b
    assert len(a) == 64
    assert all(c in "0123456789abcdef" for c in a)


def test_machine_fingerprint_changes_when_seed_changes(monkeypatch):
    monkeypatch.setattr("socket.gethostname", lambda: "host-1")
    monkeypatch.setenv("DATA_BOAR_MACHINE_SEED", "seed-A")
    a = compute_machine_fingerprint()

    monkeypatch.setenv("DATA_BOAR_MACHINE_SEED", "seed-B")
    b = compute_machine_fingerprint()

    assert a != b
