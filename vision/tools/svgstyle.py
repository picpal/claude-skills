#!/usr/bin/env python3
"""Resolve CSS-class styling on SVG elements so the geometry checkers can see it.

Roughly a quarter of this skill's examples style their nodes with classes and
custom properties rather than presentation attributes:

    <style>:root{--side-stroke:#7a8399} .side-node{fill:var(--side-fill);stroke:var(--side-stroke)}</style>
    <rect class="side-node" x="40" y="96" width="160" height="56"/>

A checker that reads `stroke="..."` off the tag finds nothing there, decides the
file has no node boxes, and reports green on a file it never examined. That is
how `dp-integration`, `it-state`, `process`, `loop` and `dp-security-matrix` —
five box-and-arrow types, twenty files — passed every geometry check without one
of their nodes ever being looked at.

`effective(text)` returns a function mapping a tag's attribute dict to the same
dict with `fill` / `stroke` / `stroke-dasharray` filled in from the stylesheet.
CSS wins over presentation attributes, which is what SVG does.

Only flat selectors are handled — `.cls`, `tag.cls`, and comma lists of those.
Anything with a combinator, pseudo-class or attribute selector is skipped, and
so are declarations inside `@media` / `@supports` blocks, whose value depends on
a viewing condition this cannot know.
"""

import re

STYLE_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)
COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)
AT_RULE_RE = re.compile(r"@[\w-]+[^{;]*", re.S)
VAR_RE = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*?)\s*)?\)")
# `.cls`, `rect.cls`, `.a.b` (element must carry both), and the same prefixed by
# `svg ` — the dominant idiom here, and safe because everything measured is inside
# the svg. A descendant whose ancestor is a class (`.card .a`) is still skipped:
# nothing here can know the element sits inside it.
SIMPLE_SEL = re.compile(r"^(?:svg\s+)?(?:[\w-]+)?((?:\.[\w-]+)+)$")

INHERITED = ("fill", "stroke", "stroke-dasharray", "stroke-width", "stroke-opacity")


def _declarations(body):
    out = {}
    for part in body.split(";"):
        if ":" not in part:
            continue
        prop, _, value = part.partition(":")
        out[prop.strip().lower()] = value.strip()
    return out


def _strip_at_rules(css):
    """Drop `@media` / `@supports` blocks whole — their values depend on a viewing
    condition a static checker cannot know, so neither branch may be trusted."""
    out, i = [], 0
    while i < len(css):
        m = AT_RULE_RE.search(css, i)
        if not m:
            out.append(css[i:])
            break
        out.append(css[i:m.start()])
        j = css.find("{", m.end() - 1)
        if j < 0:                                    # @import / @charset — no block
            i = css.find(";", m.end())
            i = len(css) if i < 0 else i + 1
            continue
        depth, k = 0, j
        while k < len(css):
            if css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        i = k + 1
    return "".join(out)


def _rules(text):
    """([(class set, declarations)], {custom property: value}), in source order."""
    rules, variables = [], {}
    for block in STYLE_RE.findall(text):
        block = _strip_at_rules(COMMENT_RE.sub("", block))
        for selector, body in RULE_RE.findall(block):
            decls = _declarations(body)
            for name in (s.strip() for s in selector.split(",")):
                if name in (":root", "html"):
                    variables.update({k: v for k, v in decls.items() if k.startswith("--")})
                    continue
                m = SIMPLE_SEL.match(name)
                if m:
                    rules.append((frozenset(m.group(1).lstrip(".").split(".")), decls))
    return rules, variables


def _expand(value, variables, depth=0):
    """Substitute `var(--x)` repeatedly — a fallback may itself hold a var()."""
    for _ in range(8):
        if "var(" not in value:
            break
        def sub(m):
            name, fallback = m.group(1), m.group(2)
            if name in variables:
                return variables[name].strip()
            return fallback if fallback is not None else ""
        expanded = VAR_RE.sub(sub, value).strip()
        if expanded == value:
            break
        value = expanded
    return value


