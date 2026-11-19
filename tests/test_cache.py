"""Tests for the download cache (no network). The key property: a run with a full cache gives
exactly the same outcome as a run without cache, with no downloads."""
import copy
import datetime
import json
import pathlib
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

from signalen import bekendmakingen, cache as cachemodule, http, insolventies, update

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
    def fetch(self, cache, lookup=premises, broken=(), statistiek=None):
        asked = []

        def download(url, **kwargs):
            asked.append(url)
            doc = url.rsplit("/", 1)[-1].removesuffix(".xml")
            if doc in broken:
                raise http.OphaalFout(url, "HTTP 429", 2)
            return DOCS[doc].encode()

        with mock.patch.object(bekendmakingen, "search", lambda query: court_records()), \
                mock.patch.object(insolventies.http, "get", download), \
                mock.patch.object(http.time, "sleep", lambda seconds: None):
            found = insolventies.fetch(CONFIG, AREA, "2026-10-19", cache, lookup, statistiek)
        return found, sorted(set(asked))

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

    def test_unreadable_publication_is_counted_and_read_again_next_time(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = pathlib.Path(folder) / "c.json"
            first, stats = cachemodule.Cache(pad), {}
            found, _ = self.fetch(first, broken={"stcrt-2"}, statistiek=stats)
            self.assertEqual(len(found), 1)
            self.assertEqual((stats["insolventie"]["gevraagd"], stats["insolventie"]["definitiefMislukt"],
                              stats["insolventie"]["redenen"]), (2, 1, {"HTTP 429": 1}))
            self.assertNotIn("stcrt-2", first.data["insolventie"])
            first.bewaar()
            _, asked = self.fetch(cachemodule.Cache(pad))
            self.assertIn("https://repository/stcrt-2.xml", asked)

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


class CacheGrens(unittest.TestCase):
    """The workflow commits the cache, and the repository refuses files above 1.5 MB: a run must
    never write a cache that makes the next run fail in its tests."""

    def setUp(self):
        self.map = tempfile.TemporaryDirectory()
        self.addCleanup(self.map.cleanup)
        self.pad = pathlib.Path(self.map.name) / "cache" / "ophaalcache.json"

    def filled(self, core=4, region=10, size=200):
        cache = cachemodule.Cache(self.pad)
        for number in range(core):
            cache.zet("tekst", f"kern-{number}", "k" * size)
        for number in range(region):
            cache.zet("tekst", f"regio-{number:02}", "r" * size)
        cache.zet("perceel", "1.0|2.0", 1200)
        cache.zet("locatie", "Breda|ergens", None)
        return cache

    def stored(self):
        return json.loads(self.pad.read_text(encoding="utf-8"))

    def test_the_limits_stay_below_what_the_repository_accepts(self):
        self.assertLess(cachemodule.WAARSCHUW_BYTES, cachemodule.GRENS_BYTES)
        self.assertLess(cachemodule.GRENS_BYTES, cachemodule.REPO_BYTES)
        self.assertEqual(cachemodule.REPO_BYTES, 1_500_000, "gelijk aan de grens in tests/test_ververst.py")

    def test_below_the_limit_everything_is_kept_and_the_size_is_reported(self):
        saved = self.filled().bewaar(grens=100_000, weglaatbaar=[f"regio-{n:02}" for n in range(10)])
        self.assertEqual(saved, {"bytes": self.pad.stat().st_size, "weggelaten": 0})
        self.assertEqual(len(self.stored()["tekst"]), 14)

    def test_without_a_limit_nothing_is_left_out(self):
        saved = self.filled().bewaar(weglaatbaar=[f"regio-{n:02}" for n in range(10)])
        self.assertEqual(saved["weggelaten"], 0)
        self.assertEqual(len(self.stored()["tekst"]), 14)

    def test_above_the_limit_the_first_listed_texts_are_left_out_until_it_fits(self):
        full = self.filled().bewaar()["bytes"]
        order = [f"regio-{n:02}" for n in range(10)]
        saved = self.filled().bewaar(grens=full - 500, weglaatbaar=order)
        self.assertLessEqual(saved["bytes"], full - 500)
        self.assertEqual(saved["bytes"], self.pad.stat().st_size)
        self.assertEqual(saved["weggelaten"], 3, "drie teksten van ruim 200 bytes maken 500 bytes vrij; niet meer dan nodig")
        texts = self.stored()["tekst"]
        self.assertEqual(sorted(set(order) - set(texts)), order[:3], "de eerstgenoemde (oudste) gaan eerst")
        self.assertEqual(sorted(key for key in texts if key.startswith("kern-")), [f"kern-{n}" for n in range(4)])

    def test_other_kinds_are_never_left_out(self):
        full = self.filled().bewaar()["bytes"]
        self.filled().bewaar(grens=full - 500, weglaatbaar=[f"regio-{n:02}" for n in range(10)])
        self.assertEqual(self.stored()["perceel"], {"1.0|2.0": 1200})
        self.assertEqual(self.stored()["locatie"], {"Breda|ergens": None})

    def test_the_core_is_never_left_out_even_when_that_is_not_enough(self):
        saved = self.filled().bewaar(grens=300, weglaatbaar=[f"regio-{n:02}" for n in range(10)])
        texts = self.stored()["tekst"]
        self.assertEqual(sorted(texts), [f"kern-{n}" for n in range(4)])
        self.assertEqual(saved["weggelaten"], 10)
        self.assertGreater(saved["bytes"], 300, "de kern alleen is al groter; dat meldt de run")

    def test_a_listed_key_that_is_not_stored_does_not_count(self):
        full = self.filled().bewaar()["bytes"]
        saved = self.filled().bewaar(grens=full - 100, weglaatbaar=["onbekend", "regio-07", "regio-00"])
        self.assertEqual(saved["weggelaten"], 1)
        self.assertNotIn("regio-07", self.stored()["tekst"])
        self.assertIn("regio-00", self.stored()["tekst"])

    def test_a_text_that_was_left_out_is_downloaded_again_by_the_next_run(self):
        full = self.filled().bewaar()["bytes"]
        self.filled().bewaar(grens=full - 100, weglaatbaar=["regio-00"])
        second = cachemodule.Cache(self.pad)
        asked = []
        fetch = second.omwikkel("tekst", lambda key: asked.append(key) or "opnieuw gelezen", lambda key: key)
        self.assertEqual(fetch("regio-00"), "opnieuw gelezen")
        self.assertEqual(fetch("regio-01"), "r" * 200)
        self.assertEqual(asked, ["regio-00"])

    def test_the_file_keeps_one_entry_per_line(self):
        full = self.filled().bewaar()["bytes"]
        self.filled().bewaar(grens=full - 500, weglaatbaar=[f"regio-{n:02}" for n in range(10)])
        lines = self.pad.read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum(1 for line in lines if line.startswith('"regio-')), 7)
        self.assertTrue(self.pad.read_text(encoding="utf-8").endswith("}\n"))


