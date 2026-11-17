"""Determine which municipalities and towns lie within the radius around the centre (the core),
and measure the municipalities of the regions that config.json adds around it.

Sources (public, no key needed):
- PDOK, BRK Bestuurlijke Gebieden (Dutch municipal boundaries)
- PDOK, BAG (Dutch town boundaries: 'woonplaatsen')
- Digitaal Vlaanderen, Voorlopig Referentiebestand Gemeentegrenzen (Flemish municipal boundaries)

Run: python -m signalen.gebied
"""
import datetime
import json
import math
import pathlib

from . import geo, http

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"
OUTPUT = ROOT / "site" / "data" / "gebied.json"

RD_CRS = "http://www.opengis.net/def/crs/EPSG/0/28992"
PDOK_GEMEENTEN = "https://api.pdok.nl/kadaster/brk-bestuurlijke-gebieden/ogc/v1/collections/gemeentegebied/items"
PDOK_WOONPLAATSEN = "https://api.pdok.nl/kadaster/bag/ogc/v2/collections/woonplaats/items"
VLAANDEREN_GEMEENTEN = "https://geo.api.vlaanderen.be/VRBG/wfs"


def bbox_wgs84(config, margin_km=3):
    """Bounding box (lon/lat) around the search circle, with a margin."""
    reach = config["straal_km"] + margin_km
    lat, lon = config["centrum"]["lat"], config["centrum"]["lon"]
    dlat = reach / 111.2
    dlon = reach / (111.2 * math.cos(math.radians(lat)))
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


def _ogc_features(url, bbox):
    """Fetch all features of an OGC API collection within bbox, following 'next' links."""
    params = {"f": "json", "limit": 100, "crs": RD_CRS, "bbox": ",".join(f"{v:.4f}" for v in bbox)}
    features = []
    while url:
        page = http.get_json(url, params)
        features.extend(page["features"])
        url = next((link["href"] for link in page.get("links", []) if link.get("rel") == "next"), None)
        params = None
    return features


def _measure(feature, centre_rd, radius_m):
    kind, parts = geo.geojson_parts(feature["geometry"])
    nearest = geo.distance(centre_rd, kind, parts)
    farthest = geo.max_distance(centre_rd, parts)
    lat, lon = geo.rd_to_wgs84(*geo.centre(parts))
    return {
        "lat": lat, "lon": lon,
        "minKm": round(nearest / 1000, 1),
        "maxKm": round(farthest / 1000, 1),
        "dekking": "geheel" if farthest <= radius_m else "gedeeltelijk",
        "_binnen": nearest <= radius_m,
    }


def _named(name):
    """The boundary of one Dutch municipality by its name, or None when PDOK does not know it."""
    page = http.get_json(PDOK_GEMEENTEN, {"f": "json", "limit": 5, "crs": RD_CRS, "naam": name})
    return next((feature for feature in page["features"] if feature["properties"]["naam"] == name), None)


def regions(config, core, centre_rd, radius_m, fetch=_named):
    """Label the core and add the municipalities of the regions in config.json. Returns the entries to add.

    The core is what lies within the radius, exactly as before; the list in config.json does not
    change it. A core municipality can name the region that the rest of it, outside the radius,
    belongs to (`buiten_straal`). A municipality with another label than "kern" is taken whole. Its
    towns are not listed: that would mean reading the boundaries of every town in three regions.
    """
    listed = {entry["naam"]: entry for entry in config.get("gemeenten", [])}
    for gemeente in core.values():
        gemeente["regio"] = "kern"
        gemeente["buitenStraal"] = listed.get(gemeente["naam"], {}).get("buiten_straal") if gemeente["land"] == "NL" else None
    added = []
    for entry in listed.values():
        if entry["regio"] == "kern" or entry["naam"] in core:
            continue  # a core municipality keeps its place, whatever the list says
        feature = fetch(entry["naam"])
        if feature is None:
            raise RuntimeError(f'Gemeente {entry["naam"]} uit config.json is niet gevonden bij PDOK')
        props = feature["properties"]
        measured = _measure(feature, centre_rd, radius_m)
        measured.pop("_binnen")
        added.append({
            "naam": props["naam"], "code": props["identificatie"], "land": "NL", "provincie": props["ligt_in_provincie_naam"],
            **measured, "dekking": "buiten", "woonplaatsen": [], "regio": entry["regio"], "buitenStraal": None,
            **({"opmerking": entry["opmerking"]} if entry.get("opmerking") else {}),
        })
    return added


def build(config):
    centre_rd = tuple(config["centrum"]["rd"])
    radius_m = config["straal_km"] * 1000
    bbox = bbox_wgs84(config)

    gemeenten = {}
    for feature in _ogc_features(PDOK_GEMEENTEN, bbox):
        props = feature["properties"]
        measured = _measure(feature, centre_rd, radius_m)
        if measured.pop("_binnen"):
            gemeenten[props["naam"]] = {
                "naam": props["naam"], "code": props["identificatie"], "land": "NL",
                "provincie": props["ligt_in_provincie_naam"], **measured, "woonplaatsen": [],
            }

    seen = set()
    for feature in _ogc_features(PDOK_WOONPLAATSEN, bbox):
        props = feature["properties"]
        key = (props["woonplaats"], props["bronhouder_naam"])
        measured = _measure(feature, centre_rd, radius_m)
        if not measured.pop("_binnen") or key in seen or props["bronhouder_naam"] not in gemeenten:
            continue
        seen.add(key)
        gemeenten[props["bronhouder_naam"]]["woonplaatsen"].append({"naam": props["woonplaats"], **measured})

    flemish = http.get_json(VLAANDEREN_GEMEENTEN, {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": "VRBG:Refgem",
        "outputFormat": "application/json", "srsName": "EPSG:28992",
        "bbox": ",".join(f"{v:.4f}" for v in bbox) + ",EPSG:4326",
    })
    for feature in flemish["features"]:
        measured = _measure(feature, centre_rd, radius_m)
        if measured.pop("_binnen"):
            name = feature["properties"]["NAAM"]
            gemeenten[name] = {
                "naam": name, "code": "NIS" + str(feature["properties"]["NISCODE"]), "land": "BE",
                "provincie": "Antwerpen (Vlaanderen)", **measured, "woonplaatsen": [],
            }

    extra = regions(config, gemeenten, centre_rd, radius_m)
    result = sorted(list(gemeenten.values()) + extra, key=lambda g: (g["minKm"], g["naam"]))
    for gemeente in result:
        gemeente["woonplaatsen"].sort(key=lambda w: (w["minKm"], w["naam"]))
    return {
        "bijgewerkt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "centrum": config["centrum"],
        "straalKm": config["straal_km"],
        "regios": config.get("regios", []),
        "gemeenten": result,
    }


def load():
    return json.loads(OUTPUT.read_text(encoding="utf-8"))


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    area = build(config)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(area, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for gemeente in area["gemeenten"]:
        towns = ", ".join(w["naam"] for w in gemeente["woonplaatsen"])
        print(f'{gemeente["naam"]:20} {gemeente["land"]} {gemeente["minKm"]:5.1f}-{gemeente["maxKm"]:5.1f} km '
              f'{gemeente["dekking"]:12} {gemeente["regio"]:15} {towns}')


if __name__ == "__main__":
    main()
