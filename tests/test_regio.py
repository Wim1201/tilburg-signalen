"""Tests for the regions around the core: the list of municipalities in config.json, how a notice
gets its region when it is fetched, and what the app shows for a choice of regions (site/logic.js).
The region choice on the page itself is tested in a real browser by tests/test_site.py (InDeBrowser).

No network. The logic tests run site/logic.js under Node and are skipped when Node is missing."""
import datetime
import json
import os
import shutil
import subprocess
import unittest
import xml.etree.ElementTree as ET

from signalen import bekendmakingen, gebied, http, update

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
NODE = shutil.which("node")

with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as _handle:
    CONFIG = json.load(_handle)
with open(os.path.join(SITE, "data", "gebied.json"), encoding="utf-8") as _handle:
    GEBIED = json.load(_handle)

# The division of the CBS, "Gebieden in Nederland 2026" (table 86247NED), read on 17-11-2026:
# COROP areas Midden-Noord-Brabant and West-Noord-Brabant, and the province of Zeeland.
CBS = {
    "Midden-Brabant": {"Alphen-Chaam", "Altena", "Baarle-Nassau", "Dongen", "Gilze en Rijen", "Goirle", "Hilvarenbeek", "Loon op Zand",
                       "Oisterwijk", "Tilburg", "Waalwijk"},
    "West-Brabant": {"Bergen op Zoom", "Breda", "Drimmelen", "Etten-Leur", "Geertruidenberg", "Halderberge", "Moerdijk", "Oosterhout",
                     "Roosendaal", "Rucphen", "Steenbergen", "Woensdrecht", "Zundert"},
    "Zeeland": {"Borsele", "Goes", "Hulst", "Kapelle", "Middelburg", "Noord-Beveland", "Reimerswaal", "Schouwen-Duiveland", "Sluis",
                "Terneuzen", "Tholen", "Veere", "Vlissingen"},
}
# The core as it was before the regions: the Dutch municipalities within 15 km of the centre.
KERN = {"Tilburg", "Hilvarenbeek", "Goirle", "Oisterwijk", "Loon op Zand", "Gilze en Rijen", "Dongen", "Alphen-Chaam", "Heusden", "Oirschot",
        "Vught", "Boxtel", "Waalwijk", "Baarle-Nassau", "Oosterhout", "Reusel-De Mierden"}


class Gemeentelijst(unittest.TestCase):
    """The list in config.json: every municipality once, with a region label."""

    def setUp(self):
        self.entries = CONFIG["gemeenten"]
        self.by_name = {entry["naam"]: entry for entry in self.entries}

    def test_every_municipality_once_with_a_known_label(self):
        names = [entry["naam"] for entry in self.entries]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(CONFIG["regios"], ["Midden-Brabant", "West-Brabant", "Zeeland"])
        for entry in self.entries:
            with self.subTest(gemeente=entry["naam"]):
                self.assertIn(entry["regio"], ["kern"] + CONFIG["regios"])
                self.assertLessEqual(set(entry), {"naam", "regio", "buiten_straal", "opmerking"})

    def test_core_is_the_core_as_it_was(self):
        self.assertEqual({entry["naam"] for entry in self.entries if entry["regio"] == "kern"}, KERN)
        self.assertEqual((CONFIG["straal_km"], CONFIG["centrum"]["naam"]), (15, "De Heuvel, Tilburg-centrum"))
        self.assertEqual(CONFIG["venster_dagen"], {"vergunning": 42, "plan": 180, "faillissement": 28, "verkoop": 120})

    def test_regions_are_the_division_of_the_cbs(self):
        for regio, expected in CBS.items():
            with self.subTest(regio=regio):
                # A municipality of the core that belongs to the region says so for the part outside the radius.
                whole = {entry["naam"] for entry in self.entries if entry["regio"] == regio}
                rest = {entry["naam"] for entry in self.entries if entry.get("buiten_straal") == regio}
                self.assertEqual(whole | rest, expected)
                self.assertFalse(whole & rest)
                self.assertLessEqual(rest, KERN)
        self.assertEqual(len(self.entries), len(KERN | set().union(*CBS.values())))
        self.assertEqual(len(self.entries), 42)

    def test_core_municipalities_outside_the_three_regions_stay_within_the_radius(self):
        without = {entry["naam"] for entry in self.entries if entry["regio"] == "kern" and "buiten_straal" not in entry}
        self.assertEqual(without, {"Heusden", "Oirschot", "Vught", "Boxtel", "Reusel-De Mierden"})

    def test_a_limited_municipality_says_why(self):
        self.assertIn("Aanvragen ontbreken", self.by_name["Roosendaal"]["opmerking"])
        self.assertEqual([entry["naam"] for entry in self.entries if "opmerking" in entry], ["Roosendaal"])


