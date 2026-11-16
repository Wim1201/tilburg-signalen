"""Daily update: fetch all sources, judge relevance and write site/data/berichten.json.

Run: python -m signalen.update
"""
import concurrent.futures
import datetime
import json
import pathlib
import sys
import zoneinfo

from . import bekendmakingen, gebied, insolventies, perceel, relevantie, tekst, vlaanderen

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "site" / "data" / "berichten.json"
SOURCES = pathlib.Path(__file__).with_name("bronnen.json")
WORKERS = 8


def _since(today, days):
    return (today - datetime.timedelta(days=days)).isoformat()


def verrijk(items, drempel, haal_tekst=tekst.haal_op, perceel_m2=perceel.kadaster_m2):
    """Add klasse, score, waarom, signalen, woningen and perceelM2 to every item (in place)."""
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as pool:
        # 1. Notices without a description in their metadata: read the opening lines of the publication.
        need_text = [i for i in items if i.get("_urlXml") and (i["type"] in ("plan", "verkoop") or not i["omschrijving"])]
        texts = pool.map(lambda i: haal_tekst(i["_urlXml"], i["titel"], 1500 if i["type"] == "plan" else 600), need_text)
        for item, text in zip(need_text, texts):
            item["_tekst"] = text

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
        for item, size in zip(need_area, pool.map(lambda i: perceel_m2(*i["_rd"]), need_area)):
            if size:
                item["_perceelM2"] = max(size, item.get("_perceelM2") or 0)

    # 4. Verdict.
    for item in items:
        facts = item["_feiten"]
        size = item.get("_perceelM2") if relevantie.needs_area(item["type"], facts) or item.get("_perceelM2") else None
        informative = item["type"] != "vergunning" or bool(item["omschrijving"] or item.get("_tekst")) or not item.get("_urlXml")
        klasse, score, waarom = relevantie.beoordeel(
            item["type"], facts, size, item["fase"], informatief=informative,
            locatie_bekend=item["locatieSoort"] != "gemeente", drempel=drempel)
        item.update({"klasse": klasse, "score": score, "waarom": waarom, "signalen": facts["signalen"],
                     "woningen": facts["woningen"], "perceelM2": size})
        for key in [key for key in item if key.startswith("_")]:
            del item[key]
    return items


def run(config, area, now):
    """Fetch every connected source and judge the result. Returns the complete output document."""
    today = now.date()
    since = {kind: _since(today, days) for kind, days in config["venster_dagen"].items()}
    fetchers = {
        "officielebekendmakingen": lambda: (bekendmakingen.fetch(config, area, since)
                                            + bekendmakingen.fetch_sales(config, area, since["verkoop"])),
        "staatscourant-insolventies": lambda: insolventies.fetch(config, area, since["faillissement"]),
        "omgevingsloket-vlaanderen": lambda: vlaanderen.fetch(config, area, since["vergunning"]),
    }

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

    items = verrijk(list(items.values()), config["drempel_perceel_m2"])
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
    for source in document["bronnen"]:
        if "status" in source:
            print(f'  bron {source["id"]}: {source["status"]} ({source["aantal"]})')


if __name__ == "__main__":
    main()
