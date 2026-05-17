---
name: obsidian-init
description: "Obsidian 제2의 뇌 Vault 초기 세팅과 검증. capture/compile/retrieve/lint 워크플로 진입 전에 vault 구조와 템플릿이 갖춰져 있는지 비파괴 방식으로 확인한다. '옵시디언 vault 초기화', 'obsidian init', 'vault 세팅', '제2의 뇌 만들어줘', '옵시디언 검증', 'vault 점검 준비' 같은 요청에 트리거. 기존 노트는 절대 덮어쓰지 않는다."
---

# Obsidian Init

Use this skill when the user wants to create, connect, or verify an Obsidian second-brain vault for this skill pack.

## Core Rule

Initialization is non-destructive. Create missing structure and report what already exists; do not overwrite existing notes.

## When to Use

- The user is setting up the vault for the first time.
- The user wants to check whether capture, compile, retrieve, and lint can run safely.
- The vault path is new, uncertain, moved, or shared across tools.
- A workflow fails because expected folders, templates, dashboards, or schemas are missing.

## Workflow

1. Identify the vault path from the user, project config, or current context.
2. If the vault exists, run:
   ```bash
   <pack-root>/tools/verify-vault.sh /path/to/obsidian-vault
   ```
3. If verification fails or the vault is new, run:
   ```bash
   <pack-root>/tools/init-second-brain-vault.sh /path/to/obsidian-vault
   ```
4. Run verification again.
5. Report the vault path, dashboard path, template path, and any remaining missing items.
6. Tell the user the vault is ready for `obsidian-capture`, `obsidian-compile`, `obsidian-retrieve`, and `obsidian-lint` only after verification passes.

## Safety

- Do not overwrite existing files in the vault.
- Do not rename user notes during init.
- Do not delete old folders or old notes.
- Keep ambiguous existing material in place; later use lint or compile to reorganize it.
- If the user wants a destructive reset, stop and ask for explicit confirmation outside this skill.

## Expected Output

Successful init should leave these anchors in place:

- `00_System/dashboards/Home.md`
- `00_System/templates/`
- `00_System/schemas/note-types.md`
- `10_Capture/inbox/`
- `20_Sources/`
- `30_Objects/`
- `40_Maps/`
- `50_Execution/`
- `60_Reviews/`

## References

- `references/init-workflow.md`
- `../../shared/obsidian-second-brain/references/vault-structure.md`
- `../../shared/obsidian-second-brain/references/note-types.md`
- `../../shared/obsidian-second-brain/references/reliability.md`
