"""Tests for the planner (tools/planner): the Cloudflare Worker that starts the workflow on GitHub at
the Dutch times of its schedule. Without Cloudflare and without network: GitHub's answers are given
by the test. The parts that run the Worker's code need Node and are skipped without it."""
import calendar
import datetime
import json
import pathlib
import re
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLANNER = ROOT / "tools" / "planner"
WORKFLOW = ROOT / ".github" / "workflows" / "dagelijks.yml"
NODE = shutil.which("node")
TOKEN = "github_pat_NIET_ECHT_alleen_voor_de_test"
ENV = {"GITHUB_TOKEN": TOKEN, "GITHUB_REPO": "Wim1201/tilburg-signalen", "WORKFLOW": "dagelijks.yml", "REF": "main"}
TUESDAY_0645 = "2026-11-17T05:45:00Z"   # winter time: 06:45 in the Netherlands
SUNDAY_0430 = "2026-11-22T03:30:00Z"


def planner(*calls):
    done = subprocess.run([NODE, str(ROOT / "tests" / "js" / "run_planner.mjs")], input=json.dumps(calls), capture_output=True, text=True,
                          encoding="utf-8", timeout=120)
    if done.returncode:
        raise AssertionError(done.stderr)
    return json.loads(done.stdout)


def config():
    """wrangler.jsonc without its comments (each on a line of its own)."""
    text = (PLANNER / "wrangler.jsonc").read_text(encoding="utf-8")
    return json.loads("\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//")))


def days(field):
    """The days of the week of a cron field (0 is Sunday): "*", "0" or "1-5"."""
    if field == "*":
        return list(range(7))
    if "-" in field:
        first, last = field.split("-")
        return list(range(int(first), int(last) + 1))
    return [int(field)]


def run(status="completed", conclusion="success", created="2026-11-17T04:00:00Z", event="schedule"):
    return {"status": status, "conclusion": conclusion, "created_at": created, "event": event}


def loop(tijd=TUESDAY_0645, env=ENV, antwoorden=()):
    return planner(["loop", {"tijd": tijd, "env": env, "antwoorden": list(antwoorden)}])[0]


