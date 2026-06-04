# Deep Paper Reading Contract

Use this contract for the paper-reading layer. It is the integrated workflow; do not ask the user to install other paper-reading skills.

## Goal

Produce a reusable research note that answers:

1. What problem does the paper solve?
2. How does the technical mechanism work?
3. Which equations, algorithms, diagrams, tables, results, and code artifacts support the claims?
4. How should a future reader find, judge, revisit, and reproduce the paper?

## Inputs

Support these input forms:

- Local PDF path.
- arXiv abstract or PDF URL.
- DOI.
- Publisher URL.
- Paper title.
- Existing local report plus metadata for publish-only use.

If the input is ambiguous, resolve the paper identity before writing. Prefer official sources over search snippets.

## Simple Input Router

Use only these common routes unless the user asks for a specialized workflow:

| Input | Route |
| --- | --- |
| Local PDF path | PDF parsing: text layer, metadata verification from page 1, evidence crops, OCR only if needed. |
| arXiv ID, abstract URL, HTML URL, or PDF URL | arXiv-first: resolve ID, fetch abstract metadata, try official HTML with `scripts/fetch_arxiv_html.py`, then fall back to PDF if HTML is unavailable or incomplete. |
| Publisher URL, DOI, or title | Metadata-first: fetch public metadata and official page; parse accessible full-text HTML when available; ask for PDF when the page is paywalled, login-gated, or abstract-only. |
| Existing `report.md`, `metadata.json`, or `obsidian_payload.json` | Publish-only: validate/build payload, deduplicate, publish, and verify. |

For arXiv HTML figures, use the official image URLs directly as hosted image links only when they are present in the HTML extraction and load over HTTPS. Trust the resolved `image_url` from `scripts/fetch_arxiv_html.py`, not raw relative `src` values from the HTML. Mark the payload `image_status` as `hosted` only when every embedded image is reachable. If any image is unreachable, use PDF crops copied into the Obsidian vault attachments directory, build a local evidence pack, or cite the figure/table label in text.

## Language Modes

- Default: English.
- Chinese: Use when explicitly requested.
- Bilingual: Use when explicitly requested. Prefer an English full report plus a compact Chinese overview unless the user asks for full section-by-section bilingual output.

## Source Resolution

1. Establish a canonical source identity.
   - DOI URL if available.
   - arXiv abstract URL if available.
   - Official publisher or project page if DOI/arXiv is unavailable.
2. For local PDFs:
   - Probe page count.
   - Extract the PDF text layer first.
   - Use OCR only when the text layer is missing or unusable.
   - Verify title, authors, and affiliations against page 1.
3. For arXiv papers:
   - Prefer the abstract page for metadata.
   - Prefer the official arXiv HTML rendering at `https://arxiv.org/html/<arxiv_id>` when available. Run `scripts/fetch_arxiv_html.py` to create a structured reading pack with title, authors, abstract, sections, verified figure URLs, tables, and equation counts.
   - Prefer HTML-linked figures/tables or source assets when they are easy to obtain and higher quality than PDF crops.
   - Use official arXiv HTML figure URLs directly only when `image_accessible` is true or the payload validator confirms the hosted image URL is reachable.
   - Use PDF crops when source assets are unavailable or unsuitable.
4. For titles or DOI:
   - Resolve to an official page before reading when network tools are available.
   - Avoid fabricating metadata when resolution fails.

## Source Registry And Reading Pack

Treat a read target as an entity with multiple possible sources. A paper may have a local PDF, arXiv page, DOI, publisher page, project page, GitHub repository, dataset page, slides, blog post, or benchmark leaderboard.

Before writing the report, prepare a compact reading pack:

- Canonical paper identity.
- Local files used.
- Official URLs checked.
- Code/data/project sources checked.
- Evidence candidates to crop or cite.
- User preferences that affect emphasis, such as implementation detail, literature-review positioning, theory depth, or concise executive summary.

If the workspace contains stable user preferences in `AGENTS.md`, local config, or prior notes, apply them when they do not conflict with the current request. Do not rewrite user preferences unless the user asks.

