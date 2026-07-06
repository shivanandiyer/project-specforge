#!/usr/bin/env python3
"""Validate specforge contract YAML files.

Checks (Phase 0 exit criterion, ROADMAP.md): a spec fails when it's missing
core ODCS identity fields or its x-buildspec extension block doesn't conform
to schema/x-buildspec.schema.json.

Usage: validate_spec.py <glob> [<glob> ...]
"""
import glob
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "x-buildspec.schema.json"

REQUIRED_ODCS_FIELDS = [
    "apiVersion", "kind", "id", "name", "version", "domain", "status", "owner",
]


def load_validator() -> Draft7Validator:
    schema = json.loads(SCHEMA_PATH.read_text())
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


def validate_file(path: str, validator: Draft7Validator) -> list[str]:
    text = Path(path).read_text()
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as e:
        return [f"{path}: invalid YAML — {e}"]

    if not isinstance(doc, dict):
        return [f"{path}: document root must be a mapping"]

    errors = [
        f"{path}: missing required ODCS field '{field}'"
        for field in REQUIRED_ODCS_FIELDS
        if field not in doc
    ]

    if "x-buildspec" not in doc:
        errors.append(f"{path}: missing required 'x-buildspec' extension block")
    else:
        for err in sorted(validator.iter_errors(doc["x-buildspec"]), key=str):
            loc = "x-buildspec" + "".join(f"[{p!r}]" for p in err.path)
            errors.append(f"{path}: {loc}: {err.message}")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: validate_spec.py <glob> [<glob> ...]", file=sys.stderr)
        return 2

    paths: list[str] = []
    for pattern in argv[1:]:
        paths.extend(sorted(glob.glob(pattern, recursive=True)))

    if not paths:
        print(f"no spec files matched: {argv[1:]}", file=sys.stderr)
        return 2

    validator = load_validator()
    all_errors = [err for path in paths for err in validate_file(path, validator)]

    if all_errors:
        print(f"✗ {len(all_errors)} error(s) across {len(paths)} spec file(s):\n")
        for err in all_errors:
            print(f"  {err}")
        return 1

    print(f"✓ {len(paths)} spec file(s) valid: {', '.join(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
