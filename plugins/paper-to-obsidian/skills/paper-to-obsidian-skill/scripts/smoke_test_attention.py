#!/usr/bin/env python3
"""Run a local smoke test with Attention Is All You Need."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import fitz
import requests
from PIL import Image


TITLE = "Attention Is All You Need"
ARXIV_URL = "https://arxiv.org/abs/1706.03762"
PDF_URL = "https://arxiv.org/pdf/1706.03762"
CODE_URL = "https://github.com/tensorflow/tensor2tensor"


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def download_pdf(path: Path) -> None:
    response = requests.get(PDF_URL, timeout=60)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "pdf" not in content_type.lower() and not response.content.startswith(b"%PDF"):
        raise RuntimeError(f"Downloaded content does not look like a PDF: {content_type}")
    path.write_bytes(response.content)


def render_header(pdf_path: Path, image_path: Path) -> str:
    doc = fitz.open(pdf_path)
    try:
        if doc.page_count < 1:
            raise RuntimeError("PDF has no pages")
        page = doc[0]
        text = page.get_text("text")
        normalized = " ".join(text.split()).lower()
        for word in TITLE.lower().split():
            if word not in normalized:
                raise RuntimeError(f"Expected title word missing from first page text: {word}")

        matrix = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        full_path = image_path.with_name("first_page_full.png")
        pix.save(full_path)
    finally:
        doc.close()

    with Image.open(full_path) as image:
        width, height = image.size
        header = image.crop((0, 0, width, int(height * 0.36)))
        header.save(image_path)
    full_path.unlink(missing_ok=True)
    return text


def write_metadata(path: Path) -> None:
    metadata = {
        "Original Title": TITLE,
        "Authors": "Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin",
        "Publication Date": "2017-06-12",
        "Year": 2017,
        "Venue": ["NeurIPS", "arXiv"],
        "Field": ["Machine Learning", "Natural Language Processing"],
        "Type": ["method", "empirical"],
        "Keywords": ["transformer", "attention", "sequence transduction"],
        "DOI": "",
        "arXiv": ARXIV_URL,
        "Code": CODE_URL,
        "Report Language": "English",
        "Reading Status": "Read",
        "Rating": "5 stars",
    }
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(path: Path, page_count: int) -> None:
    report = f"""# [TEST] {TITLE}

![Header](__PUBLIC_IMAGE_PREFIX__/header.png)

## 0. Metadata

- Original Title: {TITLE}
- Authors: Ashish Vaswani et al.
- Publication Date: 2017-06-12
- Venue: NeurIPS, arXiv
- arXiv: {ARXIV_URL}
- Code: {CODE_URL}

## 1. One-Sentence Summary

This smoke-test report confirms that the local environment can download a paper PDF, open it with PyMuPDF, extract first-page text, render a header image, and build an Obsidian payload.

## 2. Local Test Evidence

- Downloaded PDF: `{PDF_URL}`
- Parsed page count: `{page_count}`
- Header image saved locally: `images/header.png`

## 3. Publishing Note

This is a setup validation artifact. It can be published to a temporary Obsidian vault to verify note and attachment writing.
"""
    path.write_text(report, encoding="utf-8")


def run_payload_build(output_dir: Path) -> None:
    root = skill_root()
    payload_path = output_dir / "obsidian_payload.json"
    build_script = root / "scripts" / "build_obsidian_payload.py"
    validate_script = root / "scripts" / "validate_obsidian_payload.py"

    subprocess.check_call(
        [
            sys.executable,
            str(build_script),
            "--metadata",
            str(output_dir / "metadata.json"),
            "--report",
            str(output_dir / "report.md"),
            "--output",
            str(payload_path),
            "--image-status",
            "placeholder",
            "--rating",
            "5 stars",
        ]
    )
    subprocess.check_call([sys.executable, str(validate_script), str(payload_path)])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".paper-obsidian/smoke-test"))
    args = parser.parse_args()

    output_dir = args.output
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = output_dir / "attention-is-all-you-need.pdf"
    header_path = images_dir / "header.png"
    metadata_path = output_dir / "metadata.json"
    report_path = output_dir / "report.md"

    print(f"Downloading {PDF_URL}")
    download_pdf(pdf_path)

    print("Opening PDF and rendering header")
    render_header(pdf_path, header_path)
    doc = fitz.open(pdf_path)
    try:
        page_count = doc.page_count
    finally:
        doc.close()

    write_metadata(metadata_path)
    write_report(report_path, page_count)

    print("Building and validating Obsidian payload")
    run_payload_build(output_dir)

    print(f"Smoke test passed: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
