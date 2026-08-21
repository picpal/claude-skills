---
name: gen-report-monodeck
description: >-
  Use when the user wants a structured report rendered as a monochrome editorial
  "deck" HTML page — review reports, revision/plan reports, retrospectives,
  before/after comparisons, audits, or decision write-ups. Triggers on Korean
  requests like '보고서 html', '리포트 만들어줘', '덱 스타일 보고서', '검토 리포트',
  '수정계획 리포트', '분석 리포트 html', '모노크롬 보고서', '슬라이드 형식 보고서',
  '흑백 에디토리얼 보고서', 'as-is to-be 보고서', 'before after 리포트', '다이어그램 포함
  보고서', '플로우/시퀀스 다이어그램 리포트' and English equivalents. For static,
  publishable reports — NOT interactive dashboards or tools.
---

# Mono Deck Report

## Overview

Turn a structured written report into a black-and-white **editorial deck** — a
vertical stack of full-bleed "slides" alternating ink (#121212) and paper (#fff)
grounds, set in condensed uppercase display type with Korean body text. The look
is a print keynote, not a web app: hairline rules, tabular numerals, zero color
accents. Flows, comparisons, and timelines are drawn, not just written — the
template ships a monochrome visual grammar (charts, diagrams, mock screens)
that follows the same hairline/ink system. Publish via the Artifact tool.

**Core principle:** conclusion first, monochrome always, self-contained HTML,
and a visual for every mechanism prose alone can't carry.

## When to use

- Review / audit / QA reports (검토·감사·리뷰)
- Revision or implementation **plans** (수정계획·실행계획)
- Retrospectives, post-mortems (회고)
- **Before/After** or **As-Is/To-Be** comparisons
- Decision records and proposals with a clear ordered set of actions

## When NOT to use

- Interactive dashboards, live data, filters, charts you can click → this is a
  static document; use a real app or the `dataviz` skill instead.
- Anything needing color to carry meaning (status colors, category hues) — this
  theme is deliberately monochrome. Do not add accent colors.
- Casual prose answers that don't have report structure — just answer in chat.

## Design tokens (use these exact values)

**Page (the scrolling ground behind slides) — dual-token theme-aware:**
- Light `--page-bg:#e9e7e2`, `--page-muted:#7c7a75`
- Dark `--page-bg:#1a1a1a`, `--page-muted:#8d8b86`
- Pattern: set light defaults in `:root`, override in
  `@media (prefers-color-scheme: dark)`, then hard override for both
  `:root[data-theme="dark"]` and `:root[data-theme="light"]` so the Artifact
  viewer's theme toggle always wins.

**Slides are deliberately fixed** (they do not follow the viewer theme) and
alternate for rhythm:
- Paper slide: `background:#fff`, text `#141414`
- Ink slide (`.slide.dark`): `background:#121212`, text `#f4f3ef`
- Each slide sets scoped vars: `--rule` (hairline: `#e3e1dc` paper / `#2e2e2e`
  ink), `--muted` (`#71706b` / `#9b9994`), `--chipbg` for inline `code`.

**Never introduce a color accent.** The whole system is grayscale; contrast and
rules do the work color usually does.

## Typography rules

- **English display** (titles, big numbers): `"Helvetica Neue"` weight **800**,
  `font-stretch:condensed`, `text-transform:uppercase`,
  `letter-spacing:-.015em`, tight line-height. Class `.display`.
- **Korean body**: `"Apple SD Gothic Neo","Pretendard","Noto Sans KR"`,
  line-height 1.7, 15px base.
- **Eyebrow** (section kicker): 11px, uppercase, `letter-spacing:.18em`, muted.
- **Numbers**: `font-variant-numeric:tabular-nums` (class `.num`) on every
  figure, date, and counter so columns align.
- Keep display type English/short; keep explanatory prose Korean. Mixing a long
  Korean string into `.display` breaks the condensed-caps look.

## Visual grammar (monochrome charts & diagrams)

Color normally separates series; here **fill texture** does. Three fills, fixed
semantics, everywhere:

| Fill | Meaning |
|---|---|
| **Solid** (`background:currentColor`) | 현재 / 확정 / After / DONE |
| **Hatch** (`.hatch` 45° 빗금) | 비교군 / 잠정 / Before / WIP |
| **Open** (hairline outline only) | 미완 / 보조 / TODO·BLOCKED |

Rules:

- **A visual must earn its place.** 3+ step flow or actor interaction → diagram;
  numeric comparison → bars; schedule → gantt; priority argument → 2×2 matrix.
  If a sentence says it faster, write the sentence. Never decorate.
- **Legend required** (`.viz-legend`) the moment hatch coexists with solid OR
  open fills on one slide — texture semantics are not self-evident.
- **Exception — SVG diagrams:** an outlined box in a diagram is a neutral node
  frame, not a TODO marker; the fill table governs data marks (bars, chips,
  gantt), while in diagrams only hatch carries meaning (예외/보조/activation) —
  which is why a hatched diagram still needs the legend — its `<figcaption>`
  stating what the hatch means (예: "빗금 막대는 활성 구간") satisfies it.
- Everything inherits `currentColor`, so every component works unchanged on
  paper and ink slides. Never hard-code a gray, never add a hue.
- **Delta direction comes from the glyph** (`▲`/`▼`), never from color.
- **No mermaid.** Its rendered output ignores this design system; hand-drawn
  SVG and the CSS components below are the only sanctioned visuals.

**Inline SVG (sequence / branching flow):** 1 viewBox unit = 1px, always. Each
`<svg>` carries inline `min-width`/`max-width` **equal to its viewBox width**;
growing a diagram means raising viewBox width AND those two values together.
That keeps labels at 12px and hairlines at 1px on every device — a wide
diagram scrolls inside `.diagramwrap` (the `.tablewrap` pattern) instead of
shrinking, and a narrow one never stretches. Stroke/fill `currentColor`,
arrowheads via `<marker>`, hatch via `<pattern>`. Give every `<svg>`
`role="img"` + `aria-label` and a `<figcaption>`. **Def ids must be
page-unique** — duplicating a diagram means renaming
`seqarr`/`seqhatch`/`flowarr`/`flowhatch` copies.

### Insert blocks (copy into any content slide)

Small components live in the template's **`#viz-library` slide** — copy what
you need into content slides, then **delete `#viz-library` and its quicknav
entry**. Shipping it is a defect.

| Block | Use for | Typical host slide |
|---|---|---|
| `.barchart` | 수치 비교 (paired: hatch=Before, solid=After). 라벨은 짧게(한글 ~4자 + ` · Before/After` 접미사까지가 예산) — 단위·수치는 값 칼럼에 | Before/After |
| `.delta` | outcome 큰 숫자의 변화 방향·폭 | Before/After stats |
| `.meter` | 진행률·커버리지 얇은 게이지 | Action 완료기준 cell |
| `.chip` (solid/hatch/outline) | 상태 표기 DONE/WIP/BLOCKED | Action, tables |
| `.scale` (■■■□□) | 심각도·우선순위 레벨 | Summary, Action |
| `.callout` | 핵심 문장 풀쿼트 — **덱 전체에 1개** | Summary 근처 |
| `.diffwrap` | 코드 변경 (add=굵은 좌측 룰, del=해칭) | As-Is/To-Be 대신 |

## Slide catalog

Pick and order slides to fit the content; alternate paper/ink. Every type exists
as a block in `assets/template.html`. **Alternation governs**: the template's
`.dark` assignments are only a starting point — after deciding the final slide
order, reassign `.dark` so grounds alternate, keeping Cover and Closing dark.
The Contents TOC lists 4–6 **thematic groups**, not one row per slide.

| Slide | Use for |
|---|---|
| **Cover** | Title page — top meta row + large bottom display title + one-line subtitle. Usually `.dark`. |
| **Contents** | Numbered table of contents; `.d` column holds an English category tag. |
| **2-up summary** | Conclusion-first split: two contrasting columns (e.g. 강점 / 구멍, keep / fix). |
| **Action** | The workhorse. 4 quadrants — 문제 / 결정 / 변경 / 완료기준 — with a big priority number and a `.tag`. One slide per action item. |
| **Before / After + Outcome** | Two-column before/after list, then a 3-up stat row (`.outcome` big figures) for target metrics. |
| **As-Is / To-Be table** | Section-by-section change mapping. MUST stay inside `.tablewrap` (`overflow-x:auto`) with `min-width` so it scrolls, never squashes, on mobile. |
| **Sequence** | 4 ordered steps (Step 1–4) for execution order / timeline. |
| **Matrix** | 2×2 priority frame (예: 영향도×노력). Item numbers mirror the Action slides so ordering reads as coordinates. |
| **Timeline** | Gantt rows — bar position via inline `left/width %`; solid=확정, hatch=잠정; axis labels below. |
| **Flow** | Process flow. Linear → CSS `.flow` boxes+arrows (`.now`=현재 단계 마커); branching → the SVG figure. Keep one, delete the other. |
| **Sequence Diagram** | Actor lifelines + messages (inline SVG). Solid arrow=요청, dashed=응답, hatch bar=activation. |
| **Screen Mock** | Mono wireframe (창 크롬+버튼·입력) with numbered `.marker`s mapped to an event list — "이 버튼을 누르면 무슨 일이 일어나는가". Static only. |
| **Viz Library** | Insert-block source. Copy blocks out, then **delete this slide** — never ship it. |
| **Closing** | One large display statement + footer meta. Usually `.dark`. |

## Quick nav (fixed slide navigator)

Every deck ships with the `<nav class="quicknav">` block from the template — a
fixed bottom-right list that follows scroll; clicking an entry jumps to that
slide (smooth-scroll, gated behind `prefers-reduced-motion`).

- **One `<li>` per slide, in final slide order.** After deleting/duplicating
  slide blocks, rebuild the nav list so every `href="#id"` matches an existing
  `<section id>` and no slide is missing. Renumber `01/02/…` to the final order.
- Duplicated Action slides get unique ids: `action-1`, `action-2`, …
- Labels are short English uppercase words (`Cover`, `Action 01`,
  `Before/After`) — same rule as display type, no long Korean strings.
- Keep the inline `<script>` at the bottom verbatim — a deterministic scrollspy
  highlights the active slide: a clicked entry wins immediately, and on scroll
  the active slide is recomputed from the 35%-viewport reading line (bottom
  slide when pinned at max scroll). Do NOT replace it with an
  IntersectionObserver band — narrow bands mis-highlight neighbors depending on
  viewport height and go silent when a click can't scroll (clamped at page
  bottom). Inline JS is CSP-safe; only external scripts are blocked.
