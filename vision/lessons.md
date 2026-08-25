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

## A checker can be blind to a quarter of the corpus and still say green

**Broke.** `verify-connectors`, `verify-spacing` and `verify-geometry` all find
node boxes by reading `stroke="..."` off the tag. Five types — `dp-integration`,
`dp-security-matrix`, `it-state`, `process`, `loop` — style their nodes with a
class instead:

```html
<style>svg .node { fill:#fff; stroke:#2d3142 }</style>
<rect class="node" x="40" y="96" width="160" height="56"/>
```

Twenty files, every one a box-and-arrow diagram, in which not a single node was
ever looked at. All three checkers reported green on them for the same reason a
blank page reports green.

**Rule.** A checker that finds *nothing* in a file that plainly has something is
reporting its own blindness, not the file's health. Count what a detector matched,
not just what it flagged, and compare against a crude lower bound — a file with
forty rects and a dozen arrows has node boxes.

**Guard.** `tools/svgstyle.py` resolves classes, custom properties, `svg .cls`
descendants and compound selectors, and the three checkers run every rect through
it. It ships `--self-test`.

---

## The path parser read relative commands as absolute

**Broke.** `segments()` uppercased every command letter, so a relative
`a 8,8 0 0,0 -16,0` — the line-hop `example-dependency` uses — moved the cursor to
the absolute point `(-16, 0)`. Every segment after it was fiction. A rule-3 probe
reported 17 overlapping runs in that file, all at `y=0`, all imaginary; the real
geometry after each hop had never been examined by any check.

**Rule.** SVG path data is a grammar, not a token soup. Lowercase is relative;
`M` with extra coordinate pairs continues as an implicit `L`; `Z` returns to the
subpath start; and a path that ends on a corner fillet puts its arrowhead at the
end of the *curve*, several pixels past the last straight run — which is why
rule 4 could not see two arrowheads landing on the same point.

**Guard.** `tools/verify-connectors.py` ships `walk()` with per-command argument
counts, plus five self-tests covering relative commands, implicit repetition and
`Z`.

---

## `getBBox()` returns the em box, so vertical text checks are meaningless

**Broke.** The first version of `verify-text` compared a label's box to its
container on both axes. It reported **170 findings**, of which 165 were the same
thing: an 8px label measures ~10px tall — ascent to descent — whether or not the
string has a descender, so in a 12px plate it overhangs by 0.2px in *every*
example.

**Rule.** Measure text horizontally. Width is what a font, a size, a tracking and
a script actually change — Hangul advances about a full em where Latin advances
half — and it is the axis translation threatens. Height is set by `font-size`,
which translating does not change. A vertical tolerance would only have hidden
that the ruler was wrong.

**Guard.** `tools/verify-text.py`, `CHECK_VERTICALLY = False`, with the reasoning
recorded next to it.

---

## An iframe you navigate by `.src` hijacks the Back button

**Broke.** In the gallery, Back from the focus view showed a **white page** with
the toolbar still up. Assigning `.src` to an `<iframe>` that is already in the
document pushes a session history entry, so the browser's Back walked the
*frame's* history — reloading whatever that frame showed before, or
`about:blank` — while the overlay around it stayed exactly where it was.

**Rule.** Build a fresh `<iframe>` with its `src` already set and insert it; that
navigation replaces rather than pushes, and the page's history stays whatever the
page pushed itself. Then give the overlay real history: `pushState` on open,
`popstate` closes it, and everything done inside it `replaceState`s. Push
**before** the first render — a render that ends in `replaceState` would
otherwise stamp the overlay onto the entry the grid is sitting on, and Back would
land on a grid that thinks a diagram is open. Verified: opening a card, switching
language and stepping four types costs exactly one Back to leave.

**Guard.** None automatic. The check is manual and takes ten seconds: from a
*fresh* tab, open the overlay, press Back once (the grid returns), press Back
again (the page is gone). A tab you have already navigated a few times has its
own entries and will tell you nothing.

---

## A generator that duplicates instead of replacing fails silently

**Broke.** Twice while editing the gallery template, an index-based splice
(`t[:start] + new + t[end:]`) left the *old* block in place as well as the new
one. The page still rendered — masthead, rail, every thumbnail — but the script
had `const links` twice, so it threw on parse and **not one handler ever bound**.
Nothing on screen said so; the gallery just quietly stopped responding.

**Rule.** Edit generated templates with exact-match replacements that assert they
matched exactly once. Never splice by index: `str.index` finds the first
occurrence, and after one bad edit there are two.

