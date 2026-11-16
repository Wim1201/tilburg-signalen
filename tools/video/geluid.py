"""The sound of the screen recording: where the scenes start in the spoken text, and the mix.

The voice is one recording of the whole text, with a pause of 1.2 seconds between the scenes
(a <break> in the text). `timing` finds those pauses and writes how long each scene lasts, so that
opname.js can film along the voice. `mix` puts the voice and the small sounds under the film.

    python3 geluid.py tekst
    python3 geluid.py timing --stem stem.mp3 --uit timing.json
    python3 geluid.py mix --film stil.mp4 --stem stem.mp3 --gebeurtenissen gebeurtenissen.json \
        --timing timing.json --tik tik.mp3 --signaal signaal.mp3 --veeg veeg.mp3 --uit video.mp4

Needs ffmpeg and ffprobe."""
import argparse
import json
import os
import re
import subprocess
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
PAUZE = '<break time="1.2s"/>'
AANLOOP = 1.2      # seconds of film before the voice starts
UITLOOP = 2.6      # seconds of film after the last scene (the closing card)
NA_STEM = 1.8      # the last scene runs this long after the voice has stopped
VOOR_STEM = 0.3    # a scene starts this long before its first word
PIEK = {"klik": -15.0, "scroll": -24.0, "signaal": -15.0}   # how loud each small sound may peak, in dB; the voice peaks near -3


def scenario(pad=None):
    with open(pad or os.path.join(HIER, "scenario.json"), encoding="utf-8") as handle:
        return json.load(handle)


def spreektekst(scenes):
    """The text for the voice: the scenes in order, with a fixed pause between them."""
    return PAUZE.join(scene["tekst"] for scene in scenes)


def stiltes(uitvoer):
    """Read the silences from what ffmpeg's silencedetect prints: [(start, end), ...]."""
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", uitvoer)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", uitvoer)]
    return [(max(0.0, start), end) for start, end in zip(starts, ends)]


def verwachte_grenzen(scenes, duur):
    """Where each next scene would start if the voice spoke every character equally fast."""
    lengtes = [len(scene["tekst"]) for scene in scenes]
    totaal, som, plekken = float(sum(lengtes)), 0, []
    for lengte in lengtes[:-1]:
        som += lengte
        plekken.append(duur * som / totaal)
    return plekken


def grenzen(gevonden, verwacht, duur, venster=None):
    """The moments (in the recording) at which the next scene starts: just before the voice resumes
    after the pause between two scenes. A calm voice also pauses long between sentences, so the
    length of a silence alone does not say enough: for each scene the longest silence near the
    expected place is taken, and it has to be clearly the longest there."""
    venster = venster or max(2.5, 0.05 * duur)
    gekozen = []
    for plek in verwacht:
        dichtbij = sorted((s for s in gevonden if abs((s[0] + s[1]) / 2 - plek) <= venster and s[0] > 0.3 and s[1] < duur - 0.2),
                          key=lambda s: s[1] - s[0], reverse=True)
        if not dichtbij or dichtbij[0][1] - dichtbij[0][0] < 0.8:
            raise ValueError("geen pauze gevonden rond %.1f s" % plek)
        if len(dichtbij) > 1 and (dichtbij[1][1] - dichtbij[1][0]) > 0.85 * (dichtbij[0][1] - dichtbij[0][0]):
            raise ValueError("rond %.1f s zijn twee pauzes even lang (%.2f s en %.2f s); de grens is niet zeker"
                             % (plek, dichtbij[0][1] - dichtbij[0][0], dichtbij[1][1] - dichtbij[1][0]))
        if gekozen and dichtbij[0][0] <= gekozen[-1][0]:
            raise ValueError("de pauzes rond %.1f s liggen niet in volgorde" % plek)
        gekozen.append(dichtbij[0])
    return [round(end - VOOR_STEM, 3) for start, end in gekozen]


def timing(scenes, scheidingen, duur):
    """How long each scene lasts on film. The film is AANLOOP ahead of the recording."""
    randen = [-0.0] + list(scheidingen) + [duur + NA_STEM]
    lengtes = {scene["id"]: round(randen[i + 1] - randen[i], 3) for i, scene in enumerate(scenes)}
    return {"aanloop": AANLOOP, "uitloop": UITLOOP, "scenes": lengtes, "stem": round(duur, 3),
            "totaal": round(AANLOOP + sum(lengtes.values()) + UITLOOP, 3)}


def geluiden(gebeurtenissen, plan):
    """Which sound plays when: [(seconds on film, kind), ...]. A tick on every tap, a swipe when the
    list starts to scroll, the signal at the opening and on the closing card."""
    lijst = [(0.25, "signaal")]
    for g in gebeurtenissen:
        if g["soort"] in ("klik", "scroll"):
            lijst.append((g["t"], g["soort"]))
        elif g["soort"] == "slot":
            lijst.append((g["t"] + 0.2, "signaal"))
    return sorted(lijst)