class GebiedMetRegios(unittest.TestCase):
    """site/data/gebied.json, and how gebied.py adds the regions to the core."""

    def test_file_has_every_listed_municipality_with_its_label(self):
        dutch = {g["naam"]: g for g in GEBIED["gemeenten"] if g["land"] == "NL"}
        self.assertEqual(set(dutch), {entry["naam"] for entry in CONFIG["gemeenten"]})
        self.assertEqual(GEBIED["regios"], CONFIG["regios"])
        for entry in CONFIG["gemeenten"]:
            with self.subTest(gemeente=entry["naam"]):
                found = dutch[entry["naam"]]
                self.assertEqual(found["regio"], entry["regio"])
                self.assertEqual(found.get("buitenStraal"), entry.get("buiten_straal"))
                self.assertEqual(found.get("opmerking"), entry.get("opmerking"))

    def test_core_is_within_the_radius_and_the_rest_is_not(self):
        radius = GEBIED["straalKm"]
        for found in GEBIED["gemeenten"]:
            with self.subTest(gemeente=found["naam"]):
                if found["regio"] == "kern":
                    self.assertLessEqual(found["minKm"], radius)
                    self.assertIn(found["dekking"], ("geheel", "gedeeltelijk"))
                else:
                    self.assertGreater(found["minKm"], radius)
                    self.assertEqual((found["dekking"], found["woonplaatsen"]), ("buiten", []))
                self.assertLessEqual(found["minKm"], found["maxKm"])
        self.assertEqual(sum(1 for g in GEBIED["gemeenten"] if g["regio"] == "kern"), 17)  # 16 Dutch and Ravels
        self.assertEqual([g["minKm"] for g in GEBIED["gemeenten"]], sorted(g["minKm"] for g in GEBIED["gemeenten"]))

    @staticmethod
    def square(name, x, y, province="Zeeland"):
        ring = [[x, y], [x + 1000, y], [x + 1000, y + 1000], [x, y + 1000], [x, y]]
        return {"properties": {"naam": name, "identificatie": "GM0001", "ligt_in_provincie_naam": province},
                "geometry": {"type": "Polygon", "coordinates": [ring]}}

    def test_regions_are_added_and_the_core_is_only_labelled(self):
        config = {"gemeenten": [{"naam": "Tilburg", "regio": "kern", "buiten_straal": "Midden-Brabant"}, {"naam": "Vught", "regio": "kern"},
                                {"naam": "Middelburg", "regio": "Zeeland", "opmerking": "Let op."},
                                {"naam": "Oosterhout", "regio": "West-Brabant"}]}
        core = {"Tilburg": {"naam": "Tilburg", "land": "NL", "minKm": 0.0}, "Vught": {"naam": "Vught", "land": "NL", "minKm": 10.3},
                "Oosterhout": {"naam": "Oosterhout", "land": "NL", "minKm": 12.9}, "Ravels": {"naam": "Ravels", "land": "BE", "minKm": 8.7}}
        asked = []

        def fetch(name):
            asked.append(name)
            return self.square(name, 31000, 393000)

        added = gebied.regions(config, core, (134458.696, 396511.411), 15000, fetch)
        self.assertEqual(asked, ["Middelburg"])  # what lies in the core is not asked for again
        self.assertEqual([(g["regio"], g.get("buitenStraal")) for g in core.values()],
                         [("kern", "Midden-Brabant"), ("kern", None), ("kern", None), ("kern", None)])
        self.assertEqual(len(added), 1)
        found = added[0]
        self.assertEqual((found["naam"], found["regio"], found["dekking"], found["woonplaatsen"], found["opmerking"], found["land"]),
                         ("Middelburg", "Zeeland", "buiten", [], "Let op.", "NL"))
        self.assertAlmostEqual(found["minKm"], 102.5, delta=0.5)
        self.assertNotIn("_binnen", found)

    def test_a_listed_municipality_that_does_not_exist_stops_the_step(self):
        config = {"gemeenten": [{"naam": "Bestaat Niet", "regio": "Zeeland"}]}
        with self.assertRaises(RuntimeError):
            gebied.regions(config, {}, (134458.696, 396511.411), 15000, lambda name: None)


