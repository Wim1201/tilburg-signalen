"""Unit tests (no network). Run: python -m unittest discover tests"""
import unittest
import xml.etree.ElementTree as ET

from signalen import bekendmakingen, classify, geo, vlaanderen

CENTRE = (134458.696, 396511.411)  # De Heuvel, Tilburg
AREA = {"Tilburg": {"naam": "Tilburg", "minKm": 0.0}, "Dongen": {"naam": "Dongen", "minKm": 8.2}}

NS = ('xmlns:dcterms="http://purl.org/dc/terms/" xmlns:ow="http://standaarden.overheid.nl/wetgeving/" '
      'xmlns:gzd="http://standaarden.overheid.nl/sru"')


def record(rubric, title, creator, markers, extra=""):
    return ET.fromstring(f"""<record {NS}>
      <dcterms:identifier>gmb-2026-1</dcterms:identifier><dcterms:title>{title}</dcterms:title>
      <dcterms:type scheme="OVERHEIDop.Rubriek">{rubric}</dcterms:type>
      <dcterms:creator>{creator}</dcterms:creator><dcterms:date>2026-11-13</dcterms:date>
      <ow:publicatienaam>Gemeenteblad</ow:publicatienaam>{extra}{markers}
      <gzd:preferredUrl>https://zoek.officielebekendmakingen.nl/gmb-2026-1.html</gzd:preferredUrl>
      <gzd:itemUrl manifestation="html">https://repository.overheid.nl/frbr/x/gmb-2026-1.html</gzd:itemUrl>
      <gzd:itemUrl manifestation="pdf">https://repository.overheid.nl/frbr/x/gmb-2026-1.pdf</gzd:itemUrl>
    </record>""")


def marker(wkt, label="Teststraat 1, Tilburg", gemeente="Tilburg"):
    return (f"<ow:gebiedsmarkering><ow:Punt><ow:geometrie>{wkt}</ow:geometrie><ow:geometrielabel>{label}"
            f"</ow:geometrielabel><ow:ligtInGemeente>{gemeente}</ow:ligtInGemeente></ow:Punt></ow:gebiedsmarkering>")


class GeoTest(unittest.TestCase):
    def test_rd_to_wgs84_matches_pdok(self):
        lat, lon = geo.rd_to_wgs84(*CENTRE)
        self.assertAlmostEqual(lat, 51.55717769, places=4)
        self.assertAlmostEqual(lon, 5.0910001, places=4)
        lat, lon = geo.rd_to_wgs84(134169, 399320)  # pair taken from an official notice
        self.assertAlmostEqual(lat, 51.5824141, places=4)
        self.assertAlmostEqual(lon, 5.0866585, places=4)

    def test_parse_wkt_kinds(self):
        self.assertEqual(geo.parse_wkt("POINT (1 2)"), ("point", [[(1.0, 2.0)]]))
        kind, parts = geo.parse_wkt("MULTIPOLYGON(((0 0,10 0,10 10,0 10,0 0)),((20 20,30 20,30 30,20 20)))")
        self.assertEqual((kind, len(parts)), ("polygon", 2))
        self.assertEqual(geo.parse_wkt("LINESTRING (0 0, 5 5)")[0], "line")

    def test_distance(self):
        kind, parts = geo.parse_wkt("POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0))")
        self.assertEqual(geo.distance((5, 5), kind, parts), 0.0)
        self.assertAlmostEqual(geo.distance((13, 14), kind, parts), 5.0)
        self.assertAlmostEqual(geo.distance((0, 0), "point", [[(3.0, 4.0)]]), 5.0)
        self.assertAlmostEqual(geo.distance((5, 3), "line", [[(0.0, 0.0), (10.0, 0.0)]]), 3.0)


    def test_pin_stays_inside_radius(self):
        kind, parts = geo.parse_wkt("LINESTRING (0 900, 0 5000)")
        self.assertEqual(geo.pin((0, 0), kind, parts, 1000), (0.0, 900.0))  # centre lies outside: nearest vertex
        kind, parts = geo.parse_wkt("POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0))")
        self.assertEqual(geo.pin((0, 0), kind, parts, 1000), (5.0, 5.0))


