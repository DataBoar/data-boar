---
name: operator-help-sync
description: >-
  When adding CLI flags, dashboard toggles, or /help text, sync operator-facing
  help surfaces and tests/operator_help_sync_manifest.py. Use for feature work
  that changes how operators run or configure the app from CLI, web, or man.
---

# Operator help sync

## Goal

Keep **short** operator copy consistent across:

- `main.py --help` (argparse)
- GET `/help` (`api/templates/help.html`)
- `docs/data_boar.1` (and §5 when config keys change)
- Optionally `docs/USAGE.md` / `USAGE.pt_BR.md` for full reference

Do **not** duplicate the whole USAGE guide in `/help` or epilog — only enough that operators are not misled and CI can detect drift.

## Steps

1. Implement the feature (flag, checkbox, API field).
1. Edit **`tests/operator_help_sync_manifest.py`**: add an `OperatorHelpMarker` row with substrings that must appear on each surface (`None` = skip that surface).
1. Update **`main.py`**, **`help.html`**, man pages, and USAGE as needed.
1. Run **`uv run pytest tests/test_operator_help_sync.py -v`** until green.
1. For a **post-realignment** gate, follow **“Next verification pass”** in **`docs/OPERATOR_HELP_AUDIT.md`** (then walk the **Follow-ups** checkboxes: OpenAPI vs `/scan`, README **`--host`**, `/help` after new flags).
1. Mention **`docs/OPERATOR_HELP_AUDIT.md`** changelog if the change is notable.

## Files

| File                                   | Role                                   |
| ------                                 | ------                                 |
| `tests/operator_help_sync_manifest.py` | Contract data (single place to extend) |
| `tests/test_operator_help_sync.py`     | Asserts CLI + `/help` + man §1         |
| `docs/OPERATOR_HELP_AUDIT.md`          | Human checklist + changelog            |

## Rule

Repository rule: **`.cursor/rules/operator-help-sync.mdc`** (applies when editing the globs listed there).
