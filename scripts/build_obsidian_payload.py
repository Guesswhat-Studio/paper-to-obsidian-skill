#!/usr/bin/env python3
"""Build an Obsidian paper payload from metadata and an optional report."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


LANGUAGES = {"English", "Chinese", "Bilingual"}
RATINGS = {"", "1 star", "2 stars", "3 stars", "4 stars", "5 stars"}
IMAGE_STATUSES = {"hosted", "local_only", "placeholder", "no_images"}
DEFAULT_SCHEMA = Path(__file__).resolve().parents[1] / "config" / "obsidian_schema.yaml"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_schema(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except ImportError:
        print("WARNING: PyYAML is unavailable; skipping schema option filtering")
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def schema_property_map(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    properties = schema.get("properties", [])
    if not isinstance(properties, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for prop in properties:
        if not isinstance(prop, dict):
            continue
        name = str(prop.get("name", "")).strip()
        if name:
            result[name] = prop
    return result


def option_names(prop: dict[str, Any] | None) -> set[str]:
    if not prop:
        return set()
    options = prop.get("options", []) or []
    return {str(option.get("name", "")).strip() for option in options if isinstance(option, dict)}


def filter_configured_options(field: str, values: list[str], prop: dict[str, Any] | None) -> list[str]:
    allowed = option_names(prop)
    prop_type = str((prop or {}).get("type", "")).strip().upper()
    strict_options = bool((prop or {}).get("strict_options", False))
    if not allowed or (prop_type == "LIST" and not strict_options):
        return values
    kept: list[str] = []
    skipped: list[str] = []
    for value in values:
        if value in allowed:
            kept.append(value)
        else:
            skipped.append(value)
    if skipped:
        print(f"WARNING: {field} values skipped because they are not configured options: {', '.join(skipped)}")
    return kept


def configured_option_or_default(field: str, value: str, prop: dict[str, Any] | None, fallback: str = "") -> str:
    allowed = option_names(prop)
    if not allowed or not value or value in allowed:
        return value
    default = str((prop or {}).get("default", "")).strip()
    if default in allowed:
        print(f"WARNING: {field} value {value!r} is not configured; using schema default {default!r}")
        return default
    print(f"WARNING: {field} value {value!r} is not configured; using fallback {fallback!r}")
    return fallback if fallback in allowed or not allowed else ""


def first_value(data: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    props = data.get("properties")
    if isinstance(props, dict):
        for key in keys:
            if key in props and props[key] not in (None, ""):
                return props[key]
    return default


def as_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[,;|]", value) if item.strip()]
    return [str(value).strip()]


def keyword_list(value: Any) -> list[str]:
    return as_list(value)


def infer_year(publication_date: str, explicit_year: Any) -> int | None:
    if explicit_year not in (None, ""):
        try:
            return int(explicit_year)
        except (TypeError, ValueError):
            pass
    match = re.search(r"(19|20)\d{2}", publication_date or "")
    if match:
        return int(match.group(0))
    return None


def normalize_title(title: str) -> str:
    text = unicodedata.normalize("NFKC", title).casefold()
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def normalize_doi(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    match = re.search(r"10\.\d{4,9}/\S+", value, re.IGNORECASE)
    if match:
        doi = match.group(0).rstrip(".,)")
        return f"https://doi.org/{doi}"
    return value


def normalize_arxiv(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    match = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", value)
    if match:
        return f"https://arxiv.org/abs/{match.group(1)}"
    old_style = re.search(r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?", value, re.IGNORECASE)
    if old_style:
        return f"https://arxiv.org/abs/{old_style.group(1)}"
    return value


def dedup_key(doi: str, arxiv: str, original_title: str) -> tuple[str, str]:
    if doi:
        return doi.lower(), "doi"
    if arxiv:
        match = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", arxiv)
        if match:
            return match.group(1).lower(), "arxiv"
        old_style = re.search(r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?", arxiv, re.IGNORECASE)
        if old_style:
            return old_style.group(1).lower(), "arxiv"
        return arxiv.lower(), "arxiv"
    return normalize_title(original_title), "title"


def stable_report_path(report: Path, output: Path) -> str:
    output_parent = output.resolve().parent
    report_path = report.resolve()
    try:
        return report_path.relative_to(output_parent).as_posix()
    except ValueError:
        return str(report_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path, help="Metadata JSON path")
    parser.add_argument("--report", type=Path, help="Report Markdown path")
    parser.add_argument("--config", type=Path, help=".paper-obsidian/config.json path")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="Obsidian frontmatter schema YAML path")
    parser.add_argument("--output", type=Path, default=Path("obsidian_payload.json"))
    parser.add_argument("--language", choices=sorted(LANGUAGES), default="English")
    parser.add_argument("--image-status", choices=sorted(IMAGE_STATUSES), default="placeholder")
    parser.add_argument("--public-image-prefix", default="")
    parser.add_argument("--rating", choices=sorted(RATINGS), default="")
    parser.add_argument("--vault-path", default="", help="Obsidian vault path to store in the payload")
    parser.add_argument("--notes-dir", default="", help="Vault-relative notes directory")
    parser.add_argument("--attachments-dir", default="", help="Vault-relative attachment directory")
    args = parser.parse_args()

    metadata = load_json(args.metadata)
    config = load_json(args.config) if args.config and args.config.exists() else {}
    schema = load_schema(args.schema)
    schema_props = schema_property_map(schema)
    schema_vault = schema.get("vault", {}) if isinstance(schema.get("vault"), dict) else {}

    original_title = str(first_value(metadata, "Original Title", "original_title", "title", "Title")).strip()
    name = str(first_value(metadata, "Name", "name", default=original_title)).strip() or original_title
    authors = str(first_value(metadata, "Authors", "authors")).strip()
    publication_date = str(first_value(metadata, "Publication Date", "publication_date", "published", "date")).strip()
    year = infer_year(publication_date, first_value(metadata, "Year", "year", default=None))
    doi = normalize_doi(str(first_value(metadata, "DOI", "doi")).strip())
    arxiv = normalize_arxiv(str(first_value(metadata, "arXiv", "arxiv", "arxiv_url")).strip())
    code = str(first_value(metadata, "Code", "code", "code_url", "repository")).strip()
    language = str(first_value(metadata, "Report Language", "report_language", default=args.language)).strip()
    if language not in LANGUAGES:
        language = args.language
    language = configured_option_or_default("Report Language", language, schema_props.get("Report Language"), args.language)
    rating = str(first_value(metadata, "Rating", "rating", default=args.rating)).strip()
    if rating not in RATINGS:
        rating = args.rating
    rating = configured_option_or_default("Rating", rating, schema_props.get("Rating"), args.rating)
    reading_status = configured_option_or_default(
        "Reading Status",
        str(first_value(metadata, "Reading Status", "reading_status", default="Read")),
        schema_props.get("Reading Status"),
        "Read",
    )
    paper_type = filter_configured_options(
        "Type",
        as_list(first_value(metadata, "Type", "type", "Paper Type", "paper_type", "Contribution Type", "contribution_type")),
        schema_props.get("Type"),
    )

    key, strategy = dedup_key(doi, arxiv, original_title)
    report_markdown = ""
    report_path = ""
    if args.report:
        report_path = stable_report_path(args.report, args.output)
        if args.report.exists():
            report_markdown = args.report.read_text(encoding="utf-8")
            if args.public_image_prefix:
                report_markdown = report_markdown.replace(
                    "__PUBLIC_IMAGE_PREFIX__",
                    args.public_image_prefix.rstrip("/"),
                )

    payload = {
        "vault": {
            "path": args.vault_path or str(config.get("vault_path", "")),
            "notes_dir": args.notes_dir or str(config.get("notes_dir", schema_vault.get("notes_dir", "Papers"))),
            "attachments_dir": args.attachments_dir
            or str(config.get("attachments_dir", schema_vault.get("attachments_dir", "Papers/assets"))),
        },
        "dedup": {"key": key, "strategy": strategy},
        "properties": {
            "Name": name,
            "Original Title": original_title,
            "Authors": authors,
            "Publication Date": publication_date,
            "Year": year,
            "Venue": filter_configured_options("Venue", as_list(first_value(metadata, "Venue", "venue")), schema_props.get("Venue")),
            "Field": filter_configured_options("Field", as_list(first_value(metadata, "Field", "field")), schema_props.get("Field")),
            "Type": paper_type,
            "Keywords": keyword_list(first_value(metadata, "Keywords", "keywords")),
            "Reading Status": reading_status,
            "Read Date": str(first_value(metadata, "Read Date", "read_date", default=dt.date.today().isoformat())),
            "Rating": rating,
            "DOI": doi,
            "arXiv": arxiv,
            "Code": code,
            "Report Language": language,
        },
        "content": {
            "report_path": report_path,
            "image_status": args.image_status,
            "public_image_prefix": args.public_image_prefix,
            "markdown": report_markdown,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
