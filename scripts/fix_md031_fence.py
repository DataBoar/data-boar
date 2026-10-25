"""Fix MD031: ensure blank line before fenced code blocks."""

import sys
from pathlib import Path

FENCE = "```"


def fix_md031(filepath):
    lines = filepath.read_text(encoding="utf-8").splitlines(keepends=True)
    result = []
    fixes = 0
    for i, line in enumerate(lines):
        stripped = line.rstrip("\r\n")
        is_fence = stripped.lstrip().startswith(FENCE)
        prev_blank = (len(result) == 0) or (result[-1].strip() == "")
        if is_fence and not prev_blank:
            result.append("\n")
            fixes += 1
        result.append(line)
    if fixes:
        filepath.write_text("".join(result), encoding="utf-8")
    return fixes


if __name__ == "__main__":
    for p in sys.argv[1:]:
        n = fix_md031(Path(p))
        print(f"{p}: {n} fix(es)")
