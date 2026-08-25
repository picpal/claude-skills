# Style Guide

**The single source of truth for colors, typography, and tokens.** Every diagram draws from this — not from hex values inlined in other reference files. If you want to change the visual skin of vision, change this file.

Default skin is a cool editorial palette — white-smoke paper, jet-black ink, deep-teal accent, blue-slate muted. It's designed to look good out of the box; swap these values (or run [`onboarding.md`](onboarding.md)) and every new diagram inherits the new skin without touching any type-specific logic.

To generate your own from a website URL, see [`onboarding.md`](onboarding.md).

---

## Tokens

### Semantic roles

Every token is referred to by **semantic role**, not by its hex value. Type references (`type-*.md`) and SKILL.md say `accent`, not `#0f766e`.

| Role | Purpose | Default (light) | Default (dark) |
|---|---|---|---|
| `paper` | Page background, default node fill | `#f5f5f5` (white-smoke) | `#2d3142` (jet-black) |
| `paper-2` | Diagram container bg, secondary fill | `#ececec` | `#393e53` |
| `ink` | Primary text, primary stroke | `#2d3142` (jet-black) | `#f5f5f5` (white-smoke) |
| `muted` | Secondary text, default arrow stroke | `#4f5d75` (blue-slate) | `#bfc0c0` (silver) |
| `soft` | Sublabels, boundary labels | `#7a8399` | `#8e98ac` |
| `rule` | Hairline borders | `rgba(45,49,66,0.12)` | `rgba(245,245,245,0.12)` |
| `rule-solid` | Stronger borders, baselines | `#bfc0c0` (silver) | `rgba(191,192,192,0.25)` |
| `accent` | Focal / 1–2 max per diagram | `#0f766e` (deep-teal) | `#14b8a6` |
| `accent-tint` | Fill for accent-bordered boxes | `rgba(15,118,110,0.08)` | `rgba(20,184,166,0.10)` |
| `link` | HTTP/API calls, external arrows | `#4c1d95` | `#a78bfa` |
| `alert` | A cross-cutting concern that must read apart from `accent` — Security / Identity columns | `#8a5a12` (deep-ochre) | `#d9a441` |
| `alert-tint` | Wash behind an `alert` label | `rgba(138,90,18,0.06)` | `rgba(217,164,65,0.10)` |

> **Why `alert` is ochre, not red:** a second concern colour has to be legible next to `accent`, not fight it. The earlier rust-red `#b85450` sat 173° from teal — a near-complement, the one interval that visibly vibrates at hairline weights. `#8a5a12` sits 139° away (a split complement) and matches `accent` for contrast: 5.42:1 on paper light, 5.73:1 dark. Both tints above are *ceilings*, solved rather than picked — an `alert`/`accent` label sits on its own tint, so the tint may only be as strong as still leaves that label at WCAG AA. `accent-tint` drops to `rgba(15,118,110,0.06)` / `rgba(20,184,166,0.075)` when it is used that way (see `type-high-level.md` §2.2).

> **Migration note:** `alert` currently lands only in `type-high-level.md`. Eight other type references (`data-flow`, `process`, `medallion`, `it-state`, `dp-integration`, `dp-security-matrix`, `import-drawio`, and the examples built from them) still name rust-red `#b85450` for the same Security / Identity / Governance role. Those uses are node and bar *fills*, where the vibration against `accent` is far less pronounced than it is at hairline weights — so they are not wrong today, just inconsistent. Prefer `alert` in new work.

> **Brand palette source:** this skin keeps four of the five upstream brand colors — `jet-black #2d3142`, `silver #bfc0c0`, `white-smoke #f5f5f5`, `blue-slate #4f5d75` — and replaces the fifth (atomic-tangerine) with `deep-teal #0f766e`. Teal sits only 43° from blue-slate in hue, so `link` was moved out of the blue family to `#4c1d95` (violet, 88° from accent) to keep the three arrow markers distinguishable at 8×6px. `accent` clears WCAG AA on paper (5.02:1 light, 5.18:1 dark); the upstream tangerine did not (2.86:1).

> **Note:** The pre-baked example HTML files in `assets/` were built under an earlier skin. Regenerating them against the current `style-guide.md` is a v5.1 task. New diagrams the skill produces will use the tokens above.

### Inversion rule (light → dark)

