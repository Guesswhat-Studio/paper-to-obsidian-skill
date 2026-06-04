#!/usr/bin/env python3
"""Build a self-contained local HTML evidence pack from Markdown image links."""

from __future__ import annotations

import argparse
import base64
import html
import mimetypes
import re
from pathlib import Path


IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def image_refs(markdown: str, base_dir: Path) -> list[tuple[str, Path]]:
    refs: list[tuple[str, Path]] = []
    for match in IMAGE_RE.finditer(markdown):
        alt = match.group(1).strip() or "Evidence image"
        raw_path = match.group(2).strip()
        if raw_path.startswith(("http://", "https://", "data:")):
            continue
        path = Path(raw_path)
        resolved = path if path.is_absolute() else base_dir / path
        refs.append((alt, resolved.resolve()))
    return refs


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def render_pack(title: str, refs: list[tuple[str, Path]]) -> str:
    figures: list[str] = []
    for index, (alt, path) in enumerate(refs, start=1):
        if not path.exists():
            figures.append(
                f'<section class="missing"><h2>{index}. {html.escape(alt)}</h2>'
                f"<p>Missing local file: <code>{html.escape(str(path))}</code></p></section>"
            )
            continue
        figures.append(
            f'<section class="figure"><h2>{index}. {html.escape(alt)}</h2>'
            f'<img src="{data_uri(path)}" alt="{html.escape(alt)}">'
            f'<p class="path">{html.escape(path.name)}</p></section>'
        )
    body = "\n".join(figures) if figures else "<p>No local Markdown images found.</p>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} Evidence Pack</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f7f7f4;
      color: #1f2933;
    }}
    body {{
      margin: 0;
      padding: 32px;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
    }}
    h1 {{
      font-size: 28px;
      margin: 0 0 20px;
    }}
    h2 {{
      font-size: 18px;
      margin: 0 0 12px;
    }}
    .figure,
    .missing {{
      background: #fff;
      border: 1px solid #d7d8d2;
      border-radius: 8px;
      margin: 0 0 20px;
      padding: 18px;
    }}
    img {{
      display: block;
      max-width: 100%;
      height: auto;
      border: 1px solid #e4e5df;
      border-radius: 4px;
      background: white;
    }}
    .path {{
      color: #606a73;
      font-size: 13px;
      margin: 10px 0 0;
    }}
    code {{
      word-break: break-all;
    }}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(title)} Evidence Pack</h1>
    {body}
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path, help="Markdown report containing local image links")
    parser.add_argument("--output", required=True, type=Path, help="Output HTML path")
    parser.add_argument("--title", default="", help="Evidence pack title")
    args = parser.parse_args()

    markdown = args.report.read_text(encoding="utf-8")
    title = args.title.strip()
    if not title:
        heading = re.search(r"^#\s+(.+)$", markdown, flags=re.MULTILINE)
        title = heading.group(1).strip() if heading else args.report.stem

    refs = image_refs(markdown, args.report.resolve().parent)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_pack(title, refs), encoding="utf-8")
    print(f"Wrote {args.output} with {len(refs)} image reference(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
