"""Read official notices (officielebekendmakingen.nl) through the public SRU search service.

Covers Gemeenteblad, Provinciaal blad, Waterschapsblad and Staatscourant. Each record carries
its own location, so the distance to the centre is computed per notice.
"""
import re
import xml.etree.ElementTree as ET

from . import classify, geo, http

SRU_URL = "https://repository.overheid.nl/sru"
PAGE_SIZE = 500
RUBRICS = {"omgevingsvergunning": "vergunning", "ruimtelijk plan of omgevingsdocument": "plan"}

LOCATIESERVER = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"
_STREET_SUFFIX = (r"(?:straat|weg|laan|kade|dijk|plein|pad|dreef|hof|ring|steeg|baan|singel|park|"
                  r"veld|akker|heide|hoek|eind|berg|gracht|markt|wal|erf|plantsoen|dam)")
_ADDRESS = re.compile(r"((?:[A-Z][\w'’.-]+ ){0,3}[A-Z][\w'’.-]+) (\d+)")
_STREET = re.compile(rf"\b([A-Z][\w'’.-]*{_STREET_SUFFIX})\b")


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _children(element, name):
    return [child for child in element.iter() if _local(child.tag) == name]


def _text(element, name):
    for child in element.iter():
        if _local(child.tag) == name and child.text:
            return child.text.strip()
    return None


def build_query(creators, rubric, since, publication=None):
    """CQL query for one rubric, published on or after `since` (ISO date)."""
    clauses = ["c.product-area==officielepublicaties", f'dt.type=="{rubric}"', f"dt.date>={since}"]
    if creators:
        clauses.append("(" + " OR ".join(f'dt.creator=="{name}"' for name in creators) + ")")
    if publication:
        clauses.append(f'w.publicatienaam=="{publication}"')
    return " AND ".join(clauses)


def search(query):
    """Yield every record element that matches the query (handles paging)."""
    start = 1
    while True:
        body = http.get(SRU_URL, {"query": query, "maximumRecords": PAGE_SIZE, "startRecord": start})
        root = ET.fromstring(body)
        diagnostics = _text(root, "message") if _children(root, "diagnostic") else None
        if diagnostics:
            raise RuntimeError(f"SRU-fout: {diagnostics}")
        records = _children(root, "record")
        yield from records
        total = int(_text(root, "numberOfRecords") or 0)
        start += len(records)
        if not records or start > total:
            return


def _geometries(record):
    """All located area markers of a record as (label, kind, parts)."""
    found = []
    for marker in _children(record, "gebiedsmarkering"):
        wkt = _text(marker, "geometrie")
        if not wkt:
            continue
        kind, parts = geo.parse_wkt(wkt)
        if parts:
            found.append((_text(marker, "geometrielabel"), kind, parts))
    return found


def _address_label(record):
    """Readable address from an 'Adres' marker, if the record has one."""
    for marker in _children(record, "Adres"):
        street, number = _text(marker, "straatnaam"), _text(marker, "huisnummer")
        if street:
            extra = (_text(marker, "huisletter") or "") + (_text(marker, "huisnummertoevoeging") or "")
            town = _text(marker, "woonplaats")
            return f"{street} {number or ''}{extra}".strip() + (f", {town}" if town else "")
    return None


def geocode_title(title, gemeente):
    """Find an address or street named in the title, within the given municipality.

    Returns (label, (x, y)) or None. Only exact street-name matches are accepted,
    because a wrong pin is worse than no pin.
    """
    candidates = [(f"{street} {number}", "adres", street) for street, number in _ADDRESS.findall(title)]
    candidates += [(street, "weg", street) for street in _STREET.findall(title)]
    for text, kind, street in candidates:
        try:
            result = http.get_json(LOCATIESERVER, {
                "q": text, "fq": [f"type:{kind}", f'gemeentenaam:"{gemeente}"'], "rows": 1,
                "fl": "straatnaam,woonplaatsnaam,centroide_rd",
            }, attempts=2)
        except Exception:  # geocoding is a nice-to-have; never let it break the run
            return None
        docs = result.get("response", {}).get("docs", [])
        if docs and _street_matches(docs[0].get("straatnaam", ""), street):
            x, y = re.findall(r"-?\d+(?:\.\d+)?", docs[0]["centroide_rd"])
            # The house number found can differ from the one in the title, so only name the street.
            label = f'omgeving {docs[0]["straatnaam"]}, {docs[0].get("woonplaatsnaam", gemeente)}'
            return label, (float(x), float(y))
    return None


