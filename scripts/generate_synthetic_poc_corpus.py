#!/usr/bin/env python3
"""Thin CLI wrapper — canonical implementation is ``core.demo.synthetic_corpus``."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.demo.synthetic_corpus import main

if __name__ == "__main__":
    main()
