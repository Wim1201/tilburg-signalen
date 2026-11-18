"""Tests for the energy label Worker (tools/energielabel): the Cloudflare Worker that asks EP-Online
for the energy label of one address, for the tab "Adres". Without Cloudflare, without network and
without a key: EP-Online's answers are given by the test, after the documentation of its public API
(version 5, public.ep-online.nl/swagger). The parts that run the Worker's code need Node and are
skipped without it.

The address asked for is in the body of a POST and never in the address of the request: on
18-11-2026 the stored logs of Cloudflare turned out to hold the whole address of every request."""
import json
import pathlib
import re
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKER = ROOT / "tools" / "energielabel"
NODE = shutil.which("node")
SITE = "https://wim1201.github.io"
KEY = "NIET_ECHT_alleen_voor_de_test_3f9a"
ENV = {"HERKOMST": SITE, "EP_ONLINE_URL": "https://public.ep-online.nl", "EP_ONLINE_KEY": KEY, "PER_MINUUT": "3", "PER_DAG": "5"}
INVOER = {"postcode": "5037PL", "huisnummer": "118", "huisletter": "a"}
NOW = "2026-11-18T14:30:10Z"   # 15:30:10 in the Netherlands


def registration(klasse="A", registered="2023-06-12", valid="2033-06-12", building="Woningbouw", **extra):
    """A registration as EP-Online returns it (PandEnergielabelV5), with fields the Worker must not pass on."""
    base = {"Registratiedatum": registered + "T00:00:00", "Opnamedatum": "2023-06-01T00:00:00", "Geldig_tot": valid + "T00:00:00",
            "Certificaathouder": "Adviesbureau Voorbeeld B.V.", "Soort_opname": "Basisopname", "Gebouwklasse": building, "Gebouwtype": "Appartement",
            "Postcode": "5037PL", "Huisnummer": 118, "Huisletter": "a", "BAGVerblijfsobjectID": "0855010000123456", "BAGPandIDs": ["0855100000654321"],
            "Bouwjaar": 1968, "Energieklasse": klasse, "EnergieIndex": 1.12, "BerekendeCO2Emissie": 21.4}
    base.update(extra)
    return base


FOUND = {"status": 200, "body": [registration()]}


def worker(*calls):
    done = subprocess.run([NODE, str(ROOT / "tests" / "js" / "run_energielabel.mjs")], input=json.dumps(calls), capture_output=True, text=True,
                          encoding="utf-8", timeout=120)
    if done.returncode:
        raise AssertionError(done.stderr)
    return json.loads(done.stdout)


def series(requests, env=ENV, **scenario):
    return worker(["reeks", dict(scenario, env=env, verzoeken=[dict({"invoer": INVOER, "herkomst": SITE, "nu": NOW}, **request) for request in requests])])[0]


def one(env=ENV, **request):
    return series([request], env=env)[0]


