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
class VolgordeBijGelijkeScore(unittest.TestCase):
    """With equal scores: the most dwellings first, then the newest notice, then the nearest. The
    phase and the kind of location play no part, and a score is never changed (site/logic.js)."""

    def order(self, *items):
        return [entry["id"] for entry in logic(["sorted", list(items), "relevantie"])[0]]

    def test_a_higher_score_always_wins(self):
        self.assertEqual(self.order(item("veel", score=107, woningen=500, datum="2026-11-17"), item("hoog", score=108, woningen=2, datum="2026-10-01")), ["hoog", "veel"])

    def test_with_equal_scores_the_most_dwellings_come_first(self):
        # The case of 18-11-2026: a plan of 141 dwellings of 6 October and one of 100 of 27 October, both 108.
        bellini = item("bellinistraat", score=108, woningen=141, datum="2026-10-06", fase="Vastgesteld", km=3.3)
        tholen = item("tholen", score=108, woningen=100, datum="2026-10-27", fase="Voornemen", km=59.3, locatieSoort="gemeente")
        self.assertEqual(self.order(tholen, bellini), ["bellinistraat", "tholen"])

    def test_with_equal_scores_and_dwellings_the_newest_comes_first_then_the_nearest(self):
        old = item("oud", score=100, woningen=None, datum="2026-10-01", km=1.0)
        new_far = item("nieuw-ver", score=100, woningen=None, datum="2026-11-10", km=9.0)
        new_near = item("nieuw-dichtbij", score=100, woningen=None, datum="2026-11-10", km=2.0)
        self.assertEqual(self.order(old, new_far, new_near), ["nieuw-dichtbij", "nieuw-ver", "oud"])

    def test_no_number_of_dwellings_counts_as_none(self):
        self.assertEqual(self.order(item("zonder", score=100, woningen=None, datum="2026-11-17"), item("twee", score=100, woningen=2, datum="2026-10-01")), ["twee", "zonder"])

    def test_the_phase_and_the_kind_of_location_play_no_part(self):
        early = item("voornemen", score=100, woningen=10, datum="2026-11-10", fase="Voornemen", locatieSoort="gemeente")
        late = item("vastgesteld", score=100, woningen=10, datum="2026-11-01", fase="Vastgesteld", locatieSoort="exact")
        self.assertEqual(self.order(late, early), ["voornemen", "vastgesteld"], "bij gelijke score en gelijke woningen beslist de datum, niet de fase")

    def test_the_rank_numbers_follow_the_same_order_and_no_score_is_changed(self):
        items = [item("a", score=108, woningen=100, datum="2026-10-27"), item("b", score=108, woningen=141, datum="2026-10-06"), item("c", score=107, woningen=70)]
        ranks, same = logic(["rankMap", items], ["sorted", items, "relevantie"])
        self.assertEqual(ranks, {"b": 1, "a": 2, "c": 3})
        self.assertEqual(sorted((entry["id"], entry["score"]) for entry in same), [("a", 108), ("b", 108), ("c", 107)])


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class FaseTreden(unittest.TestCase):
    """The filter "Fase" has three steps. The grouping is a choice made in this app, not something
    the sources give (site/logic.js, FASE_TREDEN)."""

    def test_the_three_steps_are_these_eight_phases(self):
        steps = logic(["FASE_TREDEN"])[0]
        self.assertEqual([(step["id"], step["naam"], step["fasen"]) for step in steps],
                         [("vroeg", "Vroeg", ["Voornemen", "Aanvraag"]), ("midden", "Midden", ["Ontwerp", "Bekendmaking", "Besluit"]),
                          ("laat", "Laat", ["Vastgesteld", "Verleend", "Herstelbesluit"])])

    def test_a_phase_outside_the_three_steps_belongs_to_none(self):
        calls = [["faseTrede", fase] for fase in ("Aanvraag", "Besluit", "Herstelbesluit", "Voornemen tot verkoop", "Beslistermijn verlengd", "Geweigerd", "Ontwerpbesluit", "Onherroepelijk", None)]
        self.assertEqual(logic(*calls), ["vroeg", "midden", "laat", None, None, None, None, None, None])

    def test_the_filter_takes_a_step_or_one_phase(self):
        notices = [item("a", fase="Aanvraag"), item("b", fase="Voornemen"), item("c", fase="Vastgesteld"), item("d", fase="Voornemen tot verkoop"), item("e", fase="Besluit")]

        def found(fase):
            return sorted(entry["id"] for entry in logic(["select", notices, state(fase=fase), {"nieuw": {}, "latestDay": "2026-11-10", "today": TODAY}])[0]["main"])

        self.assertEqual(found("trede:vroeg"), ["a", "b"])
        self.assertEqual(found("trede:midden"), ["e"])
        self.assertEqual(found("trede:laat"), ["c"])
        self.assertEqual(found("Voornemen tot verkoop"), ["d"])
        self.assertEqual(found("Aanvraag"), ["a"])
        self.assertEqual(found(""), ["a", "b", "c", "d", "e"])

    def test_the_choices_show_the_steps_always_and_every_phase_that_occurs(self):
        notices = [item("a", fase="Aanvraag"), item("b", fase="Aanvraag"), item("c", fase="Vastgesteld"), item("d", fase="Voornemen tot verkoop")]
        choices = logic(["faseKeuzes", notices], ["faseKeuzes", []])
        self.assertEqual([(c["value"], c["label"]) for c in choices[0]["treden"]],
                         [("trede:vroeg", "Vroeg: voornemen, aanvraag (2)"), ("trede:midden", "Midden: ontwerp, bekendmaking, besluit (0)"), ("trede:laat", "Laat: vastgesteld, verleend, herstelbesluit (1)"),
                          ("trede:overig", "Overig: standen in geen trede (1)")])
        self.assertEqual([(c["value"], c["label"]) for c in choices[0]["fasen"]],
                         [("Aanvraag", "Aanvraag (2)"), ("Vastgesteld", "Vastgesteld (1)"), ("Voornemen tot verkoop", "Voornemen tot verkoop (1)")])
        self.assertEqual(([c["value"] for c in choices[1]["treden"]], choices[1]["fasen"]), (["trede:vroeg", "trede:midden", "trede:laat", "trede:overig"], []))

    def test_overig_is_everything_that_is_in_no_step(self):
        notices = [item("a", fase="Aanvraag"), item("b", fase="Besluit"), item("c", fase="Vastgesteld"), item("d", fase="Voornemen tot verkoop"),
                   item("e", fase="Beslistermijn verlengd"), item("f", fase="Geweigerd"), item("g", fase=None), item("h", fase="Ontwerpbesluit")]

        def found(fase):
            return sorted(entry["id"] for entry in logic(["select", notices, state(fase=fase), {"nieuw": {}, "latestDay": "2026-11-10", "today": TODAY}])[0]["main"])

        self.assertEqual(found("trede:overig"), ["d", "e", "f", "g", "h"])
        # The four choices together are all notices, and no notice is in two of them.
        parts = [found("trede:" + step) for step in ("vroeg", "midden", "laat", "overig")]
        self.assertEqual(sorted(sum(parts, [])), ["a", "b", "c", "d", "e", "f", "g", "h"])
        self.assertEqual(logic(["faseKeuzes", notices])[0]["treden"][3], {"value": "trede:overig", "label": "Overig: standen in geen trede (5)", "aantal": 5})


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class WatDeLijstenTonen(unittest.TestCase):
    """With regions chosen the lists show everything together, the core alone or one region alone."""

    CORE = [item("k1", regio="kern"), item("k2", regio="kern", datum="2026-11-12")]
    LISTS = {"Zeeland": [item("z1", regio="Zeeland", km=80.0)], "West-Brabant": [item("w1", regio="West-Brabant", km=30.0), item("w2", regio="West-Brabant", km=31.0)]}

    def ids(self, regios, toon):
        return sorted(entry["id"] for entry in logic(["toonItems", self.CORE, self.LISTS, regios, toon])[0])

    def test_without_a_region_there_is_nothing_to_choose(self):
        self.assertEqual(logic(["toonKeuzes", []], ["toonOf", [], "kern"], ["toonOf", [], "Zeeland"]), [[], "samen", "samen"])
        self.assertEqual(self.ids([], "Zeeland"), ["k1", "k2"])

    def test_the_choices_are_together_the_core_and_every_chosen_region(self):
        self.assertEqual([(c["id"], c["label"]) for c in logic(["toonKeuzes", ["West-Brabant", "Zeeland"]])[0]],
                         [("samen", "Samen"), ("kern", "Alleen de kern"), ("West-Brabant", "Alleen West-Brabant"), ("Zeeland", "Alleen Zeeland")])

    def test_together_is_the_default_and_what_an_unknown_choice_falls_back_to(self):
        chosen = ["West-Brabant", "Zeeland"]
        self.assertEqual(logic(["toonOf", chosen, "samen"], ["toonOf", chosen, None], ["toonOf", chosen, "Midden-Brabant"], ["toonOf", chosen, "kern"], ["toonOf", chosen, "Zeeland"]),
                         ["samen", "samen", "samen", "kern", "Zeeland"])
        self.assertEqual(self.ids(chosen, "Midden-Brabant"), ["k1", "k2", "w1", "w2", "z1"])

    def test_every_choice_shows_its_own_notices(self):
        chosen = ["West-Brabant", "Zeeland"]
        self.assertEqual(self.ids(chosen, "samen"), ["k1", "k2", "w1", "w2", "z1"])
        self.assertEqual(self.ids(chosen, "kern"), ["k1", "k2"])
        self.assertEqual(self.ids(chosen, "Zeeland"), ["z1"])
        self.assertEqual(self.ids(["Zeeland"], "samen"), ["k1", "k2", "z1"])

    def test_only_with_one_region_alone_the_page_says_that_the_morning_line_is_about_the_core(self):
        chosen = ["West-Brabant", "Zeeland"]
        self.assertEqual(logic(["kernNote", chosen, "Zeeland"], ["kernNote", chosen, "West-Brabant"], ["kernNote", chosen, "samen"], ["kernNote", chosen, "kern"],
                               ["kernNote", [], "Zeeland"], ["kernNote", ["Zeeland"], "West-Brabant"], ["kernNote", chosen, None]),
                         ["Dit gaat over de kern. De lijsten hieronder tonen alleen Zeeland.", "Dit gaat over de kern. De lijsten hieronder tonen alleen West-Brabant.", "", "", "", "", ""])

    def test_the_line_under_the_name_follows_the_choice(self):
        centre = "De Heuvel, Tilburg-centrum"
        self.assertEqual(logic(["scopeLine", 15, centre, ["Zeeland"], "samen"], ["scopeLine", 15, centre, ["Zeeland"], "kern"], ["scopeLine", 15, centre, ["Zeeland"], "Zeeland"],
                               ["scopeLine", 15, centre, [], "kern"], ["scopeLine", 15, centre, ["Zeeland"], "West-Brabant"]),
                         ["Kern en Zeeland", "Alleen de kern", "Alleen Zeeland", "Kern: binnen 15 km van De Heuvel, Tilburg-centrum", "Kern en Zeeland"])


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class OndertitelEnInleiding(unittest.TestCase):
    """The line under the name of the app and the introduction on the tab Gebied follow what is
    shown: the core, or the core with the chosen regions (site/logic.js)."""

    CENTRE = "De Heuvel, Tilburg-centrum"

    def test_without_a_region_the_line_names_the_core_and_its_radius(self):
        self.assertEqual(logic(["scopeLine", 15, self.CENTRE, []], ["scopeLine", 15, self.CENTRE, None], ["scopeLine", 20, "de Markt", []]),
                         ["Kern: binnen 15 km van De Heuvel, Tilburg-centrum", "Kern: binnen 15 km van De Heuvel, Tilburg-centrum", "Kern: binnen 20 km van de Markt"])

    def test_with_regions_the_line_names_the_core_and_the_regions(self):
        self.assertEqual(logic(["scopeLine", 15, self.CENTRE, ["Zeeland"]], ["scopeLine", 15, self.CENTRE, ["West-Brabant", "Zeeland"]],
                               ["scopeLine", 15, self.CENTRE, ["Midden-Brabant", "West-Brabant", "Zeeland"]]),
                         ["Kern en Zeeland", "Kern, West-Brabant en Zeeland", "Kern, Midden-Brabant, West-Brabant en Zeeland"])

    def test_the_introduction_without_a_region_describes_the_core(self):
        self.assertEqual(logic(["gebiedIntro", 15, self.CENTRE, 17, [], 17])[0],
                         "Kern: alles binnen 15 km hemelsbreed van De Heuvel, Tilburg-centrum. Daarin liggen 17 gemeenten, waarvan de meeste maar voor een deel. "
                         "Een bericht telt mee als de locatie zelf binnen de straal valt.")

    def test_the_introduction_with_regions_says_what_is_added(self):
        one, three = logic(["gebiedIntro", 15, self.CENTRE, 17, ["Zeeland"], 30],
                           ["gebiedIntro", 15, self.CENTRE, 17, ["Midden-Brabant", "West-Brabant", "Zeeland"], 43])
        self.assertEqual(one, "Kern en Zeeland. De kern is alles binnen 15 km hemelsbreed van De Heuvel, Tilburg-centrum: 17 gemeenten, waarvan de meeste maar voor een deel. "
                              "Van Zeeland telt elke gemeente in haar geheel mee. Samen staan er nu 30 gemeenten op de lijst.")
        self.assertEqual(three, "Kern, Midden-Brabant, West-Brabant en Zeeland. De kern is alles binnen 15 km hemelsbreed van De Heuvel, Tilburg-centrum: 17 gemeenten, "
                                "waarvan de meeste maar voor een deel. Van de gekozen regio's telt elke gemeente in haar geheel mee. Samen staan er nu 43 gemeenten op de lijst.")


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
        # The report on paper (rapport.js) comes last: it copies what the tab "Adres" built.
        self.assertEqual(scripts, ["logic.js", "app.js", "adres.js", "adres-app.js", "rapport.js"])

    def test_app_builds_text_not_markup(self):
        self.assertNotRegex(self.app, r"innerHTML|insertAdjacentHTML|document\.write")
        self.assertNotRegex(read("rapport.js"), r"innerHTML|insertAdjacentHTML|document\.write")

    def test_the_report_names_no_box_and_no_address(self):
        """The report copies every box of the tab "Adres"; a box added later comes along by itself.
        So the code of the report names none of the boxes, and holds no address."""
        code = read("rapport.js")
        boxes = re.findall(r'<section class="vak"[^>]*aria-labelledby="(kop-[\w-]+)"', self.html)
        self.assertGreaterEqual(len(boxes), 6)
        ids = re.findall(r'<section class="vak" id="([\w-]+)"', self.html)
        for box in boxes + [box.replace("kop-", "", 1) for box in boxes] + ids:
            with self.subTest(vak=box):
                self.assertNotIn(box, code)
        self.assertNotRegex(code, r"\b\d{4} ?[A-Z]{2}\b", "een postcode in de code van het rapport")

    def test_the_print_style_is_light_a4_and_keeps_boxes_whole(self):
        css = read("styles.css")
        self.assertRegex(css, r"@page \{[^}]*size: A4")
        self.assertIn("counter(page)", css)
        printing = css[css.index("@media print"):]
        self.assertIn("--bg: #ffffff", printing)
        self.assertIn("--ink: #000000", printing)
        self.assertRegex(printing, r"\.rapport-vak \{[^}]*break-inside: avoid")
        self.assertRegex(printing, r"\.tabs, \.masthead[^{]*\{ display: none !important; \}")

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
    def shown(data, chosen, only=None):
        """The notices in the lists: the core with the chosen regions, or `only` one part of it."""
        if only:
            return [entry for entry in data["berichten"] if entry["regio"] == only]
        return [entry for entry in data["berichten"] if entry["regio"] == "kern" or entry["regio"] in chosen]

    def expected(self, data, chosen, only=None):
        """What the tab Berichten shows for a choice of regions, as the texts on the page."""
        shown = self.shown(data, chosen, only)
        locations = sum(1 for entry in shown if entry["klasse"] == "ontwikkellocatie")
        reach = max([data["straalKm"]] + [-(-entry["afstandKm"] // 1) for entry in shown if entry["afstandKm"] > data["straalKm"]])
        return {"ranglijst": str(locations), "onzeker": str(sum(1 for entry in shown if entry["klasse"] == "onzeker")),
                "removed": "(%d)" % sum(1 for entry in shown if entry["klasse"] == "weggefilterd"),
                "count": ("Top 10 van %d ontwikkellocaties" % locations if locations > 10 else "%d ontwikkellocatie%s" % (locations, "" if locations == 1 else "s"))
                + ", hoogste rang eerst", "kmMax": str(int(reach)), "locations": locations}

    def assert_berichten(self, page, data, chosen, only=None):
        want = self.expected(data, chosen, only)
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
        for moment in ("withOne", "onlyRegion", "onlyCore", "together", "withAll"):
            with self.subTest(keuze=moment):
                self.assertTrue(seen[moment]["toon"], "de keuze van wat de lijsten tonen ontbreekt")
                self.assertTrue(all(button["height"] >= 30 and button["right"] <= 320 for button in seen[moment]["toon"]), seen[moment]["toon"])
        for moment in ("onlyRegion", "onlyCore", "together"):
            self.assertLessEqual(seen[moment]["overflow"], 0)
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
        self.assertEqual(seen["withOne"]["line"], "Met " + first + " erbij.")
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
        self.assertEqual(seen["withAll"]["line"], "Met " + sentence + " erbij.")
        self.assertEqual(sorted(seen["askedForAll"]), sorted(regio["bestand"] for regio in data["overview"]), "een regiobestand is twee keer gelezen")

    # --- What the lists show with a region chosen: together, the core alone or one region alone.

    @staticmethod
    def order_key(entry):
        """Highest score first; with equal scores the most dwellings, then the newest, then the nearest."""
        return (-entry["score"], -(entry["woningen"] or 0), tuple(-ord(c) for c in entry["datum"]), entry["afstandKm"])

    def test_the_lists_show_together_the_core_alone_or_one_region_alone(self):
        self.in_both(self.check_the_lists_show_together_the_core_alone_or_one_region_alone)

    def check_the_lists_show_together_the_core_alone_or_one_region_alone(self, seen):
        data, first, morning = seen["data"], seen["first"], seen["morning"]
        names = [button["name"] for button in seen["start"]["buttons"]]

        def choice(moment):
            return [button["label"] for button in seen[moment]["toon"]], [button["label"] for button in seen[moment]["toon"] if button["pressed"]]

        self.assertEqual(morning["toon"], [], "zonder gekozen regio valt er niets te kiezen")
        labels = ["Samen", "Alleen de kern", "Alleen " + first]
        self.assertEqual(choice("withOne"), (labels, ["Samen"]), "Samen is de standaard")
        # The region alone: the tiles, the count and the ranking are about the region; the morning line stays the core.
        alone = seen["onlyRegion"]
        self.assertEqual(choice("onlyRegion"), (labels, ["Alleen " + first]))
        self.assert_berichten(alone, data, [first], only=first)
        self.assertEqual((alone["scope"], alone["line"]), ("Alleen " + first, "Met " + first + " erbij."))
        self.assertEqual(alone["brief"], morning["brief"], "het ochtendscherm blijft de kern")
        self.assertEqual(alone["kernNote"], "Dit gaat over de kern. De lijsten hieronder tonen alleen " + first + ".")
        for moment in ("morning", "withOne", "onlyCore", "together", "withAll", "back", "reopened"):
            self.assertIsNone(seen[moment]["kernNote"], "de regel over de kern staat er ook bij " + moment)
        self.assertEqual(alone["tiles"][1], "0", "Nieuw telt de kern; in een regio alleen is niets nieuw")
        in_region = [e for e in self.shown(data, [first], only=first) if e["klasse"] == "ontwikkellocatie"]
        self.assertEqual(alone["ranks"], [str(n) for n in range(1, len(in_region) + 1)], "de rang telt binnen wat de lijst toont")
        self.assertEqual(sorted(alone["ids"]), sorted(e["id"] for e in in_region))
        # The core alone: as the app opens, with the region still chosen.
        core = seen["onlyCore"]
        self.assertEqual(choice("onlyCore"), (labels, ["Alleen de kern"]))
        self.assertEqual((core["tiles"], core["count"], core["removed"], core["kmMax"], core["brief"]),
                         (morning["tiles"], morning["count"], morning["removed"], morning["kmMax"], morning["brief"]))
        self.assertEqual((core["scope"], core["line"]), ("Alleen de kern", "Met " + first + " erbij."))
        # Together again: as before the choice.
        together = seen["together"]
        self.assertEqual(choice("together"), (labels, ["Samen"]))
        for key in ("tiles", "count", "removed", "kmMax", "scope", "line", "brief"):
            self.assertEqual(together[key], seen["withOne"][key], key)
        self.assertEqual(together["ids"], seen["withOneAllIds"])
        # The choice is one of the tab Berichten: the tab Gebied keeps the region chosen all along.
        self.assertEqual([button["pressed"] for button in seen["oneAfterChoice"]["buttons"]], [button["pressed"] for button in seen["one"]["buttons"]])
        self.assertEqual(seen["oneAfterChoice"]["rows"], seen["one"]["rows"])
        # Another choice of regions starts with everything together.
        self.assertEqual(choice("withAll"), (["Samen", "Alleen de kern"] + ["Alleen " + name for name in names], ["Samen"]))

    def test_with_equal_scores_the_most_dwellings_come_first_then_the_newest(self):
        self.in_both(self.check_with_equal_scores_the_most_dwellings_come_first_then_the_newest)

    def check_with_equal_scores_the_most_dwellings_come_first_then_the_newest(self, seen):
        by_id = {entry["id"]: entry for entry in seen["data"]["berichten"]}
        for moment, ids in (("samen", seen["withOneAllIds"]), ("alleen de regio", seen["onlyRegion"]["ids"]), ("alleen de kern", seen["onlyCore"]["ids"])):
            with self.subTest(lijst=moment):
                keys = [self.order_key(by_id[identifier]) for identifier in ids]
                self.assertEqual(keys, sorted(keys))
                self.assertGreater(len(ids), 0)

    FASEN = {"trede:vroeg": ("Vroeg", ["Voornemen", "Aanvraag"]), "trede:midden": ("Midden", ["Ontwerp", "Bekendmaking", "Besluit"]),
             "trede:laat": ("Laat", ["Vastgesteld", "Verleend", "Herstelbesluit"])}
    IN_EEN_TREDE = {fase for _, members in FASEN.values() for fase in members}

    def test_the_filter_fase_has_three_steps_overig_and_every_phase(self):
        seen = self.region()
        fase, data = seen["fase"], seen["data"]
        core = [entry for entry in data["berichten"] if entry["regio"] == "kern"]
        relevant = [entry for entry in core if entry["klasse"] != "weggefilterd"]
        self.assertEqual(fase["label"], "Fase")
        self.assertEqual([group["label"] for group in fase["groups"]], ["Trede", "Stand"])
        steps, phases = fase["groups"]
        self.assertEqual([option["value"] for option in steps["options"]], list(self.FASEN) + ["trede:overig"])
        seen_ids = []
        for option in steps["options"]:
            name, members = self.FASEN.get(option["value"], ("Overig", None))
            with self.subTest(trede=name):
                def inside(entry, members=members):
                    return entry["fase"] in members if members else entry["fase"] not in self.IN_EEN_TREDE
                count = sum(1 for entry in relevant if inside(entry))
                self.assertEqual(option["label"], "%s: %s (%d)" % (name, ", ".join(members).lower(), count) if members else "Overig: standen in geen trede (%d)" % count)
                locations = [entry for entry in core if entry["klasse"] == "ontwikkellocatie" and inside(entry)]
                seen_ids += fase["cards"][option["value"]]
                self.assertTrue(fase["counts"][option["value"]].startswith(
                    ("Top 10 van %d ontwikkellocaties" % len(locations)) if len(locations) > 10 else "%d ontwikkellocatie" % len(locations)), fase["counts"][option["value"]])
                self.assertEqual(sorted(fase["cards"][option["value"]]), sorted(entry["id"] for entry in locations))
        # The four choices together are the whole ranking, and no location is in two of them.
        self.assertEqual(sorted(seen_ids), sorted(entry["id"] for entry in core if entry["klasse"] == "ontwikkellocatie"))
        present = sorted({entry["fase"] for entry in relevant if entry["fase"]})
        self.assertEqual(sorted(option["value"] for option in phases["options"]), present)
        self.assertLessEqual(fase["overflow"], 0)
        self.assertEqual(seen["afterFase"], seen["morning"], "na wissen staat de lijst niet meer zoals bij het openen")

    def test_in_the_fixed_situation_the_choice_reads_as_written_here(self):
        _, seen = self.fixed()
        self.assertEqual([button["label"] for button in seen["withOne"]["toon"]], ["Samen", "Alleen de kern", "Alleen Zeeland"])
        self.assertEqual([button["label"] for button in seen["withAll"]["toon"]], ["Samen", "Alleen de kern", "Alleen Midden-Brabant", "Alleen West-Brabant", "Alleen Zeeland"])
        alone = seen["onlyRegion"]
        self.assertEqual((alone["scope"], alone["count"], alone["tiles"]), ("Alleen Zeeland", "3 ontwikkellocaties, hoogste rang eerst", ["3", "0", "2"]))
        self.assertEqual(alone["kernNote"], "Dit gaat over de kern. De lijsten hieronder tonen alleen Zeeland.")
        # A search stays when the choice changes: "Goes" finds one location in Zeeland and none in the core.
        self.assertEqual(seen["searchTogether"], {"zoek": "Goes", "count": "1 ontwikkellocatie, hoogste rang eerst"})
        self.assertEqual(seen["searchOnlyRegion"], {"zoek": "Goes", "count": "1 ontwikkellocatie, hoogste rang eerst"})
        self.assertEqual(seen["searchOnlyCore"], {"zoek": "Goes", "count": "0 ontwikkellocaties, hoogste rang eerst"})

    # --- The line under the name of the app and the introduction on the tab Gebied follow the choice.

    @staticmethod
    def with_core(names):
        names = ["Kern"] + list(names)
        return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " en " + names[-1]

    def test_the_line_under_the_name_follows_the_chosen_regions(self):
        self.in_both(self.check_the_line_under_the_name_follows_the_chosen_regions)

    def check_the_line_under_the_name_follows_the_chosen_regions(self, seen):
        data, first = seen["data"], seen["first"]
        names = [button["name"] for button in seen["start"]["buttons"]]
        core = "Kern: binnen %d km van %s" % (data["straalKm"], data["centrum"])
        self.assertEqual((seen["morning"]["scope"], seen["start"]["scope"]["text"]), (core, core))
        self.assertEqual((seen["one"]["scope"]["text"], seen["withOne"]["scope"]), ("Kern en " + first, "Kern en " + first), "op beide tabbladen dezelfde regel")
        self.assertEqual((seen["all"]["scope"]["text"], seen["withAll"]["scope"]), (self.with_core(names), self.with_core(names)))
        self.assertEqual(seen["reversed"]["scope"]["text"], self.with_core(names), "de volgorde van kiezen bepaalt de volgorde van de namen")
        self.assertEqual((seen["back"]["scope"], seen["backGebied"]["scope"]["text"], seen["reopened"]["scope"], seen["reopenedGebied"]["scope"]["text"]), (core,) * 4)
        for moment in ("start", "one", "all", "backGebied", "reopenedGebied", "reversed"):
            with self.subTest(moment=moment):
                line = seen[moment]["scope"]
                self.assertEqual(line["name"], "Tilburg Signalen")
                # The font service is kept out here, so the text stands in the font of this machine.
                # In a wide font (DejaVu Sans on the runners of GitHub) the long lines take three lines
                # at 320 px; that is not a fault. With the fonts of the app it is two: see the test below.
                self.assertLessEqual(line["lines"], 3, "de regel onder de naam loopt op 320 pixels over meer dan drie regels: " + line["text"])
                self.assertLessEqual(line["right"], line["updatedLeft"], "de regel loopt door het tijdstip heen")
                self.assertLessEqual(seen[moment]["overflow"], 0)

    def test_with_the_fonts_of_the_app_the_line_under_the_name_takes_at_most_two_lines(self):
        head = self.seen["kop"]
        if not head["loaded"]:
            self.skipTest("de lettertypen van de app zijn niet geladen (de lettertypedienst is niet bereikbaar)")
        self.assertEqual(sorted(head["lines"]), ["320", "375"])
        for width, texts in sorted(head["lines"].items()):
            self.assertEqual(len(texts), 3)
            for text, seen in texts.items():
                with self.subTest(breedte=width, regel=text):
                    self.assertLessEqual(seen["lines"], 2)
                    self.assertTrue(seen["clear"], "de regel loopt door het tijdstip heen")
                    self.assertLessEqual(seen["overflow"], 0)
        self.assertEqual(head["lines"]["320"]["Kern en Zeeland"]["lines"], 1)

    def test_the_introduction_of_the_area_follows_the_chosen_regions(self):
        self.in_both(self.check_the_introduction_of_the_area_follows_the_chosen_regions)

    def check_the_introduction_of_the_area_follows_the_chosen_regions(self, seen):
        data, first = seen["data"], seen["first"]
        names = [button["name"] for button in seen["start"]["buttons"]]
        centre = "alles binnen %d km hemelsbreed van %s" % (data["straalKm"], data["centrum"])
        self.assertTrue(seen["start"]["intro"].startswith("Kern: " + centre + ". Daarin liggen "), seen["start"]["intro"])
        one = seen["one"]["intro"]
        self.assertTrue(one.startswith("Kern en " + first + ". De kern is " + centre + ": %d gemeenten" % len(seen["start"]["rows"])), one)
        self.assertIn("Van " + first + " telt elke gemeente in haar geheel mee.", one)
        self.assertTrue(one.endswith("Samen staan er nu %d gemeenten op de lijst." % len(seen["one"]["rows"])), one)
        every = seen["all"]["intro"]
        self.assertTrue(every.startswith(self.with_core(names) + ". De kern is "), every)
        if len(names) > 1:
            self.assertIn("Van de gekozen regio's telt elke gemeente in haar geheel mee.", every)
        self.assertTrue(every.endswith("Samen staan er nu %d gemeenten op de lijst." % len(seen["all"]["rows"])), every)
        self.assertEqual((seen["backGebied"]["intro"], seen["reopenedGebied"]["intro"]), (seen["start"]["intro"],) * 2)

    def test_in_the_fixed_situation_the_lines_read_as_written_here(self):
        _, seen = self.fixed()
        self.assertEqual(seen["start"]["scope"]["text"], "Kern: binnen 15 km van De Heuvel, Tilburg-centrum")
        self.assertEqual(seen["one"]["scope"]["text"], "Kern en Zeeland")
        self.assertEqual(seen["all"]["scope"]["text"], "Kern, Midden-Brabant, West-Brabant en Zeeland")
        self.assertEqual(seen["reversed"]["scope"]["text"], "Kern, Midden-Brabant, West-Brabant en Zeeland")
        self.assertTrue(seen["one"]["intro"].startswith("Kern en Zeeland. De kern is alles binnen 15 km hemelsbreed van De Heuvel, Tilburg-centrum: "), seen["one"]["intro"])

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

    KEPT = ("hash", "zoek", "type", "filtersOpen", "line", "toon", "pressed", "open", "adres", "adresVisible", "bag", "perceel", "scope")

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
        self.assertTrue(after["state"]["updated"].startswith("Bijgewerkt ") and after["state"]["updated"].endswith("23:56"), after["state"]["updated"])
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
        self.assertEqual((before["pressed"], before["line"], before["toon"], before["zoek"], before["type"], before["filtersOpen"], len(before["open"]), before["scope"]),
                         (["Zeeland"], "Met Zeeland erbij.", ["Samen"], "Goes", "vergunning", True, 1, "Kern en Zeeland"))
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

    def test_a_refresh_keeps_the_choice_of_what_the_lists_show(self):
        seen = self.seen["verversen"]
        alone, later = seen["regionAlone"]["state"], seen["regionAloneLater"]["state"]
        self.assertEqual((alone["toon"], alone["scope"]), (["Alleen Zeeland"], "Alleen Zeeland"))
        self.assertTrue(later["updated"].endswith("23:59"), later["updated"])
        self.assertEqual((later["toon"], later["scope"], later["pressed"], later["zoek"], later["type"]), (alone["toon"], alone["scope"], alone["pressed"], alone["zoek"], alone["type"]))
        self.assertEqual(later["count"], alone["count"])

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
        self.assertTrue(seen["connectionBack"]["state"]["updated"].endswith("23:57"), seen["connectionBack"]["state"]["updated"])

    def test_a_region_file_that_does_not_come_at_a_refresh_keeps_what_the_region_had(self):
        seen = self.seen["verversen"]
        down, back = seen["regionDown"]["state"], seen["connectionBack"]["state"]
        self.assertTrue(down["updated"].endswith("23:58"), down["updated"])
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
        self.assertFalse([line for line in missing["onlyCore"] if "gelezen" in line], "met alleen de kern in de lijst hoort de melding van de regio er niet te staan")
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

    def test_no_test_asks_the_real_energy_label_worker(self):
        # Found in run 46 (19-11-2026): with the Worker set in the live data, the live check sent the
        # test address to the real Worker, and so to EP-Online, from GitHub. The tests now set the
        # setting themselves; any request to a Worker on workers.dev is stopped and counted.
        self.assertEqual(self.seen["realWorker"], [], "een test vroeg de echte Worker")

    def test_the_site_points_the_energy_label_at_the_worker_in_the_settings(self):
        """What the site serves, read and not used: on the live site the address of the placed
        Worker from config.json; in the checkout that, or empty until a refresh has written it."""
        with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as handle:
            setting = json.load(handle)["energielabel_worker"]
        served = self.seen["adres"].get("servedWorker")
        if self.url:
            self.assertEqual(served, setting, "de live site wijst niet naar de Worker uit config.json")
        else:
            self.assertIn(served, (None, "", setting))

    def test_address_tab_asks_only_pdok_and_without_a_key(self):
        seen = self.seen["adres"]
        self.assertEqual(sorted(seen["asked"]), ["adresobject", "bestemming", "kaart", "pand", "perceel", "perceel", "zoeker"])
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

    # --- The energy label, with the Worker set (tests/js/adres_smoke.js, 320 px). The answers of the
    # Worker are played; the Worker itself is tested in tests/test_energielabel.py.

    EP_ONLINE = "https://www.ep-online.nl/Energylabel/Search"

    def test_the_energy_label_is_asked_of_the_worker_with_the_address_and_nothing_else(self):
        label = self.seen["adres"]["label"]
        self.assertEqual(label["errors"], [])
        self.assertEqual(label["elsewhere"], [], "de app roept nog een andere dienst aan")
        first = label["asked"][0]
        self.assertEqual(first["url"], "https://energielabel.worker.test/", "het adres hoort niet in het webadres van de vraag: dat kan in een logboek komen")
        self.assertEqual(first["method"], "POST")
        self.assertEqual(json.loads(first["body"]), {"postcode": "5037PL", "huisnummer": "118", "huisletter": "a"})
        for asked in label["asked"]:
            for part in ("5037", "118", "postcode", "huisnummer", "?"):
                self.assertNotIn(part, asked["url"])
        # Plain text and no headers of the app's own: the browser then asks without a preflight.
        self.assertTrue(first["contentType"].lower().startswith("text/plain"), first["contentType"])
        for header in ("authorization", "cookie", "x-api-key"):
            self.assertNotIn(header, first["headers"], "de app stuurt geen sleutel of cookie mee")
        self.assertEqual(len(label["asked"]), 1, "één adres kiezen is één vraag aan de Worker")

    def test_a_label_that_is_found_is_shown_with_its_source_and_the_date(self):
        label = self.seen["adres"]["label"]
        found, day = label["found"], label["today"]
        self.assertEqual((found["uitkomst"], found["klasse"]), ("gevonden", "A+"))
        self.assertEqual(found["facts"], [["Geregistreerd", "12-06-2023"], ["Geldig tot", "12-06-2033"], ["Soort gebouw", "Woningbouw"]])
        today = "%s-%s-%s" % (day[8:10], day[5:7], day[0:4])
        self.assertEqual(found["notes"][0], "Bron: EP-Online (Rijksdienst voor Ondernemend Nederland), opgevraagd op " + today +
                         ". Getoond is het laatst geregistreerde label dat nog geldig is.")
        self.assertIsNone(found["button"])
        self.assertNotIn("Nog niet beschikbaar", found["text"])

    def test_the_three_other_outcomes_each_have_their_own_text(self):
        label = self.seen["adres"]["label"]
        self.assertEqual((label["none"]["uitkomst"], label["none"]["klasse"]), ("geen", None))
        none = label["none"]
        day = "-".join(reversed(label["today"].split("-")))
        self.assertTrue(none["text"].startswith(
            "EP-Online vindt voor dit adres geen geldig label. Mogelijk staat het label onder een andere schrijfwijze (huisletter of toevoeging). "
            "Zoek het na op ep-online.nl. Opgevraagd op " + day + "."), none["text"])
        self.assertIsNone(none["button"])
        # The link to the search screen of EP-Online stays under it, with what to fill in there.
        self.assertEqual(none["links"], [self.EP_ONLINE])
        self.assertIn("Zoek op EP-Online", none["text"])
        self.assertTrue(any("5037PL 118 a" in note for note in none["notes"]), none["notes"])
        self.assertLessEqual(none["overflow"], 0, "de tekst past niet op 320 pixels")
        self.assertEqual(label["minute"]["uitkomst"], "teveel")
        self.assertTrue(label["minute"]["text"].startswith("Er worden op dit moment te veel energielabels opgevraagd. Probeer het over een minuut opnieuw."))
        self.assertEqual(label["minute"]["button"], "Opnieuw proberen")
        self.assertTrue(label["day"]["text"].startswith("Er zijn vandaag te veel energielabels opgevraagd. Probeer het morgen opnieuw."))
        self.assertIsNone(label["day"]["button"], "morgen pas: een knop om het nu opnieuw te proberen helpt niet")
        for moment in ("gone", "fault"):
            with self.subTest(moment=moment):
                self.assertEqual(label[moment]["uitkomst"], "onbereikbaar")
                self.assertTrue(label[moment]["text"].startswith("Het energielabel kon niet worden opgevraagd: de dienst is niet bereikbaar."))
                self.assertEqual(label[moment]["button"], "Opnieuw proberen")
        self.assertTrue(label["refused"]["text"].startswith("Voor dit adres kan geen energielabel worden opgevraagd."))
        texts = {label[moment]["text"] for moment in ("found", "none", "minute", "day", "gone", "refused")}
        self.assertEqual(len(texts), 6)

    def test_in_every_outcome_the_link_to_ep_online_stays_and_the_box_fits_the_narrowest_phone(self):
        label = self.seen["adres"]["label"]
        for moment in ("found", "none", "minute", "day", "fault", "refused", "gone"):
            with self.subTest(moment=moment):
                box = label[moment]
                self.assertEqual(box["links"], [self.EP_ONLINE])
                self.assertIn("Zoek op EP-Online", box["text"])
                self.assertIn("Vul daar in: 5037PL 118 a.", box["text"])
                self.assertLessEqual(box["right"], 320)
                self.assertLessEqual(box["overflow"], 0)

    def test_trying_again_asks_only_the_worker_and_leaves_the_rest_of_the_address(self):
        label = self.seen["adres"]["label"]
        self.assertEqual(label["again"], {"klasse": "A+", "label": 1, "pdok": 0})
        self.assertEqual(label["other"]["bag"], 1)
        self.assertIn("Bestemming Wonen", label["other"]["plan"])
        self.assertGreater(label["other"]["notices"], 0)

    def test_address_tab_marks_the_energy_label_as_not_available_with_a_link(self):
        seen = self.seen["adres"]
        self.assertTrue(seen["energy"]["text"].startswith("Nog niet beschikbaar in de app."))
        self.assertEqual(seen["energy"]["links"], ["https://www.ep-online.nl/Energylabel/Search"])
        self.assertIn("Vul daar in: 5037PL 118 a.", seen["energy"]["text"])

    # --- The box "Bestemmingsplan en omgevingsplan". Ruimtelijke plannen (PDOK) is played back with
    # its real answer for the test address (adres_fixtures.json): an old plan without figures.

    PLAN_LINK = "https://omgevingswet.overheid.nl/regels-op-de-kaart/documenten?locatie-stelsel=RD&locatie-x=132133&locatie-y=395880"
    PLAN_WARNING = "Let op: wijzigingen sinds 1-1-2024 (Omgevingswet, omgevingsplan) ontbreken hier. Wat nu geldt, staat in Regels op de kaart van het Omgevingsloket."

    def test_the_plan_box_shows_the_zoning_its_plan_and_its_rules(self):
        plan = self.seen["adres"]["plan"]
        self.assertEqual(plan["uitkomst"], "gevonden")
        self.assertEqual(plan["facts"][0], {"Bestemming": "Wonen", "Plan": "Zorgvlied 2008", "Datum": "13-03-2009", "Status": "vigerend"})
        self.assertEqual(len(plan["facts"]), 1)
        self.assertIn("Dubbelbestemmingen: Waarde - Appartementen; Waarde - Flitsbezorging; Waarde - Parkeren; Waarde - Terrassen.", plan["text"])
        self.assertEqual(plan["links"], ["https://ruimtelijkeplannen.nl/documents/NL.IMRO.085500002008003e-/v_NL.IMRO.085500002008003e-_art11.html", self.PLAN_LINK])
        self.assertIn("Lees de regels van deze bestemming", plan["text"])
        self.assertIn("Niet getoond: 2 plannen die niet zijn vastgesteld of zijn vervallen (ontwerp, voorontwerp).", plan["text"])
        self.assertIn("Bron: Ruimtelijke plannen (Kadaster, via PDOK), opgevraagd op ", plan["text"])
        self.assertNotIn("Nog niet beschikbaar", plan["text"])
        self.assertEqual(plan["buttons"], [])
        self.assertLessEqual(plan["right"], 320)

    def test_the_plan_box_says_no_figure_is_not_no_limit_and_warns_right_after_the_zoning(self):
        plan = self.seen["adres"]["plan"]
        self.assertIn("Bij deze bestemming staat geen getal op de kaart. Geen getal op de kaart betekent niet: geen beperking.", plan["text"])
        # The zoning with its figures (here: the line that there are none), then at once the warning.
        self.assertEqual(plan["block"], ["feiten", "geen-getal", "stale plan-waarschuwing", "links"])
        self.assertEqual(plan["parts"][0], "planblok")
        self.assertEqual(plan["text"].count(self.PLAN_WARNING), 1)

    def test_a_plan_service_that_fails_or_is_gone_gives_a_message_not_an_empty_box(self):
        down = self.seen["adres"]["registersDown"]["plan"]
        self.assertEqual(down["uitkomst"], "onbereikbaar")
        self.assertTrue(down["text"].startswith("De kaart met bestemmingsplannen (Ruimtelijke plannen, via PDOK) antwoordt niet."), down["text"])
        self.assertEqual(down["buttons"], ["Opnieuw proberen"])
        self.assertEqual(down["links"], [self.PLAN_LINK], "de link naar Regels op de kaart hoort te blijven")
        again = self.seen["adres"]["afterRetry"]["plan"]
        self.assertEqual(again["facts"][0]["Bestemming"], "Wonen")
        gone = self.seen["adres"]["partsDown"]["plan"]
        self.assertEqual(gone["uitkomst"], "gestopt")
        self.assertIn("Mogelijk is hij verplaatst of gestopt.", gone["text"])
        self.assertEqual(gone["links"], [self.PLAN_LINK])
        odd = self.seen["adres"]["noNotices"]["plan"]
        self.assertEqual(odd["uitkomst"], "onbekend")
        self.assertIn("gaf een antwoord dat de app niet kent. Mogelijk is de dienst gewijzigd of gestopt.", odd["text"])
        self.assertEqual((odd["buttons"], odd["links"]), (["Opnieuw proberen"], [self.PLAN_LINK]))
        for case in (gone, odd):
            self.assertNotIn("Bestemming", [key for facts in case["facts"] for key in facts])

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

    # --- The address report on paper (rapport.js), in the print view, with the phone in the dark theme.

    def test_the_report_button_comes_with_an_address_and_says_how_to_get_a_pdf_on_an_iphone(self):
        report = self.seen["adres"]["rapport"]
        self.assertFalse(report["buttonBefore"])
        self.assertTrue(report["buttonAfter"])
        for part in ("Op een iPhone", "Delen", "Afdrukken", "twee vingers", "PDF", "Bewaar in Bestanden"):
            self.assertIn(part, report["explanation"])
        self.assertEqual(report["printed"], 1)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["elsewhere"], [], "het rapport vraagt iets op bij een andere dienst")

    def test_on_paper_only_the_report_without_bars_buttons_or_the_screen(self):
        paper = self.seen["adres"]["rapport"]["print"]
        self.assertTrue(paper["reportShown"])
        self.assertFalse(paper["tabs"], "de tabbalk staat op papier")
        self.assertFalse(paper["masthead"])
        self.assertFalse(paper["view"], "het scherm zelf staat ook op papier")
        self.assertEqual(paper["buttons"], 0)
        self.assertEqual(paper["ids"], 0, "de kopie heeft de id's van het scherm")

    def test_the_report_is_light_whatever_the_theme_of_the_screen(self):
        paper = self.seen["adres"]["rapport"]["print"]
        self.assertEqual(paper["background"], "rgb(255, 255, 255)")
        self.assertEqual(paper["color"], "rgb(0, 0, 0)")
        self.assertEqual(paper["reportColor"], "rgb(0, 0, 0)")

    def test_the_report_has_its_parts_in_order_and_every_box_of_the_tab(self):
        paper = self.seen["adres"]["rapport"]["print"]
        self.assertEqual(paper["title"], "Adresrapport")
        self.assertEqual(paper["address"], self.seen["adres"]["name"])
        self.assertRegex(paper["when"], r"^Opgevraagd op \d{1,2} \w+ \d{4} om \d\d:\d\d\. Dit rapport is gemaakt op ")
        self.assertEqual(paper["headings"], ["Lees dit eerst"] + paper["vakken"] + ["Eigen aantekeningen", "Bronnen en beperkingen", "Links"])
        self.assertIn("Proefvak", paper["vakken"], "een vak dat later is toegevoegd, komt niet mee")
        self.assertTrue(paper["testBox"], "de verborgen waarschuwing van het nieuwe vak staat niet op papier")
        self.assertFalse(paper["onlyScreen"], "wat alleen voor het scherm is, staat op papier")
        self.assertEqual(paper["lines"], 8)
        self.assertTrue(all(stand.startswith("Opgevraagd op ") for stand in paper["stands"]))
        self.assertEqual(len(paper["stands"]), len(paper["vakken"]))

    def test_read_this_first_holds_the_four_warnings(self):
        first = " ".join(self.seen["adres"]["rapport"]["print"]["first"])
        for part in ("geen advies", "Wijzigingen sinds 1-1-2024", "Geen getal betekent niet: geen beperking", "Geen resultaat betekent alleen: niet gevonden in die bron"):
            self.assertIn(part, first)

    def test_every_warning_and_source_of_the_screen_is_on_paper_readable(self):
        paper = self.seen["adres"]["rapport"]["print"]
        self.assertGreaterEqual(paper["warningCount"], 10)
        self.assertEqual(paper["missingWarnings"], [])
        self.assertEqual(paper["hiddenInReport"], 0)
        # 8 points is 10.67 CSS pixels: no warning or source line is smaller than that.
        self.assertGreaterEqual(paper["smallestFont"], 10.6, "een waarschuwing of bronregel is kleiner dan 8 punt")
        # What is folded on the screen (the same street, without house number) is open on paper.
        self.assertEqual(paper["streetRows"], 1)
        self.assertEqual(paper["liveDetailsOpen"], 0, "het scherm zelf is opengeklapt")

    def test_links_are_readable_text_together_at_the_end(self):
        paper = self.seen["adres"]["rapport"]["print"]
        self.assertEqual(paper["anchors"], 0)
        self.assertEqual(paper["missingLinks"], [])
        self.assertEqual(paper["linkCount"], paper["liveLinkCount"])
        self.assertEqual(paper["refs"], paper["linkCount"])

    def test_sources_and_limitations_list_every_box_with_the_moment_it_was_asked(self):
        paper = self.seen["adres"]["rapport"]["print"]
        sources = paper["sources"]
        self.assertTrue(sources[0].startswith("Adres: PDOK Locatieserver (Kadaster), opgevraagd op "))
        for name in paper["vakken"]:
            with self.subTest(vak=name):
                self.assertEqual(len([line for line in sources if line.startswith(name + ": opgevraagd op ")]), 1)
        self.assertTrue(any(line.startswith("Berichten van de app: laatst ververst op ") for line in sources))
        self.assertTrue(any("Bron: EP-Online" in line for line in sources))
        self.assertTrue(any("Bron: Ruimtelijke plannen" in line for line in sources))

    def test_boxes_are_not_broken_and_the_paper_is_a4(self):
        report = self.seen["adres"]["rapport"]
        self.assertTrue(report["print"]["unbroken"])
        # Only a box with many notices or list items may run over a page; the lists at the end may too.
        self.assertEqual([name for name in report["print"]["longBoxes"] if name not in ("Bronnen en beperkingen", "Links")], ["Publicaties over dit adres"])
        self.assertGreaterEqual(report["pdfPages"], 2)
        # Compact: the test address with every box and a test box was six pages on 20-11-2026.
        self.assertLessEqual(report["pdfPages"], 5)

    def test_the_title_holds_the_address_only_while_printing(self):
        report = self.seen["adres"]["rapport"]
        self.assertEqual(report["titleBefore"], "Tilburg Signalen")
        self.assertRegex(report["titleWhilePrinting"], r"^Adresrapport " + re.escape(self.seen["adres"]["name"]) + r" \d{4}-\d\d-\d\d$")
        self.assertEqual(report["titleAfter"], "Tilburg Signalen")

    def test_printing_through_the_menu_builds_the_report_and_a_change_throws_the_copy_away(self):
        report = self.seen["adres"]["rapport"]
        self.assertEqual(report["afterChange"], {"built": False, "children": 0})
        self.assertTrue(report["viewAfterChange"])
        self.assertTrue(report["viaMenu"]["built"])
        self.assertTrue(report["viaMenu"]["shown"])
        self.assertTrue(report["viaMenu"]["title"].startswith("Adresrapport "))

    def test_another_tab_prints_without_the_report(self):
        other = self.seen["adres"]["rapport"]["otherTab"]
        self.assertEqual(other["report"], "none")
        self.assertNotEqual(other["view"], "none")
        self.assertEqual(other["tabs"], "none")

    # --- The location report (adres-app.js, rapport.js): from a card, the tab "Adres" filled from
    # the notice, on paper with the same set-up. Made-up notices about the public test address.

    def test_the_location_report_starts_from_a_card_and_fills_the_tab(self):
        places = self.seen["adres"]["locatie"]
        self.assertEqual(places["errors"], [])
        self.assertEqual(places["elsewhere"], [], "het locatierapport vraagt iets op bij een andere dienst")
        for name in ("adres", "punt", "benaderd", "gemeente", "weg"):
            with self.subTest(locatie=name):
                screen = places[name]["screen"]
                self.assertEqual((screen["rapport"], screen["hash"], screen["input"]), ("locatie", "#adres", ""))
                self.assertEqual(screen["vakken"][0], "Bekendmaking")
                self.assertEqual(screen["failed"], 0)
                self.assertLessEqual(screen["overflow"], 0)
                self.assertTrue(screen["title"].startswith("Proeflocatie"))
                self.assertEqual(set(screen["facts"]), {"Soort", "Gemeente", "Datum", "Plek"})
                self.assertEqual(screen["links"], ["https://zoek.officielebekendmakingen.nl/test-locatie-%s.html" % name])
                self.assertTrue(any(note.startswith("Bron: Gemeenteblad Tilburg, gepubliceerd op ") for note in screen["notes"]))
        self.assertEqual(places["printed"], 5)

    def test_a_notice_with_one_address_gets_every_box_of_the_address(self):
        found = self.seen["adres"]["locatie"]["adres"]["screen"]
        self.assertEqual(found["vakken"], ["Bekendmaking", "Pand (BAG)", "Kadastraal perceel", "Publicaties over dit adres", "Energielabel", "Bestemmingsplan en omgevingsplan"])
        self.assertEqual((found["name"], found["sub"]), (self.seen["adres"]["name"], self.seen["adres"]["sub"]))
        self.assertIn("Adres afgeleid uit de tekst van de bekendmaking", " ".join(found["notes"]))
        self.assertEqual(found["warnings"], [])

    def test_the_notice_is_summarised_not_copied(self):
        found = self.seen["adres"]["locatie"]["adres"]["screen"]
        self.assertTrue(found["summary"].startswith("Uit de omschrijving: Proeflocatie."))
        self.assertTrue(found["summary"].endswith(" …"))
        self.assertLess(len(found["summary"]), 320)
        self.assertNotIn("want de volledige tekst staat daar", found["text"])

    def test_a_notice_without_one_address_uses_its_point_and_says_so(self):
        point = self.seen["adres"]["locatie"]["punt"]["screen"]
        self.assertEqual(point["vakken"], ["Bekendmaking", "Kadastraal perceel", "Bestemmingsplan en omgevingsplan"])
        self.assertEqual(point["plan"], "gevonden")
        text = " ".join(point["warnings"])
        self.assertIn("Geen eenduidig adres.", text)
        self.assertIn("beperkte nauwkeurigheid", text)
        self.assertIn("Pand (BAG), energielabel en publicaties over het adres zijn daarom overgeslagen.", text)
        self.assertTrue(any(note.startswith("Dit is het perceel op het punt uit de bekendmaking.") for note in point["parcelNote"]))

    def test_an_uncertain_place_or_class_gets_a_clear_warning(self):
        places = self.seen["adres"]["locatie"]
        approximate = " ".join(places["benaderd"]["screen"]["warnings"])
        self.assertIn("De plek is niet vastgesteld.", approximate)
        self.assertEqual(places["benaderd"]["screen"]["vakken"], ["Bekendmaking"])
        municipality = " ".join(places["gemeente"]["screen"]["warnings"])
        self.assertIn("De plek is niet vastgesteld. De bekendmaking noemt alleen de gemeente Tilburg.", municipality)
        self.assertIn("Onzeker bericht (op het kaartje een witte cirkel)", municipality)
        self.assertEqual(places["gemeente"]["screen"]["vakken"], ["Bekendmaking"])
        self.assertIn("Onzeker bericht (op het kaartje een witte cirkel)", " ".join(places["punt"]["screen"]["warnings"]))

    def test_a_filtered_out_notice_only_behind_the_switch(self):
        places = self.seen["adres"]["locatie"]
        self.assertEqual(places["removedHidden"], 0, "een weggefilterd bericht is te zien zonder de schakelaar")
        self.assertIn("Dit bericht is in de ranglijst weggefilterd", " ".join(places["weg"]["screen"]["warnings"]))

    def test_the_location_report_on_paper(self):
        places = self.seen["adres"]["locatie"]
        for name in ("adres", "punt", "benaderd", "gemeente", "weg"):
            with self.subTest(locatie=name):
                paper, screen = places[name]["paper"], places[name]["screen"]
                self.assertEqual(paper["h1"], "Locatierapport")
                self.assertEqual(paper["headings"], ["Lees dit eerst"] + screen["vakken"] + ["Eigen aantekeningen", "Bronnen en beperkingen", "Links"])
                self.assertEqual(len(paper["first"]), 5)
                self.assertIn("De volledige tekst", paper["first"][-1])
                self.assertEqual(paper["missing"], [], "een waarschuwing of bron van het scherm staat niet op papier")
                self.assertEqual(paper["hidden"], 0)
                self.assertTrue(paper["shown"])
                self.assertFalse(paper["tabs"])
                self.assertTrue(paper["title"].startswith("Locatierapport "))
                self.assertTrue(paper["sources"][0].startswith("Adres: afgeleid uit de bekendmaking, opgevraagd op "))
                self.assertTrue(any(line.startswith("Bekendmaking: opgevraagd op ") for line in paper["sources"]))
                self.assertIn("https://zoek.officielebekendmakingen.nl/test-locatie-%s.html" % name, paper["urls"])
        self.assertLessEqual(places["adres"]["pdfPages"], 5)

    def test_a_typed_address_after_a_location_report_is_an_address_report_again(self):
        after = self.seen["adres"]["locatie"]["daarna"]
        self.assertEqual(after, {"rapport": None, "notice": False, "vakken": 5})

if __name__ == "__main__":
    unittest.main()
