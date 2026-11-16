"""Tests for the download cache (no network). The key property: a run with a full cache gives
exactly the same outcome as a run without cache, with no downloads."""
import copy
import pathlib
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

from signalen import bekendmakingen, cache as cachemodule, insolventies, update

CENTRE = (134458.696, 396511.411)
CONFIG = {"centrum": {"rd": list(CENTRE)}, "straal_km": 15, "postcode_bereik": [[4840, 5299]]}
AREA = {"gemeenten": [{"naam": "Tilburg", "land": "NL", "woonplaatsen": [{"naam": "Tilburg"}]}]}

TEXTS = {"gmb-1": "het slopen van een loods", "gmb-2": "het bouwen van 12 appartementen", "gmb-3": "het kappen van een boom",
         "gmb-4": "het plan maakt de bouw van 16 woningen mogelijk"}
PARCELS = {(1.0, 2.0): 1200, (5.0, 6.0): None}


def items():
    def item(identifier, soort="vergunning", rd=None, **fields):
        base = {"id": identifier, "type": soort, "titel": f"Aanvraag omgevingsvergunning, Dorpsstraat {identifier[-1]}",
                "omschrijving": None, "activiteiten": [], "fase": "Aanvraag", "locatieSoort": "exact", "_rd": rd,
                "_perceelM2": None, "_urlXml": f"https://repository.overheid.nl/frbr/x/{identifier}/1/xml/{identifier}.xml"}
        base.update(fields)
        return base
    return [item("gmb-1", rd=(1.0, 2.0)), item("gmb-2"), item("gmb-3"), item("gmb-4", soort="plan", fase="Ontwerp"),
            item("gmb-5", rd=(5.0, 6.0), omschrijving="functiewijziging van winkel naar woning", _urlXml=None)]


class Bron:
    """Stands in for the text and parcel services and counts how often they are asked."""

    def __init__(self):
        self.verzoeken = 0

    def tekst(self, url, titel, limiet):
        self.verzoeken += 1
        return TEXTS[cachemodule.tekst_sleutel(url)]

    def perceel(self, x, y):
        self.verzoeken += 1
        return PARCELS[(x, y)]


def verrijk(bron, cache=None):
    return update.verrijk(items(), 400, haal_tekst=bron.tekst, perceel_m2=bron.perceel, slaap=lambda s: None, cache=cache)[0]


