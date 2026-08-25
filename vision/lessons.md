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

## A label plate must not land on the turn

**Broke.** `example-db-schema.html`: the `ON DELETE CASCADE` plate spans
x 648-736 at y 392-404. The sessions FK riser runs up x=716 and **ends at
y=400 — four pixels inside the plate**. The line went under the plate and never
came out; the connector read as two unrelated pieces. Three more instances
shipped: `import-drawio` (VERIFY covered 12px of a 20px riser),
`import-mermaid` (REQUEST landed on the corner), `dependency` (CYCLE started
exactly on it).

**Why it is not "plates must not cross lines".** A plate sitting *across* a
connector is the convention, not the bug — eleven shipped examples do it
(flowchart branch labels, state transitions, UML multiplicities) and all read
correctly. The eye bridges the gap because the stroke re-emerges on the far
side. The defect is the plate landing on the **end** of a run: the corner where
the connector turns away, or its endpoint.

**Rule.** A plate crossing a connector must leave stroke visible on **both**
sides: 6px minimum — §6 rule 2's own number, so a plate never leaves less clear
stroke than the rule already demands clear space. A tail at the arrowhead end
only has to be non-negative; the 8x6px marker is itself what the eye lands on,
so 4px of stroke plus a head reads fine.

Fixing one means moving the plate out of the turn, or moving the turn out from
under the plate. When the gutter has no lane wide enough for either — db-schema
packs three risers into 120px — move the label to the connector's other end.

**Guard.** `tools/verify-connectors.py`, PLATE check. Four positive self-tests
(the four real defects) against eight negatives (plates legitimately crossing
their own line).

---

## A checker that fires on the file you fixed is not thereby validated

**Broke.** The first plate check measured *coverage*: it flagged a plate wider
than ~80% of the run it labels. It fired on `example-deployment.html`, the file
whose broken arrow had just been fixed, so it looked validated and shipped.

Triaged against renders, its eight findings were **five false positives**:
plates offset above their run read perfectly no matter how wide they are, and a
plate twice the width of its run sitting in an empty gutter is not a defect at
all. Worse, the three it got right, it got right by accident — the actual
mechanism was the plate landing on a corner, which coverage does not measure.
And it never had a true positive to begin with: deployment's real defect was a
riser running 8px from the target box's border, a routing fault the coverage
number happened to correlate with.

Two plates with **identical** coverage geometry — `deployment`'s HTTPS:443 and
`import-mermaid`'s WRITES, both a plate exactly as long as its non-terminal run
— sat on opposite sides of the verdict. A measure that cannot separate those two
is not measuring the defect.

**Rule.** Before believing a new checker, open every finding as a picture, not
just the one that motivated it. A predicate whose false-positive rate is over
half is worse than nothing: it trains you to skim its output. Retire it rather
than tuning its threshold — the threshold was never the problem.

**Guard.** None; this is a review habit. Crop each finding's region from a real
render at 3x and look, as in the `PLATE` triage above.

---

## A plate sized to its text has no padding

**Broke.** db-schema's `ON DELETE CASCADE` plate was 88px wide; measured from a
render, the text ink spans 85.7px. In its original position that hid in open
gutter, but moved next to a table border the glyphs read as touching it. The
sibling `ON DELETE RESTRICT` plates use 112px for a *longer* string.

**Rule.** A mask plate is `text ink + 6px each side`, minimum. Geist Mono at
`font-size="8"` with `letter-spacing="0.06em"` runs about **5.05px per
character** — 17 characters need ~86px of ink and a ~104px plate. Measure, do
not estimate: the ink extent is recoverable from a render by scanning the pixel
row for the label colour.

**Guard.** None — no checker measures text. See *No checker measures text*.

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
That test is necessary, not sufficient — see *A checker that fires on the file
you fixed is not thereby validated* for a predicate that passed it and was
still measuring the wrong thing.

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
