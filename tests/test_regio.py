"""Tests for the regions around the core: the list of municipalities in config.json, how a notice
gets its region when it is fetched, and what the app shows for a choice of regions (site/logic.js).
The region choice on the page itself is tested in a real browser by tests/test_site.py (InDeBrowser).

No network. The logic tests run site/logic.js under Node and are skipped when Node is missing."""
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

from signalen import bekendmakingen, cache as cachemodule, gebied, http, relevantie, update

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

    def test_no_municipality_is_limited_any_more(self):
        # Roosendaal had "Aanvragen ontbreken" until the other rubrics were read (19-11-2026).
        # The field stays possible (gebied.py passes it on), but no municipality needs it now.
        self.assertEqual([entry["naam"] for entry in self.entries if "opmerking" in entry], [])

    def test_the_other_rubrics_are_on_for_the_core_and_every_region(self):
        self.assertEqual(CONFIG["andere_rubrieken"], {name: True for name in ["kern"] + CONFIG["regios"]})


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


OTHER_AREA = {"gemeenten": [
    {"naam": "Tilburg", "land": "NL", "minKm": 0.0, "regio": "kern", "buitenStraal": "Midden-Brabant"},
    {"naam": "Dongen", "land": "NL", "minKm": 8.2, "regio": "kern", "buitenStraal": "Midden-Brabant"},
    {"naam": "Vught", "land": "NL", "minKm": 10.3, "regio": "kern", "buitenStraal": None},
    {"naam": "Roosendaal", "land": "NL", "minKm": 39.4, "regio": "West-Brabant", "buitenStraal": None},
    {"naam": "Middelburg", "land": "NL", "minKm": 93.4, "regio": "Zeeland", "buitenStraal": None},
    {"naam": "Ravels", "land": "BE", "minKm": 8.7, "regio": "kern"},
]}
OTHER_CONFIG = {"centrum": {"rd": list(CENTRE)}, "straal_km": 15, "regios": ["Midden-Brabant", "West-Brabant", "Zeeland"],
                "extra_overheden": [{"naam": "Waterschap Brabantse Delta", "soort": "waterschap"}]}
SINCE = {"vergunning": "2026-10-08", "plan": "2026-05-23"}


def notice_record(id, creator, rubric, title, wkt, gemeente):
    return ET.fromstring(f"""<record {NS}>
      <dcterms:identifier>{id}</dcterms:identifier><dcterms:title>{title}</dcterms:title>
      <dcterms:type scheme="OVERHEIDop.Rubriek">{rubric}</dcterms:type>
      <dcterms:creator>{creator}</dcterms:creator><dcterms:date>2026-11-13</dcterms:date>
      <ow:publicatienaam>Gemeenteblad</ow:publicatienaam>{marker(wkt, gemeente)}
      <gzd:preferredUrl>https://zoek.officielebekendmakingen.nl/{id}.html</gzd:preferredUrl>
    </record>""")


# Under its own rubric: one permit in Tilburg. Under the other rubrics: an application of Roosendaal
# (as Roosendaal publishes them), a draft of Middelburg, one of Dongen, and the same notice as the
# one in Tilburg (which the source does not do, but the run must not take it twice).
OWN = [notice_record("gmb-2026-10", "Tilburg", "omgevingsvergunning", "Verleende omgevingsvergunning, Teststraat 1",
                     "POINT (134458.696 399511.411)", "Tilburg")]
OTHER = [notice_record("gmb-2026-20", "Roosendaal", "andere beschikking",
                       "Ingediende aanvraag voor een Omgevingsvergunning op de locatie Teststraat 2", "POINT (95458.696 396511.411)", "Roosendaal"),
         notice_record("gmb-2026-21", "Middelburg", "andere beschikking",
                       "Ontwerpbesluit omgevingsvergunning Teststraat 3", "POINT (31000 393000)", "Middelburg"),
         notice_record("gmb-2026-22", "Dongen", "andere vergunning",
                       "Besluit op aanvraag omgevingsvergunning voor wijzigen van winkels in woningen", "POINT (134458.696 406511.411)", "Dongen"),
         notice_record("gmb-2026-10", "Tilburg", "andere beschikking", "Zelfde nummer, andere titel", "POINT (134458.696 399511.411)", "Tilburg")]