## Metadata To Extract

Extract and verify these fields:

- Original Title.
- Authors.
- Publication Date and Year.
- Venue.
- Field.
- Type.
- Keywords.
- DOI.
- arXiv.
- Code.
- Report Language.

Keep author names in their original spelling. Infer `Field`, `Type`, and `Keywords` from the paper content, not only the title. `Type` is the paper or contribution category, such as method or survey. `Keywords` are paper-specific topic phrases, such as model names, tasks, datasets, mechanisms, or domains.

## Paper Type Classification

Classify the paper before writing. Choose one or more:

- Method.
- Theory.
- Survey.
- Benchmark.
- Dataset.
- System.
- Empirical.
- Application.

Use the type to shift reading emphasis:

| Type | Reading emphasis |
| --- | --- |
| Method | Problem setup, mechanism, objective, architecture, training/inference flow, ablations. |
| Theory | Definitions, assumptions, theorem chain, proof intuition, boundary cases. |
| Survey | Taxonomy, field map, comparison axes, missing areas, controversy, historical positioning. |
| Benchmark | Task definition, dataset split, metrics, baselines, leakage or bias risks. |
| Dataset | Collection method, annotation protocol, licensing, quality control, representativeness. |
| System | Architecture, interfaces, scaling bottlenecks, latency/cost/reliability evidence. |
| Empirical | Hypotheses, design, metrics, controls, statistical strength, confounds. |
| Application | User/task context, deployment assumptions, value evidence, failure modes. |

## Evidence Extraction Rules

Screenshots and extracted figures are not decoration. Capture only evidence that helps future reading.

Always capture:

- A compact header image from the first page showing the paper title and authors.

Capture 2 to 5 technical-core evidence items when available:

- System model or problem formulation.
- Objective, loss, or optimization program.
- Algorithm or pseudocode block.
- Architecture or framework diagram.
- Definitions, assumptions, theorem, lemma, proposition, corollary, property, or remark.
- Key derivation or update rule.

Capture 2 to 4 validation evidence items when available:

- Main benchmark table.
- Main result figure.
- Ablation table or plot.
- Robustness, sensitivity, communication/cost, case-study, or qualitative comparison.

For every captured item:

- Include the full target block and caption when relevant.
- Avoid leaking into unrelated neighboring text, next figures, proofs, or page headers.
- Explain what the item defines, measures, proves, or compares.
- Explain what conclusion it supports and what it does not prove.

If image extraction is impossible, cite the section/page/table/figure label precisely and explain the limitation.

For Obsidian publishing, keep extracted images in the local `images/` folder during report generation. The publish script copies local image links into the vault attachment directory and rewrites links relative to the note. If images should not be copied into the vault, build a self-contained local `evidence_pack.html` and link that pack from the note body.

## Formula And Table Rules

- Preserve important formulas as LaTeX, not only screenshots.
- For system/control/filtering/observer/dynamics papers, transcribe the core system equations explicitly.
- Explain symbols in plain technical language.
- Convert important numerical comparisons into Markdown tables when doing so improves scanability.
- Keep original labels such as `Theorem 1`, `Algorithm 2`, `Table 3`, and `Figure 4` when useful.

## Code And Reproducibility Audit

Check for code before claiming code is unavailable. Use available search, paper links, project pages, arXiv comments, official author pages, and GitHub when possible.

If code is found:

- Prefer official repositories over third-party reimplementations.
- Record the URL.
- Note whether the repository appears to contain training, inference, data processing, evaluation, or only demos.
- Map the paper method to code modules when clear.
- Record commit SHA, release tag, or last observed state when available.

If code is not found:

- State which sources were checked.
- Distinguish "not found" from "unavailable."

Audit:

- Data availability.
- Environment or dependencies.
- Hyperparameters.
- Evaluation scripts.
- Missing details that block reproduction.

## Report Structure

Use this structure for English reports:

