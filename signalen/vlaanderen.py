"""Read Flemish environmental permits (omgevingsvergunningen) for the Belgian part of the radius.

Source: Departement Omgeving, public Mercator WFS, layer lu:lu_omv_gd_v2.
The applicant field is deliberately not requested: it can contain names of private persons.
"""
from . import gebied, geo, http

WFS_URL = "https://www.mercator.vlaanderen.be/raadpleegdienstenmercatorpubliek/ows"
FIELDS = ("projectnummer,handeling_omschrijving,omschrijving_projecttype,datum_indiening,huidige_toestand,"
          "datum_huidige_toestand,vvo_huidige_toestand,project_link,geom")

_PHASES = {
    "Vergunning": "Verleend",
    "Weigering": "Geweigerd",
    "Stopgezet": "Ingetrokken of buiten behandeling",
    "Aktename": "Melding geaccepteerd",
}


def _phase_and_date(props, since):
    """Return (phase, date) for a project, or None when nothing happened inside the window.

    For running procedures the service fills the status date with today's date,
    so the submission date is the only usable date there.
    """
    status = props.get("huidige_toestand") or ""
    if status.startswith("In behandeling"):
        submitted = props.get("datum_indiening")
        if status.endswith("(in eerste aanleg)") and submitted and submitted >= since:
            return "Aanvraag", submitted
        return None
    changed = props.get("datum_huidige_toestand")
    if changed and changed >= since:
        return _PHASES.get(status, status or "Bekendmaking"), changed
    return None


def to_item(feature, centre_rd, radius_m, since, gemeente):
    props = feature["properties"]
    if not feature.get("geometry"):
        return None
    phase_date = _phase_and_date(props, since)
    if phase_date is None:
        return None
    kind, parts = geo.geojson_parts(feature["geometry"])
    metres = geo.distance(centre_rd, kind, parts)
    if metres > radius_m:
        return None
    lat, lon = geo.rd_to_wgs84(*geo.pin(centre_rd, kind, parts, radius_m))
    phase, date = phase_date
    project_type = props.get("omschrijving_projecttype") or "Omgevingsproject"
    return {
        "id": f'vl-{props["projectnummer"]}-{date}',
        "bron": "omgevingsloket-vlaanderen",
        "publicatie": "Omgevingsloket Vlaanderen",
        "overheid": props.get("vvo_huidige_toestand") or gemeente,
        "type": "vergunning",
        "fase": phase,
        "soort": None,
        "titel": props.get("handeling_omschrijving") or project_type,
        "omschrijving": f'{project_type}, projectnummer {props["projectnummer"]}',
        "activiteiten": [],
        "datum": date,
        "gemeente": f"{gemeente} (België)",
        "plaats": None,
        "afstandKm": round(metres / 1000, 1),
        "locatieSoort": "exact",
        "lat": lat,
        "lon": lon,
        "reactieTot": None,
        "planId": None,
        "url": props.get("project_link"),
        "urlTekst": None,
        "_rd": None,
        "_perceelM2": round(geo.area(parts)) if kind == "polygon" else None,
        "_urlXml": None,
    }


def fetch(config, area, since):
    """Fetch Flemish permit projects inside the radius that changed since `since` (ISO date)."""
    belgian = [g["naam"] for g in area["gemeenten"] if g["land"] == "BE"]
    if not belgian:
        return []
    centre_rd = tuple(config["centrum"]["rd"])
    radius_m = config["straal_km"] * 1000
    west, south, east, north = gebied.bbox_wgs84(config, margin_km=0)
    data = http.get_json(WFS_URL, {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": "lu:lu_omv_gd_v2",
        "outputFormat": "application/json", "srsName": "EPSG:28992", "propertyName": FIELDS,
        "CQL_FILTER": f"datum_huidige_toestand >= '{since}' AND BBOX(geom, {west:.4f},{south:.4f},{east:.4f},{north:.4f},'EPSG:4326')",
    })
    label = belgian[0] if len(belgian) == 1 else "Vlaanderen"
    items = (to_item(f, centre_rd, radius_m, since, label) for f in data["features"])
    return [item for item in items if item]
