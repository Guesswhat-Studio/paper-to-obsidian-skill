---
name: paper-to-obsidian-skill
description: Evidence-driven academic paper reading and Obsidian vault publishing workflow. Use when an agent needs to set up a local Obsidian paper-reading workflow, read an academic paper from a local PDF, arXiv URL, DOI, paper URL, or title, extract metadata and source-grounded evidence, generate an English-by-default Markdown report with figures, formulas, tables, code/reproducibility notes, optional Chinese or bilingual output, and create or update a Markdown note with YAML frontmatter and local attachments in an Obsidian vault across Codex, Claude, WorkBuddy, or compatible CLI runtimes.
---

# Paper To Obsidian Skill

## Overview

Use this skill to turn papers into durable Obsidian notes. The note body carries the reading report; YAML frontmatter carries indexing fields for search, graph, tags, and optional Dataview queries. Default to English reports unless the user requests Chinese or bilingual output.

## Paths And Running Scripts

All `scripts/...` and `references/...` paths are relative to the skill root, the directory that contains this `SKILL.md`.

- **Claude plugin installs**: shell commands may run from the user's project directory, so prefix scripts with the skill root when needed.
- **Codex or generic skill installs**: run commands from the skill directory when relative paths are convenient.

Durable, user-owned setup state is written to the active workspace under `.paper-obsidian/`, never into the skill/plugin directory.

## Workflow Decision

- **Setup request**: If the user asks to initialize, configure, or test the workflow, read `references/environment-setup.md`, `references/obsidian-vault-schema.md`, `references/schema-customization.md`, and `references/prompt-pack.md`.
- **Paper reading request**: If the user provides a PDF, arXiv URL, DOI, paper URL, or title and asks to read, summarize, explain, review, or save it to Obsidian, read `references/deep-reading-contract.md`, then publish with `references/obsidian-publishing.md`.
- **Publish-only request**: If the user already has a report or `obsidian_payload.json`, skip paper reading and run only the Obsidian validation and publishing steps.
- **Research-flow request**: If the user asks for daily arXiv discovery, conference tracking, paper scoring, team assignment, or weekly digests, keep the default frontmatter lean unless the user approves discovery/team fields.

## Simple Input Router

1. **Local PDF**: Use the PDF path. Extract the text layer, crop useful evidence images, and use OCR only when the text layer is missing or unusable.
2. **arXiv link or ID**: Resolve the arXiv ID, fetch metadata from the abstract page, then try `scripts/fetch_arxiv_html.py`. If official HTML is available, use it for sections, formulas, tables, and verified figure URLs. If HTML is unavailable or incomplete, fall back to the PDF path.
3. **Publisher URL, DOI, or title**: Fetch public metadata and resolve the official page. If full-text HTML is accessible, parse it. If access is blocked or only abstract metadata is public, ask the user for the PDF and continue through the PDF path.
4. **Existing report or payload**: Skip reading. Validate or build `obsidian_payload.json`, deduplicate, publish, and verify.

For arXiv HTML figures, official `https://arxiv.org/html/...` image URLs may be left as hosted Markdown images when accessible. For local-first notes, prefer PDF crops or downloaded evidence images copied into the vault attachments directory by `scripts/publish_obsidian_payload.py`.

## Setup Layer

1. Detect the runtime and local filesystem access. Obsidian does not require an MCP connector for the default workflow; the vault is a normal directory of Markdown files.
2. Prepare and verify the local paper-reading environment.
   - Read `references/environment-setup.md`.
   - Check Python, required Python packages, optional OCR/tools, and network access.
   - Prefer a uv-managed virtual environment in the active workspace at `.paper-obsidian/.venv`.
   - If Python is already available, use `python scripts/setup_environment.py --use-uv --install`.
   - If Python is missing, do not try to run Python scripts. Use the OS bootstrap script after the user approves uv/Python installation: `.\scripts\bootstrap_uv.ps1 -InstallUv` on Windows, or `INSTALL_UV=1 sh scripts/bootstrap_uv.sh` on macOS/Linux.
   - Run `python scripts/smoke_test_attention.py` after dependency setup when network access is available.
3. Configure the vault.
   - Use `config/obsidian_schema.yaml` as the machine-readable frontmatter schema source.
   - Validate customized schemas with `scripts/schema_tool.py --command validate`.
   - Default note directory: `Papers`.
   - Default attachment directory: `Papers/assets`.