Any `rgba(28,25,23, X)` in light becomes `rgba(250,247,242, X)` in dark. Same opacities, RGB flipped. The accent gets a slight hue-shift brighter to read on dark paper.

### Series palette (multi-series chart types only)

A small set of desaturated, editorial-tone colors for chart types that genuinely need to distinguish multiple overlapping entities (currently: **radar**). The "1-focal" rule still holds — `accent` is reserved for the focal series; the palette below covers the rest.

| Token | Light | Dark | Notes |
|---|---|---|---|
| `series-1` | `#7c8f6f` (sage) | `#9caf8f` | Non-focal series |
| `series-2` | `#5e7a9b` (dusty-blue) | `#82a0c0` | Non-focal series |
| `series-3` | `#b8915a` (mustard) | `#d3ad7a` | Non-focal series |
| `series-4` | `#9c6b50` (rust-brown) | `#b88670` | Non-focal series |
| `series-5` | `#6e6479` (slate) | `#8d8298` | Non-focal series |

Fills sit at `0.18` opacity light, `0.22` dark; strokes use the full color. **Don't backfill these tokens to non-chart types** — architecture, swimlane, etc. continue to use muted-ink variants. The series palette is opt-in for diagrams where overlapping shapes demand distinguishable color, not a license to add color elsewhere.

### Terminal skin (opt-in alternate)

A self-contained palette for the terminal-window primitive (see [primitive-terminal.md](primitive-terminal.md)) — a CLI-chrome register for dev-tool posts and technical social cards. It does not replace the default skin above and isn't affected by onboarding; it's a second, fixed skin you opt into per-diagram.

| Token | Hex | Purpose |
|---|---|---|
| `terminal-page` | `#0a0a0a` | Page background behind the window |
| `terminal-paper` | `#141414` | Window body, node fill |
| `terminal-bar` | `#1b1b1b` | Titlebar strip |
| `terminal-border` | `#2b2b2b` | Window border, hairlines |
| `terminal-ink` | `#f5f5f5` | Primary text, primary stroke (same white-smoke as default `ink`) |
| `terminal-muted` | `#9a9a9a` | Secondary text, sublabels, ring stroke |
| `terminal-soft` | `#5c5c5c` | Tertiary — inactive dots, spokes |
| `terminal-accent` | `#ff5a36` | The one accent — focal station, prompt sign, active dot |
| `terminal-accent-tint` | `rgba(255,90,54,0.12)` | Fill for accent-bordered boxes |

**1-accent rule still holds.** Everything that isn't `terminal-ink` or `terminal-muted`/`terminal-soft` should be `terminal-accent` — never introduce a second hue.

---

## Typography

| Role | Family | Size | Weight | Usage |
|---|---|---|---|---|
| `title` | Pretendard, Noto Sans KR | 1.75rem | 600 | Page H1 |
| `node-name` | Pretendard, Noto Sans KR | 12px | 600 | Human-readable labels |
| `sublabel` | Geist Mono, Noto Sans Mono CJK KR | 9px | 400 | Port, protocol, URL, field type |
| `eyebrow` | Geist Mono, Noto Sans Mono CJK KR | 7–8px | 500, tracked 0.18em, uppercase | Type tags, axis labels |
| `arrow-label` | Geist Mono, Noto Sans Mono CJK KR | 8px | 400, tracked 0.06em | Arrow annotations |
| `callout` | Pretendard *italic* | 14px | 400 | Editorial asides only |

### Font stack

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

**Load-bearing rule:** Mono is for *technical* content (ports, commands, URLs, field types). Names and the page title go in Pretendard. Italic Pretendard is reserved for annotation callouts (see [primitive-annotation.md](primitive-annotation.md)). **Never JetBrains Mono** as a blanket "dev" font.

**Pretendard is not on Google Fonts and cannot be linked** — every remote host except `fonts.googleapis.com` is rejected by `tools/lint-skin.py`, and `@import` / non-fragment `url()` are banned, so self-hosting and data-URI embedding are closed too. Pretendard therefore renders only where it is installed locally; `Noto Sans KR` is the loaded webfont fallback and is what CI-baked screenshots will show. Always name both, in that order.

---

## Stroke, radius, spacing