class ClassifyTest(unittest.TestCase):
    def test_permit_phases_from_real_titles(self):
        cases = {
            "Aanvraag omgevingsvergunning, Dintel 44, 5032CR Tilburg": "Aanvraag",
            "Besluit op aanvraag omgevingsvergunning, Heuvelstraat 5, 5038AA Tilburg": "Besluit",
            "Verlenging beslistermijn Omgevingsvergunning (art. 16.64 Omgevingswet), Teststraat 1": "Beslistermijn verlengd",
            "Reguliere procedure - Aanvraag verleend Zwartland 4, 5051 XJ Goirle": "Verleend",
            "Reguliere procedure - Aanvraag geweigerd Wermenbossestraat 11, 5051 BA Goirle": "Geweigerd",
            "Reguliere procedure - Aanvraag vergunning Tilburgseweg 172 c, 5051 AM Goirle": "Aanvraag",
            "Ingekomen aanvraag omgevingsvergunning, het gewijzigd uitvoeren van een reeds verleende vergunning": "Aanvraag",
            "Ingekomen aanvraag omgevingsvergunning, het plaatsen van een dakkapel met verlengde nokverhoging": "Aanvraag",
            "Aanvraag vergunning voor het wijzigen van een reeds verleende vergunning aan Teststraat 19": "Aanvraag",
            "Vergunning voor het bouwen van een bijgebouw aan Spoordonkseweg 119 5688KC Oirschot": "Verleend",
            "Toestemming voor het bouwen van een woning aan Goudberk 9, 5172 GS Kaatsheuvel": "Verleend",
            "Verlenen omgevingsvergunning reguliere procedure Beerten 2, 5081 AN Hilvarenbeek": "Verleend",
            "Gemeente Heusden - Omgevingsvergunning aangevraagd - Beethovenlaan 76, Drunen, vergroten woning": "Aanvraag",
            "Gemeente Heusden - Omgevingsvergunning verleend - Duinweg, Drunen, kappen twee bomen": "Verleend",
            "Ingetrokken aanvraag omgevingsvergunning De Ruiting 4 en 4a in Esch": "Ingetrokken of buiten behandeling",
            "Kennisgeving verlengen beslistermijn aanvraag omgevingsvergunning, Sportparkweg 9": "Beslistermijn verlengd",
            "Aanvraag omgevingsvergunning voor het kappen van één dode boom is vergunningvrij": "Vergunningvrij",
            "Provincie Noord-Brabant - Besluit verlengen beslistermijn omgevingsvergunning - Vloeiveldweg 5": "Beslistermijn verlengd",
            "GEMEENTE VUGHT BINNENGEKOMEN AANVRAAG OMGEVINGSVERGUNNING – Teststraat 1": "Aanvraag",
        }
        for title, expected in cases.items():
            self.assertEqual(classify.permit_phase(title), expected, title)

    def test_plan_phase_and_kind(self):
        title = "Ontwerp wijziging omgevingsplan Tilburg - Kraaivenstraat 1"
        self.assertEqual((classify.plan_phase(title), classify.plan_kind(title)), ("Ontwerp", "Omgevingsplan"))
        title = "Vastgesteld bestemmingsplan Groeseind 2017, 5e herz (NOAD-terrein)"
        self.assertEqual((classify.plan_phase(title), classify.plan_kind(title)), ("Vastgesteld", "Bestemmingsplan"))
        self.assertEqual(classify.plan_phase("Bestemmingsplan “Akkerstraat 2B” onherroepelijk"), "Onherroepelijk")


