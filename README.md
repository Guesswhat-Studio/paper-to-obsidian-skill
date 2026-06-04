# Paper To Obsidian Skill

[English](README.md) | [简体中文](README.zh-CN.md)

Evidence-driven paper reading for Codex, Claude, WorkBuddy, and compatible CLI agent runtimes. This skill turns an academic paper into a durable Obsidian Markdown note with YAML frontmatter, grounded evidence, formulas, figures, tables, code checks, limitations, and reproducibility notes.

Obsidian itself does not require an MCP connector, workspace connector, API token, or desktop app for the default workflow. A vault is a local folder, so the skill writes Markdown notes and attachments directly to the filesystem.

The default report language is English. Chinese and bilingual reports are supported when requested.

## Install

### Option 1: Agent-Assisted Install

If you already use Codex, the easiest path is to ask the agent to install the skill and run the first setup pass for you.

Paste this into a Codex session:

```text
Please install this skill:
https://github.com/Guesswhat-Studio/paper-to-obsidian-skill

Install it into my Codex skills directory, then use $paper-to-obsidian-skill to set up my Obsidian paper reading workflow.

Vault path: <absolute path to my Obsidian vault>

Please handle the setup automatically: first detect my OS and active shell/tool, use commands that match that shell, prepare the local Python environment, validate the Obsidian frontmatter schema, run the Attention Is All You Need smoke test, save .paper-obsidian/config.json, and only report the note path, validation status, and any action I must take.
```

### Option 2: Claude Code Plugin Install

Claude Code plugin commands are handled by the Claude Code CLI. The model cannot run `/plugin marketplace add` or `/plugin install` for you from inside a chat session. Run the install command yourself, then ask the installed skill to set up the workflow.

In an interactive Claude Code session, run these one at a time. Press Enter after each command and wait for it to finish before typing the next one:

```text
/plugin marketplace add https://github.com/Guesswhat-Studio/paper-to-obsidian-skill
```

```text
/plugin install paper-to-obsidian@guesswhat-paper-tools
```

```text
/reload-plugins
```

```text
/paper-to-obsidian:paper-to-obsidian-skill set up my Obsidian paper reading workflow
```

From a terminal, use:

```bash
claude plugin marketplace add https://github.com/Guesswhat-Studio/paper-to-obsidian-skill
claude plugin install paper-to-obsidian@guesswhat-paper-tools
claude -p "Use /paper-to-obsidian:paper-to-obsidian-skill to set up my Obsidian paper reading workflow. Vault path: <absolute path to my Obsidian vault>. Keep the setup automatic: first detect my OS and active shell/tool, use commands that match that shell, prepare the local Python environment, validate the schema, run the Attention Is All You Need smoke test, save .paper-obsidian/config.json, and only report the note path, validation status, and any action I must take."
```

As a one-liner:

```bash
claude plugin marketplace add https://github.com/Guesswhat-Studio/paper-to-obsidian-skill && claude plugin install paper-to-obsidian@guesswhat-paper-tools && claude -p "Use /paper-to-obsidian:paper-to-obsidian-skill to set up my Obsidian paper reading workflow. Vault path: <absolute path to my Obsidian vault>. Keep the setup automatic: first detect my OS and active shell/tool, use commands that match that shell, prepare the local Python environment, validate the schema, run the Attention Is All You Need smoke test, save .paper-obsidian/config.json, and only report the note path, validation status, and any action I must take."
```

Claude chat on the web does not load Claude Code plugins directly. Use Claude Code, or plugin support in a compatible Claude workspace product.

### Option 3: Manual Install

#### Codex

Windows default Codex skills directory:

```cmd
git clone https://github.com/Guesswhat-Studio/paper-to-obsidian-skill.git "%USERPROFILE%\.codex\skills\paper-to-obsidian-skill"
```

Windows with a custom `CODEX_HOME`:

```cmd
git clone https://github.com/Guesswhat-Studio/paper-to-obsidian-skill.git "%CODEX_HOME%\skills\paper-to-obsidian-skill"
```

macOS or Linux:

```bash
git clone https://github.com/Guesswhat-Studio/paper-to-obsidian-skill.git "$HOME/.codex/skills/paper-to-obsidian-skill"
```

After cloning, ask Codex:

