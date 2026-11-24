#!/usr/bin/env python3
"""Synthetic SQLite corpus with image BLOB / base64 columns (#2362)."""

from __future__ import annotations

import argparse
import base64
import io
import random
import sqlite3
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core.brazilian_cpf import cpf_checksum_valid


def _cpf_digit(base: list[int], count: int) -> int:
    total = sum(base[i] * (count + 1 - i) for i in range(count))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def _synthetic_cpf(rng: random.Random) -> str:
    while True:
        base = [rng.randint(0, 9) for _ in range(9)]
        if len(set(base)) == 1:
            continue
        d1 = _cpf_digit(base, 9)
        d2 = _cpf_digit(base + [d1], 10)
        digits = "".join(str(x) for x in base + [d1, d2])
        if cpf_checksum_valid(digits):
            return digits


def _jpeg_bytes(rng: random.Random, cpf: str) -> bytes:
    im = Image.new("RGB", (320, 120), color=(240, 240, 240))
    draw = ImageDraw.Draw(im)
    font = ImageFont.load_default()
    draw.text((12, 40), f"CPF {cpf}", fill=(0, 0, 0), font=font)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _png_bytes() -> bytes:
    im = Image.new("RGB", (4, 4), color=(32, 64, 128))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def _pdf_bytes() -> bytes:
    im = Image.new("RGB", (64, 64), color=(255, 255, 255))
    buf = io.BytesIO()
    fixed = time.strptime("2026-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
    im.save(buf, format="PDF", resolution=72.0, creationDate=fixed, modDate=fixed)
    return buf.getvalue()


def _b64_data_uri_png(png: bytes) -> str:
    # Wrap with newlines every 76 chars in the payload portion
    raw = base64.b64encode(png).decode("ascii")
    chunks = "\r\n".join(raw[i : i + 76] for i in range(0, len(raw), 76))
    return f"data:image/png;base64,{chunks}"


def _build(path: Path, *, seed: int) -> tuple[int, int]:
    rng = random.Random(seed)
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(
            """
            CREATE TABLE cadastro_documentos (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                foto_documento BLOB,
                foto_b64 TEXT,
                anexo BLOB,
                observacao TEXT
            );
            CREATE TABLE controle_negativo (
                id INTEGER PRIMARY KEY,
                hash_blob BLOB,
                token_b64 TEXT,
                hex_img TEXT
            );
            """
        )
        png = _png_bytes()
        pdf = _pdf_bytes()
        rows = 6
        for i in range(1, rows + 1):
            cpf = _synthetic_cpf(rng)
            jpeg = _jpeg_bytes(rng, cpf)
            conn.execute(
                """
                INSERT INTO cadastro_documentos
                (id, nome, foto_documento, foto_b64, anexo, observacao)
                VALUES (?,?,?,?,?,?)
                """,
                (
                    i,
                    f"Pessoa Sintetica {i:02d}",
                    jpeg,
                    _b64_data_uri_png(png),
                    pdf,
                    "Observacao sem midia",
                ),
            )
            noise = bytes(rng.randint(0, 255) for _ in range(64))
            token = base64.b64encode(
                bytes(rng.randint(0, 255) for _ in range(80))
            ).decode("ascii")[:150]
            hex_jpeg = ("ffd8ffe0" + "00" * 50)[:120]
            conn.execute(
                "INSERT INTO controle_negativo VALUES (?,?,?,?)",
                (i, noise, token, hex_jpeg),
            )
        conn.commit()
    finally:
        conn.close()
    return 2, rows * 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    out = args.output
    if out.exists() and not args.force:
        print(f"refusing to overwrite {out}", file=sys.stderr)
        return 2
    tables, nrow = _build(out, seed=args.seed)
    print(f"wrote {out} tables={tables} rows={nrow}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
