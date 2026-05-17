# Lint Workflow

## Checks

### Orphan Notes

Notes with no meaningful links to Sources, Maps, Objects, Projects, or Reviews.

### Merge Candidates

Notes with similar names, aliases, definitions, or repeated summaries.

### Stale Claims

Claim notes whose review date has passed or whose confidence is low without follow-up.

### Outdated Decisions

Decision notes whose review condition or date has been reached.

### Missing Evidence

Claim, Insight, or Decision notes without Source links.

### Broken Links

Links to notes, headings, embeds, or source references that no longer resolve.

### Unresolved Questions

Question notes that remain open and have no next exploration step.

## Lint Report Format

```markdown
---
type: lint_report
created: "{{date}}"
---

# Lint Report - {{date}}

## Orphan Notes

- [[note]]: reason

## Merge Candidates

- [[note-a]] + [[note-b]]: similarity

## Stale Claims

- [[claim]]: review reason

## Decisions Needing Review

- [[decision]]: review condition

## Missing Evidence

- [[note]]: missing source link

## Broken Links

- [[note]]: broken link target

## Unresolved Questions

- [[question]]: missing next exploration

## Suggested Next Actions

- {{action}}
```
