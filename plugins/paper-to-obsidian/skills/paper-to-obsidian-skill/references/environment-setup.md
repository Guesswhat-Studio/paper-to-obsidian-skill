# Environment Setup

Use this reference for local dependency setup and smoke testing.

## Local State

Prefer a uv-managed virtual environment in the active workspace under `.paper-obsidian/`:

```text
.paper-obsidian/
  .venv/
  config.json
  environment-check.json
  smoke-test/
```

Keep this directory out of the skill/plugin directory so it survives plugin-cache refreshes and remains user-owned.

## Setup Commands

If Python is available:

```bash
python scripts/setup_environment.py --use-uv --install --json-report .paper-obsidian/environment-check.json
```

Fallback without uv:

```bash
python scripts/setup_environment.py --venv .paper-obsidian/.venv --install --json-report .paper-obsidian/environment-check.json
```

If Python or uv needs bootstrapping and the user approves:

```powershell
.\scripts\bootstrap_uv.ps1 -InstallUv
```

```bash
INSTALL_UV=1 sh scripts/bootstrap_uv.sh
```

## Required Python Packages

| Package | Purpose |
| --- | --- |
| `PyMuPDF` | PDF probing, text extraction, page rendering, and cropping. |
| `Pillow` | Image verification and lightweight image handling. |
| `requests` | Downloading PDFs and metadata pages. |
| `beautifulsoup4` | HTML metadata parsing. |
| `lxml` | Robust HTML/XML parser backend. |
| `PyYAML` | Obsidian frontmatter schema parsing and payload validation. |

## Optional Tools

- `git`: inspect paper code repositories.
- `gh`: authenticated GitHub lookup.
- `tesseract`: OCR scanned PDFs.
- `uv`: fast dependency setup.

## Smoke Test

Run:

```bash
python scripts/smoke_test_attention.py --output .paper-obsidian/smoke-test
```

The smoke test downloads "Attention Is All You Need", opens it with PyMuPDF, renders a first-page evidence image, writes sample metadata and report files, builds `obsidian_payload.json`, and validates the payload.

To verify vault publishing, publish the smoke-test payload into a temporary or user-approved test vault:

```bash
python scripts/publish_obsidian_payload.py .paper-obsidian/smoke-test/obsidian_payload.json --vault /path/to/test-vault --dry-run
python scripts/publish_obsidian_payload.py .paper-obsidian/smoke-test/obsidian_payload.json --vault /path/to/test-vault
```

## Common Failures

- Missing `PyMuPDF`: install dependencies into `.paper-obsidian/.venv`.
- Missing text layer: use OCR only after confirming normal text extraction is unusable.
- Vault path missing: ask for a real Obsidian vault directory or publish only the local report.
- Attachment path escapes vault: reject the path and ask for a vault-relative directory.
