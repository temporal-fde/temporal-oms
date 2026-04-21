#!/usr/bin/env python3
"""Fix broken cross-package imports in protobuf-to-pydantic generated files.

protobuf-to-pydantic has a bug where same-named proto files in different
packages generate bare module imports instead of correct relative imports.
e.g.  from workflows_p2p import CompleteOrderRequest          (broken)
  ->  from ....apps.domain.v1.workflows_p2p import CompleteOrderRequest (fixed)

Run after `buf generate`. See: https://github.com/so1n/protobuf_to_pydantic/issues/<TBD>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

GENERATED_DIR = Path(__file__).parent.parent / "python" / "generated" / "pydantic"
BARE_IMPORT_RE = re.compile(r"^from ([a-z_]+_p2p) import (\w+)$")


def build_index(root: Path) -> dict[tuple[str, str], list[Path]]:
    """Map (module_stem, class_name) -> list of files that define the class."""
    index: dict[tuple[str, str], list[Path]] = {}
    for p2p_file in root.rglob("*_p2p.py"):
        stem = p2p_file.stem
        for line in p2p_file.read_text().splitlines():
            m = re.match(r"^class (\w+)", line)
            if m:
                index.setdefault((stem, m.group(1)), []).append(p2p_file)
    return index


def relative_import(from_file: Path, to_file: Path, root: Path) -> str:
    """Compute the dotted relative module path from from_file to to_file."""
    from_parts = from_file.relative_to(root).parts  # includes filename
    to_parts = to_file.relative_to(root).parts

    common = 0
    for a, b in zip(from_parts[:-1], to_parts[:-1]):
        if a != b:
            break
        common += 1

    dots = len(from_parts) - common
    tail = ".".join(to_parts[common:-1] + (to_file.stem,))
    return "." * dots + tail


def fix_file(p2p_file: Path, index: dict[tuple[str, str], list[Path]], root: Path) -> int:
    lines = p2p_file.read_text().splitlines(keepends=True)
    new_lines = []
    fixes = 0
    for line in lines:
        m = BARE_IMPORT_RE.match(line.rstrip("\n"))
        if m:
            key = (m.group(1), m.group(2))
            candidates = [p for p in index.get(key, []) if p != p2p_file]
            if len(candidates) == 1:
                rel = relative_import(p2p_file, candidates[0], root)
                new_lines.append(f"from {rel} import {m.group(2)}\n")
                fixes += 1
                continue
            elif len(candidates) > 1:
                paths = ", ".join(str(p.relative_to(root)) for p in candidates)
                print(f"  warning: ambiguous import '{m.group(2)}' in "
                      f"{p2p_file.relative_to(root)} — candidates: {paths}", file=sys.stderr)
        new_lines.append(line)
    if fixes:
        p2p_file.write_text("".join(new_lines))
    return fixes


def main() -> None:
    if not GENERATED_DIR.exists():
        print(f"error: {GENERATED_DIR} not found — run buf generate first", file=sys.stderr)
        sys.exit(1)

    index: dict[tuple[str, str], list[Path]] = build_index(GENERATED_DIR)
    total = 0
    for p2p_file in sorted(GENERATED_DIR.rglob("*_p2p.py")):
        n = fix_file(p2p_file, index, GENERATED_DIR)
        if n:
            print(f"  fixed {n} import(s) in {p2p_file.relative_to(GENERATED_DIR)}")
            total += n

    if total:
        print(f"\n{total} import(s) fixed")
    else:
        print("no broken imports found")


if __name__ == "__main__":
    main()
