# Positioning Notes

Use this reference when preparing public copy, comparing adjacent tools, or deciding future roadmap.

## Adjacent Patterns Reviewed

- Medical and PubMed-oriented paper readers that combine PDF parsing, metadata setup, image handling, and specialty summaries.
- Standalone PDF summarizers that produce text, audio, email, or workspace exports.
- Research writing systems focused on organizing sources, arguments, and writing workflows rather than agentic paper-reading execution.
- Engineering-heavy paper tools with arXiv/OpenReview ingestion, PDF download, LaTeX source/image/table extraction, batch import, paper chat, Web UI, config checks, and schema checks.
- Daily paper discovery workflows with scoring, conference tracking, team assignment, weekly digests, and multi-view triage.
- Local-first Codex paper readers for paper folders, copied-title-to-PDF matching, source registry, interactive reading, screenshot rendering, preference capture, and concise HTML notes.
- Runtime connector models for external services through `MCP + CLI` and `Skill + CLI`, including custom MCP connectors and user-scoped authorization boundaries.

## Current Strengths

- Skill-native design for Codex, Claude, WorkBuddy, and compatible MCP/CLI agent runtimes rather than a standalone app only.
- Default English output with Chinese and bilingual modes.
- Lean Obsidian frontmatter plus rich Markdown note design.
- Evidence-driven deep reading contract: formulas, figures, tables, theorem/model/algorithm evidence, code audit, reproducibility audit.
- Local-first filesystem publishing that does not require an Obsidian connector for normal note creation.
- Single-paper Obsidian publisher with vault-safe deduplication and attachment copying.
- Source registry and reading-pack contract for papers with multiple sources.
- Official arXiv HTML reading-pack extraction for papers with available `https://arxiv.org/html/<arxiv_id>` renderings.
- Local payload generation and validation before vault writes.
- Built-in environment validation and `Attention Is All You Need` smoke test.

## Remaining Gaps

- No full CLI application or Web UI yet.
- No batch import flow yet.
- No built-in arXiv LaTeX source asset extraction or table-to-image renderer yet.
- No GitHub image hosting automation yet.
- No Semantic Scholar citation enrichment yet.
- No daily arXiv discovery, conference tracking, or 5D scoring engine yet.
- No team assignment or weekly digest workflow yet.
- No persistent paper-chat index yet.
- No PubMed-specific metadata mode yet.
- No automatic copied-title-to-local-PDF matcher yet.

## Good Future Additions

1. Batch import from `.txt`, `.md`, `.csv`, Zotero export, or existing vault notes.
2. Optional image cache/downloader for remote figure URLs.
3. Deeper arXiv source asset extraction for higher-quality figures and tables beyond the official HTML rendering.
4. Semantic Scholar/OpenAlex citation count enrichment.
5. Optional daily discovery mode with arXiv categories, keyword interests, recency/popularity/social scoring, and conference tracking.
6. Optional team-reading mode with assignee, comments, priority, status board, and weekly digest views.
7. PubMed/biomedical schema preset.
8. Local vector index for follow-up Q&A over processed papers.
9. Copied-title-to-local-PDF matcher for messy download folders.
10. A public README outside the skill folder when publishing as a GitHub repository.
