"""Tests for when the workflow on GitHub starts (.github/workflows/dagelijks.yml), read as text:
the standard library has no YAML reader."""
import pathlib
import re
import unittest

WORKFLOW = pathlib.Path(__file__).resolve().parent.parent / ".github" / "workflows" / "dagelijks.yml"


def section(text, name):
    """The lines under `  name:` in the `on:` block, up to the next key at the same depth."""
    match = re.search(r"^  %s:\n((?:(?:    .*|\s*)\n)*)" % re.escape(name), text, flags=re.M)
    return match.group(1) if match else None


class WanneerDeRunStart(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")
        self.push = section(self.text, "push")

    def test_a_push_to_main_starts_a_run(self):
        self.assertIsNotNone(self.push)
        self.assertRegex(self.push, r"(?m)^    branches: \[main\]$")

    def test_a_push_that_only_touches_docs_does_not(self):
        ignored = re.search(r"(?m)^    paths-ignore:\n((?:      - .*\n)+)", self.push)
        self.assertIsNotNone(ignored, "paths-ignore ontbreekt onder push")
        self.assertEqual(re.findall(r'- "([^"]+)"', ignored.group(1)), ["docs/**"])

    def test_nothing_else_is_left_out(self):
        # `paths:` next to `paths-ignore:` is refused by GitHub, and a broader pattern would let a change of the app go unpublished.
        self.assertNotRegex(self.push, r"(?m)^    paths:")
        self.assertNotRegex(self.text, r"(?m)^\s*-\s*[\"']?(\*\*|site/|signalen/|tests/|\.github/)")

    def test_scheduled_and_manual_runs_are_untouched(self):
        schedule = section(self.text, "schedule")
        self.assertEqual(len(re.findall(r"- cron:", schedule)), 6)
        self.assertEqual(len(re.findall(r'timezone: "Europe/Amsterdam"', schedule)), 6)
        self.assertNotIn("paths", schedule)
        self.assertIsNotNone(section(self.text, "workflow_dispatch"))

    def test_the_run_still_tests_before_it_publishes(self):
        steps = re.findall(r"(?m)^      - (?:name: (.+)|uses: (\S+))", self.text)
        names = [name or uses for name, uses in steps]
        self.assertLess(names.index("Tests"), names.index("Berichten ophalen"))
        self.assertLess(names.index("Berichten ophalen"), names.index("actions/upload-pages-artifact@v3"))


if __name__ == "__main__":
    unittest.main()
