/* Tilburg Signalen: reads data/berichten.json and data/gebied.json and renders three views.
   What to show is decided in logic.js; this file only builds the page from it. The fourth view,
   "adres", is built by adres-app.js; this file only switches to it. */
(function () {
  "use strict";

  var L = window.TilburgSignalen;
  var REMOVED_PAGE = 60;
  var STORE_KEY = "tilburg-signalen.gezien";
  var VIEWS = ["berichten", "gebied", "bronnen", "adres"];
  var LISTS = ["ranglijst", "nieuw", "onzeker"];
  var state = {
    data: null, area: null, kern: [], regios: [], regioBerichten: {}, regioFout: "", kmMax: 15, view: "ranglijst", expanded: false, toonWeg: false, removedLimit: REMOVED_PAGE,
    zoek: "", type: "", gemeente: "", fase: "", signaal: "", dagen: 0, sort: "relevantie", maxKm: 15,
    nieuw: {}, ranks: {}, firstVisit: false, latestDay: "",
  };

  function $(id) { return document.getElementById(id); }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function link(url, text) {
    var a = el("a", null, text);
    a.href = url; a.target = "_blank"; a.rel = "noopener";
    return a;
  }

  var nf = new Intl.NumberFormat("nl-NL", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  var dayFormat = new Intl.DateTimeFormat("nl-NL", { weekday: "long", day: "numeric", month: "long" });
  var stampFormat = new Intl.DateTimeFormat("nl-NL", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

  function parseDay(iso) { var p = iso.split("-"); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function dayLabel(iso) {
    var label = dayFormat.format(parseDay(iso)), today = new Date();
    if (iso === L.isoDay(today)) return "Vandaag, " + label;
    if (iso === L.daysAgoIso(1, today)) return "Gisteren, " + label;
    return label.charAt(0).toUpperCase() + label.slice(1);
  }

  function context() {
    var today = new Date();
    return { centre: state.data.centrum, nieuw: state.nieuw, ranks: state.ranks, latestDay: state.latestDay, today: today };
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
    while (select.options.length > 1) select.remove(1); // the first option is "all"
    Object.keys(counts).sort(function (a, b) { return a.localeCompare(b, "nl"); }).forEach(function (value) {
      var option = el("option", null, ((labels && labels[value]) || value) + " (" + counts[value] + ")");
      option.value = value;
      select.appendChild(option);
    });
  }

  /* The morning line: greeting and date, how many locations are new, and the three lists. */
  function renderBrief() {
    var now = new Date(), counts = L.counts(state.data.berichten, state.nieuw);
    $("brief-day").textContent = L.greeting(now.getHours()) + " · " + dayFormat.format(now);
    $("brief-title").textContent = L.briefing(counts.nieuw, state.firstVisit);
    $("brief-sub").textContent = (L.alsoNewLine(counts.onzekerNieuw) + " Laatste publicatiedag: " +
      (state.latestDay ? dayLabel(state.latestDay).toLowerCase() : "nog geen berichten") + ".").trim();
    $("tile-ranglijst").querySelector("b").textContent = counts.locaties;
    $("tile-nieuw").querySelector("b").textContent = counts.nieuw;
    $("tile-onzeker").querySelector("b").textContent = counts.onzeker;
    var badge = $("onzeker-nieuw");
    badge.hidden = !counts.onzekerNieuw;
    badge.textContent = "+" + counts.onzekerNieuw;
    badge.appendChild(el("span", "sr", " nieuw"));
    $("weg-aantal").textContent = "(" + counts.weggefilterd + ")";

    var box = $("notices");
    box.textContent = "";
    notices().forEach(function (text) { box.appendChild(el("p", "stale", text)); });

    // Only when a region was chosen on the area tab: say so here, with the way back to the core.
    var line = $("regio-regel");
    line.textContent = "";
    line.hidden = !state.regios.length;
    if (state.regios.length) {
      line.appendChild(el("span", null, "Met " + L.nameList(state.regios) + " erbij. "));
      var back = el("button", "ghost", "Alleen de kern");
      back.type = "button";
      back.addEventListener("click", function () { setRegios([]); });
      line.appendChild(back);
    }
  }

  /* Messages about gaps in the data: days the source delivered incompletely, and a refresh that is overdue. */
  function notices() {
    var lines = [], gaps = state.data.onvolledigeDagen || [];
    gaps.forEach(function (gap) {
      lines.push("De gegevens van " + dayFormat.format(parseDay(gap.datum)) + " zijn onvolledig: de bron gaf " + gap.aantal +
        " van de gebruikelijke circa " + gap.verwacht.toLocaleString("nl-NL") + " publicaties door. " +
        "De app haalt die dag bij elke volgende verversing opnieuw op.");
    });
    (state.data.bronnen || []).forEach(function (source) {
      if (source.status === "fout") {
        lines.push("De bron " + source.naam + " was bij de laatste verversing niet bereikbaar. " +
          "Berichten uit die bron ontbreken tot een volgende verversing lukt.");
      }
    });
    var failed = state.data.ophaalfouten || {}, missing = (failed.tekst || 0) + (failed.perceel || 0);
    if (missing) {
      lines.push("Bij de laatste verversing konden " + missing + " bekendmakingen niet volledig worden gelezen. " +
        "Ze staan tijdelijk onder Onzeker; de volgende verversing probeert het opnieuw.");
    }
    // A chosen region reports what it still misses itself; without a region these lines are not there.
    L.regioMeldingen(state.data.regios, state.regios).forEach(function (line) { lines.push(line); });
    if (failed.insolventie) {
      lines.push("Bij de laatste verversing konden " + failed.insolventie + " rechtbankpublicaties over faillissementen niet worden gelezen. " +
        "De volgende verversing probeert het opnieuw.");
    }
    var hours = (Date.now() - new Date(state.data.bijgewerkt).getTime()) / 3600000;
    if (hours > 26) {
      lines.push("De gegevens zijn sinds " + stampFormat.format(new Date(state.data.bijgewerkt)) +
        " niet ververst. Mogelijk heeft de bron een storing; zodra die voorbij is, worden de gemiste dagen alsnog opgehaald.");
    }
    return lines;
  }

  /* One notice. Reading order: place in the ranking, the sentence why, then what and where. */
  function card(item, ctx) {
    var model = L.cardModel(item, { centre: ctx.centre, nieuw: ctx.nieuw, ranks: ctx.ranks, today: L.isoDay(ctx.today) });
    var node = el("article", "card is-" + model.klasse + (model.isNew ? " is-new" : ""));
    node.setAttribute("data-id", model.id);

    var rank = el("div", "rank");
    if (model.rank) {
      rank.appendChild(el("b", null, String(model.rank)));
      rank.title = "Plaats " + model.rank + " in de rangorde" + (model.score !== null ? ", relevantie " + model.score : "");
      rank.setAttribute("aria-label", "Rang " + model.rank);
    } else {
      rank.appendChild(el("b", null, "–"));
      rank.setAttribute("aria-label", "Weggefilterd");
    }
    node.appendChild(rank);

    var main = el("div", "card-main");
    main.appendChild(el("p", "why", model.why));
    main.appendChild(el("h3", "card-title", model.title));

    var meta = el("p", "meta");
    meta.appendChild(el("span", "place", model.place));
    meta.appendChild(document.createTextNode(" "));
    meta.appendChild(el("span", "dist", model.distance));
    meta.appendChild(document.createTextNode(" "));
    meta.appendChild(el("span", "date", model.date));
    main.appendChild(meta);

    var more = el("details", "details"), summary = el("summary"), tags = el("span", "tags"), body = el("div", "details-body");
    if (model.isNew) tags.appendChild(el("span", "chip is-new", "Nieuw"));
    tags.appendChild(el("span", "chip is-" + model.type, model.kind));
    tags.appendChild(el("span", "chip", model.fase));
    if (model.deadline) tags.appendChild(el("span", "chip is-deadline", model.deadline));
    summary.appendChild(tags);
    summary.appendChild(el("span", "toggle", "Details"));
    more.appendChild(summary);
    if (model.description) body.appendChild(el("p", "desc", model.description));
    if (model.activities) body.appendChild(el("p", null, "Activiteiten: " + model.activities));
    if (model.locationNote) body.appendChild(el("p", null, model.locationNote));
    if (model.score !== null) body.appendChild(el("p", "data", "Relevantie " + model.score + " · rang " + model.rank));
    body.appendChild(el("p", "source", model.source + " · " + model.date));
    var links = el("p", "links");
    model.links.forEach(function (entry) { links.appendChild(link(entry.url, entry.label)); });
    body.appendChild(links);
    more.appendChild(body);
    main.appendChild(more);

    node.appendChild(main);
    return node;
  }

  var TITLES = { ranglijst: "Ranglijst", nieuw: "Nieuw", onzeker: "Onzeker" };
  var NOUNS = {
    ranglijst: ["ontwikkellocatie", "ontwikkellocaties"],
    nieuw: ["nieuwe ontwikkellocatie", "nieuwe ontwikkellocaties"],
    onzeker: ["onzeker bericht", "onzekere berichten"],
  };
  var ORDER = { relevantie: "hoogste rang eerst", datum: "nieuwste eerst", afstand: "dichtstbij eerst" };

  /* How many settings in the filter panel differ from the default; the search box is separate. */
  function filtersActive() {
    return ["type", "gemeente", "fase", "signaal", "dagen"].filter(function (key) { return state[key]; }).length +
      (state.maxKm < state.kmMax ? 1 : 0) + (state.sort !== "relevantie" ? 1 : 0);
  }
  /* Whether search or a filter leaves notices out (the order alone does not). */
  function narrowed() { return !!state.zoek || filtersActive() - (state.sort !== "relevantie" ? 1 : 0) > 0; }

  function emptyState() {
    var box = el("div", "empty"), filtered = narrowed();
    if (state.view === "nieuw" && !filtered) {
      var art = el("div", "empty-art");
      ["ochtend.svg", "ochtend-donker.svg"].forEach(function (file, index) {
        var img = el("img", index ? "only-dark" : "only-light");
        img.src = "img/" + file; img.alt = ""; img.width = 512; img.height = 190;
        art.appendChild(img);
      });
      box.appendChild(art);
      box.appendChild(el("p", "empty-title", state.firstVisit ? "Geen ontwikkellocaties op de laatste publicatiedag." : "Niets nieuws sinds je vorige bezoek."));
      if (!state.firstVisit) box.appendChild(el("p", null, "De ranglijst is ongewijzigd."));
      var back = el("button", "ghost", "Bekijk de ranglijst");
      back.type = "button";
      back.addEventListener("click", function () { setView("ranglijst"); });
      box.appendChild(back);
      return box;
    }
    box.appendChild(el("p", null, filtered ? {
      ranglijst: "Geen ontwikkellocaties met deze filters. Kijk ook onder Onzeker, of wis de filters.",
      nieuw: "Geen nieuwe ontwikkellocaties met deze filters.",
      onzeker: "Geen onzekere berichten met deze filters.",
    }[state.view] : {
      ranglijst: "Er zijn op dit moment geen ontwikkellocaties. Kijk ook onder Onzeker.",
      onzeker: "Er zijn op dit moment geen onzekere berichten.",
    }[state.view]));
    return box;
  }

  function renderList() {
    var ctx = context(), selection = L.select(state.data.berichten, state, ctx);
    var main = selection.main, removed = selection.removed, alsoNew = selection.alsoNew;
    var open = {};
    [].forEach.call(document.querySelectorAll("#view-berichten .card:has(details[open])"), function (node) { open[node.getAttribute("data-id")] = true; });
    var shown = state.expanded ? main : main.slice(0, L.TOP);
    var noun = NOUNS[state.view][main.length === 1 ? 0 : 1];
    var list = $("list");
    list.textContent = "";

    $("list-title").textContent = TITLES[state.view];
    $("result-count").textContent = (shown.length < main.length
      ? (state.sort === "relevantie" ? "Top " : "") + shown.length + " van " + main.length + " " + noun
      : main.length + " " + noun) + ", " + ORDER[state.sort];

    if (!main.length && !alsoNew.length) list.appendChild(emptyState());
    var perDay = countBy(main, "datum"), perDayShown = countBy(shown, "datum"), lastDay = null;
    shown.forEach(function (item) {
      if (state.sort === "datum" && item.datum !== lastDay) {
        lastDay = item.datum;
        var head = el("p", "day", dayLabel(item.datum));
        var gap = (state.data.onvolledigeDagen || []).some(function (g) { return g.datum === item.datum; });
        var total = perDay[item.datum], visible = perDayShown[item.datum];
        head.appendChild(el("span", null, (visible < total ? visible + " van " + total : total) + (gap ? " · onvolledig" : "")));
        list.appendChild(head);
      }
      list.appendChild(card(item, ctx));
    });
    if (alsoNew.length && shown.length === main.length) {
      var also = el("p", "day", "Nieuw onder Onzeker");
      also.appendChild(el("span", null, String(alsoNew.length)));
      list.appendChild(also);
      alsoNew.forEach(function (item) { list.appendChild(card(item, ctx)); });
    }
    $("more").hidden = shown.length === main.length;
    $("more").textContent = "Toon alle " + main.length + " " + noun;

    var box = $("removed");
    box.textContent = "";
    box.hidden = !state.toonWeg;
    if (state.toonWeg) {
      var divider = el("p", "day is-removed", "Weggefilterd");
      divider.appendChild(el("span", null, String(removed.length)));
      box.appendChild(divider);
      box.appendChild(el("p", "hint", "Deze berichten voldoen niet aan de regels voor een ontwikkellocatie. Bij elk bericht staat waarom."));
      removed.slice(0, state.removedLimit).forEach(function (item) { box.appendChild(card(item, ctx)); });
    }
    $("more-removed").hidden = !state.toonWeg || removed.length <= state.removedLimit;

    [].forEach.call(document.querySelectorAll("#view-berichten .card"), function (node) {
      if (open[node.getAttribute("data-id")]) node.querySelector("details").open = true;
    });
    LISTS.forEach(function (view) { $("tile-" + view).setAttribute("aria-pressed", String(state.view === view)); });
    var active = filtersActive();
    $("filter-toggle").textContent = "Filters" + (active ? " · " + active : "");
  }

  function setView(view) {
    state.view = view; state.expanded = false; state.removedLimit = REMOVED_PAGE;
    renderList();
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
    // The map is the core: a region lies far outside its rings.
    var located = state.kern.filter(function (i) { return i.klasse !== "weggefilterd" && L.hasPoint(i); });
    located.sort(function (a, b) { return (a.klasse === "ontwikkellocatie") - (b.klasse === "ontwikkellocatie"); });
    located.forEach(function (item) {
      var o = L.offsetKm(item, centre);
      add("circle", { cx: o.x.toFixed(2), cy: (-o.y).toFixed(2), r: item.klasse === "onzeker" ? 0.32 : 0.42, "class": "p-" + item.klasse });
    });
    add("circle", { cx: 0, cy: 0, r: 0.35, "class": "centre" });
    state.area.gemeenten.forEach(function (gemeente) {
      var town = gemeente.woonplaatsen.filter(function (w) {
        var o = L.offsetKm(w, centre);
        return Math.hypot(o.x, o.y) <= state.data.straalKm - 1.5;
      })[0];
      if (!town) return;
      var o = L.offsetKm(town, centre);
      add("text", { x: o.x.toFixed(2), y: (-o.y).toFixed(2), "text-anchor": "middle", "class": "town" }, town.naam);
    });
  }

  function gemeenteKey(gemeente) { return gemeente.land === "BE" ? gemeente.naam + " (België)" : gemeente.naam; }

  /* The regions that can be shown with the core. Nothing is chosen when the app opens. */
  function renderRegios() {
    var box = $("regios"), found = L.regios(state.area, state.data.regios), note = $("regio-uitleg");
    box.textContent = "";
    box.hidden = !found.length;
    note.hidden = !found.length;
    found.forEach(function (regio) {
      var chosen = state.regios.indexOf(regio.naam) !== -1;
      var button = el("button", "regio", regio.naam);
      button.type = "button";
      button.setAttribute("aria-pressed", String(chosen));
      button.appendChild(el("span", null, regio.locaties + (regio.locaties === 1 ? " locatie" : " locaties") +
        (regio.ongelezen ? " · " + regio.ongelezen + " ongelezen" : "")));
      button.addEventListener("click", function () {
        setRegios(chosen ? state.regios.filter(function (name) { return name !== regio.naam; }) : state.regios.concat(regio.naam));
      });
      box.appendChild(button);
    });
    note.className = state.regioFout ? "stale" : "hint";
    note.textContent = state.regioFout || (state.regios.length
      ? "Je ziet de kern met " + L.nameList(state.regios) + " erbij, ook op het tabblad Berichten. Het kaartje toont alleen de kern. Bij een volgend bezoek staat de app weer op de kern."
      : "Kies een regio om die erbij te zien. De app opent altijd met alleen de kern: alles binnen " + state.area.straalKm + " km.");
  }

  function renderGebied() {
    var area = state.area, box = $("gemeenten"), core = L.gemeentenIn(area, []);
    var counts = countBy(ofClass("ontwikkellocatie"), "gemeente"), unsure = countBy(ofClass("onzeker"), "gemeente");
    $("gebied-intro").textContent = "Alles binnen " + area.straalKm + " km hemelsbreed van " + area.centrum.naam +
      ". Daarin liggen " + core.length + " gemeenten, waarvan de meeste maar voor een deel. Een bericht telt mee als de locatie zelf binnen de straal valt.";
    renderRegios();
    renderRadar();
    box.textContent = "";
    L.gemeentenIn(area, state.regios).forEach(function (gemeente) {
      var key = gemeenteKey(gemeente), outside = L.regioOf(gemeente) !== L.KERN;
      var whole = !outside && gemeente.dekking !== "geheel" && state.regios.indexOf(gemeente.buitenStraal) !== -1;
      var row = el("button", "gemeente");
      row.type = "button";
      row.appendChild(el("strong", null, gemeente.naam + (gemeente.land === "BE" ? " (België)" : "")));
      row.appendChild(el("span", "km", nf.format(gemeente.minKm) + " – " + nf.format(gemeente.maxKm) + " km"));
      var meta = el("span", "meta");
      meta.appendChild(el("span", "chip", outside ? gemeente.regio : whole ? "Hele gemeente, met " + gemeente.buitenStraal
        : gemeente.dekking === "geheel" ? "Geheel binnen de straal" : "Deels binnen de straal"));
      meta.appendChild(el("span", null, (counts[key] || 0) + " ontwikkellocaties, " + (unsure[key] || 0) + " onzeker"));
      row.appendChild(meta);
      var towns = gemeente.woonplaatsen.map(function (w) { return w.naam + (w.dekking === "geheel" ? "" : " (deels)"); });
      row.appendChild(el("span", "towns", outside ? "Hele gemeente, buiten de straal." + (gemeente.opmerking ? " " + gemeente.opmerking : "")
        : towns.length ? "Plaatsen: " + towns.join(", ") : "Grensgebied bij Tilburg en Goirle; plaatsnamen zijn voor België niet uitgesplitst."));
      row.addEventListener("click", function () {
        resetFilters();
        state.gemeente = key;
        $("f-gemeente").value = key;
        showFilters(true);
        state.view = "ranglijst"; state.expanded = true;
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
      var url = L.safeUrl(source.url);
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
    state.sort = "relevantie"; state.maxKm = state.kmMax;
    state.expanded = false; state.removedLimit = REMOVED_PAGE;
    $("zoek").value = ""; $("f-type").value = ""; $("f-gemeente").value = ""; $("f-fase").value = ""; $("f-signaal").value = "";
    $("f-dagen").value = "0"; $("f-sort").value = "relevantie";
    $("f-km").max = state.kmMax; $("f-km").value = state.maxKm; $("f-km-out").textContent = state.maxKm + " km";
  }

  /* The choices in the filter panel follow the notices that are shown. */
  function fillFilters() {
    var relevant = state.data.berichten.filter(function (item) { return item.klasse !== "weggefilterd"; });
    fillSelect($("f-type"), countBy(relevant, "type"), L.TYPE_LABEL);
    fillSelect($("f-gemeente"), countBy(relevant, "gemeente"));
    fillSelect($("f-fase"), countBy(relevant, "fase"));
    fillSelect($("f-signaal"), countBy(relevant, "signalen"));
  }

  /* The notices of one region, read once from its own file. */
  function loadRegio(name) {
    if (state.regioBerichten[name]) return Promise.resolve(state.regioBerichten[name]);
    var regio = L.regios(state.area, state.data.regios).filter(function (entry) { return entry.naam === name; })[0];
    if (!regio || !/^regio-[a-z-]+\.json$/.test(regio.bestand)) return Promise.reject(new Error("onbekende regio"));
    return fetchJson("data/" + regio.bestand).then(function (file) {
      state.regioBerichten[name] = file.berichten || [];
      return state.regioBerichten[name];
    });
  }

  /* Show the core with the chosen regions. The ranking counts over what is shown; "new" stays a
     matter of the core, so a region never fills the morning line. Nothing is remembered: the app
     opens with the core. A region whose file does not come is not chosen, and the tab says so. */
  function setRegios(chosen) {
    return Promise.all(chosen.map(function (name) {
      return loadRegio(name).then(function (items) { return { name: name, items: items }; }, function () { return { name: name, items: null }; });
    })).then(function (loaded) {
      var missing = loaded.filter(function (entry) { return !entry.items; }).map(function (entry) { return entry.name; });
      var shown = loaded.filter(function (entry) { return entry.items; });
      state.regioFout = missing.length ? "De berichten van " + L.nameList(missing) + " konden niet worden geladen. Controleer je verbinding en kies de regio opnieuw." : "";
      state.regios = shown.map(function (entry) { return entry.name; });
      state.data.berichten = L.merged(state.kern, shown.map(function (entry) { return entry.items; }));
      state.ranks = L.rankMap(state.data.berichten);
      state.kmMax = L.reachKm(state.data.berichten, state.data.straalKm);
      resetFilters();
      fillFilters();
      renderBrief(); renderList(); renderGebied();
    });
  }

  function bind() {
    function onChange(id, key, convert) {
      $(id).addEventListener("input", function (event) {
        var target = event.target;
        state[key] = convert ? convert(target) : target.value;
        state.expanded = false; state.removedLimit = REMOVED_PAGE;
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
    onChange("toon-weg", "toonWeg", function (t) { return t.checked; });
    onChange("f-km", "maxKm", function (t) { $("f-km-out").textContent = t.value + " km"; return +t.value; });
    LISTS.forEach(function (view) {
      $("tile-" + view).addEventListener("click", function () { setView(view); });
    });
    $("brand").addEventListener("click", function () { setView("ranglijst"); });
    $("filter-toggle").addEventListener("click", function () { showFilters($("filters").hidden); });
    $("filter-reset").addEventListener("click", function () { resetFilters(); renderList(); });
    $("filters").addEventListener("submit", function (event) { event.preventDefault(); });
    $("more").addEventListener("click", function () { state.expanded = true; renderList(); });
    $("more-removed").addEventListener("click", function () { state.removedLimit += REMOVED_PAGE; renderList(); });
    window.addEventListener("hashchange", showView);
  }

  /* Remember per device when each item was first seen; storage is optional. */
  function rememberSeen(items) {
    var seen = null;
    try { seen = JSON.parse(localStorage.getItem(STORE_KEY)); } catch (e) { seen = null; }
    var result = L.markNew(items, seen, Date.now());
    try { localStorage.setItem(STORE_KEY, JSON.stringify(result.next)); } catch (e) { /* storage is optional */ }
    return result;
  }

  function start(data, area) {
    state.data = data; state.area = area;
    state.kern = data.berichten; // the app opens with the core; a region is read when it is chosen
    // The address tab searches these notices and, for an address outside the core, those of its
    // region. It never changes them.
    window.TilburgSignalenGegevens = { bijgewerkt: data.bijgewerkt, vensterDagen: data.vensterDagen, centrum: data.centrum, berichten: state.kern };
    window.TilburgSignalenRegios = {
      voorGemeente: function (gemeente) {
        var names = L.regios(area, data.regios).map(function (regio) { return regio.naam; });
        names = L.regiosFor(area, gemeente).filter(function (name) { return names.indexOf(name) !== -1; });
        return Promise.all(names.map(loadRegio)).then(function (lists) {
          return { regios: names, berichten: lists.reduce(function (all, list) { return all.concat(list); }, []) };
        });
      },
    };
    state.kmMax = state.maxKm = data.straalKm;
    state.latestDay = L.latestDay(data.berichten);
    state.ranks = L.rankMap(data.berichten);
    var seen = rememberSeen(data.berichten);
    state.nieuw = seen.nieuw; state.firstVisit = seen.firstVisit;
    state.toonWeg = $("toon-weg").checked;
    $("scope").textContent = "Binnen " + data.straalKm + " km van " + data.centrum.naam;
    $("updated").textContent = "Bijgewerkt " + stampFormat.format(new Date(data.bijgewerkt));
    $("f-km").max = data.straalKm; $("f-km").value = data.straalKm; $("f-km-out").textContent = data.straalKm + " km";
    fillFilters();
    bind();
    renderBrief(); renderList(); renderGebied(); renderBronnen(); showView();
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
