"""
Generate favicon.ico from the Data Boar mascot (dark-tuned translucent PNG).

Uses Pillow to resize the mascot to 16×16 and 32×32 and save as a multi-size ICO.
Run from the project root, e.g.:

    uv run python scripts/build_favicon.py
    # or
    python scripts/build_favicon.py

Output: api/static/favicon.ico

To use a different source image (e.g. a new PNG you added under api/static/mascot/),
edit SRC_NAME below or pass the path as the first argument (future enhancement).
"""

from pathlib import Path

from PIL import Image


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    src = (
        repo_root
        / "api"
        / "static"
        / "mascot"
        / "data_boar_mascote_color_translucent_not_zombie.png"
    )
    out = repo_root / "api" / "static" / "favicon.ico"

    if not src.exists():
        raise SystemExit(f"Source image not found: {src}")

    img = Image.open(src)
    # Preserve alpha for transparency in ICO
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Standard favicon sizes; Pillow embeds all into one .ico
    sizes = [(16, 16), (32, 32)]
    img.save(out, format="ICO", sizes=sizes)
    print(f"Wrote {out} (sizes: {sizes})")


if __name__ == "__main__":
    main()
