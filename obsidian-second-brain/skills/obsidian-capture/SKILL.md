---
name: obsidian-capture
description: "생각, 링크, CLI 세션, OCR 책, 영상, YouTube 자막, 이미지, 문서, 웹페이지를 분류 강요 없이 Obsidian 제2의 뇌 Vault에 빠르게 받아 적는다. 'obsidian에 저장', '캡처해줘', '옵시디언에 메모', 'vault에 넣어줘', 'YouTube 자막 저장', 'OCR 책 저장', '링크 저장해줘' 같은 요청에 트리거. 원본은 덮어쓰지 않고, 분류 애매하면 needs_classification 상태로 둔다. 사용자가 vault가 있다는 맥락에서 메모/저장/기록을 언급하면 명시 요청이 없어도 이 스킬을 우선 고려 — 캡처 마찰은 second brain의 최대 적이다."
---

# Obsidian Capture

Use this skill when the user wants to save a thought, note, CLI session, URL, video link, YouTube transcript, OCR book scan, image, file, web page, or raw material into their Obsidian second brain.

## Core Rule

Capture must be low-friction. Do not force the user to classify the material before saving it.

**Why:** The largest failure mode of a second brain is empty inboxes — every classification question raised at capture time is friction that pushes the user to skip the vault entirely. Sorting can happen later in compile; saving cannot.

## Inputs

- Freeform thought
- Quick note
- CLI session transcript or summary
- URL or web page
- Video link, including YouTube
- Video transcript, subtitles, captions, or timestamp notes
- OCR book text, scanned book PDF, chapter excerpt, or reading note
- Image or file reference
- Text excerpt

## Workflow

1. Identify or ask for the vault path if it is not available from context.
2. Preserve the raw input or pointer.
   - For web pages / URLs (non-`.md`): use the `defuddle` skill to extract clean markdown first, then save the result. This removes navigation/ads and saves tokens. Skip `defuddle` for `.md` URLs.
3. Choose the lightest safe destination:
   - `10_Capture/inbox` for quick thoughts.
   - `10_Capture/unprocessed` for ambiguous material.
   - `20_Sources/sessions` for CLI sessions.
   - `20_Sources/web` for web pages and URLs.
   - `20_Sources/videos` for video links, transcripts, captions, and timestamp summaries.
   - `20_Sources/images` for image references.
   - `20_Sources/books/raw` for large OCR PDFs, scanned book PDFs, OCR text exports, and raw book files.
   - `20_Sources/books` for book index notes, chapter Source notes, sections, and book excerpts.
   - `20_Sources/documents` for generic documents and PDFs.
   - `20_Sources/papers` for academic papers and reports.
4. For YouTube or video links, try to capture transcript-backed meaning, not just the URL:
   - Preserve the durable video URL.
   - Capture available title, channel, publish date, duration, and transcript availability when accessible.
   - If subtitles, captions, or a user-provided transcript are available, summarize from that text.
   - Add timestamp notes when the transcript or page provides usable time anchors.
   - If transcript access is unavailable, set `status: needs_transcript` and do not infer detailed content from the title alone.
5. For OCR books, preserve the source pointer and split long material:
   - Store book OCR material under `20_Sources/books`.
   - Store large raw OCR PDFs and scan files under `20_Sources/books/raw`.
   - Create one book-level Source note as an index when the book is large.
   - Create chapter or section Source notes when a single note would become too long.
   - Record title, author, edition if known, OCR quality, page or chapter range, and file location.
   - Summarize and extract compile candidates from the OCR text, but keep uncertain OCR readings marked as low confidence.
6. Create a Source or Capture note with metadata. Write it as Obsidian Flavored Markdown — follow the `obsidian-markdown` skill for frontmatter properties (YAML), wikilinks `[[...]]`, embeds `![[...]]`, callouts `> [!note]`, and tag syntax. When Obsidian is running, use `obsidian-cli` for the actual file write so the live index updates immediately.
7. Set `status: captured`, `status: needs_classification`, `status: needs_transcript`, or `status: needs_ocr_review`.
8. Add compile candidates for concepts, claims, questions, insights, projects, or decisions when the source content supports them.
9. Add a short processing note that suggests the next compile step.

## Required Metadata

- `type`
- `created`
- `source_type`
- `status`
- `confidence`
- `related_maps`
- `related_objects`
- `related_projects`

