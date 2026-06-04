#!/usr/bin/env python3
"""Fetch and summarize an arXiv HTML paper rendering."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


ARXIV_ID_RE = re.compile(r"(?P<id>\d{4}\.\d{4,5}(?:v\d+)?|[a-z-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?)")


def normalize_arxiv_id(value: str) -> str:
    match = ARXIV_ID_RE.search(value.strip())
    if not match:
        raise ValueError(f"Could not find an arXiv identifier in: {value}")
    return match.group("id")


def html_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/html/{arxiv_id}"


def text_of(node: Any) -> str:
    if node is None:
        return ""
    return " ".join(node.get_text(" ", strip=True).split())


def first_text(soup: BeautifulSoup, selectors: list[str]) -> str:
    for selector in selectors:
        node = soup.select_one(selector)
        value = text_of(node)
        if value:
            return value
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    return " ".join(title.split())


def element_id(node: Any, fallback: str) -> str:
    value = node.get("id") if node is not None else ""
    return str(value or fallback)


def resolve_asset_url(base_url: str, src: str) -> str:
    """Resolve arXiv HTML asset URLs against the paper document URL.

    arXiv HTML currently emits at least two relative asset shapes:
    - `2605.29582v1/x1.png`, which is a sibling under `/html/`.
    - `extracted/...` or `figures/...`, which is relative to the paper HTML
      document directory.
    """
    src = str(src or "").strip()
    if not src or src.startswith("data:"):
        return ""
    if src.startswith(("http://", "https://", "//", "/")):
        return urljoin(base_url, src)
    if re.match(r"^\d{4}\.\d{4,5}(?:v\d+)?/", src):
        return urljoin(base_url, src)
    return urljoin(base_url.rstrip("/") + "/", src)


def check_image_url(
    session: requests.Session,
    url: str,
    timeout: int = 20,
) -> tuple[bool, int | None, str, str]:
    if not url:
        return False, None, "", ""

    headers = {"User-Agent": "paper-to-obsidian-skill/0.2"}
    try:
        response = session.head(url, allow_redirects=True, timeout=timeout, headers=headers)
        if response.status_code in {403, 405}:
            response.close()
            response = session.get(url, allow_redirects=True, timeout=timeout, headers=headers, stream=True)
        status_code = response.status_code
        final_url = response.url
        content_type = response.headers.get("Content-Type", "")
        response.close()
    except requests.RequestException:
        return False, None, url, ""

    return status_code < 400, status_code, final_url, content_type


def collect_sections(soup: BeautifulSoup, limit: int | None = None) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    for index, section in enumerate(soup.select("section.ltx_section, section"), start=1):
        heading = section.select_one(".ltx_title, h1, h2, h3, h4, h5, h6")
        title = text_of(heading)
        if not title:
            continue
        sections.append({"id": element_id(section, f"section-{index}"), "title": title})
        if limit and len(sections) >= limit:
            break
    return sections


def collect_figures(
    soup: BeautifulSoup,
    base_url: str,
    limit: int | None = None,
    check_images: bool = True,
    image_timeout: int = 20,
) -> list[dict[str, Any]]:
    figures: list[dict[str, Any]] = []
    session = requests.Session()
    for index, figure in enumerate(soup.select("figure"), start=1):
        image = figure.find("img")
        if not image:
            continue
        caption = text_of(figure.select_one("figcaption")) or text_of(figure)
        src = image.get("src", "")
        alt = image.get("alt", "")
        candidate_url = resolve_asset_url(base_url, src)
        image_url = candidate_url
        image_accessible: bool | None = None
        image_status_code: int | None = None
        image_content_type = ""
        if check_images and candidate_url:
            image_accessible, image_status_code, final_url, image_content_type = check_image_url(
                session,
                candidate_url,
                timeout=image_timeout,
            )
            image_url = final_url if image_accessible else ""
        figures.append(
            {
                "id": element_id(figure, f"figure-{index}"),
                "image_url": image_url,
                "candidate_image_url": candidate_url,
                "image_accessible": image_accessible,
                "image_status_code": image_status_code,
                "image_content_type": image_content_type,
                "alt": " ".join(str(alt).split()),
                "caption": caption,
            }
        )
        if limit and len(figures) >= limit:
            break
    return figures


def collect_tables(soup: BeautifulSoup, limit: int | None = None) -> list[dict[str, str]]:
    tables: list[dict[str, str]] = []
    seen: set[str] = set()
    candidates = list(soup.select("figure, table"))
    for index, table in enumerate(candidates, start=1):
        classes = set(table.get("class") or [])
        node_id = element_id(table, f"table-{index}")
        parent_figure = table.find_parent("figure") if table.name == "table" else None
        if parent_figure is not None and ".T" in element_id(parent_figure, ""):
            continue
        if node_id in seen:
            continue
        if "ltx_equation" in classes or ".E" in node_id:
            continue
        caption = text_of(table.select_one("caption")) or text_of(table)
        if not caption:
            continue
        looks_like_table = ".T" in node_id or "ltx_table" in classes or caption.lower().startswith("table")
        if not looks_like_table:
            continue
        seen.add(node_id)
        tables.append({"id": node_id, "caption": caption[:1000]})
        if limit and len(tables) >= limit:
            break
    return tables


def extract(
    html: str,
    url: str,
    arxiv_id: str,
    limit: int | None = None,
    check_images: bool = True,
    image_timeout: int = 20,
) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    title = first_text(soup, ["h1.ltx_title_document", "h1.ltx_title", ".ltx_title_document", "h1"])
    authors = first_text(soup, [".ltx_authors", ".authors"])
    abstract_node = soup.select_one(".ltx_abstract")
    abstract = text_of(abstract_node)
    abstract = re.sub(r"^Abstract\s+", "", abstract, flags=re.IGNORECASE)

    equations = soup.select(".ltx_equation, table.ltx_equation")
    return {
        "arxiv_id": arxiv_id,
        "html_url": url,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "sections": collect_sections(soup, limit=limit),
        "figures": collect_figures(
            soup,
            url,
            limit=limit,
            check_images=check_images,
            image_timeout=image_timeout,
        ),
        "tables": collect_tables(soup, limit=limit),
        "equation_count": len(equations),
    }


def write_markdown(data: dict[str, Any], path: Path) -> None:
    lines: list[str] = [
        f"# arXiv HTML Reading Pack: {data.get('title') or data.get('arxiv_id')}",
        "",
        f"- arXiv: https://arxiv.org/abs/{data['arxiv_id']}",
        f"- HTML: {data['html_url']}",
        f"- Equation-like blocks: {data['equation_count']}",
        "",
    ]
    if data.get("authors"):
        lines.extend(["## Authors", "", str(data["authors"]), ""])
    if data.get("abstract"):
        lines.extend(["## Abstract", "", str(data["abstract"]), ""])

    lines.extend(["## Sections", ""])
    for section in data.get("sections", []):
        lines.append(f"- `{section['id']}` {section['title']}")
    lines.append("")

    lines.extend(["## Figures", ""])
    for figure in data.get("figures", []):
        label = f"- `{figure['id']}`"
        if figure.get("image_url"):
            label += f" {figure['image_url']}"
        elif figure.get("candidate_image_url"):
            status = figure.get("image_status_code") or "unknown"
            label += f" unavailable image: {figure['candidate_image_url']} (status: {status})"
        lines.append(label)
        if figure.get("caption"):
            lines.append(f"  {figure['caption']}")
    lines.append("")

    lines.extend(["## Tables", ""])
    for table in data.get("tables", []):
        lines.append(f"- `{table['id']}` {table['caption']}")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper", help="arXiv ID, abstract URL, PDF URL, or HTML URL")
    parser.add_argument("--output", type=Path, default=Path(".paper-obsidian/arxiv-html"))
    parser.add_argument("--limit", type=int, default=0, help="Limit sections/figures/tables in the output")
    parser.add_argument("--save-html", action="store_true", help="Save the fetched HTML beside the extracted files")
    parser.add_argument("--no-check-images", action="store_true", help="Skip HTTP checks for extracted figure URLs")
    parser.add_argument("--image-timeout", type=int, default=20, help="Per-image URL check timeout in seconds")
    args = parser.parse_args()

    arxiv_id = normalize_arxiv_id(args.paper)
    url = html_url(arxiv_id)
    response = requests.get(url, timeout=60, headers={"User-Agent": "paper-to-obsidian-skill/0.2"})
    if response.status_code == 404:
        raise RuntimeError(f"arXiv HTML rendering is unavailable for {arxiv_id}: {url}")
    response.raise_for_status()

    args.output.mkdir(parents=True, exist_ok=True)
    limit = args.limit or None
    data = extract(
        response.text,
        url,
        arxiv_id,
        limit=limit,
        check_images=not args.no_check_images,
        image_timeout=args.image_timeout,
    )

    json_path = args.output / "arxiv_html_extract.json"
    markdown_path = args.output / "arxiv_html_reading_pack.md"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(data, markdown_path)
    if args.save_html:
        (args.output / "paper.html").write_text(response.text, encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