class AndereRubrieken(unittest.TestCase):
    """Permit notices that a municipality published under "andere beschikking" or "andere vergunning"."""

    def fetch(self, config=OTHER_CONFIG):
        queries, lookups = [], []

        def search(query):
            queries.append(query)
            if 'dt.type=="andere beschikking"' in query:
                return iter(OTHER)
            if 'dt.type=="omgevingsvergunning"' in query and "Staatscourant" not in query:
                return iter(OWN)
            return iter([])

        def lookup(*args):
            lookups.append(args)
            return None

        with mock.patch.object(bekendmakingen, "search", search), mock.patch.object(bekendmakingen, "geocode_title", lookup), \
                mock.patch.object(bekendmakingen, "reverse_gemeente", lookup):
            found = bekendmakingen.fetch(config, OTHER_AREA, SINCE)
        self.assertEqual(lookups, [], "alle testberichten hebben een locatie")
        return {entry["id"]: entry for entry in found}, [query for query in queries if 'dt.type=="andere beschikking"' in query]

    def test_query_asks_both_rubrics_with_the_word_in_the_title(self):
        query = bekendmakingen.build_other_query(["Dongen", "Roosendaal"], "2026-10-08")
        self.assertIn('(dt.type=="andere beschikking" OR dt.type=="andere vergunning")', query)
        self.assertIn('(dt.creator=="Dongen" OR dt.creator=="Roosendaal")', query)
        self.assertIn('dt.title any "omgevingsvergunning"', query)
        self.assertIn("dt.date>=2026-10-08", query)

    def test_one_extra_query_for_the_municipalities_only(self):
        _, queries = self.fetch()
        self.assertEqual(len(queries), 1)
        self.assertIn("dt.date>=2026-10-08", queries[0], "het venster van de vergunningen")
        for name in ["Tilburg", "Dongen", "Vught", "Roosendaal", "Middelburg"]:
            self.assertIn(f'dt.creator=="{name}"', queries[0])
        self.assertNotIn("Waterschap", queries[0])
        self.assertNotIn("Ravels", queries[0])

    def test_a_notice_under_another_rubric_is_a_permit_with_its_region(self):
        found, _ = self.fetch()
        self.assertEqual(sorted(found), ["gmb-2026-10", "gmb-2026-20", "gmb-2026-21", "gmb-2026-22"])
        self.assertEqual({id: (entry["type"], entry["regio"], entry["fase"]) for id, entry in found.items() if id != "gmb-2026-10"},
                         {"gmb-2026-20": ("vergunning", "West-Brabant", "Aanvraag"), "gmb-2026-21": ("vergunning", "Zeeland", "Ontwerpbesluit"),
                          "gmb-2026-22": ("vergunning", "kern", "Besluit")})

    def test_a_notice_that_came_in_under_its_own_rubric_is_not_taken_twice_or_changed(self):
        found, _ = self.fetch()
        self.assertEqual(found["gmb-2026-10"]["titel"], "Verleende omgevingsvergunning, Teststraat 1")

    def test_what_came_in_before_stays_exactly_as_it_was(self):
        off = dict(OTHER_CONFIG, andere_rubrieken={name: False for name in ["kern"] + OTHER_CONFIG["regios"]})
        before, queries = self.fetch(off)
        self.assertEqual(queries, [], "alles uit: geen extra zoekvraag")
        after, _ = self.fetch()
        self.assertEqual(sorted(before), ["gmb-2026-10"])
        self.assertEqual({id: entry for id, entry in after.items() if id in before}, before)

    def test_a_part_that_is_switched_off_is_not_asked_and_not_kept(self):
        found, queries = self.fetch(dict(OTHER_CONFIG, andere_rubrieken={"Zeeland": False}))
        self.assertNotIn("gmb-2026-21", found)
        self.assertIn("gmb-2026-20", found)
        self.assertNotIn('dt.creator=="Middelburg"', queries[0])
        found, queries = self.fetch(dict(OTHER_CONFIG, andere_rubrieken={"kern": False}))
        self.assertEqual(sorted(found), ["gmb-2026-10", "gmb-2026-20", "gmb-2026-21"])
        self.assertNotIn('dt.creator=="Vught"', queries[0], "Vught heeft geen deel buiten de straal")
        self.assertIn('dt.creator=="Dongen"', queries[0], "het deel van Dongen buiten de straal hoort bij Midden-Brabant")

    def test_a_part_that_is_not_listed_is_on(self):
        self.assertEqual(bekendmakingen.other_rubrics_on(OTHER_CONFIG), {"kern", "Midden-Brabant", "West-Brabant", "Zeeland"})
        self.assertEqual(bekendmakingen.other_rubrics_on(dict(OTHER_CONFIG, andere_rubrieken={"West-Brabant": False})),
                         {"kern", "Midden-Brabant", "Zeeland"})

    def test_titles_of_these_rubrics_get_their_phase(self):
        from signalen import classify
        self.assertEqual(classify.permit_phase("Ingediende aanvraag voor een Omgevingsvergunning op de locatie Teststraat 2"), "Aanvraag")
        self.assertEqual(classify.permit_phase("Verlengen beslistermijn aanvraag omgevingsvergunning Teststraat 2"), "Beslistermijn verlengd")
        self.assertEqual(classify.permit_phase("Intrekken omgevingsvergunning Teststraat 2"), "Ingetrokken of buiten behandeling")


