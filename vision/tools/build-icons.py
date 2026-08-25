#!/usr/bin/env python3
"""Regenerate assets/icons.html from the two primitive-icons references.

The gallery used to be maintained by hand, so it drifted: it still carried the
ten pre-normalisation icons with their own viewBoxes long after the library was
put on the 24-grid. Generating it means the two cannot disagree — the reference
is the source, the gallery is a view of it.

Only the `<section class="cat">` blocks between the header and the footer are
rewritten; the page's head, styles and copy are left alone.

Usage:
    python3 tools/build-icons.py            # rewrite assets/icons.html
    python3 tools/build-icons.py --check     # exit 1 if it is out of date
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# The library is split so an architecture diagram never pays for the brand marks:
# the function set is ~10k tokens, the brand set ~24k. The gallery shows both.
REFS = [ROOT / "references" / "primitive-icons.md",
        ROOT / "references" / "primitive-icons-brand.md"]
OUT = ROOT / "assets" / "icons.html"

START = '    <section class="cat">'
END = "    <footer>"

ENTRY_RE = re.compile(r"^### (?P<name>\S+)$\n.*?```svg\n(?P<svg>.*?)\n```", re.M | re.S)


def parse(md):
    """[(category, [(name, svg), ...]), ...] in document order."""
    out = []
    parts = re.split(r"^## (.+)$", md, flags=re.M)
    for i in range(1, len(parts), 2):
        cat, body = parts[i].strip(), parts[i + 1]
        icons = [(m.group("name"), m.group("svg").strip()) for m in ENTRY_RE.finditer(body)]
        if icons:
            out.append((cat, icons))
    return out


def render(cats):
    blocks = []
    for cat, icons in cats:
        cells = "\n".join(
            f'<div class="cell"><div class="icon">{svg}</div>'
            f'<div class="name">{name}</div></div>'
            for name, svg in icons)
        blocks.append(f'    <section class="cat"><h2>{cat}</h2><div class="grid">\n'
                      f"{cells}\n</div></section>")
    return "\n".join(blocks) + "\n"


def duplicates(cats):
    """Names sharing one drawing. `lakehouse` shipped as a byte-identical copy of
    `queue`, which reads in the gallery as two entries and in a diagram as one."""
    seen = {}
    for cat, icons in cats:
        for name, svg in icons:
            body = re.sub(r"\s+", "", re.sub(r"^<svg[^>]*>|</svg>$", "", svg))
            seen.setdefault(body, []).append(f"{cat}/{name}")
    return [v for v in seen.values() if len(v) > 1]


def main(argv):
    cats = [c for ref in REFS for c in parse(ref.read_text())]
    for group in duplicates(cats):
        print(f"duplicate artwork: {', '.join(group)} — fold them into one entry",
              file=sys.stderr)
        return 1
    page = OUT.read_text()
    head, _, rest = page.partition(START)
    _, _, tail = rest.partition(END)
    if not head or not tail:
        print(f"{OUT}: could not find the generated region", file=sys.stderr)
        return 2
    new = head + render(cats) + END + tail
    total = sum(len(i) for _, i in cats)
    if "--check" in argv:
        stale = new != page
        print(f"{OUT.name}: {'STALE — run tools/build-icons.py' if stale else 'up to date'} "
              f"({total} icons, {len(cats)} categories)")
        return 1 if stale else 0
    OUT.write_text(new)
    print(f"{OUT.name}: wrote {total} icons in {len(cats)} categories")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
