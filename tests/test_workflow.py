"""Tests for when the workflow on GitHub starts and what it tests before it publishes
(.github/workflows/dagelijks.yml and .github/actions/browser/action.yml), read as text: the
standard library has no YAML reader."""
import json
import pathlib
import re
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "dagelijks.yml"
BROWSER = ROOT / ".github" / "actions" / "browser" / "action.yml"
# Not on GitHub's own schedule, and not when the planner (tools/planner) starts the run in its place.
NOT_SCHEDULED = "if: github.event_name != 'schedule' && !inputs.gepland"


def section(text, name):
    """The lines under `  name:` (a trigger in the `on:` block, or a job), up to the next key at the same depth."""
    match = re.search(r"^  %s:\n((?:(?:    .*|\s*)\n)*)" % re.escape(name), text, flags=re.M)
    return match.group(1) if match else None


def step_names(text):
    """Every step of the workflow in order: its name, or the action it uses when it has no name."""
    return [name or uses for name, uses in re.findall(r"(?m)^      - (?:name: (.+)|uses: (\S+))", text)]


def step(text, name):
    """The lines of the step called `name`, up to the next step or job."""
    match = re.search(r"(?m)^      - name: %s\n((?:(?:        .*|\s*)\n)*)" % re.escape(name), text)
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
        names = step_names(self.text)
        self.assertLess(names.index("Tests"), names.index("Berichten ophalen"))
        self.assertLess(names.index("Berichten ophalen"), names.index("actions/upload-pages-artifact@v3"))