class CacheGrensInDeRun(unittest.TestCase):
    """What the run names as droppable, and what it writes in its log."""

    WINDOWS = {"vergunning": 42, "plan": 180, "verkoop": 120}

    def test_only_region_notices_are_droppable_and_what_leaves_its_window_first_goes_first(self):
        notices = [{"id": "k1", "regio": "kern", "datum": "2026-10-01", "type": "vergunning"},
                   {"id": "z2", "regio": "Zeeland", "datum": "2026-11-02", "type": "vergunning"},     # leaves 14-12-2026
                   {"id": "w1", "regio": "West-Brabant", "datum": "2026-10-07", "type": "vergunning"},  # leaves 18-11-2026
                   {"id": "z1", "regio": "Zeeland", "datum": "2026-10-07", "type": "vergunning"},     # leaves 18-11-2026
                   {"id": "p1", "regio": "Zeeland", "datum": "2026-06-01", "type": "plan"},           # leaves 28-11-2026
                   {"id": "v1", "regio": "West-Brabant", "datum": "2026-09-01", "type": "verkoop"},   # leaves 30-12-2026
                   {"id": "k2", "datum": "2026-09-01", "type": "plan"},
                   {"id": "m1", "regio": "Midden-Brabant", "datum": None, "type": "vergunning"}]
        self.assertEqual(update.weglaatbare_regioteksten(notices, self.WINDOWS), ["m1", "w1", "z1", "p1", "z2", "v1"])

    def test_an_old_plan_outlasts_a_recent_permit(self):
        notices = [{"id": "plan-mei", "regio": "Zeeland", "datum": "2026-07-20", "type": "plan"},
                   {"id": "vergunning-oktober", "regio": "Zeeland", "datum": "2026-10-20", "type": "vergunning"}]
        self.assertEqual(update.weglaatbare_regioteksten(notices, self.WINDOWS), ["vergunning-oktober", "plan-mei"])

    def test_a_small_cache_gives_one_plain_line(self):
        lines = update.cache_meldingen({"bytes": 921_648, "weggelaten": 0})
        self.assertEqual(lines, ["  cache: 922 kB bewaard, 61 procent van de 1.500 kB die een bestand in de repository mag zijn"])

    def test_from_1200_kb_the_log_warns(self):
        self.assertEqual(len(update.cache_meldingen({"bytes": 1_199_999, "weggelaten": 0})), 1)
        lines = update.cache_meldingen({"bytes": 1_200_000, "weggelaten": 0})
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[1].startswith("::warning::Cache is 1.200 kB, boven 1.200 kB"))
        self.assertIn("Boven 1.400 kB bewaart een run een deel van de regioteksten niet meer", lines[1])

    def test_left_out_texts_are_reported_as_a_warning(self):
        lines = update.cache_meldingen({"bytes": 1_399_100, "weggelaten": 37})
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[1].startswith("::warning::Cache te groot: 37 regioteksten niet bewaard (wat het eerst uit het venster valt)"))
        self.assertIn("onder 1.400 kB", lines[1])
        self.assertIn("de volgende run haalt ze opnieuw op", lines[1])

    def test_a_core_that_alone_is_too_large_is_reported_separately(self):
        lines = update.cache_meldingen({"bytes": 1_450_000, "weggelaten": 900})
        self.assertEqual(len(lines), 3)
        self.assertIn("ook zonder die regioteksten boven 1.400 kB", lines[2])
        self.assertIn("Boven 1.500 kB strandt de volgende run in de tests", lines[2])

    def run_main(self, limit):
        """The real `main` with a real cache in a temporary folder and a stand-in for the fetching."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        pad = pathlib.Path(folder.name) / "cache" / "ophaalcache.json"
        notices = ([{"id": f"kern-{n}", "regio": "kern", "datum": "2026-11-01", "klasse": "ontwikkellocatie", "type": "vergunning"} for n in range(3)]
                   + [{"id": f"wb-{n}", "regio": "West-Brabant", "datum": f"2026-11-{10 + n:02}", "klasse": "onzeker", "type": "vergunning"} for n in range(6)])

        def fake_run(config, area, now, cache=None, ververs=()):
            for notice in notices:
                cache.zet("tekst", notice["id"], "t" * 300)
            return {"bijgewerkt": now.isoformat(timespec="seconds"), "berichten": [dict(notice) for notice in notices], "ophaalstatistiek": {},
                    "ophaalfouten": {}, "cache": cache.statistiek(), "onvolledigeDagen": [],
                    "bronnen": [{"id": "officielebekendmakingen", "status": "ok", "aantal": 9}, {"id": "staatscourant-insolventies", "status": "ok", "aantal": 0}]}

        printed = []
        real = cachemodule.Cache
        output = pathlib.Path(folder.name) / "data" / "berichten.json"
        with mock.patch.object(update, "OUTPUT", output), mock.patch.object(update, "run", fake_run), \
                mock.patch.object(update.cachemodule, "Cache", lambda **kwargs: real(pad, **kwargs)), \
                mock.patch.object(update.cachemodule, "GRENS_BYTES", limit), \
                mock.patch("builtins.print", lambda *args, **kwargs: printed.append(" ".join(str(arg) for arg in args))):
            update.main([])
        return json.loads(pad.read_text(encoding="utf-8"))["tekst"], printed, pad.stat().st_size

    def test_the_run_keeps_the_cache_below_its_limit_and_says_so(self):
        everything, printed, full = self.run_main(limit=1_400_000)
        self.assertEqual(len(everything), 9)
        self.assertFalse([line for line in printed if "Cache te groot" in line])
        self.assertTrue([line for line in printed if line.startswith("  cache: ") and "bewaard" in line])
        self.assertTrue([line for line in printed if line.startswith("  bestanden: berichten.json ") and "regio-west-brabant.json" in line])

        texts, printed, size = self.run_main(limit=full - 600)
        self.assertLessEqual(size, full - 600)
        self.assertEqual(sorted(texts), ["kern-0", "kern-1", "kern-2", "wb-2", "wb-3", "wb-4", "wb-5"], "de twee van de regio die het eerst uit het venster vallen, zijn weggelaten")
        self.assertEqual(len([line for line in printed if line.startswith("::warning::Cache te groot: 2 regioteksten niet bewaard")]), 1)
