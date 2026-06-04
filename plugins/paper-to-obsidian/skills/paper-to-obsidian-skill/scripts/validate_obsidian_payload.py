#!/usr/bin/env python3
"""Validate an Obsidian paper payload before writing to a vault."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


IMAGE_STATUSES = {"hosted", "local_only", "placeholder", "no_images"}
DEFAULT_SCHEMA = Path(__file__).resolve().parents[1] / "config" / "obsidian_schema.yaml"


def load_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Payload must be a JSON object")
    return data


def load_schema(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required to validate against a schema. Run scripts/setup_environment.py --use-uv --install."
        ) from exc
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("Schema must be a YAML object")
    return data


def schema_properties(schema: dict[str, Any]) -> list[dict[str, Any]]:
    properties = schema.get("properties", [])
    if not isinstance(properties, list):
        raise ValueError("schema.properties must be a list")
    return [prop for prop in properties if isinstance(prop, dict)]


def option_names(prop: dict[str, Any]) -> set[str]:
    options = prop.get("options", []) or []
    return {str(option.get("name", "")).strip() for option in options if isinstance(option, dict)}


def is_url_or_blank(value: Any) -> bool:
    if value in (None, ""):
        return True
    if not isinstance(value, str):
        return False
    return bool(re.match(r"^https?://\S+$", value))


def is_date_or_blank(value: Any) -> bool:
    if value in (None, ""):
        return True
    if not isinstance(value, str):
        return False
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def image_links(markdown: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown or "")


def is_remote_image_link(link: str) -> bool:
    return link.startswith(("http://", "https://"))


def local_image_candidates(payload_path: Path, link: str) -> list[Path]:
    clean = link
    if clean.startswith("__PUBLIC_IMAGE_PREFIX__/"):
        clean = clean.removeprefix("__PUBLIC_IMAGE_PREFIX__/")
    if is_remote_image_link(clean):
        return []
    path = Path(clean)
    if path.is_absolute():
        return [path]
    return [
        (payload_path.parent / path).resolve(),
        (payload_path.parent / "images" / path.name).resolve(),
        (payload_path.parent / clean).resolve(),
    ]


def check_remote_image_url(link: str, timeout: int) -> tuple[bool, int | None, str, str]:
    try:
        import requests
    except ImportError as exc:
        raise SystemExit("requests is required for --check-image-urls") from exc

    headers = {"User-Agent": "paper-to-obsidian-skill/0.1"}
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


def validate_option_value(field: str, value: Any, prop: dict[str, Any], errors: list[str]) -> None:
    allowed = option_names(prop)
    if allowed and str(value).strip() not in allowed:
        errors.append(f"{field} must be one of: {', '.join(sorted(allowed))}")


def vault_relative(value: str) -> bool:
    if not value or Path(value).is_absolute():
        return False
    parts = Path(value).parts
    return ".." not in parts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="Obsidian frontmatter schema YAML path")
    parser.add_argument("--check-image-urls", action="store_true", help="Check hosted Markdown image URLs over HTTP")
    parser.add_argument("--image-timeout", type=int, default=20, help="Per-image URL check timeout in seconds")
    parser.add_argument("--require-vault", action="store_true", help="Fail when payload.vault.path is missing or unavailable")
    args = parser.parse_args()

    payload = load_payload(args.payload)
    schema = load_schema(args.schema)
    errors: list[str] = []
    warnings: list[str] = []

    properties = payload.get("properties")
    if not isinstance(properties, dict):
        errors.append("Missing object: properties")
        properties = {}

    content = payload.get("content")
    if not isinstance(content, dict):
        errors.append("Missing object: content")
        content = {}

    dedup = payload.get("dedup")
    if not isinstance(dedup, dict):
        errors.append("Missing object: dedup")
        dedup = {}

    vault = payload.get("vault")
    if not isinstance(vault, dict):
        errors.append("Missing object: vault")
        vault = {}

    vault_path = str(vault.get("path", "")).strip()
    if args.require_vault:
        if not vault_path:
            errors.append("vault.path is required")
        elif not Path(vault_path).exists():
            errors.append(f"vault.path does not exist: {vault_path}")
    elif vault_path and not Path(vault_path).exists():
        warnings.append(f"vault.path does not exist yet: {vault_path}")

    for field in ("notes_dir", "attachments_dir"):
        value = str(vault.get(field, "")).strip()
        if not vault_relative(value):
            errors.append(f"vault.{field} must be a non-empty vault-relative path without .. segments")

    for prop in schema_properties(schema):
        field = str(prop.get("name", "")).strip()
        prop_type = str(prop.get("type", "")).strip().upper()
        value = properties.get(field)
        if prop.get("required") and not str(value if value is not None else "").strip():
            errors.append(f"Missing required property: {field}")
            continue
        if value in (None, ""):
            continue
        if prop_type == "NUMBER":
            try:
                int(value)
            except (TypeError, ValueError):
                errors.append(f"{field} must be a number")
        elif prop_type == "DATE" and not is_date_or_blank(value):
            errors.append(f"{field} must be blank or an ISO date like YYYY-MM-DD")
        elif prop_type == "URL" and not is_url_or_blank(value):
            errors.append(f"{field} must be blank or an http(s) URL")
        elif prop_type == "SELECT":
            validate_option_value(field, value, prop, errors)
        elif prop_type == "LIST":
            if not isinstance(value, list):
                errors.append(f"{field} must be a list")

    if not str(dedup.get("key", "")).strip():
        errors.append("Missing dedup.key")
    if dedup.get("strategy") not in {"doi", "arxiv", "title"}:
        errors.append("dedup.strategy must be doi, arxiv, or title")

    image_status = str(content.get("image_status", "")).strip()
    if image_status not in IMAGE_STATUSES:
        errors.append("content.image_status must be hosted, local_only, placeholder, or no_images")

    report_path = str(content.get("report_path", "")).strip()
    if report_path:
        resolved = (args.payload.parent / report_path).resolve() if not Path(report_path).is_absolute() else Path(report_path)
        if not resolved.exists():
            warnings.append(f"Report path does not exist: {report_path}")

    markdown = str(content.get("markdown", ""))
    if not markdown.strip():
        warnings.append("content.markdown is empty")

    if image_status == "no_images" and image_links(markdown):
        errors.append("image_status is no_images but markdown contains image links")

    if image_status == "hosted":
        local_links = [link for link in image_links(markdown) if not is_remote_image_link(link)]
        if local_links:
            errors.append("image_status is hosted but markdown contains local image links")
        placeholder_links = [link for link in image_links(markdown) if link.startswith("__PUBLIC_IMAGE_PREFIX__/")]
        if placeholder_links:
            errors.append("image_status is hosted but markdown still contains placeholder image links")
        if args.check_image_urls:
            for link in image_links(markdown):
                if not is_remote_image_link(link):
                    continue
                ok, status_code, final_url, content_type = check_remote_image_url(link, args.image_timeout)
                status = status_code if status_code is not None else "unknown"
                if not ok:
                    errors.append(f"Hosted image URL is not reachable: {link} (status: {status})")
                    continue
                if content_type and not content_type.lower().startswith("image/"):
                    warnings.append(f"Hosted image URL did not return an image content type: {final_url} ({content_type})")

    if image_status == "local_only":
        local_links = [link for link in image_links(markdown) if not is_remote_image_link(link)]
        if not local_links:
            warnings.append("image_status is local_only but markdown contains no local image links")
        for link in local_links:
            candidates = local_image_candidates(args.payload, link)
            if not any(candidate.exists() and candidate.is_file() for candidate in candidates):
                errors.append(f"Local image link does not resolve from payload directory: {link}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        return 1
    print("Payload validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