class GrootteVanDeBestanden(unittest.TestCase):
    """The log line about the data files a run writes, with a warning from 90 percent of 1,5 MB."""

    def test_small_files_give_one_plain_line(self):
        lines = update.bestand_meldingen({"berichten.json": 1_036_760, "regio-west-brabant.json": 1_349_999})
        self.assertEqual(lines, ["  bestanden: berichten.json 1.037 kB (69 procent), regio-west-brabant.json 1.350 kB (89 procent)"])

    def test_from_90_percent_the_log_warns_per_file(self):
        lines = update.bestand_meldingen({"berichten.json": 1_036_760, "regio-west-brabant.json": 1_422_848, "regio-zeeland.json": 1_350_000})
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[1].startswith("::warning::regio-west-brabant.json is 1.423 kB, 94 procent van de 1.500 kB"))
        self.assertTrue(lines[2].startswith("::warning::regio-zeeland.json is 1.350 kB, 90 procent"))
        self.assertIn("De run gaat door", lines[1])
        self.assertIn("vernieuw de momentopname in de repository niet met een bestand boven 1.500 kB", lines[1])

    def test_the_warning_is_at_90_percent_of_the_limit_of_the_repository(self):
        self.assertEqual(update.BESTAND_WAARSCHUW_BYTES * 10, cachemodule.REPO_BYTES * 9)


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
            {"naam": "Midden-Brabant", "bestand": "regio-midden-brabant.json", "berichten": 0, "locaties": 0, "onzeker": 0, "ongelezen": 0, "mislukt": 0},
            {"naam": "West-Brabant", "bestand": "regio-west-brabant.json", "berichten": 1, "locaties": 0, "onzeker": 1, "ongelezen": 0, "mislukt": 0},
            {"naam": "Zeeland", "bestand": "regio-zeeland.json", "berichten": 2, "locaties": 1, "onzeker": 0, "ongelezen": 0, "mislukt": 0}])
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
            {"naam": "Midden-Brabant", "bestand": "regio-midden-brabant.json", "berichten": 0, "locaties": 0, "onzeker": 0, "ongelezen": 0, "mislukt": 0, "gemeenten": 0},
            {"naam": "West-Brabant", "bestand": "regio-west-brabant.json", "berichten": 3, "locaties": 1, "onzeker": 1, "ongelezen": 0, "mislukt": 0, "gemeenten": 2},
            {"naam": "Zeeland", "bestand": "regio-zeeland.json", "berichten": 1, "locaties": 1, "onzeker": 0, "ongelezen": 0, "mislukt": 0, "gemeenten": 1}])

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

    def test_a_chosen_region_reports_what_it_still_misses(self):
        overview = [dict(self.OVERVIEW[0]), dict(self.OVERVIEW[1], ongelezen=146, mislukt=20), dict(self.OVERVIEW[2], ongelezen=1, mislukt=1)]
        none, west, both, complete = logic(["regioMeldingen", overview, []], ["regioMeldingen", overview, ["West-Brabant"]],
                                           ["regioMeldingen", overview, ["Zeeland", "West-Brabant"]], ["regioMeldingen", overview, ["Midden-Brabant"]])
        self.assertEqual(none, [], "zonder gekozen regio meldt de app niets over de regio's")
        self.assertEqual(west, [
            'Van West-Brabant zijn 146 berichten nog niet gelezen. Ze staan onder Onzeker met "Tekst nog niet gelezen"; de volgende verversingen halen ze op.',
            "Bij de laatste verversing konden 20 bekendmakingen van West-Brabant niet volledig worden gelezen. Ze staan tijdelijk onder Onzeker; de volgende verversing probeert het opnieuw."])
        self.assertEqual(both[:2], west)
        self.assertEqual(both[2:], [
            'Van Zeeland is 1 bericht nog niet gelezen. Het staat onder Onzeker met "Tekst nog niet gelezen"; een volgende verversing haalt het op.',
            "Bij de laatste verversing kon 1 bekendmaking van Zeeland niet volledig worden gelezen. Ze staat tijdelijk onder Onzeker; de volgende verversing probeert het opnieuw."])
        self.assertEqual(complete, [])
        empty, old = logic(["regioMeldingen", None, ["Zeeland"]], ["regioMeldingen", [{"naam": "Zeeland", "bestand": "regio-zeeland.json"}], ["Zeeland"]])
        self.assertEqual((empty, old), ([], []))  # an overview from before the counts reports nothing

    def test_what_a_region_misses_travels_with_the_region_on_offer(self):
        offered, = logic(["regios", self.AREA, [dict(self.OVERVIEW[1], ongelezen=146, mislukt=20)]])
        self.assertEqual((offered[0]["ongelezen"], offered[0]["mislukt"]), (146, 20))

    def test_names_in_a_sentence(self):
        lines = logic(["nameList", ["Zeeland"]], ["nameList", ["Midden-Brabant", "Zeeland"]], ["nameList", ["Midden-Brabant", "West-Brabant", "Zeeland"]], ["nameList", []])
        self.assertEqual(lines, ["Zeeland", "Midden-Brabant en Zeeland", "Midden-Brabant, West-Brabant en Zeeland", ""])


