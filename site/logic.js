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
  var TYPE_LABEL = { vergunning: "Vergunning", plan: "Plan", faillissement: "Faillissement", verkoop: "Verkoop overheid" };
  var VIEW_KLASSE = { ranglijst: "ontwikkellocatie", nieuw: "ontwikkellocatie", onzeker: "onzeker" };

  function isoDay(date) {
    return date.getFullYear() + "-" + String(date.getMonth() + 1).padStart(2, "0") + "-" + String(date.getDate()).padStart(2, "0");
  }
  function daysAgoIso(days, today) { var d = new Date(today.getTime()); d.setDate(d.getDate() - days); return isoDay(d); }
  function shortDate(iso) { var p = iso.split("-"); return p[2] + "-" + p[1] + "-" + p[0]; }
  function km(value) { return value.toFixed(1).replace(".", ","); }
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
     is new on this device) or "onzeker". `removed` is filled only when the switch is on. */
  function select(items, state, context) {
    var klasse = VIEW_KLASSE[state.view] || "ontwikkellocatie";
    var filters = Object.assign({}, state, { alleenNieuw: state.view === "nieuw" });
    var removedFilters = Object.assign({}, state, { alleenNieuw: false });
    function pick(wanted, which) {
      return sorted(items.filter(function (item) { return item.klasse === wanted && matches(item, which, context); }), state.sort);
    }
    return { klasse: klasse, main: pick(klasse, filters), removed: state.toonWeg ? pick("weggefilterd", removedFilters) : [] };
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

  return {
    NEW_HOURS: NEW_HOURS, TOP: TOP, TYPE_LABEL: TYPE_LABEL,
    isoDay: isoDay, daysAgoIso: daysAgoIso, shortDate: shortDate, km: km, safeUrl: safeUrl, hasPoint: hasPoint,
    latestDay: latestDay, byRelevance: byRelevance, sorted: sorted, rankMap: rankMap, markNew: markNew,
    matches: matches, select: select, counts: counts, greeting: greeting, briefing: briefing,
    offsetKm: offsetKm, compass: compass, cardModel: cardModel,
  };
});
