"""Render the local demo config (#1447): expand ${VAR:-default}, filter, merge.

Linux host tool, stdlib + PyYAML only. Secrets are never written: targets use
``pass_from_env`` and the harness passes the variables to Boar.

    render_config.py --template T --out O --data-dir D [--only NAME]
                     [--variant V] [--supabase-file F]
    render_config.py --list-env CONFIG
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

_VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")
WEB_TARGETS = {"WebDAV_Demo", "REST_Demo"}
_ENV_KEYS = ("pass_from_env", "password_from_env", "user_from_env")

# SMB variants: which archive formats are scanned and which 7z password is used.
# `compressed_extensions` must be narrowed too: the SMB connector scans every
# file whose suffix is in it, regardless of `extensions`.
VARIANTS: dict[str, dict] = {
    "zip": {"suffixes": [".zip"], "passwords": {}},
    "tgz": {"suffixes": [".tgz"], "passwords": {}},
    "tar.bz2": {"suffixes": [".bz2", ".tar.bz2"], "passwords": {}},
    "7z-password": {"suffixes": [".7z"], "passwords": "default"},
    "7z-no-password": {"suffixes": [".7z"], "passwords": {}},
    "7z-wrong-password": {
        "suffixes": [".7z"],
        "passwords": {".7z": "senha-errada-demo"},
    },
}


def expand(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        val = os.environ.get(m.group(1))
        if val:
            return val
        if m.group(2) is not None:
            return m.group(2)
        raise SystemExit(f"render_config: variable {m.group(1)} is not set")

    return _VAR.sub(repl, text)


def env_names(cfg: dict) -> list[str]:
    out: list[str] = []
    for t in cfg.get("targets") or []:
        for key in _ENV_KEYS:
            val = str(t.get(key) or "").strip()
            if val and val not in out:
                out.append(val)
    return out


def render(args: argparse.Namespace) -> dict:
    os.environ["DEMO_LOCAL_DATA_DIR"] = args.data_dir
    cfg = yaml.safe_load(expand(Path(args.template).read_text(encoding="utf-8")))
    if args.supabase_file:
        extra = yaml.safe_load(Path(args.supabase_file).read_text(encoding="utf-8"))
        targets = extra.get("targets") if isinstance(extra, dict) else extra
        if isinstance(extra, dict) and "name" in extra:
            targets = [extra]
        cfg["targets"] = [*cfg["targets"], *(targets or [])]
    if args.no_web:
        cfg["targets"] = [t for t in cfg["targets"] if t.get("name") not in WEB_TARGETS]
    if args.only:
        wanted = {n.strip() for n in args.only.split(",")}
        cfg["targets"] = [t for t in cfg["targets"] if t.get("name") in wanted]
        if not cfg["targets"]:
            raise SystemExit(f"render_config: no target named {args.only}")
    if args.variant:
        var = VARIANTS[args.variant]
        fs = cfg["file_scan"]
        fs["extensions"] = [*var["suffixes"], ".csv"]
        fs["compressed_extensions"] = list(var["suffixes"])
        if var["passwords"] != "default":
            fs["file_passwords"] = dict(var["passwords"])
    return cfg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template")
    ap.add_argument("--out")
    ap.add_argument("--data-dir")
    ap.add_argument("--only")
    ap.add_argument("--variant", choices=sorted(VARIANTS))
    ap.add_argument("--supabase-file")
    ap.add_argument("--list-env")
    ap.add_argument(
        "--no-web", action="store_true", help="drop the WebDAV/REST targets"
    )
    args = ap.parse_args()
    if args.list_env:
        cfg = yaml.safe_load(Path(args.list_env).read_text(encoding="utf-8"))
        print("\n".join(env_names(cfg)))
        return 0
    if not (args.template and args.out and args.data_dir):
        ap.error("--template, --out and --data-dir are required")
    cfg = render(args)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    out.chmod(0o600)
    return 0


if __name__ == "__main__":
    sys.exit(main())
