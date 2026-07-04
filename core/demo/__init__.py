"""Installable demo corpus and workspace helpers (#1113)."""

from core.demo.runtime import (
    prepare_demo_workspace,
    print_demo_banner,
    register_demo_cleanup,
)
from core.demo.synthetic_corpus import (
    ALL_SCENARIOS,
    generate_corpus,
    main as generate_corpus_cli,
)

__all__ = [
    "ALL_SCENARIOS",
    "generate_corpus",
    "generate_corpus_cli",
    "prepare_demo_workspace",
    "print_demo_banner",
    "register_demo_cleanup",
]
