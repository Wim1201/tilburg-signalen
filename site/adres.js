/* Tilburg Signalen, tab "Adres": the logic without the page. Which addresses of the open registers
   to ask for, what the answers mean, and which notices of the app are about a chosen address.
   adres-app.js turns the results into elements; the tests run this file under Node. Nothing here
   fetches anything and nothing changes the notices: they are read as data/berichten.json has them. */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.TilburgAdres = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var SUGGEST = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/suggest";
  var BAG = "https://api.pdok.nl/kadaster/bag/ogc/v2/collections";
  var PERCEEL = "https://api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1/collections/perceel/items";
  var KAART = "https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0";
  var EP_ONLINE = "https://www.ep-online.nl/Energylabel/Search";
  var REGELS_OP_DE_KAART = "https://omgevingswet.overheid.nl/regels-op-de-kaart";
  var PLANKAART = "https://service.pdok.nl/kadaster/plu/wms/v1_0";         // Ruimtelijke plannen (Kadaster, via PDOK), without a key
  var RP_DOCUMENTEN = "https://ruimtelijkeplannen.nl/documents/";            // the rules of a plan, as a plain link
  var PLAN_LAGEN = ["enkelbestemming", "dubbelbestemming", "maatvoering", "bestemmingsplangebied"];
  /* The plan statuses that count as adopted. Every other status (ontwerp, voorontwerp, concept, or
     one this list does not know yet) is left out and counted, never shown as if it applied. */
  var VASTGESTELD = ["vastgesteld", "onherroepelijk", "vigerend", "goedgekeurd", "geconsolideerd"];
  /* A dossier in one of these states no longer applies, whatever the status of the plan says. */
  var VERVALLEN = ["afgebroken", "vernietigd", "geheel vernietigd", "niet in werking"];
  var FIELDS = ["id", "weergavenaam", "straatnaam", "huisnummer", "huisletter", "huisnummertoevoeging", "postcode", "woonplaatsnaam",
    "gemeentenaam", "centroide_rd", "centroide_ll", "adresseerbaarobject_id", "gekoppeld_perceel"].join(",");
  var MAX_PANDEN = 3;      // buildings read for one address
  var MAX_PERCELEN = 4;    // parcels read for one address
  var NEAR_M = 250;        // a notice with the same street and number further away than this is another place
  var STREET_M = 3000;     // the same for a notice that names only the street
  var MAX_PIXELS = 2048;   // widest picture asked of the map service
  var M_PER_DEGREE = 111320;
  var TYPE_LABEL = { vergunning: "Vergunning", plan: "Plan", faillissement: "Faillissement", verkoop: "Verkoop overheid" };

  /* Ways of writing the same street name. Both the address and the notice go through this, so
     "Burg. van de Mortelplein", "St. Josephstr." and "Dr. Bloemenlaan" meet their full spelling. */
  var WORDS = {
    str: "straat", st: "sint", burg: "burgemeester", dr: "dokter", doctor: "dokter", prof: "professor", past: "pastoor",
    kard: "kardinaal", gen: "generaal", mgr: "monseigneur", mr: "meester", ir: "ingenieur", pres: "president", ds: "dominee",
    pr: "prins", prinses: "prins", kon: "koning", koningin: "koning",
  };
  /* A word in front of a street name that makes it another street: "Korte Heuvel" is not "Heuvel". */
  var LEADING = ["korte", "lange", "nieuwe", "oude", "kleine", "grote", "hoge", "lage", "eerste", "tweede", "derde", "1e", "2e", "3e",
    "achter", "sint", "burgemeester", "dokter", "professor", "pastoor", "kardinaal", "generaal", "monseigneur", "meester", "ingenieur",
    "president", "dominee", "prins", "koning"];
  /* Words that show a number counts something instead of being a house number. */
  var COUNTED = ["woningen", "woning", "appartementen", "wooneenheden", "woonunits", "units", "studios", "kamers", "bomen", "boom",
    "stuks", "parkeerplaatsen", "zonnepanelen", "m2", "m", "meter", "x"];

  function query(base, params) {
    return base + "?" + Object.keys(params).map(function (key) { return key + "=" + encodeURIComponent(params[key]); }).join("&");
  }
  function safeUrl(url) { return typeof url === "string" && /^https:\/\//.test(url) ? url : null; }
  function shortDate(iso) { var p = String(iso || "").split("-"); return p.length === 3 ? p[2] + "-" + p[1] + "-" + p[0] : ""; }
  function thousands(value) { return String(Math.round(value)).replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
  function m2(value) { return typeof value === "number" && isFinite(value) ? thousands(value) + " m²" : null; }

  /* ---------- Spelling ---------- */

  function word(token) {
    if (Object.prototype.hasOwnProperty.call(WORDS, token)) return WORDS[token];
    var cut = /^([a-z-]{3,})str$/.exec(token); // "Heuvelstr." (the dot is gone by now)
    return cut ? cut[1] + "straat" : token;
  }

  /* One spelling for comparing: lower case, no accents, no dots or apostrophes, abbreviations
     written out. Commas, hyphens and slashes stay, because they separate house numbers. */
  function normalise(text) {
    var plain = String(text === null || text === undefined ? "" : text).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
      .replace(/[’'`´]/g, "").replace(/\bt\/m\b/g, " tm ").replace(/([,\/])/g, " $1 ").replace(/[^a-z0-9,\/-]+/g, " ");
    return plain.split(" ").filter(Boolean).map(word).join(" ");
  }

  /* The street name as letters and digits only: "Waspikse weg", "Waspikseweg" and "Ringbaan-Oost"
     compare without their spaces and hyphens. */
  function streetKey(street) { return normalise(street).replace(/[^a-z0-9]/g, ""); }

  /* Letter and addition of a house number as one comparable string: "A" + "" -> "a",
     "" + "01" -> "1", "V" + "3004" -> "v3004". */
  function suffix(letter, addition) {
    var extra = String(addition || "").toLowerCase().replace(/[^a-z0-9]/g, "");
    if (/^\d+$/.test(extra)) extra = String(+extra);
    return String(letter || "").toLowerCase().replace(/[^a-z]/g, "") + extra;
  }

  /* What someone typed, as the address search understands it best. */
  function searchText(text) {
    return String(text || "").replace(/\s+/g, " ").trim().replace(/([A-Za-zÀ-ÿ])str\.?(?=\s|,|$)/g, "$1straat");
  }

  /* ---------- Address ---------- */

  function point(wkt) {
    var found = /POINT\(\s*(-?[\d.]+)\s+(-?[\d.]+)\s*\)/.exec(wkt || "");
    return found ? [+found[1], +found[2]] : null;
  }

  /* "DGN01-I-2017": cadastral municipality code, section, parcel number. */
  function parcelCode(text) {
    var found = /^([A-Z]{3}\d{2})-([A-Z]{1,2})-(\d+)$/.exec(String(text || "").trim());
    return found ? { gemeente: found[1], sectie: found[2], nummer: +found[3] } : null;
  }

  function suggestUrl(text, centre) {
    var params = { q: searchText(text), fq: "type:adres", rows: 7, fl: FIELDS };
    // Nearest first: a "Hoofdstraat 12" close to Tilburg comes before the one in Stadskanaal.
    if (centre && typeof centre.lat === "number" && typeof centre.lon === "number") { params.lat = centre.lat; params.lon = centre.lon; }
    return query(SUGGEST, params);
  }

  /* One document of the address search as the address the tab works with. */
  function addressFromDoc(doc) {
    var rd = point(doc.centroide_rd), ll = point(doc.centroide_ll);
    return {
      id: doc.id || null,
      label: doc.weergavenaam || "",
      straat: doc.straatnaam || "",
      huisnummer: typeof doc.huisnummer === "number" ? doc.huisnummer : parseInt(doc.huisnummer, 10) || null,
      huisletter: doc.huisletter || "",
      toevoeging: doc.huisnummertoevoeging || "",
      postcode: String(doc.postcode || "").replace(/\s/g, "").toUpperCase(),
      woonplaats: doc.woonplaatsnaam || "",
      gemeente: doc.gemeentenaam || "",
      rd: rd ? { x: rd[0], y: rd[1] } : null,
      lon: ll ? ll[0] : null,
      lat: ll ? ll[1] : null,
      objectId: /^\d{16}$/.test(doc.adresseerbaarobject_id || "") ? doc.adresseerbaarobject_id : null,
      percelen: (doc.gekoppeld_perceel || []).map(parcelCode).filter(Boolean).slice(0, MAX_PERCELEN),
    };
  }

  function addresses(response) {
    var docs = response && response.response && response.response.docs;
    return (docs || []).filter(function (doc) { return doc && doc.weergavenaam; }).map(addressFromDoc);
  }

  function houseNumber(address) {
    return address.huisnummer + (address.huisletter || "") + (address.toevoeging ? "-" + address.toevoeging : "");
  }

  /* ---------- Building (BAG) ---------- */

  function vboUrl(objectId) { return query(BAG + "/verblijfsobject/items", { f: "json", limit: 5, identificatie: objectId }); }

  /* The buildings an address object lies in. Only links into the BAG service itself are followed. */
  function pandUrls(vbo) {
    var links = (vbo && vbo.properties && vbo.properties["pand.href"]) || [];
    return [].concat(links).filter(function (href) {
      return typeof href === "string" && href.indexOf(BAG + "/pand/items/") === 0 && !/[?#]/.test(href);
    }).slice(0, MAX_PANDEN).map(function (href) { return href + "?f=json"; });
  }

  function unique(values) { return values.filter(function (value, index) { return values.indexOf(value) === index; }); }
  function sentenceList(values) {
    return values.length > 1 ? values.slice(0, -1).join(", ") + " en " + values[values.length - 1] : values.join("");
  }

  /* What the tab shows of the building. `panden` holds one entry per building; null where the
     answer did not come. Returns null when the address has no address object with a building. */
  function bagModel(vbo, panden) {
    if (!vbo || !vbo.properties) return null;
    var props = vbo.properties, got = (panden || []).filter(Boolean).map(function (pand) { return pand.properties || {}; });
    var years = unique(got.map(function (p) { return p.bouwjaar; }).filter(function (year) { return typeof year === "number" && year > 0; }));
    var states = unique(got.map(function (p) { return p.status; }).filter(Boolean));
    var uses = String(props.gebruiksdoel || "").split(",").map(function (use) { return use.trim(); }).filter(Boolean);
    var missing = (panden || []).length - got.length;
    return {
      rows: [
        { label: "Bouwjaar", value: years.length ? sentenceList(years.map(String)) : null },
        { label: "Gebruiksdoel", value: uses.length ? uses.join(", ") : null },
        { label: "Oppervlakte", value: m2(props.oppervlakte) },
        { label: "Pandstatus", value: states.length ? sentenceList(states) : null },
      ],
      objectStatus: props.status || null,
      panden: (panden || []).length,
      // Year and status come from the building; say so when that answer is missing.
      pandMissing: missing > 0 || !(panden || []).length,
    };
  }

  /* ---------- Cadastral parcel ---------- */

  function perceelUrl(code) {
    return query(PERCEEL, { f: "json", limit: 5, akr_kadastrale_gemeente_code_waarde: code.gemeente, sectie: code.sectie, perceelnummer: code.nummer });
  }
  /* For an address that the register does not link to a parcel: the parcels at its point. */
  function perceelAtUrl(lon, lat) {
    var d = 0.00002; // about 2 m
    return query(PERCEEL, { f: "json", limit: 10, bbox: [lon - d, lat - d, lon + d, lat + d].map(function (v) { return v.toFixed(6); }).join(",") });
  }

  function rings(geometry) {
    if (!geometry || !geometry.coordinates) return [];
    var polygons = geometry.type === "MultiPolygon" ? geometry.coordinates : geometry.type === "Polygon" ? [geometry.coordinates] : [];
    return polygons.reduce(function (all, polygon) { return all.concat(polygon); }, []).filter(function (ring) { return ring.length >= 3; });
  }

  /* Even-odd rule over all rings, so a hole in a parcel is outside it. */
  function contains(parcel, lon, lat) {
    var inside = false;
    parcel.rings.forEach(function (ring) {
      for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        var a = ring[i], b = ring[j];
        if ((a[1] > lat) !== (b[1] > lat) && lon < (b[0] - a[0]) * (lat - a[1]) / (b[1] - a[1]) + a[0]) inside = !inside;
      }
    });
    return inside;
  }

  function parcelModel(feature) {
    var props = (feature && feature.properties) || {};
    return {
      aanduiding: [props.kadastrale_gemeente_waarde, props.sectie, props.perceelnummer].filter(function (part) { return part !== undefined && part !== null && part !== ""; }).join(" "),
      code: [props.akr_kadastrale_gemeente_code_waarde, props.sectie, props.perceelnummer].filter(Boolean).join(" "),
      grootte: typeof props.kadastrale_grootte_waarde === "number" ? props.kadastrale_grootte_waarde : null,
      grootteTekst: m2(props.kadastrale_grootte_waarde),
      soortGrootte: props.soort_grootte_waarde || null,
      rings: rings(feature && feature.geometry),
    };
  }

  function parcels(response) {
    return ((response && response.features) || []).map(parcelModel).filter(function (parcel) { return parcel.rings.length; });
  }
  /* Of the parcels around a point, the one the point lies in. */
  function parcelAt(response, lon, lat) {
    var found = parcels(response), inside = found.filter(function (parcel) { return contains(parcel, lon, lat); });
    return inside[0] || (found.length === 1 ? found[0] : null);
  }

  /* The small map: a square around the parcels, the official cadastral map as background and the
     parcels drawn on top. Everything is in longitude and latitude, so picture and drawing share
     one frame. Shapes are in a box of 1000 by 1000. */
  function mapModel(found, address) {
    var lons = [], lats = [];
    found.forEach(function (parcel) { parcel.rings.forEach(function (ring) { ring.forEach(function (p) { lons.push(p[0]); lats.push(p[1]); }); }); });
    if (address && typeof address.lon === "number") { lons.push(address.lon); lats.push(address.lat); }
    if (!lons.length) return null;
    var minLon = Math.min.apply(null, lons), maxLon = Math.max.apply(null, lons), minLat = Math.min.apply(null, lats), maxLat = Math.max.apply(null, lats);
    var lat0 = (minLat + maxLat) / 2, lon0 = (minLon + maxLon) / 2, mLon = M_PER_DEGREE * Math.cos(lat0 * Math.PI / 180);
    var extent = Math.max((maxLon - minLon) * mLon, (maxLat - minLat) * M_PER_DEGREE);
    var size = Math.max(60, Math.ceil(extent * 1.5 + 20)); // metres along one side
    var dLon = size / mLon, dLat = size / M_PER_DEGREE, west = lon0 - dLon / 2, north = lat0 + dLat / 2;
    function x(lon) { return ((lon - west) / dLon * 1000).toFixed(1); }
    function y(lat) { return ((north - lat) / dLat * 1000).toFixed(1); }
    // The map service draws nothing above scale 1:6000 (a pixel counts as 0.28 mm), so a wide frame asks for more pixels.
    var pixels = Math.min(MAX_PIXELS, Math.max(480, Math.ceil(size / (0.00028 * 5000) / 16) * 16));
    var bar = [1000, 500, 200, 100, 50, 20, 10, 5].filter(function (length) { return length <= size / 3; })[0] || 5;
    return {
      size: size,
      image: query(KAART, {
        service: "WMS", version: "1.3.0", request: "GetMap", layers: "Kadastralekaart", styles: "", crs: "CRS:84", format: "image/png",
        bbox: [west, lat0 - dLat / 2, west + dLon, north].map(function (v) { return v.toFixed(7); }).join(","), width: pixels, height: pixels,
      }),
      paths: found.map(function (parcel) {
        return parcel.rings.map(function (ring) {
          return "M" + ring.map(function (p) { return x(p[0]) + " " + y(p[1]); }).join("L") + "Z";
        }).join("");
      }),
      point: address && typeof address.lon === "number" ? { x: x(address.lon), y: y(address.lat) } : null,
      bar: { metres: bar, share: bar / size },
      osm: address && typeof address.lat === "number"
        ? "https://www.openstreetmap.org/?mlat=" + address.lat + "&mlon=" + address.lon + "#map=18/" + address.lat + "/" + address.lon : null,
    };
  }

  /* ---------- Notices about an address ---------- */

  function isPostcode(tokens, i) {
    if (/^\d{4}[a-z]{2}$/.test(tokens[i] || "")) return tokens[i];
    if (/^\d{4}$/.test(tokens[i] || "") && /^[a-z]{2}$/.test(tokens[i + 1] || "")) return tokens[i] + tokens[i + 1];
    return null;
  }

  /* The house numbers that follow a street name, from the words after it. Understands "12",
     "12a", "12 a", "12-a", "12bis", "40 a 1", "1V-3004", "67-12" (an addition), "2-4" and
     "12 t/m 18" (ranges) and "12, 14 en 16". A number that counts something ("3 woningen") is
     not a house number. Stops at a postcode, which it returns as well. */
  function numbersAfter(tokens) {
    var specs = [], i = 0;
    function counted(at) { return COUNTED.indexOf(tokens[at] || "") !== -1; }
    function read() {
      if (isPostcode(tokens, i)) return null;
      var found = /^(\d{1,5})(?:-?([a-z]{1,3}))?(?:-?(\d{1,5}))?$/.exec(tokens[i] || "");
      if (!found || counted(i + 1)) return null;
      i++;
      var n = +found[1], letter = found[2] || "", extra = found[3] || "";
      if (!letter && !extra && /^[a-z]$/.test(tokens[i] || "")) letter = tokens[i++];
      if (letter && !extra && /^\d{1,4}$/.test(tokens[i] || "") && !isPostcode(tokens, i) && !counted(i + 1)) extra = tokens[i++];
      // "529-721" runs from 529 to 721; "67-12" is number 67 with addition 12.
      if (!letter && extra && +extra > n) return { van: n, tot: +extra };
      return { n: n, s: suffix(letter, extra) };
    }
    if (/^(nr|nummer|huisnummer|no)$/.test(tokens[i] || "")) i++;
    var first = read();
    // A number in a form this does not understand still means: a house number was named.
    if (!first) return { specs: specs, postcode: null, unclear: /^\d/.test(tokens[i] || "") && !isPostcode(tokens, i) };
    specs.push(first);
    for (;;) {
      var start = i, range = false;
      if (tokens[i] === "tm" || tokens[i] === "-") { range = true; i++; }
      else if (tokens[i] === "tot" && tokens[i + 1] === "en" && tokens[i + 2] === "met") { range = true; i += 3; }
      else if (tokens[i] === "," || tokens[i] === "en" || tokens[i] === "/") { i++; if (tokens[i] === "en") i++; }
      else break;
      var next = read(), last = specs[specs.length - 1];
      // "12 - 18" is a range; "12 - 3 ..." is a dash before something else.
      if (!next || (range && !(last.n !== undefined && next.n > last.n))) { i = start; break; }
      if (range) specs[specs.length - 1] = { van: last.n, tot: next.n };
      else specs.push(next);
    }
    if (tokens[i] === ",") i++;
    return { specs: specs, postcode: isPostcode(tokens, i), unclear: false };
  }

  /* Every place where a street is named in a text, with the house numbers that follow it. */
  function mentions(text, street) {
    var key = streetKey(street);
    if (key.length < 3) return [];
    var plain = normalise(text), found = [], match;
    var pattern = new RegExp("(^|[^a-z0-9])(" + key.split("").join("[ -]*") + ")(?![a-z])", "g");
    while ((match = pattern.exec(plain)) !== null) {
      var start = match.index + match[1].length, before = plain.slice(0, start).trim().split(" ").pop();
      pattern.lastIndex = start + 1; // a street can be named again right behind itself
      if (LEADING.indexOf(before) !== -1) continue;
      found.push(numbersAfter(plain.slice(start + match[2].length).trim().split(" ").slice(0, 24)));
    }
    return found;
  }

  function distanceM(a, b) {
    var dx = (a.lon - b.lon) * M_PER_DEGREE * Math.cos(a.lat * Math.PI / 180), dy = (a.lat - b.lat) * M_PER_DEGREE;
    return Math.sqrt(dx * dx + dy * dy);
  }
  function located(item) { return typeof item.lat === "number" && typeof item.lon === "number"; }

  /* Whether one notice is about the address. Returns null or { soort, reden }:
     "adres"    the text names this street and house number, addition included (with a remark
                when the notice gives another postcode);
     "mogelijk" it may be: the same number with another or no addition, a range of numbers that
                includes it, or a location on the same parcel while the text names no such address;
     "straat"   the text names the street without any house number.
     `found` are the parcels of the address (may be empty). */
  function matchNotice(item, address, found) {
    var text = [item.plaats, item.titel, item.omschrijving].filter(Boolean).join(" \n ");
    var sameTown = !item.gemeente || !address.gemeente || normalise(item.gemeente) === normalise(address.gemeente);
    var exact = item.locatieSoort === "exact" && located(item) && typeof address.lat === "number";
    var away = exact ? distanceM(item, address) : null;
    var own = suffix(address.huisletter, address.toevoeging), postcode = address.postcode.toLowerCase(), nr = address.huisnummer;
    var best = null, streetOnly = false, numbered = false;

    (sameTown ? mentions(text, address.straat) : []).forEach(function (mention) {
      var confirmed = !!mention.postcode && mention.postcode === postcode;
      var other = !!mention.postcode && !!postcode && !confirmed;
      if (!mention.specs.length && !mention.unclear) { streetOnly = streetOnly || !other; return; }
      numbered = true;
      // The same street name and number elsewhere: the location of the notice decides. Without a
      // location, a postcode in another postcode area does.
      if (!confirmed && away !== null && away > NEAR_M) return;
      if (other && away === null && mention.postcode.slice(0, 4) !== postcode.slice(0, 4)) return;
      // A notice can carry a wrong postcode; say so instead of dropping it.
      var note = other ? "Het bericht noemt postcode " + mention.postcode.slice(0, 4) + " " + mention.postcode.slice(4).toUpperCase() +
        "; het adres heeft " + postcode.slice(0, 4) + " " + postcode.slice(4).toUpperCase() + "." : "";
      mention.specs.forEach(function (spec) {
        var hit = null;
        if (spec.n === nr && spec.s === own) hit = { soort: other && away === null ? "mogelijk" : "adres", reden: note };
        else if (spec.n === nr && !spec.s) hit = { soort: "mogelijk", reden: "Het bericht noemt huisnummer " + nr + " zonder toevoeging." };
        else if (spec.n === nr && !own) hit = { soort: "mogelijk", reden: "Het bericht noemt huisnummer " + nr + spec.s + "; het gekozen adres heeft geen toevoeging." };
        else if (spec.van !== undefined && nr >= spec.van && nr <= spec.tot) {
          hit = { soort: "mogelijk", reden: "Het bericht noemt de huisnummers " + spec.van + " tot en met " + spec.tot + "." };
        }
        if (hit && (!best || (best.soort !== "adres" && hit.soort === "adres"))) best = hit;
      });
    });
    if (best) return best;
    if (exact && (found || []).some(function (parcel) { return contains(parcel, item.lon, item.lat); })) {
      return { soort: "mogelijk", reden: "De tekst noemt dit adres niet, maar de locatie van het bericht ligt op hetzelfde perceel." };
    }
    if (streetOnly && !numbered && (away === null || away <= STREET_M)) {
      return { soort: "straat", reden: "Zelfde straat, geen huisnummer genoemd." };
    }
    return null;
  }

  /* One notice as the tab lists it: date, municipality, kind and a link to the source. */
  function noticeRow(item, reden) {
    return {
      id: item.id,
      datum: shortDate(item.datum),
      gemeente: item.gemeente || item.overheid || "",
      soort: (item.type === "plan" ? (item.soort || "Plan") : (TYPE_LABEL[item.type] || "Bericht")) + (item.fase ? ", " + String(item.fase).toLowerCase() : ""),
      titel: item.titel || "",
      url: safeUrl(item.url),
      weggefilterd: item.klasse === "weggefilterd",
      reden: reden || "",
    };
  }

  /* All notices about an address, also the ones the ranking filters out. The list keeps the order
     of the data file (newest first) and is not changed. */
  function findNotices(items, address, found) {
    var result = { adres: [], mogelijk: [], straat: [], doorzocht: (items || []).length };
    if (!address || !address.straat || !address.huisnummer) return result;
    (items || []).forEach(function (item) {
      var match = matchNotice(item, address, found);
      if (match) result[match.soort].push(noticeRow(item, match.reden));
    });
    return result;
  }

  /* The one line above the notices: which period the list covers. `windows` is vensterDagen of the
     data file (days a permit or a plan stays in the list). Without it the line still says that the
     list is short. */
  function periodLine(windows) {
    var permits = windows && windows.vergunning, plans = windows && windows.plan;
    var period = permits > 0 && plans > 0
      ? "Deze lijst beslaat alleen de laatste " + permits + " dagen voor vergunningen en " + plans + " dagen voor plannen."
      : "Deze lijst beslaat alleen de recente berichten die de app nu heeft.";
    return period + " \"Geen publicaties\" betekent dus niet dat er nooit iets is geweest.";
  }

  /* ---------- Zoning plan (Ruimtelijke plannen, through PDOK) ---------- */

  var PLAN_WAARSCHUWING = "Let op: wijzigingen sinds 1-1-2024 (Omgevingswet, omgevingsplan) ontbreken hier. Wat nu geldt, staat in Regels op de kaart van het Omgevingsloket.";
  var PLAN_GEEN_GETAL = "Bij deze bestemming staat geen getal op de kaart. Geen getal op de kaart betekent niet: geen beperking. Bouwhoogte, bebouwingspercentage en andere maten kunnen in de regels staan.";
  var PLAN_ONBEREIKBAAR = "De kaart met bestemmingsplannen (Ruimtelijke plannen, via PDOK) antwoordt niet. Bestemming en getallen ontbreken daardoor.";
  var PLAN_GESTOPT = "De dienst Ruimtelijke plannen van PDOK is niet gevonden op het bekende adres. Mogelijk is hij verplaatst of gestopt. Bestemming en getallen ontbreken daardoor; gebruik zolang Regels op de kaart.";
  var PLAN_ONBEKEND = "De dienst Ruimtelijke plannen van PDOK gaf een antwoord dat de app niet kent. Mogelijk is de dienst gewijzigd of gestopt. Bestemming en getallen ontbreken daardoor; gebruik zolang Regels op de kaart.";
  var UNITS = { m: " m", "%": "%", m2: " m²", "m²": " m²", graden: " graden" };

  /* One question for the four layers at the point of the address: a square of 2 by 2 metres in RD
     around it. Plain text, because the JSON answer carries the whole outline of every plan (close
     to 1 MB for a plan over the whole municipality); the text is a few kB. Null without a point. */
  function planUrl(rd) {
    if (!rd || typeof rd.x !== "number" || typeof rd.y !== "number" || !isFinite(rd.x) || !isFinite(rd.y)) return null;
    var layers = PLAN_LAGEN.join(",");
    return query(PLANKAART, {
      service: "WMS", version: "1.3.0", request: "GetFeatureInfo", layers: layers, query_layers: layers, styles: "", crs: "EPSG:28992",
      bbox: [rd.x - 1, rd.y - 1, rd.x + 1, rd.y + 1].map(function (v) { return v.toFixed(3); }).join(","),
      width: 101, height: 101, i: 50, j: 50, info_format: "text/plain", feature_count: 50,
    });
  }

  /* The plain text answer of the map service, as { layer: [ { field: value } ] }. Null when the text
     is not such an answer (an error report, a web page, nothing): the service has then changed. */
  function parsePlanText(text) {
    var lines = String(text === null || text === undefined ? "" : text).split(/\r?\n/);
    if (!/^GetFeatureInfo results:\s*$/.test(lines[0])) return null;
    var layers = {}, layer = null, feature = null;
    lines.slice(1).forEach(function (line) {
      var found;
      if ((found = /^Layer '([^']+)'\s*$/.exec(line))) { layer = layers[found[1]] = layers[found[1]] || []; feature = null; }
      else if (layer && /^\s+Feature [^:]*:\s*$/.test(line)) { feature = {}; layer.push(feature); }
      else if (feature && (found = /^\s+([a-z_]+) = '(.*)'\s*$/.exec(line))) feature[found[1]] = found[2];
    });
    return layers;
  }

  function lower(value) { return String(value || "").trim().toLowerCase(); }

  /* Whether a plan object counts: an adopted plan, not marked as history, in a dossier that has not
     been broken off or annulled. Anything else, an unknown status too, does not count. */
  function adopted(feature) {
    return VASTGESTELD.indexOf(lower(feature.planstatus)) !== -1 && !/^(1|true|ja)$/.test(lower(feature.historisch)) &&
      VERVALLEN.indexOf(lower(feature.dossierstatus)) === -1;
  }

  /* The figures of one object of the layer "maatvoering": '"maximum bouwhoogte (m)"="40"' becomes
     { label: "Maximum bouwhoogte", value: "40 m" }. Several in one object are all read. */
  function maten(text) {
    var out = [], pattern = /"([^"]+)"="([^"]*)"/g, found;
    while ((found = pattern.exec(String(text || ""))) !== null) {
      var name = found[1].split(";").pop().trim(), value = found[2].trim(), unit = /\(([^()]+)\)\s*$/.exec(name), extra = "";
      if (!name || !value) continue;
      if (unit) {
        name = name.slice(0, unit.index).trim();
        extra = Object.prototype.hasOwnProperty.call(UNITS, lower(unit[1])) ? UNITS[lower(unit[1])] : " " + unit[1].trim();
      }
      out.push({ label: name.charAt(0).toUpperCase() + name.slice(1), value: value.replace(/^(\d+)\.(\d+)$/, "$1,$2") + extra });
    }
    return out;
  }

  /* The link to the rules: only to ruimtelijkeplannen.nl, a web page before a PDF. */
  function rulesUrl(feature) {
    var urls = String((feature && feature.verwijzingnaartekst) || "").split(",").map(function (url) { return url.trim(); }).filter(function (url) {
      return url.indexOf(RP_DOCUMENTEN) === 0 && /^https:\/\/[^\s"'<>\\]+$/.test(url);
    });
    return urls.filter(function (url) { return /\.html?(#|$)/.test(url); })[0] || urls[0] || null;
  }

  function planStatusText(feature) { return String(feature.dossierstatus || feature.planstatus || "").trim(); }

  /* What the box "Bestemmingsplan en omgevingsplan" shows. `status` is the HTTP status of the answer
     (0 when none came), `text` its body, `today` the day of asking as "jjjj-mm-dd". Outcomes:
     gevonden, geen (no adopted plan at this point), onbereikbaar, gestopt (the service is gone from
     its address) and onbekend (an answer the app does not know). Where adopted plans overlap, all
     are listed, newest first, and the model says so: the app does not choose one. */
  function planModel(status, text, today) {
    if (status === 404 || status === 410) return { soort: "gestopt", tekst: PLAN_GESTOPT, opnieuw: true };
    if (status !== 200) return { soort: "onbereikbaar", tekst: PLAN_ONBEREIKBAAR, opnieuw: true };
    var layers = parsePlanText(text);
    if (!layers) return { soort: "onbekend", tekst: PLAN_ONBEKEND, opnieuw: true };

    var left = {}, kept = {}, plans = {};
    function counts(feature) {
      if (adopted(feature)) { kept[feature.plangebied || feature.identificatie || "?"] = true; return true; }
      // Say why: the status of the plan, or else the state of its dossier, or that it is history.
      left[feature.plangebied || feature.identificatie || "?"] = VASTGESTELD.indexOf(lower(feature.planstatus)) === -1 ? lower(feature.planstatus) || "zonder status"
        : VERVALLEN.indexOf(lower(feature.dossierstatus)) !== -1 ? lower(feature.dossierstatus) : "historisch";
      return false;
    }
    (layers.bestemmingsplangebied || []).forEach(function (plan) { if (counts(plan)) plans[plan.identificatie] = plan; });
    var seen = {}, enkel = (layers.enkelbestemming || []).filter(counts).filter(function (feature) {
      var key = feature.plangebied + "|" + feature.identificatie;
      return seen[key] ? false : (seen[key] = true);
    }).sort(function (a, b) { return String(b.datum || "").localeCompare(String(a.datum || "")); });
    var figures = (layers.maatvoering || []).filter(counts), dubbel = (layers.dubbelbestemming || []).filter(counts);

    // A figure belongs to the zoning area it names, or else to the zoning of its own plan.
    function owner(figure) {
      var named = /^Enkelbestemming=(.+)$/.exec(String(figure.bestemmingsvlak || "").trim());
      var match = enkel.filter(function (feature) { return named && feature.identificatie === named[1] && feature.plangebied === figure.plangebied; })[0];
      return match || enkel.filter(function (feature) { return feature.plangebied === figure.plangebied; })[0] || null;
    }
    function dedupe(rows) {
      var keys = {};
      return rows.filter(function (row) { var key = row.label + "=" + row.value; return keys[key] ? false : (keys[key] = true); });
    }
    function planName(id) { return (plans[id] && plans[id].naam) || id || ""; }

    var bestemmingen = enkel.map(function (feature) {
      return {
        naam: feature.naam || "", plan: planName(feature.plangebied), datum: shortDate(feature.datum), status: planStatusText(feature),
        maten: dedupe(figures.filter(function (figure) { return owner(figure) === feature; }).reduce(function (all, figure) { return all.concat(maten(figure.maatvoering)); }, [])),
        regels: rulesUrl(feature),
      };
    });
    var overige = {};
    figures.filter(function (figure) { return !owner(figure); }).forEach(function (figure) {
      var name = planName(figure.plangebied);
      overige[name] = dedupe((overige[name] || []).concat(maten(figure.maatvoering)));
    });
    // A plan of which something is shown is not also counted as left out.
    var leftOut = Object.keys(left).filter(function (key) { return !kept[key]; });
    var statuses = unique(leftOut.map(function (key) { return left[key]; })).sort(), notShown = leftOut.length;
    return {
      soort: bestemmingen.length ? "gevonden" : "geen",
      tekst: bestemmingen.length ? "" : "Op dit punt staat geen vastgesteld bestemmingsplan op de kaart van Ruimtelijke plannen.",
      bestemmingen: bestemmingen,
      overlap: bestemmingen.length > 1 ? "Op dit punt liggen " + bestemmingen.length + " vastgestelde plannen over elkaar. Ze staan hieronder allemaal, nieuwste eerst. " +
        "De app kiest er geen uit: welk plan voorgaat, staat in de plannen zelf." : "",
      dubbel: unique(dubbel.map(function (feature) { return String(feature.naam || "").trim(); }).filter(Boolean)).sort(),
      overigeMaten: Object.keys(overige).filter(function (name) { return overige[name].length; }).map(function (name) { return { plan: name, maten: overige[name] }; }),
      geenGetal: PLAN_GEEN_GETAL,
      waarschuwing: PLAN_WAARSCHUWING,
      nietGetoond: notShown ? "Niet getoond: " + notShown + (notShown === 1 ? " plan dat niet is vastgesteld of is vervallen" : " plannen die niet zijn vastgesteld of zijn vervallen") +
        " (" + statuses.join(", ") + ")." : "",
      bron: "Bron: Ruimtelijke plannen (Kadaster, via PDOK), opgevraagd op " + dutchDate(today) + ". Alleen vastgestelde plannen. De getallen zijn de maten op de plankaart; de regels kunnen meer zeggen.",
    };
  }

  /* ---------- Plain links to public viewers ---------- */

  function viewerLinks(address) {
    var number = [address.huisnummer, address.huisletter, address.toevoeging].filter(Boolean).join(" ");
    return {
      energielabel: { url: EP_ONLINE, label: "Zoek op EP-Online", zoekwaarde: (address.postcode + " " + number).trim() },
      plan: {
        url: address.rd ? query(REGELS_OP_DE_KAART + "/documenten", { "locatie-stelsel": "RD", "locatie-x": Math.round(address.rd.x), "locatie-y": Math.round(address.rd.y) }) : REGELS_OP_DE_KAART,
        label: "Open Regels op de kaart (Omgevingsloket)",
      },
    };
  }

  /* ---------- Energy label ---------- */

  /* What to ask the energy label Worker (tools/energielabel) for this address, as { url, body }, or
     null: when no Worker is set, when the setting is not an https address, or when the address has
     no postcode and house number in the form EP-Online knows. The address goes in the body and
     never in the url: the url of a request can end up in a log, the body does not. The Worker asks
     EP-Online; the key is known there and never here. */
  function energielabelVraag(worker, address) {
    if (typeof worker !== "string" || !/^https:\/\/[A-Za-z0-9.-]+(:\d+)?(\/[A-Za-z0-9._~\/-]*)?$/.test(worker)) return null;
    var postcode = String((address && address.postcode) || ""), number = String((address && address.huisnummer) || "");
    if (!/^[1-9][0-9]{3}[A-Z]{2}$/.test(postcode) || !/^[1-9][0-9]{0,4}$/.test(number)) return null;
    var asked = { postcode: postcode, huisnummer: number };
    if (address.huisletter) asked.huisletter = String(address.huisletter);
    if (address.toevoeging) asked.toevoeging = String(address.toevoeging);
    return { url: worker.replace(/\/+$/, "") + "/", body: JSON.stringify(asked) };
  }

  function dutchDate(iso) {
    var parts = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
    return parts ? parts[3] + "-" + parts[2] + "-" + parts[1] : "";
  }

  /* What the box "Energielabel" shows for an answer of the Worker. `status` is the HTTP status (0
     when no answer came), `body` the JSON of the answer, `today` the day of asking as "jjjj-mm-dd".
     Four outcomes, each with its own text: gevonden, geen, teveel and onbereikbaar. */
  function energielabelModel(status, body, today) {
    body = body && typeof body === "object" ? body : {};
    if (status === 200 && body.status === "gevonden" && typeof body.klasse === "string" && body.klasse) {
      return {
        soort: "gevonden", klasse: body.klasse.slice(0, 10),
        feiten: [
          { label: "Geregistreerd", value: dutchDate(body.registratiedatum) },
          { label: "Geldig tot", value: dutchDate(body.geldigTot) },
          { label: "Soort gebouw", value: typeof body.gebouw === "string" ? body.gebouw.slice(0, 40) : "" },
        ],
        bron: "Bron: EP-Online (Rijksdienst voor Ondernemend Nederland), opgevraagd op " + dutchDate(today) + ". Getoond is het laatst geregistreerde label dat nog geldig is.",
      };
    }
    if (status === 404) {
      // EP-Online answers the same for "no label" and for an address it does not know in this
      // spelling (seen with the real service on 19-11-2026), so the text names both.
      return { soort: "geen", tekst: "EP-Online vindt voor dit adres geen geldig label.",
        bron: "Mogelijk staat het label onder een andere schrijfwijze (huisletter of toevoeging). Zoek het na op ep-online.nl. Opgevraagd op " + dutchDate(today) + "." };
    }
    if (status === 429) {
      return { soort: "teveel", tekst: body.grens === "dag"
        ? "Er zijn vandaag te veel energielabels opgevraagd. Probeer het morgen opnieuw."
        : "Er worden op dit moment te veel energielabels opgevraagd. Probeer het over een minuut opnieuw.", opnieuw: body.grens !== "dag" };
    }
    if (status === 400) {
      return { soort: "geen", tekst: "Voor dit adres kan geen energielabel worden opgevraagd.", bron: "EP-Online herkent het huisnummer of de toevoeging niet in deze vorm." };
    }
    return { soort: "onbereikbaar", tekst: "Het energielabel kon niet worden opgevraagd: de dienst is niet bereikbaar.", opnieuw: true };
  }

  return {
    energielabelVraag: energielabelVraag, energielabelModel: energielabelModel,
    MAX_PANDEN: MAX_PANDEN, MAX_PERCELEN: MAX_PERCELEN, NEAR_M: NEAR_M,
    normalise: normalise, streetKey: streetKey, suffix: suffix, searchText: searchText,
    parcelCode: parcelCode, suggestUrl: suggestUrl, addressFromDoc: addressFromDoc, addresses: addresses, houseNumber: houseNumber,
    vboUrl: vboUrl, pandUrls: pandUrls, bagModel: bagModel,
    perceelUrl: perceelUrl, perceelAtUrl: perceelAtUrl, parcelModel: parcelModel, parcels: parcels, parcelAt: parcelAt, contains: contains,
    mapModel: mapModel, m2: m2,
    numbersAfter: numbersAfter, mentions: mentions, matchNotice: matchNotice, noticeRow: noticeRow, findNotices: findNotices, periodLine: periodLine,
    viewerLinks: viewerLinks,
    planUrl: planUrl, parsePlanText: parsePlanText, planModel: planModel, maten: maten, rulesUrl: rulesUrl, adopted: adopted,
  };
});
