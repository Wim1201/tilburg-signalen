"""Tests for the relevance rules and the new sources (no network). Run: python -m unittest discover tests"""
import unittest
import xml.etree.ElementTree as ET

from signalen import bekendmakingen, geo, insolventies, relevantie, tekst, update

CENTRE = (134458.696, 396511.411)
O, U, W = relevantie.ONTWIKKELLOCATIE, relevantie.ONZEKER, relevantie.WEGGEFILTERD


def oordeel(soort, titel, tekst_="", perceel=None, fase="Aanvraag", activiteiten=(), **kwargs):
    facts = relevantie.kenmerken(soort, titel, tekst_, activiteiten)
    return relevantie.beoordeel(soort, facts, perceel, fase, **kwargs)


class WoningenTest(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(relevantie.count_dwellings("het bouwen van 12 appartementen"), 12)
        self.assertEqual(relevantie.count_dwellings("bouwen van zeven aaneen gebouwde woningen"), 7)
        self.assertEqual(relevantie.count_dwellings("sloop van 2 woningen en nieuwbouw van 14 levensloopbestendige woningen"), 14)
        self.assertIsNone(relevantie.count_dwellings("het bouwen van 3 dakkapellen op woningen"))
        self.assertIsNone(relevantie.count_dwellings("het kappen van 12 bomen bij de woningen"))
        self.assertIsNone(relevantie.count_dwellings("uitbreiden van de woning over 2 bouwlagen"))

    def test_two_or_more_new_dwellings_is_a_development_location(self):
        klasse, score, waarom = oordeel("vergunning", "Aanvraag omgevingsvergunning, Bredaseweg 90", "bouwen 12 appartementen")
        self.assertEqual((klasse, waarom), (O, "12 nieuwe woningen."))
        self.assertEqual(oordeel("vergunning", "transformatie van kantoor naar 24 woningen")[0], O)
        self.assertGreater(oordeel("vergunning", "bouwen 40 woningen")[1], score)  # more dwellings rank higher

    def test_single_dwelling_and_renovation_are_filtered(self):
        klasse, _, waarom = oordeel("vergunning", "het bouwen van een woning en het aanleggen van een inrit", perceel=900)
        self.assertEqual((klasse, waarom), (W, "Nieuwbouw van één woning, zonder ander ontwikkelsignaal."))
        self.assertEqual(oordeel("vergunning", "het renoveren van 48 woningen")[0], W)
        self.assertEqual(oordeel("vergunning", "het verduurzamen van 24 woningen")[0], W)

    def test_unknown_number_is_uncertain_not_hidden(self):
        klasse, _, waarom = oordeel("vergunning", "het bouwen van woningen aan de Dorpsstraat")
        self.assertEqual(klasse, U)
        self.assertIn("aantal staat niet", waarom)
        self.assertEqual(oordeel("vergunning", "nieuwbouw appartementencomplex")[0], U)


class SignaalTest(unittest.TestCase):
    def test_each_signal_is_recognised(self):
        cases = {
            "het slopen van een bedrijfspand": "sloop",
            "functiewijziging van winkel naar woning": "functiewijziging",
            "het omzetten van een bedrijfsbestemming naar wonen": "functiewijziging",
            "het splitsen van het perceel in twee bouwkavels": "kavelsplitsing",
            "Aanvraag nieuwe verkaveling": "kavelsplitsing",
            "het wijzigen van de bestemming zodat een BSO mogelijk is": "bestemmingswijziging",
            "buitenplanse omgevingsplanactiviteit voor een nieuw bedrijfsgebouw": "bestemmingswijziging",
            "herontwikkeling van het voormalige kantoorpand": "leegstaand bedrijfspand",
        }
        for text, signal in cases.items():
            self.assertIn(signal, relevantie.kenmerken("vergunning", text, "")["signalen"], text)
        self.assertIn("sloop", relevantie.kenmerken("vergunning", "Aanvraag", "", ["slopen"])["signalen"])

    def test_small_jobs_are_not_signals(self):
        for text in ["het plaatsen van een dakkapel in afwijking van het omgevingsplan", "het kappen van een boom",
                     "het plaatsen van reclame", "het aanleggen van een uitweg"]:
            self.assertEqual(relevantie.kenmerken("vergunning", text, "")["signalen"], [], text)

    def test_parcel_threshold(self):
        self.assertEqual(oordeel("vergunning", "het slopen van een loods", perceel=1850)[::2], (O, "Sloop op een perceel van 1.850 m²."))
        self.assertEqual(oordeel("vergunning", "het slopen van een loods", perceel=400)[0], O)
        klasse, _, waarom = oordeel("vergunning", "het slopen van een schuur", perceel=399)
        self.assertEqual((klasse, waarom), (W, "Sloop op een perceel van 399 m²: kleiner dan 400 m²."))

    def test_unknown_parcel_size_is_uncertain(self):
        klasse, _, waarom = oordeel("vergunning", "functiewijziging van winkel naar woning", perceel=None)
        self.assertEqual(klasse, U)
        self.assertIn("perceelgrootte is niet te bepalen", waarom)

    def test_no_signal_is_filtered_and_missing_description_is_uncertain(self):
        self.assertEqual(oordeel("vergunning", "het kappen van een boom")[0], W)
        self.assertEqual(oordeel("vergunning", "Besluit omgevingsvergunning, Grotestraat 12", informatief=False)[0], U)

    def test_needs_area(self):
        facts = relevantie.kenmerken("vergunning", "het slopen van een loods", "")
        self.assertTrue(relevantie.needs_area("vergunning", facts))
        self.assertFalse(relevantie.needs_area("vergunning", relevantie.kenmerken("vergunning", "bouwen 12 woningen", "")))
        self.assertFalse(relevantie.needs_area("vergunning", relevantie.kenmerken("vergunning", "kappen boom", "")))
        self.assertTrue(relevantie.needs_area("faillissement", facts))


class PlanEnRangTest(unittest.TestCase):
    def test_plan_that_enables_development_ranks_highest(self):
        plan = oordeel("plan", "Ontwerp wijziging omgevingsplan Tilburg - Kraaivenstraat 1", "Het plan maakt de bouw van 16 woningen mogelijk", fase="Ontwerp")
        height = oordeel("plan", "Wijziging omgevingsplan Stationsstraat", "de maximale bouwhoogte wordt 25 meter", fase="Ontwerp")
        permit = oordeel("vergunning", "bouwen 300 woningen")
        signal = oordeel("vergunning", "het slopen van een loods", perceel=50000)
        self.assertEqual(plan[0], O)
        self.assertIn("wonen", plan[2])
        self.assertIn("bouwhoogte", height[2])
        self.assertGreater(min(plan[1], height[1]), permit[1])
        self.assertGreater(permit[1], signal[1])

    def test_thematic_and_unclear_plans(self):
        self.assertEqual(oordeel("plan", "Vastgesteld omgevingsprogramma water en riolering")[0], W)
        self.assertEqual(oordeel("plan", "Wijzigingsbesluit TAM-omgevingsplan Hoofdstuk 22s, Bellinistraat")[0], U)
        self.assertEqual(oordeel("plan", "Kennisgeving voornemen wijziging Omgevingsplan", locatie_bekend=False)[0], W)

    def test_withdrawn_and_refused_rank_lower(self):
        normal = oordeel("vergunning", "bouwen 12 woningen")[1]
        self.assertEqual(oordeel("vergunning", "bouwen 12 woningen", fase="Ingetrokken of buiten behandeling")[1], normal - 25)
        self.assertEqual(oordeel("vergunning", "bouwen 12 woningen", fase="Geweigerd")[1], normal - 15)

    def test_every_verdict_has_one_sentence(self):
        for args in [("vergunning", "bouwen 12 woningen"), ("vergunning", "kappen boom"), ("plan", "Omgevingsvisie"),
                     ("faillissement", "Faillissement X B.V."), ("verkoop", "Voornemen verkoop grond")]:
            waarom = oordeel(*args)[2]
            self.assertTrue(waarom.endswith(".") and waarom.count(". ") == 0, waarom)


class VerkoopEnFaillissementTest(unittest.TestCase):
    def test_sale_notices(self):
        self.assertTrue(bekendmakingen.is_sale_notice("Voornemen van de gemeente om gemeentegrond te verkopen"))
        self.assertTrue(bekendmakingen.is_sale_notice("Openbare kennisgeving – Voornemen tot verkoop gemeentegrond (Didam-publicatie)"))
        self.assertFalse(bekendmakingen.is_sale_notice("Besluit op aanvraag ontheffing voor standplaats oliebollen verkoop"))
        self.assertFalse(bekendmakingen.is_sale_notice("Voornemen van de gemeente om gemeentegrond te verhuren"))

    def test_sale_verdicts(self):
        self.assertEqual(oordeel("verkoop", "Voornemen verkoop gemeentegrond", perceel=900)[0], O)
        self.assertEqual(oordeel("verkoop", "Voornemen verkoop gemeentegrond", perceel=35)[0], W)
        self.assertEqual(oordeel("verkoop", "Voornemen verkoop gemeentegrond")[0], U)
        self.assertEqual(oordeel("verkoop", "Voornemen tot verkoop van snippergroen", perceel=900)[0], W)
        self.assertEqual(relevantie.area_in_text("een perceel grond, groot circa 1.250 m², en 35 m2"), 1250)
        self.assertIsNone(relevantie.area_in_text("geen maat genoemd"))

    def test_bankruptcy_verdicts(self):
        self.assertEqual(oordeel("faillissement", "Faillissement X B.V.", perceel=2400)[0], O)
        self.assertEqual(oordeel("faillissement", "Faillissement X B.V.", perceel=150)[0], W)
        self.assertEqual(oordeel("faillissement", "Faillissement X B.V.")[0], U)


BV = ("Uitspraak faillissement op 03 november 2026 inzake (F.02/26/288) Voorbeeld Metaal B.V, corr.adr. Postbus 1 5000AA Tilburg, "
      "vest.adr. Fabriekstraat 12 a 5038EN Tilburg, KvK: 12345678 hodn Voorbeeld Metaal vest.adr. Fabriekstraat 12 a 5038EN Tilburg. "
      "Cur: mr A.B. Curator, Postbus 9 5000AA TILBURG tel. 013-0000000. RC: mr. C. Rechter.")
RECORD = {"overheid": "Rechtbank Zeeland-West-Brabant", "datum": "2026-11-04", "url": "https://zoek.officielebekendmakingen.nl/stcrt-1.html", "urlTekst": None}


def bag(uses, rd=(134458.696, 399511.411)):
    return lambda postcode, number: [{"gebruiksdoel": set(uses), "oppervlakte": 800, "woonplaats": "Tilburg",
                                      "straat": "Fabriekstraat", "huisletter": "a", "rd": rd}]


class InsolventieTest(unittest.TestCase):
    def test_company_is_parsed_without_trustee(self):
        case = insolventies.parse_entry(BV)
        self.assertEqual((case["naam"], case["zaak"], case["kvk"]), ("Voorbeeld Metaal B.V.", "F.02/26/288", "12345678"))
        self.assertEqual(case["adressen"], [{"straat": "Fabriekstraat", "huisnummer": 12, "toevoeging": "a", "postcode": "5038EN", "plaats": "Tilburg"}])
        self.assertNotIn("Curator", str(case))

    def test_private_persons_and_sole_traders_are_skipped(self):
        person = ("Uitspraak faillissement op 03 november 2026 inzake (F.02/26/1) J. Jansen, woonadr. Straat 1 5000AA Tilburg, "
                  "geb. Tilburg 1 januari 1980 hodn Jansen Bouw B.V. vest.adr. Straat 1 5000AA Tilburg, KvK: 12345678.")
        sole = "Uitspraak faillissement op 03 november 2026 inzake (F.02/26/2) Klusbedrijf Pietersen, vest.adr. Straat 2 5000AA Tilburg, KvK: 12345678."
        vof = "Uitspraak faillissement op 03 november 2026 inzake (F.02/26/3) Jansen en Pietersen V.O.F., vest.adr. Straat 3 5000AA Tilburg, KvK: 12345678."
        debt = "Uitspraak schuldsanering op 03 november 2026 inzake (R.02/26/4) Voorbeeld B.V., vest.adr. Straat 4 5000AA Tilburg."
        for entry in (person, sole, vof, debt):
            self.assertIsNone(insolventies.parse_entry(entry), entry[:60])

    def test_only_new_bankruptcies_and_moratoria(self):
        ended = BV.replace("Uitspraak faillissement op", "Wegens gebrek aan baten op")
        self.assertIsNone(insolventies.parse_entry(ended))
        moratorium = BV.replace("Uitspraak faillissement op 03 november 2026 inzake", "verlening voorlopige surseance op 03 november 2026 aan:").replace("F.02", "S.02")
        self.assertEqual(insolventies.parse_entry(moratorium)["soort"], "Surseance verleend")

    def convert(self, lookup):
        return insolventies.to_item(insolventies.parse_entry(BV), RECORD, CENTRE, 15000, {"Tilburg": "Tilburg"}, [[4840, 5299]], lookup)

    def test_business_premises_inside_radius_become_an_item(self):
        item = self.convert(bag(["industriefunctie", "kantoorfunctie"]))
        self.assertEqual((item["type"], item["afstandKm"], item["gemeente"]), ("faillissement", 3.0, "Tilburg"))
        self.assertEqual(item["plaats"], "Fabriekstraat 12a, 5038EN Tilburg")
        self.assertNotIn("Curator", str(item))
        self.assertNotIn("Rechter", str(item))

    def test_home_address_outside_radius_and_outside_postcode_range_are_dropped(self):
        self.assertIsNone(self.convert(bag(["woonfunctie"])))
        self.assertIsNone(self.convert(bag(["industriefunctie"], rd=(134458.696, 420000.0))))
        self.assertIsNone(self.convert(lambda postcode, number: []))
        case = insolventies.parse_entry(BV.replace("5038EN", "9723BX"))
        self.assertIsNone(insolventies.to_item(case, RECORD, CENTRE, 15000, {}, [[4840, 5299]], bag(["industriefunctie"])))

    def test_entries_are_split_per_list_item(self):
        xml = "<x><metadata/></metadata><lijst><li><al>Een</al></li><li><al>Twee</al></li></lijst></x>"
        self.assertEqual([e.strip() for e in insolventies.entries(xml)], ["Een", "Twee"])


class TekstEnVerrijkingTest(unittest.TestCase):
    def test_excerpt_stops_at_boilerplate(self):
        xml = ("<p><metadata>x</metadata><t>GEMEENTEBLAD Aanvraag vergunning Dorpsstraat 1</t><al>De gemeente heeft een aanvraag ontvangen "
               "voor het bouwen van 6 woningen.</al><al>Bezwaar: u kunt bezwaar maken tegen het slopen.</al></p>")
        excerpt = tekst.uittreksel(xml, "Aanvraag vergunning Dorpsstraat 1")
        self.assertIn("6 woningen", excerpt)
        self.assertNotIn("slopen", excerpt)

    def test_area_helpers(self):
        kind, parts = geo.parse_wkt("POLYGON ((0 0, 20 0, 20 30, 0 30, 0 0))")
        self.assertEqual(geo.area(parts), 600)
        self.assertTrue(geo.contains((5, 5), parts))
        self.assertFalse(geo.contains((25, 5), parts))
        record = ET.fromstring('<r xmlns:o="x"><o:Perceel><o:geometrie>POLYGON ((0 0, 20 0, 20 30, 0 30, 0 0))</o:geometrie></o:Perceel>'
                               '<o:Perceel><o:geometrie>POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0))</o:geometrie></o:Perceel></r>')
        self.assertEqual(bekendmakingen.parcel_area(record), 700)

    def item(self, **fields):
        base = {"id": "1", "type": "vergunning", "titel": "Aanvraag omgevingsvergunning, Dorpsstraat 1", "omschrijving": None,
                "activiteiten": [], "fase": "Aanvraag", "locatieSoort": "exact", "_rd": (1.0, 2.0), "_perceelM2": None, "_urlXml": "u"}
        base.update(fields)
        return base

    def test_enrichment_uses_text_and_parcel_lookup(self):
        calls = []
        items = update.verrijk(
            [self.item(), self.item(id="2", omschrijving="het kappen van een boom")], 400,
            haal_tekst=lambda url, titel, limiet: "het slopen van een loods",
            perceel_m2=lambda x, y: calls.append((x, y)) or 1200)
        self.assertEqual((items[0]["klasse"], items[0]["perceelM2"], items[0]["signalen"]), (O, 1200, ["sloop"]))
        self.assertEqual((items[1]["klasse"], items[1]["perceelM2"]), (W, None))
        self.assertEqual(calls, [(1.0, 2.0)])  # the parcel is only looked up where it decides the outcome
        self.assertFalse([key for key in items[0] if key.startswith("_")])

    def test_enrichment_without_text_or_parcel_is_uncertain(self):
        items = update.verrijk([self.item(), self.item(id="2", omschrijving="het slopen van een loods")], 400,
                               haal_tekst=lambda url, titel, limiet: None, perceel_m2=lambda x, y: None)
        self.assertEqual([i["klasse"] for i in items], [U, U])

    def test_sale_notice_takes_size_from_text(self):
        items = update.verrijk([self.item(type="verkoop", titel="Voornemen verkoop gemeentegrond", _rd=None, fase="Voornemen tot verkoop")], 400,
                               haal_tekst=lambda url, titel, limiet: "een perceel van circa 1.250 m² aan de Dorpsstraat",
                               perceel_m2=lambda x, y: None)
        self.assertEqual((items[0]["klasse"], items[0]["perceelM2"]), (O, 1250))


if __name__ == "__main__":
    unittest.main()
