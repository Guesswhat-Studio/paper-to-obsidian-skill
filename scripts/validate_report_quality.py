#!/usr/bin/env python3
"""Validate a paper reading report before building or publishing an Obsidian note."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


IMAGE_STATUSES = {"hosted", "local_only", "placeholder", "no_images"}
LANGUAGES = {"English", "Chinese", "Bilingual"}
DEEP_TYPES = {"method", "system", "empirical", "benchmark", "dataset", "application"}
LIGHT_TYPES = {"survey", "theory"}
DEFAULT_DEEP_WORDS = 800
DEFAULT_LIGHT_WORDS = 650

REQUIRED_ENGLISH_HEADINGS = [
    "## 1. Problem, Motivation, And Core Idea",
    "## 2. Method And Technical Backbone",
    "## 3. Formula Walkthrough",
    "## 4. Experiments And Evidence",
    "## 5. Ablations And Design Lessons",
    "## 6. Code And Reproducibility Audit",
    "## 7. Limitations And Applicability",
    "## 8. Reader Rating",
    "## 9. Reading Recommendations",
    "## 10. Source Registry",
]

HEADING_ALIASES = {
    "source": ["## 10. Source Registry", "## 10. 来源登记", "## 10. 来源注册", "## 10. 来源清单"],
    "code": [
        "## 6. Code And Reproducibility Audit",
        "## 6. 代码与复现审计",
        "## 6. 代码和复现审计",
        "## 6. 代码与可复现性审计",
    ],
    "formula": ["## 3. Formula Walkthrough", "## 3. 公式讲解", "## 3. 公式推导", "## 3. 公式走读"],
    "evidence": ["## 4. Experiments And Evidence", "## 4. 实验与证据", "## 4. 实验和证据"],
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def strip_markdown_noise(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", text)
    text = re.sub(r"`[^`]*`", " ", text)
    return text


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", strip_markdown_noise(text)))


def heading_body(text: str, heading: str) -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    body_start = start + len(heading)
    next_heading = re.search(r"\n##\s+", text[body_start:])
    if not next_heading:
        return text[body_start:].strip()
    return text[body_start : body_start + next_heading.start()].strip()


def heading_body_any(text: str, headings: list[str]) -> str:
    for heading in headings:
        body = heading_body(text, heading)
        if body:
            return body
    return ""


def image_links(markdown: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown or "")


def remote_image_ok(link: str, timeout: int) -> tuple[bool, int | None, str, str]:
    try:
        import requests
    except ImportError as exc:
        raise SystemExit("requests is required for --check-image-urls") from exc

    headers = {"User-Agent": "paper-to-obsidian-skill/0.2"}
    try:
        response = requests.head(link, allow_redirects=True, timeout=timeout, headers=headers)
        if response.status_code in {403, 405}:
            response.close()
            response = requests.get(link, allow_redirects=True, timeout=timeout, headers=headers, stream=True)
        status_code = response.status_code
        final_url = response.url
        content_type = response.headers.get("Content-Type", "")
        response.close()
    except requests.RequestException:
        return False, None, link, ""
    return status_code < 400, status_code, final_url, content_type


def payload_props(payload: dict[str, Any]) -> dict[str, Any]:
    props = payload.get("properties")
    return props if isinstance(props, dict) else {}


def payload_content(payload: dict[str, Any]) -> dict[str, Any]:
    content = payload.get("content")
    return content if isinstance(content, dict) else {}


def as_types(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(item).strip().casefold() for item in value if str(item).strip()}
    return {item.strip().casefold() for item in re.split(r"[,;|]", str(value)) if item.strip()}


def infer_min_words(paper_types: set[str], explicit_min: int | None) -> int:
    if explicit_min is not None:
        return explicit_min
    if paper_types & LIGHT_TYPES and not (paper_types & (DEEP_TYPES - {"application"})):
        return DEFAULT_LIGHT_WORDS
    if paper_types & DEEP_TYPES:
        return DEFAULT_DEEP_WORDS
    if paper_types & LIGHT_TYPES:
        return DEFAULT_LIGHT_WORDS
    return DEFAULT_DEEP_WORDS


def reachable_html_figures(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    data = load_json(path)
    figures = data.get("figures", [])
    if not isinstance(figures, list):
        return []
    return [
        fig
        for fig in figures
        if isinstance(fig, dict) and fig.get("image_accessible") and str(fig.get("image_url", "")).startswith("https://")
    ]


def validate_structure(text: str, language: str, body_only: bool, errors: list[str], warnings: list[str]) -> None:
    if not body_only and not text.lstrip().startswith("# "):
        errors.append("missing paper title H1")

    if language == "Bilingual" and not re.search(r"中文速览|Chinese Overview", text, re.IGNORECASE):
        errors.append("bilingual report must include a compact Chinese overview")

    if language in {"English", "Bilingual"}:
        for heading in REQUIRED_ENGLISH_HEADINGS:
            if heading not in text:
                errors.append(f"missing required heading: {heading}")
                continue
            body = heading_body(text, heading)
            if word_count(body) < 25 and heading not in {"## 8. Reader Rating", "## 10. Source Registry"}:
                warnings.append(f"section is very short: {heading}")


def validate_source_and_code(text: str, errors: list[str], warnings: list[str]) -> None:
    source_body = heading_body_any(text, HEADING_ALIASES["source"])
    if not source_body:
        errors.append("missing or empty Source Registry section")
        return

    urls = re.findall(r"https?://\S+", source_body)
    if len(urls) < 2:
        warnings.append("Source Registry should include at least two official source URLs when available")

    code_body = heading_body_any(text, HEADING_ALIASES["code"])
    if not code_body:
        errors.append("missing or empty Code And Reproducibility Audit section")
        return

    audit_terms = ("checked", "found", "not found", "unavailable", "repository", "repo", "code")
    if not any(term in normalize(code_body) for term in audit_terms):
        errors.append("Code And Reproducibility Audit must say what code sources were checked or found")

    if "not found" in normalize(code_body) and "checked" not in normalize(code_body):
        warnings.append("code not-found claim should name the sources that were checked")


def validate_formulas_and_evidence(text: str, errors: list[str], warnings: list[str]) -> None:
    formula_body = heading_body_any(text, HEADING_ALIASES["formula"])
    if not formula_body:
        errors.append("missing Formula Walkthrough body")
    formula_text = normalize(formula_body)
    no_formula_terms = ("no formula", "no central mathematical", "no mathematical", "there are no formulas")
    if formula_body and "$" not in formula_body and not any(term in formula_text for term in no_formula_terms):
        warnings.append("Formula Walkthrough should include LaTeX or explicitly state why formulas are not central")

    evidence_body = heading_body_any(text, HEADING_ALIASES["evidence"])
    evidence_text = normalize(evidence_body)
    no_evidence_terms = ("no empirical evaluation", "no evaluation is reported", "no empirical study")
    if evidence_body and word_count(evidence_body) < 75 and not any(term in evidence_text for term in no_evidence_terms):
        warnings.append("Experiments And Evidence section is thin; name datasets, metrics, baselines, and boundaries when available")


def validate_images(
    text: str,
    image_status: str,
    html_figures: list[dict[str, Any]],
    check_urls: bool,
    timeout: int,
    errors: list[str],
    warnings: list[str],
) -> None:
    links = image_links(text)
    if image_status not in IMAGE_STATUSES:
        errors.append("image_status must be hosted, local_only, placeholder, or no_images")
        return

    if html_figures and image_status in {"placeholder", "no_images"}:
        errors.append("reachable arXiv HTML figures exist, but image_status does not embed available images")

    if html_figures and not links:
        errors.append("reachable arXiv HTML figures exist, but report embeds no images")
    if html_figures and links and image_status == "hosted":
        figure_urls = {str(fig.get("image_url", "")).strip() for fig in html_figures if str(fig.get("image_url", "")).strip()}
        if figure_urls and not any(link in figure_urls for link in links):
            warnings.append("report embeds hosted images, but none match the reachable arXiv HTML figure registry")

    if image_status == "hosted":
        if not links:
            errors.append("image_status is hosted but report has no Markdown image links")
        for link in links:
            if not link.startswith(("http://", "https://")):
                errors.append(f"hosted image link is not public HTTP(S): {link}")
            if link.startswith("__PUBLIC_IMAGE_PREFIX__/"):
                errors.append("image_status is hosted but report still contains placeholder image links")
        if check_urls:
            for link in links:
                if not link.startswith(("http://", "https://")):
                    continue
                ok, status_code, final_url, content_type = remote_image_ok(link, timeout)
                status = status_code if status_code is not None else "unknown"
                if not ok:
                    errors.append(f"hosted image URL is not reachable: {link} (status: {status})")
                elif content_type and not content_type.lower().startswith("image/"):
                    warnings.append(f"hosted image URL did not return image content type: {final_url} ({content_type})")

    if image_status == "no_images":
        if links:
            errors.append("image_status is no_images but report contains Markdown image links")
        if not re.search(r"no hosted images|no images|unavailable", text, re.IGNORECASE):
            warnings.append("no_images report should state the image limitation near the top")

    if image_status == "local_only":
        local_links = [link for link in links if not link.startswith(("http://", "https://"))]
        if links and not local_links:
            warnings.append("image_status is local_only but embedded images are remote HTTP(S) links")
        if not re.search(r"evidence_pack\.html|local evidence pack|local-image|local images|local_only|local-only|local only|attachments", text, re.IGNORECASE):
            warnings.append("local_only report should mention copied attachments, an evidence pack, or another local-image note")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Markdown report to validate")
    parser.add_argument("--payload", type=Path, help="Optional Obsidian payload for language, paper type, and image status")
    parser.add_argument("--language", choices=sorted(LANGUAGES), help="Expected report language")
    parser.add_argument("--image-status", choices=sorted(IMAGE_STATUSES), help="Expected image status")
    parser.add_argument("--paper-type", action="append", help="Paper type; repeat for multiple values")
    parser.add_argument("--min-words", type=int, help="Override minimum report word count")
    parser.add_argument("--body-only", dest="body_only", action="store_true", help="Allow a page body without a top-level H1 title")
    parser.add_argument("--arxiv-html-extract", type=Path, help="arxiv_html_extract.json with image_accessible flags")
    parser.add_argument("--check-image-urls", action="store_true", help="Check hosted Markdown image URLs over HTTP")
    parser.add_argument("--image-timeout", type=int, default=20, help="Per-image URL check timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable result JSON")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    if not args.report.exists():
        errors.append(f"report does not exist: {args.report}")
        result = {"errors": errors, "warnings": warnings}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"ERROR: {errors[0]}")
        return 1

    text = args.report.read_text(encoding="utf-8")
    payload: dict[str, Any] = {}
    if args.payload:
        payload = load_json(args.payload)

    props = payload_props(payload)
    content = payload_content(payload)
    language = args.language or str(props.get("Report Language") or "").strip() or "English"
    if language not in LANGUAGES:
        errors.append(f"unsupported report language: {language}")
        language = "English"

    image_status = args.image_status or str(content.get("image_status") or "").strip() or "no_images"
    paper_types = as_types(args.paper_type or props.get("Type"))
    min_words = infer_min_words(paper_types, args.min_words)
    count = word_count(text)

    if count < min_words:
        errors.append(f"report too short: {count} words < {min_words}")

    validate_structure(text, language, args.body_only, errors, warnings)
    validate_source_and_code(text, errors, warnings)
    validate_formulas_and_evidence(text, errors, warnings)
    validate_images(
        text,
        image_status,
        reachable_html_figures(args.arxiv_html_extract),
        args.check_image_urls,
        args.image_timeout,
        errors,
        warnings,
    )

    result = {
        "report": str(args.report),
        "language": language,
        "paper_types": sorted(paper_types),
        "word_count": count,
        "min_words": min_words,
        "image_status": image_status,
        "image_links": len(image_links(text)),
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for warning in warnings:
            print(f"WARNING: {warning}")
        for error in errors:
            print(f"ERROR: {error}")
        if not errors:
            print("Report quality validation passed")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
