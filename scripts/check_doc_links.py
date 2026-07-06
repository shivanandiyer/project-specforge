#!/usr/bin/env python3
"""Check that repo-relative markdown links resolve to real files.

This repo is documentation-heavy and cross-links constantly (README's doc map,
the ADR index, the glossary); a rename or move silently breaks those links
without a check like this one.

Usage: check_doc_links.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SKIP_DIRS = {".git", "node_modules"}


def is_checkable(link: str) -> bool:
    return not link.startswith(("http://", "https://", "mailto:", "#"))


def find_broken_links(md_file: Path) -> list[str]:
    errors = []
    text = md_file.read_text(encoding="utf-8")
    for match in LINK_RE.finditer(text):
        link = match.group(1).strip()
        if not is_checkable(link):
            continue
        target, _, _anchor = link.partition("#")
        if not target:
            continue  # pure in-page anchor
        resolved = (md_file.parent / target).resolve()
        if not resolved.exists():
            errors.append(f"{md_file.relative_to(ROOT)}: broken link '{link}' -> {resolved}")
    return errors


def main() -> int:
    md_files = [
        p for p in sorted(ROOT.rglob("*.md"))
        if not SKIP_DIRS & set(p.relative_to(ROOT).parts)
    ]

    errors = [err for md_file in md_files for err in find_broken_links(md_file)]

    if errors:
        print(f"✗ {len(errors)} broken link(s) across {len(md_files)} file(s):\n")
        for err in errors:
            print(f"  {err}")
        return 1

    print(f"✓ all relative links resolve across {len(md_files)} markdown file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
