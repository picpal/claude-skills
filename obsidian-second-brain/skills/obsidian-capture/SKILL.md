---
name: obsidian-capture
description: "생각, 링크, CLI 세션, OCR 책, 영상, YouTube 자막, 이미지, 문서, 웹페이지를 분류 강요 없이 Obsidian 제2의 뇌 Vault에 빠르게 받아 적는다. 'obsidian에 저장', '캡처해줘', '옵시디언에 메모', 'vault에 넣어줘', 'YouTube 자막 저장', 'OCR 책 저장', '링크 저장해줘' 같은 요청에 트리거. 원본은 덮어쓰지 않고, 분류 애매하면 needs_classification 상태로 둔다. 사용자가 vault가 있다는 맥락에서 메모/저장/기록을 언급하면 명시 요청이 없어도 이 스킬을 우선 고려 — 캡처 마찰은 second brain의 최대 적이다."
---

# Obsidian Capture

Use this skill when the user wants to save a thought, note, CLI session, URL, video link, YouTube transcript, OCR book scan, image, file, web page, or raw material into their Obsidian second brain.

## Core Rule

Capture must be low-friction. Do not force the user to classify the material before saving it.

**Why:** The largest failure mode of a second brain is empty inboxes — every classification question raised at capture time is friction that pushes the user to skip the vault entirely. Sorting can happen later in compile; saving cannot.

## Tool Preference

파일 쓰기 도구 우선순위. **MCP를 첫 시도로 쓰지 말 것.**

1. **`obsidian-cli` 스킬** — Obsidian 실행 중이면 1순위. `obsidian create name=... content=...`로 쓰면 라이브 인덱스 즉시 갱신.
2. **직접 Write tool** — 다수 파일을 한 번에 쓰거나 본문이 길어 `obsidian create`의 인자 인용이 번거로울 때.
3. **`obsidian-mcp-server` MCP 툴** — Local REST API 플러그인이 켜져 있고 원격 vault일 때만.

**Why:** MCP는 플러그인 의존, obsidian-cli는 Obsidian 기본 CLI 사용. 첫 시도 실패 시 다음 단계로 fallback.

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
7. Set one of the status values from the [Status enum](#status-enum) section below.
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

### Optional Metadata

- `parent_source` — chapter/section Source 노트가 상위 book/document index Source 노트를 가리킬 때. 값은 wikilink (`"[[api-보안-전략]]"`). 단일 책을 13개 챕터로 split하는 등의 split capture에서 backlink 유지에 필요.
- `compiled_at` — `obsidian-compile`이 처리 완료 시 자동 설정. 사람이 손으로 쓰지 않음.
- `tags` — 자유 분류 (예: `book/api-보안-전략`, `api/security`).

## Status Enum

| status | 의미 | 다음 단계 |
|---|---|---|
| `captured` | 기본값. 캡처 완료, compile 대기 | `obsidian-compile` |
| `needs_classification` | 분류 모호. 어느 디렉토리·타입인지 결정 필요 | 사람 분류 후 `captured` 또는 적절한 위치 이동 |
| `needs_transcript` | 영상이지만 자막 접근 불가 | 자막 확보 후 재캡처 |
| `needs_ocr_review` | OCR 품질 불확실, 페이지 경계 모호 | 사람이 OCR 결과 검토 |
| `needs_deep_extraction` | 캡처는 됐지만 본문 deep extract가 compile에 필요 (e.g., 책 챕터를 도입부만 캡처한 경우) | compile 이전 deep read 추가 |
| `compiled` | `obsidian-compile`이 처리 완료. `compiled_at` 함께 설정됨 | (없음 — 안정 상태) |
| `compile_failed` | compile 시도했으나 실패. `compile_error` 필드 참고 | 오류 검토 후 재시도 |

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
