# Lessons

Defects found while building and maintaining this fork, and the rule each one
produced. **Read this before fixing a bug or editing the skill** — most entries
exist because something looked fixed and was not.

Entry format: what broke, why, the rule, and what now catches it. If an entry
has no guard, that class is still unguarded — be careful there.

---

## The linter trusts the Google Fonts URL

**Broke.** A bulk rename turned `family=Geist+Mono` into `family=Pretendard+Mono`
in all 149 assets. The pages requested a font that does not exist, silently fell
back, and `lint-skin.py --all` reported **0 findings**.

**Why.** `google_fonts_families()` derives the set of approved families *from the
URL's own `?family=` query*. Whatever the URL claims to load is treated as
loaded. Nothing fetches the stylesheet.

**Rule.** A green skin lint says nothing about whether a webfont resolves. After
any change touching a font stack, enumerate the URLs and eyeball them:

```bash
grep -roh "css2?family=[^\"']*" assets/ | sort | uniq -c
```

Only `Noto+Sans+KR` and `Geist+Mono` are legitimate here. **Never** add
`family=Pretendard` — it is not on Google Fonts.

**Guard.** None. The command above is the check.

---

## `Geist+Mono` is not `Geist Mono`

**Broke.** The lesson above, in detail. The font rename protected the CSS
spelling `Geist Mono` with a sentinel and used
`re.sub(r"(?<!\+)\bGeist\b(?! Mono)", "Pretendard", t)` for the rest. In
`family=Geist+Mono` the character before `Geist` is `=` and the one after is `+`,
so both guards passed and the URL was rewritten.

**Rule.** When renaming a font, the name appears in at least three spellings:
`'Geist Mono'` (CSS), `Geist+Mono` (URL), and `Geist mono` (prose). Protect all
of them, then re-scan for the *new* name in places it should never appear.

**Guard.** None.

---

## Replace colours on the RGB triplet, never the hex

**Broke.** The plan was to swap `rgba(235,108,54,0.08)`. The assets actually
contain **20 opacity spellings** of that colour, including leading-dot forms
(`,.08)`, `,.20)`, `,.07)`) that no `0.08` search matches. A hex-and-one-rgba
replacement would have left ~370 occurrences behind — orange fills under teal
strokes.

**Rule.** Match `235\s*,\s*108\s*,\s*54` (the triplet, opacity-agnostic) and
`#eb6c36` separately. Afterwards, grep for every form of the old value and
expect zero.

**Guard.** `lint-skin.py` checks each rgba triplet against the style-guide
table, so a missed one *does* surface — but only in files not on the baseline.

---

## `re.sub` replacement strings eat digits

**Broke.** `re.sub(pat, rf"\1{title}\2", t)` with `title = "2분기 제품 출시"`
raised `invalid group reference 12` — `\1` followed by `2` parses as group 12.

**Rule.** Use a lambda for any replacement built from data:
`re.sub(pat, lambda m: m.group(1) + title + m.group(2), t)`.

**Guard.** None. It fails loudly, which is why it is cheap.

---

## No checker measures text

**Broke.** Korean labels are roughly twice as wide per glyph as Latin, so
translating node names risks overflowing boxes sized for English.
`verify-geometry.py` parses `<rect>` attributes and never calls `getBBox()`; text
spilling out of its node is invisible to it, and to every other checker here.

**Rule.** After translating labels or changing a font, measure in a browser:
compare each `<text>`'s `getBBox()` against the node rect that contains it, with
8px padding. Keep mono technical values (ports, paths, SQL identifiers, package
names) in Latin — that is both real Korean practice and the reason the 39
translations produced zero overflow.

**Guard.** None shipped. The measurement snippet lives in this session's
transcript; re-derive it rather than trusting a green lint.

---

## A connector must not start on its own box's edge

**Broke.** `example-architecture.html` drew
`M 496,240 H 692 …` from the *centre of Astro Origin's top edge*. Since `y=240`
is the top border, the first 80px of the connector ran along the border and the
arrow appeared to sprout from the corner.

**Rule.** Exit a **side** port at a fanned attach point, then turn into the
destination's top/bottom edge. For N connectors on an edge of length L, attach
point k sits at `L·k/(N+1)`; keep them ≥12px apart.

**Guard.** `tools/verify-connectors.py` — flags any arrow-bearing segment that
runs collinear with a node border.

---

## Sibling boxes must never share a border

**Broke.** In `example-tree.html`, `polish` ended at x=220 and `critique` began
at x=220. The pair drew as one 320px box with a line through it. The other three
gaps in the same row were 20px, so it read as a layout bug rather than a style.

**Rule.** Lay a tier out on a uniform pitch = node width + gap, computed for the
whole row and centred in the viewBox. Do **not** centre each parent's children
under that parent: tier-1 nodes are usually closer together than a two-child
group is wide, so centring forces groups to collide. Connectors carry parentage.

**Guard.** `tools/verify-spacing.py` — TOUCH (gap ≤ 0) on both axes, CROWD
(gap < 20) on the row axis.

---

## Chip-bearing nodes need more height than 48px

