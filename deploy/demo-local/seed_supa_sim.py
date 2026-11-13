"""SQL for the SIMULATED Supabase database ``supa_sim`` (#1447, local demo).

Prints CREATE TABLE + INSERTs to stdout. Names, e-mails and CPFs are synthetic:
CPFs are built with valid Mod-11 check digits by the corpus helper, e-mails use
the reserved ``example.com`` domain. Deterministic (fixed seed).
"""

from __future__ import annotations

import random

from core.demo.synthetic_corpus import _NAMES, _cpf_check_digits

ROWS = 60
EXPECTED_SENSITIVE_COLUMNS = ("cpf", "email")


def _cpf(rng: random.Random) -> str:
    base = [rng.randrange(10) for _ in range(9)]
    if len(set(base)) == 1:  # all-equal bases are rejected by validators
        base[0] = (base[0] + 1) % 10
    d1, d2 = _cpf_check_digits(base)
    s = "".join(map(str, [*base, d1, d2]))
    return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}"


def build_sql(rows: int = ROWS) -> str:
    rng = random.Random(1447)
    out = [
        "CREATE TABLE public.clientes_sim (",
        "  id serial PRIMARY KEY,",
        "  nome text NOT NULL,",
        "  cpf text NOT NULL,",
        "  email text NOT NULL,",
        "  plano text NOT NULL",
        ");",
        "COMMENT ON TABLE public.clientes_sim IS 'Synthetic data; simulates a Supabase table.';",
    ]
    for i in range(rows):
        nome = _NAMES[i % len(_NAMES)]
        slug = nome.lower().replace(" ", ".")
        out.append(
            "INSERT INTO public.clientes_sim (nome, cpf, email, plano) VALUES "
            f"('{nome}', '{_cpf(rng)}', '{slug}.{i}@example.com', "
            f"'{rng.choice(['free', 'pro', 'team'])}');"
        )
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    print(build_sql(), end="")
