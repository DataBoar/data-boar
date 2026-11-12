"""Contract for the LOCAL demo harness in ``deploy/demo-local/`` (#1447).

Static checks, no Podman: images pinned, every container limited and hardened,
secrets only through the environment, loopback only, scripts documented as
Linux host-only, and the config renderer behaving as the harness expects.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

import yaml

from core.brazilian_cpf import cpf_checksum_valid, normalize_cpf_digits
from tests.test_wheelhouse_sha256sums_gate import resolve_bash_executable

REPO = Path(__file__).resolve().parents[1]
DL = REPO / "deploy" / "demo-local"
SCRIPTS = ["up.sh", "down.sh", "rehearsal.sh", "build-extras.sh", "boar.sh", "web.sh"]
_DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, DL / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _images() -> dict[str, str]:
    out = {}
    for line in (DL / "images.env").read_text(encoding="utf-8").splitlines():
        m = re.match(r'^(IMG_[A-Z]+)="([^"]+)"$', line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def test_images_are_pinned_never_latest():
    imgs = _images()
    assert set(imgs) == {
        "IMG_POSTGRES",
        "IMG_REDIS",
        "IMG_MONGO",
        "IMG_HTTPD",
        "IMG_SAMBA",
        "IMG_BOAR",
    }
    for key, ref in imgs.items():
        assert ":latest" not in ref, key
        if key == "IMG_BOAR":  # published by version tag (matches deploy/demo quadlets)
            assert re.search(r":\d+\.\d+\.\d+$", ref), ref
        else:
            assert _DIGEST.search(ref), (key, ref)


def test_samba_digest_matches_the_demo_quadlet():
    quadlet = (REPO / "deploy/demo/quadlet/samba.container").read_text(encoding="utf-8")
    digest = _DIGEST.search(_images()["IMG_SAMBA"]).group(0)  # type: ignore[union-attr]
    assert digest in quadlet


def _run_blocks(text: str) -> list[str]:
    """Each `podman run ...` command, with continuation lines joined."""
    joined = text.replace("\\\n", " ")
    return [ln for ln in joined.splitlines() if "podman run -d" in ln]


def test_every_container_has_memory_limit_and_is_hardened():
    blocks: list[str] = []
    for name in ("up.sh", "web.sh", "lib.sh"):
        blocks += _run_blocks((DL / name).read_text(encoding="utf-8"))
    assert len(blocks) >= 6  # smb, pg, redis, mongo, httpd, boar
    for blk in blocks:
        assert re.search(r"--memory \d+m", blk), blk
        assert "--cap-drop all" in blk or "${HARDEN[@]}" in blk, blk
    lib = (DL / "lib.sh").read_text(encoding="utf-8")
    assert re.search(r"HARDEN=\(--cap-drop all --security-opt no-new-privileges\)", lib)
    smb = [b for b in blocks if "samba" in b.lower() or "IMG_SAMBA" in b][0]
    assert "no-new-privileges" in smb and "--cap-drop all" in smb


def test_published_ports_are_loopback_only():
    for name in ("up.sh", "web.sh"):
        for blk in _run_blocks((DL / name).read_text(encoding="utf-8")):
            for m in re.finditer(r"\s-p\s+\"?([^\s\"]+)", blk):
                assert m.group(1).startswith("127.0.0.1:"), (name, m.group(1))


def test_scripts_are_documented_linux_host_only_and_parse():
    bash = resolve_bash_executable()
    for name in SCRIPTS:
        text = (DL / name).read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:12])
        assert "Linux host-only" in head, name
        assert "set -x" not in text, name
        r = subprocess.run([bash, "-n", str(DL / name)], capture_output=True, text=True)
        assert r.returncode == 0, (name, r.stderr)
    for name in ("up.sh", "web.sh"):  # scripts that start things need rollback
        assert "trap " in (DL / name).read_text(encoding="utf-8") or name == "web.sh"


def test_pairing_docs_mention_the_harness_in_both_languages():
    for doc in (
        "SCRIPTS_CROSS_PLATFORM_PAIRING.md",
        "SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md",
    ):
        text = (REPO / "docs" / "ops" / doc).read_text(encoding="utf-8")
        assert "deploy/demo-local/" in text, doc


def test_config_template_uses_env_for_secrets_and_loopback_only():
    raw = (DL / "config.demo-local.yaml").read_text(encoding="utf-8")
    cfg = yaml.safe_load(
        re.sub(r"\$\{[A-Z_]+(?::-([^}]*))?\}", lambda m: m.group(1) or "/data", raw)
    )
    assert [t["name"] for t in cfg["targets"]][:5] == [
        "Lab_Postgres",
        "Demo_SMB_Compressed",
        "Lab_Redis",
        "Lab_Mongo",
        "Supabase_Simulated",
    ]
    for t in cfg["targets"]:
        assert "pass" not in t and "password" not in t, t["name"]
        host = t.get("host") or t.get("base_url")
        assert "127.0.0.1" in host, t["name"]
        assert t.get("allow_private_networks") is True
        assert t.get("allowed_hosts") == ["127.0.0.1"]
    creds = [t for t in cfg["targets"] if "pass_from_env" in t]
    assert len(creds) >= 5
    for t in creds:
        assert t["pass_from_env"].startswith("DATA_BOAR_DEMO_")
    fs = cfg["file_scan"]
    assert fs["scan_compressed"] is True
    assert {".zip", ".tgz", ".bz2", ".tar.bz2", ".7z"} <= set(
        fs["compressed_extensions"]
    )
    assert ".txt" not in fs["extensions"]  # EXPECTED.txt must not become a finding
    assert fs["file_passwords"] == {".7z": "demo-boar-7z-ficticia"}
    assert "supabase" not in raw.lower().replace("supabase_simulated", "").replace(
        "simulated supabase", ""
    ).replace("real supabase", "")


def _render(tmp_path: Path, **kw):
    mod = _load("render_config")
    ns = mod.argparse.Namespace(
        template=str(DL / "config.demo-local.yaml"),
        out=str(tmp_path / "c.yaml"),
        data_dir="/data",
        only=None,
        variant=None,
        supabase_file=None,
        no_web=False,
        list_env=None,
    )
    for k, v in kw.items():
        setattr(ns, k, v)
    return mod, mod.render(ns)


def test_render_filters_one_target_and_drops_web_when_asked(tmp_path):
    _, cfg = _render(tmp_path, only="Lab_Redis")
    assert [t["name"] for t in cfg["targets"]] == ["Lab_Redis"]
    _, cfg = _render(tmp_path, no_web=True)
    names = [t["name"] for t in cfg["targets"]]
    assert "WebDAV_Demo" not in names and "REST_Demo" not in names
    assert cfg["sqlite_path"] == "/data/audit_results.db"


def test_render_smb_variants_narrow_archives_and_passwords(tmp_path):
    mod, cfg = _render(tmp_path, only="Demo_SMB_Compressed", variant="7z-no-password")
    assert cfg["file_scan"]["compressed_extensions"] == [".7z"]
    assert cfg["file_scan"]["file_passwords"] == {}
    _, cfg = _render(tmp_path, only="Demo_SMB_Compressed", variant="7z-password")
    assert cfg["file_scan"]["file_passwords"] == {".7z": "demo-boar-7z-ficticia"}
    _, cfg = _render(tmp_path, only="Demo_SMB_Compressed", variant="7z-wrong-password")
    assert cfg["file_scan"]["file_passwords"] != {".7z": "demo-boar-7z-ficticia"}
    _, cfg = _render(tmp_path, only="Demo_SMB_Compressed", variant="tar.bz2")
    assert ".bz2" in cfg["file_scan"]["compressed_extensions"]


def test_render_merges_external_supabase_target_without_secrets(tmp_path):
    ext = tmp_path / "supabase.target.yaml"
    ext.write_text(
        yaml.safe_dump(
            {
                "name": "Supabase_Real",
                "type": "database",
                "driver": "postgresql+psycopg2",
                "host": "pooler.example.invalid",
                "port": 5432,
                "user": "u",
                "pass_from_env": "DATA_BOAR_SUPABASE_PASS",
                "database": "postgres",
            }
        ),
        encoding="utf-8",
    )
    mod, cfg = _render(tmp_path, supabase_file=str(ext))
    assert cfg["targets"][-1]["name"] == "Supabase_Real"
    assert "DATA_BOAR_SUPABASE_PASS" in mod.env_names(cfg)
    assert "pass" not in cfg["targets"][-1]


def test_supa_sim_seed_is_synthetic_deterministic_and_checksum_valid():
    seed = _load_seed("seed_supa_sim")
    sql = seed.build_sql()
    assert sql == seed.build_sql()
    cpfs = re.findall(r"'(\d{3}\.\d{3}\.\d{3}-\d{2})'", sql)
    assert len(cpfs) == seed.ROWS
    assert all(cpf_checksum_valid(normalize_cpf_digits(c)) for c in cpfs)
    assert "example.com" in sql and "@" in sql


def _load_seed(name: str):
    return _load(name)
