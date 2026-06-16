"""
test_claims_consistency.py — gate determinístico ANTI-OVERCLAIM (offline, sem rede, sem git/gh).

A) Invariantes de consistência interna (estática, AST/regex sobre o checkout atual):
   - connector↔tier : todo connector registrado (register("x", ...)) TEM entrada no FEATURE_TIER_MAP
                      (eleva o fail-closed do #854 de runtime → BUILD-TIME).
   - feature↔gate   : toda feature do FEATURE_TIER_MAP é referenciada por is_feature_available(...)
                      (sem "gate-fantasma"). [informativo por default — vira hard-gate quando calibrado]
B) Manifesto docs/CLAIMS.yml (opcional): cada claim.backed_by aponta pra lastro que EXISTE.
   Claim headline sem lastro ⇒ vermelho.

Contraparte HEAVY/on-demand = `claim-audit` (lab-op, ~/.local/bin/claim-audit): sincroniza +
grep + `gh`, interativo e heurístico. Este teste = a LIGHT/automática no check-all.

Roda como pytest OU standalone:  python tests/test_claims_consistency.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIER_FILE = ROOT / "core" / "licensing" / "tier_features.py"
CONNECTORS_DIR = ROOT / "connectors"
CLAIMS_FILE = ROOT / "docs" / "CLAIMS.yml"


def tier_map_keys() -> set[str]:
    src = TIER_FILE.read_text(encoding="utf-8")
    return set(re.findall(r'"([A-Za-z0-9_]+)"\s*:\s*Tier\.', src))


def registered_connectors() -> set[str]:
    names: set[str] = set()
    for p in CONNECTORS_DIR.glob("*.py"):
        for m in re.finditer(
            r'register\(\s*"([A-Za-z0-9_]+)"', p.read_text(encoding="utf-8")
        ):
            names.add(m.group(1))
    return names


def feature_gate_calls() -> set[str]:
    calls: set[str] = set()
    for p in ROOT.rglob("*.py"):
        if "tests" in p.parts or ".venv" in p.parts:
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in re.finditer(r'is_feature_available\(\s*"([A-Za-z0-9_]+)"', txt):
            calls.add(m.group(1))
    return calls


def connectors_without_tier() -> list[str]:
    # aliases: connector registrado que mapeia p/ a família de tier de OUTRO connector.
    # PLAN_CONNECTOR_TIER_GATING: powerapps targets → connector_dataverse.
    aliases = {"powerapps": "dataverse"}
    keys, regs = tier_map_keys(), registered_connectors()
    missing = []
    for c in regs:
        eff = aliases.get(c, c)
        if f"connector_{eff}" not in keys and eff not in keys:
            missing.append(c)
    return sorted(missing)


def features_without_gate() -> list[str]:
    keys, gated = tier_map_keys(), feature_gate_calls()
    # connectors são "gateados" no registry, não via is_feature_available → fora do escopo aqui
    candidates = {k for k in keys if not k.startswith("connector_")}
    return sorted(k for k in candidates if k not in gated)


def claims_without_backing() -> list[str]:
    if not CLAIMS_FILE.exists():
        return []
    try:
        import yaml  # pyyaml
    except ImportError:
        return []  # ambiente sem pyyaml: pula a peça B (não quebra o gate)
    data = yaml.safe_load(CLAIMS_FILE.read_text(encoding="utf-8")) or {}
    keys, regs = tier_map_keys(), registered_connectors()
    errs: list[str] = []
    for c in data.get("claims", []):
        cid = c.get("id", "?")
        for b in c.get("backed_by", []) or []:
            for typ, val in b.items():
                if typ in ("file", "adr", "doc", "test"):
                    if not (ROOT / val).exists():
                        errs.append(f"{cid}: {typ} '{val}' não existe")
                elif typ == "symbol":
                    fp, _, sym = str(val).partition("::")
                    p = ROOT / fp
                    if not p.exists() or sym not in p.read_text(encoding="utf-8"):
                        errs.append(f"{cid}: symbol '{val}' não encontrado")
                elif typ == "tier_feature":
                    if val not in keys:
                        errs.append(
                            f"{cid}: tier_feature '{val}' ausente do FEATURE_TIER_MAP"
                        )
                elif typ == "registry":
                    if val not in regs:
                        errs.append(f"{cid}: registry '{val}' não registrado")
                # issue / note / benchmark = informativo (não falha)
    return errs


# ---------------- pytest ----------------
def test_connector_tier_invariant():
    missing = connectors_without_tier()
    assert not missing, (
        f"Connectors registrados SEM tier no FEATURE_TIER_MAP (#854 build-time): {missing}"
    )


def test_claims_manifest_backed():
    errs = claims_without_backing()
    assert not errs, "Claims headline sem lastro:\n  " + "\n  ".join(errs)


def test_feature_gate_report():
    # informativo por default — promover a `assert not orphans` quando o map estiver calibrado
    orphans = features_without_gate()
    if orphans:
        print("⚠️ features tier-mapeadas sem is_feature_available (revisar):", orphans)


if __name__ == "__main__":
    ct = connectors_without_tier()
    fg = features_without_gate()
    cl = claims_without_backing()
    print(f"connectors registrados: {sorted(registered_connectors())}")
    print(f"connector↔tier MISSING : {ct or 'nenhum ✅'}")
    print(f"feature-gate orphans   : {fg or 'nenhum ✅'} (informativo)")
    print(f"claims sem lastro      : {cl or 'nenhum ✅'}")
    sys.exit(1 if (ct or cl) else 0)
