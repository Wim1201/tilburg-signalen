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
PAUZE = '<break time="1.2s" />'
AANLOOP = 1.2      # seconds of film before the voice starts
UITLOOP = 2.6      # seconds of film after the last scene (the closing card)
NA_STEM = 1.8      # the last scene runs this long after the voice has stopped
VOOR_STEM = 0.3    # a scene starts this long before its first word
VOLUME = {"stem": 1.0, "klik": 0.5, "scroll": 0.35, "signaal": 0.45}


def scenario(pad=None):
    with open(pad or os.path.join(HIER, "scenario.json"), encoding="utf-8") as handle:
        return json.load(handle)


def spreektekst(scenes):
    """The text for the voice: the scenes in order, with a fixed pause between them."""
    return (" " + PAUZE + " ").join(scene["tekst"] for scene in scenes)


def stiltes(uitvoer):
    """Read the silences from what ffmpeg's silencedetect prints: [(start, end), ...]."""
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", uitvoer)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", uitvoer)]
    return [(max(0.0, start), end) for start, end in zip(starts, ends)]


def grenzen(gevonden, aantal, duur):
    """The moments (in the recording) at which the next scene starts: just before the voice resumes
    after each of the `aantal` longest silences. Silences at the very start or end do not count."""
    binnen = [(start, end) for start, end in gevonden if start > 0.5 and end < duur - 0.3]
    langste = sorted(sorted(binnen, key=lambda s: s[1] - s[0], reverse=True)[:aantal])
    if len(langste) < aantal:
        raise ValueError("%d pauzes gevonden, %d nodig" % (len(langste), aantal))
    kortste = min(end - start for start, end in langste)
    overige = [end - start for start, end in binnen if (start, end) not in langste]
    if overige and max(overige) > 0.8 * kortste:
        raise ValueError("de pauzes tussen de scenes zijn niet te onderscheiden van de pauzes in de zinnen "
                         "(%.2f s tegen %.2f s)" % (kortste, max(overige)))
    return [round(end - VOOR_STEM, 3) for start, end in langste]


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


def mix_opdracht(film, stem, bestanden, momenten, aanloop, uit):
    """The ffmpeg command that lays the voice and the sounds under the film.
    bestanden: {"klik": pad, "scroll": pad, "signaal": pad}."""
    soorten = [soort for soort in ("klik", "scroll", "signaal") if any(s == soort for _, s in momenten)]
    opdracht = ["ffmpeg", "-y", "-loglevel", "error", "-i", film, "-i", stem]
    for soort in soorten:
        opdracht += ["-i", bestanden[soort]]
    delen = ["[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,adelay=%d:all=1,volume=%.2f[stem]" % (round(aanloop * 1000), VOLUME["stem"])]
    namen = ["[stem]"]
    for index, soort in enumerate(soorten):
        keren = [t for t, s in momenten if s == soort]
        kopie = ["[%s%d]" % (soort, n) for n in range(len(keren))]
        delen.append("[%d:a]aresample=48000,asplit=%d%s" % (index + 2, len(keren), "".join(kopie)))
        for n, t in enumerate(keren):
            naam = "[%s%duit]" % (soort, n)
            delen.append("%sadelay=%d:all=1,volume=%.2f%s" % (kopie[n], round(t * 1000), VOLUME[soort], naam))
            namen.append(naam)
    delen.append("%samix=inputs=%d:normalize=0:duration=longest,alimiter=limit=0.95[uit]" % ("".join(namen), len(namen)))
    opdracht += ["-filter_complex", ";".join(delen), "-map", "0:v", "-map", "[uit]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                 "-ar", "48000", "-ac", "2", "-shortest", "-movflags", "+faststart", uit]
    return opdracht


def duur_van(pad):
    uitvoer = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pad],
                             capture_output=True, text=True, check=True).stdout
    return float(uitvoer.strip())


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
        uitkomst = timing(scenes, grenzen(gevonden, len(scenes) - 1, duur), duur)
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
        subprocess.run(mix_opdracht(args.film, args.stem, {"klik": args.tik, "scroll": args.veeg, "signaal": args.signaal},
                                    momenten, plan["aanloop"], args.uit), check=True)
        print(json.dumps(momenten))


if __name__ == "__main__":
    main(sys.argv[1:])
