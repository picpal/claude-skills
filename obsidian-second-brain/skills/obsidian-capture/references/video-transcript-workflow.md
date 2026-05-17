# Video Transcript Workflow

## Goal

Video capture should preserve the link and extract usable meaning from transcript, subtitles, captions, or user-provided script when available.

## Processing Order

1. Save the durable video URL first.
2. Collect available metadata:
   - title
   - channel or author
   - publish date
   - duration
   - source platform
3. Look for transcript material in this order:
   - user-provided transcript or subtitles
   - accessible platform transcript or captions
   - browser-visible transcript panel
   - existing local transcript file
4. If transcript material is available, summarize from the transcript.
5. If transcript material is partial, summarize only the covered portions and mark `confidence: low` or `medium`.
6. If transcript material is unavailable, set `status: needs_transcript` and preserve only the URL, metadata, and user-provided context.

## Note Structure

Store video captures in `20_Sources/videos`.

Use:

```text
YYYY-MM-DD-youtube-{{slug}}.md
```

Use `source_type: video` or `source_type: youtube`.

Recommended sections:

- `Original`: URL and metadata.
- `Transcript Basis`: where the transcript came from and how complete it is.
- `Summary`: one to five lines.
- `Key Points`: main ideas, claims, examples, methods, and warnings.
- `Timestamp Notes`: timestamped moments when available.
- `Evidence Excerpts`: only short excerpts that are necessary for evidence.
- `Compile Candidates`: Concept, Claim, Question, Insight, Project, Decision.
- `Processing Notes`: status, gaps, and next step.

## Confidence Rules

- `high`: transcript is complete and source metadata is clear.
- `medium`: transcript is mostly complete or user-provided but not independently checked.
- `low`: transcript is partial, auto-generated with obvious errors, translated, or unavailable.

## Safety

- Do not infer detailed content from title, thumbnail, description, or comments alone.
- Do not paste long copyrighted transcripts by default.
- Keep transcript-derived summary separate from raw source pointers.
- Mark missing transcript as `needs_transcript`, not `captured`.
- Link any later Concept, Claim, Question, or Insight back to the video Source note.
