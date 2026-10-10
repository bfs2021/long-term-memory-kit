#!/usr/bin/env python3
"""Validate Records and memory-bank.yaml against schema/ with jsonschema.

No arguments: demo-bank must pass, fixtures/invalid must fail.
With paths: each file must pass (memory-bank.yaml uses the config schema).
Exit 0 all as expected, 1 otherwise, 2 on usage errors.
"""
import glob
import json
import os
import sys

import yaml
from jsonschema import Draft202012Validator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.environ.get("LTM_FIXTURES_DIR") or os.path.join(ROOT, "fixtures")


class Loader(yaml.SafeLoader):
    pass


# Dates must reach the validator as the strings on disk; SafeLoader would
# turn 2026-03-31 into datetime.date and fail `type: string`.
Loader.yaml_implicit_resolvers = {
    ch: [(tag, rx) for tag, rx in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for ch, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def validator(name):
    with open(os.path.join(ROOT, "schema", name), encoding="utf-8") as f:
        schema = json.load(f)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def show(path):
    full = os.path.abspath(path)
    if full.startswith(ROOT + os.sep):
        return os.path.relpath(full, ROOT)
    return path


def frontmatter(text):
    lines = text.split("\n")
    if not lines or lines[0].rstrip("\r") != "---":
        return None
    for i, line in enumerate(lines[1:], 1):
        if line.rstrip("\r") == "---":
            return "\n".join(lines[1:i])
    return None


def key_of(err):
    if err.absolute_path:
        return "/".join(str(p) for p in err.absolute_path)
    # Read the key off the instance and schema, not jsonschema's English message,
    # which isn't a stable interface.
    if err.validator == "required":
        absent = [n for n in err.validator_value if n not in err.instance]
        if absent:
            return absent[0]
    if err.validator == "additionalProperties":
        extra = [k for k in err.instance if k not in err.schema.get("properties", {})]
        if extra:
            return ",".join(str(k) for k in extra)
    return "(root)"


def check(path, validators):
    """Return a list of '<key>: <message>' failures for one file."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        if os.path.basename(path) == "memory-bank.yaml":
            data, v = yaml.load(text, Loader), validators["config"]
        else:
            fm = frontmatter(text)
            if fm is None:
                return ["(frontmatter): missing"]
            data, v = yaml.load(fm, Loader), validators["record"]
    except yaml.YAMLError as e:
        # One bad file mustn't abort the sweep; collapse the multi-line message.
        return ["(yaml): " + " ".join(str(e).split())]
    if not isinstance(data, dict):
        return ["(root): not a mapping"]
    return [f"{key_of(e)}: {e.message}" for e in sorted(v.iter_errors(data), key=lambda e: list(map(str, e.absolute_path)))]


def targets(root, kinds):
    out = []
    if "md" in kinds:
        out += glob.glob(os.path.join(root, "**", "*.md"), recursive=True)
    if "yaml" in kinds:
        out += glob.glob(os.path.join(root, "**", "memory-bank.yaml"), recursive=True)
    return sorted(out)


def main(argv):
    validators = {"record": validator("record.schema.json"), "config": validator("memory-bank.schema.json")}
    bad = False

    def expect_pass(path):
        nonlocal bad
        for msg in check(path, validators):
            print(f"{show(path)}: {msg}")
            bad = True

    if argv:
        missing = [a for a in argv if not os.path.isfile(a)]
        if missing:
            print(f"usage: check-schema.py [file ...]; not a file: {missing[0]}", file=sys.stderr)
            return 2
        for a in argv:
            expect_pass(a)
        return 1 if bad else 0

    # A missing or empty root would let CI go green while checking nothing.
    demo = os.path.join(FIXTURES, "demo-bank")
    demo_files = targets(os.path.join(demo, "_memory"), {"md"}) + targets(demo, {"yaml"})
    invalid = os.path.join(FIXTURES, "invalid")
    invalid_files = targets(invalid, {"md", "yaml"})
    for name, files in (("demo-bank", demo_files), ("invalid", invalid_files)):
        if not files:
            print(f"{name}: no files to check under {os.path.join(FIXTURES, name)}")
            bad = True
    for p in demo_files:
        expect_pass(p)
    for p in invalid_files:
        if not check(p, validators):
            print(f"{show(p)}: expected to fail but passed")
            bad = True
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