def effective(text):
    """Return `apply(attrs) -> attrs` merging class styling into a tag's attributes."""
    rules, variables = _rules(text)
    resolved = [(names, {k: _expand(v, variables) for k, v in decls.items()
                         if k in INHERITED})
                for names, decls in rules]
    resolved = [(names, decls) for names, decls in resolved if decls]
    if not resolved:
        return lambda attrs: attrs

    # Class-only selectors, so specificity is just how many classes they name;
    # ties break on source order. `.node.focal` therefore beats `.node` wherever
    # it appears in the sheet.
    order = sorted(range(len(resolved)), key=lambda i: (len(resolved[i][0]), i))

    def apply(attrs):
        have = set(attrs.get("class", "").split())
        if not have:
            return attrs
        merged = dict(attrs)
        for i in order:
            names, decls = resolved[i]
            if names <= have:
                for prop, value in decls.items():
                    if value:
                        merged[prop] = value     # CSS beats the presentation attribute
        return merged

    return apply


SELF_TEST = [
    ('<style>:root{--s:#7a8399}.side{fill:none;stroke:var(--s)}</style>',
     {"class": "side"}, {"stroke": "#7a8399", "fill": "none"},
     "class + custom property resolves"),
    ('<style>.a{stroke:#111}</style>', {"class": "a", "stroke": "#eee"},
     {"stroke": "#111"}, "CSS beats the presentation attribute"),
    ('<style>svg .node { fill:#fff; stroke:#2d3142 }</style>', {"class": "node"},
     {"stroke": "#2d3142"}, "`svg .cls` — the dominant idiom in this corpus"),
    ('<style>svg .node{stroke:#2d3142}svg .node.focal{stroke:#0f766e}</style>',
     {"class": "node focal"}, {"stroke": "#0f766e"},
     "a compound selector beats the single-class rule"),
    ('<style>svg .node.focal{stroke:#0f766e}</style>', {"class": "node"},
     {}, "a compound selector needs every class it names"),
    ('<style>svg .node.focal{stroke:#0f766e}svg .node{stroke:#2d3142}</style>',
     {"class": "node focal"}, {"stroke": "#0f766e"},
     "specificity wins over source order"),
    ('<style>.a{stroke:#111}.a{stroke:#222}</style>', {"class": "a"},
     {"stroke": "#222"}, "later rule wins"),
    ('<style>.a,.b{fill:#f5f5f5}</style>', {"class": "b"},
     {"fill": "#f5f5f5"}, "comma list"),
    ('<style>rect.z{stroke:#333}</style>', {"class": "z"},
     {"stroke": "#333"}, "tag-qualified class"),
    ('<style>:root{--p:#f5f5f5}.m{fill:var(--q,var(--p))}</style>', {"class": "m"},
     {"fill": "#f5f5f5"}, "var fallback chain"),
    ('<style>@media (prefers-color-scheme:dark){.a{stroke:#fff}}</style>',
     {"class": "a", "stroke": "#111"}, {"stroke": "#111"},
     "declarations inside @media are ignored"),
    ('<style>.wrap .a{stroke:#f00}</style>', {"class": "a", "stroke": "#111"},
     {"stroke": "#111"}, "descendant selectors are skipped"),
    ('<style>.a{stroke:#111}</style>', {"stroke": "#eee"},
     {"stroke": "#eee"}, "an element with no class is untouched"),
    ('<rect stroke="#eee"/>', {"stroke": "#eee"},
     {"stroke": "#eee"}, "a file with no stylesheet is untouched"),
]


def self_test():
    bad = 0
    for css, attrs, expect, label in SELF_TEST:
        got = effective(css)(attrs)
        ok = all(got.get(k) == v for k, v in expect.items())
        bad += not ok
        print(f"  [{'ok' if ok else 'FAIL'}] {label}"
              + ("" if ok else f": expected {expect}, got {got}"))
    print(f"self-test: {len(SELF_TEST) - bad}/{len(SELF_TEST)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    import sys
    sys.exit(self_test())