RUNS_QUIET = {"status": 200, "body": {"workflow_runs": [run()]}}
STARTED = {"status": 204}


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Rooster(unittest.TestCase):
    def test_the_slots_are_those_of_the_schedule_in_the_workflow(self):
        crons = re.findall(r'- cron: "(\d+) (\d+) \* \* (\S+)"', WORKFLOW.read_text(encoding="utf-8"))
        self.assertEqual(len(crons), 6)
        wanted = sorted((int(hour), int(minute), days(field)) for minute, hour, field in crons)
        slots = planner(["ROOSTER"])[0]
        self.assertEqual(sorted((slot["uur"], slot["minuut"], slot["dagen"]) for slot in slots), wanted)

    def test_only_the_run_of_sunday_before_nine_is_a_full_refresh(self):
        # The workflow recognises its own weekly run the same way: scheduled, on Sunday, before 9 o'clock.
        full = [slot for slot in planner(["ROOSTER"])[0] if slot.get("volledig")]
        self.assertEqual([(slot["dagen"], slot["uur"], slot["minuut"]) for slot in full], [([0], 4, 30)])
        early_on_sunday = [slot for slot in planner(["ROOSTER"])[0] if 0 in slot["dagen"] and slot["uur"] < 9]
        self.assertEqual(early_on_sunday, full)

    def test_the_time_is_dutch_time_in_winter_and_in_summer(self):
        winter, summer, hour_off, saturday_morning, saturday_noon, sunday = planner(
            ["slotOp", "2026-11-17T05:45:00Z"], ["slotOp", "2026-07-14T04:45:00Z"], ["slotOp", "2026-11-17T04:45:00Z"],
            ["slotOp", "2026-11-21T05:45:00Z"], ["slotOp", "2026-11-21T11:10:00Z"], ["slotOp", SUNDAY_0430])
        self.assertEqual((winter["uur"], winter["minuut"]), (6, 45))
        self.assertEqual((summer["uur"], summer["minuut"]), (6, 45))
        self.assertIsNone(hour_off, "05:45 uur Nederlandse tijd is geen slot")
        self.assertIsNone(saturday_morning, "06:45 uur is er alleen op werkdagen")
        self.assertEqual((saturday_noon["uur"], saturday_noon["minuut"]), (12, 10))
        self.assertTrue(sunday["volledig"])

    def test_every_slot_falls_exactly_once_on_each_of_its_days_also_when_the_clock_changes(self):
        # 2027: the clock goes forward on Sunday 28 March and back on Sunday 31 October.
        year = planner(["jaar", 2027])[0]
        self.assertEqual(year["dubbel"], [])
        expected = {6: 2, 5: 1}   # Python counts Monday as 0: Sunday two slots, Saturday one, working days five
        for month in range(1, 13):
            for day in range(1, calendar.monthrange(2027, month)[1] + 1):
                date = datetime.date(2027, month, day)
                self.assertEqual(year["perDag"].get(date.isoformat(), 0), expected.get(date.weekday(), 5), date.isoformat())

    def test_the_cron_trigger_reaches_every_slot_and_there_is_only_one(self):
        # Cloudflare's free plan allows five cron triggers per account.
        self.assertEqual(config()["triggers"]["crons"], ["*/5 * * * *"])
        self.assertTrue(all(slot["minuut"] % 5 == 0 for slot in planner(["ROOSTER"])[0]))


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class WelOfNietStarten(unittest.TestCase):
    def decide(self, runs, at=TUESDAY_0645):
        return planner(["besluit", runs, at])[0]

    def test_nothing_running_and_nothing_recent_starts_a_run(self):
        self.assertTrue(self.decide([run()])["starten"])
        self.assertTrue(self.decide([])["starten"])

    def test_a_run_that_is_running_or_waiting_is_not_joined_by_another(self):
        # GitHub keeps one waiting run per concurrency group; a second one would push the first out.
        for status in ("in_progress", "queued", "waiting", "pending", "requested"):
            with self.subTest(status=status):
                choice = self.decide([run(status=status, conclusion=None, created="2026-11-17T05:44:00Z")])
                self.assertFalse(choice["starten"])
                self.assertIn("loopt of wacht", choice["reden"])

    def test_a_run_that_has_just_succeeded_is_enough(self):
        choice = self.decide([run(created="2026-11-17T05:38:00Z", event="push")])
        self.assertFalse(choice["starten"])
        self.assertIn("zojuist", choice["reden"])
        self.assertTrue(self.decide([run(created="2026-11-17T05:30:00Z")])["starten"], "een kwartier geleden is niet zojuist")

    def test_a_run_that_has_just_failed_is_followed_by_a_new_one(self):
        self.assertTrue(self.decide([run(conclusion="failure", created="2026-11-17T05:40:00Z")])["starten"])


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class EenAanroep(unittest.TestCase):
    def test_outside_the_slots_github_is_not_called_at_all(self):
        seen = loop(tijd="2026-11-17T05:50:00Z")
        self.assertEqual((seen["verzoeken"], seen["logboek"], seen["fout"]), ([], [], None))

    def test_on_a_slot_the_workflow_is_started_on_main_as_a_scheduled_run(self):
        seen = loop(antwoorden=[RUNS_QUIET, STARTED])
        self.assertIsNone(seen["fout"])
        listed, started = seen["verzoeken"]
        self.assertEqual((listed["method"], listed["url"]), ("GET", "https://api.github.com/repos/Wim1201/tilburg-signalen/actions/workflows/dagelijks.yml/runs?per_page=10"))
        self.assertEqual((started["method"], started["url"]), ("POST", "https://api.github.com/repos/Wim1201/tilburg-signalen/actions/workflows/dagelijks.yml/dispatches"))
        self.assertEqual(started["body"], {"ref": "main", "inputs": {"gepland": "true", "volledig": "false"}})
        for request in (listed, started):
            self.assertEqual(request["headers"]["Authorization"], "Bearer " + TOKEN)
            self.assertEqual(request["headers"]["Accept"], "application/vnd.github+json")
            self.assertTrue(request["headers"]["User-Agent"], "GitHub weigert verzoeken zonder User-Agent")
        self.assertEqual(json.loads(seen["logboek"][-1])["planner"], "gestart")

    def test_the_inputs_it_sends_exist_in_the_workflow(self):
        # GitHub refuses a start with an input the workflow does not know (422).
        sent = loop(antwoorden=[RUNS_QUIET, STARTED])["verzoeken"][1]["body"]["inputs"]
        manual = re.search(r"(?m)^  workflow_dispatch:\n    inputs:\n((?:      .*\n|\s*\n)*)", WORKFLOW.read_text(encoding="utf-8")).group(1)
        self.assertEqual(sorted(sent), sorted(re.findall(r"(?m)^      (\w+):$", manual)))

    def test_the_sunday_morning_slot_asks_for_a_full_refresh(self):
        seen = loop(tijd=SUNDAY_0430, antwoorden=[RUNS_QUIET, STARTED])
        self.assertEqual(seen["verzoeken"][1]["body"]["inputs"], {"gepland": "true", "volledig": "true"})

    def test_nothing_is_started_while_a_run_is_running(self):
        busy = {"status": 200, "body": {"workflow_runs": [run(status="in_progress", conclusion=None, created="2026-11-17T05:44:30Z")]}}
        seen = loop(antwoorden=[busy])
        self.assertEqual([request["method"] for request in seen["verzoeken"]], ["GET"])
        self.assertIsNone(seen["fout"])
        self.assertEqual(json.loads(seen["logboek"][-1])["planner"], "overgeslagen")

    def test_a_missing_token_is_said_plainly_and_nothing_is_sent(self):
        seen = loop(env={key: value for key, value in ENV.items() if key != "GITHUB_TOKEN"})
        self.assertEqual(seen["verzoeken"], [])
        self.assertIn("GITHUB_TOKEN ontbreekt", seen["fout"])

    def test_a_refused_token_fails_the_invocation(self):
        for status in (401, 403):
            with self.subTest(status=status):
                seen = loop(antwoorden=[{"status": status, "body": {"message": "Bad credentials"}}])
                self.assertEqual(len(seen["verzoeken"]), 1)
                self.assertIn("GitHub weigert het token: %d" % status, seen["fout"])

    def test_when_the_list_of_runs_cannot_be_read_the_run_is_started_anyway(self):
        # Rather a run too many than a refresh that does not happen.
        for unreadable in ({"status": 502}, {"fout": "network down"}):
            with self.subTest(antwoord=unreadable):
                seen = loop(antwoorden=[unreadable, STARTED])
                self.assertIsNone(seen["fout"])
                self.assertEqual([request["method"] for request in seen["verzoeken"]], ["GET", "POST"])

    def test_a_failure_on_githubs_side_is_tried_once_more(self):
        seen = loop(antwoorden=[RUNS_QUIET, {"status": 503}, STARTED])
        self.assertIsNone(seen["fout"])
        self.assertEqual([request["method"] for request in seen["verzoeken"]], ["GET", "POST", "POST"])
        still_down = loop(antwoorden=[RUNS_QUIET, {"status": 503}, {"status": 503}])
        self.assertIn("GitHub heeft de run niet gestart: 503", still_down["fout"])
        self.assertEqual(len(still_down["verzoeken"]), 3)

    def test_a_refused_start_is_not_repeated_and_shows_what_github_said(self):
        refused = {"status": 422, "body": {"message": "Unexpected inputs provided: [\"gepland\"]"}}
        seen = loop(antwoorden=[RUNS_QUIET, refused])
        self.assertEqual(len(seen["verzoeken"]), 2)
        self.assertIn("422", seen["fout"])
        self.assertIn("Unexpected inputs provided", seen["fout"])
        self.assertEqual(json.loads(seen["logboek"][-1])["planner"], "fout")

    def test_the_main_module_exports_only_the_handler(self):
        # Cloudflare's runtime refuses to start a Worker whose main module exports a plain value
        # ("Incorrect type for map entry"); `wrangler deploy --dry-run` does not notice that.
        self.assertEqual(planner(["exports"])[0], ["default"])

    def test_the_token_never_appears_in_the_log_or_in_an_error(self):
        for answers in ([RUNS_QUIET, STARTED], [RUNS_QUIET, {"status": 422, "body": {"message": "no"}}], [{"status": 401}], [{"fout": "down"}, {"fout": "down"}, {"fout": "down"}]):
            seen = loop(antwoorden=answers)
            self.assertNotIn(TOKEN, json.dumps([seen["logboek"], seen["fout"]]))


