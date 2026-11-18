"""Tests for version 2 of the app: the ranking and the cards (site/logic.js), the house style
(site/styles.css), the mark and the icons, and what the page and the service worker refer to.

The logic tests run site/logic.js under Node and are skipped when Node is missing. The browser
test also needs Playwright and is skipped without it."""
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import threading
import unittest
import xml.etree.ElementTree as ET
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
JS = os.path.join(ROOT, "tests", "js")
NODE = shutil.which("node")


def read(*parts):
    with open(os.path.join(SITE, *parts), encoding="utf-8") as handle:
        return handle.read()


def logic(*calls):
    """Run functions of site/logic.js; each call is [name, arg, ...]. Returns the list of results."""
    done = subprocess.run([NODE, os.path.join(JS, "run_logic.js")], input=json.dumps(calls), capture_output=True,
                          text=True, encoding="utf-8", timeout=60)
    if done.returncode:
        raise AssertionError(done.stderr)
    return json.loads(done.stdout)


def item(id, score=50, datum="2026-11-10", km=5.0, klasse="ontwikkellocatie", **extra):
    base = {
        "id": id, "bron": "officielebekendmakingen", "publicatie": "Gemeenteblad", "overheid": "Tilburg", "type": "vergunning",
        "fase": "Aanvraag", "soort": None, "titel": "Aanvraag " + id, "omschrijving": None, "activiteiten": [],
        "datum": datum, "gemeente": "Tilburg", "plaats": "Teststraat 1, Tilburg", "afstandKm": km, "locatieSoort": "exact",
        "lat": 51.56, "lon": 5.09, "reactieTot": None, "planId": None,
        "url": "https://zoek.officielebekendmakingen.nl/" + id + ".html", "urlTekst": None,
        "klasse": klasse, "score": score, "waarom": "3 nieuwe woningen.", "signalen": [], "woningen": 3, "perceelM2": None,
    }
    base.update(extra)
    return base


CENTRE = {"naam": "De Heuvel, Tilburg-centrum", "lat": 51.55717769, "lon": 5.0910001}
STATE = {"view": "ranglijst", "sort": "relevantie", "toonWeg": False, "zoek": "", "type": "", "gemeente": "", "fase": "",
         "signaal": "", "dagen": 0, "maxKm": 15}
TODAY = {"$date": "2026-11-16T07:00:00"}


def state(**changes):
    return dict(STATE, **changes)


def context(nieuw=None, latest="2026-11-16"):
    return {"nieuw": nieuw or {}, "latestDay": latest, "today": TODAY}


