#!/usr/bin/env python3
"""Rebuild assets/index.html — the gallery — from what is actually on disk.

The gallery is generated rather than hand-maintained because its two halves rot
apart otherwise: which variants a type ships is a fact about the filesystem, and
transcribing it by hand is how `example-<type>-ko-dark.html` ends up requested
for a file that was never rendered. Here the variant and language badges are
read from the directory, and the only thing an author writes is which family a
type belongs to.

Adding a type: drop `example-<type>.html` in assets/, add it to FAMILIES and give
it a label in LABEL, and run this. It asserts that every type on disk is filed
exactly once, so a forgotten entry fails the build instead of silently vanishing
from the gallery.

Usage:
    python3 tools/build-gallery.py           # writes assets/index.html
    python3 tools/build-gallery.py --check   # exit 1 if the file is out of date
"""

import html
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent

ASSETS = ROOT / "assets"
names = {p.stem for p in ASSETS.glob("example-*.html")}
info = {}
for t in sorted({re.sub(r"-(dark|full|ko)$", "", n)[len("example-"):] for n in names}):
    info[t] = {"dark": f"example-{t}-dark" in names,
               "full": f"example-{t}-full" in names,
               "ko":   f"example-{t}-ko" in names}

LABEL = {
 "architecture":"Architecture","high-level":"High-level stack","high-level-vertical":"High-level · parametric",
 "datalake":"Data lake","deployment":"Deployment","dp-integration":"DP integration",
 "it-state":"IT current state","layers":"Layer stack",
 "flowchart":"Flowchart","sequence":"Sequence","sequence-oauth":"Sequence · OAuth","state":"State machine",
 "swimlane":"Swimlane","process":"Process","data-flow":"Data flow","journey":"User journey",
 "loop":"Loop · flywheel","loop-terminal":"Loop · terminal",
 "tree":"Tree","org-chart":"Org chart","nested":"Nested","dependency":"Dependency graph",
 "uml-class":"UML class","er":"ER model","db-schema":"Database schema","medallion":"Medallion",
 "timeline":"Timeline","gantt":"Gantt","kanban":"Kanban","story-map":"Story map","wardley":"Wardley map",
 "quadrant":"Quadrant","quadrant-consultant":"Quadrant · consultant","radar":"Radar","polar":"Polar",
 "venn":"Venn","pyramid":"Pyramid · funnel","fishbone":"Fishbone",
 "bar":"Bar","line":"Line","ridgeline":"Line · ridgeline","slopegraph":"Line · slopegraph",
 "scatter":"Scatter","bubble":"Scatter · bubble","treemap":"Treemap","sankey":"Sankey",
 "dp-security-matrix":"DP security matrix",
 "import-drawio":"Import · draw.io","import-mermaid":"Import · Mermaid",
 "policy-trace-animated":"Policy trace · motion","queue-animated":"Fan-in queue · motion",
 "paved-road-animated":"Paved road · motion",
}

FAMILIES = [
 ("systems",   "Systems &amp; architecture", "How the parts sit together",
  ["architecture","high-level","high-level-vertical","datalake","deployment","dp-integration","it-state","layers"]),
 ("flow",      "Flow &amp; process", "What happens, in what order",
  ["flowchart","sequence","sequence-oauth","state","swimlane","process","data-flow","journey","loop","loop-terminal"]),
 ("structure", "Structure &amp; relationships", "What contains or points at what",
  ["tree","org-chart","nested","dependency","uml-class","er","db-schema","medallion"]),
 ("planning",  "Planning &amp; delivery", "Work laid out against time",
  ["timeline","gantt","kanban","story-map","wardley"]),
 ("analysis",  "Comparison &amp; analysis", "Positions, causes, overlaps",
  ["quadrant","quadrant-consultant","radar","polar","venn","pyramid","fishbone"]),
 ("quantity",  "Quantities", "Numbers given a shape",
  ["bar","line","ridgeline","slopegraph","scatter","bubble","treemap","sankey","dp-security-matrix"]),
 ("sources",   "Sources &amp; motion", "Redrawn imports, and diagrams that move",
  ["import-drawio","import-mermaid","policy-trace-animated","queue-animated","paved-road-animated"]),
]

