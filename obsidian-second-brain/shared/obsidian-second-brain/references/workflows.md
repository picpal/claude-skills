# Workflows

## Init Flow

1. Identify the target vault path.
2. Verify whether required folders, templates, schemas, and dashboards already exist.
3. Create missing scaffold items without overwriting existing files.
4. Verify the vault again before running capture, compile, retrieve, or lint.

## Capture Flow

1. Accept raw input without requiring classification.
2. Preserve original content or source pointer.
3. Add metadata: date, source type, status, confidence.
4. Store in `10_Capture` or `20_Sources`.

## Compile Flow

1. Read the captured item.
2. Compare against existing maps, objects, projects, and decisions.
3. Prefer updating existing notes before creating new notes.
4. Create insight candidates only when a meaningful new connection appears.
5. Update maps and dashboard surfaces.
6. Log changed notes.

## Retrieve Flow

1. Start from relevant maps.
2. Follow links to object notes.
3. Open source notes for evidence.
4. Distinguish evidence from inference.
5. Save new insight, question, decision, or output candidates when retrieval creates value.

## Lint Flow

1. Find orphan notes, duplicate concepts, weak claims, stale decisions, and broken links.
2. Produce review items, not silent rewrites.
3. Add lint reports to `60_Reviews/lint-reports`.
4. Surface important review items on the Home dashboard.
