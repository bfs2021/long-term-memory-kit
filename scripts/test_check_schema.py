import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(HERE, "check-schema.py")
INVALID = os.path.join(ROOT, "fixtures", "invalid")

# Expected keys come from the issue-5 plan table, not from the script's output.
CASES = [
    ("missing-status.md", "status"),
    ("status-approved.md", "status"),
    ("id-nine-chars.md", "id"),
    ("memory-type-policy.md", "memory_type"),
    ("applies-to-no-prefix.md", "applies_to/0"),
    ("related-no-separator.md", "related/0"),
    ("deciders-nested.md", "deciders"),
    ("date-impossible.md", "date"),
    ("config-extra-key/memory-bank.yaml", "colour"),
]

VALID_RECORD = """---
schema: 1
id: aB3dEf7hIj
memory_type: Decision
title: Use Postgres for new services
status: accepted
date: {date}
---
Body.
"""


def run(*args, env=None):
    full = dict(os.environ)
    full.update(env or {})
    return subprocess.run(
        [sys.executable, SCRIPT, *args], capture_output=True, text=True, env=full
    )


class CheckSchemaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def copy_case(self, name, edit=None):
        with open(os.path.join(INVALID, name)) as f:
            text = f.read()
        if edit:
            text = edit(text)
        dest = os.path.join(self.tmp, os.path.basename(name))
        with open(dest, "w") as f:
            f.write(text)
        return dest

    @unittest.skipUnless(
        os.path.isdir(os.path.join(ROOT, "fixtures", "demo-bank")),
        "fixtures/demo-bank not landed yet",
    )
    def test_repo_as_committed_passes(self):
        r = run()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_each_invalid_case_fails_with_its_key(self):
        for name, key in CASES:
            with self.subTest(case=name):
                rel = os.path.join("fixtures", "invalid", name)
                r = run(os.path.join(ROOT, rel))
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn(f"{rel}: {key}:", r.stdout)

    def test_missing_status_flips_when_status_added(self):
        p = self.copy_case(
            "missing-status.md", lambda t: t.replace("date:", "status: accepted\ndate:", 1)
        )
        r = run(p)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_deciders_flips_on_value_shape_only(self):
        p = self.copy_case(
            "deciders-nested.md",
            lambda t: t.replace("[{name: a}]", "[alice, bob]"),
        )
        r = run(p)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_possible_date_passes(self):
        p = self.copy_case(
            "date-impossible.md", lambda t: t.replace("2026-02-30", "2026-02-28")
        )
        r = run(p)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_config_without_extra_key_passes(self):
        p = self.copy_case(
            "config-extra-key/memory-bank.yaml",
            lambda t: "".join(l for l in t.splitlines(True) if "colour" not in l),
        )
        r = run(p)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_invalid_case_that_passes_is_reported(self):
        fixtures = os.path.join(self.tmp, "fixtures")
        os.makedirs(os.path.join(fixtures, "invalid"))
        with open(os.path.join(fixtures, "invalid", "fixed.md"), "w") as f:
            f.write(VALID_RECORD.format(date="2026-03-31"))
        r = run(env={"LTM_FIXTURES_DIR": fixtures})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("expected to fail but passed", r.stdout)

    def test_no_frontmatter_fails(self):
        p = os.path.join(self.tmp, "plain.md")
        with open(p, "w") as f:
            f.write("Just a body.\n")
        r = run(p)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("(frontmatter): missing", r.stdout)

    def test_unquoted_yaml_date_reaches_validator_as_string(self):
        p = os.path.join(self.tmp, "dated.md")
        with open(p, "w") as f:
            f.write(VALID_RECORD.format(date="2026-03-31"))
        r = run(p)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_path_argument_is_a_usage_error(self):
        r = run(os.path.join(self.tmp, "nope.md"))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
