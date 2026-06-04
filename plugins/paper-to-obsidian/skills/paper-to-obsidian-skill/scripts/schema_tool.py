#!/usr/bin/env python3
"""Validate and render the Obsidian frontmatter schema YAML."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


VALID_TYPES = {
    "TEXT",
    "LIST",
    "DATE",
    "URL",
    "SELECT",
    "NUMBER",
    "BOOLEAN",
}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required for schema_tool.py. Install requirements or run setup_environment.py --use-uv --install."
        ) from exc
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("Schema YAML must contain an object")
    return data


def validate_option(option: Any, field_name: str) -> str | None:
    if not isinstance(option, dict):
        return f"{field_name}: each option must be an object"
    name = str(option.get("name", "")).strip()
    if not name:
        return f"{field_name}: option missing name"
    return None


def validate_schema(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    vault = schema.get("vault")
    if not isinstance(vault, dict):
        errors.append("Missing vault object")
    else:
        for field in ("notes_dir", "attachments_dir"):
            value = str(vault.get(field, "")).strip()
            if not value:
                errors.append(f"vault.{field} is required")
            elif Path(value).is_absolute() or ".." in Path(value).parts:
                errors.append(f"vault.{field} must be vault-relative and must not contain ..")

    properties = schema.get("properties")
    if not isinstance(properties, list) or not properties:
        errors.append("properties must be a non-empty list")
        return errors

    names: set[str] = set()
    frontmatter_names: set[str] = set()
    for index, prop in enumerate(properties):
        if not isinstance(prop, dict):
            errors.append(f"properties[{index}] must be an object")
            continue
        name = str(prop.get("name", "")).strip()
        frontmatter = str(prop.get("frontmatter", "")).strip()
        prop_type = str(prop.get("type", "")).strip().upper()
        if not name:
            errors.append(f"properties[{index}] missing name")
            continue
        if name in names:
            errors.append(f"Duplicate property name: {name}")
        names.add(name)
        if not frontmatter:
            errors.append(f"{name}: missing frontmatter")
        elif frontmatter in frontmatter_names:
            errors.append(f"Duplicate frontmatter field: {frontmatter}")
        frontmatter_names.add(frontmatter)
        if prop_type not in VALID_TYPES:
            errors.append(f"{name}: invalid type {prop_type!r}")
        if prop_type == "SELECT":
            options = prop.get("options", [])
            if options is not None and not isinstance(options, list):
                errors.append(f"{name}: options must be a list")
            else:
                for option in options or []:
                    error = validate_option(option, name)
                    if error:
                        errors.append(error)

    if "title" not in frontmatter_names:
        errors.append("Schema must define a title frontmatter field")
    return errors


def render_summary(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": schema.get("schema_version"),
        "vault": schema.get("vault", {}),
        "properties": [
            {
                "name": prop.get("name"),
                "frontmatter": prop.get("frontmatter"),
                "type": prop.get("type"),
                "required": bool(prop.get("required", False)),
                "options": [option.get("name") for option in prop.get("options", []) or []],
            }
            for prop in schema.get("properties", [])
        ],
        "deduplication": schema.get("deduplication", {}),
        "optional_extensions": list((schema.get("optional_extensions") or {}).keys()),
    }


def template_value(prop_type: str) -> Any:
    if prop_type == "LIST":
        return []
    if prop_type == "NUMBER":
        return 0
    if prop_type == "BOOLEAN":
        return False
    return ""


def render_frontmatter_template(schema: dict[str, Any]) -> str:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyYAML is required for frontmatter template rendering.") from exc

    data: dict[str, Any] = {}
    for prop in schema.get("properties", []):
        if not isinstance(prop, dict):
            continue
        key = str(prop.get("frontmatter", "")).strip()
        prop_type = str(prop.get("type", "")).strip().upper()
        if key:
            data[key] = template_value(prop_type)
    data["dedup_key"] = ""
    data["dedup_strategy"] = ""
    data["tags"] = ["papers"]
    return "---\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False).strip() + "\n---"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, default=Path(__file__).resolve().parents[1] / "config" / "obsidian_schema.yaml")
    parser.add_argument("--command", choices=["validate", "summary", "frontmatter-template"], default="validate")
    parser.add_argument("--output", type=Path, help="Write command output to a file")
    args = parser.parse_args()

    schema = load_yaml(args.schema)
    errors = validate_schema(schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.command == "validate":
        output = f"Schema validation passed: {args.schema}"
    elif args.command == "summary":
        output = json.dumps(render_summary(schema), ensure_ascii=False, indent=2)
    else:
        output = render_frontmatter_template(schema)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