NS = ('xmlns:dcterms="http://purl.org/dc/terms/" xmlns:ow="http://standaarden.overheid.nl/wetgeving/" '
      'xmlns:gzd="http://standaarden.overheid.nl/sru"')
CENTRE = (134458.696, 396511.411)
AREA = {
    "Tilburg": {"naam": "Tilburg", "minKm": 0.0, "regio": "kern", "buitenStraal": "Midden-Brabant"},
    "Oosterhout": {"naam": "Oosterhout", "minKm": 12.9, "regio": "kern", "buitenStraal": "West-Brabant"},
    "Vught": {"naam": "Vught", "minKm": 10.3, "regio": "kern", "buitenStraal": None},
    "Breda": {"naam": "Breda", "minKm": 15.2, "regio": "West-Brabant", "buitenStraal": None},
    "Middelburg": {"naam": "Middelburg", "minKm": 93.4, "regio": "Zeeland", "buitenStraal": None},
}


def record(creator, markers="", title="Aanvraag omgevingsvergunning, Teststraat 1", rubric="omgevingsvergunning"):
    return ET.fromstring(f"""<record {NS}>
      <dcterms:identifier>gmb-2026-1</dcterms:identifier><dcterms:title>{title}</dcterms:title>
      <dcterms:type scheme="OVERHEIDop.Rubriek">{rubric}</dcterms:type>
      <dcterms:creator>{creator}</dcterms:creator><dcterms:date>2026-11-13</dcterms:date>
      <ow:publicatienaam>Gemeenteblad</ow:publicatienaam>{markers}
      <gzd:preferredUrl>https://zoek.officielebekendmakingen.nl/gmb-2026-1.html</gzd:preferredUrl>
    </record>""")


def marker(wkt, gemeente=None, label="Teststraat 1"):
    where = f"<ow:ligtInGemeente>{gemeente}</ow:ligtInGemeente>" if gemeente else ""
    return (f"<ow:gebiedsmarkering><ow:Punt><ow:geometrie>{wkt}</ow:geometrie><ow:geometrielabel>{label}"
            f"</ow:geometrielabel>{where}</ow:Punt></ow:gebiedsmarkering>")


def never(*args):
    raise AssertionError("er wordt een locatie opgezocht voor een bericht buiten de kern")


def item(creator, markers="", geocode=lambda title, gemeente: None, area=AREA, **extra):
    return bekendmakingen.to_item(record(creator, markers, **extra), CENTRE, 15000, area, geocode, never)