class NoticeTest(unittest.TestCase):
    def convert(self, rec, geocode=None):
        return bekendmakingen.to_item(rec, CENTRE, 15000, AREA, geocode=geocode, reverse=None)

    def test_located_notice_gets_distance_and_source(self):
        rec = record("omgevingsvergunning", "Aanvraag omgevingsvergunning, Teststraat 1", "Tilburg",
                     marker("POINT (134458.696 399511.411)"),
                     extra='<ow:activiteit>bouwen</ow:activiteit><ow:activiteit>bouwen</ow:activiteit>')
        item = self.convert(rec)
        self.assertEqual(item["afstandKm"], 3.0)
        self.assertEqual((item["type"], item["fase"], item["locatieSoort"]), ("vergunning", "Aanvraag", "exact"))
        self.assertEqual((item["publicatie"], item["overheid"], item["gemeente"]), ("Gemeenteblad", "Tilburg", "Tilburg"))
        self.assertEqual(item["activiteiten"], ["bouwen"])
        self.assertEqual(item["plaats"], "Teststraat 1, Tilburg")
        self.assertTrue(item["url"].startswith("https://zoek.officielebekendmakingen.nl/"))
        self.assertTrue(item["urlTekst"].endswith("gmb-2026-1.html"))

    def test_notice_outside_radius_is_dropped(self):
        rec = record("omgevingsvergunning", "Aanvraag omgevingsvergunning", "Dongen",
                     marker("POINT (134458.696 411512)", gemeente="Dongen"))
        self.assertIsNone(self.convert(rec))

    def test_nearest_of_several_geometries_counts(self):
        rec = record("omgevingsvergunning", "Aanvraag omgevingsvergunning", "Tilburg",
                     marker("POINT (134458.696 420000)") + marker("POLYGON ((134400 397500, 134500 397500, 134500 397600, 134400 397500))"))
        self.assertEqual(self.convert(rec)["afstandKm"], 1.0)

    def test_plan_without_location_uses_title_address(self):
        rec = record("ruimtelijk plan of omgevingsdocument", "Ontwerp wijziging omgevingsplan Tilburg - Kraaivenstraat 1",
                     "Tilburg", "<ow:gebiedsmarkering><ow:Gemeente><ow:gemeentenaam>Tilburg</ow:gemeentenaam></ow:Gemeente></ow:gebiedsmarkering>")
        item = self.convert(rec, geocode=lambda title, gemeente: ("Kraaivenstraat 1, Tilburg", (134458.696, 401511.411)))
        self.assertEqual((item["locatieSoort"], item["afstandKm"], item["plaats"]), ("benaderd", 5.0, "Kraaivenstraat 1, Tilburg"))
        item = self.convert(rec, geocode=lambda title, gemeente: None)
        self.assertEqual((item["locatieSoort"], item["afstandKm"], item["lat"]), ("gemeente", 0.0, None))

    def test_other_rubrics_and_unlocated_outsiders_are_ignored(self):
        self.assertIsNone(self.convert(record("evenementenvergunning", "Kermis", "Tilburg", marker("POINT (134458 396511)"))))
        self.assertIsNone(self.convert(record("omgevingsvergunning", "Aanvraag", "Rijkswaterstaat", "")))

    def test_query(self):
        query = bekendmakingen.build_query(["Tilburg", "Dongen"], "omgevingsvergunning", "2026-10-05")
        self.assertIn('(dt.creator=="Tilburg" OR dt.creator=="Dongen")', query)
        self.assertIn("dt.date>=2026-10-05", query)

    def test_street_match(self):
        self.assertTrue(bekendmakingen._street_matches("Kraaivenstraat", "Tilburg Kraaivenstraat"))
        self.assertFalse(bekendmakingen._street_matches("Hoofdstraat", "Hoofdstuk"))


class VlaanderenTest(unittest.TestCase):
    def test_running_procedure_uses_submission_date(self):
        props = {"huidige_toestand": "In behandeling (in eerste aanleg)", "datum_indiening": "2026-10-19",
                 "datum_huidige_toestand": "2026-11-16"}
        self.assertEqual(vlaanderen._phase_and_date(props, "2026-10-05"), ("Aanvraag", "2026-10-19"))
        props["datum_indiening"] = "2025-07-09"  # old application: nothing new, even though the status date is today
        self.assertIsNone(vlaanderen._phase_and_date(props, "2026-10-05"))

    def test_decision_uses_status_date(self):
        props = {"huidige_toestand": "Vergunning", "datum_indiening": "2026-04-10", "datum_huidige_toestand": "2026-10-13"}
        self.assertEqual(vlaanderen._phase_and_date(props, "2026-10-05"), ("Verleend", "2026-10-13"))

    def test_item_has_no_applicant(self):
        feature = {"geometry": {"type": "Point", "coordinates": [134458.696, 386511.411]},
                   "properties": {"projectnummer": "2026122934", "handeling_omschrijving": "Nieuwbouw van bijgebouwen",
                                  "omschrijving_projecttype": "Aanvraag omgevingsproject", "datum_indiening": "2026-10-19",
                                  "huidige_toestand": "In behandeling (in eerste aanleg)", "datum_huidige_toestand": "2026-11-16",
                                  "vvo_huidige_toestand": "Ravels", "project_link": "https://example.org", "aanvrager": "Jan Jansen"}}
        item = vlaanderen.to_item(feature, CENTRE, 15000, "2026-10-05", "Ravels")
        self.assertEqual((item["afstandKm"], item["gemeente"], item["fase"]), (10.0, "Ravels (België)", "Aanvraag"))
        self.assertNotIn("Jan Jansen", str(item))


if __name__ == "__main__":
    unittest.main()
