# Licensing — Community (BSD-3) vs Pro (`pro/`)

**Why this file exists.** The repository-root [LICENSE](LICENSE) is the official **BSD 3-Clause** text for the open-core (Community) tree. Separately, the commercial Pro-tier modules under [`pro/`](pro/) are **not** covered by that grant. This document states that boundary in plain language so operators, redistributors, and counsel do not treat a single root license file as applying to every path in the clone.

## Community (open-core)

- **License:** BSD 3-Clause — see [LICENSE](LICENSE) (English text is authoritative). Convenience translation: [LICENSE.pt_BR.md](LICENSE.pt_BR.md).
- **Scope:** Everything in this repository **outside** the `pro/` directory, unless a path carries its own explicit notice.

## Pro tier (`pro/`)

- **License:** Proprietary / all rights reserved — see [`pro/LICENSE`](pro/LICENSE).
- **Scope:** All source under `pro/` (including per-file copyright headers that point back to `pro/LICENSE`).
- **Commercial model:** The final commercial license terms for `pro/` remain under active definition (tracked in issue [#1576](https://github.com/DataBoar/data-boar/issues/1576) and related planning docs). Until ratified, the default in `pro/LICENSE` governs.

## Runtime license-key gate vs copyright boundary

Data Boar may enforce Pro features at **runtime** (license key / beacon gating). That mechanism is an **enforcement layer on top of** the licensing boundary described here. It is **not** a substitute for the copyright and license notices: receiving or running a build that includes `pro/` does not expand the BSD-3 grant into `pro/`, and stripping or bypassing the runtime gate does not create a copyright license to copy, modify, or redistribute `pro/` source.

## Non-retroactivity

This notice and the `pro/LICENSE` file document the intended boundary going forward. They do **not** by themselves rewrite history for parties who already obtained a copy of `pro/` source under prior repository packaging while the tree was presented under a single package-wide BSD-3 classifier. Counsel should evaluate prior distributions on the facts of each receipt; this file is not legal advice.

## Contact

Questions about Community or Pro licensing: see contact information in [README.md](README.md) and [SECURITY.md](SECURITY.md).