def versterking(piek_nu, piek_doel):
    """The factor that brings a sound from its measured peak (dB) to the wanted peak (dB)."""
    return round(10 ** ((piek_doel - piek_nu) / 20.0), 3)


def mix_opdracht(film, stem, bestanden, momenten, aanloop, uit, factoren=None):
    """The ffmpeg command that lays the voice and the sounds under the film.
    bestanden: {"klik": pad, "scroll": pad, "signaal": pad}; factoren: the volume factor per kind."""
    factoren = factoren or {}
    soorten = [soort for soort in ("klik", "scroll", "signaal") if any(s == soort for _, s in momenten)]
    opdracht = ["ffmpeg", "-y", "-loglevel", "error", "-i", film, "-i", stem]
    for soort in soorten:
        opdracht += ["-i", bestanden[soort]]
    delen = ["[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,adelay=%d:all=1[stem]" % round(aanloop * 1000)]
    namen = ["[stem]"]
    for index, soort in enumerate(soorten):
        keren = [t for t, s in momenten if s == soort]
        kopie = ["[%s%d]" % (soort, n) for n in range(len(keren))]
        delen.append("[%d:a]aresample=48000,asplit=%d%s" % (index + 2, len(keren), "".join(kopie)))
        for n, t in enumerate(keren):
            naam = "[%s%duit]" % (soort, n)
            delen.append("%sadelay=%d:all=1,volume=%.3f%s" % (kopie[n], round(t * 1000), factoren.get(soort, 1.0), naam))
            namen.append(naam)
    # apad: the sound goes on (silent) for as long as the film lasts; without it the closing card is cut off where the voice stops.
    delen.append("%samix=inputs=%d:normalize=0:duration=longest,alimiter=limit=0.95,apad[uit]" % ("".join(namen), len(namen)))
    opdracht += ["-filter_complex", ";".join(delen), "-map", "0:v", "-map", "[uit]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                 "-ar", "48000", "-ac", "2", "-shortest", "-movflags", "+faststart", uit]
    return opdracht


def duur_van(pad):
    uitvoer = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pad],
                             capture_output=True, text=True, check=True).stdout
    return float(uitvoer.strip())


def piek_van(pad):
    uitvoer = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", pad, "-af", "volumedetect", "-f", "null", "-"],
                             capture_output=True, text=True, check=True).stderr
    return float(re.search(r"max_volume: (-?[\d.]+) dB", uitvoer).group(1))


def meet_stiltes(pad, drempel="-38dB", minimaal=0.2):
    uitvoer = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", pad, "-af", "silencedetect=noise=%s:d=%s" % (drempel, minimaal),
                              "-f", "null", "-"], capture_output=True, text=True, check=True).stderr
    return stiltes(uitvoer)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("wat", choices=["tekst", "timing", "mix"])
    for naam in ("scenario", "stem", "uit", "film", "gebeurtenissen", "timing", "tik", "signaal", "veeg"):
        parser.add_argument("--" + naam)
    args = parser.parse_args(argv)
    scenes = scenario(args.scenario)["scenes"]
    if args.wat == "tekst":
        print(spreektekst(scenes))
    elif args.wat == "timing":
        duur = duur_van(args.stem)
        gevonden = meet_stiltes(args.stem)
        uitkomst = timing(scenes, grenzen(gevonden, verwachte_grenzen(scenes, duur), duur), duur)
        uitkomst["stiltes"] = [[round(a, 3), round(b, 3)] for a, b in gevonden]
        with open(args.uit, "w", encoding="utf-8") as handle:
            json.dump(uitkomst, handle, indent=1)
        print(json.dumps(uitkomst["scenes"]), uitkomst["totaal"])
    else:
        with open(args.gebeurtenissen, encoding="utf-8") as handle:
            opname = json.load(handle)
        with open(args.timing, encoding="utf-8") as handle:
            plan = json.load(handle)
        momenten = geluiden(opname["gebeurtenissen"], plan)
        bestanden = {"klik": args.tik, "scroll": args.veeg, "signaal": args.signaal}
        factoren = {soort: versterking(piek_van(pad), PIEK[soort]) for soort, pad in bestanden.items()}
        subprocess.run(mix_opdracht(args.film, args.stem, bestanden, momenten, plan["aanloop"], args.uit, factoren), check=True)
        print(json.dumps({"momenten": momenten, "factoren": factoren}))


if __name__ == "__main__":
    main(sys.argv[1:])