def tekstbericht(id, regio="kern", datum="2026-11-10", **extra):
    """A permit notice without a description: the app has to read its text."""
    base = {"id": id, "type": "vergunning", "titel": "Aanvraag omgevingsvergunning, Teststraat " + id, "omschrijving": None, "activiteiten": [],
            "fase": "Aanvraag", "locatieSoort": "exact", "regio": regio, "datum": datum, "_rd": None, "_perceelM2": None,
            "_urlXml": "https://repository.overheid.nl/frbr/x/%s/1/xml/%s.xml" % (id, id)}
    base.update(extra)
    return base


class Teksten:
    """Stands in for the text service: records what is asked, in order, and can fail for some."""

    def __init__(self, fail=(), text="het plaatsen van een dakkapel"):
        self.asked, self.fail, self.text = [], set(fail), text

    def __call__(self, url, titel, limiet):
        key = url.rsplit("/", 1)[-1][:-4]
        self.asked.append(key)
        if key in self.fail or "*" in self.fail:
            raise http.OphaalFout(url, "HTTP 429", 1)
        return self.text


def verrijk(items, bron, **kwargs):
    return update.verrijk(items, 400, haal_tekst=bron, perceel_m2=lambda x, y: 1200, slaap=lambda seconds: None, **kwargs)


class GrensPerRun(unittest.TestCase):
    """At most a set number of new texts of the regions per run; the core first and without a limit."""

    def setUp(self):
        self.map = tempfile.TemporaryDirectory()
        self.addCleanup(self.map.cleanup)
        self.pad = pathlib.Path(self.map.name) / "ophaalcache.json"

    def cache(self):
        return cachemodule.Cache(self.pad)

    @staticmethod
    def notices():
        core = [tekstbericht("k%d" % n) for n in range(1, 6)]
        zeeland = [tekstbericht("z%d" % n, "Zeeland", "2026-11-%02d" % n) for n in range(1, 5)]
        west = [tekstbericht("w%d" % n, "West-Brabant", "2026-11-%02d" % (10 + n)) for n in range(1, 3)]
        return zeeland + core + west  # the regions deliberately not behind the core

    def test_core_is_read_completely_and_first_then_the_newest_of_the_regions(self):
        bron = Teksten()
        items, stats = verrijk(self.notices(), bron, grens_regio=3)
        # Texts are fetched a few at a time, so the order within a group is free; the groups are not mixed.
        self.assertEqual(sorted(bron.asked[:5]), ["k1", "k2", "k3", "k4", "k5"], "een regiotekst is gevraagd voordat de kern klaar was")
        self.assertEqual(sorted(bron.asked[5:]), ["w1", "w2", "z4"])  # the three newest of the regions: 12, 11 and 4 November
        waiting = {entry["id"]: entry for entry in items if entry["id"] in ("z1", "z2", "z3")}
        for entry in waiting.values():
            self.assertEqual((entry["klasse"], entry["score"], entry["waarom"]), ("onzeker", 5, "Tekst nog niet gelezen; een volgende verversing haalt hem op."))
        self.assertTrue(all(entry["klasse"] == "weggefilterd" for entry in items if entry["id"] not in waiting))
        self.assertEqual(stats["tekst"]["uitgesteld"], 3)
        self.assertEqual(stats["tekst"]["perRegio"], {"kern": {"mislukt": 0, "uitgesteld": 0}, "Zeeland": {"mislukt": 0, "uitgesteld": 3},
                                                      "West-Brabant": {"mislukt": 0, "uitgesteld": 0}})

    def test_limit_never_touches_the_core(self):
        bron = Teksten()
        items, stats = verrijk([tekstbericht("k%d" % n) for n in range(40)] + [tekstbericht("z1", "Zeeland")], bron, grens_regio=0)
        self.assertEqual(len([key for key in bron.asked if key.startswith("k")]), 40)
        self.assertNotIn("z1", bron.asked)
        self.assertEqual(stats["tekst"]["perRegio"]["kern"], {"mislukt": 0, "uitgesteld": 0})

    def test_without_a_limit_everything_is_read_as_before(self):
        bron = Teksten()
        items, stats = verrijk(self.notices(), bron)
        self.assertEqual(len(bron.asked), 11)
        self.assertEqual(stats["tekst"]["uitgesteld"], 0)

    def test_the_label_is_one_sentence_and_wins_from_what_the_title_says(self):
        self.assertRegex(relevantie.ONGELEZEN, r"^Tekst nog niet gelezen\b[^.]*\.$")
        title = "Aanvraag omgevingsvergunning voor het bouwen van 12 appartementen, Teststraat 1"
        items, _ = verrijk([tekstbericht("z-nieuw", "Zeeland", "2026-11-12"), tekstbericht("z-oud", "Zeeland", "2026-11-01", titel=title, _rd=(1.0, 2.0))],
                           Teksten(), grens_regio=1)
        old = next(entry for entry in items if entry["id"] == "z-oud")
        self.assertEqual((old["klasse"], old["waarom"], old["perceelM2"]), ("onzeker", relevantie.ONGELEZEN, None))

    def test_no_parcel_is_looked_up_for_a_notice_that_waits(self):
        looked_up = []
        title = "Aanvraag omgevingsvergunning voor het slopen van een loods, Teststraat 1"
        items = [tekstbericht("z1", "Zeeland", "2026-11-12", titel=title, _rd=(1.0, 2.0)), tekstbericht("z2", "Zeeland", "2026-11-01", titel=title, _rd=(3.0, 4.0))]
        update.verrijk(items, 400, haal_tekst=Teksten(), perceel_m2=lambda x, y: looked_up.append((x, y)) or 1200, slaap=lambda seconds: None, grens_regio=1)
        self.assertEqual(looked_up, [(1.0, 2.0)])

    def test_a_text_that_is_in_the_cache_is_not_new_and_the_next_run_reads_on(self):
        first, bron = self.cache(), Teksten()
        verrijk(self.notices(), bron, cache=first, grens_regio=3)
        first.bewaar()
        self.assertEqual(len(bron.asked), 8)

        second, bron = self.cache(), Teksten()
        items, stats = verrijk(self.notices(), bron, cache=second, grens_regio=2)
        self.assertEqual(sorted(bron.asked), ["z2", "z3"], "de tweede run leest niet verder waar de eerste ophield")
        self.assertEqual([entry["id"] for entry in items if entry["waarom"] == relevantie.ONGELEZEN], ["z1"])
        self.assertEqual(stats["tekst"]["perRegio"]["Zeeland"], {"mislukt": 0, "uitgesteld": 1})
        second.bewaar()

        third, bron = self.cache(), Teksten()
        items, stats = verrijk(self.notices(), bron, cache=third, grens_regio=2)
        self.assertEqual(bron.asked, ["z1"])
        self.assertEqual(stats["tekst"]["uitgesteld"], 0)
        self.assertFalse([entry for entry in items if entry["klasse"] == "onzeker"])