class Browsertests(unittest.TestCase):
    """The tests in a real browser on GitHub: on a push and on a manual run, not on a scheduled run."""

    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")
        self.build = section(self.text, "bouwen")
        self.names = step_names(self.build)
        self.prepare = step(self.build, "Browser klaarzetten")
        self.tests = step(self.build, "Browsertests")
        self.action = BROWSER.read_text(encoding="utf-8")

    def test_playwright_is_pinned_to_one_version(self):
        wanted = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["devDependencies"]["playwright"]
        self.assertRegex(wanted, r"^\d+\.\d+\.\d+$", "een bereik (^ of ~) laat de versie verschuiven")
        locked = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))["packages"]
        self.assertEqual(locked["node_modules/playwright"]["version"], wanted)
        self.assertEqual(locked["node_modules/playwright-core"]["version"], wanted)

    def test_installed_packages_stay_out_of_git(self):
        self.assertIn("node_modules/", (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
        try:
            done = subprocess.run(["git", "ls-files", "node_modules"], cwd=ROOT, capture_output=True, text=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("geen git-checkout")
        self.assertEqual(done.stdout, "")

    def test_they_run_after_the_quick_tests_and_before_anything_is_fetched_or_published(self):
        # Before fetching: the dry run of the video counts on the data as it is in the repository.
        order = [self.names.index(name) for name in ("Tests", "Browser klaarzetten", "Browsertests", "Berichten ophalen", "actions/upload-pages-artifact@v3")]
        self.assertEqual(order, sorted(order))

    def test_a_scheduled_run_does_not_wait_for_a_browser(self):
        self.assertIn(NOT_SCHEDULED, self.prepare)
        self.assertIn(NOT_SCHEDULED, self.tests)
        # Nothing else depends on how the run was started: the quick tests and the refresh always run.
        self.assertEqual(self.text.count(NOT_SCHEDULED), 2)
        self.assertNotIn("if:", step(self.build, "Tests"))

    def test_a_run_started_by_the_planner_can_say_that_it_is_a_scheduled_one(self):
        manual = section(self.text, "workflow_dispatch")
        for name in ("volledig", "gepland"):
            self.assertRegex(manual, r"(?m)^      %s:\n(?:        .*\n)*?        type: boolean\n        default: false$" % name)

    def test_the_step_runs_both_browser_classes_and_fails_when_playwright_is_missing(self):
        # Without Playwright these tests skip themselves; the step would be green and test nothing.
        lines = [line.strip() for line in self.tests.splitlines()]
        self.assertLess(lines.index("""node -e "require('playwright')\""""), lines.index("python -m unittest tests.test_site.InDeBrowser tests.test_video.Droogloop"))
        self.assertIn("class InDeBrowser(", (ROOT / "tests" / "test_site.py").read_text(encoding="utf-8"))
        self.assertIn("class Droogloop(", (ROOT / "tests" / "test_video.py").read_text(encoding="utf-8"))

    def test_a_hanging_browser_cannot_hold_up_the_runs_behind_it(self):
        # One run at a time (concurrency): without a limit a hanging step blocks every later run for hours.
        for part in (self.prepare, self.tests):
            self.assertRegex(part, r"(?m)^        timeout-minutes: \d+$")

    def test_node_and_playwright_come_from_the_lockfile_and_only_chromium_is_installed(self):
        self.assertIn("uses: ./.github/actions/browser", self.prepare)
        self.assertRegex(self.action, r'uses: actions/setup-node@v\d+\n      with:\n        node-version: "\d+"')
        self.assertRegex(self.action, r"(?m)^      run: npm ci$")
        self.assertEqual(re.findall(r"(?m)^      run: npx playwright install (.*)$", self.action), ["--with-deps chromium"])

    def test_the_browser_is_kept_between_runs_under_the_playwright_version(self):
        self.assertRegex(self.action, r"uses: actions/cache@v\d+")
        self.assertRegex(self.action, r"(?m)^        path: ~/\.cache/ms-playwright$")
        self.assertRegex(self.action, r"(?m)^        key: .*\$\{\{ steps\.playwright\.outputs\.versie \}\}")
        self.assertIn("""versie=$(node -p "require('playwright/package.json').version")""", self.action)
        order = [self.action.index(part) for part in ("run: npm ci", "id: playwright", "uses: actions/cache@", "npx playwright install")]
        self.assertEqual(order, sorted(order))


class LiveSite(unittest.TestCase):
    """After every publication, scheduled runs included, the page of the live site is tested in a real browser."""

    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")
        self.build, self.publish, self.live = (section(self.text, name) for name in ("bouwen", "publiceren", "live-controleren"))

    def test_only_a_run_from_main_publishes(self):
        self.assertRegex(self.publish, r"(?m)^    if: github\.ref == 'refs/heads/main'$")
        # The refresh itself does not depend on the branch or on how the run was started.
        self.assertNotRegex(self.build, r"(?m)^    if:")

    def test_it_runs_after_every_publication(self):
        self.assertRegex(self.live, r"(?m)^    needs: publiceren$")
        # No condition of its own: it follows publiceren, on a scheduled run as well.
        self.assertNotIn("if:", self.live)

    def test_it_does_not_hold_up_the_publication(self):
        self.assertRegex(self.publish, r"(?m)^    needs: bouwen$")
        self.assertNotIn("needs:", self.build)
        self.assertEqual(re.findall(r"(?m)^  ([\w-]+):$", self.text[self.text.index("\njobs:"):]), ["bouwen", "publiceren", "live-controleren"])

    def test_it_tests_the_page_at_the_live_address_and_fails_when_playwright_is_missing(self):
        test = step(self.live, "Paginatest tegen de live site")
        self.assertRegex(test, r"(?m)^          TILBURG_SITE_URL: https://wim1201\.github\.io/tilburg-signalen$")
        lines = [line.strip() for line in test.splitlines()]
        self.assertLess(lines.index("""node -e "require('playwright')\""""), lines.index("python -m unittest tests.test_site.InDeBrowser"))
        self.assertIn('os.environ.get("TILBURG_SITE_URL")', (ROOT / "tests" / "test_site.py").read_text(encoding="utf-8"))

    def test_it_uses_the_same_browser_and_the_same_checkout_as_the_build(self):
        self.assertIn("uses: ./.github/actions/browser", step(self.live, "Browser klaarzetten"))
        # The test compares the live site with the house style in the repository.
        self.assertEqual(self.live.count("ref: ${{ github.ref_name }}"), 1)
        self.assertEqual(self.build.count("ref: ${{ github.ref_name }}"), 1)

    def test_a_hanging_check_cannot_hold_up_the_runs_behind_it_and_cannot_write(self):
        self.assertRegex(self.live, r"(?m)^    timeout-minutes: \d+$")
        self.assertRegex(self.live, r"(?m)^    permissions:\n      contents: read\n    steps:$")


if __name__ == "__main__":
    unittest.main()