**Guard.** `tools/build-gallery.py` runs `verify()` on its own output — token
counts for `<script>`, `<!doctype>` and each top-level `const`, plus `node
--check` on the extracted script when node is present, and it says so when it is
not.

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

## Retoning a shape is not redesigning it

**Broke.** Asked to give the `high-level` phase banner "a different visual form,
more refined, different colours," the first pass kept the chevron silhouette and
inverted its tonality — navy slabs and reversed-out labels became an ink wash
with hairline notches. Every colour changed. The verdict was
"형태가 크게 바뀌지않았네" — the form didn't really change.

**Why.** Tonality and form are separate axes, and a viewer reads form first. Ink
wash versus navy slab is a large change *in the file* and a small one *on the
page*, because the outline — five chevrons pointing right — was identical before
and after. A palette pass answers "different colours"; it does not answer
"different form."

**Rule.** When the ask names the *form*, change the silhouette, not the fill.
Here that meant separating the band into discrete chips and adding an explicit
arrow icon per boundary — direction stated outright instead of implied by a
notch. Test: trace the outline of both versions. If the tracings match, the form
did not change.

---

## Refining a heavy element is a contrast cut in disguise

**Broke.** The high-level phase banner was five opaque navy chevrons with
reversed-out paper labels. Retoning it to a light ink wash with ink labels —
the whole point of the change — dropped the highlighted labels to 3.98–4.47:1.
The design read better and had quietly fallen below WCAG AA. The version it
replaced was at 11.82:1.

**Why.** "More refined" and "more legible" pull in opposite directions here.
Reversed-out white on a dark slab is the highest-contrast combination
available; almost anything quieter is a step down. The failure is invisible by
eye, because 4.2:1 at `font-size=7` still *looks* perfectly readable — you only
find it by computing it.

**Rule.** Any pass that lightens, softens or "refines" an element that carried
text: compute the contrast before and after. If the before-number was high, the
burden is on the new design to still clear 4.5:1 — not to merely look fine.

**Guard.** `type-high-level.md` §7 #14. Nothing computes it automatically;
`verify-text.py` measures geometry, not colour.

---

## A tint under its own label is a ceiling, not a choice

**Broke.** The first amber picked for the `alert` token, `#a16207`, was chosen
by eye from a hue-interval argument. It measured 4.52:1 on paper — meaning it
could carry a highlight wash of exactly **zero** opacity and still pass AA. The
0.06 wash it was supposed to sit on put it at 3.98:1.

**Why.** When the highlight colour is used for both the wash *and* the label on
that wash, the two are not independent: raising the wash raises the background
luminance toward the label's own, and contrast collapses toward 1:1. The wash
opacity is therefore *derived* from the label's on-paper contrast, not picked
alongside it.

**Rule.** Solve, don't choose. For a label of colour `C` on a wash of `C` at
opacity `a` over paper `P`: composite `C` onto `P` at `a`, and take the largest
`a` that keeps `contrast(C, result) >= 4.5`. If that `a` is near zero, the
colour is too light — pick a darker one. `#8a5a12` (5.42:1 on paper) tops out at
0.06; `accent` (5.02:1) at 0.06; their dark-mode pairs at 0.075–0.10.

**Guard.** `style-guide.md` documents both tint ceilings as ceilings, and
`type-high-level.md` §2.2 states the derivation for any custom override.

---

## The one hue interval to avoid is the near-complement

**Broke.** `Security` chevrons and Identity bars used rust-red `#b85450`
alongside teal `#0f766e`. At slab size it was merely loud; at hairline weights
(1px notches, 7px labels) the two edges visibly buzz against each other.

**Why.** `#b85450` sits 173° from teal — within a few degrees of its exact
complement, the interval with maximum simultaneous contrast. That is the one
place on the wheel to avoid when both colours must coexist at small size.

**Rule.** A second concern colour goes at a split-complement interval, not the
complement. `alert` `#8a5a12` is 139° away. Check the angle before the hex.

**Note.** Eight other type references still specify `#b85450` for the same
role. Those are node and bar fills — larger areas, weaker effect — so they were
left alone and the inconsistency is recorded in `style-guide.md`.

---

## A stroke on the viewBox edge is half a stroke

**Broke.** The right strip spans `x = 972..1000` and the viewBox ends at 1000.
A 1px hairline centred on `x=1000` renders at half weight, because the outer
half is outside the canvas.

**Rule.** Inset any edge-hugging stroke by half its width — `999.5`, not `1000`.

**Guard.** `type-high-level.md` §7 #15.

---

## A logo is not an icon

