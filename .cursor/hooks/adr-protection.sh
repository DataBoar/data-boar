#!/bin/sh
# beforeShellExecution hook — ADR file protection
# G0·S — agent safety hardening 2026-05-21
COMMAND="$*"
if echo "$COMMAND" | grep -qE "git (add|commit|stage)"; then
  STAGED=$(git diff --cached --name-only 2>/dev/null | grep "docs/adr/ADR-.*\.md" | head -1)
  if [ -n "$STAGED" ]; then
    echo "BLOCKED [G0·S]: staging/commit includes ADR file: $STAGED"
    echo "ADR modification requires explicit operator authorization (ADR-0056)."
    exit 1
  fi
fi
exit 0
