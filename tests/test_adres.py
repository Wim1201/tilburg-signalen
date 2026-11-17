"""Tests for the tab "Adres": how addresses are spelled and compared, which notices belong to an
address, what the answers of the open registers mean, and what happens when a register gives
nothing (site/adres.js). The page itself is tested in a real browser by tests/test_site.py
(InDeBrowser), with the registers played back by tests/js/adres_smoke.js.

The tests run site/adres.js under Node and are skipped when Node is missing."""
import json
import os
import re
import shutil
import subprocess
import unittest
from urllib.parse import parse_qs, urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
JS = os.path.join(ROOT, "tests", "js")
NODE = shutil.which("node")


def read(*parts):
    with open(os.path.join(SITE, *parts), encoding="utf-8") as handle:
        return handle.read()


def adres(*calls):
    """Run functions of site/adres.js; each call is [name, arg, ...]. Returns the list of results."""
    done = subprocess.run([NODE, os.path.join(JS, "run_logic.js"), os.path.join(SITE, "adres.js")], input=json.dumps(calls),
                          capture_output=True, text=True, encoding="utf-8", timeout=120)
    if done.returncode:
        raise AssertionError(done.stderr)
    return json.loads(done.stdout)


with open(os.path.join(JS, "adres_fixtures.json"), encoding="utf-8") as _handle:
    FIXTURES = json.load(_handle)  # real answers of PDOK for Burgemeester van de Mortelplein 118a, Tilburg

# The address the fixtures are about, as the app works with it.
MORTELPLEIN = {"straat": "Burgemeester van de Mortelplein", "huisnummer": 118, "huisletter": "a", "toevoeging": "", "postcode": "5037PL",
               "woonplaats": "Tilburg", "gemeente": "Tilburg", "lat": 51.55141136, "lon": 5.05750626}


def address(straat="Hoofdstraat", nummer=12, letter="", toevoeging="", postcode="5011AA", gemeente="Tilburg", lat=51.56, lon=5.09):
    return {"straat": straat, "huisnummer": nummer, "huisletter": letter, "toevoeging": toevoeging, "postcode": postcode,
            "woonplaats": gemeente, "gemeente": gemeente, "lat": lat, "lon": lon}


def notice(id, titel, **extra):
    base = {"id": id, "bron": "officielebekendmakingen", "publicatie": "Gemeenteblad", "overheid": "Tilburg", "type": "vergunning",
            "fase": "Aanvraag", "soort": None, "titel": titel, "omschrijving": None, "plaats": "", "datum": "2026-11-10",
            "gemeente": "Tilburg", "afstandKm": 1.0, "locatieSoort": "exact", "lat": 51.56, "lon": 5.09,
            "url": "https://zoek.officielebekendmakingen.nl/" + id + ".html", "klasse": "weggefilterd", "score": 0}
    base.update(extra)
    return base


def found(items, where, parcels=None):
    """Ids per group for one search."""
    result, = adres(["findNotices", items, where, parcels or []])
    return {group: [row["id"] for row in result[group]] for group in ("adres", "mogelijk", "straat")}