class RegioVanEenBericht(unittest.TestCase):
    """A notice within the radius is the core, as before; outside it, the region of its municipality."""

    def test_within_the_radius_is_the_core_whatever_the_municipality(self):
        found = item("Tilburg", marker("POINT (134400 396600)", "Tilburg"))
        self.assertEqual((found["regio"], found["afstandKm"], found["locatieSoort"]), ("kern", 0.1, "exact"))
        found = item("Oosterhout", marker("POINT (122000 403000)", "Oosterhout"))  # the sliver of Oosterhout in the core
        self.assertEqual((found["regio"], found["afstandKm"]), ("kern", 14.0))

    def test_municipality_of_a_region_counts_whole(self):
        breda = item("Breda", marker("POINT (112000 400000)", "Breda"))
        self.assertEqual((breda["regio"], breda["gemeente"], breda["afstandKm"], breda["locatieSoort"]), ("West-Brabant", "Breda", 22.7, "exact"))
        zeeland = item("Middelburg", marker("POINT (31425.025 393778.813)", "Middelburg"))
        self.assertEqual((zeeland["regio"], zeeland["afstandKm"]), ("Zeeland", 103.1))
        self.assertAlmostEqual(zeeland["lat"], 51.5194, places=3)  # the place itself, not a point pulled to the circle
        self.assertAlmostEqual(zeeland["lon"], 3.6066, places=3)

    def test_rest_of_a_core_municipality_belongs_to_its_region(self):
        found = item("Oosterhout", marker("POINT (118000 407000)", "Oosterhout"))
        self.assertEqual((found["regio"], found["afstandKm"]), ("West-Brabant", 19.5))

    def test_core_municipality_without_a_region_still_stops_at_the_radius(self):
        self.assertIsNone(item("Vught", marker("POINT (150000 409000)", "Vught")))

    def test_unknown_municipality_outside_the_radius_is_dropped_without_a_lookup(self):
        self.assertIsNone(item("Rijkswaterstaat", marker("POINT (92000 437000)", "Rotterdam")))
        self.assertIsNone(item("Rijkswaterstaat", marker("POINT (92000 437000)")))  # `never` would raise on a lookup

    def test_notice_of_another_authority_in_a_region_municipality_counts_too(self):
        found = item("Noord-Brabant", marker("POINT (112000 400000)", "Breda"))
        self.assertEqual((found["regio"], found["overheid"], found["gemeente"]), ("West-Brabant", "Noord-Brabant", "Breda"))

    def test_notice_without_a_location_takes_the_label_of_its_municipality(self):
        zeeland = item("Middelburg")
        self.assertEqual((zeeland["regio"], zeeland["locatieSoort"], zeeland["afstandKm"], zeeland["lat"]), ("Zeeland", "gemeente", 93.4, None))
        core = item("Oosterhout")
        self.assertEqual((core["regio"], core["locatieSoort"], core["afstandKm"]), ("kern", "gemeente", 12.9))

    def test_location_from_the_title_decides_as_a_real_location_does(self):
        def breda(title, gemeente):
            return "omgeving Teststraat, Breda", (112000.0, 400000.0)

        found = item("Breda", geocode=breda)
        self.assertEqual((found["regio"], found["locatieSoort"], found["afstandKm"]), ("West-Brabant", "benaderd", 22.7))
        self.assertIsNone(item("Vught", geocode=lambda title, gemeente: ("omgeving X, Vught", (150000.0, 409000.0))))
        self.assertEqual(item("Vught", geocode=lambda title, gemeente: ("omgeving X, Vught", (140000.0, 400000.0)))["regio"], "kern")

    def test_area_from_before_the_regions_behaves_as_before(self):
        old = {"Tilburg": {"naam": "Tilburg", "minKm": 0.0}, "Dongen": {"naam": "Dongen", "minKm": 8.2}}
        self.assertEqual(item("Tilburg", marker("POINT (134400 396600)", "Tilburg"), area=old)["regio"], "kern")
        self.assertIsNone(item("Dongen", marker("POINT (118000 407000)", "Dongen"), area=old))
        self.assertEqual(item("Dongen", area=old)["regio"], "kern")

    def test_region_of_a_location_outside_the_radius(self):
        self.assertEqual([bekendmakingen.region_outside(name, AREA) for name in ("Tilburg", "Oosterhout", "Vught", "Breda", "Middelburg", "Rotterdam", None)],
                         ["Midden-Brabant", "West-Brabant", None, "West-Brabant", "Zeeland", None, None])


