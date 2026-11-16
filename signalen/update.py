"""Daily update: fetch all sources, judge relevance and write site/data/berichten.json.

Run: python -m signalen.update
"""
import collections
import concurrent.futures
import datetime
import json
import pathlib
import sys
import time
import zoneinfo

from . import bekendmakingen, gebied, insolventies, perceel, relevantie, tekst, vlaanderen, volledigheid

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "site" / "data" / "berichten.json"
SOURCES = pathlib.Path(__file__).with_name("bronnen.json")
WORKERS = 4  # modest on purpose: the sources are public services
RETRY_SECONDS = 180  # time allowed for trying failed downloads once more
MAX_RETRY_WACHT = 20  # seconds; longest pause before a retry


def _since(today, days):
    return (today - datetime.timedelta(days=days)).isoformat()


def _alle(functie, argumenten, pool, slaap=time.sleep):
    """Call `functie` for every argument tuple in parallel. Returns (results, statistiek).

    results is a list of (value, ok). A call that fails is tried once more, one at a time, after the
    parallel round: a public service that refuses a burst of requests usually answers a calm one.
    Before each retry there is a pause that doubles while the service keeps failing, up to
    MAX_RETRY_WACHT seconds, and drops back after a success. The whole retry round stops after
    RETRY_SECONDS.
    """
    def probeer(args):
        try:
            return functie(*args), True
        except Exception as error:
            return error, False

    def oorzaak(error):
        return getattr(error, "reden", None) or type(error).__name__

    results = list(pool.map(probeer, argumenten))
    eerste = [value for value, ok in results if not ok]
    redenen = collections.Counter(oorzaak(error) for error in eerste)
    deadline = time.monotonic() + RETRY_SECONDS
    wacht = 1
    for index, (value, ok) in enumerate(results):
        if ok or time.monotonic() >= deadline:
            continue
        slaap(wacht)
        results[index] = probeer(argumenten[index])
        wacht = 1 if results[index][1] else min(MAX_RETRY_WACHT, wacht * 2)
    definitief = [value for value, ok in results if not ok]
    statistiek = {"gevraagd": len(argumenten), "eersteRondeMislukt": len(eerste),
                  "hersteld": len(eerste) - len(definitief), "definitiefMislukt": len(definitief),
                  "redenen": dict(redenen.most_common(5))}
    return [(value if ok else None, ok) for value, ok in results], statistiek


def verrijk(items, drempel, haal_tekst=tekst.haal_op, perceel_m2=perceel.kadaster_m2, slaap=time.sleep):
    """Add klasse, score, waarom, signalen, woningen and perceelM2 to every item (in place).

    Returns (items, statistiek); statistiek holds, for 'tekst' and 'perceel', how many downloads were
    asked, failed, recovered on retry and failed for good, with the causes. A notice whose text could
    not be fetched is marked 'onzeker' with that reason, and the next run tries again.
    """
    statistiek = {}
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as pool:
        # 1. Notices without a description in their metadata: read the opening lines of the publication.
        need_text = [i for i in items if i.get("_urlXml") and (i["type"] in ("plan", "verkoop") or not i["omschrijving"])]
        arguments = [(i["_urlXml"], i["titel"], 1500 if i["type"] == "plan" else 600) for i in need_text]
        texts, statistiek["tekst"] = _alle(haal_tekst, arguments, pool, slaap)
        for item, (text, ok) in zip(need_text, texts):
            item["_tekst"] = text
            item["_tekstMislukt"] = not ok

        # 2. Facts from the text.
        for item in items:
            description = " ".join(filter(None, [item["omschrijving"], item.get("_tekst")]))
            item["_feiten"] = relevantie.kenmerken(item["type"], item["titel"], description, item["activiteiten"])
            if item["type"] == "verkoop" and not item.get("_perceelM2"):
                # Sale notices usually state the size of the land in the text.
                item["_perceelM2"] = relevantie.area_in_text(" ".join([item["titel"], description]))

        # 3. Parcel size, only where it decides the outcome and the notice itself does not settle it.
        need_area = [i for i in items if i.get("_rd") and relevantie.needs_area(i["type"], i["_feiten"])
                     and (i.get("_perceelM2") or 0) < drempel]
        sizes, statistiek["perceel"] = _alle(perceel_m2, [i["_rd"] for i in need_area], pool, slaap)
        for item, (size, ok) in zip(need_area, sizes):
            if size:
                item["_perceelM2"] = max(size, item.get("_perceelM2") or 0)

    # 4. Verdict.
    for item in items:
        facts = item["_feiten"]
        size = item.get("_perceelM2") if relevantie.needs_area(item["type"], facts) or item.get("_perceelM2") else None
        informative = item["type"] != "vergunning" or bool(item["omschrijving"] or item.get("_tekst")) or not item.get("_urlXml")
        klasse, score, waarom = relevantie.beoordeel(
            item["type"], facts, size, item["fase"], informatief=informative,
            locatie_bekend=item["locatieSoort"] != "gemeente", drempel=drempel,
            tekst_mislukt=bool(item.get("_tekstMislukt")))
        item.update({"klasse": klasse, "score": score, "waarom": waarom, "signalen": facts["signalen"],
                     "woningen": facts["woningen"], "perceelM2": size})
        for key in [key for key in item if key.startswith("_")]:
            del item[key]
    return items, statistiek


