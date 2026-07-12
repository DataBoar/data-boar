"""
Redact secret values in config for safe display (GET /config) and merge on save
so placeholders do not overwrite real secrets (POST /config).

Used by Phase A of the secrets plan: UI never shows or writes plain secrets.
"""

from __future__ import annotations

import copy
import re
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

# Placeholder shown in UI instead of secret values; also used to detect "do not overwrite" on save
REDACTED_PLACEHOLDER = "# REDACTED - set via env or vault"

# Substrings in key names that indicate secret values (redacted for display; preserved on save
# when submitted value is placeholder). Exact match alone misses compound keys such as
# telegram_bot_token or file_passwords.
_SECRET_SUBSTRINGS = frozenset(
    {
        "password",
        "pass",
        "api_key",
        "token",
        "secret",
        "private_key",
        "credential",
        "bearer",
    }
)

# Keys that contain a substring above but are not secrets (e.g. OAuth token_url is a URL).
_SECRET_KEY_ALLOWLIST = frozenset({"token_url"})
_INLINE_SECRET_PLACEHOLDER = "***"
_URL_QUERY_SECRET_SUBSTRINGS = frozenset(
    {"password", "pwd", "secret", "token", "api_key", "apikey", "pass"}
)
_GENERIC_KV_SECRET_RE = re.compile(
    r"(?i)(\b(?:password|pwd|secret|token|api_key|apikey|pass)\b\s*[:=]\s*)([^;\s,&]+)"
)


def _is_secret_key(key: str) -> bool:
    k = key.lower()
    if k in _SECRET_KEY_ALLOWLIST:
        return False
    return any(sub in k for sub in _SECRET_SUBSTRINGS)


def _is_sensitive_query_key(key: str) -> bool:
    k = key.strip().lower()
    return any(sub in k for sub in _URL_QUERY_SECRET_SUBSTRINGS)


def _redact_url_like_string(value: str) -> str:
    if "://" not in value:
        return value
    split = urlsplit(value)
    if not split.scheme:
        return value
    out_netloc = split.netloc
    if split.username is not None and split.password is not None:
        username = quote(split.username, safe="")
        host = split.hostname or ""
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        port_part = f":{split.port}" if split.port is not None else ""
        out_netloc = f"{username}:{_INLINE_SECRET_PLACEHOLDER}@{host}{port_part}"
    pairs = parse_qsl(split.query, keep_blank_values=True)
    if pairs:
        redacted_pairs = [
            (k, _INLINE_SECRET_PLACEHOLDER if _is_sensitive_query_key(k) else v)
            for k, v in pairs
        ]
        out_query = urlencode(redacted_pairs, doseq=True)
    else:
        out_query = split.query
    return urlunsplit((split.scheme, out_netloc, split.path, out_query, split.fragment))


def _redact_generic_key_value_pairs(value: str) -> str:
    return _GENERIC_KV_SECRET_RE.sub(
        lambda m: f"{m.group(1)}{_INLINE_SECRET_PLACEHOLDER}", value
    )


def _redact_inline_string_secrets(value: str) -> str:
    url_redacted = _redact_url_like_string(value)
    return _redact_generic_key_value_pairs(url_redacted)


def _redact_value(val: Any) -> Any:
    if isinstance(val, str) and val.strip() and val.strip() != REDACTED_PLACEHOLDER:
        return REDACTED_PLACEHOLDER
    return val


def _redact_secret_subtree(obj: Any) -> Any:
    """Redact all non-empty string leaves under a secret-named key (e.g. file_passwords map)."""
    if isinstance(obj, dict):
        return {k: _redact_secret_subtree(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact_secret_subtree(i) for i in obj]
    return _redact_value(obj)


def _walk_redact(obj: Any, in_api: bool = False) -> Any:
    """Deep-copy and replace secret values with placeholder. in_api: we're under api key."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(k, str) and _is_secret_key(k):
                if isinstance(v, str) and (v.strip() or not in_api):
                    out[k] = REDACTED_PLACEHOLDER
                elif isinstance(v, (dict, list)):
                    out[k] = _redact_secret_subtree(v)
                else:
                    out[k] = copy.deepcopy(v)
            else:
                if isinstance(v, str):
                    out[k] = _redact_inline_string_secrets(v)
                else:
                    out[k] = _walk_redact(
                        v, in_api=(in_api or (isinstance(k, str) and k == "api"))
                    )
        return out
    if isinstance(obj, list):
        return [_walk_redact(i, in_api) for i in obj]
    return copy.deepcopy(obj)


def redact_config_for_display(data: dict[str, Any]) -> dict[str, Any]:
    """
    Return a deep copy of the config with secret values replaced by REDACTED_PLACEHOLDER.
    Use for GET /config so the UI never displays or transmits plain secrets.
    """
    return _walk_redact(data, in_api=False)


def _walk_merge(
    submitted: Any,
    current: Any,
    path: str = "",
) -> Any:
    """
    Merge submitted config into current; for secret keys, if submitted value is
    placeholder or empty, keep current value so we don't overwrite secrets on save.
    """
    if current is None:
        return submitted
    leaf = path.split(".")[-1].split("[")[0] if path else ""
    if leaf and _is_secret_key(leaf):
        sub_val = submitted if isinstance(submitted, str) else ""
        if isinstance(sub_val, str) and (
            not sub_val.strip() or sub_val.strip() == REDACTED_PLACEHOLDER
        ):
            return current
        return submitted

    if isinstance(submitted, str) and isinstance(current, str):
        if submitted.strip() == REDACTED_PLACEHOLDER:
            return current
        if submitted == _redact_inline_string_secrets(current):
            return current

    if isinstance(submitted, dict) and isinstance(current, dict):
        out = dict(current)
        for k, v in submitted.items():
            sub_path = f"{path}.{k}" if path else k
            if isinstance(k, str) and _is_secret_key(k):
                if isinstance(v, str) and (
                    not v.strip() or v.strip() == REDACTED_PLACEHOLDER
                ):
                    if k in current:
                        out[k] = current[k]
                    else:
                        out[k] = v
                else:
                    out[k] = v
            else:
                out[k] = _walk_merge(
                    v,
                    current.get(k) if isinstance(current, dict) else None,
                    sub_path,
                )
        return out
    if isinstance(submitted, list) and isinstance(current, list):
        return [
            _walk_merge(
                submitted[i] if i < len(submitted) else None,
                current[i] if i < len(current) else None,
                f"{path}[{i}]",
            )
            for i in range(max(len(submitted), len(current)))
        ]
    return submitted if submitted is not None else current


def merge_config_on_save(
    submitted_data: dict[str, Any],
    current_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Merge submitted config (from POST /config) with current config (from file).
    For secret keys, if the submitted value is the placeholder or empty, keep
    the current value so saving the form does not overwrite real secrets.
    """
    return _walk_merge(submitted_data, current_data)