def ids(items):
    return [entry["id"] for entry in items]


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Rangorde(unittest.TestCase):
    """The highest rank is at the top, and the place in the ranking belongs to the item."""

    def test_highest_score_first_then_newest_then_nearest(self):
        items = [item("laag", 40), item("hoog", 100), item("oud", 80, "2026-10-01"), item("nieuw", 80, "2026-11-01"),
                 item("ver", 60, km=9.0), item("dichtbij", 60, km=1.0)]
        result, = logic(["sorted", items, "relevantie"])
        self.assertEqual(ids(result), ["hoog", "nieuw", "oud", "dichtbij", "ver", "laag"])

    def test_sorting_and_ranking_leave_the_data_as_it_is(self):
        script = ("var L = require(process.argv[1]); var items = JSON.parse(process.argv[2]); var before = JSON.stringify(items);"
                  "L.sorted(items, 'relevantie'); L.sorted(items, 'afstand'); L.rankMap(items);"
                  "L.select(items, {view: 'ranglijst', sort: 'relevantie', maxKm: 15}, {nieuw: {}, today: new Date()});"
                  "console.log(JSON.stringify(items) === before ? 'gelijk' : 'gewijzigd');")
        items = [item("a", 40, km=9.0), item("b", 100, km=1.0), item("c", 70, klasse="onzeker")]
        done = subprocess.run([NODE, "-e", script, os.path.join(SITE, "logic.js"), json.dumps(items)], capture_output=True, text=True, timeout=60)
        self.assertEqual(done.stdout.strip(), "gelijk", done.stderr)

    def test_other_orders(self):
        items = [item("a", 40, "2026-11-12", km=3.0), item("b", 100, "2026-11-10", km=8.0), item("c", 70, "2026-11-01", km=1.0)]
        by_date, by_distance = logic(["sorted", items, "datum"], ["sorted", items, "afstand"])
        self.assertEqual(ids(by_date), ["a", "b", "c"])  # the data file is already newest first
        self.assertEqual(ids(by_distance), ["c", "a", "b"])

    def test_rank_counts_per_class_and_skips_what_is_filtered_out(self):
        items = [item("l2", 70), item("o1", 60, klasse="onzeker"), item("l1", 90), item("w", 0, klasse="weggefilterd"),
                 item("o2", 50, klasse="onzeker")]
        ranks, = logic(["rankMap", items])
        self.assertEqual(ranks, {"l1": 1, "l2": 2, "o1": 1, "o2": 2})

    def test_rank_does_not_move_when_the_list_is_filtered(self):
        items = [item("a", 100, gemeente="Goirle"), item("b", 90), item("c", 80, gemeente="Goirle"), item("d", 70)]
        ranks, chosen = logic(["rankMap", items], ["select", items, state(gemeente="Goirle"), context()])
        self.assertEqual(ids(chosen["main"]), ["a", "c"])
        self.assertEqual([ranks[i] for i in ids(chosen["main"])], [1, 3])

    def test_first_screen_shows_the_top_ten(self):
        top, = logic(["TOP"])
        self.assertEqual(top, 10)


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Lijsten(unittest.TestCase):
    """Which notices each of the three lists shows."""

    def setUp(self):
        self.items = [item("l1", 90), item("l2", 70, datum="2026-11-16"), item("o1", 60, klasse="onzeker"),
                      item("w1", 0, klasse="weggefilterd"), item("w2", 0, klasse="weggefilterd", datum="2026-11-16")]

    def test_ranking_shows_only_development_locations(self):
        chosen, = logic(["select", self.items, state(), context()])
        self.assertEqual(chosen["klasse"], "ontwikkellocatie")
        self.assertEqual(ids(chosen["main"]), ["l1", "l2"])
        self.assertEqual(chosen["removed"], [])

    def test_new_shows_only_new_development_locations_in_rank_order(self):
        chosen, = logic(["select", self.items, state(view="nieuw"), context({"l2": True, "o1": True, "l1": True})])
        self.assertEqual(ids(chosen["main"]), ["l1", "l2"])
        chosen, = logic(["select", self.items, state(view="nieuw"), context({"l2": True})])
        self.assertEqual(ids(chosen["main"]), ["l2"])

    def test_new_also_lists_new_unsure_notices_below(self):
        chosen, plain = logic(["select", self.items, state(view="nieuw"), context({"o1": True})],
                              ["select", self.items, state(), context({"o1": True})])
        self.assertEqual(chosen["main"], [])
        self.assertEqual(ids(chosen["alsoNew"]), ["o1"])
        self.assertEqual(plain["alsoNew"], [])
        lines = logic(["alsoNewLine", 0], ["alsoNewLine", 1], ["alsoNewLine", 4])
        self.assertEqual(lines, ["", "Ook 1 nieuw bericht onder Onzeker.", "Ook 4 nieuwe berichten onder Onzeker."])

    def test_unsure_is_a_list_of_its_own(self):
        chosen, = logic(["select", self.items, state(view="onzeker"), context()])
        self.assertEqual(ids(chosen["main"]), ["o1"])

    def test_filtered_out_only_with_the_switch_and_not_narrowed_to_new(self):
        chosen, = logic(["select", self.items, state(view="nieuw", toonWeg=True), context({"l2": True})])
        self.assertEqual(ids(chosen["main"]), ["l2"])
        self.assertEqual(sorted(ids(chosen["removed"])), ["w1", "w2"])

    def test_filters(self):
        items = [item("a", 90, type="plan", signalen=["sloop"], km=2.0), item("b", 80, fase="Verleend", km=12.0),
                 item("c", 70, titel="Bouw van 12 appartementen Bredaseweg", datum="2026-11-16")]
        results = logic(
            ["select", items, state(type="plan"), context()], ["select", items, state(signaal="sloop"), context()],
            ["select", items, state(fase="Verleend"), context()], ["select", items, state(maxKm=5), context()],
            ["select", items, state(zoek="bredaseweg APPARTEMENTEN"), context()], ["select", items, state(dagen=1), context()],
            ["select", items, state(dagen=7), context()], ["select", items, state(dagen=3), context()])
        self.assertEqual([ids(r["main"]) for r in results],
                         [["a"], ["a"], ["b"], ["a", "c"], ["c"], ["c"], ["a", "b", "c"], ["c"]])

    def test_filtered_out_follows_search_and_filters(self):
        chosen, = logic(["select", self.items, state(toonWeg=True, dagen=1), context()])
        self.assertEqual(ids(chosen["removed"]), ["w2"])
        chosen, = logic(["select", self.items, state(toonWeg=True, zoek="bestaat niet"), context()])
        self.assertEqual(chosen["removed"], [])

    def test_period_includes_the_first_day_of_the_window(self):
        items = [item("op de grens", datum="2026-11-09"), item("dag te oud", datum="2026-11-08")]
        chosen, = logic(["select", items, state(dagen=7), context()])
        self.assertEqual(ids(chosen["main"]), ["op de grens"])

    def test_counts_for_the_three_tiles(self):
        counts, = logic(["counts", self.items, {"l2": True, "o1": True, "w2": True}])
        self.assertEqual(counts, {"locaties": 2, "nieuw": 1, "onzeker": 1, "onzekerNieuw": 1, "weggefilterd": 2})


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class NieuwSindsVorigBezoek(unittest.TestCase):
    HOUR = 3600 * 1000
    NOW = 1_800_000_000_000

    def test_first_visit_marks_only_the_latest_publication_day(self):
        items = [item("oud", datum="2026-11-13"), item("vandaag", datum="2026-11-16")]
        result, = logic(["markNew", items, None, self.NOW])
        self.assertTrue(result["firstVisit"])
        self.assertEqual(result["nieuw"], {"vandaag": True})
        self.assertEqual(result["next"], {"oud": 0, "vandaag": self.NOW})

    def test_later_visit_marks_what_this_device_has_not_seen(self):
        items = [item("gezien"), item("gisteravond"), item("onbekend")]
        seen = {"gezien": self.NOW - 15 * self.HOUR, "gisteravond": self.NOW - 13 * self.HOUR}
        result, = logic(["markNew", items, seen, self.NOW])
        self.assertFalse(result["firstVisit"])
        self.assertEqual(result["nieuw"], {"gisteravond": True, "onbekend": True})
        self.assertEqual(result["next"]["gezien"], seen["gezien"])
        self.assertEqual(result["next"]["onbekend"], self.NOW)

    def test_new_lasts_fourteen_hours(self):
        hours, = logic(["NEW_HOURS"])
        self.assertEqual(hours, 14)
        items = [item("net binnen"), item("net voorbij")]
        seen = {"net binnen": self.NOW - 14 * self.HOUR + 1, "net voorbij": self.NOW - 14 * self.HOUR}
        result, = logic(["markNew", items, seen, self.NOW])
        self.assertEqual(result["nieuw"], {"net binnen": True})

    def test_morning_line(self):
        lines = logic(["briefing", 0, False], ["briefing", 1, False], ["briefing", 3, False], ["briefing", 2, True],
                      ["briefing", 0, True], ["greeting", 7], ["greeting", 12], ["greeting", 18])
        self.assertEqual(lines, [
            "Geen nieuwe ontwikkellocaties sinds je vorige bezoek.", "1 nieuwe ontwikkellocatie sinds je vorige bezoek.",
            "3 nieuwe ontwikkellocaties sinds je vorige bezoek.", "2 ontwikkellocaties op de laatste publicatiedag.",
            "Geen ontwikkellocaties op de laatste publicatiedag.", "Goedemorgen", "Goedemiddag", "Goedenavond"])


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Kaart(unittest.TestCase):
    """What one card shows. The sentence why comes from the data unchanged."""

    def model(self, entry, **ctx):
        base = {"centre": CENTRE, "nieuw": {}, "ranks": {entry["id"]: 4}, "today": "2026-11-16"}
        base.update(ctx)
        return logic(["cardModel", entry, base])[0]

    def test_sentence_rank_and_place(self):
        entry = item("a", 95, waarom="23 nieuwe woningen, met sloop.", plaats="dorpsstraat 47 te Goirle", lat=51.52, lon=5.06, km=4.6)
        model = self.model(entry, nieuw={"a": True})
        self.assertEqual(model["why"], "23 nieuwe woningen, met sloop.")
        self.assertEqual(model["rank"], 4)
        self.assertEqual(model["score"], 95)
        self.assertTrue(model["isNew"])
        self.assertEqual(model["place"], "Dorpsstraat 47 te Goirle")
        self.assertEqual(model["distance"], "4,6 km ZW")
        self.assertEqual(model["date"], "10-11-2026")
        self.assertEqual(model["kind"], "Vergunning")
        self.assertIsNone(model["locationNote"])

    def test_plan_shows_its_kind(self):
        self.assertEqual(self.model(item("a", type="plan", soort="Omgevingsplan"))["kind"], "Omgevingsplan")
        self.assertEqual(self.model(item("a", type="plan", soort=None))["kind"], "Plan")
        self.assertEqual(self.model(item("a", type="verkoop"))["kind"], "Verkoop overheid")

    def test_no_exact_location_is_not_shown_as_a_distance(self):
        entry = item("a", locatieSoort="gemeente", plaats=None, gemeente="Hilvarenbeek", lat=None, lon=None, km=2.3)
        model = self.model(entry)
        self.assertEqual(model["place"], "Gemeente Hilvarenbeek")
        self.assertEqual(model["distance"], "geen exacte locatie")
        self.assertEqual(model["locationNote"], "Geen exacte locatie; de afstand van 2,3 km geldt voor gemeente Hilvarenbeek.")
        self.assertNotIn("Kaart", [link["label"] for link in model["links"]])

    def test_approximate_location_is_marked(self):
        model = self.model(item("a", locatieSoort="benaderd", plaats="omgeving Bellinistraat, Tilburg", lat=51.584865, lon=5.075331, km=3.3))
        self.assertEqual(model["distance"], "± 3,3 km N")
        self.assertEqual(model["locationNote"], "Locatie bij benadering, afgeleid uit de titel.")

    def test_deadline_only_while_it_is_open(self):
        self.assertEqual(self.model(item("a", reactieTot="2026-11-16"))["deadline"], "Reageren tot 16-11-2026")
        self.assertIsNone(self.model(item("a", reactieTot="2026-11-15"))["deadline"])
        self.assertIsNone(self.model(item("a"))["deadline"])

    def test_links_only_to_https(self):
        model = self.model(item("a", url="javascript:alert(1)", urlTekst="http://example.org/x"))
        self.assertEqual([link["label"] for link in model["links"]], ["Kaart"])
        model = self.model(item("a", urlTekst="https://repository.overheid.nl/a.html"))
        self.assertEqual([link["label"] for link in model["links"]], ["Open bij de bron", "Alleen tekst", "Kaart"])
        self.assertTrue(all(link["url"].startswith("https://") for link in model["links"]))

    def test_unsure_and_filtered_out_have_no_score(self):
        self.assertIsNone(self.model(item("a", klasse="onzeker"))["score"])
        model = self.model(item("a", klasse="weggefilterd", score=0), ranks={})
        self.assertIsNone(model["rank"])
        self.assertIsNone(model["score"])

    def test_belgian_source_is_named_without_the_authority(self):
        model = self.model(item("a", bron="omgevingsloket-vlaanderen", publicatie="Omgevingsloket Vlaanderen", overheid="Baarle-Hertog"))
        self.assertEqual(model["source"], "Bron: Omgevingsloket Vlaanderen")
        self.assertEqual(self.model(item("a"))["source"], "Bron: Gemeenteblad Tilburg")


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Verversen(unittest.TestCase):
    """When it is time to fetch the data again (site/logic.js, stale)."""

    def test_fifteen_minutes_is_the_limit(self):
        start = 1_800_000_000_000
        minute = 60_000
        self.assertEqual(logic(["stale", start, start, 15], ["stale", start, start + 14 * minute + 59_999, 15],
                               ["stale", start, start + 15 * minute, 15], ["stale", start, start + 600 * minute, 15]),
                         [False, False, True, True])


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class KaartjeTeksten(unittest.TestCase):
    """Where the texts on the small map go (site/logic.js, radarLabels): no name over another name,
    no ring label behind a dot or over a name. Units: km from the centre, x east, y south."""

    RINGS = [5, 10, 15]

    @staticmethod
    def box(label, char, up=0.9, down=0.3):
        width = len(label.get("naam") or label["tekst"]) * char
        return (label["x"] - width / 2, label["y"] - up, label["x"] + width / 2, label["y"] + down)

    @staticmethod
    def hit(a, b):
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

    def place(self, towns, dots=()):
        return logic(["radarLabels", towns, self.RINGS, list(dots)])[0]

    def test_names_that_do_not_touch_stay_centred_above_their_place(self):
        towns = [{"naam": "Tilburg", "x": -3.4, "y": -1.8}, {"naam": "Drunen", "x": 4.0, "y": -12.0}]
        placed = self.place(towns)
        self.assertEqual([(t["naam"], round(t["x"], 2), round(t["y"], 2), t["krap"]) for t in placed["towns"]],
                         [("Tilburg", -3.4, -1.8, False), ("Drunen", 4.0, -12.0, False)])

    def test_goirle_slides_beside_hilvarenbeek_and_stays_at_its_height(self):
        # The places as the app has them on 18-11-2026: both names centred would run through each other.
        towns = [{"naam": "Hilvarenbeek", "x": 0.8, "y": 5.5}, {"naam": "Goirle", "x": -2.5, "y": 5.8}]
        placed = self.place(towns)["towns"]
        first, second = placed
        self.assertEqual((round(first["x"], 6), round(first["y"], 6), first["krap"]), (0.8, 5.5, False), "de eerste naam blijft staan")
        self.assertEqual((round(second["y"], 6), second["krap"]), (5.8, False), "Goirle blijft op zijn eigen hoogte")
        self.assertLess(second["x"], -2.5, "Goirle schuift naar het westen, weg van Hilvarenbeek")
        self.assertGreater(second["x"], -2.5 - 3.5, "niet verder dan nodig")
        self.assertFalse(self.hit(self.box(first, 0.62), self.box(second, 0.62)))

    def test_a_name_that_cannot_slide_goes_below_or_above(self):
        # Two long names at the same place: sliding aside would carry the second too far from its place.
        towns = [{"naam": "Loon op Zand", "x": 0.0, "y": -8.0}, {"naam": "Kaatsheuvel", "x": 0.2, "y": -8.1}]
        placed = self.place(towns)["towns"]
        self.assertFalse(placed[1]["krap"])
        self.assertAlmostEqual(placed[1]["x"], 0.2)
        self.assertNotAlmostEqual(placed[1]["y"], -8.1)
        self.assertFalse(self.hit(self.box(placed[0], 0.62), self.box(placed[1], 0.62)))

    def test_a_ring_label_starts_in_the_north_just_inside_its_ring(self):
        rings = self.place([])["rings"]
        self.assertEqual([(r["km"], r["tekst"], r["krap"]) for r in rings], [(5, "5 km", False), (10, "10 km", False), (15, "15 km", False)])
        for ring in rings:
            with self.subTest(km=ring["km"]):
                self.assertAlmostEqual(ring["x"], 0)
                self.assertLess(ring["km"] - 1.6, -ring["y"])
                self.assertLess(-ring["y"] + 0.9, ring["km"], "de tekst raakt de lijn van zijn ring")

    def test_a_ring_label_moves_away_from_a_dot(self):
        free = {ring["km"]: ring for ring in self.place([])["rings"]}
        dots = [{"x": 0.3, "y": free[15]["y"] - 0.3, "r": 0.42}]  # a location right where "15 km" would stand
        placed = {ring["km"]: ring for ring in self.place([], dots)["rings"]}
        self.assertEqual((placed[5], placed[10]), (free[5], free[10]), "de andere ringen blijven staan")
        moved = placed[15]
        self.assertFalse(moved["krap"])
        self.assertNotAlmostEqual(moved["x"], 0)
        dot = (dots[0]["x"] - 0.42, dots[0]["y"] - 0.42, dots[0]["x"] + 0.42, dots[0]["y"] + 0.42)
        self.assertFalse(self.hit(self.box(moved, 0.63), dot))
        self.assertLess(math.hypot(moved["x"], moved["y"] - 0.3), 15, "het label blijft binnen zijn ring")

    def test_a_ring_label_moves_away_from_a_name(self):
        towns = [{"naam": "Loon op Zand", "x": 0.5, "y": -8.6}]  # where "10 km" would stand
        placed = self.place(towns)
        ring = next(r for r in placed["rings"] if r["km"] == 10)
        self.assertFalse(ring["krap"])
        self.assertFalse(self.hit(self.box(ring, 0.63), self.box(placed["towns"][0], 0.62)))

    def test_when_a_ring_is_full_of_dots_the_label_is_marked_and_stands_where_fewest_are(self):
        dots = []
        for degrees in range(0, 360, 3):  # a closed row of locations just inside the 5 km ring
            angle = math.radians(degrees)
            for radius in (3.2, 3.8, 4.4):
                dots.append({"x": radius * math.sin(angle), "y": -radius * math.cos(angle), "r": 0.42})
        placed = {ring["km"]: ring for ring in self.place([], dots)["rings"]}
        self.assertTrue(placed[5]["krap"])
        self.assertFalse(placed[10]["krap"])
        self.assertFalse(placed[15]["krap"])

    def test_every_text_stays_on_the_map(self):
        towns = [{"naam": "Reusel-De Mierden", "x": -13.0, "y": 0.0}, {"naam": "Hilvarenbeek", "x": 12.5, "y": 4.0}]
        placed = self.place(towns)
        for label in placed["towns"]:
            left, top, right, bottom = self.box(label, 0.62)
            self.assertTrue(-18.5 <= left and right <= 18.5 and -18.5 <= top and bottom <= 18.5, label)


