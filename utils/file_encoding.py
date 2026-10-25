"""
Safe reading of config and pattern files in multiple encodings.

Supports UTF-8 (recommended), UTF-8 with BOM, Windows ANSI (cp1252), and Latin-1
so that configs and compliance samples work in multilingual and legacy environments
without failing in production.

Usage:
- Config file: use read_text_auto_encoding() so the file is read even if saved as ANSI/Latin-1.
- Pattern files (regex_overrides_file, ml_patterns_file, etc.): use read_text_with_encoding()
  with encoding from config (default utf-8); errors="replace" avoids crashes on bad bytes.
"""

from pathlib import Path
from typing import Sequence

# Encodings tried in order for auto-detect (config file).
# utf-8 first; utf-8-sig handles BOM; cp1252 common on Windows; latin_1 accepts any byte.
_DEFAULT_AUTO_ENCODINGS: Sequence[str] = ("utf-8", "utf-8-sig", "cp1252", "latin_1")


def read_text_auto_encoding(
    path: Path | str,
    encodings: Sequence[str] = _DEFAULT_AUTO_ENCODINGS,
    errors_strict: str = "strict",
    errors_fallback: str = "replace",
) -> str:
    """
    Read file trying a list of encodings; use strict for UTF-8 variants, replace for others.

    Use for the main config file so it loads even when saved as ANSI/CP1252/Latin-1.
    Tries encodings in order; first successful decode returns. For utf-8 and utf-8-sig
    uses errors_strict (default "strict"); for cp1252 and latin_1 uses errors_fallback
    (default "replace") so invalid bytes do not raise.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(str(path))
    raw_bytes = path.read_bytes()
    strict_encodings = ("utf-8", "utf-8-sig")
    for enc in encodings:
        try:
            return raw_bytes.decode(
                enc,
                errors=errors_strict if enc in strict_encodings else errors_fallback,
            )
        except (UnicodeDecodeError, LookupError):
            continue
    # Last resort: latin_1 never fails
    return raw_bytes.decode("latin_1", errors="replace")


def read_text_with_encoding(
    path: Path | str,
    encoding: str = "utf-8",
    errors: str = "replace",
) -> str:
    """
    Read file with a specific encoding. Use for pattern files when encoding is set in config.

    Default encoding is utf-8 with errors="replace" so that a single bad byte does not
    break the application in production. For strict validation (e.g. in tests), pass
    errors="strict".
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding=encoding, errors=errors)
