"""Cache of downloaded publication texts and parcel sizes, kept in the repository.

A daily run only downloads what it has not seen before; everything else comes from this file.
Once a week (and on request) a full refresh ignores the cache, so corrections at the source come in.

What is stored, per kind:
- tekst:       publication id -> the descriptive opening lines of that publication
- perceel:     RD coordinate -> registered parcel size in m² (null when there is no parcel)
- locatie:     municipality and title of a notice without location -> address found for it (or null)
- gemeente:    RD coordinate -> municipality at that point
- insolventie: id of a court publication -> 0, meaning "read, no company inside the radius".
               Nothing from those publications themselves is stored: they contain personal data
               and git history is permanent. A publication with a hit is simply read again.

Entries that a run did not use are dropped when the cache is saved, so the file stays as large as
the window. Failed downloads are never cached; the next run tries them again.
"""
import collections
import hashlib
import json
import pathlib
import threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAD = ROOT / "cache" / "ophaalcache.json"
VERSIE = 1
SOORTEN = ("tekst", "perceel", "locatie", "gemeente", "insolventie")


def insolventie_sleutel(config):
    """Fingerprint of the settings that decide whether a court publication has a hit."""
    relevant = [config["centrum"]["rd"], config["straal_km"], config["postcode_bereik"], VERSIE]
    return hashlib.sha1(json.dumps(relevant).encode()).hexdigest()[:12]


class Cache:
    def __init__(self, pad=PAD, lezen=True, sleutel=""):
        """`lezen=False` starts empty (a full refresh); the result is still saved afterwards."""
        self.pad = pathlib.Path(pad)
        self.sleutel = sleutel
        self.data = {soort: {} for soort in SOORTEN}
        self.gebruikt = {soort: set() for soort in SOORTEN}
        self.treffers = collections.Counter()
        self.opgehaald = collections.Counter()
        self._lock = threading.Lock()
        if lezen and self.pad.exists():
            stored = json.loads(self.pad.read_text(encoding="utf-8"))
            if stored.get("versie") == VERSIE:
                for soort in SOORTEN:
                    self.data[soort] = stored.get(soort, {})
                if stored.get("insolventieSleutel") != sleutel:
                    self.data["insolventie"] = {}  # radius or postcode range changed: old verdicts no longer hold

    def haal(self, soort, sleutel):
        """Return (found, value)."""
        with self._lock:
            if sleutel in self.data[soort]:
                self.gebruikt[soort].add(sleutel)
                self.treffers[soort] += 1
                return True, self.data[soort][sleutel]
            return False, None

    def zet(self, soort, sleutel, waarde):
        with self._lock:
            self.data[soort][sleutel] = waarde
            self.gebruikt[soort].add(sleutel)
            self.opgehaald[soort] += 1

    def omwikkel(self, soort, functie, sleutel):
        """Wrap `functie` so that a cached answer is returned without calling it.

        `sleutel` turns the arguments into the cache key. An exception from `functie` passes through
        and nothing is stored, so a failed download is tried again next time.
        """
        def met_cache(*args):
            key = sleutel(*args)
            found, value = self.haal(soort, key)
            if found:
                return value
            value = functie(*args)
            self.zet(soort, key, value)
            return value
        return met_cache

    def statistiek(self):
        return {soort: {"uitCache": self.treffers[soort], "opgehaald": self.opgehaald[soort]} for soort in SOORTEN}

    def bewaar(self, snoei=SOORTEN):
        """Write the cache. Kinds listed in `snoei` keep only the entries this run used."""
        stored = {"versie": VERSIE, "insolventieSleutel": self.sleutel}
        for soort in SOORTEN:
            keep = self.gebruikt[soort] if soort in snoei else self.data[soort].keys()
            stored[soort] = {key: self.data[soort][key] for key in keep}
        self.pad.parent.mkdir(parents=True, exist_ok=True)
        # One entry per line and sorted keys: a daily run then changes only a few lines in git.
        self.pad.write_text(json.dumps(stored, ensure_ascii=False, indent=0, sort_keys=True) + "\n", encoding="utf-8")


def tekst_sleutel(url, titel=None, limiet=None):
    """Publication id from the URL of its XML, e.g. 'gmb-2026-534344'."""
    return url.rsplit("/", 1)[-1].removesuffix(".xml")


def perceel_sleutel(x, y):
    return f"{x:.1f},{y:.1f}"