class EchteGegevens(unittest.TestCase):
    """The same checks on site/data/berichten.json as it is in the repository."""

    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(read("data", "berichten.json"))
        cls.items = cls.data["berichten"]
        cls.ranks, cls.chosen, cls.unsure = logic(
            ["rankMap", cls.items], ["select", cls.items, state(), context()], ["select", cls.items, state(view="onzeker"), context()])

    def test_ranking_runs_from_the_highest_score_down_without_gaps(self):
        main = self.chosen["main"]
        self.assertTrue(main, "geen ontwikkellocaties in de gegevens")
        self.assertEqual({entry["klasse"] for entry in main}, {"ontwikkellocatie"})
        self.assertEqual([self.ranks[entry["id"]] for entry in main], list(range(1, len(main) + 1)))
        scores = [entry["score"] for entry in main]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(main[0]["score"], max(entry["score"] for entry in self.items if entry["klasse"] == "ontwikkellocatie"))

    def test_every_notice_in_a_list_has_a_rank_and_one_sentence_why(self):
        shown = self.chosen["main"] + self.unsure["main"]
        centre = self.data["centrum"]
        models = logic(*[["cardModel", entry, {"centre": centre, "nieuw": {}, "ranks": self.ranks, "today": "2026-11-16"}] for entry in shown])
        for entry, model in zip(shown, models):
            with self.subTest(id=entry["id"]):
                self.assertEqual(model["why"], entry["waarom"])
                self.assertRegex(model["why"], r"^\S.*\.$")
                self.assertNotRegex(model["why"][:-1], r"[.!?] ", "meer dan één zin")
                self.assertGreaterEqual(model["rank"], 1)
                self.assertTrue(model["place"])
                self.assertTrue(model["links"])


def colour_tokens():
    """The colours in styles.css: (light, dark by system setting, dark when forced)."""
    blocks = re.findall(r"(:root[^{]*)\{([^}]*)\}", read("styles.css"))
    def tokens(body):
        return dict(re.findall(r"(--[\w-]+):\s*(#[0-9a-fA-F]{6})\b", body))
    return (tokens(next(body for selector, body in blocks if selector.strip() == ":root")),
            tokens(next(body for selector, body in blocks if 'not([data-theme="light"])' in selector and "--bg" in body)),
            tokens(next(body for selector, body in blocks if selector.strip() == ':root[data-theme="dark"]' and "--bg" in body)))


class Huisstijl(unittest.TestCase):
    """The colours of the house style: the same set in light and dark, and readable."""

    TEXT_PAIRS = [("--ink", "--bg"), ("--ink", "--surface"), ("--muted", "--bg"), ("--muted", "--surface"), ("--muted", "--chip-bg"),
                  ("--link", "--surface"), ("--bar-ink", "--bar-bg"), ("--bar-signal", "--bar-bg"), ("--rank-ink", "--rank-bg"),
                  ("--signal-ink", "--surface"), ("--signal-ink", "--bg"), ("--on-signal-fill", "--signal-fill"),
                  ("--warn-ink", "--warn-bg")]

    @classmethod
    def setUpClass(cls):
        cls.light, cls.dark_media, cls.dark_forced = colour_tokens()

    @staticmethod
    def contrast(first, second):
        def luminance(colour):
            channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        high, low = sorted([luminance(first), luminance(second)], reverse=True)
        return (high + 0.05) / (low + 0.05)

    def test_dark_theme_defines_every_colour_of_the_light_theme(self):
        self.assertEqual(set(self.dark_media), set(self.light))
        self.assertEqual(self.dark_media, self.dark_forced, "de twee donkere blokken lopen uiteen")

    def test_text_is_readable_in_both_themes(self):
        for name, theme in (("licht", self.light), ("donker", self.dark_media)):
            for text, ground in self.TEXT_PAIRS:
                with self.subTest(thema=name, tekst=text, achtergrond=ground):
                    self.assertGreaterEqual(self.contrast(theme[text], theme[ground]), 4.5)

    def test_theme_colour_of_the_browser_is_the_bar_colour(self):
        manifest = json.loads(read("manifest.webmanifest"))
        meta = re.search(r'<meta name="theme-color" content="([^"]+)"', read("index.html")).group(1)
        self.assertEqual(meta, self.light["--bar-bg"])
        self.assertEqual(manifest["theme_color"], self.light["--bar-bg"])
        self.assertEqual(manifest["background_color"], self.light["--bg"])


class Beeldmerk(unittest.TestCase):
    """The mark, the icons and the illustration are plain drawings without anything attached."""

    DRAWINGS = [("icons", "icon.svg"), ("icons", "beeldmerk.svg"), ("img", "ochtend.svg"), ("img", "ochtend-donker.svg")]

    def test_drawings_are_plain_paths(self):
        for parts in self.DRAWINGS:
            with self.subTest(bestand="/".join(parts)):
                text = read(*parts)
                root = ET.fromstring(text)
                tags = {element.tag.split("}")[1] for element in root.iter()}
                self.assertLessEqual(tags, {"svg", "g", "path", "rect"})
                self.assertNotRegex(text, r"(?i)<script|<metadata|href=|\bon\w+=|url\(")
                self.assertLess(len(text.encode("utf-8")), 40_000)

    def test_mark_uses_the_house_colours(self):
        light = colour_tokens()[0]
        fills = set(re.findall(r'fill="(#[0-9a-f]{6})"', read("icons", "beeldmerk.svg")))
        self.assertEqual(fills, {light["--bar-bg"], light["--signal"]})
        # The app icon is the masthead in small: paper mark and the bar's orange on the bar colour.
        icon = set(re.findall(r'fill="(#[0-9a-f]{6})"', read("icons", "icon.svg")))
        self.assertEqual(icon, {light["--bar-bg"], light["--bg"], light["--bar-signal"]})
        self.assertIn(".mark-signal { fill: var(--bar-signal); }", read("styles.css"))

    def test_mark_in_the_masthead_is_the_same_drawing(self):
        def shapes(text):
            return re.findall(r'\sd="([^"]+)"', text)
        masthead = re.search(r'<svg class="mark".*?</svg>', read("index.html"), flags=re.S).group(0)
        self.assertEqual(shapes(masthead), shapes(read("icons", "beeldmerk.svg")))
        self.assertEqual(shapes(masthead), shapes(read("icons", "icon.svg")))

    def test_png_icons_have_the_size_the_manifest_states(self):
        manifest = json.loads(read("manifest.webmanifest"))
        for icon in manifest["icons"]:
            path = os.path.join(SITE, icon["src"])
            with self.subTest(icon=icon["src"]):
                self.assertTrue(os.path.isfile(path))
                if icon["type"] == "image/png":
                    with open(path, "rb") as handle:
                        head = handle.read(24)
                    self.assertEqual(head[:8], b"\x89PNG\r\n\x1a\n")
                    self.assertEqual("%dx%d" % struct.unpack(">II", head[16:24]), icon["sizes"])


