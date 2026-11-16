"""Bankruptcies of companies with business premises inside the radius.

Source: the daily court publications in the Staatscourant (officielebekendmakingen.nl, rubric
'faillissement, surseance van betaling of schuldsanering'), read through the same public search
service as the permits.

Privacy rules applied here, on purpose:
- only legal entities (B.V., N.V., stichting, coöperatie, vereniging); entries about natural persons,
  sole traders and partnerships are skipped without being stored;
- names of trustees and judges are not kept;
- a company registered at a residential address is skipped entirely: that is someone's home, not premises.
"""
import concurrent.futures
import re
import xml.etree.ElementTree as ET

from . import bekendmakingen, geo, http, perceel

RUBRIC = "faillissement, surseance van betaling of schuldsanering"
_EVENT = re.compile(r"^(Uitspraak faillissement|[Vv]erlening (?:voorlopige|definitieve) surseance)\b.*?"
                    r"op (\d{1,2} \w+ \d{4}).*?\(([FS]\.\d+/\d+/\d+)[^)]*\)\s*(.+?)(?:, corr\.adr\.|, vest\.adr\.|, KvK)", re.S)
_ADDRESS = re.compile(r"vest\.adr\. ([^,;]+?) (\d{4}) ?([A-Z]{2}) ([A-Za-zÀ-ÿ'’\- ]+?)(?=,|\.|;| KvK| hodn| corr\.adr|$)")
_HOUSE = re.compile(r"^(.+?)\s(\d+)(?:\s*[-/]?\s*(\S{1,6}))?$")
_KVK = re.compile(r"KvK:\s*(\d{8})")
_LEGAL = re.compile(r"\bB\.?V\.?(?!\w)|\bN\.?V\.?(?!\w)|\bStichting\b|\bCoöperati|\bVereniging\b|\bU\.?A\.?(?!\w)", re.I)
_NOT_LEGAL = re.compile(r"\bV\.?O\.?F\.?(?!\w)|\bC\.V\.|\bmaatschap\b|\beenmanszaak\b", re.I)
_PERSON = re.compile(r"\bgeb\.|woonadr\.")
_RESIDENTIAL = {"woonfunctie"}


def is_legal_entity(name, entry):
    """True for a company or other legal entity; False for anything that could be a natural person."""
    if _PERSON.search(entry) or _NOT_LEGAL.search(name):
        return False
    return bool(_LEGAL.search(name))


def parse_entry(entry):
    """Parse one list entry. Returns a dict, or None when it is not a new bankruptcy of a legal entity."""
    entry = re.sub(r"\s+", " ", entry).strip(" -")
    match = _EVENT.match(entry)
    if not match:
        return None
    event, date, case, name = match.groups()
    name = re.sub(r"\bB\.V$", "B.V.", name.strip()).replace("&amp;", "&")
    if not is_legal_entity(name, entry):
        return None
    addresses = []
    for street, digits, letters, town in _ADDRESS.findall(entry):
        house = _HOUSE.match(street.strip())
        if not house:
            continue
        address = {"straat": house.group(1), "huisnummer": int(house.group(2)), "toevoeging": house.group(3) or "",
                   "postcode": digits + letters, "plaats": town.strip()}
        if address not in addresses:
            addresses.append(address)
    kvk = _KVK.search(entry)
    return {"soort": "Surseance verleend" if "surseance" in event.lower() else "Faillissement uitgesproken",
            "uitspraak": date, "zaak": case, "naam": name, "kvk": kvk.group(1) if kvk else None, "adressen": addresses}


def entries(xml_text):
    """All list entries of one court publication, as plain text."""
    body = xml_text.split("</metadata>")[-1]
    return [re.sub(r"<[^>]+>", " ", item) for item in re.findall(r"<li>(.*?)</li>", body, re.S)]


def in_postcode_range(postcode, ranges):
    return any(low <= int(postcode[:4]) <= high for low, high in ranges)


def locate(address, lookup=perceel.bag_adres, fouten=None):
    """Find the building at an address. Returns (uses, floor_area, town, rd) or None for homes and unknowns.

    A lookup that fails is appended to `fouten`, so the caller can tell "no premises" from "no answer".
    """
    try:
        objects = lookup(address["postcode"], address["huisnummer"])
    except Exception as error:
        if fouten is not None:
            fouten.append(error)
        return None
    exact = [o for o in objects if o["huisletter"].lower() == address["toevoeging"].lower().replace(" ", "")]
    objects = exact or objects
    uses = set().union(*(o["gebruiksdoel"] for o in objects)) if objects else set()
    if not uses or uses <= _RESIDENTIAL:
        return None
    first = objects[0]
    area = sum(o["oppervlakte"] or 0 for o in objects) or None
    return sorted(uses - _RESIDENTIAL), area, first["woonplaats"], first["rd"]


