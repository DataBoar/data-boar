#!/usr/bin/env python3
"""
Fetch SonarQube/SonarCloud issues for this project and print them in a machine-readable form.

Use this to drive fixes and automation: same issues the Cursor SonarQube extension shows
are available from the server API so tools (or an agent) can read and fix them.

Usage:
  export SONAR_TOKEN=your_token
  # SonarCloud (default): no SONAR_HOST_URL
  # SonarQube Server: export SONAR_HOST_URL=https://sonarqube.example.com
  uv run python scripts/sonar_issues.py
  uv run python scripts/sonar_issues.py --json   # full JSON

Output (default): one line per issue: file:line:rule:severity:message
Exit code: 0 if no issues, 1 if there are issues (so CI or scripts can fail on new issues).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

# Prefer stdlib only so the script runs without extra deps
try:
    import json
    import urllib.error
    import urllib.parse
    import urllib.request
except ImportError:
    sys.exit("Python 3 stdlib required (urllib, json).")

# Project root: parent of scripts/
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


def _load_project_key() -> str:
    """Read sonar.projectKey from sonar-project.properties."""
    prop = REPO_ROOT / "sonar-project.properties"
    if not prop.exists():
        return os.environ.get("SONAR_PROJECT_KEY", "data-boar")
    for line in prop.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("sonar.projectKey=") and "=" in line:
            return line.split("=", 1)[1].strip()
    return os.environ.get("SONAR_PROJECT_KEY", "data-boar")


def _fetch_issues(
    base_url: str,
    token: str,
    project_key: str,
    branch: str | None = None,
) -> dict:
    """GET /api/issues/search and return parsed JSON."""
    params = f"projectKeys={urllib.parse.quote(project_key)}"
    if branch:
        params += f"&branch={urllib.parse.quote(branch)}"
    url = urljoin(base_url.rstrip("/") + "/", f"api/issues/search?{params}")
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        sys.exit(f"Sonar API error {e.code}: {body or e.reason}")
    except urllib.error.URLError as e:
        sys.exit(f"Sonar API request failed: {e.reason}")


def _short_component(component: str, project_key: str) -> str:
    """Return path relative to project (e.g. file path)."""
    # API often returns "project_key:path" or just path
    if ":" in component and component.startswith(project_key):
        return component.split(":", 1)[1]
    return component


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Sonar issues for this project.")
    parser.add_argument("--json", action="store_true", help="Print full JSON response.")
    parser.add_argument(
        "--branch",
        default=os.environ.get("SONAR_BRANCH"),
        help="Branch to filter (optional).",
    )
    args = parser.parse_args()

    token = os.environ.get("SONAR_TOKEN")
    if not token:
        print("Set SONAR_TOKEN to your SonarQube/SonarCloud token.", file=sys.stderr)
        return 2

    base_url = os.environ.get("SONAR_HOST_URL", "https://sonarcloud.io")
    project_key = _load_project_key()

    data = _fetch_issues(base_url, token, project_key, args.branch)
    issues = data.get("issues") or []

    if args.json:
        print(json.dumps(data, indent=2))
        return 1 if issues else 0

    # One line per issue: file:line:rule:severity:message (tab-safe message)
    for i in issues:
        comp = _short_component(i.get("component", ""), project_key)
        line = i.get("line") or 0
        rule = i.get("rule", "")
        severity = i.get("severity", "")
        msg = (i.get("message") or "").replace("\t", " ").replace("\n", " ")
        print(f"{comp}:{line}:{rule}:{severity}:{msg}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