def square(lon, lat, half=0.0002):
    """A parcel of about 28 by 44 metres around a point, as the app holds one."""
    ring = [[lon - half, lat - half], [lon + half, lat - half], [lon + half, lat + half], [lon - half, lat + half], [lon - half, lat - half]]
    return {"aanduiding": "Tilburg A 1", "rings": [ring]}


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Schrijfwijze(unittest.TestCase):
    """One spelling for comparing: capitals, accents, dots and abbreviations do not matter."""

    def same(self, *names):
        keys = adres(*[["streetKey", name] for name in names])
        self.assertEqual(len(set(keys)), 1, dict(zip(names, keys)))
        return keys[0]

    def test_capitals_accents_and_punctuation(self):
        plain, = adres(["normalise", "  André  van Dúúrenstraat 12A, 5011 AA  's-Gravenmoer "])
        self.assertEqual(plain, "andre van duurenstraat 12a , 5011 aa s-gravenmoer")
        self.same("Heuvelstraat", "HEUVELSTRAAT", "heuvelstraat")

    def test_straat_and_str(self):
        self.assertEqual(self.same("Heuvelstraat", "Heuvelstr.", "Heuvelstr", "heuvel str.", "Heuvel straat"), "heuvelstraat")
        self.assertEqual(self.same("Sint Josephstraat", "St. Josephstr.", "St Josephstraat", "st.Josephstr"), "sintjosephstraat")

    def test_titles_in_street_names(self):
        self.same("Burgemeester van de Mortelplein", "Burg. van de Mortelplein", "burg van de mortelplein")
        self.same("Dr. Deelenlaan", "Dokter Deelenlaan", "Doctor Deelenlaan", "dr Deelenlaan")
        self.same("Professor Cobbenhagenlaan", "Prof. Cobbenhagenlaan")
        self.same("Pastoor van Beurdenstraat", "Past. van Beurdenstraat")
        self.same("Prinses Irenestraat", "Pr. Irenestraat")

    def test_spaces_and_hyphens_in_a_street_name(self):
        self.same("Waspikse weg", "Waspikseweg")
        self.same("Ringbaan-Oost", "Ringbaan Oost", "Ringbaan  oost")
        self.same("NS Plein", "NS-plein")

    def test_different_streets_stay_different(self):
        keys = adres(["streetKey", "Heuvelstraat"], ["streetKey", "Heuvelring"], ["streetKey", "Heuvel"], ["streetKey", "Korte Heuvel"])
        self.assertEqual(len(set(keys)), 4)

    def test_letter_and_addition_of_a_house_number(self):
        results = adres(["suffix", "A", ""], ["suffix", "a", None], ["suffix", "", "01"], ["suffix", "V", "3004"], ["suffix", "a", "1"],
                        ["suffix", "", "bis"], ["suffix", None, None], ["houseNumber", {"huisnummer": 1, "huisletter": "V", "toevoeging": "3004"}],
                        ["houseNumber", {"huisnummer": 12, "huisletter": "a", "toevoeging": ""}], ["houseNumber", {"huisnummer": 12, "huisletter": "", "toevoeging": ""}])
        self.assertEqual(results, ["a", "a", "1", "v3004", "a1", "bis", "", "1V-3004", "12a", "12"])

    def test_what_is_typed_goes_to_the_address_search_tidied(self):
        results = adres(["searchText", "  Heuvelstr.   5  Tilburg "], ["searchText", "Heuvelstr 5"], ["searchText", "5037PL 118a"], ["searchText", "Strijpstraat 1"])
        self.assertEqual(results, ["Heuvelstraat 5 Tilburg", "Heuvelstraat 5", "5037PL 118a", "Strijpstraat 1"])


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Huisnummers(unittest.TestCase):
    """The house numbers behind a street name, in the ways the sources write them (all taken from
    notices in site/data/berichten.json, except where marked as made up)."""

    FORMS = [
        ("Sleutelbloem 16, 5102HH Dongen", "Sleutelbloem", [{"n": 16, "s": ""}], "5102hh"),
        ("Lage Ham 42, 5102 AD Dongen", "Lage Ham", [{"n": 42, "s": ""}], "5102ad"),
        ("Heuvelstraat 6 A te Moergestel", "Heuvelstraat", [{"n": 6, "s": "a"}], None),
        ("Grotestraat 231 b te Waalwijk", "Grotestraat", [{"n": 231, "s": "b"}], None),
        ("Burgemeester van de Mortelplein 118a, 5037PL Tilburg", "Burgemeester van de Mortelplein", [{"n": 118, "s": "a"}], "5037pl"),
        ("Tilburgseweg 172 e, 5051 AM Goirle, Goirle (GLE01) E 5983", "Tilburgseweg", [{"n": 172, "s": "e"}], "5051am"),
        ("Emmastraat 40 a 1 te Goirle", "Emmastraat", [{"n": 40, "s": "a1"}], None),
        ("Dongepark 1V-3004, 5102DB Dongen", "Dongepark", [{"n": 1, "s": "v3004"}], "5102db"),
        ("Waspikse weg 17A, 5109RE 's Gravenmoer", "Waspikse weg", [{"n": 17, "s": "a"}], "5109re"),
        ("Predikherenlaan 529-721 Tilburg", "Predikherenlaan", [{"van": 529, "tot": 721}], None),
        ("Puccinistraat 103 - 311, 5049GJ Tilburg", "Puccinistraat", [{"van": 103, "tot": 311}], "5049gj"),
        ("perceel BKL04 B 6746 nabij Ijzertijd 21 en 36) te Berkel-Enschot", "IJzertijd", [{"n": 21, "s": ""}, {"n": 36, "s": ""}], None),
        ("Felixhof 54, 60, 5071BZ Udenhout", "Felixhof", [{"n": 54, "s": ""}, {"n": 60, "s": ""}], "5071bz"),
        ("Insulindestraat 1, 1a, 5013BA Tilburg", "Insulindestraat", [{"n": 1, "s": ""}, {"n": 1, "s": "a"}], "5013ba"),
        ("Wilhelminapark 141a, 141b, 5041EJ Tilburg", "Wilhelminapark", [{"n": 141, "s": "a"}, {"n": 141, "s": "b"}], "5041ej"),
        ("Hultenseweg 16 Tilburg", "Hultenseweg", [{"n": 16, "s": ""}], None),
        # Made up, forms that occur elsewhere:
        ("Heuvelring 67-12, 5038CJ Tilburg", "Heuvelring", [{"n": 67, "s": "12"}], "5038cj"),
        ("Kerkstr. 12 t/m 18 te Dongen", "Kerkstraat", [{"van": 12, "tot": 18}], None),
        ("Kerkstraat 12 tot en met 18", "Kerkstraat", [{"van": 12, "tot": 18}], None),
        ("Kerkstraat 12, 14 en 16 te Dongen", "Kerkstraat", [{"n": 12, "s": ""}, {"n": 14, "s": ""}, {"n": 16, "s": ""}], None),
        ("Kerkstraat 12/14", "Kerkstraat", [{"n": 12, "s": ""}, {"n": 14, "s": ""}], None),
        ("Kerkstraat nr. 12-A", "Kerkstraat", [{"n": 12, "s": "a"}], None),
        ("Kerkstraat 12bis", "Kerkstraat", [{"n": 12, "s": "bis"}], None),
    ]

    def test_forms_the_sources_use(self):
        results = adres(*[["mentions", text, street] for text, street, _, _ in self.FORMS])
        for (text, _, specs, postcode), mentions in zip(self.FORMS, results):
            with self.subTest(tekst=text):
                self.assertEqual(len(mentions), 1)
                self.assertEqual(mentions[0]["specs"], specs)
                self.assertEqual(mentions[0]["postcode"], postcode)

    def test_a_number_that_counts_something_is_not_a_house_number(self):
        first, second, third = adres(["mentions", "Hoofdstraat 12 - 3 woningen bouwen", "Hoofdstraat"],
                                     ["mentions", "Hoofdstraat 12 en 3 appartementen", "Hoofdstraat"],
                                     ["mentions", "kappen aan de Hoofdstraat 4 bomen", "Hoofdstraat"])
        self.assertEqual(first[0]["specs"], [{"n": 12, "s": ""}])
        self.assertEqual(second[0]["specs"], [{"n": 12, "s": ""}])
        self.assertEqual(third[0]["specs"], [])

    def test_postcode_is_not_read_as_a_house_number_or_an_addition(self):
        one, two = adres(["mentions", "Bredaseweg 70 5038 NH Tilburg", "Bredaseweg"], ["mentions", "Bredaseweg 70a 5038NH Tilburg", "Bredaseweg"])
        self.assertEqual((one[0]["specs"], one[0]["postcode"]), ([{"n": 70, "s": ""}], "5038nh"))
        self.assertEqual((two[0]["specs"], two[0]["postcode"]), ([{"n": 70, "s": "a"}], "5038nh"))

    def test_street_without_a_number_and_a_number_that_cannot_be_read(self):
        plain, odd = adres(["mentions", "Kapelmeesterlaan Tilburg", "Kapelmeesterlaan"], ["mentions", "Hoofdstraat 12-14-16", "Hoofdstraat"])
        self.assertEqual(plain, [{"specs": [], "postcode": None, "unclear": False}])
        self.assertEqual(odd, [{"specs": [], "postcode": None, "unclear": True}])

    def test_a_longer_street_name_is_another_street(self):
        results = adres(["mentions", "Korte Heuvel 12 Tilburg", "Heuvel"], ["mentions", "Heuvelring 12 Tilburg", "Heuvel"],
                        ["mentions", "Dokter Bloemenlaan 3", "Bloemenlaan"], ["mentions", "Kazernehof 1, 5017ER Tilburg", "Hof"],
                        ["mentions", "een woning aan de Heuvel 12 te Tilburg", "Heuvel"])
        self.assertEqual([len(mentions) for mentions in results], [0, 0, 0, 0, 1])

    def test_every_time_the_street_is_named_counts(self):
        mentions, = adres(["mentions", "Hoofdstraat 12 te Tilburg \n Aanvraag voor Hoofdstraat 14, 5011AA Tilburg", "Hoofdstraat"])
        self.assertEqual([mention["specs"] for mention in mentions], [[{"n": 12, "s": ""}], [{"n": 14, "s": ""}]])


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class AdresUitDeZoeker(unittest.TestCase):
    """What the address search (PDOK Locatieserver) returns, as the address the tab works with."""

    def test_address_with_a_letter_and_two_parcels(self):
        found_addresses, = adres(["addresses", FIXTURES["suggest"]])
        self.assertEqual(len(found_addresses), 1)
        where = found_addresses[0]
        self.assertEqual(where["label"], "Burgemeester van de Mortelplein 118a, 5037PL Tilburg")
        self.assertEqual((where["straat"], where["huisnummer"], where["huisletter"], where["toevoeging"]), ("Burgemeester van de Mortelplein", 118, "a", ""))
        self.assertEqual((where["postcode"], where["woonplaats"], where["gemeente"]), ("5037PL", "Tilburg", "Tilburg"))
        self.assertEqual(where["objectId"], "0855010000010053")
        self.assertEqual(where["percelen"], [{"gemeente": "TBG01", "sectie": "Q", "nummer": 4688}, {"gemeente": "TBG01", "sectie": "Q", "nummer": 4489}])
        self.assertEqual(where["rd"], {"x": 132133.035, "y": 395879.872})
        self.assertEqual((where["lat"], where["lon"]), (51.55141136, 5.05750626))

    def test_the_parcel_is_the_one_of_this_letter_not_of_the_number(self):
        # Real answers of 17-11-2026: on Tilburgseweg 172 in Goirle every letter has a parcel of its own.
        docs = [{"weergavenaam": "Tilburgseweg 172, 5051AM Goirle", "huisnummer": 172, "gekoppeld_perceel": ["GLE01-E-1061"]},
                {"weergavenaam": "Tilburgseweg 172a, 5051AM Goirle", "huisnummer": 172, "huisletter": "a", "gekoppeld_perceel": ["GLE01-E-2643"]},
                {"weergavenaam": "Tilburgseweg 172e, 5051AM Goirle", "huisnummer": 172, "huisletter": "e", "gekoppeld_perceel": ["GLE01-E-5983"]}]
        found_addresses, = adres(["addresses", {"response": {"docs": docs}}])
        self.assertEqual([(a["huisletter"], a["percelen"][0]["nummer"]) for a in found_addresses], [("", 1061), ("a", 2643), ("e", 5983)])
        urls = adres(*[["perceelUrl", a["percelen"][0]] for a in found_addresses])
        self.assertEqual([parse_qs(urlsplit(url).query)["perceelnummer"] for url in urls], [["1061"], ["2643"], ["5983"]])

    def test_address_with_an_addition_and_without_a_linked_parcel(self):
        doc = {"id": "adr-1", "weergavenaam": "Dongepark 1V-3004, 5102DB Dongen", "straatnaam": "Dongepark", "huisnummer": 1, "huisletter": "V",
               "huisnummertoevoeging": "3004", "postcode": "5102 db", "woonplaatsnaam": "Dongen", "gemeentenaam": "Dongen",
               "centroide_ll": "POINT(4.93 51.63)", "adresseerbaarobject_id": "geen nummer", "gekoppeld_perceel": ["onzin", "DGN01-I-2677"]}
        where, = adres(["addressFromDoc", doc])
        self.assertEqual((where["huisletter"], where["toevoeging"], where["postcode"]), ("V", "3004", "5102DB"))
        self.assertEqual(where["percelen"], [{"gemeente": "DGN01", "sectie": "I", "nummer": 2677}])
        self.assertIsNone(where["objectId"])
        self.assertIsNone(where["rd"])
        bare, = adres(["addressFromDoc", {"weergavenaam": "Lage Ham 42, 5102AC Dongen", "huisnummer": 42}])
        self.assertEqual((bare["percelen"], bare["lat"], bare["huisletter"]), ([], None, ""))

    def test_search_asks_for_addresses_near_tilburg_first_without_a_key(self):
        url, = adres(["suggestUrl", " Heuvelstr. 5 ", {"lat": 51.55717769, "lon": 5.0910001}])
        parts = urlsplit(url)
        params = parse_qs(parts.query)
        self.assertEqual((parts.scheme, parts.netloc, parts.path), ("https", "api.pdok.nl", "/bzk/locatieserver/search/v3_1/suggest"))
        self.assertEqual((params["q"], params["fq"], params["lat"], params["lon"]), (["Heuvelstraat 5"], ["type:adres"], ["51.55717769"], ["5.0910001"]))
        self.assertIn("gekoppeld_perceel", params["fl"][0])
        self.assertEqual(set(params), {"q", "fq", "rows", "fl", "lat", "lon"})


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Pand(unittest.TestCase):
    """Year of construction, use, floor area and status from the BAG."""

    def test_the_four_facts(self):
        vbo = FIXTURES["vbo"]["features"][0]
        model, urls = adres(["bagModel", vbo, list(FIXTURES["pand"].values())], ["pandUrls", vbo])
        self.assertEqual(model["rows"], [{"label": "Bouwjaar", "value": "1962"}, {"label": "Gebruiksdoel", "value": "gezondheidszorgfunctie"},
                                         {"label": "Oppervlakte", "value": "280 m²"}, {"label": "Pandstatus", "value": "Verbouwing pand"}])
        self.assertFalse(model["pandMissing"])
        self.assertEqual(urls, ["https://api.pdok.nl/kadaster/bag/ogc/v2/collections/pand/items/aae4c55c-740b-5668-a606-bb94819604dc?f=json"])

    def test_several_uses_and_several_buildings(self):
        vbo = {"properties": {"gebruiksdoel": "woonfunctie,kantoorfunctie", "oppervlakte": 1250, "status": "Verblijfsobject in gebruik"}}
        panden = [{"properties": {"bouwjaar": 1990, "status": "Pand in gebruik"}}, {"properties": {"bouwjaar": 2004, "status": "Pand in gebruik"}}]
        model, = adres(["bagModel", vbo, panden])
        self.assertEqual([row["value"] for row in model["rows"]], ["1990 en 2004", "woonfunctie, kantoorfunctie", "1.250 m²", "Pand in gebruik"])
        self.assertEqual(model["panden"], 2)

    def test_only_links_into_the_register_itself_are_followed(self):
        base = "https://api.pdok.nl/kadaster/bag/ogc/v2/collections/pand/items/"
        vbo = {"properties": {"pand.href": [base + "a", "https://example.org/pand/items/b", "javascript:alert(1)", base + "c?x=1", base + "d", base + "e", base + "f"]}}
        urls, none = adres(["pandUrls", vbo], ["pandUrls", {"properties": {}}])
        self.assertEqual(urls, [base + "a?f=json", base + "d?f=json", base + "e?f=json"])
        self.assertEqual(none, [])


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Perceel(unittest.TestCase):
    """The cadastral parcel: designation, registered size and the small map."""

    def test_designation_and_size(self):
        small, large = adres(["parcels", FIXTURES["perceel"]["4688"]], ["parcels", FIXTURES["perceel"]["4489"]])
        self.assertEqual((small[0]["aanduiding"], small[0]["code"], small[0]["grootteTekst"], small[0]["soortGrootte"]),
                         ("Tilburg Q 4688", "TBG01 Q 4688", "46 m²", "Vastgesteld"))
        self.assertEqual((large[0]["aanduiding"], large[0]["grootte"]), ("Tilburg Q 4489", 248))
        sizes = adres(["m2", 2510], ["m2", 1234567], ["m2", None], ["m2", 0])
        self.assertEqual(sizes, ["2.510 m²", "1.234.567 m²", None, "0 m²"])

    def test_request_names_municipality_section_and_number(self):
        url, at = adres(["perceelUrl", {"gemeente": "TBG01", "sectie": "Q", "nummer": 4688}], ["perceelAtUrl", 5.0575, 51.5514])
        params = parse_qs(urlsplit(url).query)
        self.assertEqual(urlsplit(url).netloc, "api.pdok.nl")
        self.assertEqual((params["akr_kadastrale_gemeente_code_waarde"], params["sectie"], params["perceelnummer"]), (["TBG01"], ["Q"], ["4688"]))
        west, south, east, north = [float(value) for value in parse_qs(urlsplit(at).query)["bbox"][0].split(",")]
        self.assertTrue(west < 5.0575 < east and south < 51.5514 < north)
        self.assertLess((north - south) * 111320, 6)  # a few metres around the point, not the neighbourhood

    def test_parcel_at_a_point_and_a_hole_in_a_parcel(self):
        outer = [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        hole = [[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]]
        response = {"features": [
            {"properties": {"perceelnummer": 1}, "geometry": {"type": "Polygon", "coordinates": [outer, hole]}},
            {"properties": {"perceelnummer": 2}, "geometry": {"type": "MultiPolygon", "coordinates": [[[[20, 0], [30, 0], [30, 10], [20, 10], [20, 0]]]]}}]}
        first, second, in_hole, outside = adres(["parcelAt", response, 2, 2], ["parcelAt", response, 25, 5], ["parcelAt", response, 5, 5], ["parcelAt", response, 15, 5])
        self.assertEqual((first["aanduiding"], second["aanduiding"]), ("1", "2"))
        self.assertIsNone(in_hole)
        self.assertIsNone(outside)

    def test_map_frames_the_parcels_and_draws_them_inside(self):
        parcels = adres(["parcels", FIXTURES["perceel"]["4688"]], ["parcels", FIXTURES["perceel"]["4489"]])
        both = parcels[0] + parcels[1]
        model, = adres(["mapModel", both, MORTELPLEIN])
        parts = urlsplit(model["image"])
        params = parse_qs(parts.query, keep_blank_values=True)
        self.assertEqual((parts.netloc, parts.path), ("service.pdok.nl", "/kadaster/kadastralekaart/wms/v5_0"))
        self.assertEqual((params["request"], params["crs"], params["layers"], params["width"], params["height"]), (["GetMap"], ["CRS:84"], ["Kadastralekaart"], ["480"], ["480"]))
        west, south, east, north = [float(value) for value in params["bbox"][0].split(",")]
        for parcel in both:
            for lon, lat in parcel["rings"][0]:
                self.assertTrue(west < lon < east and south < lat < north)
        self.assertEqual(len(model["paths"]), 2)
        for path in model["paths"]:
            numbers = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", path)]
            self.assertTrue(path.startswith("M") and path.endswith("Z"))
            self.assertTrue(all(0 < value < 1000 for value in numbers), path)
        self.assertTrue(0 < float(model["point"]["x"]) < 1000 and 0 < float(model["point"]["y"]) < 1000)
        # The frame is square on the ground, so the picture is not stretched.
        import math
        self.assertAlmostEqual((east - west) * 111320 * math.cos(math.radians((north + south) / 2)), (north - south) * 111320, delta=0.5)
        self.assertAlmostEqual((north - south) * 111320, model["size"], delta=0.5)
        self.assertEqual(model["bar"]["metres"], 20)
        self.assertAlmostEqual(model["bar"]["share"], 20 / model["size"])

    def test_a_very_large_parcel_still_gets_a_drawn_background(self):
        # The map service draws nothing above scale 1:6000; a wide frame therefore asks for more pixels.
        half = 0.006
        ring = [[5.0 - half, 51.5 - half], [5.0 + half, 51.5 - half], [5.0 + half, 51.5 + half], [5.0 - half, 51.5 + half], [5.0 - half, 51.5 - half]]
        model, = adres(["mapModel", [{"rings": [ring]}], None])
        width = int(parse_qs(urlsplit(model["image"]).query)["width"][0])
        self.assertLess(model["size"] / (width * 0.00028), 6000)
        self.assertIsNone(model["point"])


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class PublicatiesBijEenAdres(unittest.TestCase):
    """Which notices of the app are about a chosen address."""

    def test_other_spellings_of_the_same_address(self):
        items = [notice("afkorting", "Aanvraag omgevingsvergunning, Burg. van de Mortelplein 118A, 5037 PL Tilburg"),
                 notice("los", "Besluit, burgemeester van de mortelplein 118 a te Tilburg"),
                 notice("streepje", "Verleend: Burgemeester Van De Mortelplein 118-a Tilburg"),
                 notice("omschrijving", "Aanvraag omgevingsvergunning", omschrijving="Z2026-1 - verbouwen, Burgemeester van de Mortelplein 118a"),
                 notice("plaats", "Aanvraag omgevingsvergunning", plaats="Burgemeester van de Mortelplein 118a, 5037PL Tilburg")]
        for entry in items:
            entry.update(lat=MORTELPLEIN["lat"], lon=MORTELPLEIN["lon"])
        self.assertEqual(found(items, MORTELPLEIN), {"adres": ["afkorting", "los", "streepje", "omschrijving", "plaats"], "mogelijk": [], "straat": []})

    def test_str_and_straat_and_spaces(self):
        items = [notice("str", "Kappen boom Heuvelstr. 5 Tilburg"), notice("vol", "Dakkapel Heuvelstraat 5, 5038AA Tilburg"),
                 notice("los", "Dakkapel Heuvel straat 5 Tilburg"), notice("ander", "Dakkapel Heuvelring 5 Tilburg")]
        self.assertEqual(found(items, address("Heuvelstraat", 5, postcode="5038AA"))["adres"], ["str", "vol", "los"])
        items = [notice("los", "Aanvraag Waspikse weg 17A, 5109RE 's Gravenmoer", gemeente="Dongen"), notice("vast", "Aanvraag Waspikseweg 17a", gemeente="Dongen")]
        self.assertEqual(found(items, address("Waspikse weg", 17, "A", postcode="5109RE", gemeente="Dongen"))["adres"], ["los", "vast"])

    def test_addition_decides(self):
        items = [notice("12", "Aanvraag Hoofdstraat 12 Tilburg"), notice("12a", "Aanvraag Hoofdstraat 12a Tilburg"), notice("12b", "Aanvraag Hoofdstraat 12 B Tilburg"),
                 notice("120", "Aanvraag Hoofdstraat 120 Tilburg"), notice("112", "Aanvraag Hoofdstraat 112 Tilburg"), notice("2", "Aanvraag Hoofdstraat 2 Tilburg")]
        self.assertEqual(found(items, address(nummer=12, letter="a")), {"adres": ["12a"], "mogelijk": ["12"], "straat": []})
        self.assertEqual(found(items, address(nummer=12)), {"adres": ["12"], "mogelijk": ["12a", "12b"], "straat": []})
        result, = adres(["findNotices", items, address(nummer=12, letter="a"), []])
        self.assertEqual(result["mogelijk"][0]["reden"], "Het bericht noemt huisnummer 12 zonder toevoeging.")
        result, = adres(["findNotices", items, address(nummer=12), []])
        self.assertEqual(result["mogelijk"][0]["reden"], "Het bericht noemt huisnummer 12a; het gekozen adres heeft geen toevoeging.")

    def test_letter_with_addition(self):
        items = [notice("a1", "Aanvraag Emmastraat 40 a 1 te Goirle", gemeente="Goirle"), notice("a-1", "Aanvraag Emmastraat 40a-1, 5051LN Goirle", gemeente="Goirle"),
                 notice("a2", "Aanvraag Emmastraat 40a-2 Goirle", gemeente="Goirle"), notice("40", "Aanvraag Emmastraat 40 Goirle", gemeente="Goirle")]
        where = address("Emmastraat", 40, "a", "1", postcode="5051LN", gemeente="Goirle")
        self.assertEqual(found(items, where), {"adres": ["a1", "a-1"], "mogelijk": ["40"], "straat": []})
        zeros = [notice("67-1", "Aanvraag Heuvelring 67-1 Tilburg"), notice("67-12", "Aanvraag Heuvelring 67-12 Tilburg")]
        self.assertEqual(found(zeros, address("Heuvelring", 67, toevoeging="01"))["adres"], ["67-1"])

    def test_ranges_and_lists_of_house_numbers(self):
        items = [notice("reeks", "Verduurzamen Predikherenlaan 529-721 Tilburg"), notice("lijst", "Aanvraag Predikherenlaan 601, 603 en 605 Tilburg"),
                 notice("tm", "Aanvraag Predikherenlaan 590 t/m 600 Tilburg")]
        self.assertEqual(found(items, address("Predikherenlaan", 603)), {"adres": ["lijst"], "mogelijk": ["reeks"], "straat": []})
        self.assertEqual(found(items, address("Predikherenlaan", 600)), {"adres": [], "mogelijk": ["reeks", "tm"], "straat": []})
        self.assertEqual(found(items, address("Predikherenlaan", 801)), {"adres": [], "mogelijk": [], "straat": []})
        result, = adres(["findNotices", items, address("Predikherenlaan", 600), []])
        self.assertEqual(result["mogelijk"][0]["reden"], "Het bericht noemt de huisnummers 529 tot en met 721.")

    def test_same_street_and_number_in_another_place(self):
        where = address("Kerkstraat", 12, postcode="5011AA", gemeente="Tilburg", lat=51.56, lon=5.09)
        items = [notice("andere gemeente", "Aanvraag Kerkstraat 12 Dongen", gemeente="Dongen", lat=51.56, lon=5.09),
                 notice("zelfde gemeente ver weg", "Aanvraag Kerkstraat 12 Udenhout", lat=51.61, lon=5.14),
                 notice("zonder plek ander postcodegebied", "Aanvraag Kerkstraat 12, 5071 AA Udenhout", locatieSoort="gemeente", lat=None, lon=None),
                 notice("zonder plek", "Aanvraag Kerkstraat 12", locatieSoort="gemeente", lat=None, lon=None),
                 notice("hier", "Aanvraag Kerkstraat 12, 5011 AA Tilburg", lat=51.5601, lon=5.0901)]
        self.assertEqual(found(items, where), {"adres": ["zonder plek", "hier"], "mogelijk": [], "straat": []})

    def test_a_wrong_postcode_in_the_notice_does_not_hide_it(self):
        # As in gmb-2026-532440: the notice says 5102 AD, the BAG says 5102 AC for Lage Ham 42 in Dongen.
        where = address("Lage Ham", 42, postcode="5102AC", gemeente="Dongen", lat=51.63514482, lon=4.9335373)
        near = notice("bij het adres", "Besluit voor bouwen van een woning op locatie Lage Ham 42, 5102 AD Dongen", gemeente="Dongen", lat=51.6351, lon=4.9336)
        unplaced = notice("zonder plek", "Besluit op locatie Lage Ham 42, 5102 AD Dongen", gemeente="Dongen", locatieSoort="gemeente", lat=None, lon=None)
        result, = adres(["findNotices", [near, unplaced], where, []])
        self.assertEqual([row["id"] for row in result["adres"]], ["bij het adres"])
        self.assertEqual(result["adres"][0]["reden"], "Het bericht noemt postcode 5102 AD; het adres heeft 5102 AC.")
        self.assertEqual([row["id"] for row in result["mogelijk"]], ["zonder plek"])

    def test_longer_street_name_does_not_match(self):
        items = [notice("korte", "Aanvraag Korte Heuvel 12 Tilburg"), notice("ring", "Aanvraag Heuvelring 12 Tilburg"), notice("heuvel", "Aanvraag terras, Heuvel 12 Tilburg")]
        self.assertEqual(found(items, address("Heuvel", 12))["adres"], ["heuvel"])

    def test_street_without_a_house_number_is_listed_apart(self):
        items = [notice("straat", "Kappen van bomen, Kapelmeesterlaan Tilburg"), notice("nummer", "Dakkapel Kapelmeesterlaan 7 Tilburg"),
                 notice("beide", "Rioolwerk Kapelmeesterlaan; dakkapel Kapelmeesterlaan 9 Tilburg"), notice("ver", "Kappen Kapelmeesterlaan Tilburg", lat=51.62, lon=5.09)]
        self.assertEqual(found(items, address("Kapelmeesterlaan", 3)), {"adres": [], "mogelijk": [], "straat": ["straat"]})

    def test_notice_on_the_same_parcel_without_the_address_in_its_text(self):
        where = address("Lage Ham", 42, gemeente="Dongen", lat=51.6351, lon=4.9335)
        items = [notice("getekend", "Aanvraag omgevingsvergunning, Ingetekende geometrie", gemeente="Dongen", lat=51.63512, lon=4.93355),
                 notice("oud nummer", "Termijnverlenging voor bouwen van een woning op locatie Lage Ham 40", gemeente="Dongen", lat=51.63508, lon=4.93349),
                 notice("buren", "Dakkapel Lage Ham 44 Dongen", gemeente="Dongen", lat=51.6356, lon=4.9335),
                 notice("zonder plek", "Aanvraag omgevingsvergunning Dongen", gemeente="Dongen", locatieSoort="gemeente", lat=51.6351, lon=4.9335)]
        self.assertEqual(found(items, where, [square(4.9335, 51.6351)]), {"adres": [], "mogelijk": ["getekend", "oud nummer"], "straat": []})
        self.assertEqual(found(items, where), {"adres": [], "mogelijk": [], "straat": []})  # without the parcel there is nothing to go by
        result, = adres(["findNotices", items, where, [square(4.9335, 51.6351)]])
        self.assertEqual(result["mogelijk"][0]["reden"], "De tekst noemt dit adres niet, maar de locatie van het bericht ligt op hetzelfde perceel.")

    def test_filtered_out_notices_are_searched_too_and_every_class_is_kept(self):
        items = [notice("weg", "Dakkapel Hoofdstraat 12 Tilburg", klasse="weggefilterd"), notice("locatie", "Bouw 8 woningen Hoofdstraat 12 Tilburg", klasse="ontwikkellocatie"),
                 notice("onzeker", "Sloop Hoofdstraat 12 Tilburg", klasse="onzeker")]
        result, = adres(["findNotices", items, address(), []])
        self.assertEqual([(row["id"], row["weggefilterd"]) for row in result["adres"]], [("weg", True), ("locatie", False), ("onzeker", False)])
        self.assertEqual(result["doorzocht"], 3)

    def test_a_row_shows_date_municipality_kind_and_a_link_to_the_source(self):
        items = [notice("gmb-1", "Aanvraag Hoofdstraat 12 Tilburg", datum="2026-11-04", fase="Verleend"),
                 notice("plan", "Ontwerp Hoofdstraat 12 Tilburg", type="plan", soort="Omgevingsplan", fase="Ontwerp", gemeente="", overheid="Noord-Brabant"),
                 notice("onveilig", "Aanvraag Hoofdstraat 12 Tilburg", url="javascript:alert(1)")]
        result, = adres(["findNotices", items, address(), []])
        first, plan, unsafe = result["adres"]
        self.assertEqual((first["datum"], first["gemeente"], first["soort"], first["url"]),
                         ("04-11-2026", "Tilburg", "Vergunning, verleend", "https://zoek.officielebekendmakingen.nl/gmb-1.html"))
        self.assertEqual((plan["gemeente"], plan["soort"]), ("Noord-Brabant", "Omgevingsplan, ontwerp"))
        self.assertIsNone(unsafe["url"])

    def test_one_line_says_which_period_the_list_covers(self):
        usual, other, missing, partial = adres(["periodLine", {"vergunning": 42, "plan": 180, "faillissement": 28, "verkoop": 120}],
                                               ["periodLine", {"vergunning": 30, "plan": 90}], ["periodLine", None], ["periodLine", {"vergunning": 42}])
        closing = ' "Geen publicaties" betekent dus niet dat er nooit iets is geweest.'
        self.assertEqual(usual, "Deze lijst beslaat alleen de laatste 42 dagen voor vergunningen en 180 dagen voor plannen." + closing)
        self.assertEqual(other, "Deze lijst beslaat alleen de laatste 30 dagen voor vergunningen en 90 dagen voor plannen." + closing)
        # Without the numbers the line still warns; it never names a period it does not know.
        self.assertEqual(missing, "Deze lijst beslaat alleen de recente berichten die de app nu heeft." + closing)
        self.assertEqual(partial, missing)
        self.assertEqual(usual.count("."), 2)  # one line of two short sentences

    def test_the_period_in_the_line_is_the_one_the_refresh_uses(self):
        with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as handle:
            config = json.load(handle)["venster_dagen"]
        shown = json.loads(read("data", "berichten.json"))["vensterDagen"]
        self.assertEqual((shown["vergunning"], shown["plan"]), (config["vergunning"], config["plan"]))
        line, = adres(["periodLine", shown])
        self.assertIn("laatste %d dagen voor vergunningen en %d dagen voor plannen" % (config["vergunning"], config["plan"]), line)

    def test_searching_leaves_the_notices_as_they_are(self):
        script = ("var A = require(process.argv[1]); var items = JSON.parse(process.argv[2]); var before = JSON.stringify(items);"
                  "A.findNotices(items, JSON.parse(process.argv[3]), []);"
                  "console.log(JSON.stringify(items) === before ? 'gelijk' : 'gewijzigd');")
        items = [notice("a", "Aanvraag Hoofdstraat 12 Tilburg"), notice("b", "Kappen Hoofdstraat Tilburg"), notice("c", "Iets anders")]
        done = subprocess.run([NODE, "-e", script, os.path.join(SITE, "adres.js"), json.dumps(items), json.dumps(address())], capture_output=True, text=True, timeout=60)
        self.assertEqual(done.stdout.strip(), "gelijk", done.stderr)


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class BronDieNietAntwoordt(unittest.TestCase):
    """An empty or broken answer gives "nothing found", never an error. How the page then looks is
    tested in the browser (tests/test_site.py, InDeBrowser)."""

    def test_empty_answers(self):
        results = adres(["addresses", None], ["addresses", {}], ["addresses", {"response": {"docs": [{}, None]}}], ["parcels", None], ["parcels", {}],
                        ["parcels", {"features": [{"properties": {}, "geometry": None}]}], ["parcelAt", {}, 5.0, 51.5], ["bagModel", None, []],
                        ["pandUrls", None], ["mapModel", [], {"lat": None, "lon": None}])
        self.assertEqual(results, [[], [], [], [], [], [], None, None, [], None])

    def test_building_that_does_not_come_leaves_a_gap(self):
        vbo = FIXTURES["vbo"]["features"][0]
        model, = adres(["bagModel", vbo, [None]])
        self.assertEqual([row["value"] for row in model["rows"]], [None, "gezondheidszorgfunctie", "280 m²", None])
        self.assertTrue(model["pandMissing"])

    def test_notices_that_are_missing_or_incomplete(self):
        empty = {"adres": [], "mogelijk": [], "straat": [], "doorzocht": 0}
        bare = [{"id": "kaal"}, {"id": "leeg", "titel": None, "plaats": None, "gemeente": None, "lat": None, "lon": None},
                {"id": "wel", "titel": "Aanvraag Hoofdstraat 12 Tilburg"}]
        nothing, none, incomplete, no_address = adres(["findNotices", [], address(), []], ["findNotices", None, address(), None],
                                                      ["findNotices", bare, address(), []], ["findNotices", bare, None, []])
        self.assertEqual(nothing, empty)
        self.assertEqual(none, empty)
        self.assertEqual([row["id"] for row in incomplete["adres"]], ["wel"])
        self.assertEqual(no_address, dict(empty, doorzocht=3))


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class EchteGegevens(unittest.TestCase):
    """The notices in site/data/berichten.json as they are in the repository."""

    PLAIN = re.compile(r"^(\D+?) (\d+)([A-Za-z]?), (\d{4} ?[A-Z]{2}) ([^,]+)$")

    @classmethod
    def setUpClass(cls):
        cls.items = json.loads(read("data", "berichten.json"))["berichten"]

    def test_every_notice_with_a_plain_address_is_found_under_that_address(self):
        wanted = []
        for entry in self.items:
            match = self.PLAIN.match(entry.get("plaats") or "")
            if match and entry["locatieSoort"] == "exact":
                wanted.append((entry["id"], address(match.group(1), int(match.group(2)), match.group(3), postcode=match.group(4).replace(" ", ""),
                                                    gemeente=entry["gemeente"], lat=entry["lat"], lon=entry["lon"])))
        self.assertGreater(len(wanted), 100, "te weinig berichten met een gewoon adres om iets te zeggen")
        script = ("var A = require(process.argv[1]); var items = require(process.argv[2]).berichten; var wanted = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
                  "console.log(JSON.stringify(wanted.filter(function (w) { return !A.findNotices(items, w[1], []).adres.some(function (row) { return row.id === w[0]; }); })"
                  ".map(function (w) { return w[0]; })));")
        done = subprocess.run([NODE, "-e", script, os.path.join(SITE, "adres.js"), os.path.join(SITE, "data", "berichten.json")], input=json.dumps(wanted),
                              capture_output=True, text=True, encoding="utf-8", timeout=300)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout), [])

    def test_filtered_out_notices_are_in_the_data_the_tab_searches(self):
        self.assertTrue(any(entry["klasse"] == "weggefilterd" for entry in self.items))


