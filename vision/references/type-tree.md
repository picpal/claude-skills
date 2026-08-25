# Tree / Hierarchy

**Best for:** org charts, dependency trees, taxonomy, file trees, decision breakdowns, skill trees.

## Layout conventions
- Root at top, children fan out below (or root at left, children to right).
- Nodes are small labeled rectangles (`rx=6`), Pretendard 12px 600 name + optional Geist Mono 9px sublabel. Width 120–180px, height 40–52px.
- **Connectors are orthogonal (elbow-style), never diagonal.** Parent drops a short vertical line, then a horizontal bus connects siblings, then each child has a short vertical drop into its top edge. 1px muted stroke.
- Leaf indicator: thinner stroke (0.8) or different fill — OR let terminal position do the work.
- **Siblings sit on a uniform pitch = node width + gap, and the gap is never zero.** Lay a tier out as one evenly-spaced row across the whole viewBox rather than clustering each parent's children: with a 160px node and the 20px §7 minimum the pitch is 180, so five leaves span `4×180 + 160 = 880` and centre at `x = 60`. Two boxes that end and begin on the same coordinate draw as a single wide box with a line through it. Verify with `python3 tools/verify-spacing.py <file>`.
- **Don't try to centre each parent's children under that parent** once the pitch is fixed — tier-1 nodes are usually closer together than a two-child group is wide, so centring forces groups to overlap. The connectors carry parentage; the row carries rhythm.
- Node boxes need room for their contents: a box with a type chip needs 56px (chip + name) or 64px (chip + name + sublabel), not 48px. Grow the box rather than crowding the sublabel against the bottom border, and keep each tier's vertical centre fixed so the tier eyebrow labels stay put.
- Max depth: 4 (root + 3 tiers). Max breadth per level: 5.
- Accent on **one** node: root OR critical leaf. Not both.
- Draw connectors before nodes.

## Anti-patterns
- Tree 5+ levels deep on a single page (illegible — split).
- Nodes of wildly varying widths — pick 2 widths max.
- Diagonal connector lines.
- Skipped levels (parent connected to grandchild with no middle).
- Accent on root AND a leaf.
- Sibling boxes sharing a border (zero gap), or clustered per parent so that groups collide.

## Examples
- `assets/example-tree.html` — minimal light
- `assets/example-tree-dark.html` — minimal dark
- `assets/example-tree-full.html` — full editorial