class NietsOpenbaarEnGeenGeheimen(unittest.TestCase):
    def setUp(self):
        self.config = config()
        self.code = "".join((PLANNER / "src" / name).read_text(encoding="utf-8") for name in ("index.js", "planner.js"))

    def test_the_worker_has_no_public_address_and_does_not_answer_requests(self):
        # Anyone who could call it could start runs.
        self.assertIs(self.config["workers_dev"], False)
        self.assertIs(self.config["preview_urls"], False)
        self.assertNotIn("routes", self.config)
        self.assertNotIn("route", self.config)
        self.assertNotRegex(self.code, r"\bfetch\s*\(\s*(request|req)\b|async fetch\b")

    def test_the_token_is_a_secret_and_is_not_in_the_repository(self):
        self.assertEqual(self.config["secrets"], {"required": ["GITHUB_TOKEN"]})
        self.assertNotIn("GITHUB_TOKEN", self.config["vars"])
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        for name in (".dev.vars*", ".env*", ".wrangler/"):
            self.assertIn(name, ignored)
        try:
            tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("geen git-checkout")
        self.assertEqual([name for name in tracked if re.search(r"(^|/)(\.dev\.vars|\.env)", name)], [])
        for name in tracked:
            if name.startswith("tools/planner/") or name == "tests/test_planner.py":
                text = (ROOT / name).read_text(encoding="utf-8").replace(TOKEN, "")
                self.assertNotRegex(text, r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}", name)

    def test_it_starts_this_workflow_on_main(self):
        self.assertEqual(self.config["vars"], {"GITHUB_REPO": "Wim1201/tilburg-signalen", "WORKFLOW": "dagelijks.yml", "REF": "main"})
        self.assertTrue((ROOT / ".github" / "workflows" / self.config["vars"]["WORKFLOW"]).is_file())
        self.assertEqual(self.config["main"], "src/index.js")


if __name__ == "__main__":
    unittest.main()
