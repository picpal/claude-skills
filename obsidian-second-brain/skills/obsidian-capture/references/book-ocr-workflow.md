# Book OCR Workflow

Use this workflow when the input is an OCR scan of a book, a scanned PDF, chapter text, or a local OCR file.

## Destination

Use `20_Sources/books` for book material.

Recommended layout:

```text
20_Sources/books/
  raw/
    book-title.pdf
    book-title-ocr.txt
  YYYY-MM-DD-book-title.md
  YYYY-MM-DD-book-title-ch01.md
  YYYY-MM-DD-book-title-ch02.md
```

Put OCR PDFs, scanned PDFs, OCR text exports, and other large raw book files in `20_Sources/books/raw`. If the user already has files outside the vault, keep a durable local path in `## Original`. If the user puts the OCR files inside the vault, keep large raw OCR files as source material and create smaller Source notes for summaries, location notes, and compile candidates.

## Capture Strategy

1. Preserve the original source pointer before summarizing.
2. Detect whether the input is a whole book, chapter, section, or excerpt.
3. If it is long, create or update a book-level index note and split by chapter or section.
4. Record title, author, edition, source file, scope, language, OCR quality, and page or chapter range.
5. Summarize only the captured scope.
6. Extract key concepts, claims, questions, definitions, examples, and methods.
7. Add location notes using page, chapter, heading, or section anchors.
8. Mark uncertain OCR readings with `confidence: low` or `status: needs_ocr_review`.
9. Add compile candidates for future `obsidian-compile`.

## Status Rules

- `captured`: OCR is readable enough to summarize and compile later.
- `needs_ocr_review`: OCR has obvious recognition errors, missing pages, bad page boundaries, or unclear language.
- `needs_classification`: The material may be a book excerpt, report, paper, or note, and the type is uncertain.

## Copyright and Output Rule

Do not paste long copyrighted book text in chat output by default. In the vault, preserve the user's private source or pointer, then work from summaries, location notes, short excerpts, and compile candidates. If the user explicitly asks to keep the full OCR text in the vault, store it as source material and keep derived summaries separate.

## Compile Handoff

Good compile candidates from books include:

- Concept: recurring term, model, framework, definition, method.
- Claim: author assertion that needs evidence or comparison.
- Question: unresolved issue or contradiction.
- Insight: connection between the book and existing maps/projects.
- Project: practice, research, writing, product, or learning plan.
- Decision: change in workflow, tool choice, or research direction.