assigned = [t for _, _, _, ts in FAMILIES for t in ts]
missing, dupes = set(info) - set(assigned), [t for t in assigned if assigned.count(t) > 1]
assert not missing, f"unassigned types: {sorted(missing)}"
assert not dupes, f"duplicated: {sorted(set(dupes))}"
assert set(assigned) <= set(info), f"unknown: {sorted(set(assigned) - set(info))}"

def card(t):
    i = info[t]
    badges = []
    if i["ko"]: badges.append('<i class="b">KO</i>')
    if not (i["dark"] or i["full"]): badges.append('<i class="b b-one">single</i>')
    return f'''          <button class="card" data-type="{t}" data-name="{html.escape(LABEL[t])}">
            <span class="shot" data-src="example-{t}.html"></span>
            <span class="cap"><span class="nm">{LABEL[t]}</span><span class="bs">{"".join(badges)}</span></span>
          </button>'''


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>vision · Diagram gallery</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet" />
<style>
  /* ---------------------------------------------------------------------
     Monotone light. The chrome carries no hue at all: every surface, rule
     and state is a neutral, so the only colour on screen belongs to the
     diagrams themselves. Selection reads as ink-on-paper inverted, never
     as a tint.
     --------------------------------------------------------------------- */
  :root {
    --paper:    #fbfbfa;
    --paper-2:  #f3f3f1;
    --paper-3:  #eaeae7;
    --ink:      #1a1a19;
    --muted:    #6b6b66;
    --soft:     #9c9c96;
    --rule:     rgba(26, 26, 25, 0.10);
    --rule-2:   rgba(26, 26, 25, 0.20);
    --sans: "Pretendard", "Noto Sans KR", -apple-system, system-ui, sans-serif;
    --mono: "Geist Mono", ui-monospace, "SFMono-Regular", monospace;
    --rail: 232px;
    --head: 3.25rem;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    font-family: var(--sans);
    background: var(--paper);
    color: var(--ink);
    height: 100vh;
    display: grid;
    grid-template-rows: var(--head) 1fr;
    overflow: hidden;
  }
  .mono { font-family: var(--mono); font-size: 0.6875rem; letter-spacing: 0.14em; text-transform: uppercase; }

  /* --- masthead ------------------------------------------------------- */
  .masthead {
    display: flex; align-items: center; gap: 1rem;
    padding: 0 1.25rem;
    border-bottom: 1px solid var(--rule);
    background: var(--paper);
  }
  .brand { display: flex; align-items: baseline; gap: 0.625rem; }
  .brand b { font-size: 1.0625rem; font-weight: 600; letter-spacing: -0.015em; }
  .brand span { color: var(--muted); font-size: 0.8125rem; }
  .masthead .spacer { flex: 1; }
  .masthead .stat { color: var(--soft); }

  /* --- shell ---------------------------------------------------------- */
  .shell { display: grid; grid-template-columns: var(--rail) 1fr; min-height: 0; }

  .rail {
    border-right: 1px solid var(--rule);
    padding: 1rem 0.75rem 0.75rem;
    display: flex; flex-direction: column; gap: 0.875rem;
    overflow-y: auto; min-height: 0;
    background: var(--paper);
  }
  .search { position: relative; }
  .search input {
    width: 100%; font: inherit; font-size: 0.8125rem;
    padding: 0.4375rem 0.625rem 0.4375rem 1.75rem;
    border: 1px solid var(--rule-2); border-radius: 5px;
    background: var(--paper); color: var(--ink);
  }
  .search input::placeholder { color: var(--soft); }
  .search input:focus { outline: none; border-color: var(--ink); }
  .search .glyph {
    position: absolute; left: 0.5rem; top: 50%; transform: translateY(-50%);
    color: var(--soft); font-family: var(--mono); font-size: 0.75rem; pointer-events: none;
  }
  .families { list-style: none; display: flex; flex-direction: column; gap: 1px; }
  .families a {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.375rem 0.5rem; border-radius: 4px;
    text-decoration: none; color: var(--muted); font-size: 0.8125rem; line-height: 1.25;
  }
  .families a em { margin-left: auto; font-style: normal; color: var(--soft); font-family: var(--mono); font-size: 0.6875rem; }
  .families a:hover { background: var(--paper-2); color: var(--ink); }
  .families a[aria-current="true"] { background: var(--ink); color: var(--paper); }
  .families a[aria-current="true"] em { color: var(--paper-3); }
  .railfoot { margin-top: auto; padding-top: 0.75rem; border-top: 1px solid var(--rule); color: var(--soft); font-size: 0.6875rem; line-height: 1.7; }
  .railfoot kbd {
    font-family: var(--mono); font-size: 0.625rem; background: var(--paper-2);
    border: 1px solid var(--rule); border-radius: 3px; padding: 0 0.25rem; color: var(--muted);
  }

  /* --- contact sheet -------------------------------------------------- */
  .sheet { overflow-y: auto; min-height: 0; padding: 1.25rem 1.5rem 4rem; scroll-behavior: smooth; }
  .fam { margin-bottom: 2.25rem; }
  .fam[hidden] { display: none; }
  .famhead {
    display: grid; grid-template-columns: 1fr auto; align-items: baseline;
    gap: 0.25rem 1rem; padding-bottom: 0.5rem; margin-bottom: 0.875rem;
    border-bottom: 1px solid var(--rule);
  }
  .famhead h2 { font-size: 0.9375rem; font-weight: 600; letter-spacing: -0.005em; }
  .famhead p { grid-column: 1; color: var(--soft); font-size: 0.75rem; }
  .famhead h2 { grid-column: 1; }
  .famhead .count { grid-column: 2; grid-row: 1 / span 2; align-self: center; font-family: var(--mono); font-size: 0.6875rem; color: var(--soft); }

  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(232px, 1fr)); gap: 0.875rem; }
  .card {
    display: flex; flex-direction: column; gap: 0.5rem;
    padding: 0; border: 0; background: none; cursor: pointer; text-align: left; font: inherit;
    border-radius: 6px;
  }
  .card[hidden] { display: none; }
  .shot {
    display: block; position: relative; overflow: hidden;
    aspect-ratio: 16 / 10; border: 1px solid var(--rule-2); border-radius: 6px;
    background: var(--paper-2);
  }
  /* The thumbnail is the real page, rendered at full width and scaled down —
     nothing is redrawn or exported, so a fixed example can never go stale here. */
  .shot iframe {
    position: absolute; top: 0; left: 0;
    width: 1280px; height: 800px; border: 0;
    transform-origin: 0 0; pointer-events: none;
    opacity: 0; transition: opacity 0.25s ease;
  }
  .shot iframe.in { opacity: 1; }
  .card:hover .shot, .card:focus-visible .shot { border-color: var(--ink); }
  .card:focus-visible { outline: none; }
  .card:focus-visible .cap .nm { text-decoration: underline; text-underline-offset: 2px; }
  .cap { display: flex; align-items: center; gap: 0.5rem; padding: 0 0.125rem; }
  .nm { font-size: 0.8125rem; font-weight: 500; }
  .bs { margin-left: auto; display: flex; gap: 0.25rem; }
  .b {
    font-family: var(--mono); font-style: normal; font-size: 0.5625rem; letter-spacing: 0.1em;
    color: var(--muted); border: 1px solid var(--rule-2); border-radius: 3px; padding: 0.0625rem 0.25rem;
  }
  .b-one { color: var(--soft); }
  .empty { color: var(--soft); font-size: 0.8125rem; padding: 2rem 0; }
  .empty[hidden] { display: none; }

  /* --- focus stage ---------------------------------------------------- */
  .stage {
    position: fixed; inset: 0; z-index: 20;
    background: var(--paper);
    display: grid; grid-template-rows: auto 1fr;
  }
  .stage[hidden] { display: none; }
  .stagebar {
    display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;
    padding: 0.625rem 1rem; border-bottom: 1px solid var(--rule);
  }
  .stagebar h2 { font-size: 0.9375rem; font-weight: 600; }
  .stagebar .idx { color: var(--soft); }
  .stagebar .spacer { flex: 1; }
  .seg { display: flex; border: 1px solid var(--rule-2); border-radius: 5px; overflow: hidden; }
  .seg button {
    font: inherit; font-size: 0.75rem; padding: 0.3125rem 0.625rem;
    background: var(--paper); color: var(--muted); border: 0; cursor: pointer;
    border-left: 1px solid var(--rule);
  }
  .seg button:first-child { border-left: 0; }
  .seg button[aria-checked="true"] { background: var(--ink); color: var(--paper); }
  .seg button:disabled { color: var(--soft); opacity: 0.45; cursor: not-allowed; }
  .seg button:not(:disabled):hover { background: var(--paper-2); }
  .seg button[aria-checked="true"]:hover { background: var(--ink); }
  .ghost {
    font: inherit; font-size: 0.75rem; padding: 0.3125rem 0.625rem;
    border: 1px solid var(--rule-2); border-radius: 5px;
    background: var(--paper); color: var(--muted); cursor: pointer; text-decoration: none;
  }
  .ghost:hover { border-color: var(--ink); color: var(--ink); }
  .note { color: var(--soft); font-size: 0.6875rem; }
  .note[hidden] { display: none; }
  .stagebody { min-height: 0; }
  .stagebody iframe { display: block; width: 100%; height: 100%; border: 0; background: var(--paper); }

  @media (max-width: 720px) {
    :root { --rail: 0px; }
    .rail { display: none; }
    .shell { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
  <header class="masthead">
    <span class="brand"><b>vision</b><span>Diagram gallery</span></span>
    <span class="spacer"></span>
    <span class="stat mono"><!--NTYPES--> types · <!--NFILES--> examples</span>
  </header>

  <div class="shell">
    <nav class="rail" aria-label="Families">
      <div class="search">
        <span class="glyph">/</span>
        <input id="q" type="search" placeholder="Filter types" aria-label="Filter types" autocomplete="off" />
      </div>
      <ul class="families" id="families">
<!--RAIL-->
      </ul>
      <div class="railfoot">
        <kbd>/</kbd> filter · <kbd>Enter</kbd> open<br />
        <kbd>←</kbd> <kbd>→</kbd> step · <kbd>Esc</kbd> back
      </div>
    </nav>

    <main class="sheet" id="sheet">
<!--SECTIONS-->
      <p class="empty" id="empty" hidden>No type matches that filter.</p>
    </main>
  </div>

  <div class="stage" id="stage" hidden role="dialog" aria-modal="true" aria-labelledby="stage-name">
    <div class="stagebar">
      <h2 id="stage-name">—</h2>
      <span class="idx mono" id="stage-idx"></span>
      <span class="spacer"></span>
      <span class="note" id="stage-note" hidden></span>
      <div class="seg" id="variant-seg" role="radiogroup" aria-label="Variant">
        <button data-variant="" role="radio" aria-checked="true">Light</button>
        <button data-variant="-dark" role="radio" aria-checked="false">Dark</button>
        <button data-variant="-full" role="radio" aria-checked="false">Editorial</button>
      </div>
      <div class="seg" id="lang-seg" role="radiogroup" aria-label="Language">
        <button data-lang="" role="radio" aria-checked="true">EN</button>
        <button data-lang="-ko" role="radio" aria-checked="false">KO</button>
      </div>
      <a class="ghost" id="stage-raw" href="#" target="_blank" rel="noreferrer">Open file</a>
      <button class="ghost" id="stage-close">Close</button>
    </div>
    <div class="stagebody" id="stage-body"></div>
  </div>

<script>
  const INFO = /*TYPEINFO*/;
  const LABEL = /*LABELS*/;
  const ORDER = [...document.querySelectorAll(".card")].map((c) => c.dataset.type);
  const state = { type: null, variant: "", lang: "" };

  /* --- thumbnails: mount only what is on screen ------------------------
     Fifty-two live pages at once is a lot of layout for a browser to hold,
     and most of them are off screen at any moment. Each frame is created
     when its card scrolls into view and never torn down after. */
  /* Assigning `.src` to an iframe already in the document pushes a session
     history entry, so browser Back walks the FRAME's history: the stage
     toolbar stays up while the frame reloads whatever it showed before, or
     about:blank. That is the white screen. An iframe inserted with its src
     already set navigates by replacement, so building a fresh element each
     time keeps history to exactly the entries this page pushes itself. */
  function frameInto(host, url, opts) {
    const el = document.createElement("iframe");
    el.title = (opts && opts.title) || "";
    if (opts && opts.decorative) {
      el.tabIndex = -1;
      el.setAttribute("aria-hidden", "true");
    }
    if (opts && opts.onload) el.addEventListener("load", () => opts.onload(el), { once: true });
    el.src = url;
    host.replaceChildren(el);
    return el;
  }
  const fit = (el) => {
    const box = el.parentElement.getBoundingClientRect();
    if (box.width) el.style.transform = `scale(${box.width / 1280})`;
  };
  const mount = (shot) => {
    if (!shot || shot.dataset.mounted) return;
    shot.dataset.mounted = "1";
    fit(frameInto(shot, shot.dataset.src, {
      decorative: true,
      onload: (f) => f.classList.add("in"),
    }));
  };
  const io = new IntersectionObserver(
    (entries, obs) => entries.forEach((e) => {
      if (!e.isIntersecting) return;
      mount(e.target.querySelector(".shot"));
      obs.unobserve(e.target);
    }),
    { root: document.getElementById("sheet"), rootMargin: "400px 0px" },
  );
  document.querySelectorAll(".card").forEach((c) => io.observe(c));
  addEventListener("resize", () => document.querySelectorAll(".shot iframe").forEach(fit));

  /* --- filter ---------------------------------------------------------- */
  const q = document.getElementById("q");
  const empty = document.getElementById("empty");
  q.addEventListener("input", () => {
    const needle = q.value.trim().toLowerCase();
    let shown = 0;
    document.querySelectorAll(".fam").forEach((fam) => {
      let visible = 0;
      fam.querySelectorAll(".card").forEach((card) => {
        const hit =
          !needle ||
          card.dataset.name.toLowerCase().includes(needle) ||
          card.dataset.type.includes(needle);
        card.hidden = !hit;
        if (hit) { visible += 1; mount(card.querySelector(".shot")); }
      });
      fam.hidden = visible === 0;
      shown += visible;
    });
    empty.hidden = shown > 0;
  });

  /* --- rail: highlight the family currently under the reader ----------- */
  /* An observer reports which sections *touch* a band, and the previous family
     keeps touching it long after its heading has scrolled past, so the rail sat
     a whole section behind the reader. What the rail should name is the last
     heading to have crossed the top — a position question, not an intersection
     one. */
  const links = [...document.querySelectorAll("#families a")];
  const sheet = document.getElementById("sheet");
  const fams = [...document.querySelectorAll(".fam")];
  function spy() {
    // A quarter down the reading area: a heading that has reached the top of
    // the sheet is what the reader is on, and a fixed pixel offset gets that
    // wrong on short windows.
    const line = sheet.getBoundingClientRect().top + sheet.clientHeight * 0.25;
    let current = null;
    for (const f of fams) {
      if (f.hidden) continue;
      if (f.getBoundingClientRect().top <= line || !current) current = f;
    }
    if (!current) return;
    links.forEach((a) =>
      a.setAttribute("aria-current", String(a.dataset.family === current.dataset.family)));
  }
  sheet.addEventListener("scroll", spy, { passive: true });
  addEventListener("resize", spy);
  spy();

  /* --- focus stage ----------------------------------------------------- */
  const stage = document.getElementById("stage");
  const body = document.getElementById("stage-body");
  const nameEl = document.getElementById("stage-name");
  const idxEl = document.getElementById("stage-idx");
  const noteEl = document.getElementById("stage-note");
  const rawEl = document.getElementById("stage-raw");
  let opener = null;

  /* Korean examples ship for the light variant only, so the two axes
     constrain each other: choosing KO forces Light, and choosing Dark or
     Editorial rules KO out. Without this the frame would ask for
     example-<type>-ko-dark.html, which does not exist. */
  function render() {
    const info = INFO[state.type];
    const single = !info.dark && !info.full;
    if (single) state.variant = "";
    if (!info.ko) state.lang = "";
    if (state.lang === "-ko") state.variant = "";

    document.querySelectorAll("#variant-seg button").forEach((b) => {
      const v = b.dataset.variant;
      b.disabled = (v === "-dark" && !info.dark) || (v === "-full" && !info.full) ||
                   (v !== "" && state.lang === "-ko");
      b.setAttribute("aria-checked", String(v === state.variant));
    });
    document.querySelectorAll("#lang-seg button").forEach((b) => {
      b.disabled = b.dataset.lang === "-ko" && (!info.ko || state.variant !== "");
      b.setAttribute("aria-checked", String(b.dataset.lang === state.lang));
    });

    noteEl.hidden = false;
    if (single) noteEl.textContent = "이 예시는 minimal light 하나만 제공합니다";
    else if (!info.ko) noteEl.textContent = "이 타입은 아직 EN만 제공합니다";
    else if (state.variant !== "") noteEl.textContent = "KO는 minimal light에서만 볼 수 있습니다";
    else noteEl.hidden = true;

    const src = `example-${state.type}${state.lang}${state.variant}.html`;
    frameInto(body, src, { title: `${LABEL[state.type]} preview` });
    rawEl.href = src;
    nameEl.textContent = LABEL[state.type];
    idxEl.textContent = `${ORDER.indexOf(state.type) + 1} / ${ORDER.length}`;
    history.replaceState({ stage: state.type }, "");
  }

  /* Back closes the stage, which is what a full-screen overlay should do — and
     what the browser was doing to the frame instead. Opening pushes one entry;
     everything done inside the stage replaces it, so a type stepped through ten
     times still costs a single Back to leave. */
  function show(type, from) {
    if (from) opener = from;
    state.type = type;
    state.variant = "";
    state.lang = "";
    stage.hidden = false;
    render();
    document.getElementById("stage-close").focus();
  }
  function openStage(type, from) {
    // Push BEFORE rendering: render() ends with replaceState, so rendering
    // first would stamp the stage onto the entry the grid sits on, and Back
    // would land on a grid entry that believes a diagram is open.
    if (stage.hidden) history.pushState({ stage: type }, "");
    show(type, from);
  }
  function hideStage() {
    stage.hidden = true;
    body.replaceChildren();
    if (opener) { opener.focus(); opener = null; }
  }
  function step(delta) {
    const i = ORDER.indexOf(state.type);
    show(ORDER[(i + delta + ORDER.length) % ORDER.length]);
  }

  addEventListener("popstate", (e) => {
    const wanted = e.state && e.state.stage;
    if (wanted && INFO[wanted]) show(wanted);
    else if (!stage.hidden) hideStage();
  });

  document.querySelectorAll(".card").forEach((card) =>
    card.addEventListener("click", () => openStage(card.dataset.type, card)));
  document.getElementById("stage-close").addEventListener("click", () => history.back());
  document.getElementById("variant-seg").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (b && !b.disabled) { state.variant = b.dataset.variant; render(); }
  });
  document.getElementById("lang-seg").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (b && !b.disabled) { state.lang = b.dataset.lang; render(); }
  });

  addEventListener("keydown", (e) => {
    if (!stage.hidden) {
      if (e.key === "Escape") { e.preventDefault(); history.back(); }
      if (e.key === "ArrowRight") { e.preventDefault(); step(1); }
      if (e.key === "ArrowLeft") { e.preventDefault(); step(-1); }
      return;
    }
    if (e.key === "/" && document.activeElement !== q) { e.preventDefault(); q.focus(); q.select(); }
    if (e.key === "Escape" && document.activeElement === q) { q.value = ""; q.dispatchEvent(new Event("input")); q.blur(); }
  });
