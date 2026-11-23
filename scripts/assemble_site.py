from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def assemble(generated: Path, book_html: Path, site: Path) -> None:
    if not book_html.is_dir():
        raise FileNotFoundError(f"Jupyter Book HTML output not found: {book_html}")
    if not (generated / "storymap" / "data" / "storymap.json").is_file():
        raise FileNotFoundError(f"Generated StoryMap data not found: {generated}")

    site.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "site_index.html", site / "index.html")
    (site / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copytree(ROOT / "assets", site / "assets", dirs_exist_ok=True)
    shutil.copytree(ROOT / "storymap", site / "storymap", dirs_exist_ok=True)
    shutil.copytree(generated / "storymap", site / "storymap", dirs_exist_ok=True)
    shutil.copytree(book_html, site / "book", dirs_exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble the Book and StoryMap into a Pages site.")
    parser.add_argument("--generated", type=Path, default=ROOT / "_build" / "generated")
    parser.add_argument("--book-html", type=Path, default=ROOT / "_build" / "jbook" / "_build" / "html")
    parser.add_argument("--site", type=Path, default=ROOT / "_build" / "site")
    args = parser.parse_args()
    assemble(args.generated, args.book_html, args.site)


if __name__ == "__main__":
    main()
