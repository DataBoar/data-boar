from __future__ import annotations

import re
from pathlib import Path


def clean_profile_name(cell: str) -> str:
    # In the table, the first column sometimes includes leading counters like "10|| Colleague-K".
    # After markdown splitting, that ends up inside the "Perfil" cell.
    c = cell.strip()
    c = re.sub(r"^\s*\d+\s*\|\|\s*", "", c)
    # If the cell still contains "||", keep the last segment.
    if "||" in c:
        c = c.split("||")[-1].strip()
    return c.strip()


def extract_rows_from_relationship_map(map_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in map_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        if "Perfil" in s and "Vínculo" in s:
            continue
        if set(s.replace("|", "").strip()) <= {"-", " "}:
            continue
        # Only consider table area rows (6 columns expected).
        # Note: this assumes no cell contains a literal '|' character.
        parts = [p.strip() for p in s.strip("|").split("|")]
        if len(parts) < 6:
            continue
        perfil, vinculo, cruzamento, evidencia, confianca, pendente = parts[:6]
        rows.append(
            {
                "perfil": clean_profile_name(perfil),
                "vinculo": vinculo,
                "cruzamento": cruzamento,
                "evidencia": evidencia,
                "confianca": confianca,
                "pendente": pendente,
            }
        )
    return rows


def build_operator_centered_graph(rows: list[dict[str, str]]) -> str:
    # Mermaid graph. We keep it operator-centered because the source map is
    # narrative-heavy and doesn't encode explicit edges deterministically.
    # This gives a safe "mesh starter" for visualization and auditing.
    lines: list[str] = []
    lines.append("graph TD")
    lines.append('  operador["Operador (você)"]:::core')

    # Classes for styling
    lines.append("  classDef core fill:#0b3a66,color:#fff,stroke:#0b3a66;")
    lines.append("  classDef family fill:#1f7a4a,color:#fff,stroke:#1f7a4a;")
    lines.append("  classDef professional fill:#5b3a88,color:#fff,stroke:#5b3a88;")
    lines.append("  classDef both fill:#8a2d2d,color:#fff,stroke:#8a2d2d;")
    lines.append("")

    # Node ids: slug-like
    def node_id(name: str) -> str:
        nid = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower())
        nid = re.sub(r"_+", "_", nid).strip("_")
        return nid or "node"

    # Deduplicate by profile
    seen: set[str] = set()

    for r in rows:
        name = r["perfil"]
        if not name or name in seen:
            continue
        seen.add(name)

        nid = node_id(name)
        vinculo_sim = "Sim" in r["vinculo"]
        profissional_ok = "Confirmado pelo operador" in r["evidencia"]

        # Node label: keep it short
        label = name.replace('"', "'")

        # Create node and connect to operator
        lines.append(f'  {nid}["{label}"]')

        if vinculo_sim and profissional_ok:
            lines.append(f"  operador -->|família + profissional| {nid}")
            lines.append(f"  class {nid} both")
        elif vinculo_sim:
            lines.append(f"  operador -->|família| {nid}")
            lines.append(f"  class {nid} family")
        elif profissional_ok:
            lines.append(f"  operador -->|profissional| {nid}")
            lines.append(f"  class {nid} professional")
        else:
            # Keep it as a neutral node (still visible for auditing).
            lines.append(f"  operador -->|associado| {nid}")
            lines.append(f"  class {nid} professional")

    return "\n".join(lines)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    map_path = (
        repo_root
        / "docs"
        / "private"
        / "commercial"
        / "TALENT_POOL_RELATIONSHIP_MAP.pt_BR.md"
    )
    out_path = (
        repo_root
        / "docs"
        / "private"
        / "commercial"
        / "TALENT_POOL_RELATIONSHIP_MERMAID.pt_BR.md"
    )

    map_text = map_path.read_text(encoding="utf-8")
    rows = extract_rows_from_relationship_map(map_text)

    graph = build_operator_centered_graph(rows)

    out_lines: list[str] = []
    out_lines.append("# Rede de relações (Mermaid)")
    out_lines.append("")
    out_lines.append(
        "> Fonte: `TALENT_POOL_RELATIONSHIP_MAP.pt_BR.md` (mapa narrativo)."
    )
    out_lines.append(
        "> Export gerado por `scripts/export_talent_relationship_mermaid.py`."
    )
    out_lines.append("")
    out_lines.append("```mermaid")
    out_lines.append(graph)
    out_lines.append("```")

    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