```markdown
# Paper Title

Optional image-status note when local images cannot be embedded.

## 1. Problem, Motivation, And Core Idea

## 2. Method And Technical Backbone

## 3. Formula Walkthrough

## 4. Experiments And Evidence

## 5. Ablations And Design Lessons

## 6. Code And Reproducibility Audit

## 7. Limitations And Applicability

## 8. Reader Rating

## 9. Reading Recommendations

## 10. Source Registry
```

For Chinese reports, translate section headings naturally. For bilingual reports, keep the English full report and add a compact Chinese overview near the top unless the user asks otherwise.

## Batch Mode Guardrails

For a multi-paper batch:

1. Generate and validate one representative report first, then compare it against a known good prior report or the structure in this contract before continuing the batch.
2. Use `scripts/validate_report_quality.py` for every report. Do not publish the batch if any report fails the quality gate.
3. Track each paper's image status as `hosted`, `local_only`, `placeholder`, or `no_images`. If arXiv HTML extraction reports reachable figures, the report must embed at least one hosted or local figure unless there is a documented reason not to.
4. Keep a small batch index with paper ID/title, report path, word count, image status, and validation result so failures are visible before Obsidian publishing.

## Section Expectations

- Do not include a dedicated metadata section in the note body by default. Store metadata in YAML frontmatter. Mention metadata in prose only when it affects interpretation.
- Problem, Motivation, And Core Idea: State the problem, why previous methods are insufficient, and the paper's central idea.
- Method And Technical Backbone: Walk through the architecture, algorithm, theorem chain, model, or system pipeline. Explain each evidence item in terms of what it changes in the method.
- Formula Walkthrough: Preserve the paper's core formulas as LaTeX and explain symbols, dimensions, and the reason each formula exists.
- Experiments And Evidence: Explain datasets, baselines, metrics, training/evaluation protocol, result tables/figures, and what the evidence proves versus what it only suggests.
- Ablations And Design Lessons: Interpret component variations, sensitivity, robustness, or design trade-offs. If the paper lacks ablations, state that and identify the closest substitute evidence.
- Code And Reproducibility Audit: Record code search and reproducibility blockers.
- Limitations And Applicability: Separate author-stated limitations from reader-inferred limitations.
- Reader Rating: Include a 1 to 5 star rating only if the user provides it or asks the agent to judge. Explain the reason in the note body, not only in frontmatter.
- Reading Recommendations: Include advice for beginner readers, graduate students, and senior researchers/professors. Mention mathematical derivation difficulty.
- Source Registry: Put this at the end. Include primary paper, PDF, code, project, dataset, slide, local files, extracted images, and checked-but-not-found sources.

## Quality Gate

Before publishing:

- Metadata is verified against official sources or the PDF.
- The local report passes `scripts/validate_report_quality.py`. Use `--payload obsidian_payload.json` when a payload already exists, and use `--arxiv-html-extract arxiv_html_extract.json` when an arXiv HTML reading pack exists.
- The source registry distinguishes used sources from checked-but-not-found sources.
- Local evidence images are extracted when useful; if they cannot be copied into the vault, or hosted arXiv images fail reachability checks, the note states the image limitation and points to the local evidence pack.
- Important formulas are in LaTeX.
- Technical evidence is not just summarized; it is interpreted.
- Method analysis identifies the mechanism, tensor/object flow, and design trade-offs.
- Experimental evidence names datasets, baselines, metrics, training/evaluation protocol, result values, and conclusion boundaries.
- Ablations or component variations are analyzed when the paper provides them.
- Code availability is checked or the failure to check is disclosed.
- Report language matches the user's request.
- Obsidian image status is honest: hosted, local-only, placeholder, or no images. Hosted image URLs are checked before publishing.

Example validation commands:

```bash
python scripts/validate_report_quality.py paper-output/report.md --payload paper-output/obsidian_payload.json
python scripts/validate_report_quality.py paper-output/report.md --payload paper-output/obsidian_payload.json --arxiv-html-extract paper-output/arxiv_html_extract.json --check-image-urls
```
