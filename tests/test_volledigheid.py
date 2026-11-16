"""Tests for incomplete publication days and for catching up after an outage (no network)."""
import datetime
import unittest

from signalen import update, volledigheid

D = datetime.date
MONDAY = D(2026, 11, 16)
NORMAL = {D(2026, 11, 9): 2159, D(2026, 11, 10): 1860, D(2026, 11, 11): 2973, D(2026, 11, 12): 2630, D(2026, 11, 13): 2083}


def at(hour, day=MONDAY):
    return datetime.datetime(day.year, day.month, day.day, hour, 0)


class OnvolledigeDagTest(unittest.TestCase):
    def test_day_with_almost_no_publications_is_incomplete(self):
        counts = dict(NORMAL)
        counts[MONDAY] = 4  # the situation of 16-11-2026: 4 instead of some 2,100
        self.assertEqual(volledigheid.onvolledige_dagen(counts, at(14)),
                         [{"datum": "2026-11-16", "aantal": 4, "verwacht": 2159}])

    def test_half_indexed_day_is_incomplete_and_a_quiet_day_is_not(self):
        counts = dict(NORMAL)
        counts[D(2026, 11, 12)] = 900   # far below normal: partly delivered
        counts[D(2026, 11, 10)] = 1400  # quiet, but within the normal spread
        self.assertEqual([gap["datum"] for gap in volledigheid.onvolledige_dagen(counts, at(14))], ["2026-11-12"])

    def test_today_is_not_judged_before_publication_time(self):
        counts = dict(NORMAL)
        counts[MONDAY] = 0
        self.assertEqual(volledigheid.onvolledige_dagen(counts, at(8)), [])
        self.assertEqual(len(volledigheid.onvolledige_dagen(counts, at(10))), 1)

    def test_weekends_and_holidays_are_never_incomplete(self):
        counts = dict(NORMAL)
        counts[D(2026, 11, 14)] = 0  # Saturday
        counts[D(2026, 11, 15)] = 1  # Sunday
        self.assertEqual(volledigheid.onvolledige_dagen(counts, at(14, D(2026, 11, 15))), [])
        christmas = {D(2026, 12, 21): 2100, D(2026, 12, 22): 2000, D(2026, 12, 23): 2600, D(2026, 12, 24): 2500, D(2026, 12, 25): 0}
        self.assertEqual(volledigheid.onvolledige_dagen(christmas, at(14, D(2026, 12, 25))), [])
        self.assertIn(D(2026, 4, 6), volledigheid.feestdagen(2026))   # Easter Monday
        self.assertIn(D(2026, 5, 14), volledigheid.feestdagen(2026))  # Ascension Day
        self.assertNotIn(D(2026, 12, 25), volledigheid.publicatiedagen(D(2026, 12, 28)))

    def test_old_gaps_and_thin_evidence_are_ignored(self):
        counts = dict(NORMAL)
        counts[D(2026, 10, 20)] = 0  # outside the check period of 14 days
        self.assertEqual(volledigheid.onvolledige_dagen(counts, at(14)), [])
        self.assertEqual(volledigheid.onvolledige_dagen({MONDAY: 0, D(2026, 11, 13): 2000}, at(14)), [])

    def test_normal_level_does_not_drop_through_outage_days(self):
        normal = [2070, 2036, 2716, 2618, 1951, 1886, 1893, 2622, 2654, 2090]
        self.assertEqual(volledigheid.gebruikelijk(normal), 2080)
        # Five outage days among them: a plain median would fall to 1951, the normal level stays.
        self.assertEqual(volledigheid.gebruikelijk(normal + [0, 4, 0, 12, 300]), 2080)
        # Even when the source was down on most days, the complete days still set the level.
        self.assertEqual(volledigheid.gebruikelijk([2070, 2036, 2716] + [0] * 9), 2070)
        self.assertIsNone(volledigheid.gebruikelijk([2070, 0, 0, 0]))  # too few complete days to judge
        self.assertIsNone(volledigheid.gebruikelijk([0, 0, 0]))

    def test_long_outage_flags_every_affected_day_with_the_normal_level(self):
        days = volledigheid.publicatiedagen(MONDAY, 28)
        counts = {day: 2100 for day in days}
        outage = [day for day in days if day >= D(2026, 11, 4)]  # nine working days in a row
        for day in outage:
            counts[day] = 3
        gaps = volledigheid.onvolledige_dagen(counts, at(14))
        self.assertEqual([gap["datum"] for gap in gaps], [day.isoformat() for day in outage])
        self.assertTrue(all(gap["verwacht"] == 2100 for gap in gaps))

    def test_check_counts_every_working_day_once(self):
        asked = []
        gaps = volledigheid.controleer(at(14), tel=lambda day: asked.append(day) or (0 if day == MONDAY else 2000))
        self.assertEqual([gap["datum"] for gap in gaps], ["2026-11-16"])
        self.assertEqual(len(asked), len(set(asked)))
        self.assertTrue(all(day.weekday() < 5 for day in asked))


def item(identifier, day):
    return {"id": identifier, "datum": day, "afstandKm": 1.0}


CONFIG = {"venster_dagen": {"vergunning": 42, "plan": 180, "faillissement": 28, "verkoop": 120},
          "centrum": {}, "straal_km": 15, "drempel_perceel_m2": 400}


class InhalenTest(unittest.TestCase):
    """A day the source missed is fetched again by the next run, because every run takes the whole window."""

    def run_once(self, available, gaps):
        return update.run(CONFIG, {"gemeenten": []}, at(14), fetchers={"officielebekendmakingen": lambda: list(available)},
                          verrijker=lambda found: (found, {}), dagcontrole=lambda now: gaps)

    def test_missed_day_is_caught_up_and_flag_disappears(self):
        friday = item("gmb-1", "2026-11-13")
        monday = item("gmb-2", "2026-11-16")
        during = self.run_once([friday], [{"datum": "2026-11-16", "aantal": 0, "verwacht": 2097}])
        self.assertEqual([i["id"] for i in during["berichten"]], ["gmb-1"])
        self.assertEqual(during["onvolledigeDagen"][0]["datum"], "2026-11-16")

        after = self.run_once([friday, monday], [])
        self.assertEqual([i["id"] for i in after["berichten"]], ["gmb-2", "gmb-1"])
        self.assertEqual(after["onvolledigeDagen"], [])

    def test_failing_check_does_not_block_the_update(self):
        def broken(now):
            raise RuntimeError("zoekdienst antwoordt niet")
        document = update.run(CONFIG, {"gemeenten": []}, at(14), fetchers={"officielebekendmakingen": lambda: [item("gmb-1", "2026-11-13")]},
                              verrijker=lambda found: (found, {}), dagcontrole=broken)
        self.assertEqual((len(document["berichten"]), document["onvolledigeDagen"]), (1, []))

    def test_failing_source_is_reported_not_hidden(self):
        def down():
            raise RuntimeError("503")
        document = update.run(CONFIG, {"gemeenten": []}, at(14), fetchers={"officielebekendmakingen": down},
                              verrijker=lambda found: (found, {}), dagcontrole=lambda now: [])
        status = next(s for s in document["bronnen"] if s["id"] == "officielebekendmakingen")
        self.assertEqual((status["status"], document["berichten"]), ("fout", []))


if __name__ == "__main__":
    unittest.main()
