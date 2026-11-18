"""Tests for "Bijgewerkt" at the top of the app: it is the moment of the last refresh that
succeeded, not the moment the notices last changed. A skipped refresh therefore shows as an old time."""
import datetime
import json
import pathlib
import subprocess
import tempfile
import unittest
import unittest.mock
import zoneinfo

from signalen import update

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = {"venster_dagen": {"vergunning": 42, "plan": 180, "faillissement": 28, "verkoop": 120},
          "centrum": {}, "straal_km": 15, "drempel_perceel_m2": 400}
AMSTERDAM = zoneinfo.ZoneInfo("Europe/Amsterdam")


def notice(identifier, day):
    return {"id": identifier, "datum": day, "afstandKm": 1.0, "type": "vergunning", "titel": "x", "omschrijving": "y", "activiteiten": []}


def run_at(moment, notices):
    return update.run(CONFIG, {"gemeenten": []}, moment, fetchers={"officielebekendmakingen": lambda: [dict(n) for n in notices]},
                      verrijker=lambda found: (found, {}), dagcontrole=lambda now: [])


class TijdstipVanDeVerversing(unittest.TestCase):
    def test_it_is_the_moment_the_refresh_ran(self):
        moment = datetime.datetime(2026, 11, 17, 6, 45, 12, tzinfo=AMSTERDAM)
        document = run_at(moment, [notice("gmb-1", "2026-11-13")])
        self.assertEqual(document["bijgewerkt"], "2026-11-17T06:45:12+01:00")

    def test_a_refresh_that_finds_nothing_new_still_moves_the_time(self):
        notices = [notice("gmb-1", "2026-11-13")]
        monday = run_at(datetime.datetime(2026, 11, 16, 17, 38, 35, tzinfo=AMSTERDAM), notices)
        tuesday = run_at(datetime.datetime(2026, 11, 17, 6, 45, 12, tzinfo=AMSTERDAM), notices)
        self.assertEqual(monday["berichten"], tuesday["berichten"])
        self.assertEqual((monday["bijgewerkt"], tuesday["bijgewerkt"]), ("2026-11-16T17:38:35+01:00", "2026-11-17T06:45:12+01:00"))

    def test_it_does_not_follow_the_date_of_the_newest_notice(self):
        document = run_at(datetime.datetime(2026, 11, 17, 6, 45, tzinfo=AMSTERDAM), [notice("gmb-1", "2026-10-01")])
        self.assertTrue(document["bijgewerkt"].startswith("2026-11-17T06:45"))


class GeschrevenBestand(unittest.TestCase):
    """What ends up in site/data/berichten.json, with the sources replaced by stand-ins."""

    OLD = {"bijgewerkt": "2026-11-16T17:38:35+01:00", "berichten": []}

    def write(self, main_source_status):
        seen = {}

        def fake_run(config, area, now, cache=None, **extra):
            seen["now"] = now
            return {"bijgewerkt": now.isoformat(timespec="seconds"), "berichten": [], "ophaalstatistiek": {}, "ophaalfouten": {},
                    "cache": {}, "onvolledigeDagen": [],
                    "bronnen": [{"id": "officielebekendmakingen", "status": main_source_status, "aantal": 0},
                                {"id": "staatscourant-insolventies", "status": "ok", "aantal": 0}]}

        with tempfile.TemporaryDirectory() as folder:
            output = pathlib.Path(folder) / "berichten.json"
            output.write_text(json.dumps(self.OLD), encoding="utf-8")
            with unittest.mock.patch.object(update, "OUTPUT", output), unittest.mock.patch.object(update, "run", fake_run), \
                    unittest.mock.patch.object(update.cachemodule, "Cache", unittest.mock.MagicMock()), \
                    unittest.mock.patch("builtins.print"):
                try:
                    update.main([])
                    stopped = None
                except SystemExit as stop:
                    stopped = str(stop)
            return json.loads(output.read_text(encoding="utf-8")), seen["now"], stopped

    def test_a_successful_refresh_writes_its_own_moment_in_dutch_time(self):
        before = datetime.datetime.now(AMSTERDAM)
        written, moment, stopped = self.write("ok")
        self.assertIsNone(stopped)
        stamp = datetime.datetime.fromisoformat(written["bijgewerkt"])
        self.assertEqual(stamp.utcoffset(), before.utcoffset())
        self.assertLess(abs((stamp - before).total_seconds()), 120)
        self.assertEqual(written["bijgewerkt"], moment.isoformat(timespec="seconds"))

    def test_a_refresh_that_fails_leaves_the_old_time_so_the_gap_shows(self):
        written, moment, stopped = self.write("fout")
        self.assertIn("Hoofdbron niet bereikbaar", stopped)
        self.assertEqual(written, self.OLD)


class GeenFilmInGit(unittest.TestCase):
    """Films are made with tools/video and handed over outside the repository."""

    def test_no_film_or_still_is_tracked(self):
        try:
            done = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("geen git-checkout")
        films = [name for name in done.stdout.splitlines() if name.lower().endswith((".mp4", ".webm", ".mov", ".mkv", ".avi", ".gif"))]
        self.assertEqual(films, [])
        self.assertEqual([name for name in done.stdout.splitlines() if name.startswith("tools/video/uit/")], [])
        large = [name for name in done.stdout.splitlines() if (ROOT / name).is_file() and (ROOT / name).stat().st_size > 1_500_000]
        self.assertEqual(large, [], "bestanden groter dan 1,5 MB horen niet in de repo")


if __name__ == "__main__":
    unittest.main()