def bron_ophalers(config, area, since):
    """The connected sources: source id -> function that returns its items for the whole window."""
    return {
        "officielebekendmakingen": lambda: (bekendmakingen.fetch(config, area, since)
                                            + bekendmakingen.fetch_sales(config, area, since["verkoop"])),
        "staatscourant-insolventies": lambda: insolventies.fetch(config, area, since["faillissement"]),
        "omgevingsloket-vlaanderen": lambda: vlaanderen.fetch(config, area, since["vergunning"]),
    }


def run(config, area, now, fetchers=None, verrijker=None, dagcontrole=volledigheid.controleer):
    """Fetch every connected source and judge the result. Returns the complete output document.

    Each run fetches the complete window again and keeps no state. A day the source missed
    (an outage, a lagging search index) is therefore picked up by the next run that finds it.
    """
    today = now.date()
    since = {kind: _since(today, days) for kind, days in config["venster_dagen"].items()}
    fetchers = fetchers or bron_ophalers(config, area, since)
    verrijker = verrijker or (lambda found: verrijk(found, config["drempel_perceel_m2"]))

    items, statuses = {}, {}
    for source_id, fetcher in fetchers.items():
        try:
            fetched = fetcher()
            for item in fetched:
                items.setdefault(item["id"], item)
            statuses[source_id] = {"status": "ok", "aantal": len(fetched)}
        except Exception as error:  # one failing source must not hide the others
            statuses[source_id] = {"status": "fout", "aantal": 0, "melding": str(error)[:300]}
            print(f"FOUT bij bron {source_id}: {error}", file=sys.stderr)

    try:
        incomplete = dagcontrole(now)
    except Exception as error:  # the check is a safeguard; without it the data is still published
        incomplete = []
        print(f"Dagcontrole mislukt: {error}", file=sys.stderr)

    items, statistiek = verrijker(list(items.values()))
    items.sort(key=lambda item: (item["datum"], -item["afstandKm"], item["id"]), reverse=True)
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    for source in sources:
        source.update(statuses.get(source["id"], {}))
    return {
        "bijgewerkt": now.isoformat(timespec="seconds"),
        "centrum": config["centrum"],
        "straalKm": config["straal_km"],
        "vensterDagen": config["venster_dagen"],
        "drempelPerceelM2": config["drempel_perceel_m2"],
        "onvolledigeDagen": incomplete,
        "ophaalfouten": {kind: stats["definitiefMislukt"] for kind, stats in statistiek.items()},
        "ophaalstatistiek": statistiek,
        "bronnen": sources,
        "berichten": items,
    }


def main():
    config = json.loads(gebied.CONFIG.read_text(encoding="utf-8"))
    area = gebied.load()
    now = datetime.datetime.now(zoneinfo.ZoneInfo(config["tijdzone"]))
    document = run(config, area, now)

    main_source = next(s for s in document["bronnen"] if s["id"] == "officielebekendmakingen")
    if main_source.get("status") != "ok":
        # Keep yesterday's data online rather than publishing an almost empty list.
        sys.exit("Hoofdbron niet bereikbaar; bestaande gegevens blijven staan.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    counts = {}
    for item in document["berichten"]:
        key = (item["klasse"], item["type"])
        counts[key] = counts.get(key, 0) + 1
    print(f'{len(document["berichten"])} berichten geschreven')
    for (klasse, kind), count in sorted(counts.items()):
        print(f"  {klasse:17} {kind:14} {count}")
    for kind, stats in document["ophaalstatistiek"].items():
        causes = ", ".join(f"{cause}: {count}" for cause, count in stats["redenen"].items()) or "geen"
        print(f'  ophalen {kind}: {stats["gevraagd"]} gevraagd, {stats["eersteRondeMislukt"]} mislukt in eerste ronde '
              f'({causes}), {stats["hersteld"]} hersteld, {stats["definitiefMislukt"]} definitief mislukt')
    fouten = document["ophaalfouten"]
    if any(fouten.values()):
        # "::warning::" makes the line stand out in the GitHub Actions log.
        print(f'::warning::Niet op te halen: {fouten.get("tekst", 0)} teksten en {fouten.get("perceel", 0)} perceelgroottes; '
              "die berichten staan tot de volgende verversing onder Onzeker")
    for gap in document["onvolledigeDagen"]:
        print(f'  ONVOLLEDIG {gap["datum"]}: {gap["aantal"]} van gebruikelijk {gap["verwacht"]} Gemeenteblad-publicaties')
    for source in document["bronnen"]:
        if "status" in source:
            print(f'  bron {source["id"]}: {source["status"]} ({source["aantal"]})')


if __name__ == "__main__":
    main()