```text
Use $paper-to-obsidian-skill to set up my Obsidian paper reading workflow.

Vault path: <absolute path to my Obsidian vault>
```

#### Claude Code

Add the repository as a Claude Code plugin marketplace and install the plugin:

```bash
claude plugin marketplace add https://github.com/Guesswhat-Studio/paper-to-obsidian-skill
claude plugin install paper-to-obsidian@guesswhat-paper-tools
```

Then start Claude Code and ask:

```text
Use /paper-to-obsidian:paper-to-obsidian-skill to set up my Obsidian paper reading workflow.

Vault path: <absolute path to my Obsidian vault>
```

Compatible plugin users can add the same GitHub repository as a plugin marketplace, then install `Paper To Obsidian` from `guesswhat-paper-tools`.

The marketplace and plugin structure in this repo follows the Claude Code plugin docs:

- [Discover and install plugins](https://code.claude.com/docs/en/discover-plugins)
- [Create and distribute plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference)

## What It Does

- Reads papers from a local PDF, arXiv URL, DOI, paper URL, or title.
- Resolves paper identity and verifies metadata from the paper or official sources.
- Builds a source registry and reading pack before writing the report.
- Uses official arXiv HTML renderings when available at `https://arxiv.org/html/<arxiv_id>`.
- Reuses arXiv HTML figure URLs as hosted Markdown images only after the generated URLs pass reachability checks.
- Extracts evidence from formulas, figures, tables, algorithms, theorems, model diagrams, ablations, robustness panels, and result sections when available.
- Generates Obsidian-ready reports with source-grounded claims and explicit uncertainty markers.
- Validates report depth and template compliance before payload creation, so shallow notes do not get published just because the payload schema is valid.
- Creates or updates an Obsidian note using DOI, arXiv ID, or normalized original title for deduplication.
- Keeps YAML frontmatter compact while putting deep analysis in the Markdown body.
- Provides local validation scripts, schema tooling, and a smoke test based on "Attention Is All You Need".

## Repository Contents

```text
paper-to-obsidian-skill/
  .claude-plugin/marketplace.json  # Claude Code marketplace catalog
  .github/workflows/validate.yml    # GitHub Actions validation workflow
  LICENSE                          # MIT license
  SKILL.md                         # Main skill instructions
  requirements.txt                 # Python dependencies
  agents/openai.yaml               # Agent configuration example
  config/obsidian_schema.yaml      # Default Obsidian frontmatter schema
  plugins/paper-to-obsidian/       # Claude Code plugin package with mirrored skill copy
  references/                      # Reading, publishing, vault, and setup contracts
  scripts/                         # Environment, report-quality, payload, validation, and publishing helpers
  tools/                           # Repository validation and plugin-sync helpers
```

## Requirements

- Python 3.10 or newer, or shell access to run the bootstrap scripts that install a uv-managed Python.
- A compatible agent runtime, such as Codex, Claude, WorkBuddy, or another CLI-capable runtime.
- Local filesystem access to the target Obsidian vault folder.
- Optional: `uv` for faster environment setup.
- Optional: `gh`, `git`, and `tesseract` for GitHub checks, repository inspection, and OCR support.

## Maintainer Notes

The install section above is the intended user path. The commands below are for maintainers, debugging, and air-gapped setup.

Clone the repository:

```bash
git clone https://github.com/Guesswhat-Studio/paper-to-obsidian-skill.git
cd paper-to-obsidian-skill
```

Install it as a Codex skill by placing the folder under your Codex skills directory.

macOS or Linux:

```bash
mkdir -p "$HOME/.codex/skills"
cp -R . "$HOME/.codex/skills/paper-to-obsidian-skill"
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $env:USERPROFILE\.codex\skills
Copy-Item -Recurse . $env:USERPROFILE\.codex\skills\paper-to-obsidian-skill
```

For Claude Code plugin testing from a local checkout:

```bash
claude plugin validate .
claude plugin validate ./plugins/paper-to-obsidian
claude plugin marketplace add .
claude plugin install paper-to-obsidian@guesswhat-paper-tools
```

After changing `SKILL.md`, `requirements.txt`, `agents/`, `config/`, `references/`, or `scripts/`, sync the Claude plugin copy:

```bash
python tools/sync_plugin.py
```

Before publishing a report, run:

```bash
python scripts/validate_report_quality.py paper-output/report.md --payload paper-output/obsidian_payload.json
python scripts/validate_obsidian_payload.py paper-output/obsidian_payload.json --check-image-urls
```

Use this check before committing:

```bash
python tools/sync_plugin.py --check
python tools/validate_repository.py
```

For WorkBuddy or other compatible runtimes, add this repository as a skill/workflow directory and make `SKILL.md` available to the agent.

## CI

GitHub Actions runs a lightweight validation workflow on push and pull request:

- Compile Python helper scripts and repository tools.
- Check that the Claude plugin copy is byte-for-byte in sync with `tools/sync_plugin.py --check`.
- Validate repository packaging and mirror invariants with `tools/validate_repository.py`.
- Validate the Obsidian frontmatter schema.
- Check helper CLI entry points.

The arXiv network smoke test is available through manual `workflow_dispatch` with `run_network_smoke=true` so temporary network or arXiv issues do not block normal PRs.

## What The Agent Sets Up

After installation, Codex or Claude should perform the remaining setup from the skill instructions:

- Detect the runtime and available filesystem access.
- Detect the operating system and active shell/tool before running shell commands.
- Record the target Obsidian vault path.
- Validate the default schema in `config/obsidian_schema.yaml`.
- Prepare a workspace Python environment at `.paper-obsidian/.venv`.
- Run the `Attention Is All You Need` smoke test when network access is available.
- Save workspace state in `.paper-obsidian/config.json`.
- Verify that an Obsidian payload can be built, validated, and dry-run published.

## Manual Environment Commands

If Python is already available, create a workspace virtual environment (`.paper-obsidian/.venv`) and install dependencies:

```bash
python scripts/setup_environment.py --use-uv --install --json-report .paper-obsidian/environment-check.json
```

The Python setup helper creates `.paper-obsidian/` paths as needed. When shell-specific commands are required, use the command block that matches the active shell/tool: PowerShell snippets belong in PowerShell, while Bash snippets belong in Bash, zsh, sh, WSL, macOS, or Linux shells.

If Python is not available yet, use the bootstrap script for your OS. These commands install or use the standalone `uv` binary first, then let uv install Python and create `.venv`.

Windows PowerShell:

```powershell
.\scripts\bootstrap_uv.ps1 -InstallUv
```

macOS/Linux:

```bash
INSTALL_UV=1 sh scripts/bootstrap_uv.sh
```

If you already have a Python environment and only want to check it:

```bash
python scripts/setup_environment.py --check-only
```

Validate the default Obsidian schema:

```bash
python scripts/schema_tool.py --command validate
```

Fetch a structured reading pack from arXiv HTML:

```bash
python scripts/fetch_arxiv_html.py 1706.03762 --output .paper-obsidian/arxiv-html-test --limit 5
```

Run the local smoke test:

```bash
python scripts/smoke_test_attention.py --output .paper-obsidian/smoke-test
```

The smoke test downloads "Attention Is All You Need", opens it with PyMuPDF, renders a first-page evidence image, writes sample metadata and report files, builds `obsidian_payload.json`, and validates the payload.

## Obsidian Vault

The default vault layout is intentionally lean:

- Notes directory: `Papers/`
- Attachments directory: `Papers/assets/`
- Metadata source: YAML frontmatter in each Markdown note.

The default frontmatter fields are:

- `title`
- `original_title`
- `authors`
- `publication_date`
- `year`
- `venue`
- `field`
- `type`
- `keywords`
- `reading_status`
- `read_date`
- `rating`
- `doi`
- `arxiv`
- `code`
- `report_language`
- `dedup_key`
- `dedup_strategy`
- `tags`

Long analytical material belongs in the Markdown body, not in frontmatter.

The machine-readable schema lives in:

```text
config/obsidian_schema.yaml
```

Render a schema summary:

```bash
python scripts/schema_tool.py --command summary
```

Render a Markdown frontmatter template:

```bash
python scripts/schema_tool.py --command template
```

## Image Handling

- Hosted arXiv HTML images can be embedded directly when they are reachable over HTTPS.
- Local evidence crops should live in the paper output folder during report generation.
- `scripts/publish_obsidian_payload.py` copies local Markdown image links into the vault attachment directory and rewrites the links relative to the note.
- Use `scripts/build_evidence_pack.py` when images are private, copyrighted, or not ready to copy into the vault.

Avoid publishing paper figures to public image hosts when the paper license or your workspace policy does not allow redistribution.

## Typical Agent Usage

Set up the workflow:

```text
Use $paper-to-obsidian-skill to set up my Obsidian paper reading workflow.

Vault path: <absolute path to my Obsidian vault>

Please detect my runtime, OS, and active shell/tool, prepare the local Python environment using commands that match the shell, run the Attention Is All You Need smoke test, save .paper-obsidian/config.json, and verify that a payload can be dry-run published to the vault.
```

Common input routing is intentionally simple:

- Local PDF: parse the PDF and crop evidence.
- arXiv link or ID: try official arXiv HTML first, including verified figure URLs; fall back to PDF.
- Publisher URL, DOI, or title: fetch metadata and accessible full-text HTML; ask for PDF if access is blocked.
- Existing report or payload: skip reading and publish only.

Read and publish a paper in English:

```text
Use $paper-to-obsidian-skill to read this paper in English and save it to my Obsidian vault:

Vault path: <absolute path to my Obsidian vault>
Paper: https://arxiv.org/abs/1706.03762

Please resolve the paper identity, extract verified metadata, capture important evidence, generate an Obsidian-ready report with formulas, figures, tables, code and reproducibility notes, create or update the Markdown note, and verify the note after publishing.
```

Read and publish a paper in Chinese:

```text
Use $paper-to-obsidian-skill to read this paper in Chinese and save it to my Obsidian vault:

Vault path: <absolute path to my Obsidian vault>
Paper: <PDF path, DOI, arXiv URL, paper URL, or title>

Please keep the official English title in Original Title, write the report body in Chinese, preserve formulas in LaTeX, include key figures and tables, and verify the Markdown note after publishing.
```

Publish an existing report:

```text
Use $paper-to-obsidian-skill to publish this existing report to my Obsidian vault:

Vault path: <absolute path to my Obsidian vault>
Report path: <report.md>
Metadata path: <metadata.json>

Please build or validate obsidian_payload.json, deduplicate by DOI/arXiv/title, create or update the Markdown note, and verify the result.
```

## Payload Workflow

Build an Obsidian payload from paper metadata and a Markdown report:

```bash
python scripts/build_obsidian_payload.py \
  --metadata metadata.json \
  --report report.md \
  --output obsidian_payload.json \
  --vault-path /path/to/obsidian-vault \
  --language English \
  --image-status local_only
```

Validate report quality:

```bash
python scripts/validate_report_quality.py report.md --payload obsidian_payload.json
```

Validate the payload:

```bash
python scripts/validate_obsidian_payload.py obsidian_payload.json --require-vault
```

Dry run and publish:

```bash
python scripts/publish_obsidian_payload.py obsidian_payload.json --dry-run
python scripts/publish_obsidian_payload.py obsidian_payload.json --if-exists update
```

Build a self-contained local evidence pack from Markdown image links:

```bash
python scripts/build_evidence_pack.py \
  --report report.md \
  --output evidence-pack.html \
  --title "Evidence Pack"
```

## Evidence And Report Policy

- Every factual claim should be traceable to the paper or an official source.
- Important formulas stay in LaTeX.
- Important numerical comparisons should become Markdown tables.
- Local-only images should resolve from the payload directory before publishing.
- Code and reproducibility notes should say what was checked and what remains unverified.
- Uncertain inferences should be labeled as uncertain.

## Configuration State

Workspace-specific setup state should live outside the repository in:

```text
.paper-obsidian/config.json
```

Typical fields:

- `runtime`
- `vault_path`
- `notes_dir`
- `attachments_dir`
- `schema_version`
- `default_report_language`

This folder is ignored by Git because it can contain local runtime state.

## Roadmap

- Batch import from text files, CSV, Zotero exports, or existing vault notes.
- Optional image cache/downloader for remote figure URLs.
- Deeper arXiv source asset extraction for higher-quality figures and tables beyond the official HTML rendering.
- Semantic Scholar or OpenAlex citation enrichment.
- Optional daily discovery mode with arXiv categories, scoring, and conference tracking.
- Team-reading workflows with assignment, priority, review status, and weekly digests.
- Local vector index for follow-up Q&A over processed papers.

## License

MIT License. See [LICENSE](LICENSE).