class TellingPerRegio(unittest.TestCase):
    """What could not be read is counted per region, so the morning screen reports the core only."""

    def test_a_failure_in_a_region_is_not_a_failure_of_the_core(self):
        items, stats = verrijk([tekstbericht("k1"), tekstbericht("z1", "Zeeland"), tekstbericht("z2", "Zeeland"), tekstbericht("w1", "West-Brabant")],
                               Teksten(fail={"z1", "w1"}))
        self.assertEqual(stats["tekst"]["definitiefMislukt"], 2)
        self.assertEqual(stats["tekst"]["perRegio"], {"kern": {"mislukt": 0, "uitgesteld": 0}, "Zeeland": {"mislukt": 1, "uitgesteld": 0},
                                                      "West-Brabant": {"mislukt": 1, "uitgesteld": 0}})
        self.assertEqual(update.kern_fouten(stats), {"tekst": 0, "perceel": 0})

    def test_a_failure_in_the_core_is_reported_as_before(self):
        items, stats = verrijk([tekstbericht("k1"), tekstbericht("k2"), tekstbericht("z1", "Zeeland")], Teksten(fail={"k1", "z1"}))
        self.assertEqual(update.kern_fouten(stats), {"tekst": 1, "perceel": 0})
        failed = next(entry for entry in items if entry["id"] == "k1")
        self.assertEqual((failed["klasse"], failed["waarom"]),
                         ("onzeker", "De tekst van deze bekendmaking kon niet worden opgehaald; de volgende verversing probeert het opnieuw."))

    def test_a_missing_text_is_counted_also_when_the_title_already_decides(self):
        # Run 22 of 18-11-2026: 35 texts did not come, but only 31 notices showed it. For the other four the
        # title settled the verdict, so nothing in the notice told that its text was missing.
        title = "Aanvraag omgevingsvergunning voor het bouwen van 12 appartementen, Teststraat 1"
        items, stats = verrijk([tekstbericht("w1", "West-Brabant", titel=title)], Teksten(fail={"w1"}))
        self.assertEqual(items[0]["klasse"], "ontwikkellocatie")
        self.assertNotIn("kon niet worden opgehaald", items[0]["waarom"])
        self.assertEqual(stats["tekst"]["perRegio"]["West-Brabant"]["mislukt"], 1)

    def test_a_failed_parcel_lookup_is_counted_with_its_region(self):
        def down(x, y):
            raise http.OphaalFout("https://api.pdok.nl/x", "tijdslimiet", 2)

        title = "Aanvraag omgevingsvergunning voor het slopen van een loods, Teststraat 1"
        items = [tekstbericht("k1", titel=title, _rd=(1.0, 2.0)), tekstbericht("z1", "Zeeland", titel=title, _rd=(3.0, 4.0))]
        _, stats = update.verrijk(items, 400, haal_tekst=Teksten(), perceel_m2=down, slaap=lambda seconds: None)
        self.assertEqual(stats["perceel"]["perRegio"], {"kern": {"mislukt": 1}, "Zeeland": {"mislukt": 1}})
        self.assertEqual(update.kern_fouten(stats)["perceel"], 1)

    def test_statistics_without_a_split_count_as_they_are(self):
        self.assertEqual(update.kern_fouten({"insolventie": {"definitiefMislukt": 3}, "tekst": {"definitiefMislukt": 2}}), {"insolventie": 3, "tekst": 2})

    def document(self, fail, grens=None):
        def notice(id, regio):
            return dict(tekstbericht(id, regio), afstandKm=1.0 if regio == "kern" else 90.0)

        config = {"venster_dagen": {"vergunning": 42}, "centrum": {}, "straal_km": 15, "drempel_perceel_m2": 400}
        fetchers = {"officielebekendmakingen": lambda: [notice("k1", "kern"), notice("z1", "Zeeland"), notice("z2", "Zeeland"), notice("z3", "Zeeland"),
                                                         notice("w1", "West-Brabant")]}
        now = datetime.datetime(2026, 11, 18, 9, 0, tzinfo=datetime.timezone.utc)
        return update.run(config, {"gemeenten": []}, now, fetchers=fetchers, dagcontrole=lambda moment: [],
                          verrijker=lambda found: verrijk(found, Teksten(fail=fail), grens_regio=grens))

    def test_what_the_run_writes_for_the_morning_screen_is_about_the_core(self):
        document = self.document(fail={"z1", "w1"})
        self.assertEqual(document["ophaalfouten"], {"tekst": 0, "perceel": 0})
        self.assertEqual(document["ophaalstatistiek"]["tekst"]["definitiefMislukt"], 2)  # the full figures stay in the statistics
        self.assertEqual(self.document(fail={"k1"})["ophaalfouten"], {"tekst": 1, "perceel": 0})

    def test_every_region_gets_its_own_count_in_the_overview(self):
        # Four new texts in the regions on one day and room for three: the last one waits. One of Zeeland fails.
        document = self.document(fail={"z1"}, grens=3)
        core, files = update.verdeel(document, ["Midden-Brabant", "West-Brabant", "Zeeland"])
        self.assertEqual({regio["naam"]: (regio["ongelezen"], regio["mislukt"]) for regio in core["regios"]},
                         {"Midden-Brabant": (0, 0), "West-Brabant": (1, 0), "Zeeland": (0, 1)})
        waiting = [entry["id"] for file in files.values() for entry in file["berichten"] if entry["waarom"] == relevantie.ONGELEZEN]
        self.assertEqual(waiting, ["w1"])
        self.assertEqual(core["ophaalfouten"], {"tekst": 0, "perceel": 0})