**Broke.** Tree CAT nodes at h=48 held a type chip, a name and a sublabel. The
sublabel sat **1.5px** from the bottom border while the top had 8px.

**Rule.** A box with a chip needs 56px (chip + name) or 64px (chip + name +
sublabel). Grow the box; keep the row's vertical centre fixed so tier eyebrow
labels stay put, and move the connector endpoints with the box.

**Guard.** None. Measure content-block centre vs box centre with `getBBox()`;
±1px is the target.

---

## A label plate can break a connector two different ways

**Broke.** `example-deployment.html`: the `HTTPS:443` plate was 64px wide and the
horizontal run it labelled was 64px long — the plate covered 100% of it. The eye
left the Cloudflare box, hit a white plate, and picked the line up again further
right and above. Rerouted to exit Cloudflare's top edge, giving a 152px run for
the same 64px plate.

**Why two ways.** The `verify-connectors` plate check then surfaced 37 more, and
triage split them:

- **False (state ×4).** A plate sitting over a straight arrow that ends in its
  own arrowhead reads fine — the line is never occluded and the arrowhead gives
  the eye somewhere to land. Fixed by checking **non-terminal runs only**: a run
  that bends away is where the connector goes missing.
- **Real, different cause (db-schema).** The `ON DELETE CASCADE` plate does not
  cover its own run — it **intersects an unrelated vertical connector** and
  severs it. Same symptom, opposite mechanism.

**Rule.** Two distinct predicates, don't conflate them:
1. a plate must not cover most of a **non-terminal** run (the run gets too short
   to read);
2. a plate must not **intersect** any connector stroke, including ones it does
   not label.

**Guard.** `tools/verify-connectors.py` implements (1) only, on non-terminal
runs. (2) is unimplemented — the message it prints for db-schema names the wrong
cause. Outstanding: `db-schema`, `import-drawio`, `import-mermaid` (25 findings).

---

## Every new detector over-fires first

**Broke.** Twice.

`verify-connectors` initially reported 27 findings — all false. Bar-chart axis
baselines legitimately sit on the bars' bottom edge, and layer separators sit on
each layer's top edge. Discriminator: **only arrow-bearing elements are
connectors** (`marker-end` / `marker-start`).

`verify-spacing` initially reported 34 findings — all false. Every one was a
*vertical* stack: kanban's documented 12px card gap, story-map cards inside
release bands, high-level's full-width phase bars. Discriminator: **CROWD applies
to the row axis only**; vertical spacing is per-type grammar.

**Rule.** Before believing a new checker, run it against the file you already
fixed *and* its pre-fix copy. It must flag the second and clear the first. Then
write self-tests where the majority of cases are ones that must **not** fire.

**Guard.** Both checkers ship `--self-test` with more negative than positive
cases.

---

## The frontmatter limit is bytes, not characters

**Broke.** Adding Korean trigger words pushed the frontmatter to 962 characters —
under the 1024 limit — but **1040 bytes**. Hangul is 3 bytes per glyph in UTF-8.

**Rule.** Measure `len(fm.encode())`, not `len(fm)`. Keep headroom; the current
frontmatter is 840 bytes.

**Guard.** None.

---

## Interacting axes need mutual constraints

**Broke.** The gallery gained an EN/KO toggle beside the existing variant tabs.
Korean examples exist for minimal-light only, so KO + dark requested
`example-<type>-ko-dark.html`, which does not exist.

**Rule.** When two independent selectors compose into a filename, each must
disable the other's impossible values, and the note text must say which
constraint is active.

**Guard.** None.

---

## Copies of baselined files inherit their findings

**Broke.** `example-high-level-ko.html` reported a stale colour that its EN
original is excused from — the original is listed in
`tools/lint-skin-baseline.txt`, the copy was not.

**Rule.** When deriving a new file from an existing one, check whether the source
is on the baseline and add the derivative if so.

**Guard.** `lint-skin.py --all --baseline` surfaces it; per-file runs do too.

---

## Inherited defects worth knowing

Not introduced here; recorded so they are not mistaken for fork damage.

- **`&#NNNN;` reads as a colour.** `lint-skin.py`'s hex scanner reports
  `&#8594;` (→) as `color: #8594 is not in the style-guide palette`. Use literal
  characters, not numeric entities.
- **Connector rules 3/4/5 are unguarded upstream.** `verify-geometry` checks
  label-mask overlap only. `verify-connectors.py` here covers one member of that
  family (collinear-with-border); overlapping paths, shared attach points and
  transit behind non-endpoint boxes remain unchecked. Known violators upstream:
  `it-state` (zone-label detour), `dp-integration` (solid line behind the
  Orchestrator bar), `high-level` (two arrows into one attach point).
- **SKILL.md's own snippets break its §7 grid.** `font-size="7"` and `"9"` are
  off the 4px list. The style guide's per-role sizes are the intended reading.
- **`type-swimlane.md` has no layout grammar** — no lane height, no routing rule
  for the reject/return edge. Derive from §6/§7.
- **Linters hardcode paths.** Upstream they point at `skills/diagram-design/`;
  here they resolve `ROOT` as `Path(__file__).resolve().parent.parent`. Getting
  that depth wrong makes a checker silently lint the wrong tree and report green.