class Pagina(unittest.TestCase):
    """The page, the scripts and the service worker refer to things that exist."""

    def setUp(self):
        self.html = read("index.html")
        self.app = read("app.js")

    def local_references(self):
        found = re.findall(r'(?:href|src)="([^"#]+)"', self.html)
        return [ref for ref in found if not ref.startswith("https://")]

    def test_files_the_page_refers_to_exist(self):
        for ref in self.local_references():
            with self.subTest(ref=ref):
                self.assertTrue(os.path.isfile(os.path.join(SITE, ref)))

    def test_every_element_the_app_looks_up_is_on_the_page(self):
        on_page = set(re.findall(r'\sid="([^"]+)"', self.html))
        wanted = set(re.findall(r'\$\("([\w-]+)"\)', self.app))
        for prefix, names in (("view-", ["berichten", "gebied", "bronnen", "adres"]), ("tab-", ["berichten", "gebied", "bronnen", "adres"]),
                              ("tile-", ["ranglijst", "nieuw", "onzeker"])):
            wanted |= {prefix + name for name in names}
        self.assertGreater(len(wanted), 25)
        self.assertEqual(wanted - on_page, set())

    def test_logic_is_loaded_before_the_app(self):
        scripts = re.findall(r'<script src="([^"]+)"', self.html)
        # The tab "Adres" (adres.js, adres-app.js) comes after the app it is added to.
        self.assertEqual(scripts, ["logic.js", "app.js", "adres.js", "adres-app.js"])

    def test_app_builds_text_not_markup(self):
        self.assertNotRegex(self.app, r"innerHTML|insertAdjacentHTML|document\.write")

    def test_service_worker_keeps_everything_the_app_needs_offline(self):
        worker = read("sw.js")
        shell = set(re.findall(r'"([^"]+)"', re.search(r"var SHELL = \[(.*?)\];", worker, flags=re.S).group(1)))
        for ref in shell - {"./"}:
            with self.subTest(ref=ref):
                self.assertTrue(os.path.isfile(os.path.join(SITE, ref)))
        needed = {ref for ref in self.local_references() if not ref.startswith("icons/")}
        needed |= {"img/" + name for name in re.findall(r'"([\w-]+\.svg)"', self.app)}
        self.assertGreaterEqual(len(needed), 6)
        self.assertEqual(needed - shell, set())

    RULES = [
        "Hoogste rang: een wijziging van een omgevingsplan of bestemmingsplan die ontwikkeling mogelijk maakt, bijvoorbeeld naar wonen of met meer bouwhoogte.",
        "Daarna: twee of meer nieuwe woningen. Hoe meer woningen, hoe hoger.",
        "Daarna: een perceel van minstens 400 m² met een ontwikkelsignaal: sloop, functiewijziging, kavelsplitsing, bestemmingswijziging of een leegstaand of vrijkomend bedrijfspand.",
        "Ook: een overheid die grond of vastgoed van minstens 400 m² wil verkopen, en een failliet bedrijf met een bedrijfspand op zo'n perceel.",
        "Onzeker: er is een signaal, maar het aantal woningen of de perceelgrootte is niet te bepalen. Deze berichten worden niet verborgen.",
        "Weggefilterd: al het andere, zoals dakkapellen, kappen, reclame en één losse woning. Met de schakelaar op het tabblad Berichten kun je ze bekijken; bij elk bericht staat de reden.",
        "Ingetrokken en geweigerde aanvragen blijven zichtbaar, maar zakken in de rangorde.",
    ]

    def test_rules_on_the_sources_tab_are_word_for_word_those_of_version_1(self):
        block = re.search(r'fill\("regels", \[(.*?)\]\);', self.app, flags=re.S).group(1)
        lines = [json.loads(line.replace('" + limit + "', "400")) for line in re.findall(r'^\s*("(?:[^"\\]|\\.|" \+ limit \+ ")*"),$', block, flags=re.M)]
        self.assertEqual(lines, self.RULES)

    def test_switch_for_filtered_out_is_on_the_tab_itself_not_inside_the_filter_panel(self):
        panel = re.search(r'<form id="filters".*?</form>', self.html, flags=re.S).group(0)
        self.assertNotIn('id="toon-weg"', panel)
        section = re.search(r'<section id="view-berichten".*?</section>', self.html, flags=re.S).group(0)
        self.assertIn('id="toon-weg"', section)

    def test_one_minute_view_has_no_more_than_three_lists(self):
        tiles = re.findall(r'class="tile[^"]*" id="tile-(\w+)" data-view="(\w+)"', self.html)
        self.assertEqual(tiles, [("ranglijst", "ranglijst"), ("nieuw", "nieuw"), ("onzeker", "onzeker")])
        self.assertIn('<option value="relevantie">Hoogste rang eerst</option>', self.html)


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def playwright_available():
    if not NODE:
        return False
    return subprocess.run([NODE, "-e", "require('playwright')"], capture_output=True).returncode == 0


