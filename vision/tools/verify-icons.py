#!/usr/bin/env python3
"""Flag icons that break the 24-grid, wobble off their node's axis, or mix styles.

primitive-icons.md documented a "monochrome 24x24 library" but nothing enforced it,
and the library had drifted badly:

  * ten icons carried their own viewBox — `hop` was 440x506, `pentaho` had a
    fractional origin. Each rendered fine standalone, so the drift was invisible;
    but the documented placement (`<g transform="translate(x,y)">`) inherits the
    parent's user units, so any of those ten dropped into a diagram drew 5-20x
    oversized, straight across the page.
  * every data-platform diagram mixed stroked Tabler icons with filled Simple
    Icons silhouettes. A filled mark is a solid mass and a hairline mark of the
    same 24x24 box carries a fraction of the ink, so the row never reads as one
    system however carefully each icon is placed.

Five checks:

  GRID    an icon's viewBox is not `0 0 24 24`. Every icon in the library is
          normalised to it, and every placement rule assumes it.
  BOX     width != height, or a size outside {20, 24}. Two sizes only — 24 in a
          node, 20 in a caption or legend — so a row never wobbles.
  AXIS    the icon's centre is off the axis of the label it sits above. Drift
          here is what reads as "the icons aren't lined up" — example-high-level
          -vertical.html had every node icon 56px right of its own centred label.

          Anchored to the label, not to the enclosing box, because a band or a
          boundary often carries a caption glyph at its left edge with the title
          centred elsewhere. Those two marks answer to different rules; only a
          stacked icon-over-label pair has one axis to share.
  BAND    a caption glyph inside a full-width band is off the band's centre line.
          A band has no stacked label to share an axis with, so it answers to the
          bar it sits in instead.
  MIX     one file contains both stroked and filled icons. See primitive-icons.md
          -> The two rules.

CATALOGS lists files whose job is to display the library itself, where showing
both styles is the point. Nothing else earns a MIX exemption.

Usage:
    python3 tools/verify-icons.py <file.html> [...]
    python3 tools/verify-icons.py --all
    python3 tools/verify-icons.py --self-test
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgstyle import effective                      # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "assets"

GRID = "0 0 24 24"
SIZES = (20.0, 24.0)        # caption/legend, node
AXIS_TOL = 0.75             # half a hairline; below this nothing is visible
LABEL_REACH = 40.0          # how far below the icon its label may sit
LABEL_SPAN = 120.0          # how far sideways, so a neighbour node's label never claims it
BAND_MIN_W, BAND_MAX_H = 400.0, 64.0    # a bar wide enough, and short enough, to be a band

SVG_RE = re.compile(r"<svg\b([^>]*)>", re.S)
TEXT_RE = re.compile(r"<text\b([^>]*)>", re.S)
RECT_RE = re.compile(r"<rect\b([^>]*)>", re.S)
ATTR_RE = re.compile(r'([\w:-]+)\s*=\s*"([^"]*)"')

# Files that exist to display the library, where both styles appearing is the point.
CATALOGS = {"icons.html"}


def attrs_of(tag):
    return dict(ATTR_RE.findall(tag))


def num(a, key):
    try:
        return float(a[key])
    except (KeyError, ValueError):
        return None


def is_paint(v):
    return v not in (None, "", "none", "transparent")


def icons(text, apply):
    """Every nested <svg> — the root diagram svg is the one that opens the file."""
    out = []
    for m in list(SVG_RE.finditer(text))[1:]:
        a = apply(attrs_of(m.group(1)))
        w, h = num(a, "width"), num(a, "height")
        if w is None or h is None or max(w, h) > 64:
            continue                                # not an icon-scale element
        out.append((m.start(), a, w, h))
    return out


def labels(text, apply):
    """Centred, upright labels, as (x, y). A left-anchored caption sets no axis for
    an icon to share, and neither does a rotated one — high-level's vertical strip
    labels are centred at their own x but drawn down the page."""
    out = []
    for m in TEXT_RE.finditer(text):
        a = apply(attrs_of(m.group(1)))
        if a.get("text-anchor") != "middle" or "transform" in a:
            continue
        x, y = num(a, "x"), num(a, "y")
        if x is not None and y is not None:
            out.append((x, y))
    return out


def bands(text, apply):
    """Full-width bars, as (x, y, w, h). A band carries a caption glyph at its edge
    rather than a stacked icon, so it gets its own rule."""
    out = []
    for m in RECT_RE.finditer(text):
        a = apply(attrs_of(m.group(1)))
        x, y, w, h = (num(a, k) for k in ("x", "y", "width", "height"))
        if None in (w, h) or w < BAND_MIN_W or h > BAND_MAX_H:
            continue
        out.append((x or 0.0, y or 0.0, w, h))
    return out


def check(text, catalog=False):
    apply = effective(text)
    found = icons(text, apply)
    centred = labels(text, apply)
    bars = bands(text, apply)
    msgs, styles = [], set()

    for _, a, w, h in found:
        name = a.get("data-icon") or "icon"
        vb = a.get("viewBox", "")
        if vb.strip() != GRID:
            msgs.append(f'GRID: {name} at ({a.get("x","?")},{a.get("y","?")}) has '
                        f'viewBox="{vb}" — every icon is normalised to "{GRID}"; '
                        f"re-copy it from primitive-icons.md or primitive-icons-brand.md")
        if w != h:
            msgs.append(f"BOX: {name} is {w:g}x{h:g} — icons are square")
        elif w not in SIZES:
            msgs.append(f"BOX: {name} is {w:g}px — use 24 in a node or 20 in a "
                        f"caption/legend, so a row never wobbles")

        stroked, filled = is_paint(a.get("stroke")), is_paint(a.get("fill"))
        if stroked:
            styles.add("stroked")
        elif filled:
            styles.add("filled")

        # AXIS — the label this icon stacks on top of, if there is one
        ix, iy = num(a, "x"), num(a, "y")
        if ix is None or iy is None:
            continue
        # A glyph inside a band is a caption: it answers to the bar's centre line, not
        # to any node label that happens to be within reach. example-high-level's
        # orchestration mark sat 4px high at the far edge while every other band put
        # its glyph left, inset 12 and centred.
        holding = [b for b in bars
                   if b[0] <= ix and ix + w <= b[0] + b[2]
                   and b[1] <= iy and iy + h <= b[1] + b[3]]
        if holding:
            bx, by, bw, bh = min(holding, key=lambda b: b[2] * b[3])
            off = (iy + h / 2) - (by + bh / 2)
            if abs(off) > AXIS_TOL:
                msgs.append(f"BAND: {name} at ({ix:g},{iy:g}) sits {off:+.1f}px off the "
                            f"centre line of its {bw:g}x{bh:g} band at ({bx:g},{by:g}) — "
                            f'set y="{by + bh / 2 - h / 2:g}"')
            continue

        below = [(lx, ly) for lx, ly in centred
                 if 0 < ly - (iy + h) <= LABEL_REACH and abs(lx - (ix + w / 2)) <= LABEL_SPAN]
        if not below:
            continue
        lx, ly = min(below, key=lambda p: p[1])         # the nearest one down
        drift = (ix + w / 2) - lx
        if abs(drift) > AXIS_TOL:
            msgs.append(f"AXIS: {name} at ({ix:g},{iy:g}) sits {drift:+.1f}px off its "
                        f'label\'s axis (x={lx:g}, y={ly:g}) — set x="{lx - w / 2:g}"')

    if len(styles) > 1 and not catalog:
        msgs.append(f"MIX: this file uses {' and '.join(sorted(styles))} icons — "
                    f"they cannot be optically balanced against each other; pick one "
                    f"(primitive-icons.md -> The two rules)")
    return msgs


ICON = ('<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}" '
        'fill="none" stroke="#2d3142" aria-hidden="true"><path d="M0 0"/></svg>')
# a node box plus the centred label its icon must share an axis with (cx = 180)
NODE = ('<rect x="100" y="50" width="160" height="80" stroke="#000" fill="white"/>'
        '<text x="180" y="108" text-anchor="middle">Trino</text>')
# a full-width band: caption glyph at the left edge, title centred in the middle
BAND = ('<rect x="20" y="50" width="960" height="44" stroke="#000" fill="white"/>'
        '<text x="500" y="76" text-anchor="middle">Orchestration</text>')
ROOT_SVG = '<svg viewBox="0 0 1000 500">'

SELF_TEST = [
    (ROOT_SVG + NODE + ICON.format(x=168, y=60, w=24, h=24, vb=GRID),
     0, "icon centred on its node"),
    (ROOT_SVG + NODE + ICON.format(x=150, y=60, w=24, h=24, vb=GRID),
     1, "icon off its node's axis"),
    (ROOT_SVG + NODE + ICON.format(x=168, y=60, w=24, h=24, vb="0 0 128 128"),
     1, "off-grid viewBox"),
    (ROOT_SVG + NODE + ICON.format(x=168, y=60, w=24, h=20, vb=GRID),
     1, "non-square box"),
    (ROOT_SVG + NODE + ICON.format(x=166, y=60, w=28, h=28, vb=GRID),
     1, "size outside {20, 24}"),
    (ROOT_SVG + ICON.format(x=10, y=10, w=20, h=20, vb=GRID),
     0, "20px caption glyph outside any node"),
    (ROOT_SVG + ICON.format(x=10, y=10, w=24, h=24, vb=GRID)
     + '<svg x="50" y="10" width="24" height="24" viewBox="0 0 24 24" '
       'fill="#2d3142" aria-hidden="true"><path d="M0 0"/></svg>',
     1, "stroked and filled in one file"),
    (ROOT_SVG + '<svg viewBox="0 0 24 24" width="900" height="400"><path d="M0 0"/></svg>',
     0, "large nested svg is not an icon"),
    (ROOT_SVG + BAND + ICON.format(x=30, y=60, w=24, h=24, vb=GRID),
     0, "band caption glyph does not answer to the band's centred title"),
    (ROOT_SVG + BAND + ICON.format(x=30, y=54, w=24, h=24, vb=GRID),
     1, "band caption glyph off the band's centre line"),
    (ROOT_SVG + BAND + '<text x="90" y="140" text-anchor="middle">node below</text>'
     + ICON.format(x=30, y=60, w=24, h=24, vb=GRID),
     0, "a nearby node label never claims a band's caption glyph"),
    (ROOT_SVG + '<text x="180" y="140" text-anchor="middle">far below</text>'
     + ICON.format(x=150, y=58, w=24, h=24, vb=GRID),
     0, "a label further than LABEL_REACH below sets no axis"),
    (ROOT_SVG + '<text x="180" y="108">left-anchored</text>'
     + ICON.format(x=150, y=60, w=24, h=24, vb=GRID),
     0, "a left-anchored label sets no axis"),
    (ROOT_SVG + '<text x="180" y="108" text-anchor="middle" '
     'transform="rotate(-90 180 108)">rotated strip label</text>'
     + ICON.format(x=150, y=60, w=24, h=24, vb=GRID),
     0, "a rotated label sets no horizontal axis"),
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
        for msg in check(f.read_text(), catalog=f.name in CATALOGS):
            print(f"{f}: icons: {msg}")
            total += 1
    print(f"Summary: {len(files)} file(s) checked, {total} finding(s).")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