4. Save local setup state in `.paper-obsidian/config.json` in the active workspace.
   - Include `runtime`, `vault_path`, `notes_dir`, `attachments_dir`, `schema_version`, and `default_report_language`.
5. Verify by publishing a dry run or harmless smoke-test note into a temporary/test vault when the user asks for end-to-end validation.

## Reading Layer

Read `references/deep-reading-contract.md` before processing a paper. The reading layer must:

- Resolve the paper identity from PDF, arXiv, DOI, URL, or title.
- Build a compact source registry and reading pack before writing.
- Extract and verify metadata from the paper itself or official sources.
- For arXiv papers, prefer the official arXiv HTML rendering at `https://arxiv.org/html/<arxiv_id>` when available. Use `scripts/fetch_arxiv_html.py` to build a structured reading pack with validated figure URLs before falling back to PDF text/crops.
- Classify the paper type and adapt the reading strategy.
- Capture evidence: title/author header, formulas, algorithms, theorems, models, architecture diagrams, result figures, tables, ablations, and robustness panels as applicable.
- Explain every evidence block in terms of its role in the paper's argument.
- Search for official code or implementation evidence, then record what was checked.
- Keep factual claims source-grounded and mark uncertain inferences explicitly.

## Writing And Publishing Layer

Read `references/obsidian-publishing.md` before writing to the vault. The writing layer must:

- Create a complete Markdown report body with deep method, formula, experiment, ablation, limitation, and reproducibility analysis.
- Store indexing metadata in YAML frontmatter. Avoid duplicating a long metadata section in the body unless it helps the reader.
- Preserve formulas as normal Markdown/LaTeX.
- Extract useful local evidence images from the PDF when possible. Keep local images in the paper output folder first; the publish script copies them into the vault attachments directory and rewrites Markdown links.
- Run `scripts/validate_report_quality.py` on the report before building or publishing the Obsidian payload. Treat validation errors as a stop condition: fix the report instead of publishing a shallow note.
- Generate `obsidian_payload.json` before writing when possible, then validate it with `scripts/validate_obsidian_payload.py`. If `content.image_status` is `hosted`, run the validator with `--check-image-urls` before publishing.
- Use DOI, arXiv ID, or normalized original title for deduplication.
- Create a new note when no match exists; update the existing note when a match exists.
- Verify that the Markdown note exists, frontmatter is present, and referenced local attachments exist.

## Language Policy

- Default report language: English.
- Use Chinese only when the user asks for Chinese output.
- Use bilingual output when the user asks for bilingual, dual-language, English and Chinese, or similar wording.
- For bilingual reports, prefer an English full report with a compact Chinese overview unless the user asks for full section-by-section bilingual writing.
- Store the selected language in the `report_language` frontmatter field.

## Required Frontmatter Fields

Use this compact schema unless the user asks to customize it:

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

Do not add long analytical fields such as contribution, technical core, limitations, or evidence summary to frontmatter by default. Put those in the note body.

## Useful Scripts

- `scripts/setup_environment.py`: Check Python/PDF dependencies and optionally create the workspace `.paper-obsidian/.venv`.
- `scripts/fetch_arxiv_html.py`: Fetch official arXiv HTML renderings and extract title, authors, abstract, sections, verified figures, tables, and equation counts into a reading pack.
- `scripts/smoke_test_attention.py`: Download and parse the Attention Is All You Need paper, then generate a local test report and payload.
- `scripts/schema_tool.py`: Validate `config/obsidian_schema.yaml` and render a frontmatter template.
- `scripts/build_obsidian_payload.py`: Normalize metadata and report paths into an `obsidian_payload.json` file.
- `scripts/build_evidence_pack.py`: Build a self-contained local HTML evidence pack from Markdown image links when useful.
- `scripts/validate_report_quality.py`: Validate report depth, required sections, bilingual overview, image policy, code audit, source registry, and arXiv hosted-figure usage before payload creation or publishing.
- `scripts/validate_obsidian_payload.py`: Validate required fields, language, rating, URLs, dedup key, vault-relative paths, report existence, local image sources, and optionally hosted image reachability before publishing.
- `scripts/publish_obsidian_payload.py`: Single-paper Obsidian publisher. Validates a payload, deduplicates by DOI/arXiv/title, then creates or updates one Markdown note in the vault.

## Final Response

When the task completes, report only the useful handoff details:

- Obsidian note path.
- Local report path, if one was produced.
- Image status: hosted, local-only, placeholder, or no images.
- Validation result and any remaining manual step.
