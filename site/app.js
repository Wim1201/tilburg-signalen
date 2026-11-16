/* Tilburg Signalen: reads data/berichten.json and data/gebied.json and renders three views. */
(function () {
  "use strict";

  var PAGE = 60;
  var NEW_HOURS = 14; // an item counts as "new" for this long after this device first saw it
  var STORE_KEY = "tilburg-signalen.gezien";
  var VIEWS = ["berichten", "gebied", "bronnen"];
  var state = {
    data: null, area: null, klasse: "ontwikkellocatie", toonWeg: false, zoek: "", type: "", gemeente: "",
    fase: "", signaal: "", dagen: 0, sort: "relevantie", maxKm: 15, alleenNieuw: false, limit: PAGE, nieuw: {},
  };

  function $(id) { return document.getElementById(id); }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function safeUrl(url) {
    return typeof url === "string" && /^https:\/\//.test(url) ? url : null;
  }

  function link(url, text) {
    var a = el("a", null, text);
    a.href = url; a.target = "_blank"; a.rel = "noopener";
    return a;
  }

  var nf = new Intl.NumberFormat("nl-NL", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  var dayFormat = new Intl.DateTimeFormat("nl-NL", { weekday: "long", day: "numeric", month: "long" });
  var shortDate = new Intl.DateTimeFormat("nl-NL", { day: "2-digit", month: "2-digit", year: "numeric" });
  var stampFormat = new Intl.DateTimeFormat("nl-NL", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

  function parseDay(iso) { var p = iso.split("-"); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function isoDay(date) {
    return date.getFullYear() + "-" + String(date.getMonth() + 1).padStart(2, "0") + "-" + String(date.getDate()).padStart(2, "0");
  }
  function daysAgoIso(days) { var d = new Date(); d.setDate(d.getDate() - days); return isoDay(d); }
  function dayLabel(iso) {
    var label = dayFormat.format(parseDay(iso));
    if (iso === isoDay(new Date())) return "Vandaag, " + label;
    if (iso === daysAgoIso(1)) return "Gisteren, " + label;
    return label.charAt(0).toUpperCase() + label.slice(1);
  }

  /* Compass direction from the centre to a point (Dutch abbreviations). */
  function offsetKm(item, centre) {
    return {
      x: (item.lon - centre.lon) * 111.2 * Math.cos(centre.lat * Math.PI / 180),
      y: (item.lat - centre.lat) * 111.2,
    };
  }
  function compass(item, centre) {
    if (item.lat === null || item.lat === undefined || item.afstandKm < 0.3) return "";
    var o = offsetKm(item, centre);
    var angle = (Math.atan2(o.x, o.y) * 180 / Math.PI + 360) % 360;
    return ["N", "NO", "O", "ZO", "Z", "ZW", "W", "NW"][Math.round(angle / 45) % 8];
  }

  /* "New since my last visit": remember per device when each item was first seen. */
  function markNew(items) {
    var seen = null, now = Date.now(), next = {}, result = {};
    try { seen = JSON.parse(localStorage.getItem(STORE_KEY)); } catch (e) { seen = null; }
    var firstVisit = !seen || typeof seen !== "object";
    var latestDay = items.length ? items.reduce(function (a, b) { return a.datum > b.datum ? a : b; }).datum : "";
    items.forEach(function (item) {
      var first = firstVisit ? (item.datum === latestDay ? now : 0) : (seen[item.id] !== undefined ? seen[item.id] : now);
      next[item.id] = first;
      if (now - first < NEW_HOURS * 3600 * 1000) result[item.id] = true;
    });
    try { localStorage.setItem(STORE_KEY, JSON.stringify(next)); } catch (e) { /* storage is optional */ }
    return result;
  }

  var TYPE_LABEL = { vergunning: "Vergunning", plan: "Plan", faillissement: "Faillissement", verkoop: "Verkoop overheid" };
  var KLASSE_LABEL = { ontwikkellocatie: "Ontwikkellocaties", onzeker: "Onzeker", weggefilterd: "Weggefilterd" };

  /* Filters that apply to every list; the class (ontwikkellocatie, onzeker, weggefilterd) is chosen separately. */
  function matches(item) {
    if (state.type && item.type !== state.type) return false;
    if (state.gemeente && item.gemeente !== state.gemeente) return false;
    if (state.fase && item.fase !== state.fase) return false;
    if (state.signaal && item.signalen.indexOf(state.signaal) === -1) return false;
    if (item.afstandKm > state.maxKm) return false;
    if (state.alleenNieuw && !state.nieuw[item.id]) return false;
    if (state.dagen === 1 && item.datum !== state.latestDay) return false;
    if (state.dagen > 1 && item.datum < daysAgoIso(state.dagen)) return false;
    if (state.zoek) {
      var hay = [item.titel, item.omschrijving, item.waarom, item.plaats, item.gemeente, item.overheid, item.fase].join(" ").toLowerCase();
      var words = state.zoek.toLowerCase().split(/\s+/).filter(Boolean);
      for (var i = 0; i < words.length; i++) if (hay.indexOf(words[i]) === -1) return false;
    }
    return true;
  }

  function sorted(items) {
    var list = items.slice();
    if (state.sort === "afstand") {
      list.sort(function (a, b) { return a.afstandKm - b.afstandKm || (a.datum < b.datum ? 1 : -1); });
    } else if (state.sort === "relevantie") {
      list.sort(function (a, b) { return b.score - a.score || (a.datum < b.datum ? 1 : a.datum > b.datum ? -1 : a.afstandKm - b.afstandKm); });
    }
    return list; // "datum": the data file is already newest first
  }

  function ofClass(klasse) {
    return state.data.berichten.filter(function (item) { return item.klasse === klasse; });
  }

  function countBy(items, key) {
    var counts = {};
    items.forEach(function (item) {
      [].concat(item[key] || []).forEach(function (value) { counts[value] = (counts[value] || 0) + 1; });
    });
    return counts;
  }

  function fillSelect(select, counts, labels) {
    Object.keys(counts).sort(function (a, b) { return a.localeCompare(b, "nl"); }).forEach(function (value) {
      var option = el("option", null, ((labels && labels[value]) || value) + " (" + counts[value] + ")");
      option.value = value;
      select.appendChild(option);
    });
  }

  function figure(value, label, className) {
    var box = el("div", "figure " + className);
    box.appendChild(el("b", null, String(value)));
    box.appendChild(el("span", null, label));
    return box;
  }

  function renderSummary() {
    var relevant = ofClass("ontwikkellocatie"), unsure = ofClass("onzeker"), box = $("summary");
    box.textContent = "";
    var line = el("p", "summary-day");
    line.appendChild(document.createTextNode("Laatste publicatiedag: "));
    line.appendChild(el("strong", null, state.latestDay ? dayLabel(state.latestDay).toLowerCase() : "nog geen berichten"));
    box.appendChild(line);
    var isNew = function (item) { return state.nieuw[item.id]; };
    var figures = el("div", "summary-figures");
    figures.appendChild(figure(relevant.length, "ontwikkellocaties", "is-permit"));
    figures.appendChild(figure(unsure.length, "onzeker", "is-plan"));
    figures.appendChild(figure(relevant.filter(isNew).length + unsure.filter(isNew).length, "nieuw sinds vorig bezoek", "is-new"));
    box.appendChild(figures);
  }

  function card(item) {
    var centre = state.data.centrum;
    var node = el("article", "card is-" + item.klasse + (state.nieuw[item.id] ? " is-new" : ""));

    var chips = el("div", "chips");
    chips.appendChild(el("span", "chip is-" + item.type, item.type === "plan" ? (item.soort || "Plan") : TYPE_LABEL[item.type]));
    chips.appendChild(el("span", "chip", item.fase));
    if (item.klasse === "ontwikkellocatie") chips.appendChild(el("span", "chip is-score", "relevantie " + item.score));
    if (state.nieuw[item.id]) chips.appendChild(el("span", "chip is-new", "Nieuw"));
    node.appendChild(chips);

    var plate = el("div", "plate");
    plate.appendChild(el("b", null, nf.format(item.afstandKm)));
    plate.appendChild(el("span", null, ("km " + compass(item, centre)).trim()));
    plate.title = "Afstand tot " + centre.naam;
    node.appendChild(plate);

    node.appendChild(el("p", "why", item.waarom));
    node.appendChild(el("h4", null, item.titel));
    if (item.omschrijving) node.appendChild(el("p", "desc", item.omschrijving));

    var where = el("p", "where");
    var place = item.plaats || (item.gemeente ? "Gemeente " + item.gemeente : item.overheid);
    if (item.locatieSoort === "gemeente") place = "Geen exacte locatie; afstand geldt voor gemeente " + item.gemeente;
    if (item.locatieSoort === "benaderd") place += " (locatie bij benadering, afgeleid uit de titel)";
    where.appendChild(el("span", null, place));
    if (item.activiteiten.length) where.appendChild(el("span", null, item.activiteiten.join(", ")));
    if (item.reactieTot && item.reactieTot >= isoDay(new Date())) {
      where.appendChild(el("span", "deadline", "Reageren tot " + shortDate.format(parseDay(item.reactieTot))));
    }
    node.appendChild(where);

    var source = el("p", "source");
    var name = item.publicatie + (item.bron === "omgevingsloket-vlaanderen" ? "" : " " + item.overheid);
    source.appendChild(el("span", null, "Bron: " + name + " · " + shortDate.format(parseDay(item.datum))));
    var links = el("span"), parts = [];
    var url = safeUrl(item.url);
    if (url) parts.push(link(url, "Open bij de bron"));
    if (safeUrl(item.urlTekst)) parts.push(link(item.urlTekst, "Alleen tekst"));
    if (item.lat !== null && item.lat !== undefined) {
      parts.push(link("https://www.openstreetmap.org/?mlat=" + item.lat + "&mlon=" + item.lon + "#map=17/" + item.lat + "/" + item.lon, "Kaart"));
    }
    parts.forEach(function (part, index) {
      if (index) links.appendChild(document.createTextNode(" · "));
      links.appendChild(part);
    });
    source.appendChild(links);
    node.appendChild(source);
    return node;
  }

  var EMPTY = {
    ontwikkellocatie: "Geen ontwikkellocaties met deze filters. Kijk ook onder Onzeker, of wis de filters.",
    onzeker: "Geen onzekere berichten met deze filters.",
  };

  function renderList() {
    var list = $("list");
    var main = sorted(ofClass(state.klasse).filter(matches));
    var removed = state.toonWeg ? sorted(ofClass("weggefilterd").filter(matches)) : [];
    list.textContent = "";
    $("result-count").textContent = main.length + " " + KLASSE_LABEL[state.klasse].toLowerCase() +
      (state.toonWeg ? " en " + removed.length + " weggefilterd" : "") + ", " +
      { relevantie: "meest relevant eerst", datum: "nieuwste eerst", afstand: "dichtstbij eerst" }[state.sort];

    if (!main.length) list.appendChild(el("p", "empty", EMPTY[state.klasse]));
    var shown = 0, perDay = countBy(main, "datum"), lastDay = null;
    main.slice(0, state.limit).forEach(function (item) {
      if (state.sort === "datum" && item.datum !== lastDay) {
        lastDay = item.datum;
        var head = el("h3", "day", dayLabel(item.datum));
        head.appendChild(el("span", null, String(perDay[item.datum])));
        list.appendChild(head);
      }
      list.appendChild(card(item));
      shown++;
    });
    if (state.toonWeg && shown === main.length) {
      var divider = el("h3", "day is-removed", "Weggefilterd");
      divider.appendChild(el("span", null, String(removed.length)));
      list.appendChild(divider);
      list.appendChild(el("p", "hint", "Deze berichten voldoen niet aan de regels voor een ontwikkellocatie. Bij elk bericht staat waarom."));
      removed.slice(0, state.limit - shown).forEach(function (item) { list.appendChild(card(item)); });
    }
    $("more").hidden = main.length + removed.length <= state.limit;

    ["ontwikkellocatie", "onzeker"].forEach(function (klasse) {
      $("klasse-" + klasse).querySelector("span").textContent = ofClass(klasse).length;
      $("klasse-" + klasse).setAttribute("aria-pressed", String(state.klasse === klasse));
    });
    $("weg-aantal").textContent = "(" + ofClass("weggefilterd").length + ")";
  }

  /* Small overview map: rings at 5, 10 and 15 km, one dot per development location. */
  function renderRadar() {
    var svg = $("radar"), ns = "http://www.w3.org/2000/svg", centre = state.data.centrum;
    function add(tag, attrs, text) {
      var node = document.createElementNS(ns, tag);
      Object.keys(attrs).forEach(function (key) { node.setAttribute(key, attrs[key]); });
      if (text) node.textContent = text;
      svg.appendChild(node);
      return node;
    }
    svg.textContent = "";
    [5, 10, 15].forEach(function (km) {
      add("circle", { cx: 0, cy: 0, r: km, "class": "ring" + (km === state.data.straalKm ? " ring-outer" : "") });
      add("text", { x: 0.3, y: -km + 1.2 }, km + " km");
    });
    add("text", { x: 0, y: -16.6, "text-anchor": "middle" }, "N");
    var located = state.data.berichten.filter(function (i) {
      return i.klasse !== "weggefilterd" && i.lat !== null && i.lat !== undefined;
    });
    located.sort(function (a, b) { return (a.klasse === "ontwikkellocatie") - (b.klasse === "ontwikkellocatie"); });
    located.forEach(function (item) {
      var o = offsetKm(item, centre);
      add("circle", { cx: o.x.toFixed(2), cy: (-o.y).toFixed(2), r: item.klasse === "onzeker" ? 0.32 : 0.42, "class": "p-" + item.klasse });
    });
    add("circle", { cx: 0, cy: 0, r: 0.35, "class": "centre" });
    state.area.gemeenten.forEach(function (gemeente) {
      var town = gemeente.woonplaatsen.filter(function (w) {
        var o = offsetKm(w, centre);
        return Math.hypot(o.x, o.y) <= state.data.straalKm - 1.5;
      })[0];
      if (!town) return;
      var o = offsetKm(town, centre);
      add("text", { x: o.x.toFixed(2), y: (-o.y).toFixed(2), "text-anchor": "middle", "class": "town" }, town.naam);
    });
  }

  function gemeenteKey(gemeente) { return gemeente.land === "BE" ? gemeente.naam + " (België)" : gemeente.naam; }

  function renderGebied() {
    var area = state.area, box = $("gemeenten");
    var counts = countBy(ofClass("ontwikkellocatie"), "gemeente"), unsure = countBy(ofClass("onzeker"), "gemeente");
    $("gebied-intro").textContent = "Alles binnen " + area.straalKm + " km hemelsbreed van " + area.centrum.naam +
      ". Daarin liggen " + area.gemeenten.length + " gemeenten, waarvan de meeste maar voor een deel. Een bericht telt mee als de locatie zelf binnen de straal valt.";
    renderRadar();
    box.textContent = "";
    area.gemeenten.forEach(function (gemeente) {
      var key = gemeenteKey(gemeente);
      var row = el("button", "gemeente");
      row.type = "button";
      row.appendChild(el("strong", null, gemeente.naam + (gemeente.land === "BE" ? " (België)" : "")));
      row.appendChild(el("span", "km", nf.format(gemeente.minKm) + " – " + nf.format(gemeente.maxKm) + " km"));
      var meta = el("span", "meta");
      meta.appendChild(el("span", "chip", gemeente.dekking === "geheel" ? "Geheel binnen de straal" : "Deels binnen de straal"));
      meta.appendChild(el("span", null, (counts[key] || 0) + " ontwikkellocaties, " + (unsure[key] || 0) + " onzeker"));
      row.appendChild(meta);
      var towns = gemeente.woonplaatsen.map(function (w) { return w.naam + (w.dekking === "geheel" ? "" : " (deels)"); });
      row.appendChild(el("span", "towns", towns.length ? "Plaatsen: " + towns.join(", ") : "Grensgebied bij Tilburg en Goirle; plaatsnamen zijn voor België niet uitgesplitst."));
      row.addEventListener("click", function () {
        resetFilters();
        state.gemeente = key;
        $("f-gemeente").value = key;
        showFilters(true);
        renderList();
        location.hash = "#berichten";
      });
      box.appendChild(row);
    });
  }

  function renderBronnen() {
    var on = $("bronnen-aan"), off = $("bronnen-uit");
    on.textContent = ""; off.textContent = "";
    state.data.bronnen.forEach(function (source) {
      var box = el("div", "bron"), head = el("div", "bron-head");
      head.appendChild(el("strong", null, source.naam));
      if (source.status === "ok") head.appendChild(el("span", "status is-ok", source.aantal + " berichten"));
      else if (source.status === "fout") head.appendChild(el("span", "status is-fout", "Niet bereikbaar"));
      else head.appendChild(el("span", "status", source.aangesloten ? "Hulpbron" : "Niet aangesloten"));
      box.appendChild(head);
      box.appendChild(el("p", "who", source.beheerder));
      box.appendChild(el("p", null, source.levert));
      box.appendChild(el("p", "access", source.toegang));
      if (source.status === "fout") box.appendChild(el("p", "access", "Bij de laatste verversing lukte het ophalen niet; berichten uit deze bron ontbreken tijdelijk."));
      var url = safeUrl(source.url);
      if (url) { var p = el("p"); p.appendChild(link(url, url.replace(/^https:\/\/(www\.)?/, "").replace(/\/$/, ""))); box.appendChild(p); }
      (source.aangesloten ? on : off).appendChild(box);
    });
    var windows = state.data.vensterDagen, limit = state.data.drempelPerceelM2;
    function fill(id, lines) {
      var box = $(id);
      box.textContent = "";
      lines.forEach(function (text) { box.appendChild(el("li", null, text)); });
    }
    fill("regels", [
      "Hoogste rang: een wijziging van een omgevingsplan of bestemmingsplan die ontwikkeling mogelijk maakt, bijvoorbeeld naar wonen of met meer bouwhoogte.",
      "Daarna: twee of meer nieuwe woningen. Hoe meer woningen, hoe hoger.",
      "Daarna: een perceel van minstens " + limit + " m² met een ontwikkelsignaal: sloop, functiewijziging, kavelsplitsing, bestemmingswijziging of een leegstaand of vrijkomend bedrijfspand.",
      "Ook: een overheid die grond of vastgoed van minstens " + limit + " m² wil verkopen, en een failliet bedrijf met een bedrijfspand op zo'n perceel.",
      "Onzeker: er is een signaal, maar het aantal woningen of de perceelgrootte is niet te bepalen. Deze berichten worden niet verborgen.",
      "Weggefilterd: al het andere, zoals dakkapellen, kappen, reclame en één losse woning. Met de schakelaar op het tabblad Berichten kun je ze bekijken; bij elk bericht staat de reden.",
      "Ingetrokken en geweigerde aanvragen blijven zichtbaar, maar zakken in de rangorde.",
    ]);
    fill("notes", [
      "Vergunningen blijven " + windows.vergunning + " dagen in de lijst, planberichten " + windows.plan + " dagen, verkoopvoornemens " + windows.verkoop + " dagen en faillissementen " + windows.faillissement + " dagen.",
      "Het aantal woningen en de signalen komen uit de titel en de eerste regels van de bekendmaking. De perceelgrootte komt uit het Kadaster, voor het perceel op de locatie van het bericht. Beslaat een project meer percelen, dan kan de werkelijke omvang groter zijn.",
      "Bij faillissementen gaat het alleen om rechtspersonen met een pand dat volgens de BAG geen woning is. Of het bedrijf eigenaar of huurder is, is niet bekend.",
      "Gemeenten publiceren op werkdagen rond 9 uur. Bovenaan staat het tijdstip van de laatste verversing.",
      "De afstand is hemelsbreed tot " + state.data.centrum.naam + ", gemeten naar het dichtstbijzijnde punt van de locatie in de bekendmaking.",
      "De stand (aanvraag, verleend, enzovoort) en de reden van relevantie zijn automatisch afgeleid. De bron zelf is altijd leidend.",
    ]);
  }

  function showView() {
    var name = location.hash.replace("#", "");
    if (VIEWS.indexOf(name) === -1) name = "berichten";
    VIEWS.forEach(function (view) {
      $("view-" + view).hidden = view !== name;
      if (view === name) $("tab-" + view).setAttribute("aria-current", "page");
      else $("tab-" + view).removeAttribute("aria-current");
    });
    window.scrollTo(0, 0);
  }

  function showFilters(open) {
    $("filters").hidden = !open;
    $("filter-toggle").setAttribute("aria-expanded", String(open));
  }

  function resetFilters() {
    state.zoek = ""; state.type = ""; state.gemeente = ""; state.fase = ""; state.signaal = ""; state.dagen = 0;
    state.sort = "relevantie"; state.maxKm = state.data.straalKm; state.alleenNieuw = false; state.limit = PAGE;
    $("zoek").value = ""; $("f-type").value = ""; $("f-gemeente").value = ""; $("f-fase").value = ""; $("f-signaal").value = "";
    $("f-dagen").value = "0"; $("f-sort").value = "relevantie"; $("f-nieuw").checked = false;
    $("f-km").value = state.maxKm; $("f-km-out").textContent = state.maxKm + " km";
  }

  function bind() {
    function onChange(id, key, convert) {
      $(id).addEventListener("input", function (event) {
        var target = event.target;
        state[key] = convert ? convert(target) : target.value;
        state.limit = PAGE;
        renderList();
      });
    }
    onChange("zoek", "zoek");
    onChange("f-type", "type");
    onChange("f-gemeente", "gemeente");
    onChange("f-fase", "fase");
    onChange("f-signaal", "signaal");
    onChange("f-sort", "sort");
    onChange("f-dagen", "dagen", function (t) { return +t.value; });
    onChange("f-nieuw", "alleenNieuw", function (t) { return t.checked; });
    onChange("toon-weg", "toonWeg", function (t) { return t.checked; });
    onChange("f-km", "maxKm", function (t) { $("f-km-out").textContent = t.value + " km"; return +t.value; });
    ["ontwikkellocatie", "onzeker"].forEach(function (klasse) {
      $("klasse-" + klasse).addEventListener("click", function () { state.klasse = klasse; state.limit = PAGE; renderList(); });
    });
    $("filter-toggle").addEventListener("click", function () { showFilters($("filters").hidden); });
    $("filter-reset").addEventListener("click", function () { resetFilters(); renderList(); });
    $("filters").addEventListener("submit", function (event) { event.preventDefault(); });
    $("more").addEventListener("click", function () { state.limit += PAGE; renderList(); });
    window.addEventListener("hashchange", showView);
  }

  function start(data, area) {
    state.data = data; state.area = area;
    state.maxKm = data.straalKm;
    state.latestDay = data.berichten.length ? data.berichten.reduce(function (a, b) { return a.datum > b.datum ? a : b; }).datum : "";
    state.nieuw = markNew(data.berichten);
    state.toonWeg = $("toon-weg").checked;
    $("scope").textContent = "Ontwikkellocaties binnen " + data.straalKm + " km van " + data.centrum.naam;
    $("updated").textContent = "Bijgewerkt " + stampFormat.format(new Date(data.bijgewerkt));
    $("f-km").max = data.straalKm; $("f-km").value = data.straalKm; $("f-km-out").textContent = data.straalKm + " km";
    var relevant = data.berichten.filter(function (item) { return item.klasse !== "weggefilterd"; });
    fillSelect($("f-type"), countBy(relevant, "type"), TYPE_LABEL);
    fillSelect($("f-gemeente"), countBy(relevant, "gemeente"));
    fillSelect($("f-fase"), countBy(relevant, "fase"));
    fillSelect($("f-signaal"), countBy(relevant, "signalen"));
    bind();
    renderSummary(); renderList(); renderGebied(); renderBronnen(); showView();
  }

  function fetchJson(path) {
    return fetch(path, { cache: "no-cache" }).then(function (response) {
      if (!response.ok) throw new Error(path + ": " + response.status);
      return response.json();
    });
  }

  Promise.all([fetchJson("data/berichten.json"), fetchJson("data/gebied.json")]).then(function (results) {
    start(results[0], results[1]);
  }).catch(function () {
    var box = $("load-error");
    box.textContent = "De berichten konden niet worden geladen. Controleer je verbinding en open de app opnieuw.";
    box.hidden = false;
  });

  try {
    if ("serviceWorker" in navigator && location.protocol === "https:") {
      navigator.serviceWorker.register("sw.js").catch(function () { /* the app works without it */ });
    }
  } catch (e) { /* embedded previews may block service workers */ }
})();