def config():
    """wrangler.jsonc without its comments (each on a line of its own)."""
    text = (WORKER / "wrangler.jsonc").read_text(encoding="utf-8")
    return json.loads("\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//")))


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Gevonden(unittest.TestCase):
    def test_a_label_comes_back_with_the_four_values_the_tab_shows_and_nothing_else(self):
        seen = one(antwoord=FOUND)
        self.assertIsNone(seen["fout"])
        self.assertEqual(seen["antwoord"]["status"], 200)
        self.assertEqual(seen["antwoord"]["body"], {"status": "gevonden", "klasse": "A", "registratiedatum": "2023-06-12", "geldigTot": "2033-06-12", "gebouw": "Woningbouw"})
        text = json.dumps(seen["antwoord"])
        for private in ("Certificaathouder", "Adviesbureau", "0855010000123456", "0855100000654321", "1968", "EnergieIndex", "Appartement"):
            self.assertNotIn(private, text)

    def test_ep_online_is_asked_as_its_documentation_says(self):
        asked = one(antwoord=FOUND)["naarBron"]
        self.assertEqual(len(asked), 1)
        self.assertEqual(asked[0]["url"], "https://public.ep-online.nl/api/v5/PandEnergielabel/Adres?postcode=5037PL&huisnummer=118&huisletter=a")
        self.assertEqual(asked[0]["method"], "GET")
        self.assertEqual(asked[0]["headers"], {"Authorization": KEY, "Accept": "application/json"}, "de sleutel hoort als Authorization-header mee te gaan, zonder iets ervoor")
        self.assertTrue(asked[0]["metTijdslimiet"])
        self.assertEqual(asked[0]["redirect"], "manual", "een doorverwijzing wordt niet gevolgd: de sleutel reist niet mee naar een ander adres")
        self.assertEqual(worker(["WACHT_MS"], ["PAD"]), [8000, "/api/v5/PandEnergielabel/Adres"])

    def test_of_several_registrations_the_last_valid_one_is_shown(self):
        body = [registration("C", "2015-03-01", "2025-03-01"), registration("A", "2023-06-12", "2033-06-12"), registration("B", "2019-01-15", "2029-01-15")]
        self.assertEqual(one(antwoord={"status": 200, "body": body})["antwoord"]["body"]["klasse"], "A")
        self.assertEqual(one(antwoord={"status": 200, "body": list(reversed(body))})["antwoord"]["body"]["klasse"], "A", "de volgorde van EP-Online mag niet uitmaken")

    def test_a_label_is_valid_up_to_and_including_its_last_day(self):
        today, yesterday = "2026-11-18", "2026-11-17"
        picked = worker(["kiesLabel", [registration("D", "2016-11-18", today)], today], ["kiesLabel", [registration("D", "2016-11-17", yesterday)], today])
        self.assertEqual(picked[0]["klasse"], "D")
        self.assertIsNone(picked[1])

    def test_the_day_is_the_dutch_day(self):
        # 23:30 UTC on the 18th is already the 19th in the Netherlands.
        self.assertEqual(worker(["dagVan", "2026-11-18T22:59:59Z"], ["dagVan", "2026-11-18T23:00:00Z"], ["dagVan", "2026-07-01T21:59:59Z"], ["dagVan", "2026-07-01T22:00:00Z"]),
                         ["2026-11-18", "2026-11-19", "2026-07-01", "2026-07-02"])
        expired_today = {"status": 200, "body": [registration("E", "2016-11-18", "2026-11-18")]}
        self.assertEqual(one(antwoord=expired_today, nu="2026-11-18T22:30:00Z")["antwoord"]["status"], 200)
        self.assertEqual(one(antwoord=expired_today, nu="2026-11-18T23:30:00Z")["antwoord"]["status"], 404)

    def test_the_answer_may_only_be_read_by_the_page_of_the_app_and_is_not_kept(self):
        headers = one(antwoord=FOUND)["antwoord"]["headers"]
        self.assertEqual(headers["Access-Control-Allow-Origin"], SITE)
        self.assertEqual((headers["Vary"], headers["Cache-Control"], headers["X-Content-Type-Options"]), ("Origin", "no-store", "nosniff"))
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class NietGevonden(unittest.TestCase):
    def assert_none(self, seen, logged):
        self.assertEqual((seen["antwoord"]["status"], seen["antwoord"]["body"]), (404, {"status": "geen"}))
        self.assertEqual(json.loads(seen["logboek"][0])["energielabel"], logged)
        self.assertEqual(seen["antwoord"]["headers"]["Access-Control-Allow-Origin"], SITE)

    def test_ep_online_knows_no_label_for_the_address(self):
        seen = one(antwoord={"status": 404})
        self.assert_none(seen, "geen")
        self.assertEqual(json.loads(seen["logboek"][0]), {"energielabel": "geen", "bron": 404})

    def test_an_empty_list_is_no_label(self):
        seen = one(antwoord={"status": 200, "body": []})
        self.assert_none(seen, "geen geldig label")
        self.assertEqual(json.loads(seen["logboek"][0]), {"energielabel": "geen geldig label", "bron": 200, "registraties": 0, "zonderKlasse": 0, "zonderDatum": 0, "verlopen": 0})

    def test_only_expired_labels_is_no_valid_label(self):
        seen = one(antwoord={"status": 200, "body": [registration("C", "2015-03-01", "2025-03-01"), registration("F", "2010-01-01", "2020-01-01")]})
        self.assert_none(seen, "geen geldig label")
        self.assertEqual(json.loads(seen["logboek"][0]), {"energielabel": "geen geldig label", "bron": 200, "registraties": 2, "zonderKlasse": 0, "zonderDatum": 0, "verlopen": 2})

    def test_a_registration_without_class_or_dates_is_not_a_label(self):
        broken = [registration(klasse=None), registration(klasse="  "), registration(Geldig_tot=None), registration(Registratiedatum="binnenkort"), None, "tekst", 7]
        seen = one(antwoord={"status": 200, "body": broken})
        self.assert_none(seen, "geen geldig label")
        self.assertEqual(json.loads(seen["logboek"][0]), {"energielabel": "geen geldig label", "bron": 200, "registraties": 7, "zonderKlasse": 5, "zonderDatum": 2, "verlopen": 0})
        found = one(antwoord={"status": 200, "body": broken + [registration("B")]})
        self.assertEqual(found["antwoord"]["body"]["klasse"], "B")
        self.assertEqual(json.loads(found["logboek"][0]), {"energielabel": "gevonden", "bron": 200, "registraties": 8, "zonderKlasse": 5, "zonderDatum": 2, "verlopen": 0})

    def test_the_log_line_tells_the_two_kinds_of_nothing_apart_and_why(self):
        """Found on 18-11-2026 with the real service: two addresses gave "geen" and the answer did
        not say why. The log line does: EP-Online knew nothing (bron 404), or it sent registrations
        that the Worker did not count, and then for which reason."""
        # An answer whose fields are named otherwise than the documentation says: every registration lacks its class.
        renamed = [{"energieklasse": "A", "registratiedatum": "2023-06-12T00:00:00", "geldig_tot": "2033-06-12T00:00:00"}]
        # Dates in a form the Worker does not read.
        dated = [registration(Registratiedatum="12-06-2023", Geldig_tot="12-06-2033")]
        logged = [json.loads(one(antwoord=answer)["logboek"][0]) for answer in ({"status": 404}, {"status": 200, "body": renamed}, {"status": 200, "body": dated})]
        self.assertEqual(logged[0], {"energielabel": "geen", "bron": 404})
        self.assertEqual((logged[1]["bron"], logged[1]["registraties"], logged[1]["zonderKlasse"]), (200, 1, 1))
        self.assertEqual((logged[2]["bron"], logged[2]["registraties"], logged[2]["zonderDatum"]), (200, 1, 1))

    def test_the_counts_say_nothing_of_a_registration(self):
        weighed = worker(["weeg", [registration("A"), registration("C", "2015-03-01", "2025-03-01"), registration(klasse=None)], "2026-11-18"])[0]
        self.assertEqual(weighed["telling"], {"registraties": 3, "zonderKlasse": 1, "zonderDatum": 0, "verlopen": 1})
        self.assertEqual(weighed["label"], {"klasse": "A", "registratiedatum": "2023-06-12", "geldigTot": "2033-06-12", "gebouw": "Woningbouw"})
        self.assertTrue(all(isinstance(value, int) for value in weighed["telling"].values()))


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Toevoeging(unittest.TestCase):
    def asked(self, **address):
        seen = one(invoer=address, antwoord=FOUND)
        self.assertEqual(seen["antwoord"]["status"], 200, address)
        return seen["naarBron"][0]["url"].split("?")[1]

    def test_house_letter_and_addition_go_to_their_own_parameters(self):
        self.assertEqual(self.asked(postcode="5037PL", huisnummer="118"), "postcode=5037PL&huisnummer=118")
        self.assertEqual(self.asked(postcode="5037PL", huisnummer="118", huisletter="a"), "postcode=5037PL&huisnummer=118&huisletter=a")
        self.assertEqual(self.asked(postcode="5037PL", huisnummer="118", toevoeging="2"), "postcode=5037PL&huisnummer=118&huisnummertoevoeging=2")
        self.assertEqual(self.asked(postcode="5037PL", huisnummer="12", huisletter="B", toevoeging="bis1"), "postcode=5037PL&huisnummer=12&huisletter=B&huisnummertoevoeging=bis1")

    def test_empty_letter_and_addition_are_left_out(self):
        self.assertEqual(self.asked(postcode="5037PL", huisnummer="118", huisletter="", toevoeging=""), "postcode=5037PL&huisnummer=118")

    def test_the_postcode_is_written_as_ep_online_wants_it(self):
        self.assertEqual(self.asked(postcode="5037 pl", huisnummer="118"), "postcode=5037PL&huisnummer=118")
        self.assertEqual(self.asked(postcode=" 5037pl ", huisnummer=" 118 "), "postcode=5037PL&huisnummer=118")

    def test_the_letter_goes_on_as_it_was_given(self):
        # Whether EP-Online tells "a" from "A" is not in its documentation; the Worker changes nothing.
        self.assertEqual(self.asked(postcode="5037PL", huisnummer="118", huisletter="A"), "postcode=5037PL&huisnummer=118&huisletter=A")


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class FouteInvoer(unittest.TestCase):
    GOOD = {"postcode": "5037PL", "huisnummer": "118"}
    CASES = {
        "postcode": [{"huisnummer": "118"}, {"postcode": "", "huisnummer": "118"}, {"postcode": "503PL", "huisnummer": "118"}, {"postcode": "0537PL", "huisnummer": "118"},
                     {"postcode": "5037P1", "huisnummer": "118"}, {"postcode": "5037PLX", "huisnummer": "118"}, {"postcode": "5037PL' OR 1=1", "huisnummer": "118"},
                     {"postcode": 5037, "huisnummer": "118"}, {"postcode": ["5037PL"], "huisnummer": "118"}, {"postcode": None, "huisnummer": "118"},
                     {"postcode": {"waarde": "5037PL"}, "huisnummer": "118"}],
        "huisnummer": [{"postcode": "5037PL"}, {"postcode": "5037PL", "huisnummer": ""}, {"postcode": "5037PL", "huisnummer": "0"}, {"postcode": "5037PL", "huisnummer": "018"},
                       {"postcode": "5037PL", "huisnummer": "118a"}, {"postcode": "5037PL", "huisnummer": "123456"}, {"postcode": "5037PL", "huisnummer": "-1"},
                       {"postcode": "5037PL", "huisnummer": "1.5"}, {"postcode": "5037PL", "huisnummer": 118}, {"postcode": "5037PL", "huisnummer": ["118"]},
                       {"postcode": "5037PL", "huisnummer": True}],
        "huisletter": [dict(GOOD, huisletter="ab"), dict(GOOD, huisletter="1"), dict(GOOD, huisletter="é"), dict(GOOD, huisletter=["a"]), dict(GOOD, huisletter=None), dict(GOOD, huisletter=1)],
        "toevoeging": [dict(GOOD, toevoeging="12345"), dict(GOOD, toevoeging="2-3"), dict(GOOD, toevoeging="a b"), dict(GOOD, toevoeging="../"), dict(GOOD, toevoeging=2), dict(GOOD, toevoeging=None)],
    }
    # A body that is no address at all: no JSON, no object, empty, too long (null) or unreadable.
    NO_OBJECT = ["", " ", "postcode=5037PL&huisnummer=118", "{", '"5037PL"', "5037", "null", "true", '["5037PL", "118"]', "[]", '{"postcode": "5037PL", "huisnummer": "118"',
                 None, "KAPOT"]

    def assert_refused(self, seen, field):
        self.assertIsNone(seen["fout"])
        self.assertEqual((seen["antwoord"]["status"], seen["antwoord"]["body"]), (400, {"status": "ongeldig", "veld": field}))
        self.assertEqual(seen["naarBron"], [])
        self.assertIsNone(seen["stand"], "foute invoer telt niet mee voor de grens")

    def test_input_that_ep_online_would_refuse_is_refused_here_and_never_reaches_it(self):
        for field, bodies in self.CASES.items():
            for body in bodies:
                with self.subTest(veld=field, invoer=body):
                    self.assert_refused(one(invoer=body), field)  # no answer given: reaching EP-Online would be a fault

    def test_a_body_that_is_no_address_is_refused(self):
        for text in self.NO_OBJECT:
            with self.subTest(tekst=text):
                self.assert_refused(one(tekst=text), "invoer")

    def test_a_body_is_read_to_a_limit_and_no_further(self):
        limit = worker(["MAX_INVOER"])[0]
        self.assertTrue(200 <= limit <= 1000, "ruim genoeg voor een adres, te klein om iets anders mee te doen")
        address = json.dumps(INVOER)
        whole, pieces, exact, over, endless, empty, none, broken = worker(
            ["leesTekst", [address], limit], ["leesTekst", [address[:7], address[7:20], address[20:]], limit], ["leesTekst", ["x" * limit], limit],
            ["leesTekst", ["x" * limit, "y"], limit], ["leesTekst", ["x" * 300] * 50, limit], ["leesTekst", [], limit], ["leesTekst", None, limit],
            ["leesTekst", [[0xC3, 0x28]], limit])
        self.assertEqual((whole["tekst"], pieces["tekst"]), (address, address))
        self.assertEqual(exact["tekst"], "x" * limit)
        self.assertEqual((over["tekst"], over["afgebroken"]), (None, True))
        self.assertEqual((endless["tekst"], endless["afgebroken"]), (None, True))
        self.assertLessEqual(endless["gelezen"], 3, "een te lange inhoud wordt niet tot het einde gelezen")
        self.assertEqual((empty["tekst"], none["tekst"]), ("", ""))
        self.assertIsNone(broken["tekst"], "bytes die geen UTF-8 zijn, zijn geen adres")
        # Letters outside ASCII count as the bytes they are.
        self.assertIsNone(worker(["leesTekst", ["é" * (limit // 2 + 1)], limit])[0]["tekst"])

    def test_the_formats_are_those_of_the_documentation(self):
        read = worker(["leesAdres", json.dumps({"postcode": "9999ZZ", "huisnummer": "99999", "huisletter": "Z", "toevoeging": "ab12"})],
                      ["leesAdres", json.dumps({"postcode": "1000AA", "huisnummer": "1"})])
        self.assertEqual(read[0], {"adres": {"postcode": "9999ZZ", "huisnummer": "99999", "huisletter": "Z", "toevoeging": "ab12"}})
        self.assertEqual(read[1], {"adres": {"postcode": "1000AA", "huisnummer": "1", "huisletter": "", "toevoeging": ""}})

    def test_names_that_every_object_has_are_no_fields(self):
        # "__proto__" and "constructor" in the body must not stand in for a field.
        read = worker(["leesAdres", '{"__proto__": {"postcode": "5037PL", "huisnummer": "118"}}'], ["leesAdres", '{"constructor": "x", "toString": "y", "postcode": "5037PL", "huisnummer": "118"}'])
        self.assertEqual(read[0], {"fout": "postcode"})
        self.assertEqual(read[1], {"adres": {"postcode": "5037PL", "huisnummer": "118", "huisletter": "", "toevoeging": ""}})

    def test_input_that_ep_online_itself_refuses_comes_back_as_invalid(self):
        seen = one(antwoord={"status": 400, "body": {"title": "One or more validation errors occurred.", "errors": {"huisnummertoevoeging": ["ongeldig"]}}})
        self.assertEqual((seen["antwoord"]["status"], seen["antwoord"]["body"]), (400, {"status": "ongeldig"}))

    def test_only_post_is_answered(self):
        for method in ("GET", "PUT", "DELETE", "PATCH", "HEAD"):
            with self.subTest(methode=method):
                seen = one(method=method)
                self.assertEqual((seen["antwoord"]["status"], seen["antwoord"]["headers"]["Allow"], seen["naarBron"]), (405, "POST, OPTIONS", []))
                self.assertEqual(seen["gelezen"], 0, "van een verzoek dat geen POST is, wordt de inhoud niet gelezen")
                self.assertIsNone(seen["stand"])

    def test_the_address_of_the_request_is_not_looked_at(self):
        """An address in the address of the request (as before 18-11-2026) is not read: asking that
        way must not work, or it would be done and end up in a log."""
        logic = (WORKER / "src" / "energielabel.js").read_text(encoding="utf-8")
        index = (WORKER / "src" / "index.js").read_text(encoding="utf-8")
        for text in (logic, index):
            self.assertNotIn("request.url", text)
            self.assertNotIn("verzoek.url", text)
            self.assertNotIn("searchParams.get", text)
        self.assertIn("tekst: () => leesTekst(request.body, MAX_INVOER)", index)

    def test_the_address_at_ep_online_never_comes_from_the_request(self):
        seen = one(invoer=dict(INVOER, url="https://kwaad.voorbeeld", EP_ONLINE_URL="https://kwaad.voorbeeld", detailaanduiding="x", pad="/api/v5/Mutatiebestand/DownloadInfo"), antwoord=FOUND)
        self.assertEqual(seen["naarBron"][0]["url"], "https://public.ep-online.nl/api/v5/PandEnergielabel/Adres?postcode=5037PL&huisnummer=118&huisletter=a")


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class VerkeerdeHerkomst(unittest.TestCase):
    OTHERS = [None, "", "null", "https://voorbeeld.example", "http://wim1201.github.io", "https://wim1201.github.io.kwaad.example", "https://kwaad.example/https://wim1201.github.io",
              "https://wim1201.github.io:8443", "https://WIM1201.github.io", "https://wim1201.github.io/", "https://sub.wim1201.github.io", "https://xwim1201.github.io"]

    def test_only_the_page_of_the_app_gets_an_answer(self):
        for origin in self.OTHERS:
            with self.subTest(herkomst=origin):
                seen = one(herkomst=origin)  # no answer given: reaching EP-Online would be a fault
                self.assertIsNone(seen["fout"])
                self.assertEqual((seen["antwoord"]["status"], seen["antwoord"]["body"]), (403, {"status": "geweigerd"}))
                self.assertNotIn("Access-Control-Allow-Origin", seen["antwoord"]["headers"])
                self.assertEqual(seen["naarBron"], [])
                self.assertIsNone(seen["stand"], "een geweigerd verzoek telt niet mee voor de grens")
                self.assertEqual(seen["gelezen"], 0, "van een geweigerd verzoek wordt de inhoud niet gelezen")

    def test_a_preflight_from_elsewhere_is_refused_too(self):
        seen = one(method="OPTIONS", herkomst="https://voorbeeld.example")
        self.assertEqual(seen["antwoord"]["status"], 403)
        self.assertNotIn("Access-Control-Allow-Origin", seen["antwoord"]["headers"])

    def test_a_preflight_from_the_app_is_answered_without_asking_ep_online(self):
        seen = one(method="OPTIONS")
        self.assertEqual((seen["antwoord"]["status"], seen["antwoord"]["body"], seen["naarBron"], seen["stand"]), (204, None, [], None))
        headers = seen["antwoord"]["headers"]
        self.assertEqual((headers["Access-Control-Allow-Origin"], headers["Access-Control-Allow-Methods"], headers["Access-Control-Allow-Headers"]), (SITE, "POST", "Content-Type"))
        self.assertEqual(seen["gelezen"], 0)

    def test_without_the_setting_nobody_gets_an_answer(self):
        for env in (dict(ENV, HERKOMST=""), {key: value for key, value in ENV.items() if key != "HERKOMST"}):
            self.assertEqual(one(env=env)["antwoord"]["status"], 403)
            self.assertEqual(one(env=env, herkomst="")["antwoord"]["status"], 403)

    def test_the_setting_is_the_live_site(self):
        self.assertEqual(config()["vars"]["HERKOMST"], SITE)


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Begrenzing(unittest.TestCase):
    """PER_MINUUT is 3 and PER_DAG is 5 in these tests, counted over everyone together."""

    @staticmethod
    def at(time, **request):
        return dict({"nu": "2026-11-18T" + time + "Z", "antwoord": FOUND}, **request)

    def statuses(self, requests, **scenario):
        return [seen["antwoord"]["status"] for seen in series(requests, **scenario)]

    def test_the_fourth_request_in_a_minute_is_refused_and_not_passed_on(self):
        seen = series([self.at("14:30:01"), self.at("14:30:20"), self.at("14:30:40"), self.at("14:30:50", antwoord=None)])
        self.assertEqual([entry["antwoord"]["status"] for entry in seen], [200, 200, 200, 429])
        refused = seen[3]
        self.assertIsNone(refused["fout"])
        self.assertEqual(refused["antwoord"]["body"], {"status": "teveel", "grens": "minuut"})
        self.assertEqual(refused["antwoord"]["headers"]["Retry-After"], "10", "tot het einde van de klokminuut")
        self.assertEqual(refused["antwoord"]["headers"]["Access-Control-Allow-Origin"], SITE, "de app moet kunnen lezen dat het te veel was")
        self.assertEqual(refused["naarBron"], [])

    def test_the_next_minute_opens_again(self):
        self.assertEqual(self.statuses([self.at("14:30:01"), self.at("14:30:02"), self.at("14:30:03"), self.at("14:30:59", antwoord=None), self.at("14:31:00")]), [200, 200, 200, 429, 200])

    def test_a_refused_request_is_not_counted(self):
        seen = series([self.at("14:30:01"), self.at("14:30:02"), self.at("14:30:03")] + [self.at("14:30:1%d" % n, antwoord=None) for n in range(5)])
        self.assertEqual(seen[-1]["stand"], {"minuut": seen[2]["stand"]["minuut"], "inMinuut": 3, "dag": "2026-11-18", "inDag": 3})

    def test_the_sixth_request_of_a_day_is_refused_until_the_dutch_midnight(self):
        times = ["09:00:00", "10:00:00", "11:00:00", "12:00:00", "13:00:00"]
        seen = series([self.at(time) for time in times] + [self.at("14:30:00", antwoord=None), self.at("22:59:30", antwoord=None), self.at("23:00:00")])
        self.assertEqual([entry["antwoord"]["status"] for entry in seen], [200] * 5 + [429, 429, 200])
        self.assertEqual(seen[5]["antwoord"]["body"], {"status": "teveel", "grens": "dag"})
        self.assertEqual(seen[5]["antwoord"]["headers"]["Retry-After"], str(8 * 3600 + 30 * 60), "tot middernacht in Nederland: van 15:30 tot 24:00 uur")
        self.assertEqual(seen[6]["antwoord"]["headers"]["Retry-After"], "30")
        self.assertEqual(seen[7]["stand"]["dag"], "2026-11-19")

    def test_the_day_limit_wins_from_the_minute_limit(self):
        seen = series([self.at("14:30:01", antwoord=None)], stand={"minuut": 29916870, "inMinuut": 3, "dag": "2026-11-18", "inDag": 5})
        self.assertEqual(seen[0]["antwoord"]["body"], {"status": "teveel", "grens": "dag"})

    def test_every_request_that_reaches_ep_online_counts_whatever_the_answer(self):
        answers = [{"status": 404}, {"status": 500}, {"fout": "TimeoutError"}]
        self.assertEqual(self.statuses([self.at("14:30:0%d" % n, antwoord=answer) for n, answer in enumerate(answers)] + [self.at("14:30:30", antwoord=None)]), [404, 502, 502, 429])

    def test_when_the_counter_does_not_answer_nothing_is_asked_of_ep_online(self):
        seen = series([self.at("14:30:01", antwoord=None)], tellerKapot=True)[0]
        self.assertIsNone(seen["fout"])
        self.assertEqual((seen["antwoord"]["status"], seen["antwoord"]["body"], seen["naarBron"]), (503, {"status": "onbereikbaar"}, []))

    def test_settings_that_are_no_number_fall_back_to_the_defaults(self):
        env = dict(ENV, PER_MINUUT="veel", PER_DAG="-4")
        self.assertEqual(self.statuses([self.at("14:30:%02d" % n) for n in range(20)] + [self.at("14:30:40", antwoord=None)], env=env), [200] * 20 + [429])

    def test_the_limits_in_the_settings_are_numbers_within_reason(self):
        settings = config()["vars"]
        self.assertTrue(1 <= int(settings["PER_MINUUT"]) <= 60)
        self.assertTrue(int(settings["PER_MINUUT"]) <= int(settings["PER_DAG"]) <= 2000)


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class DienstAntwoordtNiet(unittest.TestCase):
    def assert_unreachable(self, seen, logged):
        self.assertIsNone(seen["fout"])
        self.assertEqual((seen["antwoord"]["status"], seen["antwoord"]["body"]), (502, {"status": "onbereikbaar"}))
        self.assertEqual(seen["antwoord"]["headers"]["Access-Control-Allow-Origin"], SITE, "de app moet kunnen lezen wat er mis is")
        self.assertEqual(json.loads(seen["logboek"][0])["energielabel"], logged)

    def test_ep_online_does_not_answer_in_time(self):
        seen = one(antwoord={"fout": "TimeoutError"})
        self.assert_unreachable(seen, "bron antwoordt niet")
        self.assertEqual(json.loads(seen["logboek"][0]), {"energielabel": "bron antwoordt niet", "fout": "TimeoutError"})

    def test_the_connection_fails(self):
        self.assert_unreachable(one(antwoord={"fout": "TypeError"}), "bron antwoordt niet")

    def test_ep_online_answers_with_a_fault(self):
        for status in (500, 502, 503, 301, 302, 418):
            with self.subTest(status=status):
                self.assert_unreachable(one(antwoord={"status": status, "body": {"title": "kapot"}}), "bron geeft een fout")

    def test_ep_online_answers_with_something_that_is_no_list(self):
        self.assert_unreachable(one(antwoord={"status": 200, "tekst": "<html>Onderhoud</html>"}), "bron onleesbaar")
        self.assert_unreachable(one(antwoord={"status": 200, "body": {"Energieklasse": "A"}}), "bron onleesbaar")

    def test_ep_online_refuses_the_key(self):
        for status in (401, 403):
            with self.subTest(status=status):
                seen = one(antwoord={"status": status})
                self.assert_unreachable(seen, "sleutel geweigerd")
                self.assertEqual(json.loads(seen["logboek"][0])["bron"], status)

    def test_ep_online_says_too_many_requests(self):
        seen = one(antwoord={"status": 429})
        self.assertEqual((seen["antwoord"]["status"], seen["antwoord"]["body"]), (429, {"status": "teveel", "grens": "bron"}))

    def test_without_the_key_nothing_is_asked(self):
        for env in (dict(ENV, EP_ONLINE_KEY=""), {key: value for key, value in ENV.items() if key != "EP_ONLINE_KEY"}):
            seen = one(env=env)
            self.assertEqual((seen["antwoord"]["status"], seen["antwoord"]["body"], seen["naarBron"], seen["stand"]), (503, {"status": "onbereikbaar"}, [], None))


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class DeSleutelEnHetAdresBlijvenBinnen(unittest.TestCase):
    """The key is in no answer and in no log line; the address is in no log line."""

    def test_in_every_outcome(self):
        outcomes = [dict(antwoord=FOUND), dict(antwoord={"status": 404}), dict(antwoord={"status": 401}), dict(antwoord={"status": 500, "body": {"detail": KEY}}),
                    dict(antwoord={"fout": "TimeoutError"}), dict(antwoord={"status": 200, "tekst": "kapot " + KEY}), dict(herkomst="https://voorbeeld.example"),
                    dict(invoer={"postcode": "5037PL", "huisnummer": "118x"}), dict(tekst="5037PL 118"), dict(tekst=None), dict(method="OPTIONS"), dict(method="GET"),
                    dict(antwoord={"status": 200, "body": [registration(klasse=KEY[:10]), registration("B")]}),
                    dict(antwoord={"status": 200, "body": [registration("C", "2015-03-01", "2025-03-01")]}), dict(antwoord={"status": 400}), dict(antwoord={"status": 429})]
        for outcome in outcomes:
            with self.subTest(uitkomst=outcome):
                seen = one(**outcome)
                self.assertIsNone(seen["fout"])
                answer, log = json.dumps(seen["antwoord"]), "\n".join(seen["logboek"])
                self.assertNotIn(KEY, answer)
                self.assertNotIn(KEY, log)
                for part in ("5037PL", "5037", "118", "huisnummer", "postcode", "workers.dev", "Adviesbureau", "0855"):
                    self.assertNotIn(part, log, "een logregel hoort het adres niet te bevatten, en niets uit een registratie")
                self.assertEqual(len(seen["logboek"]), 1, "één regel per verzoek")

    def test_the_key_is_nowhere_in_the_repository(self):
        # Everything git would take along: what is tracked and what is new and not ignored.
        tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "tools/energielabel", "site", "config.json"],
                                 cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        self.assertIn("tools/energielabel/wrangler.jsonc", tracked)
        self.assertFalse([name for name in tracked if pathlib.PurePath(name).name in (".dev.vars", ".env")], "een bestand met geheimen hoort niet in de repo")
        for name in tracked:
            if name.endswith((".png", ".svg", ".ico", ".json")) and not name.endswith(("wrangler.jsonc", "config.json", "package.json")):
                continue
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(bestand=name):
                self.assertIsNone(re.search(r"EP_ONLINE_KEY\s*[=:]\s*[\"']?[A-Za-z0-9]{12,}", text), "hier lijkt een sleutel te staan")

    def test_secret_files_stay_out_of_git(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
        self.assertIn(".dev.vars*", ignored)
        self.assertIn(".env*", ignored)
        self.assertIn(".wrangler/", ignored)
        probe = subprocess.run(["git", "check-ignore", "tools/energielabel/.dev.vars", "tools/energielabel/.wrangler/state", "tools/energielabel/.env"],
                               cwd=ROOT, capture_output=True, text=True).stdout.split()
        self.assertEqual(len(probe), 3, "git zou een bestand met geheimen of de lokale toestand van wrangler meenemen")


class Instellingen(unittest.TestCase):
    """wrangler.jsonc and the entry file, read as text: what only exists at Cloudflare."""

    def setUp(self):
        self.config = config()
        self.index = (WORKER / "src" / "index.js").read_text(encoding="utf-8")
        self.logic = (WORKER / "src" / "energielabel.js").read_text(encoding="utf-8")

    def test_the_key_is_a_required_secret_and_not_a_setting(self):
        self.assertEqual(self.config["secrets"], {"required": ["EP_ONLINE_KEY"]})
        self.assertNotIn("EP_ONLINE_KEY", self.config["vars"])
        self.assertEqual(sorted(self.config["vars"]), ["EP_ONLINE_URL", "HERKOMST", "PER_DAG", "PER_MINUUT"])

    def test_ep_online_is_asked_at_its_documented_address(self):
        self.assertEqual(self.config["vars"]["EP_ONLINE_URL"], "https://public.ep-online.nl")

    def test_the_worker_has_an_address_and_its_own_name(self):
        self.assertEqual((self.config["name"], self.config["main"], self.config["workers_dev"]), ("tilburg-signalen-energielabel", "src/index.js", True))
        planner = (ROOT / "tools" / "planner" / "wrangler.jsonc").read_text(encoding="utf-8")
        self.assertIn('"name": "tilburg-signalen-planner"', planner)
        self.assertNotIn("energielabel", planner)
        self.assertNotIn("triggers", self.config, "deze Worker draait alleen op verzoek, niet op een klok")

    def test_the_counter_is_one_object_with_its_own_storage(self):
        self.assertEqual(self.config["durable_objects"], {"bindings": [{"name": "TELLER", "class_name": "Teller"}]})
        self.assertEqual(self.config["migrations"], [{"tag": "v1", "new_sqlite_classes": ["Teller"]}])
        self.assertIn("export class Teller extends DurableObject", self.index)
        self.assertIn('env.TELLER.get(env.TELLER.idFromName("alle"))', self.index)
        self.assertIn("telOp(this.ctx.storage, perMinuut, perDag, nu)", self.index)

    def test_cloudflare_keeps_nothing_of_a_request(self):
        """Found on 18-11-2026: with the logs on, Cloudflare stored for every request its whole
        address (then with postcode and house number), its headers and the IP address of the
        visitor. Whether the Worker's own lines carry those too is not in the documentation, so
        nothing is stored at all; watching live (wrangler tail) is not storing."""
        self.assertEqual(self.config["observability"], {
            "enabled": False, "redact_query_string": True,
            "logs": {"enabled": False, "invocation_logs": False, "persist": False},
            "traces": {"enabled": False, "persist": False}})
        for sink in ("tail_consumers", "logpush", "analytics_engine_datasets"):
            self.assertNotIn(sink, self.config, "een tweede plek waar verzoeken worden vastgelegd")

    def test_the_readme_says_what_is_and_is_not_recorded(self):
        readme = (WORKER / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("Nooit het adres en nooit de sleutel", readme, "die bewering klopte niet zolang Cloudflare het logboek bewaarde")
        self.assertIn("Cloudflare bewaart van deze Worker geen logboek", readme)
        self.assertIn("IP-adres", readme)
        self.assertNotRegex(readme, r"workers\.dev/\?postcode=", "een voorbeeld met het adres in het webadres")

    def test_the_entry_file_passes_on_the_origin_and_nothing_else_of_the_visitor(self):
        self.assertIn('herkomst: request.headers.get("Origin")', self.index)
        self.assertEqual(re.findall(r"request\.headers\.get\(\"([^\"]+)\"\)", self.index), ["Origin"])
        for header in ("CF-Connecting-IP", "X-Forwarded-For", "User-Agent", "Cookie"):
            self.assertNotIn(header, self.index + self.logic)
        self.assertNotIn("request.cf", self.index + self.logic)

    def test_nothing_is_stored_but_the_two_counts(self):
        self.assertEqual(re.findall(r"opslag\.put\(([^,]+),", self.logic), ['"stand"'])
        self.assertIn('await opslag.put("stand", { minuut, inMinuut: inMinuut + 1, dag, inDag: inDag + 1 });', self.logic)
        for store in ("kv_namespaces", "r2_buckets", "d1_databases", "caches.default", "cache.put"):
            self.assertNotIn(store, json.dumps(self.config) + self.index + self.logic)

    def test_cloudflare_knows_the_way_a_redirect_is_handled(self):
        # Found in Cloudflare's own runtime on 18-11-2026: redirect "error" does not exist there and
        # made every request to EP-Online fail.
        self.assertNotIn('redirect: "error"', self.logic)
        self.assertIn('redirect: "manual"', self.logic)

    def test_no_packages_are_needed(self):
        package = json.loads((WORKER / "package.json").read_text(encoding="utf-8"))
        self.assertEqual((package["name"], package["type"], package.get("dependencies"), package.get("devDependencies")), ("tilburg-signalen-energielabel", "module", None, None))
        self.assertEqual(re.findall(r"(?m)^import .* from \"([^\"]+)\";", self.index), ["cloudflare:workers", "./energielabel.js"])
        self.assertEqual(re.findall(r"(?m)^import ", self.logic), [])


if __name__ == "__main__":
    unittest.main()
