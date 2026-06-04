#!/usr/bin/env python3
"""Mirror the top-level skill source into the Claude plugin copy.

The repository ships one skill to two runtimes:

- the top-level tree (``SKILL.md``, ``scripts/``, ``references/`` ...) is the
  source of truth used by Codex and generic skill installs;
- ``plugins/paper-to-obsidian/skills/paper-to-obsidian-skill/`` is a byte-for-byte
  copy that Claude Code's plugin loader auto-discovers.

``tools/validate_repository.py`` fails when the two drift apart. Run this script
to fix that drift in one command instead of hand-editing both trees.

Usage:
    python tools/sync_plugin.py            # copy source -> plugin, report changes
    python tools/sync_plugin.py --check    # exit 1 if anything is out of sync
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "paper-to-obsidian"
PLUGIN_SKILL = PLUGIN_ROOT / "skills" / "paper-to-obsidian-skill"


def mirror_pairs() -> list[tuple[Path, Path]]:
    """Return (source, plugin-copy) pairs that must stay identical.

    Keep this list aligned with ``validate_repository.validate_mirrors`` so the
    sync tool and the validator never disagree about what is mirrored.
    """
    pairs: list[tuple[Path, Path]] = [
        (ROOT / "LICENSE", PLUGIN_ROOT / "LICENSE"),
        (ROOT / "SKILL.md", PLUGIN_SKILL / "SKILL.md"),
        (ROOT / "requirements.txt", PLUGIN_SKILL / "requirements.txt"),
        (ROOT / "agents" / "openai.yaml", PLUGIN_SKILL / "agents" / "openai.yaml"),
        (ROOT / "config" / "obsidian_schema.yaml", PLUGIN_SKILL / "config" / "obsidian_schema.yaml"),
    ]
    for path in sorted((ROOT / "references").glob("*.md")):
        pairs.append((path, PLUGIN_SKILL / "references" / path.name))
    for path in sorted((ROOT / "scripts").iterdir()):
        if path.is_file():
            pairs.append((path, PLUGIN_SKILL / "scripts" / path.name))
    return pairs


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift and exit 1 without writing (for CI). Default copies source over the plugin copy.",
    )
    args = parser.parse_args()

    missing_sources: list[str] = []
    out_of_sync: list[str] = []
    copied: list[str] = []

    for source, plugin_copy in mirror_pairs():
        if not source.exists():
            missing_sources.append(rel(source))
            continue
        in_sync = plugin_copy.exists() and plugin_copy.read_bytes() == source.read_bytes()
        if in_sync:
            continue
        if args.check:
            out_of_sync.append(rel(plugin_copy))
        else:
            plugin_copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, plugin_copy)
            copied.append(rel(plugin_copy))

    if missing_sources:
        for path in missing_sources:
            print(f"ERROR: missing source file: {path}", file=sys.stderr)
        return 1

    if args.check:
        if out_of_sync:
            for path in out_of_sync:
                print(f"ERROR: plugin copy out of sync: {path}", file=sys.stderr)
            print("Run: python tools/sync_plugin.py", file=sys.stderr)
            return 1
        print("Plugin copy is in sync")
        return 0

    if copied:
        for path in copied:
            print(f"synced: {path}")
        print(f"Synced {len(copied)} file(s) into the plugin copy")
    else:
        print("Plugin copy already in sync; nothing to do")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
