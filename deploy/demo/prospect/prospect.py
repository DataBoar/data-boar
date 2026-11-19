#!/usr/bin/env python3
"""prospect-up/down: ephemeral per-prospect Data Boar pod in the dashboard slot (#2280).

Design: ``docs/desenho/2280.1.md``. Host-only Linux script, standard library only
(Python 3.11+), installed by the ``demo_prospect`` role under ``~/demo/prospect/bin``.
Subcommands: ``up``, ``down``, ``list``, ``reap``, ``restore-slot``, ``teardown``.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_LEFTOVERS = 3
EXIT_BUSY = 4
EXIT_PREREQ = 5
EXIT_PROXY = 6
EXIT_UNHEALTHY = 7
EXIT_SLOT = 8


class CliError(Exception):
    """A one-line error for stderr with its exit code."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def validate_slug(slug: str, reserved: Iterable[str] = ()) -> str:
    raise NotImplementedError


def parse_ttl(text: str) -> int:
    raise NotImplementedError


def load_inventory(path: Path) -> dict[str, Any]:
    raise NotImplementedError


def render_ttl_dropin(ttl_s: int) -> str:
    raise NotImplementedError


def render_pod_env(api_key: str, inventory: dict[str, Any]) -> str:
    raise NotImplementedError


def render_state_env(port: int, corpus_dir: str, extras_dir: str) -> str:
    raise NotImplementedError


def render_config(slug: str, inventory: dict[str, Any]) -> str:
    raise NotImplementedError


def render_site(
    *,
    slug: str,
    domain: str,
    proxy_port: int,
    pod_port: int,
    tls_line: str,
    bcrypt_hash: str,
    api_key: str,
    caddy_dir_in_proxy: str,
) -> str:
    raise NotImplementedError


def openssl_argv(slug: str, directory: Path) -> list[str]:
    raise NotImplementedError


class Runner:
    """Runs a command without a shell: ``run(argv, input=None) -> (rc, stdout, stderr)``."""

    def run(self, argv: list[str], input: str | None = None) -> tuple[int, str, str]:
        raise NotImplementedError


class AdminClient:
    """``POST /load`` of a Caddyfile on the proxy admin unix socket."""

    def __init__(self, socket_path: str) -> None:
        self.socket_path = socket_path

    def load(self, text: str) -> int:
        raise NotImplementedError


class HealthProbe:
    """Loopback HTTPS probes: ``/status`` of the pod or the slot, and the route check."""

    def status(
        self, url: str, key: str | None = None, cafile: str | None = None
    ) -> dict | None:
        raise NotImplementedError

    def route_status(self, host: str, port: int) -> int:
        raise NotImplementedError


class Alerter:
    """journal ``err`` line plus the operator's optional notifier."""

    def __init__(self, runner: Runner, alert_cmd: str | None = None) -> None:
        self.runner = runner
        self.alert_cmd = alert_cmd

    def emit(self, msg: str) -> None:
        raise NotImplementedError

    def info(self, msg: str) -> None:
        raise NotImplementedError


@dataclass
class Context:
    """Every side effect of the CLI goes through these seams (design, section 15)."""

    runner: Any
    admin: Any
    probe: Any
    alerter: Any
    clock: Callable[[], datetime]
    sleep: Callable[[float], None]
    meminfo: Callable[[], int]
    port_busy: Callable[[int], bool]
    which: Callable[[str], str | None]
    runtime_dir: Path
    systemd_runtime_dir: Path
    quadlet_dir: Path
    home: Path
    inventory_path: Path | None = None
    lock_timeout_up: float = 30.0
    lock_timeout_reap: float = 60.0
    out: TextIO = field(default_factory=lambda: sys.stdout)
    err: TextIO = field(default_factory=lambda: sys.stderr)


def main(argv: list[str] | None = None, ctx: Context | None = None) -> int:
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
