#!/usr/bin/env python3
"""Check or create the local environment for paper-to-obsidian-skill."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import venv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_PACKAGES = [
    ("PyMuPDF", "fitz", "PDF probing, text extraction, page rendering, and cropping"),
    ("Pillow", "PIL", "Image verification and lightweight image handling"),
    ("requests", "requests", "Downloading PDFs and metadata pages"),
    ("beautifulsoup4", "bs4", "HTML metadata parsing"),
    ("lxml", "lxml", "Robust HTML/XML parser backend"),
    ("PyYAML", "yaml", "Obsidian frontmatter schema parsing and payload validation"),
]

OPTIONAL_TOOLS = [
    ("git", "Inspect paper code repositories"),
    ("gh", "Authenticated GitHub lookup"),
    ("tesseract", "OCR scanned PDFs"),
    ("uv", "Fast dependency setup"),
]


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    required: bool = True


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def workspace_venv() -> Path:
    """Default virtual environment location inside the active workspace.

    Placed under the current working directory (the user's project) rather than
    the skill directory so it survives plugin-cache refreshes on Claude and stays
    user-owned across every runtime.
    """
    return Path.cwd() / ".paper-obsidian" / ".venv"


def venv_python_candidates(venv_dir: Path) -> list[Path]:
    preferred = [
        venv_dir / "Scripts" / "python.exe",
        venv_dir / "Scripts" / "python",
        venv_dir / "bin" / "python.exe",
        venv_dir / "bin" / "python",
        venv_dir / "bin" / "python3",
    ]
    if not sys.platform.startswith("win"):
        preferred = [
            venv_dir / "bin" / "python",
            venv_dir / "bin" / "python3",
            venv_dir / "bin" / "python.exe",
            venv_dir / "Scripts" / "python.exe",
            venv_dir / "Scripts" / "python",
        ]
    return preferred


def venv_python(venv_dir: Path) -> Path:
    for candidate in venv_python_candidates(venv_dir):
        if candidate.exists():
            return candidate
    return venv_python_candidates(venv_dir)[0]


def run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.check_call(command, cwd=str(cwd) if cwd else None)


def create_venv(venv_dir: Path) -> Path:
    if not venv_dir.exists():
        venv.EnvBuilder(with_pip=True).create(venv_dir)
    python = venv_python(venv_dir)
    if not python.exists():
        searched = ", ".join(str(path) for path in venv_python_candidates(venv_dir))
        raise RuntimeError(f"Virtual environment Python not found. Searched: {searched}")
    return python


def create_uv_venv(venv_dir: Path, python_version: str | None = None, install_python: bool = False) -> Path:
    uv = shutil.which("uv")
    if not uv:
        raise RuntimeError("uv was requested but was not found on PATH")
    if install_python and python_version:
        run([uv, "python", "install", python_version])
    command = [uv, "venv", str(venv_dir)]
    if python_version:
        command.extend(["--python", python_version])
    run(command)
    python = venv_python(venv_dir)
    if not python.exists():
        searched = ", ".join(str(path) for path in venv_python_candidates(venv_dir))
        raise RuntimeError(f"uv virtual environment Python not found. Searched: {searched}")
    return python


def install_requirements(python: Path, use_uv: bool = False) -> None:
    requirements = skill_root() / "requirements.txt"
    if use_uv:
        uv = shutil.which("uv")
        if not uv:
            raise RuntimeError("uv was requested but was not found on PATH")
        run([uv, "pip", "install", "--python", str(python), "-r", str(requirements)])
        return
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "-r", str(requirements)])


def package_checks(python: Path | None) -> list[Check]:
    checks: list[Check] = []
    if python:
        probe = (
            "import importlib.util, json; "
            f"mods={json.dumps([(pkg, mod) for pkg, mod, _ in REQUIRED_PACKAGES])}; "
            "print(json.dumps({pkg: importlib.util.find_spec(mod) is not None for pkg, mod in mods}))"
        )
        output = subprocess.check_output([str(python), "-c", probe], text=True)
        found = json.loads(output)
        for package, _module, purpose in REQUIRED_PACKAGES:
            checks.append(Check(package, bool(found.get(package)), purpose))
        return checks

    for package, module, purpose in REQUIRED_PACKAGES:
        checks.append(Check(package, importlib.util.find_spec(module) is not None, purpose))
    return checks


def python_checks(python: Path | None) -> list[Check]:
    executable = Path(python or sys.executable)
    version_code = "import sys, json; print(json.dumps({'version': sys.version.split()[0], 'ok': sys.version_info >= (3, 10)}))"
    output = subprocess.check_output([str(executable), "-c", version_code], text=True)
    data = json.loads(output)
    return [Check("Python >= 3.10", bool(data["ok"]), f"{executable} ({data['version']})")]


def tool_checks() -> list[Check]:
    checks = []
    for tool, purpose in OPTIONAL_TOOLS:
        path = shutil.which(tool)
        checks.append(Check(tool, bool(path), path or purpose, required=False))
    return checks


def capability_checks(python: Path | None) -> list[Check]:
    executable = Path(python or sys.executable)
    checks: list[Check] = []
    snippets: list[tuple[str, str]] = [
        ("PyMuPDF open empty document", "import fitz; doc = fitz.open(); doc.close()"),
        ("Pillow create image", "from PIL import Image; Image.new('RGB', (8, 8), 'white')"),
        ("requests import", "import requests; assert requests.__version__"),
        ("PyYAML parse schema", "import yaml; assert yaml.safe_load('x: 1')['x'] == 1"),
    ]
    for name, code in snippets:
        proc = subprocess.run([str(executable), "-c", code], text=True, capture_output=True)
        detail = "ok" if proc.returncode == 0 else (proc.stderr.strip() or proc.stdout.strip())
        checks.append(Check(name, proc.returncode == 0, detail))

    schema_tool = skill_root() / "scripts" / "schema_tool.py"
    proc = subprocess.run(
        [str(executable), str(schema_tool), "--command", "validate"],
        text=True,
        capture_output=True,
    )
    detail = "ok" if proc.returncode == 0 else (proc.stderr.strip() or proc.stdout.strip())
    checks.append(Check("schema_tool validate", proc.returncode == 0, detail))
    return checks


def print_checks(checks: list[Check]) -> None:
    for check in checks:
        marker = "OK" if check.ok else ("MISSING" if check.required else "OPTIONAL")
        print(f"[{marker}] {check.name}: {check.detail}")


def write_report(path: Path, checks: list[Check], python: Path | None) -> None:
    data: dict[str, Any] = {
        "python": str(python or sys.executable),
        "checks": [
            {
                "name": check.name,
                "ok": check.ok,
                "detail": check.detail,
                "required": check.required,
            }
            for check in checks
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv", type=Path, help="Virtual environment directory to create or check; defaults to .paper-obsidian/.venv in the current workspace when installing")
    parser.add_argument("--install", action="store_true", help="Install requirements into --venv")
    parser.add_argument("--use-uv", action="store_true", help="Use uv for venv creation and dependency installation")
    parser.add_argument("--install-python", action="store_true", help="With --use-uv, install a uv-managed Python first")
    parser.add_argument("--python-version", default="3.13", help="Python version for uv-managed environments")
    parser.add_argument("--check-only", action="store_true", help="Only check the current environment")
    parser.add_argument("--json-report", type=Path, help="Write check results to JSON")
    args = parser.parse_args()

    python: Path | None = None
    if args.venv is None and (args.install or args.use_uv or args.install_python):
        args.venv = workspace_venv()

    if args.check_only and args.venv is None:
        python = None
    elif args.venv:
        if args.use_uv:
            python = create_uv_venv(args.venv, args.python_version, args.install_python)
        else:
            python = create_venv(args.venv)
        if args.install:
            install_requirements(python, args.use_uv)
    elif args.install:
        raise SystemExit("--install requires --venv")

    checks: list[Check] = []
    checks.extend(python_checks(python))
    checks.extend(package_checks(python))
    checks.extend(capability_checks(python))
    checks.extend(tool_checks())

    print_checks(checks)
    if args.json_report:
        write_report(args.json_report, checks, python)

    failed = [check for check in checks if check.required and not check.ok]
    if failed:
        print("\nRequired environment checks failed.")
        if not args.venv:
            print("Try: python scripts/setup_environment.py --use-uv --install")
            print("Fallback without uv: python scripts/setup_environment.py --venv .paper-obsidian/.venv --install")
        return 1

    print("\nEnvironment checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
