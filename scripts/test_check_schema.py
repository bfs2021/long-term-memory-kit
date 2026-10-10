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
    ("id-trailing-newline.md", "id"),
    ("memory-type-policy.md", "memory_type"),
    ("applies-to-no-prefix.md", "applies_to/0"),
    ("related-no-separator.md", "related/0"),
    ("deciders-nested.md", "deciders"),
    ("date-impossible.md", "date"),
    ("config-extra-key/memory-bank.yaml", "colour"),
    ("consumers-key-newline/memory-bank.yaml", "consumers"),
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

    def test_repo_as_committed_passes(self):
        r = run()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_each_invalid_case_fails_with_its_key(self):
        for name, key in CASES:
            with self.subTest(case=name):
                rel = os.path.join("fixtures", "invalid", name)
                r = run(os.path.join(ROOT, rel))
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                # One defect per fixture: a second diagnostic would mask a regression.
                lines = [line for line in r.stdout.splitlines() if line.startswith(f"{rel}:")]
                self.assertEqual(len(lines), 1, r.stdout)
                self.assertTrue(lines[0].startswith(f"{rel}: {key}:"), lines[0])

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

    def test_empty_fixtures_dir_fails_instead_of_checking_nothing(self):
        fixtures = os.path.join(self.tmp, "empty")
        os.makedirs(fixtures)
        r = run(env={"LTM_FIXTURES_DIR": fixtures})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("demo-bank", r.stdout + r.stderr)

    def test_invalid_without_demo_bank_fails(self):
        fixtures = os.path.join(self.tmp, "fixtures")
        os.makedirs(os.path.join(fixtures, "invalid"))
        with open(os.path.join(fixtures, "invalid", "bad.md"), "w") as f:
            f.write("---\nschema: 1\n---\n")
        r = run(env={"LTM_FIXTURES_DIR": fixtures})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("demo-bank", r.stdout + r.stderr)

    def test_malformed_yaml_is_reported_without_a_traceback(self):
        p = os.path.join(self.tmp, "broken.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("---\ntitle: [unclosed\nid: : :\n---\nBody.\n")
        r = run(p)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("(yaml):", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)

    def test_two_extra_config_keys_are_both_reported(self):
        p = self.copy_case(
            "config-extra-key/memory-bank.yaml", lambda t: t + "shade: red\n"
        )
        r = run(p)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("colour,shade:", r.stdout)

    def test_demo_bank_config_flips_on_extra_key(self):
        src = os.path.join(ROOT, "fixtures", "demo-bank", "memory-bank.yaml")
        with open(src, encoding="utf-8") as f:
            original = f.read()
        p = os.path.join(self.tmp, "memory-bank.yaml")
        with open(p, "w", encoding="utf-8") as f:
            f.write(original + "colour: blue\n")
        r = run(p)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("colour:", r.stdout)
        with open(p, "w", encoding="utf-8") as f:
            f.write(original)
        r = run(p)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_path_argument_is_a_usage_error(self):
        r = run(os.path.join(self.tmp, "nope.md"))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
