"""Daily update: fetch all sources, judge relevance and write site/data/berichten.json.

Run: python -m signalen.update
"""
import argparse
import collections
import concurrent.futures
import datetime
import json
import pathlib
import re
import sys
import time
import zoneinfo

from . import bekendmakingen, cache as cachemodule, gebied, http, insolventies, perceel, relevantie, tekst, vlaanderen, volledigheid

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "site" / "data" / "berichten.json"
SOURCES = pathlib.Path(__file__).with_name("bronnen.json")
WORKERS = 4  # modest on purpose: the sources are public services
MAX_RETRY_WACHT = http.MAX_RETRY_WACHT


def _since(today, days):
    return (today - datetime.timedelta(days=days)).isoformat()


_alle = http.parallel  # kept under its old name for the enrichment code below


GRENS_REGIOTEKSTEN = 300  # new texts of the regions read per run; the core is never limited


def _samen(rondes):
    """Add up the download statistics of several rounds."""
    total = {"gevraagd": 0, "eersteRondeMislukt": 0, "hersteld": 0, "definitiefMislukt": 0}
    causes = collections.Counter()
    for stats in rondes:
        for key in total:
            total[key] += stats[key]
        causes.update(stats["redenen"])
    return {**total, "redenen": dict(causes.most_common(5))}