class CacheTest(unittest.TestCase):
    def setUp(self):
        self.map = tempfile.TemporaryDirectory()
        self.addCleanup(self.map.cleanup)
        self.pad = pathlib.Path(self.map.name) / "cache" / "ophaalcache.json"

    def cache(self, **kwargs):
        return cachemodule.Cache(self.pad, **kwargs)

    def test_full_cache_gives_the_same_outcome_without_downloads(self):
        zonder = Bron()
        expected = verrijk(zonder)
        self.assertEqual(zonder.verzoeken, 6)  # four texts and two parcels

        koud, first = Bron(), self.cache()
        self.assertEqual(verrijk(koud, first), expected)
        self.assertEqual(koud.verzoeken, 6)
        first.bewaar()

        warm, second = Bron(), self.cache()
        self.assertEqual(verrijk(warm, second), expected)
        self.assertEqual(warm.verzoeken, 0)
        self.assertEqual(second.statistiek()["tekst"], {"uitCache": 4, "opgehaald": 0})
        self.assertEqual(second.statistiek()["perceel"], {"uitCache": 2, "opgehaald": 0})

    def test_only_new_publications_are_downloaded(self):
        first = self.cache()
        verrijk(Bron(), first)
        first.bewaar()
        bron, second = Bron(), self.cache()
        extra = items() + [dict(items()[1], id="gmb-6", _urlXml="https://repository.overheid.nl/frbr/x/gmb-6/1/xml/gmb-6.xml")]
        with mock.patch.dict(TEXTS, {"gmb-6": "het bouwen van 4 woningen"}):
            result = update.verrijk(extra, 400, haal_tekst=bron.tekst, perceel_m2=bron.perceel, cache=second)[0]
        self.assertEqual(bron.verzoeken, 1)
        self.assertEqual(result[-1]["woningen"], 4)

    def test_parcel_without_result_is_cached_as_no_parcel(self):
        first = self.cache()
        verrijk(Bron(), first)
        first.bewaar()
        self.assertEqual(self.cache().haal("perceel", "5.0,6.0"), (True, None))
        self.assertEqual(self.cache().haal("perceel", "9.0,9.0"), (False, None))

    def test_failed_download_is_not_cached(self):
        def down(url, titel, limiet):
            raise RuntimeError("HTTP 429")

        first = self.cache()
        update.verrijk(items(), 400, haal_tekst=down, perceel_m2=Bron().perceel, slaap=lambda s: None, cache=first)
        first.bewaar()
        self.assertEqual(self.cache().data["tekst"], {})
        bron = Bron()
        self.assertEqual(verrijk(bron, self.cache()), verrijk(Bron()))  # the next run fetches them after all
        # Four texts, plus one parcel: without its text the first run could not know that parcel mattered.
        self.assertEqual(bron.verzoeken, 5)

    def test_full_refresh_ignores_the_cache_and_replaces_it(self):
        first = self.cache()
        verrijk(Bron(), first)
        first.bewaar()
        bron, fresh = Bron(), self.cache(lezen=False)
        with mock.patch.dict(TEXTS, {"gmb-3": "het slopen van een fabriekshal"}):  # the source corrected a publication
            result = verrijk(bron, fresh)
        fresh.bewaar()
        self.assertEqual(bron.verzoeken, 6)
        self.assertIn("sloop", result[2]["signalen"])
        self.assertEqual(self.cache().data["tekst"]["gmb-3"], "het slopen van een fabriekshal")

    def test_unused_entries_are_dropped_and_file_is_stable(self):
        first = self.cache()
        first.zet("tekst", "gmb-oud", "buiten het venster")
        first.bewaar()
        second = self.cache()
        verrijk(Bron(), second)
        second.bewaar()
        stored = self.pad.read_text(encoding="utf-8")
        self.assertNotIn("gmb-oud", stored)
        third = self.cache()
        verrijk(Bron(), third)
        third.bewaar()
        self.assertEqual(self.pad.read_text(encoding="utf-8"), stored)  # same input, byte-identical file
        self.assertIn('\n"gmb-1": ', stored)  # one entry per line keeps the daily change in git small

    def test_kind_that_did_not_run_is_not_pruned(self):
        first = self.cache()
        first.zet("insolventie", "stcrt-1", 0)
        first.bewaar()
        second = self.cache()
        second.bewaar(snoei=("tekst", "perceel"))
        self.assertEqual(self.cache().data["insolventie"], {"stcrt-1": 0})

    def test_other_radius_drops_cached_insolvency_verdicts(self):
        key = cachemodule.insolventie_sleutel(CONFIG)
        first = self.cache(sleutel=key)
        first.zet("insolventie", "stcrt-1", 0)
        first.zet("tekst", "gmb-1", "tekst")
        first.bewaar(snoei=())
        self.assertEqual(self.cache(sleutel=key).data["insolventie"], {"stcrt-1": 0})
        wider = cachemodule.insolventie_sleutel(dict(CONFIG, straal_km=20))
        changed = self.cache(sleutel=wider)
        self.assertEqual((changed.data["insolventie"], changed.data["tekst"]), ({}, {"gmb-1": "tekst"}))


NS = 'xmlns:dcterms="http://purl.org/dc/terms/" xmlns:gzd="http://standaarden.overheid.nl/sru"'
HIT = ("Uitspraak faillissement op 03 november 2026 inzake (F.02/26/288) Voorbeeld Metaal B.V, "
       "vest.adr. Fabriekstraat 12 5038EN Tilburg, KvK: 12345678. Cur: mr A.B. Curator.")
MISS = ("Uitspraak faillissement op 03 november 2026 inzake (F.02/26/289) Elders B.V, "
        "vest.adr. Kade 1 9723BX Groningen, KvK: 87654321.")
DOCS = {"stcrt-1": f"<x><metadata/></metadata><li><al>{HIT}</al></li></x>",
        "stcrt-2": f"<x><metadata/></metadata><li><al>{MISS}</al></li></x>"}


