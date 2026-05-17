# Compile Workflow

## Processing Steps

1. Read the captured Source, Capture, quick-note, or unprocessed note.
2. Extract candidate concepts, claims, questions, tensions, and execution implications.
3. Search `30_Objects`, `40_Maps`, and `50_Execution` for existing related notes, projects, and decisions.
4. Decide for each candidate:
   - update existing note
   - create new note
   - keep as unresolved
   - mark as hypothesis
5. Update or create notes using templates from the pack's `shared/obsidian-second-brain/templates`.
6. Update the most relevant Map.
7. Update Dashboard sections when there are visible insights, tensions, decisions, or next actions.
8. Write a log entry.

## Log Entry Format

```markdown
## {{date}} Compile

- Source processed: [[source-note]]
- Updated notes:
  - [[note]]
- Created notes:
  - [[note]]
- Insight candidates:
  - [[insight]]
- Unresolved:
  - {{question_or_issue}}
```

## Merge Before Create Checklist

- Search exact title.
- Search aliases and near synonyms.
- Check relevant maps.
- Check recent insights.
- If a similar note exists, update it and add the source link.
