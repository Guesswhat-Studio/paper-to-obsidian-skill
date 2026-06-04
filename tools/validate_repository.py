#!/usr/bin/env python3
"""Validate repository packaging for Codex and Claude plugin installs."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "paper-to-obsidian"
PLUGIN_SKILL = PLUGIN_ROOT / "skills" / "paper-to-obsidian-skill"
EXPECTED_PLUGIN_VERSION = "0.2.0"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_json(path: Path, errors: list[str]) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:  # noqa: BLE001 - report all parse/read failures together.
        errors.append(f"{rel(path)} is not valid JSON: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{rel(path)} must contain a JSON object")
        return {}
    return data


def assert_exists(path: Path, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"Missing required file: {rel(path)}")


def assert_same(root_path: Path, plugin_path: Path, errors: list[str]) -> None:
    if not root_path.exists():
        errors.append(f"Missing source file: {rel(root_path)}")
        return
    if not plugin_path.exists():
        errors.append(f"Missing plugin copy: {rel(plugin_path)}")
        return
    if root_path.read_bytes() != plugin_path.read_bytes():
        errors.append(f"Plugin copy is out of sync: {rel(plugin_path)} should match {rel(root_path)}")


def validate_manifests(errors: list[str]) -> None:
    marketplace_path = ROOT / ".claude-plugin" / "marketplace.json"
    plugin_manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    marketplace = read_json(marketplace_path, errors)
    plugin = read_json(plugin_manifest_path, errors)

    if marketplace.get("name") != "guesswhat-paper-tools":
        errors.append(".claude-plugin/marketplace.json name must be guesswhat-paper-tools")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append(".claude-plugin/marketplace.json must list at least one plugin")
    else:
        paper_plugin = next((item for item in plugins if isinstance(item, dict) and item.get("name") == "paper-to-obsidian"), None)
        if paper_plugin is None:
            errors.append("Marketplace must include paper-to-obsidian")
        else:
            if paper_plugin.get("version") != EXPECTED_PLUGIN_VERSION:
                errors.append(f"paper-to-obsidian marketplace version must be {EXPECTED_PLUGIN_VERSION}")
            if paper_plugin.get("source") != "./plugins/paper-to-obsidian":
                errors.append("paper-to-obsidian marketplace source must be ./plugins/paper-to-obsidian")

    if plugin.get("name") != "paper-to-obsidian":
        errors.append("plugins/paper-to-obsidian/.claude-plugin/plugin.json name must be paper-to-obsidian")
    if plugin.get("version") != EXPECTED_PLUGIN_VERSION:
        errors.append(f"plugins/paper-to-obsidian/.claude-plugin/plugin.json version must be {EXPECTED_PLUGIN_VERSION}")
    if plugin.get("license") != "MIT":
        errors.append("plugins/paper-to-obsidian/.claude-plugin/plugin.json license must be MIT")


def validate_mirrors(errors: list[str]) -> None:
    assert_same(ROOT / "LICENSE", PLUGIN_ROOT / "LICENSE", errors)
    assert_same(ROOT / "SKILL.md", PLUGIN_SKILL / "SKILL.md", errors)
    assert_same(ROOT / "requirements.txt", PLUGIN_SKILL / "requirements.txt", errors)
    assert_same(ROOT / "agents" / "openai.yaml", PLUGIN_SKILL / "agents" / "openai.yaml", errors)
    assert_same(ROOT / "config" / "obsidian_schema.yaml", PLUGIN_SKILL / "config" / "obsidian_schema.yaml", errors)

    for path in sorted((ROOT / "references").glob("*.md")):
        assert_same(path, PLUGIN_SKILL / "references" / path.name, errors)

    for path in sorted((ROOT / "scripts").iterdir()):
        if path.is_file():
            assert_same(path, PLUGIN_SKILL / "scripts" / path.name, errors)


def validate_venv_python_resolution(errors: list[str]) -> None:
    try:
        import importlib.util

        script_path = ROOT / "scripts" / "setup_environment.py"
        spec = importlib.util.spec_from_file_location("setup_environment", script_path)
        if spec is None or spec.loader is None:
            errors.append("Could not load scripts/setup_environment.py for venv layout validation")
            return
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            venv_dir = Path(tmp) / "venv"
            (venv_dir / "bin").mkdir(parents=True)
            expected = venv_dir / "bin" / "python"
            expected.write_text("", encoding="utf-8")
            actual = module.venv_python(venv_dir)
            if actual != expected:
                errors.append(f"venv_python should accept Unix-style bin/python layout, got {actual}")
    except Exception as exc:  # noqa: BLE001 - report validation failure with context.
        errors.append(f"venv layout validation failed: {exc}")


def validate_arxiv_asset_resolution(errors: list[str]) -> None:
    try:
        import importlib.util

        script_path = ROOT / "scripts" / "fetch_arxiv_html.py"
        spec = importlib.util.spec_from_file_location("fetch_arxiv_html", script_path)
        if spec is None or spec.loader is None:
            errors.append("Could not load scripts/fetch_arxiv_html.py for asset URL validation")
            return
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        cases = [
            (
                "https://arxiv.org/html/2503.14232",
                "extracted/6458440/images/fig1-min.png",
                "https://arxiv.org/html/2503.14232/extracted/6458440/images/fig1-min.png",
            ),
            (
                "https://arxiv.org/html/2605.29582",
                "2605.29582v1/x1.png",
                "https://arxiv.org/html/2605.29582v1/x1.png",
            ),
        ]
        for base_url, src, expected in cases:
            resolved = module.resolve_asset_url(base_url, src)
            if resolved != expected:
                errors.append(f"arXiv asset URL resolution regressed: expected {expected}, got {resolved}")
    except Exception as exc:  # noqa: BLE001 - report validation failure with context.
        errors.append(f"arXiv asset URL validation failed: {exc}")


def validate_dynamic_list_options(errors: list[str]) -> None:
    try:
        import importlib.util

        script_path = ROOT / "scripts" / "build_obsidian_payload.py"
        spec = importlib.util.spec_from_file_location("build_obsidian_payload", script_path)
        if spec is None or spec.loader is None:
            errors.append("Could not load scripts/build_obsidian_payload.py for dynamic LIST option validation")
            return
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        prop = {"type": "LIST", "options": [{"name": "arXiv"}, {"name": "NeurIPS"}]}
        values = ["arXiv", "NeurIPS 2017"]
        resolved = module.filter_configured_options("Venue", values, prop)
        if resolved != values:
            errors.append(f"LIST options should preserve dynamic values: expected {values}, got {resolved}")
    except Exception as exc:  # noqa: BLE001 - report validation failure with context.
        errors.append(f"dynamic LIST option validation failed: {exc}")


def main() -> int:
    errors: list[str] = []
    for path in [
        ROOT / "LICENSE",
        ROOT / "README.md",
        ROOT / "README.zh-CN.md",
        ROOT / "SKILL.md",
        ROOT / ".claude-plugin" / "marketplace.json",
        PLUGIN_ROOT / ".claude-plugin" / "plugin.json",
        PLUGIN_SKILL / "SKILL.md",
    ]:
        assert_exists(path, errors)

    validate_manifests(errors)
    validate_mirrors(errors)
    validate_venv_python_resolution(errors)
    validate_arxiv_asset_resolution(errors)
    validate_dynamic_list_options(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Repository packaging validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
