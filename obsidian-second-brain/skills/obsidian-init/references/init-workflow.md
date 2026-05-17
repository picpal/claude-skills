# Init Workflow

This workflow prepares an Obsidian vault so the second-brain skills can work from a known structure.

## Commands

Initialize a vault:

```bash
<pack-root>/tools/init-second-brain-vault.sh /path/to/obsidian-vault
```

Verify a vault:

```bash
<pack-root>/tools/verify-vault.sh /path/to/obsidian-vault
```

## What Init Does

- Creates the vault directory if it does not exist.
- Copies the starter `<pack-root>/vault-template/` tree into the vault.
- Creates missing folders.
- Copies missing templates, schemas, and dashboards.
- Keeps every existing file unchanged.

## What Init Does Not Do

- It does not delete notes.
- It does not overwrite existing files.
- It does not classify old notes.
- It does not move user material into the new structure.

## Success Criteria

The vault is ready when `verify-vault.sh` prints:

```text
Obsidian second brain vault verification passed.
```

After that, use:

- `obsidian-capture` to add raw material and thoughts.
- `obsidian-compile` to turn material into linked objects and insights.
- `obsidian-retrieve` to answer from the vault with evidence.
- `obsidian-lint` to find stale, weak, duplicate, or under-linked memory.

## Failure Handling

If verification fails, read the missing file or directory list first. Run init again to restore missing scaffold items. If verification still fails, inspect whether an existing user file has the expected role but different content.