class Verversing(unittest.TestCase):
    """What a run writes: every notice has a region, and refused requests are counted."""

    def test_sources_that_only_cover_the_core_are_labelled_as_core(self):
        def notice(id, **extra):
            return dict({"id": id, "datum": "2026-11-13", "afstandKm": 1.0}, **extra)

        config = {"venster_dagen": {"vergunning": 42}, "centrum": {}, "straal_km": 15, "drempel_perceel_m2": 400}
        fetchers = {"officielebekendmakingen": lambda: [notice("a", regio="Zeeland", afstandKm=100.0), notice("b", regio="kern")],
                    "omgevingsloket-vlaanderen": lambda: [notice("vl-1")], "staatscourant-insolventies": lambda: [notice("f-1")]}
        now = datetime.datetime(2026, 11, 17, 9, 0, tzinfo=datetime.timezone.utc)
        document = update.run(config, {"gemeenten": []}, now, fetchers=fetchers, verrijker=lambda items: (items, {}), dagcontrole=lambda moment: [])
        self.assertEqual({entry["id"]: entry["regio"] for entry in document["berichten"]}, {"a": "Zeeland", "b": "kern", "vl-1": "kern", "f-1": "kern"})

    def test_output_is_split_into_the_core_and_one_file_per_region(self):
        def notice(id, regio, klasse="weggefilterd"):
            return {"id": id, "regio": regio, "klasse": klasse}

        document = {"bijgewerkt": "2026-11-17T09:00:00+01:00", "straalKm": 15, "berichten": [
            notice("k1", "kern", "ontwikkellocatie"), notice("z1", "Zeeland", "ontwikkellocatie"), notice("w1", "West-Brabant", "onzeker"),
            notice("k2", "kern"), notice("z2", "Zeeland"), {"id": "oud", "klasse": "weggefilterd"}]}
        core, files = update.verdeel(document, ["Midden-Brabant", "West-Brabant", "Zeeland"])
        self.assertEqual([entry["id"] for entry in core["berichten"]], ["k1", "k2", "oud"])  # the order of the run is kept
        self.assertEqual(core["straalKm"], 15)
        self.assertEqual(core["regios"], [
            {"naam": "Midden-Brabant", "bestand": "regio-midden-brabant.json", "berichten": 0, "locaties": 0, "onzeker": 0},
            {"naam": "West-Brabant", "bestand": "regio-west-brabant.json", "berichten": 1, "locaties": 0, "onzeker": 1},
            {"naam": "Zeeland", "bestand": "regio-zeeland.json", "berichten": 2, "locaties": 1, "onzeker": 0}])
        self.assertEqual(sorted(files), ["regio-midden-brabant.json", "regio-west-brabant.json", "regio-zeeland.json"])
        self.assertEqual(files["regio-zeeland.json"], {"regio": "Zeeland", "bijgewerkt": "2026-11-17T09:00:00+01:00",
                                                       "berichten": [notice("z1", "Zeeland", "ontwikkellocatie"), notice("z2", "Zeeland")]})
        self.assertEqual(files["regio-midden-brabant.json"]["berichten"], [])  # an empty region still gets its file
        self.assertEqual(len(document["berichten"]), 6, "het document van de run is gewijzigd")

    def test_without_regions_everything_stays_in_the_one_file(self):
        document = {"bijgewerkt": "x", "berichten": [{"id": "a", "regio": "kern", "klasse": "onzeker"}, {"id": "b", "regio": "Zeeland", "klasse": "onzeker"}]}
        core, files = update.verdeel(document, [])
        self.assertEqual((len(core["berichten"]), core["regios"], files), (2, [], {}))

    def test_refused_requests_are_counted_also_when_a_retry_succeeds(self):
        import io
        import urllib.error
        import urllib.request

        answers = [urllib.error.HTTPError("https://voorbeeld.test/x", 429, "Too Many Requests", {}, io.BytesIO(b"")), io.BytesIO(b"ok")]

        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake(request, timeout=None):
            answer = answers.pop(0)
            if isinstance(answer, Exception):
                raise answer
            return Response(answer.getvalue())

        real = urllib.request.urlopen
        http.GEWEIGERD.clear()
        urllib.request.urlopen = fake
        try:
            body = http.get("https://voorbeeld.test/x", slaap=lambda seconds: None)
        finally:
            urllib.request.urlopen = real
        self.assertEqual(body, b"ok")
        self.assertEqual(http.GEWEIGERD["voorbeeld.test"], 1)
        http.GEWEIGERD.clear()