@unittest.skipUnless(playwright_available(), "Playwright is niet geïnstalleerd")
class InDeBrowser(unittest.TestCase):
    """The app in a real browser at phone size, with the data the page itself loads. By default the
    site/ folder of this checkout; with TILBURG_SITE_URL set, the site at that address, for example
    TILBURG_SITE_URL=https://wim1201.github.io/tilburg-signalen python -m unittest tests.test_site.InDeBrowser"""

    @classmethod
    def setUpClass(cls):
        cls.url = (os.environ.get("TILBURG_SITE_URL") or "").rstrip("/")
        server = None
        if not cls.url:
            server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Quiet, directory=SITE))
            threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            done = subprocess.run([NODE, os.path.join(JS, "browser_smoke.js"), cls.url or "http://127.0.0.1:%d" % server.server_address[1]],
                                  capture_output=True, text=True, encoding="utf-8", timeout=300)
        finally:
            if server:
                server.shutdown()
                server.server_close()
        if done.returncode:
            raise AssertionError(done.stderr)
        cls.seen = json.loads(done.stdout)
        # The app opens with the core: every expectation below is about the notices within the radius.
        cls.items = [entry for entry in cls.seen["data"]["berichten"] if entry.get("regio", "kern") == "kern"]
        cls.locations = sorted([entry for entry in cls.items if entry["klasse"] == "ontwikkellocatie"], key=lambda entry: -entry["score"])

    def test_no_errors_and_nothing_wider_than_the_phone(self):
        self.assertEqual(self.seen["errors"], [])
        self.assertLessEqual(self.seen["overflow"], 0)
        self.assertLessEqual(self.seen["narrowOverflow"], 0)
        self.assertEqual(self.seen["mark"], 2)

    def test_on_the_narrowest_phone_no_date_breaks_and_no_label_covers_the_details_button(self):
        self.assertEqual(self.seen["brokenDates"], 0)
        self.assertEqual(self.seen["chipsOverToggle"], 0)

    def test_first_visit_counts_the_latest_publication_day_as_new(self):
        latest = max(entry["datum"] for entry in self.items)
        new = [entry for entry in self.locations if entry["datum"] == latest]
        self.assertEqual(self.seen["tiles"]["nieuw"], str(len(new)))
        self.assertEqual(self.seen["newCards"], len(new))
        expected = {0: "Geen ontwikkellocaties", 1: "1 ontwikkellocatie"}.get(len(new), "%d ontwikkellocaties" % len(new))
        self.assertEqual(self.seen["brief"], expected + " op de laatste publicatiedag.")

    def test_tiles_keep_their_label_on_one_line_and_the_same_height(self):
        # threeDigitTileShapes: the narrowest phone with a count of three digits and a badge of "+12".
        self.assertLessEqual(self.seen["threeDigitOverflow"], 0)
        for name in ("tileShapes", "narrowTileShapes", "threeDigitTileShapes"):
            shapes = self.seen[name]
            with self.subTest(breedte=name):
                self.assertEqual([shape["label"] for shape in shapes], ["Ranglijst", "Nieuw", "Onzeker"])
                self.assertEqual([shape["lines"] for shape in shapes], [1, 1, 1])
                self.assertEqual(len({shape["height"] for shape in shapes}), 1)
                self.assertFalse(any(shape["badgeOverNumber"] for shape in shapes), "het bolletje staat over het getal")

    def test_new_unsure_notices_show_as_a_count_on_the_tile(self):
        latest = max(entry["datum"] for entry in self.items)
        new = len([entry for entry in self.items if entry["klasse"] == "onzeker" and entry["datum"] == latest])
        self.assertEqual(self.seen["badgeFirst"], "+%d nieuw" % new if new else None)
        if self.seen["hasUnsure"]:
            self.assertEqual(self.seen["badgeLater"], "+1 nieuw")
        self.assertIsNone(self.seen["badgeNone"])

    def test_count_line_does_not_leave_one_word_on_its_own_line(self):
        count = self.seen["countLines"]
        if count["lines"] > 1:
            self.assertGreater(count["lastShare"], 0.25, count["text"])

    def test_details_stay_open_and_are_large_enough_to_tap(self):
        self.assertEqual(self.seen["openAfterShowAll"], 1)
        self.assertGreaterEqual(self.seen["toggleHeight"], 40)
        self.assertGreaterEqual(self.seen["linkHeight"], 40)

    def test_name_in_the_masthead_goes_back_to_the_ranking(self):
        self.assertEqual(self.seen["afterBrand"], "tile-ranglijst")

    def test_order_by_date_shows_day_headings_that_count_what_is_shown(self):
        heads = self.seen["dayHeads"]
        self.assertTrue(heads)
        shown = 0
        for head in heads:
            count = re.search(r"(\d+)( van \d+)?$", head)
            self.assertIsNotNone(count, head)
            shown += int(count.group(1))
        self.assertEqual(shown, self.seen["dayCards"])

    def test_tapping_a_municipality_shows_its_notices(self):
        name = self.seen["gemeente"]
        own = [entry for entry in self.locations if entry["gemeente"] == name]
        self.assertEqual(self.seen["gemeenteHash"], "#berichten")
        self.assertEqual(self.seen["gemeenteFilter"], name)
        self.assertEqual(len(self.seen["gemeenteRanks"]), len(own))
        self.assertEqual(self.seen["gemeenteRanks"], sorted(self.seen["gemeenteRanks"], key=int))

    def test_rules_are_shown_as_in_version_1(self):
        limit = str(self.seen["data"]["drempelPerceelM2"])
        self.assertEqual(self.seen["rules"], [rule.replace("400", limit) for rule in Pagina.RULES])

    def test_house_style_is_the_one_in_this_checkout(self):
        light = colour_tokens()[0]
        bar = tuple(int(light["--bar-bg"][i:i + 2], 16) for i in (1, 3, 5))
        self.assertEqual(self.seen["themeColor"], light["--bar-bg"])
        self.assertEqual(self.seen["barColor"], "rgb(%d, %d, %d)" % bar)

    def test_top_of_the_app_shows_the_moment_of_the_last_refresh(self):
        import datetime
        import zoneinfo
        stamp = datetime.datetime.fromisoformat(self.seen["data"]["bijgewerkt"]).astimezone(zoneinfo.ZoneInfo("Europe/Amsterdam"))
        shown = self.seen["updated"]
        self.assertTrue(shown.startswith("Bijgewerkt "), shown)
        self.assertIn(" %d " % stamp.day, shown)
        self.assertTrue(shown.endswith(stamp.strftime("%H:%M")), shown)

    def test_a_skipped_refresh_shows_as_an_old_time_and_a_warning(self):
        self.assertIn(" %d " % self.seen["staleDay"], self.seen["updatedStale"])
        stale = [line for line in self.seen["notices"] if "niet ververst" in line]
        self.assertEqual(len(stale), 1)
        self.assertTrue(stale[0].startswith("De gegevens zijn sinds "), stale[0])

    def test_gaps_in_the_data_are_reported(self):
        notices = " ".join(self.seen["notices"])
        self.assertEqual(len(self.seen["notices"]), 5)
        for part in ("zijn onvolledig: de bron gaf 4 van de gebruikelijke circa 2.097", "was bij de laatste verversing niet bereikbaar",
                     "konden 3 bekendmakingen niet volledig worden gelezen", "konden 3 rechtbankpublicaties"):
            self.assertIn(part, notices)
        self.assertTrue(self.seen["gapHead"].endswith("· onvolledig"), self.seen["gapHead"])

    def test_first_screen_is_the_top_ten_with_the_highest_rank_on_top(self):
        first = self.seen["first"]
        self.assertEqual([card["rank"] for card in first], [str(n) for n in range(1, min(10, len(self.locations)) + 1)])
        top_score = self.locations[0]["score"]
        self.assertIn(first[0]["why"], [entry["waarom"] for entry in self.locations if entry["score"] == top_score])
        self.assertTrue(all(card["firstText"] == "why" for card in first), "de zin waarom staat niet bovenaan de kaart")
        self.assertTrue(all(link.startswith("https://") for card in first for link in card["links"]))
        if len(self.locations) > 10:
            self.assertEqual(self.seen["count"], "Top 10 van %d ontwikkellocaties, hoogste rang eerst" % len(self.locations))

    def test_show_all_gives_the_whole_ranking_in_order(self):
        self.assertEqual(self.seen["all"], [str(n) for n in range(1, len(self.locations) + 1)])

    def test_tiles_count_the_data(self):
        unsure = [entry for entry in self.items if entry["klasse"] == "onzeker"]
        self.assertEqual(self.seen["tiles"]["ranglijst"], str(len(self.locations)))
        self.assertEqual(self.seen["tiles"]["onzeker"], str(len(unsure)))
        self.assertEqual(self.seen["onzeker"], min(10, len(unsure)))

    def test_filtered_out_is_behind_the_switch_and_has_no_rank(self):
        removed = [entry for entry in self.items if entry["klasse"] == "weggefilterd"]
        self.assertTrue(self.seen["switchVisible"], "de schakelaar is niet zichtbaar zonder het filterpaneel te openen")
        self.assertEqual(self.seen["removed"], min(60, len(removed)))
        self.assertEqual(self.seen["removedRank"], "–")
        self.assertEqual(self.seen["removedWhileSearching"], 0)
        self.assertTrue(self.seen["switchAfterReset"], "Filters wissen zet de schakelaar uit")

    def test_a_new_unsure_notice_is_announced_and_listed_under_new(self):
        if not self.seen["hasUnsure"]:
            self.skipTest("geen onzekere berichten in de gegevens")
        self.assertEqual(self.seen["briefLater"], "Geen nieuwe ontwikkellocaties sinds je vorige bezoek.")
        self.assertTrue(self.seen["briefSubLater"].startswith("Ook 1 nieuw bericht onder Onzeker."))
        self.assertEqual([(card["klasse"], card["isNew"]) for card in self.seen["newUnsure"]], [("onzeker", True)])
        self.assertEqual(self.seen["newUnsureHead"], ["Nieuw onder Onzeker1"])

    def test_nothing_new_shows_the_illustration(self):
        self.assertEqual(self.seen["emptyTitle"], "Niets nieuws sinds je vorige bezoek.")
        self.assertEqual(self.seen["emptyArt"], 1)

    # --- The region choice on the tab "Gebied" (tests/js/regio_smoke.js), on the narrowest phone. The
    # expectations are worked out from the data the page loaded, so they hold for any data.

    def region(self):
        seen = self.seen["regio"]
        if not seen["start"]["buttons"]:
            self.skipTest("de gegevens zijn van vóór de regio's: er is niets te kiezen")
        return seen

    # The walk through the region choice is done twice: with the regions as the site delivers them,
    # and in a fixed situation (tests/js/regio_ongelezen.json) in which regions have notices whose
    # text still waits. The site in the repository has none of those and the live site often has;
    # run 26 failed on exactly that difference, after publishing. Every check of the walk runs in both.
    SITUATIES = (("regio", "de regio's zoals de site ze levert"), ("regioOngelezen", "vaste situatie met ongelezen regioberichten"))

    def in_both(self, check):
        for key, label in self.SITUATIES:
            with self.subTest(situatie=label):
                seen = self.seen[key]
                if not seen["start"]["buttons"]:
                    self.skipTest("de gegevens zijn van vóór de regio's: er is niets te kiezen")
                check(seen)

    def fixed(self):
        with open(os.path.join(JS, "regio_ongelezen.json"), encoding="utf-8") as handle:
            return json.load(handle), self.seen["regioOngelezen"]

    @staticmethod
    def shown(data, chosen):
        return [entry for entry in data["berichten"] if entry["regio"] == "kern" or entry["regio"] in chosen]

    def expected(self, data, chosen):
        """What the tab Berichten shows for a choice of regions, as the texts on the page."""
        shown = self.shown(data, chosen)
        locations = sum(1 for entry in shown if entry["klasse"] == "ontwikkellocatie")
        reach = max([data["straalKm"]] + [-(-entry["afstandKm"] // 1) for entry in shown if entry["afstandKm"] > data["straalKm"]])
        return {"ranglijst": str(locations), "onzeker": str(sum(1 for entry in shown if entry["klasse"] == "onzeker")),
                "removed": "(%d)" % sum(1 for entry in shown if entry["klasse"] == "weggefilterd"),
                "count": ("Top 10 van %d ontwikkellocaties" % locations if locations > 10 else "%d ontwikkellocatie%s" % (locations, "" if locations == 1 else "s"))
                + ", hoogste rang eerst", "kmMax": str(int(reach)), "locations": locations}

    def assert_berichten(self, page, data, chosen):
        want = self.expected(data, chosen)
        self.assertEqual((page["tiles"][0], page["tiles"][2], page["removed"], page["count"], page["kmMax"]),
                         (want["ranglijst"], want["onzeker"], want["removed"], want["count"], want["kmMax"]))
        self.assertEqual(page["kmOut"], want["kmMax"] + " km")

    def test_region_choice_is_offered_but_nothing_is_chosen_at_the_start(self):
        self.in_both(self.check_region_choice_is_offered_but_nothing_is_chosen_at_the_start)

    def check_region_choice_is_offered_but_nothing_is_chosen_at_the_start(self, seen):
        data, start = seen["data"], seen["start"]
        self.assertEqual([button["name"] for button in start["buttons"]], data["regios"])
        self.assertEqual(data["inFiles"], [regio["berichten"] for regio in data["overview"]], "het overzicht klopt niet met de regiobestanden")
        self.assertEqual(seen["askedByThePage"], [], "de app leest een regiobestand zonder dat een regio is gekozen")
        self.assertEqual({button["pressed"] for button in start["buttons"]}, {"false"})
        # On the live site a region can have notices whose text still waits; the button then says so.
        # The snapshot in the repository has none, so there the line is the number of locations only.
        unread = {regio["naam"]: regio.get("ongelezen", 0) for regio in data["overview"]}
        for button in start["buttons"]:
            locations = sum(1 for entry in data["berichten"] if entry["regio"] == button["name"] and entry["klasse"] == "ontwikkellocatie")
            waiting = " · %d ongelezen" % unread[button["name"]] if unread[button["name"]] else ""
            self.assertEqual(button["sub"], "%d locatie%s" % (locations, "" if locations == 1 else "s") + waiting)
        core = [g for g in data["gemeenten"] if g["regio"] == "kern"]
        self.assertEqual([row["name"].replace(" (België)", "") for row in start["rows"]], [g["naam"] for g in core])
        self.assertIn("Daarin liggen %d gemeenten" % len(core), start["intro"])
        self.assertTrue(start["hint"].startswith("Kies een regio om die erbij te zien."), start["hint"])
        # The morning screen is the core, whatever else the data holds.
        self.assert_berichten(seen["morning"], data, [])
        self.assertIsNone(seen["morning"]["line"])
        self.assertEqual(seen["morning"]["brief"], self.seen["brief"])
        self.assertEqual(seen["morning"]["tiles"], [self.seen["tiles"][name] for name in ("ranglijst", "nieuw", "onzeker")])
        self.assertEqual(seen["errors"], [])

    def test_region_choice_fits_the_narrowest_phone(self):
        self.in_both(self.check_region_choice_fits_the_narrowest_phone)

    def check_region_choice_fits_the_narrowest_phone(self, seen):
        for moment in ("start", "one", "all", "backGebied"):
            with self.subTest(moment=moment):
                self.assertLessEqual(seen[moment]["overflow"], 0)
                self.assertTrue(all(button["height"] >= 44 and button["left"] >= 0 and button["right"] <= 320 for button in seen[moment]["buttons"]), seen[moment]["buttons"])
                self.assertTrue(all(row["right"] <= 320 for row in seen[moment]["rows"]))
        self.assertLessEqual(seen["withOneOverflow"], 0)
        self.assertLessEqual(seen["withOneAllOverflow"], 0)
        self.assertGreaterEqual(seen["lineButton"]["height"], 30)
        if seen["tapped"]:
            self.assertLessEqual(seen["tap"]["overflow"], 0)

    def test_a_chosen_region_is_shown_with_the_core(self):
        self.in_both(self.check_a_chosen_region_is_shown_with_the_core)

    def check_a_chosen_region_is_shown_with_the_core(self, seen):
        data, first, one = seen["data"], seen["first"], seen["one"]
        self.assertEqual({button["name"]: button["pressed"] for button in one["buttons"]},
                         {button["name"]: str(button["name"] == first).lower() for button in one["buttons"]})
        wanted = [g for g in data["gemeenten"] if g["regio"] in ("kern", first)]
        self.assertEqual([row["name"].replace(" (België)", "") for row in one["rows"]], [g["naam"] for g in wanted])
        by_name = {row["name"]: row for row in one["rows"]}
        for gemeente in wanted:
            row = by_name[gemeente["naam"] + (" (België)" if gemeente["land"] == "BE" else "")]
            with self.subTest(gemeente=gemeente["naam"]):
                if gemeente["regio"] == first:
                    self.assertEqual(row["chip"], first)
                    self.assertTrue(row["towns"].startswith("Hele gemeente, buiten de straal."), row["towns"])
                    if gemeente["opmerking"]:
                        self.assertIn(gemeente["opmerking"], row["towns"])
                elif gemeente["buitenStraal"] == first and gemeente["dekking"] != "geheel":
                    self.assertEqual(row["chip"], "Hele gemeente, met " + first)
                shown = [e for e in self.shown(data, [first]) if e["gemeente"] == row["name"]]
                self.assertEqual(row["counts"], "%d ontwikkellocaties, %d onzeker" % (sum(1 for e in shown if e["klasse"] == "ontwikkellocatie"),
                                                                                    sum(1 for e in shown if e["klasse"] == "onzeker")))
        self.assertTrue(one["hint"].startswith("Je ziet de kern met " + first + " erbij"), one["hint"])
        self.assertEqual(one["dots"], seen["start"]["dots"], "het kaartje van de kern verandert door een regio")
        file = next(regio["bestand"] for regio in data["overview"] if regio["naam"] == first)
        self.assertEqual(seen["askedForOne"], [file], "kiezen van één regio leest precies dat ene bestand")
        # On the tab Berichten: the core with the region, said in one line, and the morning line unchanged.
        self.assert_berichten(seen["withOne"], data, [first])
        self.assertEqual(seen["withOne"]["line"], "Met " + first + " erbij. Alleen de kern")
        self.assertEqual(seen["withOne"]["brief"], seen["morning"]["brief"])
        self.assertEqual(seen["withOne"]["tiles"][1], seen["morning"]["tiles"][1], "een regio telt mee als nieuw")
        want = self.expected(data, [first])
        self.assertEqual(seen["withOneAllRanks"], [str(n) for n in range(1, want["locations"] + 1)])

    def test_tapping_a_municipality_of_a_region_shows_its_notices(self):
        self.in_both(self.check_tapping_a_municipality_of_a_region_shows_its_notices)

    def check_tapping_a_municipality_of_a_region_shows_its_notices(self, seen):
        if not seen["tapped"]:
            self.skipTest("de gekozen regio heeft geen eigen gemeenten")
        data, name, tap = seen["data"], seen["tapped"], seen["tap"]
        own = [e for e in data["berichten"] if e["gemeente"] == name and e["klasse"] == "ontwikkellocatie" and e["regio"] in ("kern", seen["first"])]
        self.assertEqual(tap["hash"], "#berichten")
        self.assertEqual(tap["cards"], len(own))
        if own:
            self.assertEqual(tap["filter"], name)
            self.assertTrue(tap["count"].startswith("%d ontwikkellocatie" % len(own)), tap["count"])
            self.assertTrue(all(" km" in distance or distance == "geen exacte locatie" for distance in tap["distances"]))

    def test_back_to_the_core_and_every_region_at_once(self):
        self.in_both(self.check_back_to_the_core_and_every_region_at_once)

    def check_back_to_the_core_and_every_region_at_once(self, seen):
        data = seen["data"]
        self.assertEqual(seen["back"], seen["morning"])
        self.assertEqual({button["pressed"] for button in seen["backGebied"]["buttons"]}, {"false"})
        self.assertEqual(seen["backGebied"]["rows"], seen["start"]["rows"])
        names = [button["name"] for button in seen["start"]["buttons"]]
        self.assertEqual({button["pressed"] for button in seen["all"]["buttons"]}, {"true"})
        self.assertEqual(len(seen["all"]["rows"]), sum(1 for g in data["gemeenten"] if g["regio"] == "kern" or g["regio"] in names))
        self.assert_berichten(seen["withAll"], data, names)
        sentence = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " en " + names[-1]
        self.assertEqual(seen["withAll"]["line"], "Met " + sentence + " erbij. Alleen de kern")
        self.assertEqual(sorted(seen["askedForAll"]), sorted(regio["bestand"] for regio in data["overview"]), "een regiobestand is twee keer gelezen")

    def test_the_fixed_situation_is_what_the_page_was_given(self):
        fixture, seen = self.fixed()
        self.assertEqual(seen["data"]["overview"], fixture["regios"])
        self.assertEqual(seen["data"]["inFiles"], [len(fixture["bestanden"][regio["bestand"]]["berichten"]) for regio in fixture["regios"]])
        self.assertEqual(seen["data"]["core"], self.seen["regio"]["data"]["core"], "de kern is die van de site zelf")
        self.assertEqual(seen["morning"], self.seen["regio"]["morning"], "het ochtendscherm verandert door de regio's")
        self.assertEqual(seen["errors"], [])

    def test_a_region_with_waiting_notices_says_so_on_its_button(self):
        # Written out, not worked out: this is the line that the live check of run 26 stumbled on.
        _, seen = self.fixed()
        for moment in ("start", "one", "all", "backGebied", "reopenedGebied"):
            with self.subTest(moment=moment):
                self.assertEqual({button["name"]: button["sub"] for button in seen[moment]["buttons"]},
                                 {"Midden-Brabant": "2 locaties", "West-Brabant": "1 locatie · 4 ongelezen", "Zeeland": "3 locaties · 1 ongelezen"})

    def test_waiting_notices_stand_under_onzeker_with_their_reason(self):
        fixture, seen = self.fixed()
        waiting = {regio["naam"]: regio["ongelezen"] for regio in fixture["regios"]}
        unsure = {regio["naam"]: regio["onzeker"] for regio in fixture["regios"]}
        core = int(seen["morning"]["tiles"][2])
        reason = "Tekst nog niet gelezen; een volgende verversing haalt hem op."
        first = seen["first"]
        self.assertGreater(waiting[first], 0, "de regio die de test kiest, heeft in de vaste situatie wachtende berichten")
        for moment, chosen in (("unsureWithOne", [first]), ("unsureWithAll", list(waiting))):
            with self.subTest(moment=moment):
                shown = seen[moment]
                total = core + sum(unsure[name] for name in chosen)
                self.assertEqual(shown["count"], "%d onzekere berichten, hoogste rang eerst" % total)
                self.assertEqual(len(shown["reasons"]), total)
                self.assertEqual(shown["reasons"].count(reason), sum(waiting[name] for name in chosen))
                self.assertLessEqual(shown["overflow"], 0)
        # The tab says it per chosen region, in the singular for one notice.
        self.assertEqual([line for line in seen["unsureWithOne"]["notices"] if "gelezen" in line],
                         ['Van Zeeland is 1 bericht nog niet gelezen. Het staat onder Onzeker met "Tekst nog niet gelezen"; een volgende verversing haalt het op.'])
        self.assertEqual([line for line in seen["unsureWithAll"]["notices"] if "gelezen" in line],
                         ['Van West-Brabant zijn 4 berichten nog niet gelezen. Ze staan onder Onzeker met "Tekst nog niet gelezen"; de volgende verversingen halen ze op.',
                          'Van Zeeland is 1 bericht nog niet gelezen. Het staat onder Onzeker met "Tekst nog niet gelezen"; een volgende verversing haalt het op.'])

    def test_in_the_fixed_situation_tapping_a_municipality_shows_a_location(self):
        _, seen = self.fixed()
        self.assertEqual((seen["first"], seen["tapped"]), ("Zeeland", "Reimerswaal"))
        self.assertEqual((seen["tap"]["cards"], seen["tap"]["filter"]), (1, "Reimerswaal"))

    # --- Coming back to the app after a while (tests/js/verversen_smoke.js, 375 px). The page had a
    # region chosen, a search and a filter set, a card opened and an address looked up.

    KEPT = ("hash", "zoek", "type", "filtersOpen", "line", "pressed", "open", "adres", "adresVisible", "bag", "perceel", "scope")

    def kept(self, moment):
        return {key: self.seen["verversen"][moment]["state"][key] for key in self.KEPT}

    def test_back_in_view_within_fifteen_minutes_nothing_is_fetched(self):
        seen = self.seen["verversen"]
        self.assertEqual(seen["errors"], [])
        self.assertEqual(seen["early"], seen["before"])
        self.assertEqual(seen["atOnce"], seen["after"], "direct na een verversing wordt opnieuw opgehaald")

    def test_back_in_view_after_fifteen_minutes_the_data_and_the_moment_are_new(self):
        seen = self.seen["verversen"]
        before, after = seen["before"], seen["after"]
        self.assertNotEqual(after["state"]["updated"], before["state"]["updated"])
        self.assertTrue(after["state"]["updated"].startswith("Bijgewerkt ") and after["state"]["updated"].endswith("23:57"), after["state"]["updated"])
        # One fetch of each data file and of the file of the chosen region; no register is asked again.
        self.assertEqual((after["requests"]["berichten"], after["requests"]["gebied"]), (before["requests"]["berichten"] + 1, before["requests"]["gebied"] + 1))
        self.assertEqual(after["requests"]["regio"], before["requests"]["regio"] + ["regio-zeeland.json"])
        self.assertEqual(after["requests"]["pdok"], before["requests"]["pdok"])
        # The new run brought one location in the core and one in the region; the one in the core is new.
        tiles_before, tiles_after = [int(n) for n in before["state"]["tiles"]], [int(n) for n in after["state"]["tiles"]]
        self.assertEqual(tiles_after, [tiles_before[0] + 2, tiles_before[1] + 1, tiles_before[2]])

    def test_a_refresh_keeps_the_region_the_search_the_filter_and_the_opened_card(self):
        seen = self.seen["verversen"]
        before = self.kept("before")
        self.assertEqual((before["pressed"], before["line"], before["zoek"], before["type"], before["filtersOpen"], len(before["open"])),
                         (["Zeeland"], "Met Zeeland erbij. Alleen de kern", "Goes", "vergunning", True, 1))
        for moment in ("after", "sameRun", "noConnection", "connectionBack", "regionDown"):
            with self.subTest(moment=moment):
                self.assertEqual(self.kept(moment), before)
        # The search still narrows the list, and now finds the new notice of the region as well.
        self.assertEqual(seen["before"]["state"]["count"], "1 ontwikkellocatie, hoogste rang eerst")
        self.assertEqual(seen["after"]["state"]["count"], "2 ontwikkellocaties, hoogste rang eerst")
        self.assertEqual(seen["end"]["cards"], ["test-ververst-regio"] + seen["before"]["state"]["cards"])
        self.assertEqual(seen["end"]["open"], seen["before"]["state"]["open"], "de geopende kaart is dichtgegaan")

    def test_a_refresh_keeps_the_address_and_searches_the_new_notices_for_it(self):
        seen = self.seen["verversen"]
        before, after = seen["before"]["state"], seen["after"]["state"]
        self.assertEqual(before["hash"], "#adres")
        self.assertEqual(before["adres"], "Burgemeester van de Mortelplein 118a")
        self.assertTrue(before["adresVisible"])
        self.assertNotIn("test-ververst-adres", before["pubs"])
        self.assertEqual(after["pubs"], ["test-ververst-adres"] + before["pubs"])
        self.assertNotEqual(after["searched"], before["searched"], "het aantal doorzochte berichten is niet bijgewerkt")

    def test_the_same_run_again_changes_nothing(self):
        seen = self.seen["verversen"]
        self.assertEqual(seen["sameRun"]["state"], seen["after"]["state"])
        self.assertEqual(seen["sameRun"]["requests"]["berichten"], seen["after"]["requests"]["berichten"] + 1)
        self.assertEqual(seen["sameRun"]["requests"]["regio"], seen["after"]["requests"]["regio"], "zonder nieuwe run is een regiobestand opnieuw gelezen")

    def test_without_connection_everything_stays_and_the_next_time_tries_again(self):
        seen = self.seen["verversen"]
        self.assertEqual(seen["noConnection"]["state"], seen["sameRun"]["state"])
        self.assertFalse(seen["noConnection"]["state"]["loadError"])
        # No waiting of fifteen minutes after a failure: back in view, it fetches at once.
        self.assertEqual(seen["connectionBack"]["requests"]["berichten"], seen["noConnection"]["requests"]["berichten"] + 1)
        self.assertTrue(seen["connectionBack"]["state"]["updated"].endswith("23:58"), seen["connectionBack"]["state"]["updated"])

    def test_a_region_file_that_does_not_come_at_a_refresh_keeps_what_the_region_had(self):
        seen = self.seen["verversen"]
        down, back = seen["regionDown"]["state"], seen["connectionBack"]["state"]
        self.assertTrue(down["updated"].endswith("23:59"), down["updated"])
        self.assertEqual((down["pressed"], down["line"], down["count"], down["tiles"]), (back["pressed"], back["line"], back["count"], back["tiles"]))
        self.assertEqual(seen["regionDown"]["requests"]["regio"][-1], "regio-zeeland.json")

    def test_on_the_small_map_no_text_covers_another_and_no_ring_label_lies_behind_a_dot(self):
        for width, radar in sorted(self.seen["verversen"]["radar"].items()):
            with self.subTest(breedte=width):
                self.assertEqual(radar["overlaps"], [])
                self.assertEqual(radar["behind"], [])
                self.assertEqual(radar["outside"], [])
                self.assertEqual(radar["rings"], ["5 km", "10 km", "15 km"])
                self.assertIn("Goirle", radar["towns"])
                self.assertIn("Hilvarenbeek", radar["towns"])
                self.assertLessEqual(radar["overflow"], 0)
                self.assertGreater(radar["dots"], 0)
                if not self.url:
                    # With the data in the repository every text finds a free place. On the live site a
                    # text may be marked as cramped on a crowded day; it is then left out of the above.
                    self.assertEqual(radar["krap"], [])

    def test_a_region_file_that_does_not_come_leaves_the_core(self):
        seen = self.region()
        down = seen["fileDown"]
        self.assertEqual(down["message"], "De berichten van " + seen["first"] + " konden niet worden geladen. Controleer je verbinding en kies de regio opnieuw.")
        self.assertEqual((down["pressed"], down["line"], down["errors"]), (0, False, []))
        self.assertEqual(down["rows"], len(seen["start"]["rows"]))
        self.assertEqual(down["count"], seen["morning"]["count"])
        self.assertLessEqual(down["overflow"], 0)

    def test_the_app_opens_with_the_core_again(self):
        self.in_both(self.check_the_app_opens_with_the_core_again)

    def check_the_app_opens_with_the_core_again(self, seen):
        self.assertEqual(seen["storage"], ["tilburg-signalen.gezien"], "de keuze voor een regio wordt bewaard")
        self.assertEqual({button["pressed"] for button in seen["reopenedGebied"]["buttons"]}, {"false"})
        self.assertEqual(seen["reopenedGebied"]["rows"], seen["start"]["rows"])
        reopened, morning = dict(seen["reopened"]), dict(seen["morning"])
        # Opened a second time, the notices of the first visit are no longer "new"; the rest is the same.
        for page in (reopened, morning):
            page.pop("brief")
            page["tiles"] = [page["tiles"][0], page["tiles"][2]]
        self.assertEqual(reopened, morning)

    def test_what_a_region_misses_is_reported_with_the_region_not_on_the_morning_screen(self):
        seen = self.region()
        missing, first = seen["missing"], seen["first"]
        unread = 'Van %s zijn 146 berichten nog niet gelezen. Ze staan onder Onzeker met "Tekst nog niet gelezen"; de volgende verversingen halen ze op.' % first
        failed = ("Bij de laatste verversing konden 20 bekendmakingen van %s niet volledig worden gelezen. "
                  "Ze staan tijdelijk onder Onzeker; de volgende verversing probeert het opnieuw." % first)
        self.assertEqual(missing["errors"], [])
        # The core misses nothing: no line about reading on the morning screen, whatever the regions miss.
        self.assertFalse([line for line in missing["morning"] if "gelezen" in line], missing["morning"])
        self.assertEqual([line for line in missing["chosen"] if "gelezen" in line], [unread, failed])
        self.assertEqual(missing["back"], missing["morning"])
        subs = {button["name"]: button["sub"] for button in missing["buttons"]}
        self.assertTrue(subs[first].endswith(" · 146 ongelezen"), subs[first])
        self.assertFalse([sub for name, sub in subs.items() if name != first and "ongelezen" in sub])
        self.assertTrue(all(button["right"] <= 320 for button in missing["buttons"]), missing["buttons"])
        self.assertLessEqual(missing["buttonOverflow"], 0)
        self.assertLessEqual(missing["chosenOverflow"], 0)

    def test_address_outside_the_core_finds_its_notices_while_the_app_shows_the_core(self):
        outside = self.seen["adres"]["outside"]
        self.assertEqual(outside["errors"], [])
        self.assertEqual((outside["name"], outside["sub"]), ("Noordweg 402", "4333KK Middelburg"))
        self.assertEqual(outside["bag"]["Bouwjaar"], "1622")
        self.assertEqual(outside["parcels"], [{"Aanduiding": "Middelburg T 3010 (MDB01 T 3010)", "Grootte": "6.249 m², vastgesteld"}])
        self.assertLessEqual(outside["overflow"], 0)
        if "Zeeland" in outside["regios"]:
            # The notices of Zeeland are in a file of their own; the tab read it for this address, once.
            self.assertIn("test-regio-zeeland", outside["notices"]["groups"]["Dit adres"])
            self.assertEqual(outside["notices"]["rows"]["test-regio-zeeland"]["meta"], "10-11-2026 · Middelburg · Vergunning, aanvraag")
            self.assertEqual(outside["regionFile"], 1)
            self.assertRegex(outside["searched"], r"^Doorzocht: [\d.]+ berichten die de app nu heeft, ook de weggefilterde en die van Zeeland\.")
        # Nothing was chosen on the tab Gebied: the app itself still shows the core only.
        self.assertFalse(outside["regionLine"])
        self.assertEqual(outside["pressed"], 0)
        self.assertEqual(outside["coreCount"], self.seen["count"])
        self.assertEqual(outside["coreCards"], len(self.seen["first"]))

    # --- The tab "Adres". The registers of PDOK are played back by tests/js/adres_smoke.js, so these
    # tests do not depend on PDOK; the notices about the test address are added to what the page loads.

    def test_address_tab_is_compact_on_the_narrowest_phone(self):
        seen = self.seen["adres"]
        self.assertEqual(seen["errors"], [])
        for moment in ("emptyOverflow", "suggestOverflow", "overflow", "streetOpenOverflow"):
            with self.subTest(moment=moment):
                self.assertLessEqual(seen[moment], 0)
        self.assertLessEqual(seen["widest"], 320)
        self.assertEqual(seen["brokenDates"], 0)
        tabs = seen["tabs"]
        self.assertEqual([tab["label"] for tab in tabs], ["Berichten", "Gebied", "Bronnen", "Adres"])
        self.assertEqual([tab["lines"] for tab in tabs], [1, 1, 1, 1])
        self.assertEqual(len({tab["width"] for tab in tabs}), 1, "de vier tabbladen zijn niet even breed")
        self.assertTrue(all(tab["textWidth"] <= tab["width"] for tab in tabs), "een tabnaam past niet in zijn tab")
        self.assertLessEqual(tabs[-1]["right"], 320)
        self.assertEqual([tab["current"] for tab in tabs], [None, None, None, "page"])
        self.assertLessEqual(seen["map"]["right"], 320)
        self.assertEqual(seen["map"]["width"], seen["map"]["height"])
        self.assertTrue(all(height >= 40 for height in seen["linkHeights"]), seen["linkHeights"])
        self.assertTrue(all(option["height"] >= 44 and option["right"] <= 320 for option in seen["suggestions"]), seen["suggestions"])

    def test_address_tab_leaves_the_morning_screen_alone(self):
        seen = self.seen["adres"]
        self.assertEqual(seen["requestsBeforeUse"], 0, "het ochtendscherm vraagt iets op bij PDOK")
        self.assertEqual(seen["hash"], "#adres")
        self.assertEqual(seen["views"], ["view-adres"])
        self.assertTrue(seen["resultHiddenAtStart"])
        self.assertEqual(seen["viewsAfter"], ["view-berichten"])
        self.assertEqual(seen["morningAfter"], seen["morningBefore"])
        self.assertEqual(seen["morningBefore"]["brief"], self.seen["brief"])

    def test_address_search_suggests_while_typing_and_a_choice_fills_the_tab(self):
        seen = self.seen["adres"]
        self.assertEqual(seen["requestsForTwoLetters"], 0)
        self.assertEqual([option["text"] for option in seen["suggestions"]], ["Burgemeester van de Mortelplein 118a, 5037PL Tilburg"])
        self.assertIn("/bzk/locatieserver/search/v3_1/suggest?q=Burg.%20van%20de%20Mortelplein%20118a&fq=type%3Aadres", seen["suggestRequest"])
        self.assertEqual(seen["name"], "Burgemeester van de Mortelplein 118a")
        self.assertEqual(seen["sub"], "5037PL Tilburg")
        self.assertEqual(seen["input"], "Burgemeester van de Mortelplein 118a, 5037PL Tilburg")

    def test_address_tab_asks_only_pdok_and_without_a_key(self):
        seen = self.seen["adres"]
        self.assertEqual(sorted(seen["asked"]), ["adresobject", "kaart", "pand", "perceel", "perceel", "zoeker"])
        self.assertEqual(seen["askedHosts"], ["api.pdok.nl", "service.pdok.nl"])
        self.assertEqual(seen["keys"], 0)
        self.assertEqual(seen["elsewhere"], [], "de app roept nog een andere dienst aan")
        self.assertTrue(seen["newTabLinks"])

    def test_address_tab_shows_the_building_from_the_bag(self):
        seen = self.seen["adres"]
        self.assertEqual(seen["bag"], {"Bouwjaar": "1962", "Gebruiksdoel": "gezondheidszorgfunctie", "Oppervlakte": "280 m²", "Pandstatus": "Verbouwing pand"})
        self.assertIn("Bron: Basisregistratie Adressen en Gebouwen", seen["bagText"])

    def test_address_tab_shows_the_parcel_with_the_warning_at_its_size(self):
        seen = self.seen["adres"]
        self.assertEqual(seen["parcels"], [{"Aanduiding": "Tilburg Q 4688 (TBG01 Q 4688)", "Grootte": "46 m², vastgesteld"},
                                           {"Aanduiding": "Tilburg Q 4489 (TBG01 Q 4489)", "Grootte": "248 m², vastgesteld"}])
        self.assertEqual(seen["parcelWarning"], "Let op: de kadastrale kaart geeft alleen een indicatie van de ligging en de grootte. Er zijn geen maten aan te ontlenen.")
        self.assertTrue(seen["warningRightAfterSize"], "de waarschuwing staat niet direct onder de grootte")
        self.assertIn("Dit adres is aan 2 percelen gekoppeld.", seen["parcelText"])
        plan = seen["map"]
        self.assertTrue(plan["image"], "de achtergrondkaart is niet geladen")
        self.assertIn("https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0?", plan["src"])
        self.assertEqual(plan["shapes"], [True, True])
        self.assertTrue(plan["dot"])
        self.assertEqual(plan["bar"], "20 m")
        self.assertTrue(plan["barInside"])

    def test_address_tab_lists_the_notices_about_the_address(self):
        seen = self.seen["adres"]["notices"]
        groups = {name: [entry for entry in ids if entry.startswith("test-")] for name, ids in seen["groups"].items()}
        self.assertEqual(groups, {"Dit adres": ["test-adres-zelf"], "Mogelijk dit adres": ["test-adres-zonder", "test-adres-perceel"],
                                  "Zelfde straat, zonder huisnummer": ["test-adres-straat"]})
        shown = {entry for ids in seen["groups"].values() for entry in ids}
        self.assertFalse({"test-adres-buren", "test-adres-elders"} & shown)
        own = seen["rows"]["test-adres-zelf"]
        self.assertEqual(own["meta"], "10-11-2026 · Tilburg · Vergunning, aanvraag")
        self.assertEqual(own["titel"], "Aanvraag omgevingsvergunning, Burg. van de Mortelplein 118A, 5037 PL Tilburg")
        self.assertEqual((own["link"], own["linkText"]), ("https://zoek.officielebekendmakingen.nl/test-adres-zelf.html", "Open bij de bron"))
        self.assertEqual(own["reden"], ["In de ranglijst weggefilterd."])
        self.assertEqual(seen["rows"]["test-adres-zonder"]["meta"], "03-11-2026 · Tilburg · Vergunning, verleend")
        self.assertEqual(seen["rows"]["test-adres-zonder"]["reden"], ["Het bericht noemt huisnummer 118 zonder toevoeging."])
        self.assertIn("De tekst noemt dit adres niet, maar de locatie van het bericht ligt op hetzelfde perceel.", seen["rows"]["test-adres-perceel"]["reden"])
        text = self.seen["adres"]["noticesText"]
        self.assertRegex(text, r"Doorzocht: [\d.]+ berichten die de app nu heeft, ook de weggefilterde")
        self.assertIn("een bericht kan ontbreken", text)

    def test_address_tab_says_first_which_period_the_notices_cover(self):
        period = self.seen["adres"]["period"]
        windows = period["windows"]
        line = ("Deze lijst beslaat alleen de laatste %d dagen voor vergunningen en %d dagen voor plannen. "
                '"Geen publicaties" betekent dus niet dat er nooit iets is geweest.' % (windows["vergunning"], windows["plan"]))
        self.assertEqual(period["text"], line)
        self.assertTrue(period["first"], "de regel over de periode staat niet bovenaan het blok")
        self.assertEqual(period["lines"], 1)
        # Without any notice about the address: the same line first, then that nothing was found.
        empty = self.seen["adres"]["noNotices"]
        self.assertEqual(empty["errors"], [])
        self.assertEqual(empty["rows"], 0)
        self.assertLessEqual(empty["overflow"], 0)
        self.assertEqual([entry["text"] for entry in empty["lines"][:2]],
                         [line, "Geen publicaties over Burgemeester van de Mortelplein 118a in de berichten van de app."])
        self.assertEqual(empty["lines"][0]["cls"], "periode")
        self.assertEqual(len(empty["lines"]), 3)  # the period, nothing found, and what was searched

    def test_address_tab_marks_energy_label_and_plan_as_not_available_with_a_link(self):
        seen = self.seen["adres"]
        self.assertTrue(seen["energy"]["text"].startswith("Nog niet beschikbaar in de app."))
        self.assertEqual(seen["energy"]["links"], ["https://www.ep-online.nl/Energylabel/Search"])
        self.assertIn("Vul daar in: 5037PL 118 a.", seen["energy"]["text"])
        self.assertTrue(seen["plan"]["text"].startswith("Nog niet beschikbaar in de app."))
        self.assertEqual(seen["plan"]["links"], ["https://omgevingswet.overheid.nl/regels-op-de-kaart/documenten?locatie-stelsel=RD&locatie-x=132133&locatie-y=395880"])

    def test_address_search_that_does_not_answer_gives_a_message_not_an_empty_page(self):
        message = "De adreszoeker (PDOK Locatieserver) antwoordt niet. Controleer je verbinding of probeer het later opnieuw."
        down = self.seen["adres"]["searchDown"]
        self.assertEqual(down["message"], message)
        self.assertEqual((down["input"], down["heading"], down["result"], down["suggestions"]), (True, "Adres", False, False))
        self.assertEqual(down["errors"], [])
        silent = self.seen["adres"]["searchSilent"]
        self.assertEqual(silent["message"], message)
        self.assertLess(silent["seconds"], 20, "de app blijft wachten op een bron die zwijgt")
        self.assertEqual(silent["errors"], [])

    def test_a_register_that_does_not_answer_leaves_a_message_in_its_own_box(self):
        down = self.seen["adres"]["registersDown"]
        self.assertTrue(down["bag"].startswith("De BAG (Kadaster, via PDOK) antwoordt niet."), down["bag"])
        self.assertEqual(down["bagRetry"], ["Opnieuw proberen"])
        self.assertTrue(down["parcel"].startswith("De kadastrale kaart (Kadaster, via PDOK) antwoordt niet."), down["parcel"])
        self.assertEqual(down["parcelRetry"], 1)
        self.assertLessEqual(down["overflow"], 0)
        # What does not need those registers is simply there.
        self.assertEqual(down["name"], "Burgemeester van de Mortelplein 118a")
        self.assertIn("test-adres-zelf", down["notices"]["groups"]["Dit adres"])
        self.assertNotIn("test-adres-perceel", down["notices"]["groups"]["Mogelijk dit adres"])
        self.assertIn("worden pas gekoppeld als het perceel bekend is", down["noticesText"])
        self.assertTrue(down["energy"].startswith("Nog niet beschikbaar in de app."))
        self.assertTrue(down["plan"].startswith("Nog niet beschikbaar in de app."))
        # Trying again once the registers are back fills the boxes.
        again = self.seen["adres"]["afterRetry"]
        self.assertEqual(again["bag"]["Bouwjaar"], "1962")
        self.assertEqual(again["parcels"], 2)
        self.assertIn("test-adres-perceel", again["notices"]["groups"]["Mogelijk dit adres"])
        self.assertEqual(again["errors"], [])

    def test_a_missing_building_or_background_map_leaves_the_rest(self):
        parts = self.seen["adres"]["partsDown"]
        self.assertEqual(parts["bag"], {"Bouwjaar": "niet bekend", "Gebruiksdoel": "gezondheidszorgfunctie", "Oppervlakte": "280 m²", "Pandstatus": "niet bekend"})
        self.assertIn("Het pand zelf kon niet worden opgehaald; bouwjaar en pandstatus ontbreken daardoor.", parts["bagText"])
        self.assertEqual(parts["shapes"], 2)
        self.assertIn("De achtergrondkaart kon niet worden geladen; alleen de omtrek van het perceel is getekend.", parts["mapText"])
        self.assertEqual(parts["errors"], [])


if __name__ == "__main__":
    unittest.main()
