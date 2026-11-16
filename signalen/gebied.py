"""Determine which municipalities and towns lie within the radius around the centre.

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

    result = sorted(gemeenten.values(), key=lambda g: (g["minKm"], g["naam"]))
    for gemeente in result:
        gemeente["woonplaatsen"].sort(key=lambda w: (w["minKm"], w["naam"]))
    return {
        "bijgewerkt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "centrum": config["centrum"],
        "straalKm": config["straal_km"],
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
        print(f'{gemeente["naam"]:20} {gemeente["land"]} {gemeente["minKm"]:5.1f}-{gemeente["maxKm"]:4.1f} km '
              f'{gemeente["dekking"]:12} {towns}')


if __name__ == "__main__":
    main()
