"""
Dashboard HTML locale: JSON catalogs (no gettext in v1), slug negotiation, and t(key).

See docs/plans/completed/PLAN_DASHBOARD_I18N.md (M-LOCALE-V1).
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from starlette.requests import Request

# BCP 47 tag -> URL path segment (slug). Slugs are lowercase in paths; tags use
# standard BCP 47 casing (e.g. pt-BR) and match api/locales/<tag>.json and config.
LOCALE_SLUG_BY_TAG: dict[str, str] = {"en": "en", "pt-BR": "pt-br"}
LOCALE_TAG_BY_SLUG: dict[str, str] = {v: k for k, v in LOCALE_SLUG_BY_TAG.items()}
VALID_SLUGS = frozenset(LOCALE_TAG_BY_SLUG.keys())

_LOCALES_DIR = Path(__file__).resolve().parent / "locales"


def _flatten_keys(obj: Any, prefix: str = "") -> set[str]:
    """Collect dot-separated keys for parity checks (leaf values must be str)."""
    keys: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, dict):
                keys |= _flatten_keys(v, p)
            elif isinstance(v, str):
                keys.add(p)
            else:
                keys |= _flatten_keys(v, p)
    return keys


@lru_cache(maxsize=8)
def _load_locale_json(tag: str) -> dict[str, Any]:
    path = _LOCALES_DIR / f"{tag}.json"
    if not path.is_file():
        return {}
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    return data if isinstance(data, dict) else {}


def locale_catalog_keys(tag: str) -> set[str]:
    """All translation keys for a locale file (flattened)."""
    return _flatten_keys(_load_locale_json(tag))


def get_fallback_chain(supported_locales: list[str], default_locale: str) -> list[str]:
    """Locales to try after the active tag (missing-key fallback), ending with English."""
    seen: set[str] = set()
    out: list[str] = []
    for t in list(supported_locales) + [default_locale]:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    if "en" not in seen:
        out.append("en")
    return out


def _get_leaf(catalog: dict[str, Any], key: str) -> str | None:
    parts = key.split(".")
    cur: Any = catalog
    for p in parts:
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur if isinstance(cur, str) else None


def translate(
    catalogs: dict[str, dict[str, Any]],
    key: str,
    locale_tag: str,
    fallback_chain: list[str],
) -> str:
    """Return translated string; try active locale, then fallback_chain order."""
    order: list[str] = [locale_tag]
    for t in fallback_chain:
        if t not in order:
            order.append(t)
    for tag in order:
        cat = catalogs.get(tag)
        if cat is None:
            cat = _load_locale_json(tag)
            catalogs[tag] = cat
        val = _get_leaf(cat, key)
        if val is not None:
            return val
    return key


def make_t(
    locale_tag: str,
    supported_locales: list[str],
    default_locale: str,
    catalogs: dict[str, dict[str, Any]] | None = None,
):
    """Build t(key) -> str for Jinja."""
    catalogs = catalogs if catalogs is not None else {}
    chain = get_fallback_chain(supported_locales, default_locale)

    def t(key: str) -> str:
        return translate(catalogs, key, locale_tag, chain)

    return t


def _normalize_tag(tag: str) -> str:
    t = tag.strip().replace("_", "-")
    if t.lower() in ("pt-br", "pt_br"):
        return "pt-BR"
    return t


def parse_accept_language(header: str | None, supported: list[str]) -> str | None:
    """
    Pick first supported locale from Accept-Language (RFC 7231-ish).
    supported tags: e.g. ['en', 'pt-BR'].
    """
    if not header or not supported:
        return None
    supported_norm = {_normalize_tag(x): x for x in supported}
    # Parse "en-US,en;q=0.9,pt-BR;q=0.8"
    entries: list[tuple[str, float]] = []
    for part in header.split(","):
        part = part.strip()
        if not part:
            continue
        if ";" in part:
            lang, _, rest = part.partition(";")
            lang = lang.strip()
            q = 1.0
            if "q=" in rest:
                try:
                    q = float(re.search(r"q=([\d.]+)", rest).group(1))  # type: ignore[union-attr]
                except (AttributeError, ValueError):
                    q = 1.0
        else:
            lang = part
            q = 1.0
        base = lang.split("-")[0].lower() if lang else ""
        entries.append((lang, q))
        if base and base != lang.lower():
            entries.append((base, q * 0.9))
    entries.sort(key=lambda x: -x[1])
    for lang, _ in entries:
        nt = _normalize_tag(lang)
        if nt in supported_norm:
            return supported_norm[nt]
        # en-US -> en
        base = lang.split("-")[0].lower()
        for sup in supported:
            if sup.lower() == base:
                return sup
    return None


def negotiate_locale_tag(request: Request, cfg: dict[str, Any]) -> str:
    """
    (1) Cookie (2) Accept-Language (3) default_locale from config.locale.
    """
    loc = cfg.get("locale") or {}
    supported = list(loc.get("supported_locales") or ["en", "pt-BR"])
    default_locale = str(loc.get("default_locale") or "en")
    if default_locale.lower() in ("pt-br", "pt_br"):
        default_locale = "pt-BR"
    cookie_name = str(loc.get("cookie_name") or "db_locale")
    raw = request.cookies.get(cookie_name)
    if raw:
        nt = _normalize_tag(raw)
        if nt in supported:
            return nt
        if nt.lower() == "en":
            return "en"
    al = request.headers.get("accept-language")
    picked = parse_accept_language(al, supported)
    if picked:
        return picked
    return default_locale if default_locale in supported else supported[0]


def html_base_path(locale_slug: str) -> str:
    """Prefix for dashboard HTML links, e.g. /en or /pt-br."""
    return f"/{locale_slug}".rstrip("/") or "/"


def strip_locale_prefix(path: str) -> tuple[str | None, str]:
    """
    If path starts with /{slug}/..., return (slug, remainder path starting with /).
    Otherwise (None, path).
    """
    segments = [s for s in path.split("/") if s]
    if not segments:
        return None, path
    first = segments[0].lower()
    if first in LOCALE_TAG_BY_SLUG:
        slug = LOCALE_TAG_BY_SLUG[first]
        rest = "/" + "/".join(segments[1:]) if len(segments) > 1 else "/"
        return slug, rest
    return None, path
