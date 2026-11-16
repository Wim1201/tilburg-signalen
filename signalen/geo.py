"""Geometry helpers. All distances are computed in the Dutch RD grid (EPSG:28992, metres)."""
import math
import re

_NUM = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
_GROUP = re.compile(r"\(([^()]+)\)")
_PAIR = re.compile(rf"({_NUM})\s+({_NUM})")


def parse_wkt(wkt):
    """Parse WKT into (kind, parts); kind is 'point', 'line' or 'polygon'.

    Each part is a list of (x, y) tuples: a point set, a line or a polygon ring.
    """
    head = wkt.strip().upper()
    if "POLYGON" in head[:20]:
        kind = "polygon"
    elif "LINE" in head[:20]:
        kind = "line"
    else:
        kind = "point"
    parts = []
    for group in _GROUP.findall(wkt):
        coords = [(float(x), float(y)) for x, y in _PAIR.findall(group)]
        if coords:
            parts.append(coords)
    return kind, parts


def geojson_parts(geometry):
    """Convert a GeoJSON geometry into the same (kind, parts) shape as parse_wkt."""
    gtype = geometry["type"]
    coords = geometry["coordinates"]
    if gtype == "Point":
        return "point", [[tuple(coords[:2])]]
    if gtype == "MultiPoint":
        return "point", [[tuple(c[:2]) for c in coords]]
    if gtype == "LineString":
        return "line", [[tuple(c[:2]) for c in coords]]
    if gtype == "MultiLineString":
        return "line", [[tuple(c[:2]) for c in line] for line in coords]
    if gtype == "Polygon":
        return "polygon", [[tuple(c[:2]) for c in ring] for ring in coords]
    if gtype == "MultiPolygon":
        return "polygon", [[tuple(c[:2]) for c in ring] for poly in coords for ring in poly]
    raise ValueError(f"Unsupported geometry type: {gtype}")


def _segment_distance(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _inside(p, rings):
    """Even-odd test over all rings, so holes and multipolygons are handled alike."""
    x, y = p
    inside = False
    for ring in rings:
        for i in range(len(ring)):
            a, b = ring[i], ring[i - 1]
            if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
                inside = not inside
    return inside


def distance(p, kind, parts):
    """Shortest distance in metres from point p to the geometry (0 when p lies inside a polygon)."""
    if kind == "polygon" and _inside(p, parts):
        return 0.0
    best = math.inf
    for part in parts:
        if kind == "point" or len(part) == 1:
            best = min(best, min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in part))
        else:
            for i in range(len(part) - 1):
                best = min(best, _segment_distance(p, part[i], part[i + 1]))
    return best


def max_distance(p, parts):
    """Largest distance in metres from p to any vertex."""
    return max(math.hypot(p[0] - q[0], p[1] - q[1]) for part in parts for q in part)


def centre(parts):
    """Centre of the bounding box; good enough to put a pin on a map."""
    xs = [q[0] for part in parts for q in part]
    ys = [q[1] for part in parts for q in part]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def area(parts):
    """Area in m² of polygon rings (shoelace); holes cancel out when wound the other way."""
    total = 0.0
    for ring in parts:
        total += sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1] for i in range(len(ring) - 1)) / 2
    return abs(total)


def contains(p, parts):
    """True when point p lies inside the polygon rings."""
    return _inside(p, parts)


def pin(p, kind, parts, radius):
    """Point to show on a map: the centre of the part nearest to p.

    Large shapes (a road, a whole district) can have their centre outside the radius;
    in that case the vertex nearest to p is used, so the pin stays inside the circle.
    """
    nearest = min(parts, key=lambda part: distance(p, kind, [part]))
    point = centre([nearest])
    if math.hypot(point[0] - p[0], point[1] - p[1]) > radius:
        point = min((q for part in parts for q in part), key=lambda q: math.hypot(q[0] - p[0], q[1] - p[1]))
    return point


# RD -> WGS84, polynomial approximation (Schreutelkamp & Strang van Hees), accurate to < 1 m in NL.
_X0, _Y0, _PHI0, _LAM0 = 155000.0, 463000.0, 52.15517440, 5.38720621
_K = [(0, 1, 3235.65389), (2, 0, -32.58297), (0, 2, -0.24750), (2, 1, -0.84978), (0, 3, -0.06550),
      (2, 2, -0.01709), (1, 0, -0.00738), (4, 0, 0.00530), (2, 3, -0.00039), (4, 1, 0.00033), (1, 1, -0.00012)]
_L = [(1, 0, 5260.52916), (1, 1, 105.94684), (1, 2, 2.45656), (3, 0, -0.81885), (1, 3, 0.05594),
      (3, 1, -0.05607), (0, 1, 0.01199), (3, 2, -0.00256), (1, 4, 0.00128), (0, 2, 0.00022),
      (2, 0, -0.00022), (5, 0, 0.00026)]


def rd_to_wgs84(x, y):
    """Return (lat, lon) in degrees for an RD coordinate."""
    dx, dy = (x - _X0) * 1e-5, (y - _Y0) * 1e-5
    lat = _PHI0 + sum(c * dx ** p * dy ** q for p, q, c in _K) / 3600
    lon = _LAM0 + sum(c * dx ** p * dy ** q for p, q, c in _L) / 3600
    return round(lat, 6), round(lon, 6)