class WekelijkseBeurt(unittest.TestCase):
    """The weekly full refresh reads the core anew and one region, in turn."""

    REGIOS = ["Midden-Brabant", "West-Brabant", "Zeeland"]

    def setUp(self):
        self.map = tempfile.TemporaryDirectory()
        self.addCleanup(self.map.cleanup)
        self.pad = pathlib.Path(self.map.name) / "ophaalcache.json"

    def test_which_region_which_sunday(self):
        sundays = {"2026-11-22": "Midden-Brabant", "2026-11-29": "West-Brabant", "2026-12-06": "Zeeland", "2026-12-13": "Midden-Brabant",
                   "2026-12-20": "West-Brabant", "2026-12-27": "Zeeland", "2027-01-03": "Midden-Brabant", "2027-01-10": "West-Brabant",
                   "2027-01-17": "Zeeland"}
        for day, regio in sundays.items():
            with self.subTest(zondag=day):
                self.assertEqual(update.regio_van_de_week(datetime.date.fromisoformat(day), self.REGIOS), regio)

    def test_the_whole_week_has_the_same_region_and_no_week_is_skipped(self):
        monday = datetime.date(2026, 11, 16)
        self.assertEqual({update.regio_van_de_week(monday + datetime.timedelta(days=n), self.REGIOS) for n in range(7)}, {"Midden-Brabant"})
        turns = [update.regio_van_de_week(monday + datetime.timedelta(weeks=n), self.REGIOS) for n in range(120)]
        for n in range(len(turns) - 2):
            self.assertEqual(set(turns[n:n + 3]), set(self.REGIOS), "een regio wacht langer dan drie weken (week %d)" % n)
        self.assertIsNone(update.regio_van_de_week(monday, []))

    def filled(self):
        cache = cachemodule.Cache(self.pad)
        verrijk(GrensPerRun.notices(), Teksten(text="oude tekst"), cache=cache)
        cache.bewaar()
        return cachemodule.Cache(self.pad)

    def test_core_and_the_region_of_the_week_are_read_anew_the_rest_comes_from_the_cache(self):
        cache, bron = self.filled(), Teksten()
        items, stats = verrijk(GrensPerRun.notices(), bron, cache=cache, ververs=("kern", "Zeeland"), grens_regio=1)
        self.assertEqual(sorted(bron.asked), ["k1", "k2", "k3", "k4", "k5", "z1", "z2", "z3", "z4"])
        self.assertEqual(stats["tekst"]["uitgesteld"], 0, "een tekst die opnieuw gelezen wordt telt als nieuw voor de grens")
        self.assertEqual(cache.statistiek()["tekst"], {"uitCache": 2, "opgehaald": 9})
        cache.bewaar()
        stored = json.loads(self.pad.read_text(encoding="utf-8"))["tekst"]
        self.assertEqual((stored["z1"], stored["k1"], stored["w1"]), ("het plaatsen van een dakkapel", "het plaatsen van een dakkapel", "oude tekst"))

    def test_a_refresh_that_fails_keeps_what_was_read_before(self):
        cache = self.filled()
        items, stats = verrijk(GrensPerRun.notices(), Teksten(fail={"*"}), cache=cache, ververs=("kern", "Zeeland"))
        self.assertEqual((stats["tekst"]["definitiefMislukt"], stats["tekst"]["perRegio"]["kern"]["mislukt"]), (0, 0))
        self.assertFalse([entry for entry in items if entry["klasse"] == "onzeker"])
        self.assertEqual(cache.statistiek()["tekst"]["nietVerverst"], 9)
        cache.bewaar()
        stored = json.loads(self.pad.read_text(encoding="utf-8"))["tekst"]
        self.assertEqual(len(stored), 11)
        self.assertEqual(stored["z1"], "oude tekst")

    def test_a_text_that_was_never_read_and_fails_is_tried_again_next_time(self):
        cache = cachemodule.Cache(self.pad)
        items, stats = verrijk([tekstbericht("z1", "Zeeland")], Teksten(fail={"z1"}), cache=cache, ververs=("kern", "Zeeland"))
        self.assertEqual(stats["tekst"]["perRegio"]["Zeeland"]["mislukt"], 1)
        cache.bewaar()
        self.assertEqual(json.loads(self.pad.read_text(encoding="utf-8"))["tekst"], {})

    def test_lookups_made_while_fetching_follow_the_label_of_the_municipality(self):
        cache = cachemodule.Cache(self.pad)
        for key in ("Tilburg|Plan A", "Middelburg|Plan B", "Breda|Plan C", "Oosterhout|Plan D"):
            cache.zet("locatie", key, None)
        cache.zet("gemeente", "1,2", "Tilburg")
        cache.zet("insolventie", "stcrt-1", 0)
        area = {"gemeenten": [{"naam": "Tilburg", "regio": "kern"}, {"naam": "Oosterhout", "regio": "kern", "buitenStraal": "West-Brabant"},
                              {"naam": "Middelburg", "regio": "Zeeland"}, {"naam": "Breda", "regio": "West-Brabant"}]}
        update.markeer_verversing(cache, area, ("kern", "Zeeland"))
        self.assertEqual({key: cache.haal("locatie", key)[0] for key in cache.data["locatie"]},
                         {"Tilburg|Plan A": False, "Middelburg|Plan B": False, "Breda|Plan C": True, "Oosterhout|Plan D": False})
        self.assertEqual((cache.haal("gemeente", "1,2")[0], cache.haal("insolventie", "stcrt-1")[0]), (False, False))
        untouched = cachemodule.Cache(self.pad)
        untouched.zet("locatie", "Tilburg|Plan A", None)
        update.markeer_verversing(untouched, area, ())
        self.assertTrue(untouched.haal("locatie", "Tilburg|Plan A")[0])

    def main(self, argv):
        """Run update.main with the sources replaced; returns what the run was asked to read anew."""
        seen = {}

        def fake_run(config, area, now, cache=None, ververs=()):
            seen.update(ververs=ververs, grens=config.get("grens_regioteksten"), now=now)
            return {"bijgewerkt": now.isoformat(timespec="seconds"), "berichten": [], "ophaalstatistiek": {}, "ophaalfouten": {},
                    "cache": {}, "onvolledigeDagen": [],
                    "bronnen": [{"id": "officielebekendmakingen", "status": "ok", "aantal": 0}, {"id": "staatscourant-insolventies", "status": "ok", "aantal": 0}]}

        output = pathlib.Path(self.map.name) / "data" / "berichten.json"
        cache = mock.MagicMock(**{"return_value.bewaar.return_value": {"bytes": 0, "weggelaten": 0}})
        with mock.patch.object(update, "OUTPUT", output), mock.patch.object(update, "run", fake_run), \
                mock.patch.object(update.cachemodule, "Cache", cache), mock.patch("builtins.print"):
            update.main(argv)
        seen["lezen"] = cache.call_args.kwargs["lezen"]
        seen["written"] = json.loads(output.read_text(encoding="utf-8"))
        seen["files"] = sorted(path.name for path in output.parent.iterdir())
        return seen

    def test_the_run_reads_anew_what_its_arguments_say(self):
        plain = self.main([])
        self.assertEqual((plain["ververs"], plain["lezen"], plain["grens"]), ((), True, 300))
        self.assertEqual((plain["written"]["ververst"], plain["written"]["volledigeVerversing"]), ([], False))

        weekly = self.main(["--volledig"])
        turn = update.regio_van_de_week(weekly["now"].date(), CONFIG["regios"])
        self.assertEqual((weekly["ververs"], weekly["lezen"]), (("kern", turn), True), "de wekelijkse run leest de cache niet meer, of niet de regio van de week")
        self.assertEqual((weekly["written"]["ververst"], weekly["written"]["volledigeVerversing"]), (["kern", turn], True))

        chosen = self.main(["--volledig", "--regio", "Zeeland"])
        self.assertEqual(chosen["ververs"], ("kern", "Zeeland"))

        everything = self.main(["--alles"])
        self.assertEqual((everything["ververs"], everything["lezen"], everything["grens"]), ((), False, None))
        self.assertEqual(everything["written"]["ververst"], ["alles"])
        self.assertEqual(plain["files"], ["berichten.json", "regio-midden-brabant.json", "regio-west-brabant.json", "regio-zeeland.json"])

    def test_an_unknown_region_stops_the_run(self):
        with self.assertRaises(SystemExit), mock.patch("builtins.print"):
            update.main(["--volledig", "--regio", "Limburg"])

    def test_the_limit_in_the_config_is_the_agreed_one(self):
        self.assertEqual((CONFIG["grens_regioteksten"], update.GRENS_REGIOTEKSTEN), (300, 300))


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


