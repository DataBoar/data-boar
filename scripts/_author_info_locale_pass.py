"""One-off pt-BR pass for docs/private/author_info/*.md (run from repo root).

Skips aggressive partilh* / repost wording — fix those files manually if needed.
"""

from __future__ import annotations

import pathlib


def fix_common(text: str) -> str:
    t = text
    pairs = [
        ("Secção", "Seção"),
        ("secção", "seção"),
        ("ficheiros", "arquivos"),
        ("Ficheiros", "Arquivos"),
        ("ficheiro", "arquivo"),
        ("Ficheiro", "Arquivo"),
        ("contacto", "contato"),
        ("Contacto", "Contato"),
        ("canónicos", "canônicos"),
        ("canónico", "canônico"),
        ("canónica", "canônica"),
        ("quiseres", "quiser"),
        ("tiveres", "tiver"),
        ("registo", "registro"),
        ("utilizadores", "usuários"),
        ("utilizador", "usuário"),
        ("Utilizador", "Usuário"),
        ("planeamento", "planejamento"),
        ("Planeamento", "Planejamento"),
    ]
    for a, b in pairs:
        t = t.replace(a, b)
    return t


def main() -> None:
    root = pathlib.Path("docs/private/author_info")
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        updated = fix_common(text)
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="\n")
            print("updated", path)


if __name__ == "__main__":
    main()