def logic(*calls):
    done = subprocess.run([NODE, os.path.join(ROOT, "tests", "js", "run_logic.js")], input=json.dumps(calls), capture_output=True,
                          text=True, encoding="utf-8", timeout=60)
    if done.returncode:
        raise AssertionError(done.stderr)
    return json.loads(done.stdout)


def bericht(id, regio=None, klasse="ontwikkellocatie", km=5.0, gemeente="Tilburg"):
    base = {"id": id, "klasse": klasse, "afstandKm": km, "gemeente": gemeente, "score": 50, "datum": "2026-11-10"}
    if regio:
        base["regio"] = regio
    return base


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Regiofilter(unittest.TestCase):
    """What the app shows for a choice of regions. The core is always shown."""

    ITEMS = [bericht("k1", "kern"), bericht("oud"), bericht("k2", "kern", "weggefilterd"), bericht("w1", "West-Brabant", km=22.7, gemeente="Breda"),
             bericht("w2", "West-Brabant", "onzeker", km=41.2, gemeente="Roosendaal"), bericht("w3", "West-Brabant", "weggefilterd", km=19.5, gemeente="Oosterhout"),
             bericht("z1", "Zeeland", km=103.1, gemeente="Middelburg")]
    AREA = {"regios": ["Midden-Brabant", "West-Brabant", "Zeeland"], "gemeenten": [
        {"naam": "Tilburg", "regio": "kern", "buitenStraal": "Midden-Brabant", "dekking": "geheel"}, {"naam": "Ravels", "land": "BE"},
        {"naam": "Oosterhout", "regio": "kern", "buitenStraal": "West-Brabant", "dekking": "gedeeltelijk"},
        {"naam": "Breda", "regio": "West-Brabant"}, {"naam": "Roosendaal", "regio": "West-Brabant"}, {"naam": "Middelburg", "regio": "Zeeland"}]}

    @staticmethod
    def ids(entries):
        return [entry["id"] for entry in entries]

    @staticmethod
    def names(entries):
        return [entry["naam"] for entry in entries]

    OVERVIEW = [{"naam": "Midden-Brabant", "bestand": "regio-midden-brabant.json", "berichten": 0, "locaties": 0, "onzeker": 0},
                {"naam": "West-Brabant", "bestand": "regio-west-brabant.json", "berichten": 3, "locaties": 1, "onzeker": 1},
                {"naam": "Zeeland", "bestand": "regio-zeeland.json", "berichten": 1, "locaties": 1, "onzeker": 0}]

    def test_core_on_its_own_is_the_list_as_it_is(self):
        core = self.ITEMS[:3]
        alone, empty, label = logic(["merged", core, []], ["merged", core, [[], None]], ["regioOf", {"id": "x"}])
        self.assertEqual(alone, core)
        self.assertEqual(empty, core)
        self.assertEqual(label, "kern")  # data from before the regions has no label: core

    def test_a_chosen_region_is_merged_with_the_core_newest_first_then_nearest(self):
        core = [bericht("k-nieuw", "kern", km=9.0), bericht("k-oud", "kern", km=1.0)]
        core[0]["datum"], core[1]["datum"] = "2026-11-16", "2026-11-10"
        west = [bericht("w-nieuw", "West-Brabant", km=22.0), bericht("w-ver", "West-Brabant", km=40.0), bericht("w-oud", "West-Brabant", km=30.0)]
        west[0]["datum"], west[1]["datum"], west[2]["datum"] = "2026-11-16", "2026-11-16", "2026-11-03"
        zeeland = [bericht("z", "Zeeland", km=100.0)]
        zeeland[0]["datum"] = "2026-11-12"
        one, two = logic(["merged", core, [west]], ["merged", core, [west, zeeland]])
        self.assertEqual(self.ids(one), ["k-nieuw", "w-nieuw", "w-ver", "k-oud", "w-oud"])
        self.assertEqual(self.ids(two), ["k-nieuw", "w-nieuw", "w-ver", "z", "k-oud", "w-oud"])

    def test_choosing_leaves_the_data_as_it_is(self):
        script = ("var L = require(process.argv[1]); var items = JSON.parse(process.argv[2]); var area = JSON.parse(process.argv[3]);"
                  "var before = JSON.stringify([items, area]); L.merged(items.slice(0, 3), [items.slice(3)]); L.gemeentenIn(area, ['Zeeland']);"
                  "L.regios(area, []); L.regiosFor(area, 'Breda'); L.reachKm(items, 15); console.log(JSON.stringify([items, area]) === before ? 'gelijk' : 'gewijzigd');")
        done = subprocess.run([NODE, "-e", script, os.path.join(SITE, "logic.js"), json.dumps(self.ITEMS), json.dumps(self.AREA)],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(done.stdout.strip(), "gelijk", done.stderr)

    def test_municipalities_follow_the_choice(self):
        core, west, all_three = logic(["gemeentenIn", self.AREA, []], ["gemeentenIn", self.AREA, ["West-Brabant"]],
                                      ["gemeentenIn", self.AREA, ["Midden-Brabant", "West-Brabant", "Zeeland"]])
        self.assertEqual(self.names(core), ["Tilburg", "Ravels", "Oosterhout"])
        self.assertEqual(self.names(west), ["Tilburg", "Ravels", "Oosterhout", "Breda", "Roosendaal"])
        self.assertEqual(self.names(all_three), self.names(self.AREA["gemeenten"]))

    def test_regions_on_offer_say_what_they_add(self):
        offered, = logic(["regios", self.AREA, self.OVERVIEW])
        self.assertEqual(offered, [
            {"naam": "Midden-Brabant", "bestand": "regio-midden-brabant.json", "berichten": 0, "locaties": 0, "onzeker": 0, "gemeenten": 0},
            {"naam": "West-Brabant", "bestand": "regio-west-brabant.json", "berichten": 3, "locaties": 1, "onzeker": 1, "gemeenten": 2},
            {"naam": "Zeeland", "bestand": "regio-zeeland.json", "berichten": 1, "locaties": 1, "onzeker": 0, "gemeenten": 1}])

    def test_data_from_before_the_regions_offers_no_choice(self):
        old_area = {"gemeenten": [{"naam": "Tilburg"}, {"naam": "Dongen"}]}
        results = logic(["regios", old_area, None], ["regios", self.AREA, None], ["regios", self.AREA, [{"naam": "Zeeland"}, None]],
                        ["gemeentenIn", old_area, ["Zeeland"]], ["regiosFor", old_area, "Tilburg"])
        self.assertEqual(results[:3], [[], [], []])  # a region without a file cannot be chosen
        self.assertEqual(self.names(results[3]), ["Tilburg", "Dongen"])
        self.assertEqual(results[4], [])

    def test_regions_that_can_hold_notices_about_a_municipality(self):
        results = logic(["regiosFor", self.AREA, "Breda"], ["regiosFor", self.AREA, "Middelburg"], ["regiosFor", self.AREA, "Oosterhout"],
                        ["regiosFor", self.AREA, "Tilburg"], ["regiosFor", self.AREA, "Ravels"], ["regiosFor", self.AREA, "Amsterdam"])
        # Oosterhout lies in the core, but what is outside the radius is in the file of West-Brabant.
        # Tilburg lies wholly within the radius: there is nothing of it in the file of its region.
        self.assertEqual(results, [["West-Brabant"], ["Zeeland"], ["West-Brabant"], [], [], []])

    def test_distance_filter_reaches_as_far_as_what_is_shown(self):
        core, west, zeeland, empty = logic(["reachKm", self.ITEMS[:3], 15], ["reachKm", self.ITEMS[:6], 15], ["reachKm", self.ITEMS, 15], ["reachKm", [], 15])
        self.assertEqual((core, west, zeeland, empty), (15, 42, 104, 15))

    def test_names_in_a_sentence(self):
        lines = logic(["nameList", ["Zeeland"]], ["nameList", ["Midden-Brabant", "Zeeland"]], ["nameList", ["Midden-Brabant", "West-Brabant", "Zeeland"]], ["nameList", []])
        self.assertEqual(lines, ["Zeeland", "Midden-Brabant en Zeeland", "Midden-Brabant, West-Brabant en Zeeland", ""])


class EchteGegevens(unittest.TestCase):
    """site/data/berichten.json and the region files next to it, as they are in the repository.

    berichten.json there is the snapshot of 16-11-2026 that the video was made with (tests/test_video.py
    depends on it); only the overview of the regions was added to it. The region files are those of
    the measured run of 17-11-2026. On the live site every run writes all of them anew."""

    @classmethod
    def setUpClass(cls):
        def read(name):
            with open(os.path.join(SITE, "data", name), encoding="utf-8") as handle:
                return json.load(handle)
        cls.data = read("berichten.json")
        cls.core = cls.data["berichten"]
        cls.files = {regio["naam"]: read(regio["bestand"]) for regio in cls.data["regios"]}

    def test_core_file_holds_the_core_only_and_lists_the_regions(self):
        self.assertEqual({entry.get("regio", "kern") for entry in self.core}, {"kern"})
        self.assertEqual([regio["naam"] for regio in self.data["regios"]], CONFIG["regios"])
        self.assertEqual([regio["bestand"] for regio in self.data["regios"]], [update.regio_bestand(naam) for naam in CONFIG["regios"]])
        radius = self.data["straalKm"]
        for entry in self.core:
            self.assertLessEqual(entry["afstandKm"], radius, entry["id"])

    def test_every_region_file_holds_its_region_only_and_what_the_overview_says(self):
        radius = self.data["straalKm"]
        labels = {entry["naam"]: entry for entry in CONFIG["gemeenten"]}
        for regio in self.data["regios"]:
            file = self.files[regio["naam"]]
            with self.subTest(regio=regio["naam"]):
                items = file["berichten"]
                self.assertTrue(items, "geen berichten in deze regio")
                self.assertEqual(file["regio"], regio["naam"])
                self.assertEqual({entry["regio"] for entry in items}, {regio["naam"]})
                self.assertEqual((regio["berichten"], regio["locaties"], regio["onzeker"]),
                                 (len(items), sum(1 for e in items if e["klasse"] == "ontwikkellocatie"), sum(1 for e in items if e["klasse"] == "onzeker")))
                for entry in items:
                    self.assertGreaterEqual(entry["afstandKm"], radius, entry["id"])  # the distance is rounded to 100 m
                    listed = labels[entry["gemeente"]]
                    self.assertIn(regio["naam"], (listed["regio"], listed.get("buiten_straal")), entry["id"])
                self.assertEqual([entry["datum"] for entry in items], sorted((entry["datum"] for entry in items), reverse=True))

    def test_no_notice_is_in_two_files(self):
        ids = [entry["id"] for entry in self.core] + [entry["id"] for file in self.files.values() for entry in file["berichten"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_bankruptcies_and_the_flemish_source_stay_in_the_core(self):
        for file in self.files.values():
            for entry in file["berichten"]:
                self.assertNotEqual(entry["type"], "faillissement", entry["id"])
                self.assertEqual(entry["bron"], "officielebekendmakingen", entry["id"])

    def test_every_file_stays_small_enough_for_the_repository_and_the_phone(self):
        # tests/test_ververst.py keeps files above 1.5 MB out of the repository.
        for name in ["berichten.json"] + [regio["bestand"] for regio in self.data["regios"]]:
            with self.subTest(bestand=name):
                self.assertLess(os.path.getsize(os.path.join(SITE, "data", name)), 1_500_000)


if __name__ == "__main__":
    unittest.main()
