"""Tests for the screen recording (tools/video): the scenario, the timeline, where the scenes start
in the spoken text, the mix, and the film itself once it is in docs/.

Parts need Node, Playwright, ffmpeg or ffprobe and are skipped without them."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO = os.path.join(ROOT, "tools", "video")
SITE = os.path.join(ROOT, "site")
sys.path.insert(0, VIDEO)
import geluid  # noqa: E402

NODE = shutil.which("node")
FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")
FILM = os.path.join(ROOT, "docs", "video", "tilburg-signalen_ochtendronde.mp4")


def tijdlijn(*calls):
    done = subprocess.run([NODE, os.path.join(ROOT, "tests", "js", "run_logic.js"), os.path.join(VIDEO, "tijdlijn.js")],
                          input=json.dumps(calls), capture_output=True, text=True, encoding="utf-8", timeout=60)
    if done.returncode:
        raise AssertionError(done.stderr)
    return json.loads(done.stdout)


def read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as handle:
        return handle.read()


def playwright_available():
    return bool(NODE) and subprocess.run([NODE, "-e", "require('playwright')"], capture_output=True).returncode == 0


class Scenario(unittest.TestCase):
    def setUp(self):
        self.scenario = geluid.scenario()
        self.scenes = self.scenario["scenes"]

    def test_shows_what_was_asked_for_in_order(self):
        self.assertEqual([scene["id"] for scene in self.scenes], ["ochtend", "top10", "details", "onzeker", "slot"])

    def test_every_target_is_something_the_app_has(self):
        html, app = read(SITE, "index.html"), read(SITE, "app.js")
        ids = set(re.findall(r'\sid="([^"]+)"', html))
        classes = set(re.findall(r'el\("\w+", "([\w -]+)"', app)) | {"card"}
        classes = {name for group in classes for name in group.split()}
        for scene in self.scenes:
            for step in scene["stappen"]:
                target = step.get("doel")
                if not target or target == "top":
                    continue
                with self.subTest(doel=target):
                    for name in re.findall(r"#([\w-]+)", target):
                        self.assertIn(name, ids)
                    for name in re.findall(r"\.([a-z][\w-]*)", target):
                        self.assertIn(name, classes)

    def test_spoken_text_is_the_scenes_with_a_pause_between_them(self):
        text = geluid.spreektekst(self.scenes)
        self.assertEqual(text.count(geluid.PAUZE), len(self.scenes) - 1)
        self.assertEqual([part.strip() for part in text.split(geluid.PAUZE)], [scene["tekst"] for scene in self.scenes])
        self.assertNotRegex(text.replace(geluid.PAUZE, ""), r"\d", "getallen staan in woorden, anders leest de stem ze onvoorspelbaar")

    def test_what_is_said_about_number_one_is_in_the_data(self):
        items = json.loads(read(SITE, "data", "berichten.json"))["berichten"]
        top = max((entry for entry in items if entry["klasse"] == "ontwikkellocatie"), key=lambda entry: entry["score"])
        said = next(scene["tekst"] for scene in self.scenes if scene["id"] == "top10")
        self.assertIn("Bellinistraat", top["titel"])
        self.assertEqual(top["woningen"], 141)
        self.assertIn("Bellinistraat", said)
        self.assertIn("honderdeenenveertig woningen", said)


@unittest.skipUnless(NODE, "Node is niet geïnstalleerd")
class Tijdlijn(unittest.TestCase):
    SCENARIO = {"scenes": [
        {"id": "a", "kop": "A", "tekst": "Een.", "stappen": [{"op": 0.0, "actie": "wijs", "doel": "#x"}, {"op": 0.5, "actie": "tik", "doel": "#x"}]},
        {"id": "b", "kop": "B", "tekst": "Twee.", "stappen": [{"op": 0.25, "actie": "scroll", "doel": "top", "tot": 0.75}, {"op": 0.8, "actie": "slot"}]},
    ]}
    TIMING = {"aanloop": 1.0, "uitloop": 2.0, "scenes": {"a": 4.0, "b": 8.0}}

    def test_scenes_follow_each_other_and_steps_land_inside_their_scene(self):
        plan, = tijdlijn(["bouw", self.SCENARIO, self.TIMING])
        self.assertEqual([(s["id"], s["start"], s["eind"]) for s in plan["scenes"]], [("a", 1.0, 5.0), ("b", 5.0, 13.0)])
        self.assertEqual([(s["actie"], s["start"], s["eind"]) for s in plan["stappen"]],
                         [("wijs", 1.0, None), ("tik", 3.0, None), ("scroll", 7.0, 11.0), ("slot", 11.4, None)])
        self.assertEqual(plan["totaal"], 15.0)
        self.assertEqual(plan["frames"], 450)

    def test_a_scene_without_a_length_is_refused(self):
        with self.assertRaises(AssertionError):
            tijdlijn(["bouw", self.SCENARIO, {"aanloop": 1, "uitloop": 1, "scenes": {"a": 4.0}}])

    def test_mistakes_in_a_scenario_are_named(self):
        wrong = {"scenes": [{"id": "a", "kop": "A", "tekst": " ", "stappen": [
            {"op": 0.5, "actie": "wijs", "doel": "#x"}, {"op": 0.2, "actie": "tik", "doel": "#x"}, {"op": 0.6, "actie": "spring", "doel": "#x"},
            {"op": 0.7, "actie": "scroll", "doel": "top"}, {"op": 1.4, "actie": "wijs"}]}]}
        good, bad = tijdlijn(["controleer", self.SCENARIO], ["controleer", wrong])
        self.assertEqual(good, [])
        self.assertEqual(len(bad), 6)
        for part in ("geen tekst", "begint voor de vorige stap", "onbekende actie spring", "scroll heeft een eind", "tussen 0 en 1", "geen doel"):
            self.assertTrue(any(part in line for line in bad), part)

    def test_the_scenario_in_the_repository_is_sound(self):
        problems, = tijdlijn(["controleer", geluid.scenario()])
        self.assertEqual(problems, [])

    def test_pointer_eases_from_start_to_end(self):
        values = tijdlijn(["tussen", 10, 110, -1], ["tussen", 10, 110, 0], ["tussen", 10, 110, 0.5], ["tussen", 10, 110, 1], ["tussen", 10, 110, 3])
        self.assertEqual(values, [10, 10, 60, 110, 110])
        early, late = tijdlijn(["ease", 0.1], ["ease", 0.9])
        self.assertLess(early, 0.1)
        self.assertGreater(late, 0.9)


class Geluid(unittest.TestCase):
    SCENES = [{"id": "a", "tekst": "Een."}, {"id": "b", "tekst": "Twee."}, {"id": "c", "tekst": "Drie."}]
    FFMPEG_OUT = """
