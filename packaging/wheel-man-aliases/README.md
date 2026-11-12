# Wheel man page legacy aliases

Symlinks in `man1/`, `man5/` and `man7/` point at `docs/data_boar.{1,5,7}` so Hatch can ship
`data_boar` and `lgpd_crawler` man names in the wheel without duplicating troff.
Paths and nfpm symlinks are defined in `core/man_page_packaging.py` (#2163).
