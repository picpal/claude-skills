#!/usr/bin/env python3
"""Flag sibling node boxes that touch, overlap, or crowd each other.

The upstream design system states gap sizes in SKILL.md §7 (20/24/32/40/48) but
nothing enforces them, so a row of siblings can ship sharing a border. That is
what happened in example-tree.html: `polish` ended at x=220 and `critique` began
at x=220, drawing one 320px box with a line through it.

Two severities:

  TOUCH   gap <= 0 — the boxes share a border or overlap. Checked on BOTH axes.
          Always a defect; no type in this system tiles stroked node boxes edge
          to edge.
  CROWD   0 < gap < 20 — below the smallest gap §7 allows. Checked on the ROW
          axis only, and skipped for types with a documented gutter (GUTTERS).

CROWD is deliberately not applied down a column. Vertical stacking is per-type
grammar, not §7 spacing: type-kanban.md fixes a 12px card gap, story-map stacks
cards inside release bands, and high-level stacks full-width phase bars. Those
are intentionally tight and each type reference governs them.

GUTTERS records the types whose grammar sets its own spacing, with the reference
that says so. Widen this table rather than lowering MIN_GAP.

Usage:
    python3 tools/verify-spacing.py <file.html> [...]
    python3 tools/verify-spacing.py --all
    python3 tools/verify-spacing.py --self-test
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgstyle import effective                      # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "assets"

MIN_GAP = 20.0          # SKILL.md §7: smallest allowed gap between nodes
MIN_NODE_W, MIN_NODE_H = 60, 28

# type slug -> (documented gutter, where it is documented)
GUTTERS = {
    "treemap":   (4.0,  "type-treemap.md — cells tile on the 4px grid; area is the encoding"),
    "medallion": (16.0, "type-medallion.md — tiers read as one stack"),
    "data-flow": (12.0, "type-data-flow.md — role-scoped steps read as one pipeline"),
    "process":   (12.0, "type-process.md:89 — step_slot_w 112 with node_w 100 fixes a 12px pitch"),
    "dp-security-matrix": (12.0,
                 "type-dp-security-matrix.md:81,83 — comp_role_gap 12, role_col_gap 16"),
}

RECT_RE = re.compile(r"<rect\b([^>]*)>", re.S)
ATTR_RE = re.compile(r'([\w:-]+)\s*=\s*"([^"]*)"')
ZONE_FILL = re.compile(r"rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*0?\.0[0-3]\s*\)")


def slug_of(path):
    name = Path(path).stem
    for prefix in ("example-",):
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in ("-ko", "-dark", "-full", "-vertical"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def nodes(text):
    """Stroked rects big enough to be node boxes; zone containers excluded.

    Styling may come from a class rather than an attribute — see svgstyle.py.
    """
    style = effective(text)
    out = []
    for blob in RECT_RE.findall(text):
        a = style(dict(ATTR_RE.findall(blob)))
        if not a.get("stroke") or a["stroke"] == "none":
            continue
        try:
            x, y, w, h = (float(a[k]) for k in ("x", "y", "width", "height"))
        except (KeyError, ValueError):
            continue
        if w < MIN_NODE_W or h < MIN_NODE_H:
            continue
        if ZONE_FILL.search(a.get("fill", "")):
            continue
        out.append((x, y, w, h))
    return out


def check(text, min_gap=MIN_GAP):
    findings = []
    ns = nodes(text)

    # A "row" is boxes sharing top edge and height; a "column" shares left edge
    # and width. Siblings in tree/kanban/swimlane layouts always line up that way.
    for axis, keyfn, posfn, sizefn, word, crowd in (
        ("row", lambda n: (n[1], n[3]), lambda n: n[0], lambda n: n[2], "horizontally", True),
        ("column", lambda n: (n[0], n[2]), lambda n: n[1], lambda n: n[3], "vertically", False),
    ):
        groups = defaultdict(set)
        for n in ns:
            groups[keyfn(n)].add((posfn(n), sizefn(n)))
        for key, items in groups.items():
            items = sorted(items)
            for (p1, s1), (p2, _) in zip(items, items[1:]):
                gap = p2 - (p1 + s1)
                if gap <= 0:
                    findings.append(
                        f"TOUCH: two boxes in the same {axis} at {key[0]:g} "
                        f"{'share a border' if gap == 0 else 'overlap'} "
                        f"({p1:g}+{s1:g} vs {p2:g}, gap {gap:g}px)")
                elif crowd and gap < min_gap:
                    findings.append(
                        f"CROWD: boxes {word} {gap:g}px apart in the same {axis} "
                        f"at {key[0]:g} — SKILL.md §7 allows no gap under {min_gap:g}px")
    return sorted(set(findings))


SELF_TEST = [
    ('<rect x="60" y="336" width="160" height="48" stroke="#000" fill="#fff"/>'
     '<rect x="220" y="336" width="160" height="48" stroke="#000" fill="#fff"/>',
     1, "siblings sharing a border (the example-tree defect)"),
    ('<rect x="60" y="336" width="160" height="48" stroke="#000" fill="#fff"/>'
     '<rect x="240" y="336" width="160" height="48" stroke="#000" fill="#fff"/>',
     0, "siblings 20px apart"),
    ('<rect x="60" y="336" width="160" height="48" stroke="#000" fill="#fff"/>'
     '<rect x="228" y="336" width="160" height="48" stroke="#000" fill="#fff"/>',
     1, "siblings 8px apart — crowded"),
    ('<rect x="60" y="336" width="160" height="48" stroke="#000" fill="#fff"/>'
     '<rect x="200" y="336" width="160" height="48" stroke="#000" fill="#fff"/>',
     1, "siblings overlapping"),
    ('<rect x="60" y="100" width="160" height="48" stroke="#000" fill="#fff"/>'
     '<rect x="220" y="336" width="160" height="48" stroke="#000" fill="#fff"/>',
     0, "different rows never compared"),
    ('<rect x="60" y="100" width="160" height="48" stroke="#000" fill="#fff"/>'
     '<rect x="60" y="148" width="160" height="48" stroke="#000" fill="#fff"/>',
     1, "stacked boxes sharing a horizontal border"),
    ('<rect x="60" y="100" width="160" height="48" stroke="#000" fill="#fff"/>'
     '<rect x="60" y="160" width="160" height="48" stroke="#000" fill="#fff"/>',
     0, "12px vertical stack is per-type grammar, not a CROWD"),
    ('<rect x="10" y="10" width="30" height="12" stroke="#000" fill="none"/>'
     '<rect x="40" y="10" width="30" height="12" stroke="#000" fill="none"/>',
     0, "tag chips are not node boxes"),
    ('<rect x="0" y="0" width="164" height="272" stroke="#ccc" fill="rgba(45,49,66,0.02)"/>'
     '<rect x="164" y="0" width="164" height="272" stroke="#ccc" fill="rgba(45,49,66,0.02)"/>',
     0, "zone containers may abut"),
]


def self_test():
    bad = 0
    for svg, want, label in SELF_TEST:
        got = len(check(svg))
        ok = got == want
        bad += not ok
        print(f"  [{'ok' if ok else 'FAIL'}] {label}: expected {want}, got {got}")
    print(f"self-test: {len(SELF_TEST) - bad}/{len(SELF_TEST)} passed")
    return 1 if bad else 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    files = (sorted(ASSET_DIR.glob("*.html")) if "--all" in argv
             else [Path(a) for a in argv if not a.startswith("-")])
    if not files:
        print(__doc__)
        return 2
    total = 0
    for f in files:
        gutter = GUTTERS.get(slug_of(f))
        for msg in check(f.read_text(), gutter[0] if gutter else MIN_GAP):
            print(f"{f}: spacing: {msg}")
            total += 1
    print(f"Summary: {len(files)} file(s) checked, {total} finding(s).")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
