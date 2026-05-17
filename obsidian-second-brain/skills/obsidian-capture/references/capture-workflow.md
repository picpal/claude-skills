# Capture Workflow

## Filename Pattern

Use:

```text
YYYY-MM-DD-slug.md
```

For very short freeform thoughts, use:

```text
YYYY-MM-DD-HHMM-quick-thought.md
```

## Frontmatter Example

```yaml
---
type: source
created: "2026-05-15"
source_type: thought
status: captured
confidence: low
related_maps: []
related_objects: []
related_projects: []
---
```

## Body Structure

```markdown
# Title

## Original

Raw content or pointer.

## Summary

One to five lines.

## Processing Notes

- Status: captured
- Suggested next step: run obsidian-compile
```

## Video Link Body Structure

Use this structure for YouTube or video links:

```markdown
# YouTube - {{title}}

## Original

- URL: {{url}}
- Channel: {{channel_or_unknown}}
- Published: {{published_or_unknown}}
- Duration: {{duration_or_unknown}}

## Transcript Basis

- Transcript source: captions | subtitles | user-provided transcript | unavailable
- Language: {{language_or_unknown}}
- Access status: available | partial | unavailable
- Confidence: low | medium | high

## Summary

One to five lines based on transcript or captions.

## Key Points

- {{point}}

## Timestamp Notes

- {{timestamp}} - {{note}}

## Compile Candidates

- Concept:
- Claim:
- Question:
- Insight:
- Project:
- Decision:

## Processing Notes

- Status: captured | needs_transcript
- Suggested next step: run obsidian-compile
```

If transcript or captions are unavailable, keep the durable URL and metadata, set `status: needs_transcript`, and avoid detailed content claims.

## OCR Book Body Structure

Use this structure for OCR books, scanned books, or chapter excerpts:

Put large raw source files such as OCR PDFs, scanned PDFs, and OCR text exports in `20_Sources/books/raw`. Create smaller Source notes in `20_Sources/books` that point back to those raw files.

```markdown
# Book OCR - {{book_title}} - {{scope}}

## Original

- Title: {{book_title}}
- Author: {{author_or_unknown}}
- Edition: {{edition_or_unknown}}
- Source file: {{local_file_path_or_pointer}}
- Scope: {{whole_book_or_chapter_or_page_range}}

## OCR Basis

- OCR source: scanned PDF | image OCR | text file | markdown file | user-provided OCR
- Language: {{language_or_unknown}}
- OCR quality: low | medium | high
- Page or chapter range: {{range_or_unknown}}
- Review status: captured | needs_ocr_review

## Summary

One to five lines for this book, chapter, or section.

## Key Points

- {{point}}

## Location Notes

- {{page_or_chapter_or_heading}} - {{note}}

## Compile Candidates

- Concept:
- Claim:
- Question:
- Insight:
- Project:
- Decision:

## OCR Text or Excerpts

Store short relevant excerpts here, or point to the local OCR file when the text is long.

## Processing Notes

- Status: captured | needs_ocr_review
- Suggested next step: run obsidian-compile after reviewing OCR quality
```

For long books, create one book-level Source note as an index and separate chapter or section Source notes. Use `20_Sources/books` for book material, not `20_Sources/documents`.

## Ambiguous Input

When the material is unclear, save it anyway and mark:

```yaml
status: needs_classification
confidence: low
```