**Symptom.** "아이콘이 의미하는 것이 분명한 것 이외 나머지는 의미가 불분명하다."
Every data-platform diagram labelled its nodes with the vendor's logo: NiFi's
teardrop, Trino's rabbit, MinIO's flamingo, Superset's two circles.

**Broke.** The node already spells the product name in bold 11px underneath. The
logo repeats that name in a shape a reader cannot decode, and spends the one
visual slot that could have said *what kind of thing this is*. A reader who knows
Trino learns nothing from the rabbit; a reader who doesn't learns nothing at all.
Meanwhile "query engine" — the fact that actually helps — went unsaid.

**Rule.** The icon says what the node *does*; the label says which product does
it. Brand marks only where the vendor **is** the subject: an inventory, a
comparison. Never as a node icon in an architecture or flow diagram.

**Guard.** style-guide.md → Icons; `verify-icons.py` MIX (a brand set is filled,
a function set is stroked, so reaching for one inside the other trips the style
check).

---

## Optical weight is not a size you can set

**Symptom.** "전체적으로 아이콘들이 정렬되어있지 않음." The obvious reading is a
coordinate bug, so the obvious fix is to normalise every icon's bounding box to a
common size and centre.

**Broke.** Normalising the boxes changed nothing. Rendered side by side at equal
size, NiFi's teardrop is a solid black mass and Airflow's pinwheel is a hairline
outline — same box, an order of magnitude apart in ink. No placement makes those
two read as one system.

**Rule.** Optical weight lives in the artwork, not in the geometry. Filled and
stroked marks cannot be balanced against each other at any size, so a diagram
picks one and stays there. When "align these" cannot be satisfied by moving
things, the misfit is in the assets.

**Test.** Render the candidates at one size on one row. If some read as blobs and
others as wireframes, no amount of coordinate work will fix it.

**Guard.** `verify-icons.py` MIX.

---

## A library that renders is not a library that is aligned

**Symptom.** `primitive-icons.md` opened with "a monochrome 24×24 icon library".
Ten of its icons were not 24×24 — `hop` was 440×506, `pentaho` had a fractional
origin at `47.71126037 35.82`.

**Broke.** Each snippet carried its own `viewBox`, so each rendered perfectly
standalone and in the gallery. Nothing looked wrong anywhere. But the documented
placement was `<g transform="translate(x,y) scale(s)">`, which inherits the
parent's user units — drop `hop` into a diagram that way and it draws 20×
oversized, straight across the page. The defect was invisible until used.

**Rule.** A contract stated in prose is a wish. Measure the corpus against it,
then encode it in a checker. Here: parse every `viewBox`, compute every drawn
bounding box with `getBBox()`, and compare against the documented grid.

**Guard.** `verify-icons.py` GRID/BOX, and `build-icons.py` generates the gallery
from the reference so the two cannot drift apart again.

---

## Align to the label, not to the box

**Symptom.** Every node icon in `example-high-level-vertical.html` sat 56px right
of centre. The first checker version compared the icon's centre to its enclosing
rect's centre — correct for nodes, and it caught these.

**Broke.** It also fired on every band and boundary, where a caption glyph sits
at the left edge while the band's title is centred hundreds of pixels away. Those
are not misaligned; they answer to a different rule.

**Rule.** A stacked icon shares its **label's** axis, not its box's. Anchoring to
the label makes the node case exact and drops the band case automatically — and
a band glyph then gets its own rule (centred on the bar's centre line). Order
matters: test band membership *first*, or a node label within reach claims the
band's glyph.

**Guard.** `verify-icons.py` AXIS and BAND, with self-tests for the left-anchored,
rotated, out-of-reach and band-adjacent cases that must **not** fire.

---

## Measure the file before you shrink it

**Symptom.** `primitive-icons.md` had grown to 117KB — more than twice SKILL.md,
the largest file in the skill. The obvious economies are the obvious ones: strip
the repeated `<svg>` wrapper, trim the descriptions, round the path coordinates.

**Broke.** The wrapper is 13% and the prose 2%. The real weight is 32 filled
brand silhouettes at 2,383 bytes each against 385 for a stroked icon — 72% of the
file in the category the skill's own rules say not to use as a node icon.
`sqlserver` alone is 9,368 bytes, and it renders as an illegible tangle.

**Rule.** Profile before optimising, in bytes, by category. The cheapest cut is
usually structural — here, splitting the file so an architecture diagram never
loads the brand marks — not compression of what is already small.

**Guard.** `build-icons.py` reads both files and still fails on duplicate artwork,
so the split cannot silently drop or double an icon.

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
