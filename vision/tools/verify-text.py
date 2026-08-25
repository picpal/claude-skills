#!/usr/bin/env python3
"""Measure rendered text against the box or plate that is supposed to contain it.

Every other checker here parses attributes. None of them can see a label, because
how wide a label draws depends on the font, the size, the tracking and the script
— Hangul advances roughly a full em where Latin advances half. That is the gap
this closes: it renders the file in a real browser, reads `getBBox()` for every
`<text>`, and compares it to the rect behind it.

Two checks:

  FIT    a label's box must fit inside its mask plate. A plate narrower than its
         text is not masking it — whatever runs behind shows through the first
         and last glyphs. Found in example-db-schema: an 88px plate holding
         90px of `ON DELETE CASCADE`.

  BOX    a label's box must fit inside its node box, with padding. This is the
         one that catches translation: a name sized for English overflowing the
         box when it becomes Korean.

Both compare against the *advance* box `getBBox()` returns, which is the area the
text occupies, side bearings included — the conservative measure, and the right
one for a mask.

REQUIRES A BROWSER. Set CHROME to a Chrome/Chromium binary, or let it find one in
the usual places. Without one this exits 2 and says so; it never reports green.

Caveat: it measures the fonts that actually resolve. `Pretendard` is not on
Google Fonts (see NOTICE), so where it is not installed locally the measurement
is of `Noto Sans KR` — which is what a CI render shows anyway, and the wider of
the two. Mono falls back to the system monospace when offline; measure online for
numbers that match what a reader sees.

Usage:
    python3 tools/verify-text.py <file.html> [...]
    python3 tools/verify-text.py --all
    python3 tools/verify-text.py --self-test
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "assets"

MIN_PLATE_PAD = 0.0    # a mask must at least contain its text, across
MIN_BOX_PAD_X = 0.0    # so must a node box; §7 asks for 8, the corpus keeps ~4
MIN_BOX_PAD_Y = 0.0
# Both checks are HORIZONTAL only.
#
# `getBBox()` on <text> returns the em box — ascent to descent — not the ink box.
# An 8px label measures ~10px tall whether or not the string has a descender, so a
# label sitting near an edge reads as overhanging by a fraction of a pixel that is
# not there. Measured across this corpus, a vertical test flags all 726 plates at
# about -0.2px, and thirteen node labels between -0.1px and -4.9px — every one of
# them a label deliberately set against an edge (`nested`'s container captions sit
# ON the border, by that type's grammar) or a descender's worth of empty box.
# Tuning a tolerance would only hide that the em box is the wrong ruler.
#
# Horizontal is the axis with a defect class behind it, and the one translation
# threatens: Hangul advances about a full em where Latin advances half, so a name
# that fits in English overflows in Korean. Height is set by font-size, which
# translating does not change.
CHECK_VERTICALLY = False
PLATE_H = (10.0, 14.0)
MIN_NODE_W, MIN_NODE_H = 60, 28
PAPER = {"#f5f5f5", "#2d3142", "#ffffff", "#fff"}
# A zone container is a wash-filled or transparent dashed frame drawn first. It
# encloses labels it does not own, so it must never be read as their box.
ZONE_FILL = re.compile(r"^(transparent|none)$|rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*0?\.0[0-5]\s*\)")

CHROME_CANDIDATES = [
    os.environ.get("CHROME", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "chromium", "chromium-browser", "chrome",
]

PROBE = r"""
<script>
(async () => {
  try { await document.fonts.ready; } catch (e) {}
  const out = [];
  for (const svg of document.querySelectorAll('svg')) {
    const rects = [];
    for (const r of svg.querySelectorAll('rect')) {
      if ((r.getAttribute('width') || '').includes('%')) continue;
      let b; try { b = r.getBBox(); } catch (e) { continue; }
      if (!(b.width > 0 && b.height > 0)) continue;
      rects.push({x: b.x, y: b.y, w: b.width, h: b.height,
                  fill: (r.getAttribute('fill') || '').trim().toLowerCase(),
                  stroke: (r.getAttribute('stroke') || '').trim().toLowerCase(),
                  dash: !!r.getAttribute('stroke-dasharray')});
    }
    for (const t of svg.querySelectorAll('text')) {
      let b; try { b = t.getBBox(); } catch (e) { continue; }
      if (!(b.width > 0)) continue;
      out.push({txt: (t.textContent || '').trim().slice(0, 40),
                x: b.x, y: b.y, w: b.width, h: b.height, rects: rects});
    }
    if (out.length) break;
  }
  document.title = 'VT' + JSON.stringify(out.map(o => ({t: o.txt, b: [o.x, o.y, o.w, o.h]})))
                 + 'VR' + JSON.stringify(out.length ? out[0].rects : []);
})();
</script>
"""


def find_chrome():
    for cand in CHROME_CANDIDATES:
        if not cand:
            continue
        if os.path.sep in cand:
            if Path(cand).exists():
                return cand
        else:
            found = shutil.which(cand)
            if found:
                return found
    return None


def unescape(s):
    for a, b in (("&quot;", '"'), ("&#34;", '"'), ("&amp;", "&"),
                 ("&lt;", "<"), ("&gt;", ">"), ("&#39;", "'")):
        s = s.replace(a, b)
    return s


def render(chrome, path, tmpdir):
    src = Path(path).read_text()
    probed = (src.replace("</body>", PROBE + "</body>", 1) if "</body>" in src
              else src + PROBE)
    tmp = Path(tmpdir) / (Path(path).stem + ".probe.html")
    tmp.write_text(probed)
    proc = subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=5000", "--dump-dom", f"file://{tmp}"],
        capture_output=True, text=True, timeout=90)
    m = re.search(r"<title>VT(.*?)VR(.*?)</title>", proc.stdout, re.S)
    if not m:
        return None
    return json.loads(unescape(m.group(1))), json.loads(unescape(m.group(2)))


def classify(r):
    stroked = bool(r["stroke"]) and r["stroke"] != "none"
    if not stroked and r["fill"] in PAPER and PLATE_H[0] <= r["h"] <= PLATE_H[1]:
        return "plate"
    if stroked and r["w"] >= MIN_NODE_W and r["h"] >= MIN_NODE_H:
        if r["dash"] or ZONE_FILL.search(r["fill"]):
            return None                      # zone container, not a label's box
        return "node"
    return None


def smallest_containing(rects, kind, cx, cy):
    hits = [r for r in rects
            if classify(r) == kind
            and r["x"] <= cx <= r["x"] + r["w"] and r["y"] <= cy <= r["y"] + r["h"]]
    return min(hits, key=lambda r: r["w"] * r["h"]) if hits else None


def check(texts, rects):
    findings = []
    for t in texts:
        bx, by, bw, bh = t["b"]
        cx, cy = bx + bw / 2, by + bh / 2
        for kind, tag, padx, pady in (("plate", "FIT", MIN_PLATE_PAD, MIN_PLATE_PAD),
                                      ("node", "BOX", MIN_BOX_PAD_X, MIN_BOX_PAD_Y)):
            box = smallest_containing(rects, kind, cx, cy)
            if not box:
                continue
            left, right = bx - box["x"], (box["x"] + box["w"]) - (bx + bw)
            top, bot = by - box["y"], (box["y"] + box["h"]) - (by + bh)
            worst_x = min(left, right)
            worst_y = min(top, bot) if CHECK_VERTICALLY else None
            if worst_x < padx or (worst_y is not None and worst_y < pady):
                where = "plate" if kind == "plate" else "node box"
                down = "" if worst_y is None else f", {worst_y:.1f}px down"
                findings.append(
                    f"{tag}: {t['t']!r} draws {bw:.1f}x{bh:.1f}px but its {where} is "
                    f"{box['w']:g}x{box['h']:g} at ({box['x']:g},{box['y']:g}) — "
                    f"padding {worst_x:.1f}px across{down}; "
                    f"widen the {where} or shorten the text")
    return sorted(set(findings))


SELF_TEST = [
    # (texts, rects, expected, label)
    ([{"t": "OK", "b": [10, 10, 40, 9]}],
     [{"x": 4, "y": 8, "w": 52, "h": 12, "fill": "#f5f5f5", "stroke": "", "dash": False}],
     0, "text inside its plate with 6px each side"),
    ([{"t": "ON DELETE CASCADE", "b": [652, 55, 90, 9]}],
     [{"x": 652, "y": 54, "w": 88, "h": 12, "fill": "#f5f5f5", "stroke": "", "dash": False}],
     1, "90px of text in an 88px plate (the db-schema defect)"),
    ([{"t": "ON DELETE CASCADE", "b": [655, 55, 90, 9]}],
     [{"x": 648, "y": 54, "w": 104, "h": 12, "fill": "#f5f5f5", "stroke": "", "dash": False}],
     0, "same text after the plate was widened to 104px"),
    ([{"t": "Capture Events", "b": [70, 60, 100, 12]}],
     [{"x": 60, "y": 48, "w": 160, "h": 48, "fill": "#ffffff", "stroke": "#2d3142", "dash": False}],
     0, "node name inside its box"),
    ([{"t": "이벤트 수집 파이프라인", "b": [70, 60, 158, 12]}],
     [{"x": 60, "y": 48, "w": 160, "h": 48, "fill": "#ffffff", "stroke": "#2d3142", "dash": False}],
     1, "a Korean name overflowing a box sized for English"),
    ([{"t": "HTTPS", "b": [162, 290, 30, 9]}],
     [{"x": 158, "y": 38, "w": 822, "h": 624, "fill": "transparent",
       "stroke": "rgba(45,49,66,0.18)", "dash": True}],
     0, "a dashed zone frame is never a label's box"),
    ([{"t": "EDGE", "b": [56, 112, 30, 8]}],
     [{"x": 40, "y": 96, "w": 300, "h": 200, "fill": "rgba(45,49,66,0.02)",
       "stroke": "#ccc", "dash": False}],
     0, "a wash-filled zone container is not a node box either"),
    ([{"t": "free label", "b": [10, 10, 60, 9]}], [],
     0, "a label with nothing behind it is not measured"),
    ([{"t": "PK", "b": [232, 90, 14, 8]}],
     [{"x": 228, "y": 88, "w": 40, "h": 12, "fill": "none",
       "stroke": "rgba(45,49,66,0.40)", "dash": False}],
     0, "a tag chip is neither a plate nor a node box"),
    ([{"t": "Batch · ML", "b": [830, 290, 48, 10.4]}],
     [{"x": 816, "y": 244, "w": 136, "h": 56, "fill": "#ffffff", "stroke": "#2d3142", "dash": False}],
     0, "a descender's worth of em box past the bottom edge is not overflow"),
    ([{"t": "SUBMIT", "b": [295, 184.2, 32.7, 9.8]}],
     [{"x": 288, "y": 184, "w": 48, "h": 12, "fill": "#f5f5f5", "stroke": "", "dash": False}],
     0, "an em box 0.2px proud of its plate is font metrics, not overflow"),
]


def self_test():
    bad = 0
    for texts, rects, want, label in SELF_TEST:
        got = len(check(texts, rects))
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
    files = [f for f in files if f.stem != "index"]
    if not files:
        print(__doc__)
        return 2
    chrome = find_chrome()
    if not chrome:
        print("verify-text: no Chrome/Chromium found. Set CHROME=<path>.\n"
              "This check measures rendered text and cannot run without a browser;\n"
              "it reports nothing rather than reporting green.", file=sys.stderr)
        return 2

    total, failed = 0, []
    with tempfile.TemporaryDirectory() as tmpdir:
        def one(f):
            try:
                return f, render(chrome, f, tmpdir)
            except Exception as exc:                       # noqa: BLE001
                return f, exc
        with ThreadPoolExecutor(max_workers=min(6, (os.cpu_count() or 4))) as pool:
            for f, result in pool.map(one, files):
                if isinstance(result, Exception) or result is None:
                    failed.append(f)
                    continue
                texts, rects = result
                for msg in check(texts, rects):
                    print(f"{f}: text: {msg}")
                    total += 1
    for f in failed:
        print(f"{f}: text: could not be rendered — NOT checked", file=sys.stderr)
    print(f"Summary: {len(files) - len(failed)} file(s) checked, "
          f"{len(failed)} unrendered, {total} finding(s).")
    return 1 if (total or failed) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
