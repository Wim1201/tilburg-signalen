"""Tests for version 2 of the app: the ranking and the cards (site/logic.js), the house style
(site/styles.css), the mark and the icons, and what the page and the service worker refer to.

The logic tests run site/logic.js under Node and are skipped when Node is missing. The browser
test also needs Playwright and is skipped without it."""
import json
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

    def test_sorting_leaves_the_data_as_it_is(self):
        items = [item("a", 40), item("b", 100)]
        result, = logic(["sorted", items, "relevantie"])
        self.assertEqual(ids(result), ["b", "a"])
        self.assertEqual(ids(items), ["a", "b"])

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
        self.assertEqual(main[0]["score"], max(entry["score"] for entry in self.items))

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
        self.assertIn('fill="%s"' % light["--bar-bg"], read("icons", "icon.svg"))

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
        for prefix, names in (("view-", ["berichten", "gebied", "bronnen"]), ("tab-", ["berichten", "gebied", "bronnen"]),
                              ("tile-", ["ranglijst", "nieuw", "onzeker"])):
            wanted |= {prefix + name for name in names}
        self.assertGreater(len(wanted), 25)
        self.assertEqual(wanted - on_page, set())

    def test_logic_is_loaded_before_the_app(self):
        scripts = re.findall(r'<script src="([^"]+)"', self.html)
        self.assertEqual(scripts, ["logic.js", "app.js"])

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
    """The app in a real browser at phone size, with the data in the repository."""

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Quiet, directory=SITE))
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        try:
            done = subprocess.run([NODE, os.path.join(JS, "browser_smoke.js"), "http://127.0.0.1:%d" % cls.server.server_address[1]],
                                  capture_output=True, text=True, encoding="utf-8", timeout=180)
        finally:
            cls.server.shutdown()
            cls.server.server_close()
        if done.returncode:
            raise AssertionError(done.stderr)
        cls.seen = json.loads(done.stdout)
        cls.items = json.loads(read("data", "berichten.json"))["berichten"]
        cls.locations = sorted([entry for entry in cls.items if entry["klasse"] == "ontwikkellocatie"], key=lambda entry: -entry["score"])

    def test_no_errors_and_nothing_wider_than_the_phone(self):
        self.assertEqual(self.seen["errors"], [])
        self.assertLessEqual(self.seen["overflow"], 0)
        self.assertEqual(self.seen["mark"], 2)

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
        self.assertEqual(self.seen["removed"], min(60, len(removed)))
        self.assertEqual(self.seen["removedRank"], "–")

    def test_nothing_new_shows_the_illustration(self):
        self.assertEqual(self.seen["briefLater"], "Geen nieuwe ontwikkellocaties sinds je vorige bezoek.")
        self.assertEqual(self.seen["emptyTitle"], "Niets nieuws sinds je vorige bezoek.")
        self.assertEqual(self.seen["emptyArt"], 1)


if __name__ == "__main__":
    unittest.main()
