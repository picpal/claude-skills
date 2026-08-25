#!/usr/bin/env python3
"""Flag connectors that vanish into a node border or under a label plate.

The upstream design system has no checker for SKILL.md §6 connector rules 3/4/5.
This covers two members of that family, both of which make an arrow read as
broken:

  BORDER   an axis-aligned connector segment COLLINEAR with a node edge, so the
           stroke disappears into the box outline and the arrow appears to
           sprout from a corner. Canonical case, upstream example-architecture:

               <rect x="416" y="240" width="160" height="64" .../>
               <path d="M 496,240 H 692 ..."/>     <!-- starts ON y=240 -->

  PLATE    a label plate that swallows the END of a connector it crosses. A
           plate sitting ACROSS a line is the normal convention — the eye reads
           line, label, line — but only while the line re-emerges on both sides.
           When a plate covers the corner where a connector turns, the line goes
           in and never comes out. Canonical case, example-db-schema:

               <path d="M 640,408 H 708 Q 716,400 ... V 88 ..."/>
               <rect x="648" y="392" width="88" height="12" .../>

           The vertical at x=716 ends at y=400, four pixels INSIDE the plate.

Both are geometric, not aesthetic: a defect is a connector whose stroke is not
visible where the reader needs it.

Usage:
    python3 tools/verify-connectors.py <file.html> [...]
    python3 tools/verify-connectors.py --all
    python3 tools/verify-connectors.py --self-test
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgstyle import effective                      # noqa: E402

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

# A label mask is the opaque plate painted behind an arrow label (§6 rule 2).
# Masks are unstroked paper-filled rects 10-14px tall, drawn AFTER the connectors
# so they knock a hole in whatever runs behind them.
#
# MIN_TAIL is how much straight stroke must stay visible on each side of a plate
# the connector crosses. 6px is §6 rule 2's own number — the gap it already
# requires between a label and its line — so a plate may never leave less clear
# stroke than the rule demands clear space. A tail at the ARROWHEAD end is
# exempt from the minimum and only has to be non-negative: the 8x6px marker is
# itself the thing the eye lands on, so 4px of stroke plus a head reads fine.
MASK_H = (10.0, 14.0)
MIN_TAIL = 6.0
ATTR_RE = re.compile(r'([\w:-]+)\s*=\s*"([^"]*)"')

TOL = 1.5          # collinear if within this many px of the edge
MIN_OVERLAP = 8.0  # ignore grazing contact shorter than this
MIN_ATTACH = 12.0  # §6 rule 4: attach points on one edge stay this far apart
MIN_TRANSIT = 4.0  # ignore a stroke clipping a rounded corner

# §6 rule 1 forbids diagonals, but a few grammars are built on angle and cannot
# obey it. Widen this table rather than relaxing the rule.
DIAGONAL_TYPES = {
    "loop":          "type-loop.md:7,63 — parametric: stations sit on a circle and spokes radiate",
    "loop-terminal": "type-loop.md — same grammar, terminal variant",
    "queue-animated":     "motion demo — queue arrivals fan in at an angle",
    "paved-road-animated": "motion demo",
}


def slug_of(path):
    name = Path(path).stem
    if name.startswith("example-"):
        name = name[len("example-"):]
    for suffix in ("-ko", "-dark", "-full", "-vertical"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def attrs(blob):
    return dict(ATTR_RE.findall(blob))


def num(d, k):
    try:
        return float(d.get(k, ""))
    except ValueError:
        return None


def nodes(text):
    """Stroked rects that read as node boxes.

    Styling may come from a class rather than an attribute — see svgstyle.py.
    """
    style = effective(text)
    out = []
    for blob in RECT_RE.findall(text):
        a = style(attrs(blob))
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


# Argument counts per SVG path command. Lowercase is the same command relative to
# the current point — reading a relative `a 8,8 0 0,0 -16,0` (a line hop) as if it
# were absolute puts the cursor at (-16, 0) and every segment after it is fiction.
ARGC = {"M": 2, "L": 2, "T": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "A": 7, "Z": 0}
TOKEN_RE = re.compile(r"([MLHVCSQTAZmlhvcsqtaz])|(-?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)")


def walk(d, segs):
    """Append this path's axis-aligned straight runs as (x1,y1,x2,y2,False).

    Returns ((start_x, start_y), (end_x, end_y)) — the true endpoints, which are
    NOT the last segment's: a connector that finishes on a corner fillet puts its
    arrowhead at the end of the curve, several pixels past the last straight run.

    Curves and arcs move the cursor without emitting a segment: in this system
    they are only ever corner fillets, never a run a reader traces.
    """
    items = TOKEN_RE.findall(d)
    cx = cy = sx = sy = 0.0
    cmd = None
    args = []
    first = None

    def emit(nx, ny):
        nonlocal cx, cy
        if abs(nx - cx) > 1e-9 or abs(ny - cy) > 1e-9:
            segs.append((cx, cy, nx, ny, False))
        cx, cy = nx, ny

    def run(letter, a):
        nonlocal cx, cy, sx, sy, first
        up = letter.upper()
        rel = letter.islower()
        if up == "M":
            cx, cy = (cx + a[0], cy + a[1]) if rel else (a[0], a[1])
            sx, sy = cx, cy
            if first is None:
                first = (cx, cy)
        elif up == "L" or up == "T":
            emit(cx + a[0] if rel else a[0], cy + a[1] if rel else a[1])
        elif up == "H":
            emit(cx + a[0] if rel else a[0], cy)
        elif up == "V":
            emit(cx, cy + a[0] if rel else a[0])
        elif up == "C":
            cx, cy = (cx + a[4], cy + a[5]) if rel else (a[4], a[5])
        elif up in ("S", "Q"):
            cx, cy = (cx + a[2], cy + a[3]) if rel else (a[2], a[3])
        elif up == "A":
            cx, cy = (cx + a[5], cy + a[6]) if rel else (a[5], a[6])
        elif up == "Z":
            emit(sx, sy)

    for letter, number in items:
        if letter:
            cmd = letter
            args = []
            if ARGC[cmd.upper()] == 0:
                run(cmd, [])
                cmd = None
            continue
        if cmd is None:
            continue
        args.append(float(number))
        need = ARGC[cmd.upper()]
        if len(args) == need:
            run(cmd, args)
            args = []
            # An M with extra coordinate pairs continues as an implicit L.
            if cmd == "M":
                cmd = "L"
            elif cmd == "m":
                cmd = "l"
    return (first[0], first[1]) if first else (cx, cy), (cx, cy)


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

    for blob in PATH_RE.findall(text):
        if not MARKER_RE.search(blob):
            continue
        m = re.search(r'\bd="([^"]+)"', blob)
        if not m:
            continue
        before = len(segs)
        walk(m.group(1), segs)
        if len(segs) > before:
            segs[-1] = segs[-1][:4] + (True,)   # last drawn segment carries the arrowhead
    return segs


def connectors(text):
    """One record per arrow-bearing element: its runs, true endpoints, dash state.

    The dash state decides whether §6 rule 5 permits a transit, and it is often
    set by a class (`.auth{stroke-dasharray:5 4}`) rather than an attribute — so
    it is resolved the same way node fills are.
    """
    style = effective(text)
    out = []
    for blob in LINE_RE.findall(text):
        if not MARKER_RE.search(blob):
            continue
        a = style(attrs(blob))
        pts = [num(a, k) for k in ("x1", "y1", "x2", "y2")]
        if None in pts:
            continue
        out.append({"segs": [tuple(pts) + (True,)],
                    "start": (pts[0], pts[1]), "end": (pts[2], pts[3]),
                    "dashed": bool(a.get("stroke-dasharray"))})
    for blob in PATH_RE.findall(text):
        if not MARKER_RE.search(blob):
            continue
        m = re.search(r'\bd="([^"]+)"', blob)
        if not m:
            continue
        segs = []
        start, end = walk(m.group(1), segs)
        if segs:
            segs[-1] = segs[-1][:4] + (True,)
        a = style(attrs(blob))
        out.append({"segs": segs, "start": start, "end": end,
                    "dashed": bool(a.get("stroke-dasharray"))})
    return out


def masks(text, paper):
    """Opaque label plates: unstroked rects of label height filled with paper."""
    style = effective(text)
    out = []
    for blob in RECT_RE.findall(text):
        a = style(attrs(blob))
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


def check(text, allow_diagonal=False):
    findings = []
    ns, sg = nodes(text), segments(text)
    cons = connectors(text)
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
    # A label plate that swallows the end of a connector it crosses.
    #
    # Crossing a line is what a mask is FOR: the plate knocks a hole in the
    # stroke so the label is legible, and the eye bridges the gap because the
    # line re-emerges on the far side. The defect is the plate landing on the
    # END of a run — the corner where the connector turns away. There the line
    # goes under the plate and never comes out, so the connector reads as two
    # unrelated pieces. Measured as the straight stroke left visible on each
    # side; an arrowhead end only has to clear the plate, since the marker is
    # itself what the eye lands on.
    for (mx, my, mw, mh) in masks(text, paper_colors(text)):
        for (x1, y1, x2, y2, term) in sg:
            if abs(y1 - y2) < 0.01:                       # horizontal
                if not (my < y1 < my + mh):
                    continue
                lo, hi, plo, phi = min(x1, x2), max(x1, x2), mx, mx + mw
                head_at_hi = term and x2 > x1
                axis = f"horizontal run at y={y1:g}"
            elif abs(x1 - x2) < 0.01:                     # vertical
                if not (mx < x1 < mx + mw):
                    continue
                lo, hi, plo, phi = min(y1, y2), max(y1, y2), my, my + mh
                head_at_hi = term and y2 > y1
                axis = f"vertical run at x={x1:g}"
            else:
                continue
            if min(hi, phi) - max(lo, plo) <= 0:          # plate misses the run
                continue
            for tail, is_head, side in ((plo - lo, term and not head_at_hi, "before"),
                                        (hi - phi, head_at_hi, "after")):
                floor = 0.0 if is_head else MIN_TAIL
                if tail >= floor:
                    continue
                findings.append(
                    f"label plate ({mx:g},{my:g} {mw:g}x{mh:g}) leaves {tail:g}px of the "
                    f"{axis} visible {side} it — the connector disappears under the plate "
                    f"and does not re-emerge; move the plate clear of the turn "
                    f"(§6 rule 2 wants {MIN_TAIL:g}px)")
    # --- §6 rule 1: connectors are orthogonal -------------------------------
    for c in (() if allow_diagonal else cons):
        for (x1, y1, x2, y2, _t) in c["segs"]:
            if abs(y1 - y2) > 0.5 and abs(x1 - x2) > 0.5:
                findings.append(
                    f"DIAGONAL: run ({x1:g},{y1:g})-({x2:g},{y2:g}) is neither "
                    f"horizontal nor vertical — §6 rule 1 allows orthogonal runs "
                    f"with r=8 corners only")

    # --- §6 rule 3: two connectors must not be drawn on top of each other ----
    for i in range(len(cons)):
        for j in range(i + 1, len(cons)):
            for a in cons[i]["segs"]:
                for b in cons[j]["segs"]:
                    ah, bh = abs(a[1] - a[3]) < 0.01, abs(b[1] - b[3]) < 0.01
                    av, bv = abs(a[0] - a[2]) < 0.01, abs(b[0] - b[2]) < 0.01
                    if ah and bh and abs(a[1] - b[1]) < 1.0:
                        ov, axis = overlap(a[0], a[2], b[0], b[2]), f"y={a[1]:g}"
                    elif av and bv and abs(a[0] - b[0]) < 1.0:
                        ov, axis = overlap(a[1], a[3], b[1], b[3]), f"x={a[0]:g}"
                    else:
                        continue
                    if ov > MIN_OVERLAP:
                        findings.append(
                            f"OVERLAP: two connectors share {ov:.0f}px of the same "
                            f"line at {axis} — §6 rule 3; fan them onto separate "
                            f"lanes, or hop one over the other")

    # --- §6 rule 4: attach points on one edge stay 12px apart ---------------
    for i in range(len(cons)):
        for j in range(i + 1, len(cons)):
            for ka, kb in (("end", "end"), ("start", "start")):
                pa, pb = cons[i][ka], cons[j][kb]
                d = abs(pa[0] - pb[0]) + abs(pa[1] - pb[1])
                if d < MIN_ATTACH:
                    what = "arrowheads" if ka == "end" else "tails"
                    findings.append(
                        f"ATTACH: two {what} land {d:.0f}px apart at "
                        f"({pa[0]:g},{pa[1]:g}) — §6 rule 4 fans N connectors "
                        f"across an edge of length L at L*k/(N+1), never under "
                        f"{MIN_ATTACH:g}px apart")

    # --- §6 rule 5: no solid connector transits a non-endpoint box ----------
    for c in cons:
        if c["dashed"]:
            continue                      # rule 5 permits it dashed, labelled at the visible end
        for (nx, ny, nw, nh) in ns:
            if any(nx - 2 <= px <= nx + nw + 2 and ny - 2 <= py <= ny + nh + 2
                   for px, py in (c["start"], c["end"])):
                continue                  # this box is one of the connector's endpoints
            for (x1, y1, x2, y2, _t) in c["segs"]:
                if abs(y1 - y2) < 0.01:
                    if not (ny + 2 < y1 < ny + nh - 2):
                        continue
                    ov = overlap(x1, x2, nx + 2, nx + nw - 2)
                elif abs(x1 - x2) < 0.01:
                    if not (nx + 2 < x1 < nx + nw - 2):
                        continue
                    ov = overlap(y1, y2, ny + 2, ny + nh - 2)
                else:
                    continue
                if ov > MIN_TRANSIT:
                    findings.append(
                        f"TRANSIT: a solid connector runs {ov:.0f}px through node "
                        f"({nx:g},{ny:g},{nw:g}x{nh:g}), which is neither its source "
                        f"nor its target — §6 rule 5; route around it, or dash the "
                        f"stroke and label it at the visible end")

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
    # --- path grammar: a misread command puts every later segment somewhere else -
    ('<rect x="200" y="240" width="160" height="64" stroke="#000" fill="#fff"/>'
     '<path d="M 100,240 h 160" marker-end="url(#arrow)"/>',
     1, "relative h — 100+160 lands on the top border, not at x=160"),
    ('<rect x="200" y="240" width="160" height="64" stroke="#000" fill="#fff"/>'
     '<path d="M 600,200 H 460 a 8,8 0 0,0 -16,0 H 100 V 40" marker-end="url(#arrow)"/>',
     0, "a relative arc hop keeps the cursor on the run, not at (-16,0)"),
    ('<rect x="200" y="240" width="160" height="64" stroke="#000" fill="#fff"/>'
     '<path d="M 100,100 L 100,240 360,240" marker-end="url(#arrow)"/>',
     1, "implicit repeat of L still reaches the border"),
    ('<rect x="200" y="240" width="160" height="64" stroke="#000" fill="#fff"/>'
     '<path d="M 100,100 100,240 360,240" marker-end="url(#arrow)"/>',
     1, "extra coordinate pairs after M are implicit L"),
    ('<rect x="200" y="240" width="120" height="64" stroke="#000" fill="#fff"/>'
     '<path d="M 100,240 V 400 H 360 V 240 Z" marker-end="url(#arrow)"/>',
     1, "Z closes back to the subpath start — and that leg hits the border"),
    # --- PLATE: a plate must not swallow the end of a run it crosses ---------
    # Positives are the four real defects found in the shipped corpus; the
    # negatives outnumber them, and every one is a plate that legitimately sits
    # ACROSS its own connector — the convention this check must not break.
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M 640,408 H 708 A8,8 0 0 0 716,400 V 88 A8,8 0 0 1 724,80 H 760" marker-end="url(#a)"/>'
     '<rect x="648" y="392" width="88" height="12" fill="#f5f5f5"/>',
     1, "PLATE: plate ends 4px past the corner it covers (example-db-schema)"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M560,192 H592 A8,8 0 0 0 600,184 V164 A8,8 0 0 1 608,156 H640" marker-end="url(#a)"/>'
     '<rect x="568" y="172" width="44" height="12" fill="#f5f5f5"/>',
     1, "PLATE: plate covers 12px of a 20px riser (example-import-drawio VERIFY)"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M208,296 H264 A8,8 0 0 0 272,288 V200 A8,8 0 0 1 280,192 H328" marker-end="url(#a)"/>'
     '<rect x="220" y="276" width="56" height="12" fill="#f5f5f5"/>',
     1, "PLATE: plate lands on the turn (example-import-mermaid REQUEST)"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M432,508 H204 A8,8 0 0 1 196,500 V320" marker-end="url(#a)"/>'
     '<rect x="204" y="504" width="40" height="12" fill="#f5f5f5"/>',
     1, "PLATE: plate starts exactly on the corner (example-dependency CYCLE)"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M 500,288 V 328" marker-end="url(#a)"/>'
     '<rect x="484" y="298" width="32" height="12" fill="#f5f5f5"/>',
     0, "PLATE: branch label sits across its own line, 10px tail each side"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M 640,240 V 300" marker-end="url(#a)"/>'
     '<rect x="612" y="264" width="56" height="12" fill="#f5f5f5"/>',
     0, "PLATE: state transition label centred on its arrow"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M 640,400 V 432" marker-end="url(#a)"/>'
     '<rect x="620" y="416" width="40" height="12" fill="#f5f5f5"/>',
     0, "PLATE: 4px tail is fine when the arrowhead lands there"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M 220,288 H 168" marker-end="url(#a)"/>'
     '<rect x="172" y="278" width="32" height="12" fill="#f5f5f5"/>',
     0, "PLATE: same, running leftward into its head"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M 260,480 H 380" marker-end="url(#a)"/>'
     '<rect x="288" y="474" width="12" height="12" fill="#f5f5f5"/>'
     '<rect x="348" y="474" width="24" height="12" fill="#f5f5f5"/>',
     0, "PLATE: two multiplicity plates on one association line"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M 876,320 H 480" marker-end="url(#a)"/>'
     '<rect x="660" y="314" width="36" height="12" fill="#f5f5f5"/>',
     0, "PLATE: plate mid-way along a long run"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M220,164 H272 A8,8 0 0 1 280,172 V192 A8,8 0 0 0 288,200 H360" marker-end="url(#a)"/>'
     '<rect x="228" y="144" width="44" height="12" fill="#f5f5f5"/>',
     0, "PLATE: plate offset 8px above its run, wider than the run"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M 400,104 H 348 Q 340,104 340,112 Q 340,120 332,120 H 280" marker-end="url(#a)"/>'
     '<rect x="284" y="82" width="112" height="12" fill="#f5f5f5"/>',
     0, "PLATE: plate twice the width of its run, sitting in an empty gutter"),
    ('<rect width="100%" height="100%" fill="#f5f5f5"/>'
     '<path d="M752,336 V352 A8,8 0 0 1 744,360 H696 A8,8 0 0 0 688,368 V384" marker-end="url(#a)"/>'
     '<rect x="696" y="340" width="48" height="12" fill="#f5f5f5"/>',
     0, "PLATE: plate exactly as long as its run, but clear of both turns"),
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
        exempt = slug_of(f) in DIAGONAL_TYPES
        for msg in check(f.read_text(), allow_diagonal=exempt):
            print(f"{f}: connector: {msg}")
            total += 1
    print(f"Summary: {len(files)} file(s) checked, {total} finding(s).")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
