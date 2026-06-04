# Environment Setup

Use this reference for local dependency setup and smoke testing.

## Shell And OS Preflight

Before running setup commands, detect both the operating system and the active shell/tool. The OS decides paths and bootstrap choices; the active shell decides command syntax.

- Use PowerShell cmdlets such as `New-Item`, `Copy-Item`, and `.\scripts\bootstrap_uv.ps1` only in a PowerShell tool.
- Use POSIX commands such as `mkdir -p`, `cp -R`, and `sh scripts/bootstrap_uv.sh` only in Bash, zsh, sh, WSL, or another POSIX-like shell.
- If Claude Code or Codex exposes both Bash and PowerShell tools, choose the tool that matches the command block. Do not run PowerShell commands in Bash.
- Prefer `python scripts/setup_environment.py ...` when Python is already available. It creates `.paper-obsidian/` and report directories as needed, so pre-creating the directory with shell-specific commands is usually unnecessary.

Useful preflight checks:

```bash
uname -a
python --version || python3 --version
uv --version || true
```

```powershell
$PSVersionTable.PSVersion
python --version
uv --version
```

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

PowerShell:

```powershell
.\scripts\bootstrap_uv.ps1 -InstallUv
```

Bash, zsh, sh, WSL, macOS, or Linux:

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
