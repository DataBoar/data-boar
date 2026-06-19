# LAB Lessons Learned — 2026-06-18 (frozen snapshot)

**Scope:** Release-gate acceptance attempt for the `1.7.4-rc` → `1.7.4` promotion (gate #406),
run from the **temporary primary Linux dev workstation** (see [ADR 0068](../../adr/ADR-0068-primary-linux-dev-workstation-temporary.md))
after the former Windows primary went offline for repair.

**Verdict (short):** **Gate NOT accepted.** Finding-parity was never measured — the scan did
not start on any node. The completão was blocked **before** any audit by two structural,
infra-level issues (not product defects): a **Windows-bound orchestrator** that cannot run on
the only available host, and **persistent per-node provisioning gaps** that recur across the
fleet. Gate stays **OPEN** (operator decision); **no** version bump.

## Root causes

### 1. Orchestrator is Windows-bound

The canonical completão orchestrator drives every remote step through `cmd.exe`. On the
Linux primary it starts, completes the inventory preflight, then dies at the first remote
call (`cmd.exe` not found). The regente host it assumes (the Windows primary) is offline.
Net: **no working orchestrated path exists today** — a direct consequence of the ADR-0068
migration not yet covering the completão tooling on Linux.

### 2. Recurring per-node provisioning gaps (signal, not noise)

Read-only preflight probes (non-interactive SSH) reproduced the **same failures across
multiple node classes**:

| Node class | `uv` on non-interactive SSH | Native fast-filter extension | Gap |
| ---------- | --------------------------- | ---------------------------- | --- |
| ARM SBC | missing from `PATH` | absent | no published ARM wheel; `uv` missing from non-interactive `PATH` (so it can't fetch the maturin build-backend or build); on-host Rust not probed this session |
| musl edge node | present (system path) | wheel built, not installed in `.venv` | `uv run` prune behavior drops the local wheel; ML sdists rebuild on sync |
| minimal-coreutils node | present | absent | distro build deps; busybox-style coreutils |
| glibc x86_64 laptop | missing from `PATH` | previously compiled | `PATH` only |
| primary-dev loopback | missing from `PATH` (interactive OK) | n/a | `PATH`; **protected — never an align target** |

Evidence-based correction (operator proofs, same session): the musl edge node **does**
build the native fast-filter (a `musllinux` wheel and on-host Rust toolchain are present).
Its real gap is the wheel **not being installed into the project `.venv`** — `uv run`
re-resolves and prunes the local wheel, and ML sdists (no musl wheels) try to rebuild on
that sync. So "no musl wheel / no Rust" was a **false** first read. The genuine multi-arch
gap is the **ARM SBC** (no ARM wheel published, Build-Once is x86_64-glibc), where the
"30x faster import" sanity stays unverified and parity would rely on the pure-Python
fallback — which still needs `uv` on the non-interactive `PATH`.

## Central lesson — aggregate failures into a verdict

The `uv`-PATH gap and the fast-filter build matrix were **already a tracked follow-up from
the 2026-05-13 session** ("native extension compiled on one node only"), and they returned
because they were never propagated across the fleet. An auditor smoke that sees the **same
failure on N nodes** is reporting **"lab not provisioned"** — that is **signal aggregation
that should escalate and abort with a diagnosis**, not per-node noise to retry. Governance
held (the canonical dev clone was untouched), but the diagnostic loop wasted operator time
by re-attempting the run instead of stopping on the recurring signal.

## #406 pending items — actual state

All **UNVERIFIED** this session (the run died at the orchestrator before reaching handlers):
`.7z`/py7zr support, the ensure-script `$HOME` bug, per-handler SSH `ConnectTimeout`, and the
`--bench-config` argument on baremetal + docker handlers.

## Follow-ups → plans

Promoted to **[`docs/plans/PLANS_TODO.md`](../../plans/PLANS_TODO.md)**:

- Cross-platform completão runner (replace `cmd.exe` core with a Linux-capable transport).
- Fleet-wide `uv` non-interactive `PATH` provisioning.
- Native fast-filter build matrix (multi-arch / musl) — propagate the 2026-05-13 follow-up to **all** nodes.
- Auditor smoke: escalate repeated identical failures across nodes as a single "lab-not-provisioned" verdict + abort.
- `protect_canonical` guard load-bearing in the Maestro sync path (covers both primary dev hosts).

Private narrative (hostnames/LAN): `docs/private/homelab/COMPLETAO_SESSION_2026-06-18.md` —
public summary only here.
