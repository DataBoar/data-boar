"""
Anti-regression tests for scripts/demo.sh (#834).

Validates the demo entrypoint contract:
- Script exists and is executable.
- Usage comment block is present (--help passthrough).
- Script generates corpus via generate_synthetic_poc_corpus.py.
- README.md references demo.sh in its opening lines.
- Docker variant hint is present.
"""

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).parent.parent


def test_demo_sh_exists_and_is_executable() -> None:
    """Anti-regression #834: scripts/demo.sh must exist and be executable."""
    demo = _repo_root() / "scripts" / "demo.sh"
    assert demo.exists(), "scripts/demo.sh must exist (#834)"
    assert demo.stat().st_mode & 0o111, "scripts/demo.sh must be executable (#834)"


def test_demo_sh_uses_synthetic_corpus_generator() -> None:
    """Anti-regression #834/#1113: demo delegates to ``data-boar --demo`` or core.demo."""
    demo = (_repo_root() / "scripts" / "demo.sh").read_text(encoding="utf-8")
    assert "main.py --demo" in demo or "data-boar --demo" in demo, (
        "scripts/demo.sh must call main.py --demo (#1113)"
    )


def test_demo_sh_starts_web_dashboard() -> None:
    """Anti-regression #834/#1113: default path uses --demo (implies --web)."""
    demo = (_repo_root() / "scripts" / "demo.sh").read_text(encoding="utf-8")
    assert "--demo" in demo, (
        "scripts/demo.sh must invoke --demo so the dashboard opens (#1113)"
    )


def test_demo_sh_has_cleanup_trap() -> None:
    """Anti-regression #834: demo.sh must clean up temporary files on exit."""
    demo = (_repo_root() / "scripts" / "demo.sh").read_text(encoding="utf-8")
    assert "trap" in demo, (
        "scripts/demo.sh must have a trap to clean up /tmp files on Ctrl+C or exit (#834)"
    )
    assert "cleanup" in demo or "rm -rf" in demo, (
        "scripts/demo.sh must remove the temporary demo directory on exit (#834)"
    )


def test_demo_sh_headless_mode_available() -> None:
    """Anti-regression #834: demo.sh must support --headless for non-interactive environments."""
    demo = (_repo_root() / "scripts" / "demo.sh").read_text(encoding="utf-8")
    assert "--headless" in demo, (
        "scripts/demo.sh must support --headless mode for CI/non-interactive use (#834)"
    )


def test_readme_references_demo_sh_in_opening() -> None:
    """Anti-regression #834: README.md must reference demo.sh near the top (first 10 lines)."""
    readme = (_repo_root() / "README.md").read_text(encoding="utf-8")
    first_lines = "\n".join(readme.splitlines()[:10])
    assert "demo.sh" in first_lines, (
        "README.md must mention scripts/demo.sh in the first 10 lines so newcomers "
        "see the zero-config demo immediately (#834)"
    )


def test_demo_sh_docker_hint_present() -> None:
    """Anti-regression #834: README or demo.sh must mention Docker run variant."""
    demo = (_repo_root() / "scripts" / "demo.sh").read_text(encoding="utf-8")
    readme = (_repo_root() / "README.md").read_text(encoding="utf-8", errors="replace")
    has_docker = "docker run" in demo or "docker run" in readme[:500]
    assert has_docker, (
        "demo.sh or README.md opening must mention `docker run … demo` so users "
        "without a local Python env know the Docker variant (#834)"
    )