- Mobile (`≤720px`) hides labels and shows numbers only — preserve that
  override.

## Authoring principles

- **Numbering encodes meaning.** Use 01/02/03 only when it's a real order or
  priority. If items are unordered, use symbols (`＋`, `—`) instead so a reader
  never infers a ranking you didn't intend.
- **Conclusion first.** The summary slide states the verdict before the detail
  slides justify it — mirror the report's own top-down logic.
- **Self-contained (Artifact CSP).** No external fonts, CDNs, scripts, or remote
  images — a strict CSP blocks them. Everything inline; rely on system font
  stacks only. Do not add `<!DOCTYPE>`, `<html>`, `<head>`, or `<body>` — the
  Artifact wrapper supplies them; the file starts at `<title>`.
- **Mobile responsive.** The `@media (max-width:720px)` block already collapses
  every grid to one column; preserve it. Keep tables in `.tablewrap`.
- **Respect `prefers-reduced-motion`.** The slide rise animation is already
  gated behind `@media (prefers-reduced-motion: no-preference)`; don't add
  unconditional motion.
- Keep prose tight — a slide holds a claim and its support, not paragraphs.

## Procedure

1. **Design the structure first.** Map the report's content onto slides: which
   items are actions (one Action slide each), what the verdict is (summary),
   what changed (Before/After + table), in what order (Sequence). **Then map
   the visuals**: every multi-step flow, actor interaction, numeric comparison,
   schedule, or priority argument gets the matching visual component — a deck
   with zero visuals on flow-heavy content is as wrong as one decorated with
   unearned charts. Decide the ink/paper alternation.