[silencedetect @ 0x1] silence_start: -0.01
[silencedetect @ 0x1] silence_end: 0.21 | silence_duration: 0.22
[silencedetect @ 0x1] silence_start: 3.1
[silencedetect @ 0x1] silence_end: 3.5 | silence_duration: 0.4
[silencedetect @ 0x1] silence_start: 6.02
[silencedetect @ 0x1] silence_end: 7.6 | silence_duration: 1.58
[silencedetect @ 0x1] silence_start: 12.0
[silencedetect @ 0x1] silence_end: 13.5 | silence_duration: 1.5
[silencedetect @ 0x1] silence_start: 15.9
[silencedetect @ 0x1] silence_end: 16.3 | silence_duration: 0.4
"""

    def test_scene_starts_just_before_the_voice_resumes_after_the_long_pauses(self):
        found = geluid.stiltes(self.FFMPEG_OUT)
        self.assertEqual(found[0], (0.0, 0.21))
        self.assertEqual(len(found), 5)
        self.assertEqual(geluid.grenzen(found, 2, 16.3), [7.3, 13.2])

    def test_too_few_or_unclear_pauses_are_refused(self):
        found = geluid.stiltes(self.FFMPEG_OUT)
        with self.assertRaisesRegex(ValueError, "2 pauzes gevonden, 3 nodig"):
            geluid.grenzen([s for s in found if s[1] - s[0] > 1], 3, 16.3)
        with self.assertRaisesRegex(ValueError, "niet te onderscheiden"):
            geluid.grenzen(found + [(9.0, 10.3)], 2, 16.3)

    def test_scene_lengths_add_up_to_the_film(self):
        plan = geluid.timing(self.SCENES, [7.3, 13.2], 16.3)
        self.assertEqual(plan["scenes"], {"a": 7.3, "b": 5.9, "c": 4.9})
        self.assertAlmostEqual(plan["totaal"], geluid.AANLOOP + 16.3 + geluid.NA_STEM + geluid.UITLOOP, places=3)

    def test_sounds_follow_what_happens_on_screen(self):
        events = [{"t": 1.2, "soort": "scene"}, {"t": 5.0, "soort": "tik"}, {"t": 5.35, "soort": "klik"}, {"t": 9.0, "soort": "scroll"},
                  {"t": 20.0, "soort": "slot"}, {"t": 3.0, "soort": "wijs"}]
        self.assertEqual(geluid.geluiden(events, {}), [(0.25, "signaal"), (5.35, "klik"), (9.0, "scroll"), (20.2, "signaal")])

    def test_mix_puts_every_sound_at_its_moment_and_leaves_the_picture_alone(self):
        moments = [(0.25, "signaal"), (5.35, "klik"), (7.0, "klik"), (20.2, "signaal")]
        command = geluid.mix_opdracht("film.mp4", "stem.mp3", {"klik": "tik.mp3", "scroll": "veeg.mp3", "signaal": "s.mp3"}, moments, 1.2, "uit.mp4")
        graph = command[command.index("-filter_complex") + 1]
        self.assertEqual(command.count("-i"), 4, "de veeg komt niet voor en hoort er dan niet in")
        self.assertNotIn("veeg.mp3", command)
        for delay in ("adelay=1200:all=1", "adelay=250:all=1", "adelay=5350:all=1", "adelay=7000:all=1", "adelay=20200:all=1"):
            self.assertIn(delay, graph)
        self.assertIn("amix=inputs=5:normalize=0", graph)
        self.assertEqual(command[command.index("-c:v") + 1], "copy")
        self.assertLess(geluid.VOLUME["klik"], geluid.VOLUME["stem"])

    @unittest.skipUnless(FFMPEG, "ffmpeg is niet geïnstalleerd")
    def test_pauses_are_found_in_a_real_sound_file(self):
        pattern = [("toon", 2.0), ("stil", 0.4), ("toon", 1.5), ("stil", 1.3), ("toon", 2.5), ("stil", 0.35), ("toon", 1.0), ("stil", 1.3), ("toon", 1.2)]
        inputs, labels = [], ""
        for index, (kind, seconds) in enumerate(pattern):
            source = "sine=frequency=220:duration=%s" % seconds if kind == "toon" else "anullsrc=r=44100:cl=mono:d=%s" % seconds
            inputs += ["-f", "lavfi", "-t", str(seconds), "-i", source]
            labels += "[%d:a]" % index
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "stem.mp3")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", labels + "concat=n=%d:v=0:a=1" % len(pattern), path], check=True)
            total = geluid.duur_van(path)
            starts = geluid.grenzen(geluid.meet_stiltes(path), 2, total)
        self.assertAlmostEqual(total, sum(seconds for _, seconds in pattern), delta=0.15)
        self.assertAlmostEqual(starts[0], 2.0 + 0.4 + 1.5 + 1.3 - geluid.VOOR_STEM, delta=0.12)
        self.assertAlmostEqual(starts[1], 2.0 + 0.4 + 1.5 + 1.3 + 2.5 + 0.35 + 1.0 + 1.3 - geluid.VOOR_STEM, delta=0.12)


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@unittest.skipUnless(playwright_available(), "Playwright is niet geïnstalleerd")
class Droogloop(unittest.TestCase):
    """The scenario is walked through the real app without filming."""

    @classmethod
    def setUpClass(cls):
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Quiet, directory=SITE))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            done = subprocess.run([NODE, os.path.join(VIDEO, "opname.js"), "--base", "http://127.0.0.1:%d" % server.server_address[1], "--droog"],
                                  capture_output=True, text=True, encoding="utf-8", timeout=180)
        finally:
            server.shutdown()
            server.server_close()
        if done.returncode:
            raise AssertionError(done.stderr)
        cls.run_ = json.loads(done.stdout)

    def test_every_step_is_carried_out_without_errors(self):
        self.assertEqual(self.run_["fouten"], [])
        self.assertEqual(self.run_["nietUitgevoerd"], 0)
        taps = [event["doel"] for event in self.run_["gebeurtenissen"] if event["soort"] == "klik"]
        self.assertEqual(taps, ["#tile-nieuw", "#tile-ranglijst", "#list .card:nth-of-type(1) .toggle", "#tile-onzeker", "#brand h1"])

    def test_it_is_a_morning_with_something_new_and_ends_on_the_ranking(self):
        end = self.run_["eind"]
        self.assertTrue(end["ochtend"].startswith("Goedemorgen"), end["ochtend"])
        self.assertRegex(end["zin"], r"^\d+ nieuwe ontwikkellocatie")
        self.assertEqual(end["gekozen"], "tile-ranglijst")
        self.assertEqual(end["kaarten"], 10)


@unittest.skipUnless(FFMPEG and os.path.isfile(FILM), "de film staat nog niet in docs/video of ffprobe ontbreekt")
class Film(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height", "-of", "json", FILM],
                             capture_output=True, text=True, check=True).stdout
        cls.info = json.loads(out)

    def test_between_sixty_and_ninety_seconds(self):
        self.assertTrue(60 <= float(self.info["format"]["duration"]) <= 90, self.info["format"]["duration"])

    def test_picture_and_sound(self):
        streams = {stream["codec_type"]: stream for stream in self.info["streams"]}
        self.assertEqual((streams["video"]["codec_name"], streams["video"]["width"], streams["video"]["height"]), ("h264", 1920, 1080))
        self.assertEqual(streams["audio"]["codec_name"], "aac")

    def test_small_enough_for_the_repository(self):
        self.assertLess(os.path.getsize(FILM), 15_000_000)


if __name__ == "__main__":
    unittest.main()
