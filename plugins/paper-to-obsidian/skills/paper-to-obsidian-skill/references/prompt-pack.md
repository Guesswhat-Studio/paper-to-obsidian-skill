# Prompt Pack

These prompts are examples for users or future agents. The skill itself should follow `SKILL.md` and the references directly.

## Setup Prompt

```text
Use $paper-to-obsidian-skill to set up my Obsidian paper reading workflow.

Please detect the OS, prepare a workspace uv-managed .venv at .paper-obsidian/.venv for PDF reading, validate the frontmatter schema, use this Obsidian vault path: <VAULT_PATH>, save .paper-obsidian/config.json in this workspace, run the Attention Is All You Need smoke test, then dry-run a publish into the vault.

Before running shell commands, detect the active shell/tool and use matching syntax: PowerShell commands only in PowerShell, POSIX commands only in Bash/zsh/sh. Prefer the Python setup helper when Python is available.
```

## Environment-Only Prompt

```text
Use $paper-to-obsidian-skill to check and prepare my local paper-reading environment.

Please detect Windows/macOS/Linux, create the workspace .venv at .paper-obsidian/.venv with uv if useful, install the required Python packages, validate PyMuPDF/Pillow/requests/HTML parsing support, report optional tool availability, and run the Attention Is All You Need smoke test if network access is available.

Before running shell commands, detect the active shell/tool and use matching syntax: PowerShell commands only in PowerShell, POSIX commands only in Bash/zsh/sh. Prefer the Python setup helper when Python is available.
```

## Default English Reading Prompt

```text
Use $paper-to-obsidian-skill to read this paper in English and save it to my Obsidian vault:

Vault path: <VAULT_PATH>
Paper: <PAPER_INPUT>

Please resolve the paper identity, extract verified metadata, classify the paper type, capture important evidence, generate a Markdown report with figures, formulas, tables, code and reproducibility notes, create or update the Obsidian note, copy local attachments, and verify the note after publishing.
```

## Chinese Reading Prompt

```text
Use $paper-to-obsidian-skill to read this paper in Chinese and save it to my Obsidian vault:

Vault path: <VAULT_PATH>
Paper: <PAPER_INPUT>

Please keep the official English title in original_title, write the report body in Chinese, preserve formulas in LaTeX, include the key figures and tables, and verify the note after publishing.
```

## Bilingual Reading Prompt

```text
Use $paper-to-obsidian-skill to read this paper bilingually and save it to my Obsidian vault:

Vault path: <VAULT_PATH>
Paper: <PAPER_INPUT>

Please write the full report in English, add a compact Chinese overview near the top, preserve formulas, and write report_language as Bilingual in frontmatter.
```

## Publish Existing Report Prompt

```text
Use $paper-to-obsidian-skill to publish this existing report to my Obsidian vault:

Vault path: <VAULT_PATH>
Report path: <REPORT_PATH>
Metadata path, if available: <METADATA_OR_PAYLOAD_PATH>

Please build or validate obsidian_payload.json, deduplicate by DOI/arXiv/title, create or update the Markdown note, and verify the result.
```

## Optional Research-Flow Extension Prompt

```text
Use $paper-to-obsidian-skill to extend my Obsidian paper notes for daily discovery and team reading.

Please keep the default paper-reading frontmatter fields intact, ask before adding optional scoring/team fields, then add only the fields needed for arXiv discovery, conference tracking, paper scoring, assignee tracking, and weekly digest views.
```