class VasteSituatieOngelezen(unittest.TestCase):
    """tests/js/regio_ongelezen.json: the fixed situation the browser tests play back, in which
    regions have notices whose text still waits. It must stay what a run would have written."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "tests", "js", "regio_ongelezen.json"), encoding="utf-8") as handle:
            cls.fixture = json.load(handle)
        with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as handle:
            cls.config = json.load(handle)

    def test_the_overview_is_what_a_run_writes_for_these_files(self):
        notices = [notice for file in self.fixture["bestanden"].values() for notice in file["berichten"]]
        waiting = {}
        for notice in notices:
            if notice["waarom"] == relevantie.ONGELEZEN:
                waiting[notice["regio"]] = waiting.get(notice["regio"], 0) + 1
        document = {"bijgewerkt": "2026-11-18T09:13:38+01:00", "berichten": notices,
                    "ophaalstatistiek": {"tekst": {"perRegio": {naam: {"uitgesteld": count} for naam, count in waiting.items()}}}}
        core, files = update.verdeel(document, self.config["regios"])
        self.assertEqual(core["berichten"], [])
        self.assertEqual(core["regios"], self.fixture["regios"])
        self.assertEqual({name: file["berichten"] for name, file in files.items()},
                         {name: file["berichten"] for name, file in self.fixture["bestanden"].items()})

    def test_a_waiting_notice_looks_like_the_run_makes_it(self):
        waiting = [notice for file in self.fixture["bestanden"].values() for notice in file["berichten"] if notice["waarom"] == relevantie.ONGELEZEN]
        self.assertEqual(len(waiting), 5)
        for notice in waiting:
            with self.subTest(id=notice["id"]):
                self.assertEqual((notice["klasse"], notice["score"], notice["omschrijving"]), ("onzeker", 5, None))
        self.assertEqual({notice["type"] for notice in waiting}, {"vergunning", "plan", "verkoop"})

    def test_it_has_a_region_without_and_regions_with_waiting_notices_and_a_single_location(self):
        by_name = {regio["naam"]: regio for regio in self.fixture["regios"]}
        self.assertEqual(list(by_name), self.config["regios"])
        self.assertEqual({naam: regio["ongelezen"] for naam, regio in by_name.items()}, {"Midden-Brabant": 0, "West-Brabant": 4, "Zeeland": 1})
        self.assertEqual({naam: regio["locaties"] for naam, regio in by_name.items()}, {"Midden-Brabant": 2, "West-Brabant": 1, "Zeeland": 3})

    def test_every_notice_lies_in_a_municipality_of_its_region(self):
        regions = {}
        for gemeente in self.config["gemeenten"]:
            regions.setdefault(gemeente["naam"], set()).update(filter(None, [gemeente["regio"], gemeente.get("buiten_straal")]))
        for file in self.fixture["bestanden"].values():
            for notice in file["berichten"]:
                with self.subTest(id=notice["id"]):
                    self.assertEqual(notice["regio"], file["regio"])
                    self.assertIn(file["regio"], regions[notice["gemeente"]])
                    self.assertGreaterEqual(notice["afstandKm"], self.config["straal_km"])  # 15.0 is 15.04 rounded