2. **Copy the template.** Duplicate `assets/template.html` into the scratchpad
   (or the user's requested path) and fill every `{{PLACEHOLDER}}`. Delete
   unused slide blocks; duplicate Action blocks per item; copy needed insert
   blocks out of `#viz-library`, then delete that slide; keep the `<style>`
   block verbatim.
3. **Sync the quick nav.** Rebuild the `.quicknav` list to mirror the final
   slide set: one entry per remaining slide, sequential numbering, every
   `href` pointing at a real `<section id>`. Keep the inline script.
4. **Publish.** Save the filled file, then call the **Artifact** tool with its
   path, a stable `<title>`, a one-line `description`, and a monochrome-friendly
   `favicon` emoji. Redeploy to the same path to update in place. (If the user
   asked for a raw HTML file only, stop after saving — publishing is the
   default, not a hard requirement.)

## Common mistakes

- Adding a color accent "just for emphasis" → breaks the system; use weight,
  rules, or an ink slide instead.
- Long Korean sentences inside `.display` → condensed caps only reads well for
  short English/numeric strings.
- Dropping the table out of `.tablewrap` → horizontal overflow breaks mobile.
- Sequential numbers on unordered items → implies a false priority.
- Pulling a web font or CDN → blocked by Artifact CSP, page renders unstyled.
- Quick nav out of sync with slides → dead `#anchor` links or missing entries;
  rebuild the list whenever slides are deleted, duplicated, or reordered.
- Copied Action slides sharing one id → anchors all jump to the first copy;
  ids must be unique (`action-1`, `action-2`, …).
- Deleting the quicknav block or its inline script → the deck loses navigation;
  the nav is a required part of every deck.
- Shipping `#viz-library` in the final deck → it's a parts bin, not content;
  copy blocks out and delete it (and its nav entry).
- Hatch mixed with solid or open fills on one slide without `.viz-legend` →
  texture semantics are unreadable; add the legend (SVG diagrams included).
- Mermaid, or color inside SVG/charts → breaks the design system; only
  currentColor CSS components and hand-drawn SVG.
- `<svg>` min/max-width out of sync with its viewBox width → the diagram
  rescales (wider viewBox = smaller type, 5-actor labels shrink to 7px);
  keep the three values identical and let `.diagramwrap` scroll.
- Duplicated SVG `<defs>` ids (`seqarr`, `flowhatch`, …) after copying a
  diagram → markers render from the wrong def; rename per copy.
- Visuals as decoration — a chart restating a 2-item list, a flow for 2 steps →
  delete it; the visual must carry something prose can't.
