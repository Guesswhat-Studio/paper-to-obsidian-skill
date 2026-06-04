# Paper To Obsidian Skill

Evidence-driven paper reading for Codex, Claude, WorkBuddy, and compatible CLI runtimes. This skill turns an academic paper into a durable Obsidian Markdown note with YAML frontmatter, grounded evidence, formulas, figures, tables, code checks, limitations, and reproducibility notes.

Obsidian itself does not need an MCP connector for the default workflow. A vault is a local folder, so the skill writes Markdown files and attachments directly to the filesystem.

## What It Does

- Reads papers from local PDFs, arXiv URLs, DOI links, paper URLs, or titles.
- Extracts verified metadata and source-grounded evidence.
- Uses arXiv HTML when available for sections, formulas, tables, and figure URLs.
- Builds `obsidian_payload.json` from metadata and a Markdown report.
- Publishes or updates one note in an Obsidian vault.
- Copies local evidence images into the vault attachments directory.
- Deduplicates by DOI, arXiv ID, or normalized title.

## Repository Layout

```text
paper-to-obsidian-skill/
  .claude-plugin/marketplace.json
  SKILL.md
  agents/openai.yaml
  config/obsidian_schema.yaml
  plugins/paper-to-obsidian/
  references/
  scripts/
  tools/
```

The top-level skill is the source of truth. The Claude plugin copy is mirrored with:

```bash
python tools/sync_plugin.py
```

## Install For Codex

Clone or copy this repository to your Codex skills directory:

```powershell
Copy-Item -Recurse . $env:USERPROFILE\.codex\skills\paper-to-obsidian-skill
```

Then use:

```text
Use $paper-to-obsidian-skill to read this paper in English and save it to my Obsidian vault:

Vault path: D:\path\to\vault
Paper: https://arxiv.org/abs/1706.03762
```

## Install For Claude Code Plugin Testing

```bash
claude plugin validate .
claude plugin validate ./plugins/paper-to-obsidian
claude plugin marketplace add .
claude plugin install paper-to-obsidian@guesswhat-paper-tools
```

## Local Environment

Create and check the workspace environment:

```bash
python scripts/setup_environment.py --use-uv --install --json-report .paper-obsidian/environment-check.json
```

Run the smoke test:

```bash
python scripts/smoke_test_attention.py --output .paper-obsidian/smoke-test
```

## Publish Flow

Build a payload:

```bash
python scripts/build_obsidian_payload.py --metadata metadata.json --report report.md --output obsidian_payload.json --vault-path D:\path\to\vault
```

Validate report quality:

```bash
python scripts/validate_report_quality.py report.md --payload obsidian_payload.json
```

Validate:

```bash
python scripts/validate_obsidian_payload.py obsidian_payload.json --require-vault
```

Dry run and publish:

```bash
python scripts/publish_obsidian_payload.py obsidian_payload.json --dry-run
python scripts/publish_obsidian_payload.py obsidian_payload.json --if-exists update
```

## Vault Defaults

- Notes: `Papers/`
- Attachments: `Papers/assets/`
- Schema: `config/obsidian_schema.yaml`
- Local setup state: `.paper-obsidian/config.json`

The generated note frontmatter is intentionally lean. Put long contribution analysis, method details, limitations, evidence explanations, and reproducibility notes in the Markdown body.
