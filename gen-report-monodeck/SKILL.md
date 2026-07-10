---
name: gen-report-monodeck
description: >-
  Use when the user wants a structured report rendered as a monochrome editorial
  "deck" HTML page — review reports, revision/plan reports, retrospectives,
  before/after comparisons, audits, or decision write-ups. Triggers on Korean
  requests like '보고서 html', '리포트 만들어줘', '덱 스타일 보고서', '검토 리포트',
  '수정계획 리포트', '분석 리포트 html', '모노크롬 보고서', '슬라이드 형식 보고서',
  '흑백 에디토리얼 보고서', 'as-is to-be 보고서', 'before after 리포트' and English
  equivalents. For static, publishable reports — NOT interactive dashboards or tools.
---

# Mono Deck Report

## Overview

Turn a structured written report into a black-and-white **editorial deck** — a
vertical stack of full-bleed "slides" alternating ink (#121212) and paper (#fff)
grounds, set in condensed uppercase display type with Korean body text. The look
is a print keynote, not a web app: hairline rules, tabular numerals, zero color
accents. Publish via the Artifact tool.

**Core principle:** conclusion first, monochrome always, self-contained HTML.

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

## Slide catalog

Pick and order slides to fit the content; alternate paper/ink. Every type exists
as a block in `assets/template.html`.

| Slide | Use for |
|---|---|
| **Cover** | Title page — top meta row + large bottom display title + one-line subtitle. Usually `.dark`. |
| **Contents** | Numbered table of contents; `.d` column holds an English category tag. |
| **2-up summary** | Conclusion-first split: two contrasting columns (e.g. 강점 / 구멍, keep / fix). |
| **Action** | The workhorse. 4 quadrants — 문제 / 결정 / 변경 / 완료기준 — with a big priority number and a `.tag`. One slide per action item. |
| **Before / After + Outcome** | Two-column before/after list, then a 3-up stat row (`.outcome` big figures) for target metrics. |
| **As-Is / To-Be table** | Section-by-section change mapping. MUST stay inside `.tablewrap` (`overflow-x:auto`) with `min-width` so it scrolls, never squashes, on mobile. |
| **Sequence** | 4 ordered steps (Step 1–4) for execution order / timeline. |
| **Closing** | One large display statement + footer meta. Usually `.dark`. |

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
   what changed (Before/After + table), in what order (Sequence). Decide the
   ink/paper alternation.
2. **Copy the template.** Duplicate `assets/template.html` into the scratchpad
   (or the user's requested path) and fill every `{{PLACEHOLDER}}`. Delete
   unused slide blocks; duplicate Action blocks per item; keep the `<style>`
   block verbatim.
3. **Publish.** Save the filled file, then call the **Artifact** tool with its
   path, a stable `<title>`, a one-line `description`, and a monochrome-friendly
   `favicon` emoji. Redeploy to the same path to update in place.

## Common mistakes

- Adding a color accent "just for emphasis" → breaks the system; use weight,
  rules, or an ink slide instead.
- Long Korean sentences inside `.display` → condensed caps only reads well for
  short English/numeric strings.
- Dropping the table out of `.tablewrap` → horizontal overflow breaks mobile.
- Sequential numbers on unordered items → implies a false priority.
- Pulling a web font or CDN → blocked by Artifact CSP, page renders unstyled.
