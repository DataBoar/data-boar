"""Shared man page install paths for wheel and native packages (#2163)."""

from __future__ import annotations

MAN1_CANONICAL = "data-boar.1"
MAN5_CANONICAL = "data-boar.5"
MAN7_CANONICAL = "data-boar.7"

MAN1_LEGACY_ALIASES: tuple[str, ...] = ("data_boar.1", "lgpd_crawler.1")
MAN5_LEGACY_ALIASES: tuple[str, ...] = ("data_boar.5", "lgpd_crawler.5")
MAN7_LEGACY_ALIASES: tuple[str, ...] = ("data_boar.7", "lgpd_crawler.7")

WHEEL_ALIAS_ROOT = "packaging/wheel-man-aliases"


def nfpm_man_symlink_contents() -> list[dict[str, str]]:
    """nfpm ``type: symlink`` entries for legacy man names (#2163)."""
    out: list[dict[str, str]] = []
    for alias in MAN1_LEGACY_ALIASES:
        out.append(
            {
                "dst": f"/usr/share/man/man1/{alias}",
                "type": "symlink",
                "src": f"/usr/share/man/man1/{MAN1_CANONICAL}",
            }
        )
    for alias in MAN5_LEGACY_ALIASES:
        out.append(
            {
                "dst": f"/usr/share/man/man5/{alias}",
                "type": "symlink",
                "src": f"/usr/share/man/man5/{MAN5_CANONICAL}",
            }
        )
    for alias in MAN7_LEGACY_ALIASES:
        out.append(
            {
                "dst": f"/usr/share/man/man7/{alias}",
                "type": "symlink",
                "src": f"/usr/share/man/man7/{MAN7_CANONICAL}",
            }
        )
    return out


def void_man_alias_install_lines() -> str:
    """Shell lines appended inside ``do_install`` after ``vman`` calls."""
    lines: list[str] = []
    for alias in MAN1_LEGACY_ALIASES:
        lines.append(
            f'\tln -sf {MAN1_CANONICAL} "${{DESTDIR}}/usr/share/man/man1/{alias}"'
        )
    for alias in MAN5_LEGACY_ALIASES:
        lines.append(
            f'\tln -sf {MAN5_CANONICAL} "${{DESTDIR}}/usr/share/man/man5/{alias}"'
        )
    for alias in MAN7_LEGACY_ALIASES:
        lines.append(
            f'\tln -sf {MAN7_CANONICAL} "${{DESTDIR}}/usr/share/man/man7/{alias}"'
        )
    return "\n".join(lines) + ("\n" if lines else "")


def wheel_shared_man_paths() -> dict[str, str]:
    """Hatch ``shared-data`` destinations for legacy man aliases in the wheel."""
    mapping: dict[str, str] = {
        "docs/data_boar.1": "share/man/man1/data-boar.1",
        "docs/data_boar.5": "share/man/man5/data-boar.5",
        "docs/data_boar.7": "share/man/man7/data-boar.7",
    }
    for alias in MAN1_LEGACY_ALIASES:
        mapping[f"{WHEEL_ALIAS_ROOT}/man1/{alias}"] = f"share/man/man1/{alias}"
    for alias in MAN5_LEGACY_ALIASES:
        mapping[f"{WHEEL_ALIAS_ROOT}/man5/{alias}"] = f"share/man/man5/{alias}"
    for alias in MAN7_LEGACY_ALIASES:
        mapping[f"{WHEEL_ALIAS_ROOT}/man7/{alias}"] = f"share/man/man7/{alias}"
    return mapping
