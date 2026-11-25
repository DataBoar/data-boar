"""Run a child process on a real pseudo-terminal for passphrase prompt tests (#2239).

``getpass`` opens ``/dev/tty``, so the only honest way to test "the passphrase
comes only from the terminal" is a child that owns a controlling terminal.
``pty.fork()`` gives it one. The parent waits for the prompt before typing,
because ``getpass`` flushes pending input when it switches echo off.

POSIX only: callers skip with ``PTY_SKIP_REASON`` where ``pty`` is missing.
"""

from __future__ import annotations

import os
import select
import signal
import sys
import time
from dataclasses import dataclass

PTY_AVAILABLE = sys.platform != "win32"
PTY_SKIP_REASON = "pty unavailable on this platform"


@dataclass(frozen=True)
class TtyResult:
    exit_code: int
    output: str
    prompted: bool
    timed_out: bool


def env_without_ci(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Child env without ``CI``: with ``CI`` set the scripts treat stdin as non-interactive."""
    env = {k: v for k, v in os.environ.items() if k != "CI"}
    if extra:
        env.update(extra)
    return env


def run_under_pty(
    argv: list[str],
    *,
    env: dict[str, str],
    cwd: str,
    prompt_marker: bytes,
    typed: str | None,
    timeout: float = 60.0,
) -> TtyResult:
    """Run ``argv`` on a pty; type ``typed`` + newline once ``prompt_marker`` shows up.

    ``typed=None`` never types: a child that prompts then blocks until the
    deadline, and the result says ``timed_out=True``.
    """
    if not PTY_AVAILABLE:
        raise RuntimeError(PTY_SKIP_REASON)
    import pty  # POSIX only; imported here so Windows can still collect the tests

    pid, fd = pty.fork()
    if pid == 0:  # child: exec at once, nothing else runs after fork
        try:
            os.chdir(cwd)
            os.execve(argv[0], argv, env)
        finally:
            os._exit(127)
    buf = b""
    prompted = False
    sent = False
    timed_out = False
    deadline = time.monotonic() + timeout
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                os.kill(pid, signal.SIGKILL)
                break
            ready, _, _ = select.select([fd], [], [], min(remaining, 0.5))
            if not ready:
                continue
            try:
                chunk = os.read(fd, 4096)
            except OSError:  # EIO: the child closed the terminal
                break
            if not chunk:
                break
            buf += chunk
            if not prompted and prompt_marker in buf:
                prompted = True
            if prompted and not sent and typed is not None:
                os.write(fd, typed.encode("utf-8") + b"\n")
                sent = True
    finally:
        os.close(fd)
    _, status = os.waitpid(pid, 0)
    return TtyResult(
        exit_code=os.waitstatus_to_exitcode(status),
        output=buf.decode("utf-8", errors="replace"),
        prompted=prompted,
        timed_out=timed_out,
    )