def playwright_available():
    return bool(NODE) and subprocess.run([NODE, "-e", "require('playwright')"], capture_output=True).returncode == 0


@unittest.skipUnless(os.environ.get("TILBURG_ADRES_LIVE") and playwright_available(),
                     "alleen op verzoek, tegen de echte bronnen: TILBURG_ADRES_LIVE=1 python -m unittest tests.test_adres.EchteBronnen")
class EchteBronnen(unittest.TestCase):
    """The tab against the real registers of PDOK, with real addresses in Tilburg, Dongen and Goirle,
    at 320 px. Not part of the normal run: it fails when PDOK does not answer, and the registers
    change over time. With TILBURG_ADRES_SHOTS=<map> the script also saves screenshots there."""

    @classmethod
    def setUpClass(cls):
        import threading
        from functools import partial
        from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=SITE))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            command = [NODE, os.path.join(JS, "adres_live.js"), "http://127.0.0.1:%d" % server.server_address[1]]
            if os.environ.get("TILBURG_ADRES_SHOTS"):
                command.append(os.environ["TILBURG_ADRES_SHOTS"])
            done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=600)
        finally:
            server.shutdown()
            server.server_close()
        if done.returncode:
            raise AssertionError(done.stderr)
        cls.seen = json.loads(done.stdout)
        cls.by_label = {entry["label"]: entry for entry in cls.seen["addresses"]}

    def test_every_address_is_found_and_filled_without_errors(self):
        self.assertEqual(self.seen["errors"], [])
        self.assertEqual(self.seen["hosts"], ["api.pdok.nl", "service.pdok.nl"])
        self.assertEqual(len(self.seen["addresses"]), 7)
        for entry in self.seen["addresses"]:
            with self.subTest(adres=entry["label"]):
                self.assertIn(entry["label"], entry["suggestions"])
                self.assertEqual(entry["failed"], 0, "een bron gaf geen antwoord")
                self.assertRegex(entry["bag"]["Bouwjaar"], r"^\d{4}")
                self.assertRegex(entry["bag"]["Oppervlakte"], r"^[\d.]+ m²$")
                self.assertNotEqual(entry["bag"]["Gebruiksdoel"], "niet bekend")
                self.assertTrue(entry["parcels"])
                for parcel in entry["parcels"]:
                    self.assertRegex(parcel["Aanduiding"], r"^\S.* [A-Z]{1,2} \d+ \([A-Z]{3}\d{2} [A-Z]{1,2} \d+\)$")
                    self.assertRegex(parcel["Grootte"], r"^[\d.]+ m², (vastgesteld|voorlopig)")
                self.assertTrue(entry["map"]["image"], "de achtergrondkaart is niet geladen")
                self.assertEqual(entry["map"]["shapes"], len(entry["parcels"]))
                self.assertLessEqual(entry["overflow"], 0)

    def test_an_addition_gives_its_own_parcel(self):
        with_letter = self.by_label["Tilburgseweg 172e, 5051AM Goirle"]["parcels"]
        without = self.by_label["Tilburgseweg 172, 5051AM Goirle"]["parcels"]
        self.assertEqual(len(with_letter), 1)
        self.assertTrue(with_letter[0]["Aanduiding"].startswith("Goirle E "))
        self.assertNotIn(with_letter[0]["Aanduiding"], [parcel["Aanduiding"] for parcel in without])
        self.assertEqual(self.by_label["Tilburgseweg 172e, 5051AM Goirle"]["name"], "Tilburgseweg 172e")
        self.assertEqual(self.by_label["Heuvelring 67-12, 5038CJ Tilburg"]["name"], "Heuvelring 67-12")

    def test_addresses_outside_the_core_find_the_notices_of_their_region(self):
        # With the region files as they are in the repository (run of 17-11-2026) each of these two
        # addresses has a notice of 16-11-2026. The app itself shows the core; the tab reads the file.
        for label, regio, file in (("Noordweg 402, 4333KK Middelburg", "Zeeland", "regio-zeeland.json"),
                                   ("Prinsenkade 10, 4811VB Breda", "West-Brabant", "regio-west-brabant.json")):
            with self.subTest(adres=label):
                entry = self.by_label[label]
                self.assertEqual(entry["regionFiles"], [file])
                self.assertIn("en die van " + regio, entry["searched"])
                self.assertTrue(entry["notices"].get("Dit adres"), "geen publicatie over dit adres gevonden")
        for label in ("Heuvelring 67-12, 5038CJ Tilburg", "Burgemeester van de Mortelplein 118a, 5037PL Tilburg"):
            self.assertEqual(self.by_label[label]["regionFiles"], [], "voor een adres in Tilburg is een regiobestand gelezen")

    def test_tilburg_and_dongen(self):
        tilburg = self.by_label["Burgemeester van de Mortelplein 118a, 5037PL Tilburg"]
        dongen = self.by_label["Lage Ham 42, 5102AC Dongen"]
        self.assertTrue(all(parcel["Aanduiding"].startswith("Tilburg ") for parcel in tilburg["parcels"]))
        self.assertTrue(all(parcel["Aanduiding"].startswith("Dongen ") for parcel in dongen["parcels"]))
        self.assertEqual(tilburg["links"][0], "https://www.ep-online.nl/Energylabel/Search")
        self.assertRegex(dongen["links"][1], r"^https://omgevingswet\.overheid\.nl/regels-op-de-kaart/documenten\?locatie-stelsel=RD&locatie-x=\d+&locatie-y=\d+$")


