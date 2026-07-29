#!/bin/sh
# run-config-matrix.sh — run LAYER 1 (files) and extract COMPARABLE output. (#1368)
#
# Comparable = two measures, not one:
#   (a) findings by sensitivity
#   (b) scan_failures BY REASON  <- the axis post-GA fixes attack
# Absence of error is NOT a result. The result is the failure staying VISIBLE when it should.
#
# Usage:  sh run-config-matrix.sh [work-directory]
# No argument → ./matrix-run. No credentials required.
set -u
WORK="${1:-$PWD/matrix-run}"
HERE=$(cd "$(dirname "$0")" && pwd)
REPO="${DATABOAR_REPO:-$(cd "$HERE/../.." && pwd)}"

echo "########## corner: $(uname -s)/$(uname -m) · $(grep -m1 '^PRETTY_NAME=' /etc/os-release 2>/dev/null | cut -d'"' -f2) ##########"
command -v data-boar >/dev/null 2>&1 || { echo "FATAL: data-boar not on PATH"; exit 1; }
data-boar --version

mkdir -p "$WORK/corpus" "$WORK/out"
cd "$WORK" || exit 1

echo; echo "=== [1/4] corpus: fixtures from THIS repo (origin/main) ==="
if [ -d corpus/compressed ]; then
  echo "  already present, reusing"
else
  # git archive reads from ORIGIN (published truth) without touching the working tree
  git -C "$REPO" archive origin/main tests/data | tar -x -C corpus --strip-components=2 \
    || { echo "FATAL: could not extract tests/data from origin/main"; exit 1; }
fi
echo "  compressed: $(ls corpus/compressed 2>/dev/null | wc -l) files"
ls -la corpus/compressed 2>/dev/null | awk 'NR>1 && NF>=9 {printf "    %-24s %s bytes\n", $9, $5}'
echo "  NOTE: sample3.tgz and sample4.tar.bz2 have the SAME bytes; the .bz2 extension LIES (#1354 bait)"

cp "$HERE/config-files.yaml" ./config.yaml

echo; echo "=== [2/4] scan ==="; date
# --demo does NOT return (starts API and stays in LISTEN); a normal --config scan returns.
# --scan-compressed and --content-type-check: the #1354 pair.
data-boar --config ./config.yaml --scan-compressed --content-type-check 2>&1 | tail -12
date

echo; echo "=== [3/4] findings ==="
S=$(ls -1 out/POC_SUMMARY_*.md 2>/dev/null | head -1)
if [ -n "$S" ]; then
  grep -o "[0-9]* achados em base · [0-9]* em arquivos · [0-9]* falhas" "$S" | head -1 | sed 's/^/  /'
  grep -E "^### (Alta|Média|Baixa)" -A1 "$S" | grep -vE "^--|^$" | sed 's/^/  /'
else
  echo "  NO POC_SUMMARY in out/ — see scan output above"
fi

echo; echo "=== [4/4] scan_failures BY REASON (what the fixes make visible) ==="
python3 - <<'PY'
import sqlite3, os, sys
db = "out/matrix.db"
if not os.path.exists(db):
    print("  no out/matrix.db"); sys.exit(0)
c = sqlite3.connect(db)
try:
    rows = c.execute(
        "SELECT reason, target_name, COUNT(*) FROM scan_failures GROUP BY reason, target_name ORDER BY 3 DESC"
    ).fetchall()
except sqlite3.OperationalError as e:
    print("  scan_failures table missing:", e); sys.exit(0)
if not rows:
    print("  NO failures recorded")
    print("  WARNING: with sample4.tar.bz2 in corpus, EXPECT >=1 `archive_type_mismatch` (#1354 Part A).")
    print("     Zero rows here = fix missing from this artifact, or path not exercised.")
else:
    for reason, target, n in rows:
        print("  %-28s %-24s %d" % (reason, target or "-", n))
    if not any(r[0] == "archive_type_mismatch" for r in rows):
        print("  WARNING: no `archive_type_mismatch` — check whether #1354 Part A is in this artifact")
PY
echo; echo "CONFIG_MATRIX_DONE"; date
