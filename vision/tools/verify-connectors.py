#!/usr/bin/env python3
"""Flag connectors that run along a node's own border.

The upstream design system has no checker for §6 connector rules 3/4/5.
This covers the most visible member of that family: an axis-aligned connector
segment that is COLLINEAR with a node edge and overlaps it, so the stroke
disappears into the box outline and the arrow appears to sprout from a corner.

Canonical example (upstream example-architecture.html, now fixed):

    <rect x="416" y="240" width="160" height="64" .../>   <!-- node -->
    <path d="M 496,240 H 692 ..."/>                       <!-- starts ON y=240 -->

The horizontal run from x=496 to x=576 lies exactly on the node's top border.

Usage:
    python3 tools/verify-connectors.py <file.html> [...]
    python3 tools/verify-connectors.py --all
    python3 tools/verify-connectors.py --self-test
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "assets"

# A node box is a stroked rect big enough to hold a label. Tag chips (28-36 x 12),
# label masks (h=12) and zone containers (drawn first, 2% wash) are excluded.
MIN_NODE_W, MIN_NODE_H = 60, 28
ZONE_FILL = re.compile(r"rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*0?\.0[0-3]\s*\)")

RECT_RE = re.compile(r"<rect\b([^>]*)>", re.S)
PATH_RE = re.compile(r"<path\b([^>]*)>", re.S)
LINE_RE = re.compile(r"<line\b([^>]*)>", re.S)
# Only arrow-bearing elements are connectors. Chart baselines, axis rules, layer
# separators and lifelines legitimately touch or coincide with a shape edge; an
# arrow doing it is the defect. Marker presence is the discriminator.
MARKER_RE = re.compile(r"\bmarker-(?:end|start|mid)\s*=", re.I)

# A label mask is the opaque plate painted behind an arrow label (§6). When it is
# nearly as long as the segment it annotates, the connector survives only as a
# sliver above or below the plate and the arrow reads as broken — that is what
# happened to example-deployment.html, where a 64px HTTPS:443 plate sat over a
# 64px run. Masks are unstroked paper-filled rects 10-14px tall.
MASK_H = (10.0, 14.0)
MASK_COVER_MAX = 0.8      # plate may cover at most this share of its segment
MASK_GAP_MAX = 20.0       # how far a plate can sit from the line it labels
ATTR_RE = re.compile(r'([\w:-]+)\s*=\s*"([^"]*)"')

TOL = 1.5          # collinear if within this many px of the edge
MIN_OVERLAP = 8.0  # ignore grazing contact shorter than this


def attrs(blob):
    return dict(ATTR_RE.findall(blob))


def num(d, k):
    try:
        return float(d.get(k, ""))
    except ValueError:
        return None


def nodes(text):
    """Stroked rects that read as node boxes."""
    out = []
    for blob in RECT_RE.findall(text):
        a = attrs(blob)
        if not a.get("stroke") or a.get("stroke") == "none":
            continue
        x, y = num(a, "x"), num(a, "y")
        w, h = num(a, "width"), num(a, "height")
        if None in (x, y, w, h) or w < MIN_NODE_W or h < MIN_NODE_H:
            continue
        if ZONE_FILL.search(a.get("fill", "")):   # zone container, painted first
            continue
        out.append((x, y, w, h))
    return out


def segments(text):
    """Axis-aligned segments from <path d> and <line>, as (x1,y1,x2,y2)."""
    segs = []
    for blob in LINE_RE.findall(text):
        if not MARKER_RE.search(blob):
            continue
        a = attrs(blob)
        pts = [num(a, k) for k in ("x1", "y1", "x2", "y2")]
        if None not in pts:
            segs.append(tuple(pts) + (True,))   # a <line> is its own last segment

    tok = re.compile(r"([MLHVQCAZmlhvqcaz])|(-?\d*\.?\d+)")
    for blob in PATH_RE.findall(text):
        if not MARKER_RE.search(blob):
            continue
        m = re.search(r'\bd="([^"]+)"', blob)
        if not m:
            continue
        d = m.group(1)
        cx = cy = 0.0
        cmd = None
        nums = []
        items = [(c, n) for c, n in tok.findall(d)]

        def flush():
            nonlocal cx, cy, nums
            if cmd == "M" and len(nums) >= 2:
                cx, cy = nums[0], nums[1]
            elif cmd == "H" and nums:
                nx = nums[-1]
                segs.append((cx, cy, nx, cy, False))
                cx = nx
            elif cmd == "V" and nums:
                ny = nums[-1]
                segs.append((cx, cy, cx, ny, False))
                cy = ny
            elif cmd == "L" and len(nums) >= 2:
                segs.append((cx, cy, nums[0], nums[1], False))
                cx, cy = nums[0], nums[1]
            elif cmd == "Q" and len(nums) >= 4:      # corner arc — endpoint only
                cx, cy = nums[2], nums[3]
            elif cmd == "C" and len(nums) >= 6:
                cx, cy = nums[4], nums[5]
            elif cmd == "A" and len(nums) >= 7:
                cx, cy = nums[5], nums[6]
            nums = []

        for c, n in items:
            if c:
                flush()
                cmd = c.upper() if c not in "mlhvqca" else c.upper()
            else:
                nums.append(float(n))
        flush()
        if segs and not segs[-1][4]:
            segs[-1] = segs[-1][:4] + (True,)   # last drawn segment carries the arrowhead
    return segs


def masks(text, paper):
    """Opaque label plates: unstroked rects of label height filled with paper."""
    out = []
    for blob in RECT_RE.findall(text):
        a = attrs(blob)
        if a.get("stroke") and a["stroke"] != "none":
            continue
        if a.get("fill", "").strip().lower() not in paper:
            continue
        x, y = num(a, "x"), num(a, "y")
        w, h = num(a, "width"), num(a, "height")
        if None in (x, y, w, h) or not (MASK_H[0] <= h <= MASK_H[1]):
            continue
        out.append((x, y, w, h))
    return out


def paper_colors(text):
    """Fills that count as paper — the page rect plus the usual two tokens."""
    found = {"#f5f5f5", "#2d3142", "#ffffff", "#fff"}
    m = re.search(r'<rect\b[^>]*width="100%"[^>]*fill="([^"]+)"', text)
    if m:
        found.add(m.group(1).strip().lower())
    return found


def overlap(a1, a2, b1, b2):
    lo, hi = max(min(a1, a2), min(b1, b2)), min(max(a1, a2), max(b1, b2))
    return hi - lo


def check(text):
    findings = []
    ns, sg = nodes(text), segments(text)
    for (x1, y1, x2, y2, _term) in sg:
        horiz = abs(y1 - y2) < 0.01
        vert = abs(x1 - x2) < 0.01
        if not (horiz or vert):
            continue
        for (nx, ny, nw, nh) in ns:
            if horiz:
                for edge, name in ((ny, "top"), (ny + nh, "bottom")):
                    if abs(y1 - edge) <= TOL:
                        ov = overlap(x1, x2, nx, nx + nw)
                        if ov > MIN_OVERLAP:
                            findings.append(
                                f"horizontal segment at y={y1:g} runs {ov:.0f}px along the "
                                f"{name} border of node ({nx:g},{ny:g},{nw:g}x{nh:g})")
            else:
                for edge, name in ((nx, "left"), (nx + nw, "right")):
                    if abs(x1 - edge) <= TOL:
                        ov = overlap(y1, y2, ny, ny + nh)
                        if ov > MIN_OVERLAP:
                            findings.append(
                                f"vertical segment at x={x1:g} runs {ov:.0f}px along the "
                                f"{name} border of node ({nx:g},{ny:g},{nw:g}x{nh:g})")
    # Label plate swallowing its own segment
    # Only NON-terminal runs matter: a plate over the final run still leaves the
    # arrowhead for the eye to land on, which is why state-machine transition
    # labels sitting over their whole arrow read fine. A plate over a run that
    # bends away is where the connector goes missing.
    horiz = [s for s in sg if abs(s[1] - s[3]) < 0.01 and not s[4]]
    for (mx, my, mw, mh) in masks(text, paper_colors(text)):
        for (x1, y1, x2, _y2, _t) in horiz:
            gap_below = y1 - (my + mh)      # line under the plate
            gap_above = my - y1             # line over the plate
            gap = gap_below if gap_below >= 0 else gap_above
            if not (0 <= gap <= MASK_GAP_MAX):
                continue
            ov = overlap(mx, mx + mw, x1, x2)
            if ov <= 0:
                continue
            seg = abs(x2 - x1)
            if seg > 0 and mw / seg > MASK_COVER_MAX:
                findings.append(
                    f"label plate {mw:g}px wide covers {mw / seg * 100:.0f}% of the "
                    f"{seg:g}px segment at y={y1:g} — the connector reads as broken; "
                    f"lengthen the run or shorten the label")
    return sorted(set(findings))


SELF_TEST = [
    # (svg, expected finding count, label)
    ('<rect x="416" y="240" width="160" height="64" stroke="#000" fill="#fff"/>'
     '<path d="M 496,240 H 692 Q 700,240 700,232 V 224" marker-end="url(#arrow)"/>', 1, "collinear with top border"),
    ('<rect x="416" y="240" width="160" height="64" stroke="#000" fill="#fff"/>'
     '<path d="M 576,256 H 692 Q 700,256 700,248 V 224" marker-end="url(#arrow)"/>', 0, "exits the side, clear of borders"),
    ('<rect x="416" y="240" width="160" height="64" stroke="#000" fill="#fff"/>'
     '<line x1="576" y1="272" x2="700" y2="272" marker-end="url(#arrow)"/>', 0, "leaves right edge at one point"),
    ('<rect x="416" y="240" width="160" height="64" stroke="#000" fill="#fff"/>'
     '<path d="M 416,304 H 576" marker-end="url(#arrow)"/>', 1, "full run along bottom border"),
    ('<rect x="416" y="240" width="160" height="64" stroke="#000" fill="#fff"/>'
     '<path d="M 570,304 H 590" marker-end="url(#arrow)"/>', 0, "6px graze is under the threshold"),
    ('<rect x="10" y="10" width="30" height="12" stroke="#000" fill="none"/>'
     '<path d="M 10,10 H 40" marker-end="url(#arrow)"/>', 0, "tag chip is not a node"),
    ('<rect x="616" y="128" width="164" height="272" stroke="#ccc" fill="rgba(45,49,66,0.02)"/>'
     '<path d="M 616,128 H 780" marker-end="url(#arrow)"/>', 0, "zone container is painted first"),
    ('<rect x="416" y="240" width="160" height="64" stroke="#000" fill="#fff"/>'
     '<path d="M 416,200 V 340" marker-end="url(#arrow)"/>', 1, "vertical along left border"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<rect x="304" y="80" width="232" height="84" stroke="#000" fill="#fff"/>'
     '<path d="M 224,196 H 288 Q 296,196 296,188 V 128" marker-end="url(#a)"/>'
     '<rect x="224" y="176" width="64" height="12" fill="#f5f5f5"/>',
     1, "label plate as long as its segment (the deployment defect)"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<rect x="304" y="80" width="232" height="84" stroke="#000" fill="#fff"/>'
     '<path d="M 144,156 V 128 Q 144,120 152,120 H 304" marker-end="url(#a)"/>'
     '<rect x="196" y="100" width="64" height="12" fill="#f5f5f5"/>',
     0, "label plate on a run long enough to stay readable"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<rect x="340" y="176" width="160" height="48" stroke="#000" fill="#fff"/>'
     '<line x1="280" y1="200" x2="340" y2="200" marker-end="url(#a)"/>'
     '<rect x="280" y="184" width="60" height="12" fill="#f5f5f5"/>',
     0, "plate over a straight arrow that ends in its arrowhead (state transitions)"),
    ('<rect x="99" y="192" width="72" height="228" stroke="#000" fill="#fff"/>'
     '<line x1="80" y1="420" x2="960" y2="420"/>', 0, "chart baseline under bars carries no arrow"),
    ('<rect x="120" y="144" width="840" height="64" stroke="#000" fill="#fff"/>'
     '<line x1="120" y1="144" x2="960" y2="144"/>', 0, "layer separator carries no arrow"),
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
    files = ([p for p in sorted(ASSET_DIR.glob("*.html"))] if "--all" in argv
             else [Path(a) for a in argv if not a.startswith("-")])
    if not files:
        print(__doc__)
        return 2
    total = 0
    for f in files:
        for msg in check(f.read_text()):
            print(f"{f}: connector: {msg}")
            total += 1
    print(f"Summary: {len(files)} file(s) checked, {total} finding(s).")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
