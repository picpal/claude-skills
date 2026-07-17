---
name: gen-report-monodeck-ppt
description: >-
  Use when the user wants a report or presentation rendered as an actual
  navigable slide deck — one full-viewport slide at a time, paging left/right
  like a real PPT deck, advanced with arrow keys, on-screen buttons, or swipe
  — instead of a scrolling page. Triggers on Korean requests like 'ppt 형태
  html', '슬라이드로 넘기는 html', '좌우로 넘어가는 html', '발표자료 html',
  '피치덱 만들어줘', '한 장씩 넘어가는 리포트', '키노트 스타일 html', '프레젠테이션
  슬라이드' and English equivalents like 'presentation deck html',
  'slide-by-slide html', 'pptx-style slides', 'keynote deck'. Shares the
  monochrome editorial look of gen-report-monodeck but pages like a deck
  instead of scrolling like a document — use gen-report-monodeck instead when
  the user just wants "a report" with no slide/presentation framing.
---

# Mono Deck PPT

## Overview

Same black-and-white editorial system as **gen-report-monodeck** (ink/paper
grounds, condensed uppercase display type, hairline rules, zero color) but
delivered as a real **paged deck**: one full-viewport slide on screen at a
time, paging left-to-right like an actual PPT deck, advanced with arrow keys,
click buttons, or swipe — not a page you scroll through top to bottom.

**REQUIRED BACKGROUND:** Read `gen-report-monodeck` first. It owns the shared
design tokens (colors, typography, slide catalog, authoring principles). This
skill only documents what changes for paging — it does not repeat them.

**Core principle:** identical monochrome system, but the deck advances one
screen at a time, left to right, instead of scrolling.

## When to use

- Explicit slide/presentation framing: 발표자료, 피치덱, 키노트 스타일, "슬라이드로
  넘겨보는", "PPT처럼" — same content types as gen-report-monodeck (review,
  plan, retro, before/after, decision record) requested as a deck, not a page.

## When NOT to use

- No explicit slide/presentation framing → use `gen-report-monodeck` (a
  scrolling page reads faster for most reports; don't force paging).
- Anything gen-report-monodeck already excludes: interactive dashboards, live
  data, or content that needs color to carry meaning.

## What's different from gen-report-monodeck

The slide catalog, color tokens, and typography rules are unchanged — copy
this skill's `assets/template.html`, not the base skill's, and everything
below layers on top of that shared system:

- **Paged left/right, not stacked.** `.deck` is a horizontal
  `scroll-snap-type:x mandatory` row (`width:100dvw`, `flex-direction:row`);
  each `.slide` is `flex:0 0 auto; width:100dvw` with `scroll-snap-align:start`
  — slides advance left-to-right like a real PPT deck instead of flowing down
  the page. CSS scroll-snap alone makes it swipeable/pageable even with no JS.
- **Edge-to-edge, no page gutter.** The `.deck-caption` meta row from the base
  template is gone; slides render full-bleed with no visible page background.
- **Content sits in its own `.slide-inner` wrapper.** Every slide's content
  goes inside one `<div class="slide-inner">` (instead of directly in
  `<section class="slide">`) so it can be width-capped and vertically centered
  independent of the full-bleed slide background. Cover and closing slides add
  `class="slide-inner cover"` / `class="slide-inner closing"` to span the full
  slide height edge-to-edge instead of centering.
- **A HUD, not a caption row.** A fixed slide counter (`01 / 08`) top-left,
  edge-mounted prev/next buttons (left/right edge, vertically centered), and a
  bottom-center progress-dot row overlay every slide. They use
  `mix-blend-mode:difference` so the same white-drawn HUD reads correctly on
  both paper and ink slides without per-slide contrast logic — never
  hand-color the HUD per slide. There is deliberately **no fullscreen
  button**: Artifact renders in a sandboxed iframe that generally withholds
  the Fullscreen API, so `requestFullscreen()` silently fails there — a button
  for it is dead UI, not a missing feature.
- **Inline vanilla JS drives navigation**: arrow/Page/Home/End keys, the
  prev/next buttons, and dot clicks all call one `go(index)` that does
  `slide.scrollIntoView({inline:'start', block:'nearest'})`. It reads slide
  count from the DOM (`document.querySelectorAll('.slide').length`) — never
  hardcode a total.
- **Motion respects `prefers-reduced-motion`**: smooth scroll and the slide
  rise animation both fall back to instant/none.

## Procedure

1. Design the structure exactly as in gen-report-monodeck: map content onto
   the slide catalog, decide ink/paper alternation, order slides.
2. Copy **this skill's** `assets/template.html` into the scratchpad (or the
   user's requested path). Fill every `{{PLACEHOLDER}}`. Delete unused slide
   blocks; duplicate Action blocks per item. Keep `<style>` and the closing
   `<script>` verbatim — do not hand-edit the nav logic per deck.
3. Publish via the **Artifact** tool: save the file, call Artifact with its
   path, a stable `<title>`, a one-line `description`, and a monochrome
   favicon emoji. Redeploy to the same path to update in place.

## Common mistakes

- Everything gen-report-monodeck already warns about (color accents, long
  Korean strings in `.display`, dropping tables out of `.tablewrap`,
  sequential numbers on unordered items) applies here too.
- Hand-styling the HUD per slide instead of relying on `mix-blend-mode` →
  it'll look right on one ground and vanish on the other.
- Letting `.deck` scroll on both axes → fights the click/keyboard pager; the
  deck only ever pages horizontally, and a slide's own content scrolls
  vertically *inside itself* if it's taller than the screen. A wide
  `.tablewrap` table nested inside the horizontally-paging deck will
  legitimately eat a trackpad swipe when the pointer is directly over it —
  that's normal nested-scroll behavior, not a bug to route around.
- Hardcoding the slide total in the counter or dots instead of deriving it
  from `document.querySelectorAll('.slide')` → drifts the moment a slide is
  added or removed.
- Pulling in a reveal.js-style CDN library for the paging → blocked by
  Artifact CSP; this is pure CSS scroll-snap plus ~30 lines of vanilla JS,
  already in the template.
- Adding a fullscreen button back → `requestFullscreen()` is silently
  unavailable inside the Artifact iframe sandbox; it was removed on purpose,
  not an oversight.
