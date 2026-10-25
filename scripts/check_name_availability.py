"""
One-off script: check PyPI and (optionally) web for chosen name availability.
Used to complete Logo and naming plan step 5. Safe: timeouts, no crashes.
"""

from __future__ import annotations

import json
import ssl
import urllib.request
import sys

TIMEOUT = 15
USER_AGENT = "DataBoar-NameCheck/1.0"


def safe_get(url: str, timeout: int = TIMEOUT) -> tuple[int | None, str | None]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2  # S4423: enforce strong TLS
        with urllib.request.urlopen(  # nosec B310
            req, timeout=timeout, context=ctx
        ) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)


def main() -> int:
    names_to_check = ["data-boar", "data_boar"]
    results = []
    for name in names_to_check:
        url = f"https://pypi.org/pypi/{name}/json"
        code, body = safe_get(url)
        if code == 200:
            try:
                data = json.loads(body) if body else {}
                info = data.get("info", {})
                summary = (info.get("summary") or "(no summary)")[:60]
                results.append(f"PyPI {name}: TAKEN - {summary}")
            except Exception:
                results.append(f"PyPI {name}: TAKEN (code 200)")
        elif code == 404:
            results.append(f"PyPI {name}: AVAILABLE (404)")
        else:
            results.append(f"PyPI {name}: check failed - code={code} err={body}")
    for line in results:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
