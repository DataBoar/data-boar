"""Synthetic files for the optional WebDAV + REST toy container (#1447).

Usage: seed_web.py <out-dir>   (writes <out>/dav/cadastro_webdav.csv and
<out>/api/people). CPFs have valid check digits; e-mails use example.com.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from core.demo.synthetic_corpus import _NAMES, _cpf_check_digits


def _cpf(rng: random.Random) -> str:
    base = [rng.randrange(10) for _ in range(9)]
    if len(set(base)) == 1:
        base[0] = (base[0] + 1) % 10
    d1, d2 = _cpf_check_digits(base)
    s = "".join(map(str, [*base, d1, d2]))
    return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}"


def people(n: int = 6) -> list[dict[str, str]]:
    rng = random.Random(14470)
    out = []
    for i in range(n):
        nome = _NAMES[i % len(_NAMES)]
        out.append(
            {
                "nome": nome,
                "cpf": _cpf(rng),
                "email": f"{nome.lower().replace(' ', '.')}.{i}@example.com",
            }
        )
    return out


def main(out_dir: str) -> None:
    out = Path(out_dir)
    (out / "dav").mkdir(parents=True, exist_ok=True)
    (out / "api").mkdir(parents=True, exist_ok=True)
    rows = ["nome,cpf,email"] + [
        f"{p['nome']},{p['cpf']},{p['email']}" for p in people()
    ]
    (out / "dav" / "cadastro_webdav.csv").write_text(
        "\n".join(rows) + "\n", encoding="utf-8"
    )
    (out / "api" / "people").write_text(
        json.dumps(people(), ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main(sys.argv[1])