def regio_van_de_week(datum, regios):
    """The region that the weekly full refresh reads anew, next to the core: one per week, in turn.

    Weeks run from Monday and are counted without a break, so the turn does not skip at New Year.
    """
    return regios[((datum.toordinal() - 1) // 7) % len(regios)] if regios else None


def markeer_verversing(cache, area, ververs):
    """Before fetching: mark what a full refresh reads anew of the lookups that happen while fetching.

    Addresses found for notices without a location are kept per municipality, so they follow the
    label of that municipality; the court publications and the municipality of a point only concern
    the core. Texts and parcels are marked later, once the notices and their regions are known.
    """
    if not cache or not ververs:
        return
    labels = {g["naam"]: g.get("regio", "kern") for g in area["gemeenten"]}
    cache.markeer_vers("locatie", [key for key in cache.data["locatie"] if labels.get(key.split("|", 1)[0], "kern") in ververs])
    if "kern" in ververs:
        cache.markeer_vers("gemeente")
        cache.markeer_vers("insolventie")


def verrijk(items, drempel, haal_tekst=tekst.haal_op, perceel_m2=perceel.kadaster_m2, slaap=time.sleep, cache=None,
            grens_regio=None, ververs=()):
    """Add klasse, score, waarom, signalen, woningen and perceelM2 to every item (in place).

    Returns (items, statistiek); statistiek holds, for 'tekst' and 'perceel', how many downloads were
    asked, failed, recovered on retry and failed for good, with the causes, and per region how many
    notices are affected. A notice whose text could not be fetched is marked 'onzeker' with that
    reason, and the next run tries again.

    The core comes first and is read completely. Of the regions at most `grens_regio` new texts are
    read per run, newest first; a notice whose text has to wait is 'onzeker' with the reason "Tekst
    nog niet gelezen". A text that is in the cache is not new and does not count. `ververs` names the
    regions (and "kern") that a full refresh reads anew.
    """
    statistiek = {}
    regio = lambda item: item.get("regio", "kern")  # noqa: E731
    if cache:
        cache.markeer_vers("tekst", [cachemodule.tekst_sleutel(i["_urlXml"]) for i in items if i.get("_urlXml") and regio(i) in ververs])
        cache.markeer_vers("perceel", [cachemodule.perceel_sleutel(*i["_rd"]) for i in items if i.get("_rd") and regio(i) in ververs])
    known = (lambda item: cache.heeft("tekst", cachemodule.tekst_sleutel(item["_urlXml"]))) if cache else (lambda item: False)
    if cache:
        haal_tekst = cache.omwikkel("tekst", haal_tekst, cachemodule.tekst_sleutel)
        perceel_m2 = cache.omwikkel("perceel", perceel_m2, cachemodule.perceel_sleutel)
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as pool:
        # 1. Notices without a description in their metadata: read the opening lines of the publication.
        need_text = [i for i in items if i.get("_urlXml") and (i["type"] in ("plan", "verkoop") or not i["omschrijving"])]
        core = [i for i in need_text if regio(i) == "kern"]
        outside = [i for i in need_text if regio(i) != "kern"]
        new = sorted((i for i in outside if not known(i)), key=lambda i: i.get("datum") or "", reverse=True)
        later = new[grens_regio:] if grens_regio is not None else []
        for item in later:
            item["_tekstUitgesteld"] = True
        # Two rounds: the core is complete, retries included, before the first text of a region is asked.
        rounds = []
        for group in (core, [i for i in outside if not i.get("_tekstUitgesteld")]):
            arguments = [(i["_urlXml"], i["titel"], 1500 if i["type"] == "plan" else 600) for i in group]
            texts, stats = _alle(haal_tekst, arguments, pool, slaap)
            rounds.append(stats)
            for item, (text, ok) in zip(group, texts):
                item["_tekst"] = text
                item["_tekstMislukt"] = not ok
        statistiek["tekst"] = _samen(rounds)

        # 2. Facts from the text.
        for item in items:
            description = " ".join(filter(None, [item["omschrijving"], item.get("_tekst")]))
            item["_feiten"] = relevantie.kenmerken(item["type"], item["titel"], description, item["activiteiten"])
            if item["type"] == "verkoop" and not item.get("_perceelM2"):
                # Sale notices usually state the size of the land in the text.
                item["_perceelM2"] = relevantie.area_in_text(" ".join([item["titel"], description]))

        # 3. Parcel size, only where it decides the outcome and the notice itself does not settle it.
        #    Not for a notice whose text has to wait: its verdict waits with it.
        need_area = [i for i in items if i.get("_rd") and not i.get("_tekstUitgesteld") and relevantie.needs_area(i["type"], i["_feiten"])
                     and (i.get("_perceelM2") or 0) < drempel]
        sizes, statistiek["perceel"] = _alle(perceel_m2, [i["_rd"] for i in need_area], pool, slaap)
        for item, (size, ok) in zip(need_area, sizes):
            item["_perceelMislukt"] = not ok
            if size:
                item["_perceelM2"] = max(size, item.get("_perceelM2") or 0)

    # How many notices per region miss something: the app reports the core and each region apart.
    per_region = {"tekst": {}, "perceel": {}}
    for item in items:
        for kind, flags in (("tekst", {"mislukt": "_tekstMislukt", "uitgesteld": "_tekstUitgesteld"}), ("perceel", {"mislukt": "_perceelMislukt"})):
            counts = per_region[kind].setdefault(regio(item), {name: 0 for name in flags})
            for name, flag in flags.items():
                counts[name] += bool(item.get(flag))
    for kind in per_region:
        statistiek[kind]["perRegio"] = per_region[kind]
    statistiek["tekst"]["uitgesteld"] = len(later)

    # 4. Verdict.
    for item in items:
        facts = item["_feiten"]
        size = item.get("_perceelM2") if relevantie.needs_area(item["type"], facts) or item.get("_perceelM2") else None
        informative = item["type"] != "vergunning" or bool(item["omschrijving"] or item.get("_tekst")) or not item.get("_urlXml")
        klasse, score, waarom = relevantie.beoordeel(
            item["type"], facts, size, item["fase"], informatief=informative,
            locatie_bekend=item["locatieSoort"] != "gemeente", drempel=drempel,
            tekst_mislukt=bool(item.get("_tekstMislukt")), tekst_uitgesteld=bool(item.get("_tekstUitgesteld")))
        item.update({"klasse": klasse, "score": score, "waarom": waarom, "signalen": facts["signalen"],
                     "woningen": facts["woningen"], "perceelM2": size})
        for key in [key for key in item if key.startswith("_")]:
            del item[key]
    return items, statistiek


def worker_adres(waarde):
    """The address of the energy label Worker (tools/energielabel) for the tab "Adres", or "".

    Only an https address without anything odd in it is passed on to the app; anything else is
    left empty, and the tab then stays as it was without the Worker.
    """
    waarde = (waarde or "").strip() if isinstance(waarde, str) else ""
    return waarde.rstrip("/") if re.fullmatch(r"https://[A-Za-z0-9.-]+(:\d+)?(/[A-Za-z0-9._~/-]*)?", waarde) else ""


def instellingen(config):
    """The settings from config.json as the site reads them from berichten.json. One place, so that
    a refresh and the step in tests.yml (signalen/instellingen.py) write exactly the same."""
    return {
        "centrum": config["centrum"],
        "straalKm": config["straal_km"],
        "vensterDagen": config["venster_dagen"],
        "drempelPerceelM2": config["drempel_perceel_m2"],
        "energielabelWorker": worker_adres(config.get("energielabel_worker")),
    }


def kern_fouten(statistiek):
    """Downloads that failed for good, counted for the core only: what the morning screen reports.

    A region reports its own shortfall with the region. Statistics without a split per region (a
    stage that only concerns the core, or an older caller) count as they are.
    """
    return {kind: stats["perRegio"].get("kern", {}).get("mislukt", 0) if "perRegio" in stats else stats["definitiefMislukt"]
            for kind, stats in statistiek.items()}


def bron_ophalers(config, area, since, cache=None, statistiek=None):
    """The connected sources: source id -> function that returns its items for the whole window."""
    return {
        "officielebekendmakingen": lambda: (bekendmakingen.fetch(config, area, since, cache)
                                            + bekendmakingen.fetch_sales(config, area, since["verkoop"], cache)),
        "staatscourant-insolventies": lambda: insolventies.fetch(config, area, since["faillissement"], cache, statistiek=statistiek),
        "omgevingsloket-vlaanderen": lambda: vlaanderen.fetch(config, area, since["vergunning"]),
    }


def run(config, area, now, fetchers=None, verrijker=None, dagcontrole=volledigheid.controleer, cache=None, ververs=()):
    """Fetch every connected source and judge the result. Returns the complete output document.

    Each run fetches the complete window again and keeps no state. A day the source missed
    (an outage, a lagging search index) is therefore picked up by the next run that finds it.
    """
    today = now.date()
    since = {kind: _since(today, days) for kind, days in config["venster_dagen"].items()}
    bronstatistiek = {}
    fetchers = fetchers or bron_ophalers(config, area, since, cache, bronstatistiek)
    markeer_verversing(cache, area, ververs)
    verrijker = verrijker or (lambda found: verrijk(found, config["drempel_perceel_m2"], cache=cache,
                                                    grens_regio=config.get("grens_regioteksten", GRENS_REGIOTEKSTEN), ververs=ververs))

    items, statuses = {}, {}
    for source_id, fetcher in fetchers.items():
        try:
            fetched = fetcher()
            for item in fetched:
                item.setdefault("regio", "kern")  # bankruptcies and the Flemish source only cover the core
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
    statistiek = {**statistiek, **bronstatistiek}
    items.sort(key=lambda item: (item["datum"], -item["afstandKm"], item["id"]), reverse=True)
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    for source in sources:
        source.update(statuses.get(source["id"], {}))
    return {
        "bijgewerkt": now.isoformat(timespec="seconds"),
        **instellingen(config),
        "onvolledigeDagen": incomplete,
        "ophaalfouten": kern_fouten(statistiek),
        "ophaalstatistiek": statistiek,
        "cache": cache.statistiek() if cache else None,
        "bronnen": sources,
        "berichten": items,
    }


def regio_bestand(naam):
    """File name of the notices of one region, next to berichten.json: 'regio-west-brabant.json'."""
    return "regio-" + "-".join(naam.lower().split()) + ".json"


def verdeel(document, regios):
    """Split the output of a run: the core stays in the document, every region gets a document of its own.

    The app opens with the core only, so berichten.json stays as large as it was; a region is read
    when someone chooses it. The core document lists the regions with what each of them holds and
    what it still misses: `ongelezen` (texts that wait for a later run) and `mislukt` (downloads
    that failed).
    Returns (core document, {file name: region document}). Every region of the config gets a file,
    also when it is empty, so the app never asks for a file that is not there.
    """
    per_region = {naam: [] for naam in regios}
    core = []
    statistiek = document.get("ophaalstatistiek") or {}

    def short(kind, naam, name):
        return statistiek.get(kind, {}).get("perRegio", {}).get(naam, {}).get(name, 0)

    for item in document["berichten"]:
        (per_region[item["regio"]] if item.get("regio", "kern") in per_region else core).append(item)
    files, overview = {}, []
    for naam in regios:
        items = per_region[naam]
        files[regio_bestand(naam)] = {"regio": naam, "bijgewerkt": document["bijgewerkt"], "berichten": items}
        overview.append({"naam": naam, "bestand": regio_bestand(naam), "berichten": len(items),
                         "locaties": sum(1 for item in items if item["klasse"] == "ontwikkellocatie"),
                         "onzeker": sum(1 for item in items if item["klasse"] == "onzeker"),
                         # What this region still misses; the app says so with the region, not on the morning screen.
                         "ongelezen": short("tekst", naam, "uitgesteld"),
                         "mislukt": short("tekst", naam, "mislukt") + short("perceel", naam, "mislukt")})
    return {**document, "regios": overview, "berichten": core}, files


def weglaatbare_regioteksten(berichten, vensters):
    """Text keys of the notices outside the core that the cache may leave out, in that order.

    First what leaves its window first: a permit is listed for 42 days and a plan for 180, so the
    oldest notice is not always the one that goes first. A text that is left out is downloaded again
    by the next run; this order keeps that repetition short. The core is never listed.
    """
    def leaves(item):
        try:
            return (datetime.date.fromisoformat(item["datum"][:10]) + datetime.timedelta(days=vensters.get(item.get("type"), 0))).isoformat()
        except (TypeError, ValueError):
            return ""
    outside = [item for item in berichten if item.get("regio", "kern") != "kern"]
    return [item["id"] for item in sorted(outside, key=lambda item: (leaves(item), item["id"]))]


def cache_meldingen(saved, grens=cachemodule.GRENS_BYTES, waarschuw=cachemodule.WAARSCHUW_BYTES, repo=cachemodule.REPO_BYTES):
    """Lines for the run log about the size of the cache file; "::warning::" where someone should look."""
    size, left_out = saved["bytes"], saved["weggelaten"]
    kb = lambda count: f"{count / 1000:,.0f}".replace(",", ".") + " kB"  # noqa: E731
    lines = [f"  cache: {kb(size)} bewaard, {size * 100 // repo} procent van de {kb(repo)} die een bestand in de repository mag zijn"]
    if left_out:
        lines.append(f"::warning::Cache te groot: {left_out} regioteksten niet bewaard (wat het eerst uit het venster valt), zodat het bestand "
                     f"onder {kb(grens)} blijft; de volgende run haalt ze opnieuw op")
    if size > grens:
        lines.append(f"::warning::Cache is {kb(size)}, ook zonder die regioteksten boven {kb(grens)}. Boven {kb(repo)} strandt de volgende run "
                     "in de tests; de cache moet dan met de hand kleiner")
    elif size >= waarschuw and not left_out:
        lines.append(f"::warning::Cache is {kb(size)}, boven {kb(waarschuw)}. Boven {kb(grens)} bewaart een run een deel van de regioteksten niet meer")
    return lines


BESTAND_WAARSCHUW_BYTES = 1_350_000  # 90 percent of what a file in the repository may be


def bestand_meldingen(sizes, waarschuw=BESTAND_WAARSCHUW_BYTES, repo=cachemodule.REPO_BYTES):
    """Lines for the run log about the size of the data files the run wrote; "::warning::" from 90 percent.

    The run does not stop on a large data file: it is written and published, and the workflow does
    not put it in the repository. The limit only holds for the snapshot in the repository; see
    docs/tilburg-signalen_verslag_andere-rubrieken_19-11-2026.md.
    """
    kb = lambda count: f"{count / 1000:,.0f}".replace(",", ".") + " kB"  # noqa: E731
    lines = ["  bestanden: " + ", ".join(f"{name} {kb(size)} ({size * 100 // repo} procent)" for name, size in sizes.items())]
    for name, size in sizes.items():
        if size >= waarschuw:
            lines.append(f"::warning::{name} is {kb(size)}, {size * 100 // repo} procent van de {kb(repo)} die een bestand in de repository "
                         "mag zijn. De run gaat door en de site krijgt het bestand; vernieuw de momentopname in de repository niet met een "
                         f"bestand boven {kb(repo)}")
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description="Berichten ophalen en beoordelen")
    parser.add_argument("--volledig", action="store_true",
                        help="volledige verversing: de kern en de regio van de week opnieuw lezen, de rest uit de cache")
    parser.add_argument("--regio", help="met --volledig: deze regio opnieuw lezen in plaats van de regio van de week")
    parser.add_argument("--alles", action="store_true",
                        help="de cache niet lezen en alles opnieuw ophalen, zonder grens; niet voor de dagelijkse gang")
    args = parser.parse_args(argv)

    config = json.loads(gebied.CONFIG.read_text(encoding="utf-8"))
    area = gebied.load()
    now = datetime.datetime.now(zoneinfo.ZoneInfo(config["tijdzone"]))
    regios = config.get("regios", [])
    if args.regio and args.regio not in regios:
        sys.exit(f"Onbekende regio {args.regio}; kies uit: {', '.join(regios)}")
    # A full refresh reads the core anew and one region, in turn per week: all at once is too much
    # for the source (run 22 of 18-11-2026). What is not read anew comes from the cache.
    ververs = tuple(filter(None, ["kern", args.regio or regio_van_de_week(now.date(), regios)])) if args.volledig and not args.alles else ()
    cache = cachemodule.Cache(lezen=not args.alles, sleutel=cachemodule.insolventie_sleutel(config))
    http.VERZOEKEN.clear()
    http.GEWEIGERD.clear()
    started = time.monotonic()
    if args.alles:
        config = dict(config, grens_regioteksten=None)
    document = run(config, area, now, cache=cache, ververs=ververs)
    document["volledigeVerversing"] = args.volledig or args.alles
    document["ververst"] = ["alles"] if args.alles else list(ververs)
    document["verzoeken"] = {"totaal": sum(http.VERZOEKEN.values()), "perDienst": dict(http.VERZOEKEN),
                             "geweigerd429": sum(http.GEWEIGERD.values())}

    main_source = next(s for s in document["bronnen"] if s["id"] == "officielebekendmakingen")
    if main_source.get("status") != "ok":
        # Keep yesterday's data online rather than publishing an almost empty list.
        sys.exit("Hoofdbron niet bereikbaar; bestaande gegevens blijven staan.")

    # A kind is only pruned when its stage ran: otherwise a failing source would empty its cache.
    insolvency_ok = next(s for s in document["bronnen"] if s["id"] == "staatscourant-insolventies").get("status") == "ok"
    saved = cache.bewaar(snoei=("tekst", "perceel", "locatie", "gemeente") + (("insolventie",) if insolvency_ok else ()),
                         grens=cachemodule.GRENS_BYTES, weglaatbaar=weglaatbare_regioteksten(document["berichten"], config["venster_dagen"]))

    everything = document["berichten"]
    document, region_files = verdeel(document, config.get("regios", []))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    for name, region_document in region_files.items():
        (OUTPUT.parent / name).write_text(json.dumps(region_document, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    sizes = {name: (OUTPUT.parent / name).stat().st_size for name in [OUTPUT.name] + list(region_files)}
    counts = {}
    for item in everything:
        key = (item["klasse"], item["type"])
        counts[key] = counts.get(key, 0) + 1
    print(f'{len(everything)} berichten geschreven, waarvan {len(document["berichten"])} in de kern')
    for (klasse, kind), count in sorted(counts.items()):
        print(f"  {klasse:17} {kind:14} {count}")
    for kind, stats in document["ophaalstatistiek"].items():
        causes = ", ".join(f"{cause}: {count}" for cause, count in stats["redenen"].items()) or "geen"
        print(f'  ophalen {kind}: {stats["gevraagd"]} gevraagd, {stats["eersteRondeMislukt"]} mislukt in eerste ronde '
              f'({causes}), {stats["hersteld"]} hersteld, {stats["definitiefMislukt"]} definitief mislukt')
    fouten = document["ophaalfouten"]
    if any(fouten.values()):
        # "::warning::" makes the line stand out in the GitHub Actions log.
        details = ", ".join(f"{count} x {kind}" for kind, count in fouten.items() if count)
        print(f"::warning::Niet op te halen in de kern: {details}; de volgende verversing probeert het opnieuw")
    for regio in document["regios"]:
        if regio["mislukt"]:
            print(f'::warning::Niet op te halen in {regio["naam"]}: {regio["mislukt"]} berichten; de volgende verversing probeert het opnieuw')
        if regio["ongelezen"]:
            print(f'  {regio["naam"]}: {regio["ongelezen"]} teksten nog niet gelezen (grens van '
                  f'{config.get("grens_regioteksten", GRENS_REGIOTEKSTEN)} nieuwe regioteksten per run); een volgende run leest verder')
    for source in document["bronnen"]:
        if source.get("status") == "fout":
            print(f'::warning::Bron {source["id"]} niet bereikbaar: {source.get("melding", "")[:200]}')
    kind_of_run = ("alles opnieuw (cache niet gelezen)" if args.alles
                   else f"volledige verversing ({' en '.join(ververs)} opnieuw gelezen)" if args.volledig else "gewone run")
    print(f'  {kind_of_run}: {document["verzoeken"]["totaal"]} verzoeken in {time.monotonic() - started:.0f} seconden, '
          f'{document["verzoeken"]["geweigerd429"]} keer geweigerd (HTTP 429)')
    print("  per regio: " + ", ".join(f'{regio["naam"]} {regio["berichten"]} ({regio["bestand"]})' for regio in document["regios"]))
    for soort, stats in document["cache"].items():
        print(f'  cache {soort}: {stats["uitCache"]} uit cache, {stats["opgehaald"]} opgehaald')
    for line in cache_meldingen(saved):
        print(line)
    for line in bestand_meldingen(sizes):
        print(line)
    for gap in document["onvolledigeDagen"]:
        print(f'  ONVOLLEDIG {gap["datum"]}: {gap["aantal"]} van gebruikelijk {gap["verwacht"]} Gemeenteblad-publicaties')
    for source in document["bronnen"]:
        if "status" in source:
            print(f'  bron {source["id"]}: {source["status"]} ({source["aantal"]})')


if __name__ == "__main__":
    main()