</script>
</body>
</html>
"""

sections, railitems = [], []
for key, title, blurb, ts in FAMILIES:
    railitems.append(f'          <li><a href="#f-{key}" data-family="{key}">{title}<em>{len(ts)}</em></a></li>')
    cards = "\n".join(card(t) for t in ts)
    sections.append(f'''      <section class="fam" id="f-{key}" data-family="{key}">
        <header class="famhead">
          <h2>{title}</h2>
          <p>{blurb}</p>
          <span class="count">{len(ts)}</span>
        </header>
        <div class="grid">
{cards}
        </div>
      </section>''')

out = (TEMPLATE.replace("<!--RAIL-->", "\n".join(railitems))
          .replace("<!--SECTIONS-->", "\n".join(sections))
          .replace("/*TYPEINFO*/", json.dumps(info, separators=(",", ":"), sort_keys=True))
          .replace("/*LABELS*/", json.dumps({t: LABEL[t] for t in info}, separators=(",", ":"), sort_keys=True))
          .replace("<!--NTYPES-->", str(len(info)))
          .replace("<!--NFILES-->", str(len(names))))

def verify(page):
    """Structural checks on the generated page.

    Both times this generator broke, it broke by *duplicating* a block rather
    than replacing it — which produces a page that still looks plausible and a
    script that dies on `const` redeclaration before a single handler binds.
    Nothing on screen says so: the grid renders, and only the interactive parts
    quietly do nothing. So the invariants are asserted here rather than trusted.
    """
    for token, want in (("<!doctype html>", 1), ("<script>", 1), ("</script>", 1),
                        ("const links", 1), ("const io =", 1), ("function frameInto", 1)):
        got = page.count(token)
        assert got == want, f"{token!r} appears {got}x, expected {want}"

    script = re.search(r"<script>(.*?)</script>", page, re.S)
    assert script, "no script block"
    node = shutil.which("node")
    if node:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
            fh.write(script.group(1))
            path = fh.name
        try:
            proc = subprocess.run([node, "--check", path], capture_output=True, text=True)
            assert proc.returncode == 0, f"generated JS does not parse:\n{proc.stderr}"
        finally:
            os.unlink(path)
    else:
        print("note: node not found — generated JS was not syntax-checked", file=sys.stderr)


verify(out)

target = ASSETS / "index.html"
if "--check" in sys.argv:
    current = target.read_text() if target.exists() else ""
    if current == out:
        print(f"gallery is up to date — {len(info)} types, {len(FAMILIES)} families")
        sys.exit(0)
    print("gallery is out of date; run: python3 tools/build-gallery.py", file=sys.stderr)
    sys.exit(1)
target.write_text(out)
print(f"wrote {target} — {len(info)} types, {len(names)} examples, {len(FAMILIES)} families")