## Video Capture Requirements

For YouTube or video links, the Source note should include:

- `## Original`: durable URL and available metadata.
- `## Transcript Basis`: transcript source, language, access status, and confidence.
- `## Summary`: one to five lines based on transcript/captions when available.
- `## Key Points`: main ideas, claims, examples, and methods.
- `## Timestamp Notes`: important moments when timestamps are available.
- `## Compile Candidates`: candidate Concept, Claim, Question, Insight, Project, or Decision notes.
- `## Processing Notes`: next step and any transcript gaps.

Do not paste long copyrighted transcripts by default. Prefer transcript-based summaries, timestamp notes, and short evidence excerpts. If the user provides their own transcript and asks to preserve it, store it as source material while keeping summaries separate.

## OCR Book Capture Requirements

For OCR books, scanned books, or chapter text, the Source note should include:

- `## Original`: book title, author, edition, local file path or source pointer, and scope.
- `## OCR Basis`: OCR source, OCR quality, language, page or chapter range, and review status.
- `## Summary`: one to five lines for the captured scope.
- `## Key Points`: main concepts, claims, examples, methods, and definitions.
- `## Location Notes`: page, chapter, heading, or section anchors when available.
- `## Compile Candidates`: candidate Concept, Claim, Question, Insight, Project, or Decision notes.
- `## OCR Text or Excerpts`: only the needed excerpt, or a pointer to the local OCR file when the text is long.
- `## Processing Notes`: next step, OCR cleanup needs, and split/merge notes.

Prefer `20_Sources/books` for book material. Use `20_Sources/documents` only when the material is not book-like. Do not turn a whole book into one giant note if chapter or section notes would make retrieval easier.

## Safety

- Never overwrite raw source content.
- Do not invent source details.
- If classification is uncertain, use `needs_classification`.
- If a video has no accessible transcript or captions, use `needs_transcript`.
- If OCR quality is poor or page boundaries are uncertain, use `needs_ocr_review`.
- Do not summarize a video in detail from title, thumbnail, or comments alone.
- Do not treat OCR text as exact evidence when the scan quality is uncertain.
- Do not expose long copyrighted book text in chat output by default. Keep private OCR source material in the vault and work from summaries, location notes, and short excerpts unless the user explicitly asks otherwise.
- If evidence is weak, set `confidence: low`.

## Example

**Input:** "이 YouTube 링크를 vault에 저장해줘 (vault: ~/my-vault): https://www.youtube.com/watch?v=XYZ — 가능하면 transcript 기반 핵심까지"

**Output:** `~/my-vault/20_Sources/videos/2026-05-17-video-title.md` 1개 파일, 다음 frontmatter+섹션 포함:

```markdown
---
type: source
source_type: video
created: 2026-05-17
status: needs_transcript    # 자막 접근 불가 시
confidence: low
related_maps: []
related_objects: []
related_projects: []
---
# 영상 제목

## Original
URL: https://www.youtube.com/watch?v=XYZ
채널, 게시일, 길이 (가용 시)

## Transcript Basis
자막 가용성, 언어, 신뢰도

## Summary
(자막 가용 시 1~5줄, 아니면 비워두고 needs_transcript 유지)

## Key Points
## Timestamp Notes
## Compile Candidates
- Concept 후보, Claim 후보, Question 후보, Insight 후보

## Processing Notes
다음 compile 단계 제안
```

자막 없으면 제목·썸네일만 보고 내용 추론하지 않음 — `status: needs_transcript` 유지.

## Companion Skills (kepano/obsidian-skills)

This skill decides *what to capture and where to put it*. Delegate the actual file shape and write path:

- `defuddle` — fetch web pages / URLs and convert to clean markdown before saving. Use instead of WebFetch for any non-`.md` URL.
- `obsidian-markdown` — Source/Capture note body and frontmatter must follow Obsidian Flavored Markdown (properties, wikilinks, embeds, callouts, tags).
- `obsidian-cli` — when Obsidian is running, prefer it for creating notes so the index/graph refreshes; otherwise plain file write is fine for the inbox.

## References

- `../../shared/obsidian-second-brain/references/vault-structure.md`
- `../../shared/obsidian-second-brain/references/note-types.md`
- `references/capture-workflow.md`
- `references/video-transcript-workflow.md`
- `references/book-ocr-workflow.md`
