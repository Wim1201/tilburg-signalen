"""Daily update: fetch all sources and write site/data/berichten.json.

Run: python -m signalen.update
"""
import datetime
import json
import pathlib
import sys
import zoneinfo

from . import bekendmakingen, gebied, vlaanderen

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "site" / "data" / "berichten.json"
SOURCES = pathlib.Path(__file__).with_name("bronnen.json")


def _since(today, days):
    return (today - datetime.timedelta(days=days)).isoformat()


def run(config, area, now):
    """Fetch every connected source. Returns the complete output document."""
    today = now.date()
    since = {kind: _since(today, days) for kind, days in config["venster_dagen"].items()}
    fetchers = {
        "officielebekendmakingen": lambda: bekendmakingen.fetch(config, area, since),
        "omgevingsloket-vlaanderen": lambda: vlaanderen.fetch(config, area, since["vergunning"]),
    }

    items, statuses = [], {}
    for source_id, fetcher in fetchers.items():
        try:
            fetched = fetcher()
            items.extend(fetched)
            statuses[source_id] = {"status": "ok", "aantal": len(fetched)}
        except Exception as error:  # one failing source must not hide the others
            statuses[source_id] = {"status": "fout", "aantal": 0, "melding": str(error)[:300]}
            print(f"FOUT bij bron {source_id}: {error}", file=sys.stderr)

    items.sort(key=lambda item: (item["datum"], -item["afstandKm"], item["id"]), reverse=True)
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    for source in sources:
        source.update(statuses.get(source["id"], {}))
    return {
        "bijgewerkt": now.isoformat(timespec="seconds"),
        "centrum": config["centrum"],
        "straalKm": config["straal_km"],
        "vensterDagen": config["venster_dagen"],
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
        counts[item["type"]] = counts.get(item["type"], 0) + 1
    print(f'{len(document["berichten"])} berichten geschreven: {counts}')
    for source in document["bronnen"]:
        if "status" in source:
            print(f'  {source["id"]}: {source["status"]} ({source["aantal"]})')


if __name__ == "__main__":
    main()