def court_records():
    return [ET.fromstring(f'<record {NS}><dcterms:identifier>{doc}</dcterms:identifier><dcterms:creator>Rechtbank X</dcterms:creator>'
                          f'<dcterms:date>2026-11-04</dcterms:date><gzd:preferredUrl>https://zoek/{doc}.html</gzd:preferredUrl>'
                          f'<gzd:itemUrl manifestation="xml">https://repository/{doc}.xml</gzd:itemUrl></record>') for doc in DOCS]


def premises(postcode, number):
    return [{"gebruiksdoel": {"industriefunctie"}, "oppervlakte": 800, "woonplaats": "Tilburg", "straat": "Fabriekstraat",
             "huisletter": "", "rd": (134458.696, 399511.411)}]


class InsolventieCacheTest(unittest.TestCase):
    def fetch(self, cache, lookup=premises):
        asked = []

        def download(url, **kwargs):
            asked.append(url)
            return DOCS[url.rsplit("/", 1)[-1].removesuffix(".xml")].encode()

        with mock.patch.object(bekendmakingen, "search", lambda query: court_records()), \
                mock.patch.object(insolventies.http, "get", download):
            found = insolventies.fetch(CONFIG, AREA, "2026-10-19", cache, lookup)
        return found, asked

    def test_publication_without_hit_is_skipped_next_time_and_outcome_is_equal(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = pathlib.Path(folder) / "c.json"
            without, asked = self.fetch(None)
            self.assertEqual((len(without), len(asked)), (1, 2))

            first = cachemodule.Cache(pad)
            cold, asked = self.fetch(first)
            self.assertEqual((cold, len(asked)), (without, 2))
            first.bewaar()
            stored = pad.read_text(encoding="utf-8")
            self.assertIn("stcrt-2", stored)
            for private in ("Voorbeeld Metaal", "Elders", "Curator", "12345678", "stcrt-1"):
                self.assertNotIn(private, stored)  # only the verdict "no hit" is kept, never content

            warm, asked = self.fetch(cachemodule.Cache(pad))
            self.assertEqual((warm, asked), (without, ["https://repository/stcrt-1.xml"]))

    def test_failed_address_lookup_is_not_cached_as_no_hit(self):
        def down(postcode, number):
            raise RuntimeError("BAG niet bereikbaar")

        with tempfile.TemporaryDirectory() as folder:
            first = cachemodule.Cache(pathlib.Path(folder) / "c.json")
            found, _ = self.fetch(first, lookup=down)
            self.assertEqual(found, [])
            self.assertNotIn("stcrt-1", first.data["insolventie"])  # unknown, so it is read again next time
            self.assertIn("stcrt-2", first.data["insolventie"])


class LocatieCacheTest(unittest.TestCase):
    def test_address_lookup_is_cached_including_not_found(self):
        calls = []

        def geocoder(title, gemeente):
            calls.append(title)
            return ("omgeving Dorpsstraat, Tilburg", (134000.0, 396000.0)) if "Dorpsstraat" in title else None

        with tempfile.TemporaryDirectory() as folder, mock.patch.object(bekendmakingen, "geocode_title", geocoder):
            pad = pathlib.Path(folder) / "c.json"
            first = cachemodule.Cache(pad)
            geocode, _ = bekendmakingen.lookups(first)
            expected = [geocode("Plan Dorpsstraat 1", "Tilburg"), geocode("Omgevingsvisie", "Tilburg")]
            first.bewaar()
            geocode, _ = bekendmakingen.lookups(cachemodule.Cache(pad))
            self.assertEqual([geocode("Plan Dorpsstraat 1", "Tilburg"), geocode("Omgevingsvisie", "Tilburg")], expected)
            self.assertEqual(len(calls), 2)  # nothing was asked the second time

    def test_failing_lookup_means_unknown_and_is_asked_again(self):
        def down(title, gemeente):
            raise RuntimeError("geen verbinding")

        with tempfile.TemporaryDirectory() as folder, mock.patch.object(bekendmakingen, "geocode_title", down):
            cache = cachemodule.Cache(pathlib.Path(folder) / "c.json")
            geocode, _ = bekendmakingen.lookups(cache)
            self.assertIsNone(bekendmakingen._optional(geocode, "Plan Dorpsstraat 1", "Tilburg"))
            self.assertEqual(cache.data["locatie"], {})


if __name__ == "__main__":
    unittest.main()