def reverse_gemeente(x, y):
    """Name of the Dutch municipality at an RD coordinate, or None."""
    try:
        result = http.get_json(LOCATIESERVER.replace("/free", "/reverse"), {
            "X": round(x), "Y": round(y), "type": "gemeente", "distance": 0, "fl": "gemeentenaam"}, attempts=2)
    except Exception:
        return None
    docs = result.get("response", {}).get("docs", [])
    return docs[0].get("gemeentenaam") if docs else None


def _useful_label(label):
    """Skip technical labels such as 'Vlak 1' or 'Verzoeklocatie 2026052000103'."""
    return bool(label) and not re.match(r"(?i)(vlak|punt|lijn|verzoeklocatie|locatie|perceel|gebiedsmarkering)\b", label)


def _street_matches(found, wanted):
    """True when the geocoder's street is the street we asked for (ignoring leading words)."""
    found, wanted = found.lower(), wanted.lower()
    return bool(found) and (wanted == found or wanted.endswith(" " + found))


def to_item(record, centre_rd, radius_m, area_by_name, geocode=geocode_title, reverse=reverse_gemeente):
    """Turn one SRU record into an app item, or None when it falls outside the radius."""
    rubric = next((c.text for c in _children(record, "type") if c.text in RUBRICS), None)
    if rubric is None:
        return None
    kind = RUBRICS[rubric]
    title = _text(record, "title") or ""
    creator = _text(record, "creator") or ""
    gemeente = _text(record, "ligtInGemeente") or _text(record, "gemeentenaam")
    if gemeente is None and creator in area_by_name:
        gemeente = creator

    location, location_kind, place = None, None, None
    geometries = _geometries(record)
    if geometries:
        label, gkind, parts = min(geometries, key=lambda g: geo.distance(centre_rd, g[1], g[2]))
        metres = geo.distance(centre_rd, gkind, parts)
        if metres > radius_m:
            return None
        location, location_kind = geo.pin(centre_rd, gkind, parts, radius_m), "exact"
        place = _address_label(record) or next((lbl for lbl, _, _ in geometries if _useful_label(lbl)), None)
        if place is None and label and label.startswith("Perceel"):
            place = label
        if gemeente is None and reverse:
            gemeente = reverse(*location)
    elif gemeente in area_by_name:
        hit = geocode(title, gemeente) if geocode else None
        if hit:
            place, location = hit
            metres = geo.distance(centre_rd, "point", [[location]])
            if metres > radius_m:
                return None
            location_kind = "benaderd"
        else:
            metres = area_by_name[gemeente]["minKm"] * 1000
            location_kind = "gemeente"
    else:
        return None  # no location and not tied to a municipality in the area

    lat_lon = geo.rd_to_wgs84(*location) if location else None
    activities = sorted({c.text.strip() for c in _children(record, "activiteit") if c.text})
    return {
        "id": _text(record, "identifier"),
        "bron": "officielebekendmakingen",
        "publicatie": _text(record, "publicatienaam") or "Officiële bekendmaking",
        "overheid": creator,
        "type": kind,
        "fase": classify.permit_phase(title) if kind == "vergunning" else classify.plan_phase(title),
        "soort": None if kind == "vergunning" else classify.plan_kind(title),
        "titel": title,
        "omschrijving": _text(record, "abstract"),
        "activiteiten": activities,
        "datum": _text(record, "date"),
        "gemeente": gemeente,
        "plaats": place,
        "afstandKm": round(metres / 1000, 1),
        "locatieSoort": location_kind,
        "lat": lat_lon[0] if lat_lon else None,
        "lon": lat_lon[1] if lat_lon else None,
        "reactieTot": _text(record, "datumEindeReactietermijn"),
        "planId": _text(record, "bekendmakingBetreffendePlan"),
        "url": _text(record, "preferredUrl"),
        # Plain-text copy in the open data repository; a fallback when the main site is down.
        "urlTekst": next((c.text for c in _children(record, "itemUrl") if c.get("manifestation") == "html"), None),
    }


def fetch(config, area, since_by_kind):
    """Fetch all notices within the radius. Returns a list of items (newest first is done by the caller)."""
    centre_rd = tuple(config["centrum"]["rd"])
    radius_m = config["straal_km"] * 1000
    area_by_name = {g["naam"]: g for g in area["gemeenten"] if g["land"] == "NL"}
    local_creators = sorted(area_by_name) + [o["naam"] for o in config["extra_overheden"]]

    items = {}
    for rubric, kind in RUBRICS.items():
        since = since_by_kind[kind]
        queries = [
            build_query(local_creators, rubric, since),
            build_query(None, rubric, since, publication="Staatscourant"),
        ]
        for query in queries:
            for record in search(query):
                item = to_item(record, centre_rd, radius_m, area_by_name)
                if item and item["id"]:
                    items[item["id"]] = item
    return list(items.values())
