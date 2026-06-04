#!/usr/bin/env python3
"""Publish a validated paper payload to an Obsidian vault."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any


DEFAULT_SCHEMA = Path(__file__).resolve().parents[1] / "config" / "obsidian_schema.yaml"
FRONTMATTER_FIELDS = {
    "Name": "title",
    "Original Title": "original_title",
    "Authors": "authors",
    "Publication Date": "publication_date",
    "Year": "year",
    "Venue": "venue",
    "Field": "field",
    "Type": "type",
    "Keywords": "keywords",
    "Reading Status": "reading_status",
    "Read Date": "read_date",
    "Rating": "rating",
    "DOI": "doi",
    "arXiv": "arxiv",
    "Code": "code",
    "Report Language": "report_language",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyYAML is required. Run scripts/setup_environment.py --use-uv --install.") from exc
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def dump_yaml(data: dict[str, Any]) -> str:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyYAML is required. Run scripts/setup_environment.py --use-uv --install.") from exc
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False).strip()


def run_validation(payload_path: Path, schema: Path, require_vault: bool) -> None:
    validator = Path(__file__).with_name("validate_obsidian_payload.py")
    command = [sys.executable, str(validator), str(payload_path), "--schema", str(schema)]
    if require_vault:
        command.append("--require-vault")
    subprocess.check_call(command)


def slugify(value: str, max_length: int = 90) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s.-]+", "", text).strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-.")
    if not text:
        text = "paper"
    return text[:max_length].rstrip("-.") or "paper"


def normalize_title(title: str) -> str:
    text = unicodedata.normalize("NFKC", title).casefold()
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def safe_join(root: Path, relative: str) -> Path:
    if Path(relative).is_absolute():
        raise ValueError(f"Path must be vault-relative: {relative}")
    resolved = (root / relative).resolve()
    root_resolved = root.resolve()
    if root_resolved != resolved and root_resolved not in resolved.parents:
        raise ValueError(f"Path escapes vault: {relative}")
    return resolved


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[text.find("\n", end + 4) + 1 :] if "\n" in text[end + 4 :] else ""
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(raw) if raw else {}
    except Exception:
        data = {}
    return (data if isinstance(data, dict) else {}), body


def markdown_from_payload(payload: dict[str, Any], payload_path: Path) -> str:
    content = payload.get("content", {})
    if not isinstance(content, dict):
        return ""
    markdown = str(content.get("markdown", ""))
    if markdown.strip():
        return markdown
    report_path = str(content.get("report_path", "")).strip()
    if not report_path:
        return ""
    resolved = (payload_path.parent / report_path).resolve() if not Path(report_path).is_absolute() else Path(report_path)
    return resolved.read_text(encoding="utf-8") if resolved.exists() else ""


def frontmatter_from_payload(payload: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    properties = payload.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}

    field_map = FRONTMATTER_FIELDS.copy()
    for prop in schema.get("properties", []) or []:
        if not isinstance(prop, dict):
            continue
        name = str(prop.get("name", "")).strip()
        frontmatter = str(prop.get("frontmatter", "")).strip()
        if name and frontmatter:
            field_map[name] = frontmatter

    frontmatter: dict[str, Any] = {}
    for source, target in field_map.items():
        value = properties.get(source)
        if value in (None, "", []):
            continue
        frontmatter[target] = value

    dedup = payload.get("dedup", {})
    if isinstance(dedup, dict):
        frontmatter["dedup_key"] = str(dedup.get("key", ""))
        frontmatter["dedup_strategy"] = str(dedup.get("strategy", ""))

    tags = ["papers"]
    for field in frontmatter.get("field", []) if isinstance(frontmatter.get("field"), list) else []:
        tag = slugify(str(field), 32)
        if tag:
            tags.append(f"papers/{tag}")
    frontmatter["tags"] = sorted(set(tags))
    return frontmatter


def candidate_existing_notes(notes_root: Path, payload: dict[str, Any]) -> list[Path]:
    if not notes_root.exists():
        return []

    properties = payload.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}
    dedup = payload.get("dedup", {})
    dedup_key = str(dedup.get("key", "")).strip().lower() if isinstance(dedup, dict) else ""
    doi = str(properties.get("DOI", "")).strip().lower()
    arxiv = str(properties.get("arXiv", "")).strip().lower()
    original_title = normalize_title(str(properties.get("Original Title", "")).strip())
    name = normalize_title(str(properties.get("Name", "")).strip())

    matches: list[Path] = []
    for note in sorted(notes_root.rglob("*.md")):
        frontmatter, _body = split_frontmatter(note.read_text(encoding="utf-8"))
        note_dedup = str(frontmatter.get("dedup_key", "")).strip().lower()
        note_doi = str(frontmatter.get("doi", "")).strip().lower()
        note_arxiv = str(frontmatter.get("arxiv", "")).strip().lower()
        note_original_title = normalize_title(str(frontmatter.get("original_title", "")).strip())
        note_title = normalize_title(str(frontmatter.get("title", "")).strip())
        if dedup_key and note_dedup == dedup_key:
            matches.append(note)
        elif doi and note_doi == doi:
            matches.append(note)
        elif arxiv and note_arxiv == arxiv:
            matches.append(note)
        elif original_title and note_original_title == original_title:
            matches.append(note)
        elif name and note_title == name:
            matches.append(note)
    return matches


def note_filename(payload: dict[str, Any]) -> str:
    properties = payload.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}
    year = str(properties.get("Year", "") or "").strip()
    title = str(properties.get("Original Title") or properties.get("Name") or "paper")
    prefix = f"{year}-" if year else ""
    return f"{prefix}{slugify(title)}.md"


def image_candidates(payload_path: Path, link: str) -> list[Path]:
    clean = link
    if clean.startswith("__PUBLIC_IMAGE_PREFIX__/"):
        clean = clean.removeprefix("__PUBLIC_IMAGE_PREFIX__/")
    if clean.startswith(("http://", "https://")):
        return []
    path = Path(clean)
    if path.is_absolute():
        return [path]
    return [
        (payload_path.parent / path).resolve(),
        (payload_path.parent / "images" / path.name).resolve(),
        (payload_path.parent / clean).resolve(),
    ]


def copy_and_rewrite_images(
    markdown: str,
    payload_path: Path,
    note_path: Path,
    attachment_root: Path,
    note_slug: str,
    dry_run: bool = False,
) -> tuple[str, list[str]]:
    copied: list[str] = []
    target_dir = attachment_root / note_slug

    def replace(match: re.Match[str]) -> str:
        alt = match.group(1)
        link = match.group(2).strip()
        if link.startswith(("http://", "https://")):
            return match.group(0)
        for candidate in image_candidates(payload_path, link):
            if candidate.exists() and candidate.is_file():
                target = target_dir / candidate.name
                if not dry_run:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    if candidate.resolve() != target.resolve():
                        shutil.copy2(candidate, target)
                copied.append(str(target))
                relative = target.relative_to(note_path.parent).as_posix()
                return f"![{alt}]({relative})"
        return match.group(0)

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace, markdown), copied


def compose_note(frontmatter: dict[str, Any], body: str) -> str:
    cleaned = body.strip()
    title = str(frontmatter.get("title", "")).strip()
    if title and not cleaned.startswith("#"):
        cleaned = f"# {title}\n\n{cleaned}" if cleaned else f"# {title}"
    return f"---\n{dump_yaml(frontmatter)}\n---\n\n{cleaned}\n"


def publish(args: argparse.Namespace) -> dict[str, Any]:
    payload = load_json(args.payload)
    schema = load_yaml(args.schema)
    if not args.skip_validation:
        run_validation(args.payload, args.schema, require_vault=False)

    vault = payload.get("vault", {})
    if not isinstance(vault, dict):
        vault = {}
    vault_path = args.vault or os.environ.get("OBSIDIAN_VAULT", "") or str(vault.get("path", ""))
    if not vault_path:
        raise SystemExit("Set --vault, OBSIDIAN_VAULT, or payload.vault.path before publishing.")
    vault_root = Path(vault_path).resolve()
    if not vault_root.exists():
        raise SystemExit(f"Obsidian vault does not exist: {vault_root}")

    notes_dir = args.notes_dir or str(vault.get("notes_dir", "Papers"))
    attachments_dir = args.attachments_dir or str(vault.get("attachments_dir", "Papers/assets"))
    notes_root = safe_join(vault_root, notes_dir)
    attachments_root = safe_join(vault_root, attachments_dir)

    frontmatter = frontmatter_from_payload(payload, schema)
    body = markdown_from_payload(payload, args.payload)
    note_slug = slugify(str(frontmatter.get("original_title") or frontmatter.get("title") or "paper"))

    existing = candidate_existing_notes(notes_root, payload)
    target = existing[0] if existing else notes_root / note_filename(payload)

    rewritten_body, copied = copy_and_rewrite_images(body, args.payload, target, attachments_root, note_slug, args.dry_run)
    note_text = compose_note(frontmatter, rewritten_body)
    result = {
        "status": "dry_run",
        "note_path": str(target),
        "note_relative_path": target.relative_to(vault_root).as_posix(),
        "existing_matches": [path.relative_to(vault_root).as_posix() for path in existing],
        "attachments_copied": copied,
    }
    if args.dry_run:
        return result

    if existing:
        if args.if_exists == "fail":
            raise SystemExit(f"Duplicate note found: {target}")
        if args.if_exists == "skip":
            result["status"] = "skipped_existing"
            return result
        if args.body_mode == "none":
            old_frontmatter, old_body = split_frontmatter(target.read_text(encoding="utf-8"))
            merged_frontmatter = {**old_frontmatter, **frontmatter}
            note_text = compose_note(merged_frontmatter, old_body)
        elif args.body_mode == "append":
            old_frontmatter, old_body = split_frontmatter(target.read_text(encoding="utf-8"))
            merged_frontmatter = {**old_frontmatter, **frontmatter}
            joined = old_body.rstrip() + "\n\n---\n\n" + rewritten_body.strip()
            note_text = compose_note(merged_frontmatter, joined)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(note_text, encoding="utf-8")
    result["status"] = "updated" if existing else "created"
    result["attachments_copied"] = copied
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path, help="obsidian_payload.json path")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--vault", default="", help="Overrides payload.vault.path and OBSIDIAN_VAULT")
    parser.add_argument("--notes-dir", default="", help="Overrides payload.vault.notes_dir")
    parser.add_argument("--attachments-dir", default="", help="Overrides payload.vault.attachments_dir")
    parser.add_argument("--if-exists", choices=["update", "skip", "fail"], default="update")
    parser.add_argument("--body-mode", choices=["replace", "append", "none"], default="replace")
    parser.add_argument("--skip-validation", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = publish(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
