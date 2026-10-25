# PLAN: CLI `--demo` subcommand (#1113)

**Status:** In progress
**Issue:** [#1113](https://github.com/DataBoar/data-boar/issues/1113)

## Goal

Turnkey `data-boar --demo` for Windows operators (Estela): zero-config synthetic corpus, initial scan, loopback dashboard on port 8088.

## Scope

| Item | Status |
| ---- | ------ |
| `core/demo/synthetic_corpus.py` (installable generator) | Done |
| `core/demo/runtime.py` (workspace + atexit) | Done |
| `main.py --demo` | Done |
| `scripts/demo.sh` thin wrapper | Done |
| Excel praise sheet sanitization | Done |
| Tests (`test_cli_demo`, excel sheet) | Done |
| QUICKSTART / README / operator help | Done |

## Steering (locked)

- **Cleanup:** single owner — `atexit` for `main.py --demo`; bash `trap` + `register_cleanup=False` for `demo.sh --headless`.
- **Loopback:** `--demo` forces `127.0.0.1` bind.
- **Excel:** `_SHEET_PRAISE_CONTROLS` sanitizes `/` in sheet title; headless test expects `returncode == 0`.

## Follow-up

- PyPI publish after PR merge (operator).
- #1112 Windows quickstart docs alignment after land.
