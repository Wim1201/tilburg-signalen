"""Look up parcels and buildings in the public registers of the Kadaster (through PDOK)."""
from . import geo, http

PERCELEN = "https://api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1/collections/perceel/items"
BAG_WFS = "https://service.pdok.nl/lv/bag/wfs/v2_0"
RD_CRS = "http://www.opengis.net/def/crs/EPSG/0/28992"


def kadaster_m2(x, y):
    """Registered size in m² of the cadastral parcel at an RD coordinate, or None."""
    try:
        data = http.get_json(PERCELEN, {
            "f": "json", "limit": 10, "crs": RD_CRS, "bbox-crs": RD_CRS,
            "bbox": f"{x - 0.5:.2f},{y - 0.5:.2f},{x + 0.5:.2f},{y + 0.5:.2f}"}, attempts=2, timeout=40)
    except Exception:
        return None
    features = data.get("features", [])
    for feature in features:
        if geo.contains((x, y), geo.geojson_parts(feature["geometry"])[1]):
            return feature["properties"].get("kadastrale_grootte_waarde")
    return features[0]["properties"].get("kadastrale_grootte_waarde") if len(features) == 1 else None


def bag_adres(postcode, huisnummer):
    """BAG address objects at a postcode and house number.

    Returns a list of dicts with gebruiksdoel (set of uses), oppervlakte, woonplaats, straat and RD point.
    """
    filter_xml = (
        '<Filter xmlns="http://www.opengis.net/fes/2.0"><And>'
        f"<PropertyIsEqualTo><ValueReference>postcode</ValueReference><Literal>{postcode}</Literal></PropertyIsEqualTo>"
        f"<PropertyIsEqualTo><ValueReference>huisnummer</ValueReference><Literal>{int(huisnummer)}</Literal></PropertyIsEqualTo>"
        "</And></Filter>")
    data = http.get_json(BAG_WFS, {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeName": "bag:verblijfsobject",
        "outputFormat": "application/json", "count": 50, "filter": filter_xml}, attempts=2, timeout=40)
    found = []
    for feature in data.get("features", []):
        props = feature["properties"]
        if not feature.get("geometry") or "ingetrokken" in (props.get("status") or "").lower():
            continue
        found.append({
            "gebruiksdoel": {use.strip() for use in (props.get("gebruiksdoel") or "").split(",") if use.strip()},
            "oppervlakte": props.get("oppervlakte"),
            "woonplaats": props.get("woonplaats"),
            "straat": props.get("openbare_ruimte"),
            "huisletter": (props.get("huisletter") or "") + (props.get("toevoeging") or ""),
            "rd": tuple(feature["geometry"]["coordinates"][:2]),
        })
    return found
