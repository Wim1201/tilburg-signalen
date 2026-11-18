/* Tilburg Signalen: the logic of the app without the page. Ranking, filtering, "new since my last
   visit", the morning line and the content of one card. app.js turns the results into elements;
   the tests run this file under Node. Nothing here changes the data or the rules: the score, the
   class and the sentence come from data/berichten.json as they are. */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.TilburgSignalen = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var NEW_HOURS = 14; // an item counts as "new" for this long after this device first saw it
  var TOP = 10;       // what the list shows before "Toon alle"
  var RANKED = ["ontwikkellocatie", "onzeker"];
  var KERN = "kern";  // the label of everything within the radius
  var TYPE_LABEL = { vergunning: "Vergunning", plan: "Plan", faillissement: "Faillissement", verkoop: "Verkoop overheid" };
  var VIEW_KLASSE = { ranglijst: "ontwikkellocatie", nieuw: "ontwikkellocatie", onzeker: "onzeker" };

  function isoDay(date) {
    return date.getFullYear() + "-" + String(date.getMonth() + 1).padStart(2, "0") + "-" + String(date.getDate()).padStart(2, "0");
  }
  function daysAgoIso(days, today) { var d = new Date(today.getTime()); d.setDate(d.getDate() - days); return isoDay(d); }
  function shortDate(iso) { var p = iso.split("-"); return p[2] + "-" + p[1] + "-" + p[0]; }
  function km(value) { return (value || 0).toFixed(1).replace(".", ","); }
  function capitalise(text) { return text ? text.charAt(0).toUpperCase() + text.slice(1) : text; }
  function safeUrl(url) { return typeof url === "string" && /^https:\/\//.test(url) ? url : null; }
  function hasPoint(item) { return item.lat !== null && item.lat !== undefined; }

  function latestDay(items) {
    return items.reduce(function (latest, item) { return item.datum > latest ? item.datum : latest; }, "");
  }

  /* Highest score first; with equal scores the newest notice, then the nearest. */
  function byRelevance(a, b) {
    return b.score - a.score || (a.datum < b.datum ? 1 : a.datum > b.datum ? -1 : a.afstandKm - b.afstandKm);
  }

  function sorted(items, sort) {
    var list = items.slice();
    if (sort === "afstand") list.sort(function (a, b) { return a.afstandKm - b.afstandKm || (a.datum < b.datum ? 1 : -1); });
    else if (sort === "relevantie") list.sort(byRelevance);
    return list; // "datum": the data file is already newest first
  }

  /* Place in the ranking per class, 1 = highest. It does not move when the list is filtered or
     sorted differently, so "3" always means the third most relevant location of all. */
  function rankMap(items) {
    var ranks = {};
    RANKED.forEach(function (klasse) {
      items.filter(function (item) { return item.klasse === klasse; }).sort(byRelevance)
        .forEach(function (item, index) { ranks[item.id] = index + 1; });
    });
    return ranks;
  }

  /* "New since my last visit": per device, when each item was first seen. `seen` is what the
     previous visit stored (null on a first visit); `next` is what to store now. On a first visit
     only the latest publication day counts as new, otherwise everything would be. */
  function markNew(items, seen, now) {
    var firstVisit = !seen || typeof seen !== "object", latest = latestDay(items), next = {}, nieuw = {};
    items.forEach(function (item) {
      var first = firstVisit ? (item.datum === latest ? now : 0) : (seen[item.id] !== undefined ? seen[item.id] : now);
      next[item.id] = first;
      if (now - first < NEW_HOURS * 3600 * 1000) nieuw[item.id] = true;
    });
    return { nieuw: nieuw, next: next, firstVisit: firstVisit };
  }

  /* Filters that apply to every list; the class is chosen separately. */
  function matches(item, filters, context) {
    if (filters.type && item.type !== filters.type) return false;
    if (filters.gemeente && item.gemeente !== filters.gemeente) return false;
    if (filters.fase && item.fase !== filters.fase) return false;
    if (filters.signaal && item.signalen.indexOf(filters.signaal) === -1) return false;
    if (item.afstandKm > filters.maxKm) return false;
    if (filters.alleenNieuw && !context.nieuw[item.id]) return false;
    if (filters.dagen === 1 && item.datum !== context.latestDay) return false;
    if (filters.dagen > 1 && item.datum < daysAgoIso(filters.dagen, context.today)) return false;
    if (filters.zoek) {
      var hay = [item.titel, item.omschrijving, item.waarom, item.plaats, item.gemeente, item.overheid, item.fase].join(" ").toLowerCase();
      var words = filters.zoek.toLowerCase().split(/\s+/).filter(Boolean);
      for (var i = 0; i < words.length; i++) if (hay.indexOf(words[i]) === -1) return false;
    }
    return true;
  }

  /* The lists for one view: "ranglijst" (all development locations), "nieuw" (the same, only what
     is new on this device) or "onzeker". `alsoNew` holds the new unsure notices in the view
     "nieuw", so that nothing new stays out of sight. `removed` is filled only when the switch is on. */
  function select(items, state, context) {
    var klasse = VIEW_KLASSE[state.view] || "ontwikkellocatie";
    var filters = Object.assign({}, state, { alleenNieuw: state.view === "nieuw" });
    var removedFilters = Object.assign({}, state, { alleenNieuw: false });
    function pick(wanted, which) {
      return sorted(items.filter(function (item) { return item.klasse === wanted && matches(item, which, context); }), state.sort);
    }
    return {
      klasse: klasse, main: pick(klasse, filters),
      alsoNew: state.view === "nieuw" ? pick("onzeker", filters) : [],
      removed: state.toonWeg ? pick("weggefilterd", removedFilters) : [],
    };
  }

  function counts(items, nieuw) {
    var result = { locaties: 0, nieuw: 0, onzeker: 0, onzekerNieuw: 0, weggefilterd: 0 };
    items.forEach(function (item) {
      if (item.klasse === "ontwikkellocatie") { result.locaties++; if (nieuw[item.id]) result.nieuw++; }
      else if (item.klasse === "onzeker") { result.onzeker++; if (nieuw[item.id]) result.onzekerNieuw++; }
      else result.weggefilterd++;
    });
    return result;
  }

  function greeting(hour) { return hour < 12 ? "Goedemorgen" : hour < 18 ? "Goedemiddag" : "Goedenavond"; }

  /* Under the morning line: new notices that are not (yet) a development location. */
  function alsoNewLine(count) {
    if (!count) return "";
    return count === 1 ? "Ook 1 nieuw bericht onder Onzeker." : "Ook " + count + " nieuwe berichten onder Onzeker.";
  }

  /* The one line at the top of the morning: how many locations are new. */
  function briefing(count, firstVisit) {
    if (firstVisit) {
      if (!count) return "Geen ontwikkellocaties op de laatste publicatiedag.";
      return count === 1 ? "1 ontwikkellocatie op de laatste publicatiedag." : count + " ontwikkellocaties op de laatste publicatiedag.";
    }
    if (!count) return "Geen nieuwe ontwikkellocaties sinds je vorige bezoek.";
    return count === 1 ? "1 nieuwe ontwikkellocatie sinds je vorige bezoek." : count + " nieuwe ontwikkellocaties sinds je vorige bezoek.";
  }

  function offsetKm(item, centre) {
    return {
      x: (item.lon - centre.lon) * 111.2 * Math.cos(centre.lat * Math.PI / 180),
      y: (item.lat - centre.lat) * 111.2,
    };
  }
  /* Compass direction from the centre to a point (Dutch abbreviations). */
  function compass(item, centre) {
    if (!hasPoint(item) || item.afstandKm < 0.3) return "";
    var o = offsetKm(item, centre);
    var angle = (Math.atan2(o.x, o.y) * 180 / Math.PI + 360) % 360;
    return ["N", "NO", "O", "ZO", "Z", "ZW", "W", "NW"][Math.round(angle / 45) % 8];
  }

  /* Everything one card shows, as plain values. context: { centre, nieuw, ranks, today } with
     today as "jjjj-mm-dd". The first thing on the card is `why`: the one sentence from the rules. */
  function cardModel(item, context) {
    var place = capitalise(item.plaats || (item.gemeente ? "Gemeente " + item.gemeente : item.overheid));
    var distance = (km(item.afstandKm) + " km " + compass(item, context.centre)).trim();
    var note = null;
    if (item.locatieSoort === "gemeente") {
      place = "Gemeente " + item.gemeente;
      note = "Geen exacte locatie; de afstand van " + distance + " geldt voor gemeente " + item.gemeente + ".";
      distance = "geen exacte locatie";
    } else if (item.locatieSoort === "benaderd") {
      note = "Locatie bij benadering, afgeleid uit de titel.";
      distance = "± " + distance;
    }
    var links = [];
    if (safeUrl(item.url)) links.push({ label: "Open bij de bron", url: item.url });
    if (safeUrl(item.urlTekst)) links.push({ label: "Alleen tekst", url: item.urlTekst });
    if (hasPoint(item)) {
      links.push({ label: "Kaart", url: "https://www.openstreetmap.org/?mlat=" + item.lat + "&mlon=" + item.lon + "#map=17/" + item.lat + "/" + item.lon });
    }
    return {
      id: item.id,
      klasse: item.klasse,
      rank: context.ranks[item.id] || null,
      isNew: !!context.nieuw[item.id],
      why: item.waarom,
      title: item.titel,
      type: item.type,
      kind: item.type === "plan" ? (item.soort || "Plan") : TYPE_LABEL[item.type],
      fase: item.fase,
      place: place,
      distance: distance,
      date: shortDate(item.datum),
      score: item.klasse === "ontwikkellocatie" ? item.score : null,
      deadline: item.reactieTot && item.reactieTot >= context.today ? "Reageren tot " + shortDate(item.reactieTot) : null,
      description: item.omschrijving || null,
      activities: (item.activiteiten || []).join(", "),
      locationNote: note,
      source: "Bron: " + item.publicatie + (item.bron === "omgevingsloket-vlaanderen" ? "" : " " + item.overheid),
      links: links,
    };
  }

  /* ---------- Regions around the core ----------
     The app opens with the core: the notices in data/berichten.json, all within the radius. Around
     it lie regions, each with a file of its own that is read when someone chooses the region.
     Every municipality carries `regio`: "kern" or the name of its region. Data from before the
     regions has no label and counts as the core. */
  function regioOf(entry) { return (entry && entry.regio) || KERN; }

  /* The municipalities of the area tab for a choice of regions, in the order of the file (nearest
     first). The core is always shown. */
  function gemeentenIn(area, chosen) {
    return area.gemeenten.filter(function (gemeente) { var regio = regioOf(gemeente); return regio === KERN || (chosen || []).indexOf(regio) !== -1; });
  }

  /* The regions that can be chosen, with what choosing one adds. `overview` is `regios` of
     data/berichten.json: per region its file and how many notices it holds. A region without a
     file is left out, so data from before the regions offers no choice. */
  function regios(area, overview) {
    return (overview || []).filter(function (regio) { return regio && regio.naam && regio.bestand; }).map(function (regio) {
      return {
        naam: regio.naam, bestand: regio.bestand, berichten: regio.berichten || 0, locaties: regio.locaties || 0, onzeker: regio.onzeker || 0,
        ongelezen: regio.ongelezen || 0, mislukt: regio.mislukt || 0,
        gemeenten: area.gemeenten.filter(function (gemeente) { return regioOf(gemeente) === regio.naam; }).length,
      };
    });
  }

  /* What the chosen regions still miss, as the lines the app shows with them. The morning screen
     reports the core only (`ophaalfouten` of the data file); a region reports its own shortfall, and
     only when it is chosen. `ongelezen`: texts that wait for a later run, because a run reads a
     limited number of new texts of the regions. `mislukt`: downloads that failed. */
  function regioMeldingen(overview, chosen) {
    var lines = [];
    (overview || []).forEach(function (regio) {
      if (!regio || (chosen || []).indexOf(regio.naam) === -1) return;
      if (regio.ongelezen) {
        lines.push(regio.ongelezen === 1
          ? "Van " + regio.naam + " is 1 bericht nog niet gelezen. Het staat onder Onzeker met \"Tekst nog niet gelezen\"; een volgende verversing haalt het op."
          : "Van " + regio.naam + " zijn " + regio.ongelezen + " berichten nog niet gelezen. Ze staan onder Onzeker met \"Tekst nog niet gelezen\"; de volgende verversingen halen ze op.");
      }
      if (regio.mislukt) {
        lines.push(regio.mislukt === 1
          ? "Bij de laatste verversing kon 1 bekendmaking van " + regio.naam + " niet volledig worden gelezen. Ze staat tijdelijk onder Onzeker; de volgende verversing probeert het opnieuw."
          : "Bij de laatste verversing konden " + regio.mislukt + " bekendmakingen van " + regio.naam + " niet volledig worden gelezen. Ze staan tijdelijk onder Onzeker; de volgende verversing probeert het opnieuw.");
      }
    });
    return lines;
  }

  /* The regions whose file can hold notices about a municipality: its own region, or for a
     municipality of the core the region of the part outside the radius. A municipality that lies
     wholly within the radius has nothing outside it. */
  function regiosFor(area, gemeente) {
    var found = [];
    area.gemeenten.forEach(function (entry) {
      if (entry.naam !== gemeente) return;
      var regio = regioOf(entry) === KERN ? (entry.dekking === "geheel" ? null : entry.buitenStraal) : entry.regio;
      if (regio && found.indexOf(regio) === -1) found.push(regio);
    });
    return found;
  }

  /* The core and the notices of the chosen regions as one list, in the order of the data file:
     newest first, then nearest. The core on its own is returned as it is. */
  function merged(core, lists) {
    var extra = (lists || []).filter(function (list) { return list && list.length; });
    if (!extra.length) return core;
    return extra.reduce(function (all, list) { return all.concat(list); }, core.slice()).sort(function (a, b) {
      return (a.datum < b.datum ? 1 : a.datum > b.datum ? -1 : 0) || a.afstandKm - b.afstandKm || (a.id < b.id ? 1 : a.id > b.id ? -1 : 0);
    });
  }

  /* The farthest the distance filter has to reach: the radius for the core, further with a region. */
  function reachKm(items, radiusKm) {
    return items.reduce(function (reach, item) { return item.afstandKm > reach ? Math.ceil(item.afstandKm) : reach; }, radiusKm);
  }

  /* "Midden-Brabant", "Midden-Brabant en Zeeland", "Midden-Brabant, West-Brabant en Zeeland". */
  function nameList(names) {
    return names.length > 1 ? names.slice(0, -1).join(", ") + " en " + names[names.length - 1] : names.join("");
  }

  /* The line under the name of the app: what the app shows now. The core alone with its radius; with
     regions only the names, so that the line stays short on a narrow phone. */
  function scopeLine(straalKm, centrum, regios) {
    return regios && regios.length ? nameList(["Kern"].concat(regios)) : "Kern: binnen " + straalKm + " km van " + centrum;
  }

  /* The introduction on the tab Gebied, for the same choice. `kern` is the number of municipalities
     of the core, `totaal` the number on the list with the chosen regions. */
  function gebiedIntro(straalKm, centrum, kern, regios, totaal) {
    var core = "alles binnen " + straalKm + " km hemelsbreed van " + centrum;
    if (!regios || !regios.length) {
      return "Kern: " + core + ". Daarin liggen " + kern + " gemeenten, waarvan de meeste maar voor een deel. Een bericht telt mee als de locatie zelf binnen de straal valt.";
    }
    return nameList(["Kern"].concat(regios)) + ". De kern is " + core + ": " + kern + " gemeenten, waarvan de meeste maar voor een deel. Van " +
      (regios.length === 1 ? regios[0] : "de gekozen regio's") + " telt elke gemeente in haar geheel mee. Samen staan er nu " + totaal + " gemeenten op de lijst.";
  }

  /* Whether what the app shows was fetched long enough ago to fetch it again (both in milliseconds). */
  function stale(loadedAt, now, minutes) {
    return now - loadedAt >= minutes * 60000;
  }

  /* Where the texts on the small map go, so that no place name covers another, no ring label lies
     behind a dot and no ring label covers a place name. Plain geometry in the units of the drawing:
     km from the centre, x to the east and y to the south.
       towns: [{ naam, x, y }]   the place itself; its name stands centred just above it
       rings: [5, 10, 15]        every ring gets "<km> km" just inside its line
       dots:  [{ x, y, r }]      the locations that are drawn
     Returns { towns: [{ naam, x, y, krap }], rings: [{ km, tekst, x, y, krap }] } with x the middle
     of the text and y its baseline. Earlier towns keep their place. A later one that would cover a
     name first slides sideways, away from that name and no further than needed, so that it stays at
     the height of its place; only then it moves below, above or beside it. A ring label walks along
     its ring, starting in the north. `krap` says that
     no free place was found and the text stands where it bothers least. The widths are estimates
     that err on the wide side: the fonts are set in styles.css (.radar .town and .radar .ring-label). */
  var RADAR = { edge: 18.3, townChar: 0.62, ringChar: 0.63, up: 0.9, down: 0.3, gap: 0.12 };
  function radarBox(x, baseline, width) {
    return { l: x - width / 2, r: x + width / 2, t: baseline - RADAR.up, b: baseline + RADAR.down };
  }
  function radarHit(a, b) {
    return a.l < b.r + RADAR.gap && b.l < a.r + RADAR.gap && a.t < b.b + RADAR.gap && b.t < a.b + RADAR.gap;
  }
  function radarInside(box) {
    return box.l >= -RADAR.edge && box.r <= RADAR.edge && box.t >= -RADAR.edge && box.b <= RADAR.edge;
  }
  function radarLabels(towns, rings, dots) {
    var placed = [], result = { towns: [], rings: [] };
    function hits(box, others) { return others.filter(function (other) { return radarHit(box, other); }).length; }
    towns.forEach(function (town) {
      var width = town.naam.length * RADAR.townChar, aside = width / 2 + 0.8;
      var shifts = [[0, 0], [0, 1.7], [0, -1.4], [aside, 0.6], [-aside, 0.6], [0, 3], [0, -2.8], [aside, -0.8], [-aside, -0.8]];
      var boxes = shifts.map(function (shift) { return radarBox(town.x + shift[0], town.y + shift[1], width); });
      var blockers = placed.filter(function (other) { return radarHit(boxes[0], other); });
      if (blockers.length) {
        var clear = RADAR.gap + 0.05;
        var left = Math.min.apply(null, blockers.map(function (other) { return other.l; })) - clear - boxes[0].r;
        var right = Math.max.apply(null, blockers.map(function (other) { return other.r; })) + clear - boxes[0].l;
        var slides = (-left <= right ? [left, right] : [right, left]).filter(function (dx) { return Math.abs(dx) <= width / 2 + 1; });
        boxes = [boxes[0]].concat(slides.map(function (dx) { return radarBox(town.x + dx, town.y, width); }), boxes.slice(1));
      }
      var free = boxes.filter(function (box) { return radarInside(box) && !hits(box, placed); })[0];
      var box = free || boxes[0];
      placed.push(box);
      result.towns.push({ naam: town.naam, x: (box.l + box.r) / 2, y: box.t + RADAR.up, krap: !free });
    });
    var dotBoxes = dots.map(function (dot) { return { l: dot.x - dot.r, r: dot.x + dot.r, t: dot.y - dot.r, b: dot.y + dot.r }; });
    dotBoxes.push({ l: -0.45, r: 0.45, t: -0.45, b: 0.45 }); // the centre
    var angles = [0];
    for (var step = 1; step <= 12; step++) angles.push(step * 15, -step * 15);
    rings.forEach(function (km) {
      var text = km + " km", width = text.length * RADAR.ringChar, height = RADAR.up + RADAR.down;
      var candidates = angles.slice(0, 24).map(function (degrees) {
        var angle = degrees * Math.PI / 180, sin = Math.sin(angle), cos = Math.cos(angle);
        // Far enough inside the ring that the text does not touch its line, whatever the direction.
        var radius = km - 0.35 - Math.abs(sin) * width / 2 - Math.abs(cos) * height / 2;
        var cx = radius * sin, cy = -radius * cos;
        var box = radarBox(cx, cy + (RADAR.up - RADAR.down) / 2, width);
        return { box: box, dots: hits(box, dotBoxes), texts: hits(box, placed) };
      });
      var free = candidates.filter(function (candidate) { return !candidate.dots && !candidate.texts; })[0];
      var best = free || candidates.slice().sort(function (a, b) { return a.texts - b.texts || a.dots - b.dots; })[0];
      placed.push(best.box);
      result.rings.push({ km: km, tekst: text, x: (best.box.l + best.box.r) / 2, y: best.box.t + RADAR.up, krap: !free });
    });
    return result;
  }

  return {
    stale: stale, radarLabels: radarLabels, scopeLine: scopeLine, gebiedIntro: gebiedIntro,
    KERN: KERN, regioOf: regioOf, gemeentenIn: gemeentenIn, regios: regios, regioMeldingen: regioMeldingen, regiosFor: regiosFor, merged: merged, reachKm: reachKm, nameList: nameList,
    NEW_HOURS: NEW_HOURS, TOP: TOP, TYPE_LABEL: TYPE_LABEL,
    isoDay: isoDay, daysAgoIso: daysAgoIso, shortDate: shortDate, km: km, safeUrl: safeUrl, hasPoint: hasPoint,
    latestDay: latestDay, byRelevance: byRelevance, sorted: sorted, rankMap: rankMap, markNew: markNew,
    matches: matches, select: select, counts: counts, greeting: greeting, briefing: briefing, alsoNewLine: alsoNewLine,
    offsetKm: offsetKm, compass: compass, cardModel: cardModel,
  };
});