def to_item(case, record, centre_rd, radius_m, town_to_gemeente, ranges, lookup=perceel.bag_adres, fouten=None):
    """Turn a parsed case into an app item when one of its premises lies inside the radius."""
    for address in case["adressen"]:
        if not in_postcode_range(address["postcode"], ranges):
            continue
        found = locate(address, lookup, fouten)
        if not found:
            continue
        uses, floor_area, town, rd = found
        metres = geo.distance(centre_rd, "point", [[rd]])
        if metres > radius_m:
            continue
        lat, lon = geo.rd_to_wgs84(*rd)
        number = f'{address["huisnummer"]}{address["toevoeging"]}'
        place = f'{address["straat"]} {number}, {address["postcode"]} {town}'
        size = f", {floor_area} m² vloeroppervlak" if floor_area else ""
        return {
            "id": f'ins-{case["zaak"]}',
            "bron": "staatscourant-insolventies",
            "publicatie": "Staatscourant",
            "overheid": record["overheid"],
            "type": "faillissement",
            "fase": case["soort"],
            "soort": None,
            "titel": f'{case["soort"]}: {case["naam"]}',
            "omschrijving": (f'Uitspraak van {case["uitspraak"]}, zaaknummer {case["zaak"]}'
                             + (f', KvK {case["kvk"]}' if case["kvk"] else "")
                             + f'. Pand volgens de BAG: {", ".join(uses)}{size}.'),
            "activiteiten": [],
            "datum": record["datum"],
            "gemeente": town_to_gemeente.get(town),
            "plaats": place,
            "afstandKm": round(metres / 1000, 1),
            "locatieSoort": "exact",
            "lat": lat, "lon": lon,
            "reactieTot": None, "planId": None,
            "url": record["url"], "urlTekst": record["urlTekst"],
            "_rd": rd, "_perceelM2": None, "_urlXml": None,
        }
    return None


def fetch(config, area, since, cache=None, lookup=perceel.bag_adres):
    """Fetch new bankruptcies and moratoria of legal entities with premises inside the radius.

    With a cache, a court publication that was read before and had no company inside the radius is
    not downloaded again. Only that verdict is cached, never the content.
    """
    centre_rd = tuple(config["centrum"]["rd"])
    radius_m = config["straal_km"] * 1000
    ranges = config["postcode_bereik"]
    town_to_gemeente = {w["naam"]: g["naam"] for g in area["gemeenten"] for w in g["woonplaatsen"]}
    query = f'c.product-area==officielepublicaties AND dt.type=="{RUBRIC}" AND dt.date>={since}'
    records = []
    for record in bekendmakingen.search(query):
        urls = {c.get("manifestation"): c.text for c in bekendmakingen._children(record, "itemUrl")}
        records.append({"id": bekendmakingen._text(record, "identifier"),
                        "overheid": bekendmakingen._text(record, "creator"), "datum": bekendmakingen._text(record, "date"),
                        "url": bekendmakingen._text(record, "preferredUrl"), "urlTekst": urls.get("html"), "xml": urls.get("xml")})

    def load(record):
        try:
            return record, http.get(record["xml"], attempts=2, timeout=40).decode("utf-8-sig", "replace")
        except Exception:
            return record, ""

    # After about a month the publisher withdraws the readable text of these publications (only a PDF
    # stays); those records are skipped on purpose, in line with that privacy measure.
    readable = [r for r in records if r["xml"]]
    todo = [r for r in readable if not (cache and r["id"] and cache.haal("insolventie", r["id"])[0])]
    items, failed = {}, 0
    with concurrent.futures.ThreadPoolExecutor(6) as pool:
        for record, text in pool.map(load, todo):
            failed += not text
            found, fouten = 0, []
            for entry in entries(text):
                case = parse_entry(entry)
                if case and any(in_postcode_range(a["postcode"], ranges) for a in case["adressen"]):
                    item = to_item(case, record, centre_rd, radius_m, town_to_gemeente, ranges, lookup, fouten)
                    if item:
                        found += 1
                        items.setdefault(item["id"], item)
            if cache and record["id"] and text and not found and not fouten:
                cache.zet("insolventie", record["id"], 0)
    if todo and failed > len(todo) / 2:
        raise RuntimeError(f"{failed} van {len(todo)} publicaties niet te lezen")
    return list(items.values())