| Token | Value | Use |
|---|---|---|
| `stroke-thin` | `0.8` | Tag-box outlines, leaf nodes |
| `stroke-default` | `1` | Most strokes |
| `stroke-strong` | `1.2` | Emphasis strokes |
| `radius-sm` | `4` | Small tags |
| `radius-md` | `6` | Node boxes |
| `radius-lg` | `8` | Containers, rings |
| `grid` | `4` | Every coord, size, and gap is divisible by 4 (hard rule) |

---

## Node type → treatment

Semantic role combinations — reference these by name in type specs.

| Type | Fill | Stroke |
|---|---|---|
| `focal` (1–2 max) | `accent-tint` | `accent` |
| `backend` | `#ffffff` (white) | `ink` |
| `store` | `ink @ 0.05` | `muted` |
| `external` | `ink @ 0.03` | `ink @ 0.30` |
| `input` | `muted @ 0.10` | `soft` |
| `optional` | `ink @ 0.02` | `ink @ 0.20` dashed `4,3` |
| `security` | `accent @ 0.05` | `accent @ 0.50` dashed `4,4` |

---

## Icons

Full library and per-icon snippets: [primitive-icons.md](primitive-icons.md).
Enforced by [`tools/verify-icons.py`](../tools/verify-icons.py).

**The icon says what the node *does*; the label says which product does it.** A node already
carries the product name in bold, so a brand mark on the same node repeats that name in a shape
most readers cannot decode, and spends the one visual slot that could have said what kind of thing
this is. Use `transform`, `query`, `bucket`, `schedule`, `dashboard`, `notebook` — not the vendor's
logo. Brand marks are for diagrams where the vendor *is* the subject: a stack inventory, a
tool comparison. Never in an architecture or flow diagram.

**One icon style per diagram.** Stroked and filled marks cannot be optically balanced against each
other — a filled silhouette is a solid mass, a hairline mark of the same box carries a fraction of
the ink. The stroked categories (Compute · People · Network · Data · Analytics · Kubernetes ·
Action · DevOps) are interchangeable; the filled ones (Brand · Data stack · Language · Statistical
tools) are a separate set.

| | rule |
|---|---|
| viewBox | exactly `0 0 24 24` |
| size | **24** in a node, **20** in a caption, legend, or band; square, always |
| placement | nested `<svg x= y=>`, never `<g transform>` |
| stacked on a label | `icon_cx == label_x` — the icon hangs off the label's axis |
| in a band | left edge, inset **12**, centred on the band's centre line |
| stroke | `1.5`, `currentColor` or an explicit token; `fill="none"` |
| colour | `ink` normally, `accent` on the focal node, `muted` for a caption glyph |

---

## Customizing the skin

Four options:

1. **Run onboarding** — see [`onboarding.md`](onboarding.md). Drop a URL; the skill extracts the palette + fonts and rewrites this file.
2. **Edit by hand** — change the hex values in the tables above. Run the pre-output taste gate afterward to verify the accent still reads as "focal" against the new paper color.
3. **Brand handoff** — paste your existing design-token JSON into a new section here and map its tokens to the semantic roles above.
4. **Client profiles** — save and switch named skins, or bind one to a project, using [`profiles.md`](profiles.md).

### Constraints (don't break these)

- **Contrast**: `ink` must hit WCAG AA on `paper`. `muted` must hit AA on `paper` for 11px+ text.
- **One accent**: pick one color for `accent`. Two accents erases the focal signal.
- **No rainbow palette**: if your brand ships 8 colors, pick 3 (paper, ink, accent). The rest become `muted` variants.
- **Sans + mono**: two families, not more. This fork collapsed the upstream serif/sans split into Pretendard alone so that Korean titles set in the same face as Korean labels. Title and body separate by size and weight (1.75rem/600 vs 12px/600), not by family.
- **Paper is warm-neutral, not pure white**: pure white turns the design sterile. Pick a cream, bone, or light grey with a hint of warmth.
- **Dot pattern is optional, not default**: the 22×22 dot pattern is an opt-in "dotted paper" variant (good for long-form editorial hero diagrams). The default background is a clean `paper` fill, no pattern. When the pattern is enabled, it should sit at ~10% opacity of `ink` on `paper` — visible but quiet.
- **Container is clean by default**: the diagram sits directly on the page paper, no secondary container background or border. A framed variant (`paper-2` bg + `rule` border + 8px radius + padding) is available as an opt-in for card-heavy layouts, but don't reach for it by default — the extra chrome fights the figure.
