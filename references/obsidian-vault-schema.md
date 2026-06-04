# Obsidian Vault Schema

Use this reference for setup, schema verification, and frontmatter customization.

The machine-readable source of truth is `config/obsidian_schema.yaml`. Users should customize that YAML file when changing frontmatter fields. Use `scripts/schema_tool.py` to validate and render a frontmatter template from the YAML.

## Default Vault Layout

```text
Vault/
  Papers/
    2026-example-paper.md
    assets/
      example-paper/
        figure-1.png
```

Default note directory: `Papers`

Default attachment directory: `Papers/assets`

Both paths must be vault-relative and must not contain `..`.

## Default Frontmatter

These are the default index fields:

| Field | Purpose |
| --- | --- |
| `title` | Display title. |
| `original_title` | Official paper title. |
| `authors` | Author list as written in the paper. |
| `publication_date` | Publication, arXiv, conference, or journal date when known. |
| `year` | Numeric year for filtering and Dataview queries. |
| `venue` | Venue labels. |
| `field` | Broad research area labels. |
| `type` | Paper or contribution type labels. |
| `keywords` | Paper-specific topic phrases. |
| `reading_status` | Workflow state. |
| `read_date` | Date the report was written or last substantially updated. |
| `rating` | Optional reader rating. |
| `doi` | DOI URL. |
| `arxiv` | arXiv abstract URL. |
| `code` | Official code or best verified implementation URL. |
| `report_language` | `English`, `Chinese`, or `Bilingual`. |
| `dedup_key` | DOI, arXiv ID, or normalized title used for duplicate detection. |
| `dedup_strategy` | `doi`, `arxiv`, or `title`. |
| `tags` | Defaults to `papers` plus broad field tags. |

## Setup Steps

1. Identify the target vault directory.
2. Validate the schema:

   ```bash
   python scripts/schema_tool.py --command validate
   ```

3. Optionally render a frontmatter template:

   ```bash
   python scripts/schema_tool.py --command frontmatter-template
   ```

4. Save `.paper-obsidian/config.json` in the active workspace:

   ```json
   {
     "runtime": "codex",
     "vault_path": "/path/to/vault",
     "notes_dir": "Papers",
     "attachments_dir": "Papers/assets",
     "schema_version": "1.0.0",
     "default_report_language": "English",
     "venv": ".paper-obsidian/.venv",
     "last_environment_check": ".paper-obsidian/environment-check.json",
     "last_smoke_test": ".paper-obsidian/smoke-test/obsidian_payload.json"
   }
   ```

5. Run a dry-run publish before the first real write.

## Optional Research Flow Fields

Do not create these fields by default. They are defined under `optional_extensions.research_flow` in `config/obsidian_schema.yaml`. Add them only when the user asks for daily paper discovery, conference tracking, paper scoring, or team reading workflows.