class Tabblad(unittest.TestCase):
    """The tab on the page: what it refers to, and what it must not do."""

    def setUp(self):
        self.html = read("index.html")
        self.logic = read("adres.js")
        self.page = read("adres-app.js")

    def test_every_element_the_tab_looks_up_is_on_the_page(self):
        on_page = set(re.findall(r'\sid="([^"]+)"', self.html))
        wanted = set(re.findall(r'\$\("([\w-]+)"\)', self.page))
        self.assertGreaterEqual(len(wanted), 9)
        self.assertEqual(wanted - on_page, set())

    def test_tab_is_the_fourth_next_to_the_existing_three(self):
        tabs = re.findall(r'<a href="#(\w+)" id="tab-(\w+)"', self.html)
        self.assertEqual(tabs, [("berichten", "berichten"), ("gebied", "gebied"), ("bronnen", "bronnen"), ("adres", "adres")])
        views = re.findall(r'<section id="view-(\w+)" class="view"( hidden)?', self.html)
        self.assertEqual(views, [("berichten", ""), ("gebied", " hidden"), ("bronnen", " hidden"), ("adres", " hidden")])
        self.assertIn('var VIEWS = ["berichten", "gebied", "bronnen", "adres"];', read("app.js"))

    def test_tab_builds_text_not_markup(self):
        self.assertNotRegex(self.page, r"innerHTML|insertAdjacentHTML|document\.write")

    def test_only_open_sources_without_a_key(self):
        hosts = set(re.findall(r'"https://([^/"]+)', self.logic + self.page))
        self.assertEqual(hosts, {"api.pdok.nl", "service.pdok.nl", "www.ep-online.nl", "omgevingswet.overheid.nl", "www.openstreetmap.org"})
        for text in (self.logic, self.page):
            self.assertNotRegex(text, r"(?i)api[-_]?key|x-api-key|authorization|bearer|secret|wachtwoord|password")
        # Only PDOK is asked for data; the other three hosts are plain links for the user to tap.
        asked = re.findall(r'var (\w+) = "https://([^/"]+)', self.logic)
        self.assertEqual({name: host for name, host in asked}, {
            "SUGGEST": "api.pdok.nl", "BAG": "api.pdok.nl", "PERCEEL": "api.pdok.nl", "KAART": "service.pdok.nl",
            "EP_ONLINE": "www.ep-online.nl", "REGELS_OP_DE_KAART": "omgevingswet.overheid.nl"})
        self.assertEqual(set(re.findall(r"getJson\(([^)]*?)\)", self.page)) - {"url"},
                         {"A.suggestUrl(text, (loaded && loaded.centrum", "A.vboUrl(address.objectId", "A.perceelUrl(code", "A.perceelAtUrl(address.lon, address.lat"})

    def test_tab_only_reads(self):
        for text in (self.logic, self.page):
            self.assertNotRegex(text, r"localStorage|sessionStorage|indexedDB|ophaalcache|method:|\.setItem\(|sendBeacon")
        self.assertEqual(len(re.findall(r"\bfetch\(", self.page)), 1)
        self.assertNotIn("fetch(", self.logic)

    def test_size_of_the_parcel_carries_the_warning(self):
        self.assertIn("de kadastrale kaart geeft alleen een indicatie van de ligging en de grootte. Er zijn geen maten aan te ontlenen.", self.page)

    def test_energy_label_and_plan_are_marked_as_not_available_with_a_plain_link(self):
        block = re.search(r"function renderLinks\(address\) \{(.*?)\n  \}", self.page, flags=re.S).group(1)
        self.assertEqual(block.count('"Nog niet beschikbaar in de app."'), 2)
        self.assertNotIn("getJson", block)
        links, = adres(["viewerLinks", {"huisnummer": 118, "huisletter": "a", "toevoeging": "", "postcode": "5037PL", "rd": {"x": 132133.035, "y": 395879.872}}]) if NODE else [None]
        if links:
            self.assertEqual(links["energielabel"], {"url": "https://www.ep-online.nl/Energylabel/Search", "label": "Zoek op EP-Online", "zoekwaarde": "5037PL 118 a"})
            self.assertEqual(links["plan"]["url"], "https://omgevingswet.overheid.nl/regels-op-de-kaart/documenten?locatie-stelsel=RD&locatie-x=132133&locatie-y=395880")


if __name__ == "__main__":
    unittest.main()
