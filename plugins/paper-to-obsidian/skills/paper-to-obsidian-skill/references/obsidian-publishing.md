# Obsidian Publishing

Use this reference after reading the paper or when publishing an existing report.

## Principle

The Obsidian note body is the report. YAML frontmatter is the lean index. Keep long analysis, formulas, tables, and review notes in the Markdown body.

## Output Files

For each paper run, keep a dedicated local folder when possible:

```text
paper-output/
  metadata.json
  report.md
  obsidian_payload.json
  images/
```

`report.md` is the note body source. `obsidian_payload.json` is the structured bridge to the vault.

## Report Quality Validation

Run the report quality validator before building or publishing a payload:

```bash
python scripts/validate_report_quality.py paper-output/report.md --language Bilingual --image-status hosted --arxiv-html-extract paper-output/arxiv_html_extract.json --check-image-urls
```

If a payload already exists, let the validator read language, paper type, and image status from it:

```bash
python scripts/validate_report_quality.py paper-output/report.md --payload paper-output/obsidian_payload.json
```

Validation errors are publish blockers. Warnings should be reviewed; they often indicate a thin experiment section, missing formula explanation, or weak local-image note.

## Payload Shape

Use this JSON shape:

```json
{
  "vault": {
    "path": "",
    "notes_dir": "Papers",
    "attachments_dir": "Papers/assets"
  },
  "dedup": {
    "key": "",
    "strategy": "doi|arxiv|title"
  },
  "properties": {
    "Name": "",
    "Original Title": "",
    "Authors": "",
    "Publication Date": "",
    "Year": 0,
    "Venue": [],
    "Field": [],
    "Type": [],
    "Keywords": [],
    "Reading Status": "Read",
    "Read Date": "",
    "Rating": "",
    "DOI": "",
    "arXiv": "",
    "Code": "",
    "Report Language": "English"
  },
  "content": {
    "report_path": "report.md",
    "image_status": "hosted|local_only|placeholder|no_images",
    "public_image_prefix": "",
    "markdown": ""
  }
}
```

Use blank strings for unknown optional URLs. Omit `Rating` or use blank if the reader has not rated the paper.

## Build And Validate

Build a payload from metadata and a Markdown report:

```bash
python scripts/build_obsidian_payload.py --metadata metadata.json --report report.md --output obsidian_payload.json --vault-path /path/to/vault
```

Validate before writing:

```bash
python scripts/validate_obsidian_payload.py obsidian_payload.json --require-vault
```

For `local_only` payloads, validation checks that local Markdown image links resolve from the payload directory before publishing.

If hosted images are used, check them:

```bash
python scripts/validate_obsidian_payload.py obsidian_payload.json --check-image-urls --require-vault
```

## Publish

Dry run first when a vault path is new:

```bash
python scripts/publish_obsidian_payload.py obsidian_payload.json --dry-run
```

Then write:

```bash
python scripts/publish_obsidian_payload.py obsidian_payload.json --if-exists update
```

You can override the payload vault path:

```bash
python scripts/publish_obsidian_payload.py obsidian_payload.json --vault /path/to/vault
```

## Image Policy

- PDF images and evidence crops should be extracted locally when useful. Keep them in `images/` during report generation.
- The publish script copies local Markdown image links into `attachments_dir/<paper-slug>/` and rewrites links relative to the note.
- Remote `http(s)` image links are left unchanged.
- Placeholder links such as `__PUBLIC_IMAGE_PREFIX__/header.png` are resolved against the output `images/` directory when a matching file exists.
- If images are private, copyrighted, or not ready to put in the vault, use `scripts/build_evidence_pack.py` and link the local evidence pack in the note body.

## Math Policy

Keep normal Markdown/LaTeX syntax, such as `$K$` and `$$...$$`. Obsidian and common math plugins expect ordinary Markdown math, so do not convert inline math into Notion enhanced Markdown.

## Dedup Query

Prefer DOI, then arXiv, then normalized title. The publisher scans existing Markdown notes under `notes_dir` and compares:

- `dedup_key`
- `doi`
- `arxiv`
- `original_title`
- `title`

## Create Or Update Logic

1. Validate the report body with `scripts/validate_report_quality.py`.
2. Build and validate `obsidian_payload.json`.
3. Scan the note directory for duplicates.
4. If no duplicate exists, create a new note using a year-title filename.
5. If a duplicate exists:
   - `--if-exists update` replaces the generated note body by default.
   - `--body-mode append` appends the new report after a divider.
   - `--body-mode none` updates only frontmatter.
6. Verify that the note exists and local attachment links point to copied files.

## Verification Checklist

After publishing:

- The local report passed `scripts/validate_report_quality.py`.
- The note exists under the configured vault.
- The note starts with YAML frontmatter.
- The report body is present and starts with the title or first report section.
- Local images were copied or intentionally left remote/absent.
- The note can be found by title, DOI, arXiv ID, author, or keyword through Obsidian search.
