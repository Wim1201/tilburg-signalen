/* Tilburg Signalen, tab "Adres": the page. Asks the open registers of the Kadaster (through PDOK)
   straight from the browser, without a key, and searches the notices the app already loaded.
   What to ask and what the answers mean is decided in adres.js; this file builds the page from it.
   Every part loads on its own: a register that does not answer leaves a message in its own box. */
(function () {
  "use strict";

  var A = window.TilburgAdres;
  var TIMEOUT = 12000;  // ms before a register counts as not answering
  var WAIT = 250;       // ms of silence at the keyboard before the address search is asked
  var MIN = 3;          // characters before the first suggestion
  var CENTRE = { lat: 51.55717769, lon: 5.0910001 }; // until the data file gives the centre
  var typed = 0, chosen = 0, timer = null, shown = [];
  // What is known about the chosen address so far; the notices are drawn again as more comes in.
  var current = { address: null, parcels: [], withParcel: false, regios: [], extra: [], regioFout: false };

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

  function svg(tag, attrs) {
    var node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.keys(attrs).forEach(function (key) { node.setAttribute(key, attrs[key]); });
    return node;
  }

  /* A plain GET to an open register; `read` turns the response into what is wanted. A register
     that does not answer within TIMEOUT counts as not answering. */
  function get(url, read) {
    var controller = typeof AbortController === "function" ? new AbortController() : null;
    var clock = setTimeout(function () { if (controller) controller.abort(); }, TIMEOUT);
    function done() { clearTimeout(clock); }
    return fetch(url, controller ? { signal: controller.signal } : {}).then(read).then(function (data) { done(); return data; }, function (error) { done(); throw error; });
  }

  function getJson(url) {
    return get(url, function (response) {
      if (!response.ok) throw new Error(String(response.status));
      return response.json();
    });
  }

  /* The answer as text with its status; status 0 when no answer came. Never fails. */
  function getText(url) {
    return get(url, function (response) {
      return response.text().then(function (text) { return { status: response.status, text: text }; });
    }).catch(function () { return { status: 0, text: "" }; });
  }

  function data() { return window.TilburgSignalenGegevens || null; }

  function message(text) {
    var box = $("adres-melding");
    box.textContent = text || "";
    box.hidden = !text;
  }

  /* A box whose register did not answer: say which one, and offer to try again. */
  function failed(box, text, retry) {
    box.textContent = "";
    box.appendChild(el("p", "stale", text));
    var again = el("button", "ghost", "Opnieuw proberen");
    again.type = "button";
    again.addEventListener("click", retry);
    box.appendChild(again);
  }

  function busy(box, text) {
    box.textContent = "";
    box.appendChild(el("p", "bezig", text));
  }

  function facts(rows) {
    var list = el("dl", "feiten");
    rows.forEach(function (row) {
      list.appendChild(el("dt", null, row.label));
      list.appendChild(el("dd", row.value ? null : "is-leeg", row.value || "niet bekend"));
    });
    return list;
  }

  /* ---------- Searching ---------- */

  function hideSuggestions() {
    var box = $("adres-suggesties");
    box.textContent = "";
    box.hidden = true;
    shown = [];
  }

  function showSuggestions(found) {
    var box = $("adres-suggesties");
    box.textContent = "";
    shown = found;
    if (!found.length) box.appendChild(el("p", "leeg", "Geen adres gevonden. Typ straat, huisnummer en plaats."));
    found.forEach(function (address) {
      var option = el("button", "suggestie", address.label);
      option.type = "button";
      option.addEventListener("click", function () { choose(address); });
      box.appendChild(option);
    });
    box.hidden = false;
  }

  function suggest() {
    var text = $("adres-zoek").value.trim(), mine = ++typed;
    if (text.length < MIN) { hideSuggestions(); message(""); return; }
    var loaded = data();
    getJson(A.suggestUrl(text, (loaded && loaded.centrum) || CENTRE)).then(function (response) {
      if (mine !== typed) return; // an answer to what was typed earlier
      message("");
      showSuggestions(A.addresses(response));
    }).catch(function () {
      if (mine !== typed) return;
      hideSuggestions();
      message("De adreszoeker (PDOK Locatieserver) antwoordt niet. Controleer je verbinding of probeer het later opnieuw.");
    });
  }

  /* ---------- One address ---------- */

  function renderBag(box, model) {
    box.textContent = "";
    if (!model) {
      box.appendChild(el("p", null, "Bij dit adres staat geen verblijfsobject in de BAG, bijvoorbeeld omdat het een standplaats of ligplaats is. Bouwjaar, gebruiksdoel en oppervlakte zijn er dan niet."));
      return;
    }
    box.appendChild(facts(model.rows));
    if (model.pandMissing) box.appendChild(el("p", "stale", "Het pand zelf kon niet worden opgehaald; bouwjaar en pandstatus ontbreken daardoor."));
    if (model.panden > 1) box.appendChild(el("p", "bronregel", "Dit adres ligt in " + model.panden + " panden; bouwjaar en status gelden voor die panden samen."));
    if (model.objectStatus) box.appendChild(el("p", "bronregel", "Status van het adres zelf: " + model.objectStatus.toLowerCase() + "."));
    box.appendChild(el("p", "bronregel", "Bron: Basisregistratie Adressen en Gebouwen (Kadaster, via PDOK). De oppervlakte is de gebruiksoppervlakte van het adres, niet van het perceel."));
  }

  function loadBag(address, mine) {
    var box = $("adres-bag");
    if (!address.objectId) { renderBag(box, null); return; }
    busy(box, "De BAG wordt geraadpleegd…");
    getJson(A.vboUrl(address.objectId)).then(function (response) {
      var vbo = (response.features || [])[0] || null;
      // The address object is the main answer; a building that does not come leaves a gap, not an error.
      return Promise.all(A.pandUrls(vbo).map(function (url) { return getJson(url).catch(function () { return null; }); }))
        .then(function (panden) { return A.bagModel(vbo, panden); });
    }).then(function (model) {
      if (mine === chosen) renderBag(box, model);
    }).catch(function () {
      if (mine !== chosen) return;
      failed(box, "De BAG (Kadaster, via PDOK) antwoordt niet. Bouwjaar, gebruiksdoel, oppervlakte en pandstatus ontbreken daardoor.",
        function () { loadBag(address, mine); });
    });
  }

  function renderMap(model) {
    var figure = el("figure", "perceelkaart"), frame = el("div", "kaartvlak");
    var image = el("img");
    image.alt = ""; image.decoding = "async"; image.width = 640; image.height = 640;
    // Without the background the outline of the parcel is still drawn.
    image.addEventListener("error", function () {
      image.remove();
      figure.appendChild(el("p", "bronregel", "De achtergrondkaart kon niet worden geladen; alleen de omtrek van het perceel is getekend."));
    });
    image.src = model.image;
    frame.appendChild(image);
    var drawing = svg("svg", { viewBox: "0 0 1000 1000", role: "img", "aria-label": "Kaartje met de ligging van het perceel. Noord is boven." });
    model.paths.forEach(function (path) { drawing.appendChild(svg("path", { d: path, "class": "p-perceel", "fill-rule": "evenodd" })); });
    if (model.point) drawing.appendChild(svg("circle", { cx: model.point.x, cy: model.point.y, r: 11, "class": "p-adres" }));
    frame.appendChild(drawing);
    var bar = el("span", "schaal", model.bar.metres + " m");
    bar.style.width = (model.bar.share * 100).toFixed(2) + "%";
    frame.appendChild(bar);
    figure.appendChild(frame);
    var caption = el("figcaption", "bronregel");
    caption.appendChild(el("span", "dot dot-perceel"));
    caption.appendChild(document.createTextNode(" perceel "));
    caption.appendChild(el("span", "dot dot-adres"));
    caption.appendChild(document.createTextNode(" adres. Noord is boven."));
    figure.appendChild(caption);
    return figure;
  }

  function renderParcels(box, address, found, linked) {
    box.textContent = "";
    if (!found.length) {
      box.appendChild(el("p", null, "Bij dit adres is geen kadastraal perceel gevonden."));
      return;
    }
    found.forEach(function (parcel) {
      box.appendChild(facts([
        { label: "Aanduiding", value: parcel.aanduiding + (parcel.code ? " (" + parcel.code + ")" : "") },
        { label: "Grootte", value: parcel.grootteTekst ? parcel.grootteTekst + (parcel.soortGrootte ? ", " + parcel.soortGrootte.toLowerCase() : "") : null },
      ]));
    });
    box.appendChild(el("p", "stale", "Let op: de kadastrale kaart geeft alleen een indicatie van de ligging en de grootte. Er zijn geen maten aan te ontlenen."));
    if (found.length > 1) box.appendChild(el("p", "bronregel", "Dit adres is aan " + found.length + " percelen gekoppeld."));
    if (!linked) {
      box.appendChild(el("p", address.punt ? "stale" : "bronregel", address.punt
        ? "Dit is het perceel op het punt uit de bekendmaking. Dat punt is omgerekend en kan enkele meters afwijken; bij een groot gebied is het het deel het dichtst bij Tilburg-centrum."
        : "Het adres is in de bron niet aan een perceel gekoppeld; dit is het perceel op de plek van het adrespunt."));
    }
    var map = A.mapModel(found, address);
    if (map) {
      box.appendChild(renderMap(map));
      if (map.osm) { var links = el("p", "links"); links.appendChild(link(map.osm, "Open op een gewone kaart")); box.appendChild(links); }
    }
    box.appendChild(el("p", "bronregel", "Bron: Basisregistratie Kadaster, kadastrale kaart (Kadaster, via PDOK). Bij een appartement is dit het grondperceel van het gebouw."));
  }

  function loadParcels(address, mine) {
    var box = $("adres-perceel"), linked = address.percelen.length > 0, wanted;
    if (linked) {
      wanted = Promise.all(address.percelen.map(function (code) {
        return getJson(A.perceelUrl(code)).then(function (response) { return A.parcels(response)[0] || null; });
      }));
    } else if (typeof address.lon === "number") {
      wanted = getJson(A.perceelAtUrl(address.lon, address.lat)).then(function (response) { return [A.parcelAt(response, address.lon, address.lat)]; });
    } else {
      renderParcels(box, address, [], linked);
      return;
    }
    busy(box, "Het Kadaster wordt geraadpleegd…");
    wanted.then(function (found) {
      if (mine !== chosen) return;
      found = found.filter(Boolean);
      renderParcels(box, address, found, linked);
      current.parcels = found; current.withParcel = true;
      renderNotices(); // now also the notices that lie on the parcel
    }).catch(function () {
      if (mine !== chosen) return;
      failed(box, "De kadastrale kaart (Kadaster, via PDOK) antwoordt niet. Het perceel en het kaartje ontbreken daardoor.",
        function () { loadParcels(address, mine); });
    });
  }

  function noticeNode(row) {
    var node = el("div", "pub"), meta = el("p", "pub-meta");
    node.setAttribute("data-id", row.id);
    meta.appendChild(el("span", "pub-datum", row.datum));
    meta.appendChild(document.createTextNode(" · " + row.gemeente + " · " + row.soort));
    node.appendChild(meta);
    node.appendChild(el("p", "pub-titel", row.titel));
    if (row.reden) node.appendChild(el("p", "pub-reden", row.reden));
    if (row.weggefilterd) node.appendChild(el("p", "pub-reden", "In de ranglijst weggefilterd."));
    if (row.url) { var links = el("p", "links"); links.appendChild(link(row.url, "Open bij de bron")); node.appendChild(links); }
    return node;
  }

  function noticeGroup(title, rows) {
    var group = el("div", "pubs"), head = el("p", "day", title);
    head.appendChild(el("span", null, String(rows.length)));
    group.appendChild(head);
    rows.forEach(function (row) { group.appendChild(noticeNode(row)); });
    return group;
  }

  /* An address outside the core: the notices of its region come from a file of their own, which
     the app reads when it is needed. Until then, and when it does not come, the core is searched. */
  function loadRegion(address, mine) {
    var regios = window.TilburgSignalenRegios;
    if (!regios) return;
    regios.voorGemeente(address.gemeente).then(function (found) {
      if (mine !== chosen) return;
      current.regios = found.regios; current.extra = found.berichten; current.regioFout = false;
      renderNotices();
    }).catch(function () {
      if (mine !== chosen) return;
      current.regioFout = true;
      renderNotices();
    });
  }

  /* The app fetched its data again (app.js): search the new notices for the address that is open.
     The address itself, its building and its parcel stay as they are; no register is asked again. */
  window.addEventListener("tilburg-signalen:ververst", function () {
    if (!current.address) return;
    renderNotices();
    loadRegion(current.address, chosen);
  });

  /* The notices of the app about the chosen address: those of the core and, when they are in,
     those of the region of the address. With the parcel known, notices are also matched by where
     they lie. */
  function renderNotices() {
    var box = $("adres-publicaties"), loaded = data(), address = current.address;
    if (!address) return; // a point from a notice: no address to search for
    box.textContent = "";
    if (!loaded || !loaded.berichten) {
      box.appendChild(el("p", "stale", "De berichten van de app zijn niet geladen; er kan niet in worden gezocht."));
      return;
    }
    // First of all the period the list covers, so that an empty list is not read as "never anything".
    box.appendChild(el("p", "periode", A.periodLine(loaded.vensterDagen)));
    var result = A.findNotices(window.TilburgSignalen.merged(loaded.berichten, [current.extra]), address, current.parcels);
    if (!result.adres.length && !result.mogelijk.length && !result.straat.length) {
      box.appendChild(el("p", null, "Geen publicaties over " + address.straat + " " + A.houseNumber(address) + " in de berichten van de app."));
    }
    if (result.adres.length) box.appendChild(noticeGroup("Dit adres", result.adres));
    if (result.mogelijk.length) box.appendChild(noticeGroup("Mogelijk dit adres", result.mogelijk));
    if (result.straat.length) {
      var more = el("details", "details"), summary = el("summary");
      summary.appendChild(el("span", "tags", "Zelfde straat, zonder huisnummer (" + result.straat.length + ")"));
      summary.appendChild(el("span", "toggle", "Toon"));
      more.appendChild(summary);
      var list = el("div", "pubs");
      result.straat.forEach(function (row) { row.reden = ""; list.appendChild(noticeNode(row)); });
      more.appendChild(list);
      box.appendChild(more);
    }
    box.appendChild(el("p", "bronregel", "Doorzocht: " + result.doorzocht.toLocaleString("nl-NL") + " berichten die de app nu heeft, ook de weggefilterde" +
      (current.regios.length ? " en die van " + window.TilburgSignalen.nameList(current.regios) : "") +
      ". De bronnen schrijven adressen niet in een vaste vorm: een bericht kan ontbreken."));
    if (current.regioFout) box.appendChild(el("p", "stale", "De berichten van de regio van dit adres konden niet worden geladen; alleen de kern is doorzocht."));
    if (!current.withParcel) box.appendChild(el("p", "bronregel", "Berichten zonder dit adres in de tekst worden pas gekoppeld als het perceel bekend is."));
  }

  /* The box "Energielabel". `fill` puts the label, or what is known about it, in the box; under it
     the link to EP-Online always stays, so that the register itself is one tap away. */
  function renderEnergy(address, fill) {
    var links = A.viewerLinks(address), energy = $("adres-energie"), row;
    energy.textContent = "";
    fill(energy);
    row = el("p", "links"); row.appendChild(link(links.energielabel.url, links.energielabel.label)); energy.appendChild(row);
    energy.appendChild(el("p", "bronregel", "De link opent het zoekscherm van EP-Online (Rijksdienst voor Ondernemend Nederland). Vul daar in: " + links.energielabel.zoekwaarde + "."));
  }

  /* Ask the energy label Worker, when its address is set (config.json, energielabel_worker).
     Without that setting the box stays as it was before the Worker existed. */
  function loadLabel(address, mine) {
    var loaded = data(), ask = A.energielabelVraag(loaded && loaded.energielabelWorker, address);
    if (!ask) {
      renderEnergy(address, function (box) { box.appendChild(el("p", null, "Nog niet beschikbaar in de app.")); });
      return;
    }
    renderEnergy(address, function (box) { box.appendChild(el("p", "bezig", "Energielabel wordt opgezocht bij EP-Online ...")); });
    var controller = typeof AbortController === "function" ? new AbortController() : null;
    var clock = setTimeout(function () { if (controller) controller.abort(); }, TIMEOUT);
    // A POST with the address in the body. No headers of our own: the browser then sends it as plain
    // text, without a question beforehand (a preflight); the Worker reads the body as JSON.
    var options = { method: "POST", body: ask.body, credentials: "omit", cache: "no-store" };
    if (controller) options.signal = controller.signal;
    fetch(ask.url, options).then(function (response) {
      // Every answer of the Worker is JSON; a body that is not, with a fault status, still says enough.
      return response.json().then(function (body) { return { status: response.status, body: body }; }, function () { return { status: response.ok ? 0 : response.status, body: null }; });
    }, function () { return { status: 0, body: null }; }).then(function (answer) {
      clearTimeout(clock);
      if (mine !== chosen) return;
      var model = A.energielabelModel(answer.status, answer.body, window.TilburgSignalen.isoDay(new Date()));
      renderEnergy(address, function (box) {
        if (model.soort === "gevonden") {
          var label = el("p", "label-klasse");
          label.appendChild(el("span", "sr", "Energielabel "));
          label.appendChild(el("strong", null, model.klasse));
          box.appendChild(label);
          box.appendChild(facts(model.feiten));
        } else {
          box.appendChild(el("p", model.soort === "geen" ? null : "stale", model.tekst));
          if (model.opnieuw) {
            var again = el("button", "ghost", "Opnieuw proberen");
            again.type = "button";
            again.addEventListener("click", function () { loadLabel(address, mine); });
            box.appendChild(again);
          }
        }
        box.setAttribute("data-uitkomst", model.soort);
        if (model.bron) box.appendChild(el("p", "bronregel", model.bron));
      });
    });
  }

  /* The box "Bestemmingsplan en omgevingsplan". `fill` puts what is known about the plans in the
     box; under it the link to Regels op de kaart always stays: that is where the current rules are. */
  function renderPlan(address, fill) {
    var links = A.viewerLinks(address), plan = $("adres-plan"), row;
    plan.textContent = "";
    fill(plan);
    row = el("p", "links"); row.appendChild(link(links.plan.url, links.plan.label)); plan.appendChild(row);
    plan.appendChild(el("p", "bronregel", "De link opent de kaart van het Omgevingsloket op de plek van dit adres."));
  }

  /* One adopted zoning with its plan, its figures, right under them the warning that changes since
     1-1-2024 are missing, and a link to its rules. */
  function planBlock(item, model) {
    var block = el("div", "planblok");
    block.appendChild(facts([
      { label: "Bestemming", value: item.naam },
      { label: "Plan", value: item.plan },
      { label: "Datum", value: item.datum },
      { label: "Status", value: item.status },
    ].concat(item.maten)));
    if (!item.maten.length) block.appendChild(el("p", "geen-getal", model.geenGetal));
    // Right at the figures: what this source does not have.
    block.appendChild(el("p", "stale plan-waarschuwing", model.waarschuwing));
    if (item.regels) { var row = el("p", "links"); row.appendChild(link(item.regels, "Lees de regels van deze bestemming")); block.appendChild(row); }
    return block;
  }

  /* Ask Ruimtelijke plannen (PDOK) what applies at the point of the address. */
  function loadPlan(address, mine) {
    var url = A.planUrl(address.rd);
    if (!url) {
      renderPlan(address, function (box) {
        box.setAttribute("data-uitkomst", "geen-punt");
        box.appendChild(el("p", null, "Bij dit adres is geen plek op de kaart bekend; het bestemmingsplan kan niet worden opgezocht."));
      });
      return;
    }
    renderPlan(address, function (box) { box.removeAttribute("data-uitkomst"); busy(box, "Het bestemmingsplan wordt opgezocht…"); });
    getText(url).then(function (answer) {
      if (mine !== chosen) return;
      var model = A.planModel(answer.status, answer.text, window.TilburgSignalen.isoDay(new Date()));
      renderPlan(address, function (box) {
        box.setAttribute("data-uitkomst", model.soort);
        if (model.soort !== "gevonden" && model.soort !== "geen") {
          failed(box, model.tekst, function () { loadPlan(address, mine); });
          return;
        }
        if (model.overlap) box.appendChild(el("p", "stale", model.overlap));
        if (model.tekst) box.appendChild(el("p", null, model.tekst));
        model.bestemmingen.forEach(function (item) { box.appendChild(planBlock(item, model)); });
        model.overigeMaten.forEach(function (other) {
          box.appendChild(el("p", "bronregel", "Ook op de kaart, uit " + other.plan + ":"));
          box.appendChild(facts(other.maten));
        });
        // Without a zoning the warning still comes: the current rules may well say something here.
        if (!model.bestemmingen.length) box.appendChild(el("p", "stale plan-waarschuwing", model.waarschuwing));
        box.appendChild(el("p", "dubbel", "Dubbelbestemmingen: " + (model.dubbel.length ? model.dubbel.join("; ") : "geen") + "."));
        if (model.nietGetoond) box.appendChild(el("p", "bronregel", model.nietGetoond));
        box.appendChild(el("p", "bronregel", model.bron));
      });
    });
  }

  /* Every box of the tab; `shown` says per box whether it is in use. A box that is not in use is
     hidden, and stays off paper too (rapport.js). */
  function boxes(shown) {
    [].forEach.call(document.querySelectorAll("#adres-uitkomst section.vak"), function (vak) { vak.hidden = !shown(vak); });
  }

  /* `notice`: the notice the address was taken from (the location report), or nothing when the
     address was typed. */
  function choose(address, notice) {
    var mine = ++chosen;
    if (!notice) forgetNotice();
    boxes(function (vak) { return vak.id !== "vak-bekendmaking" || !!notice; });
    typed++; // an answer of the address search that is still on its way no longer counts
    clearTimeout(timer);
    hideSuggestions();
    message("");
    $("adres-zoek").value = notice ? "" : address.label;
    $("adres-naam").textContent = address.straat ? address.straat + " " + A.houseNumber(address) : address.label;
    $("adres-sub").textContent = [address.postcode, address.woonplaats].filter(Boolean).join(" ") +
      (address.gemeente && address.gemeente !== address.woonplaats ? " · gemeente " + address.gemeente : "");
    $("adres-uitkomst").hidden = false;
    current = { address: address, parcels: [], withParcel: false, regios: [], extra: [], regioFout: false };
    $("adres-energie").removeAttribute("data-uitkomst");
    loadLabel(address, mine);
    renderNotices();
    loadRegion(address, mine);
    loadBag(address, mine);
    loadParcels(address, mine);
    loadPlan(address, mine);
  }

  /* ---------- A location from a notice (the location report) ---------- */

  function forgetNotice() {
    $("adres-bekendmaking").textContent = "";
    $("adres-uitkomst").removeAttribute("data-rapport");
  }

  /* The box "Bekendmaking": what the notice says, in short, with its warnings, how the rest of the
     tab was filled, and the source. Never the whole text: the link leads to it. */
  function renderNotice(item, how) {
    var L = window.TilburgSignalen, loaded = data(), box = $("adres-bekendmaking");
    var model = L.cardModel(item, { centre: (loaded && loaded.centrum) || CENTRE, nieuw: {}, ranks: {}, today: L.isoDay(new Date()) });
    box.textContent = "";
    box.appendChild(el("p", "pub-titel", item.titel));
    box.appendChild(facts([
      { label: "Soort", value: model.kind + (model.fase ? ", " + model.fase.toLowerCase() : "") },
      { label: "Gemeente", value: item.gemeente || item.overheid },
      { label: "Datum", value: model.date },
      { label: "Plek", value: model.place + (item.locatieSoort === "exact" ? "" : item.locatieSoort === "benaderd" ? " (bij benadering)" : " (alleen de gemeente)") },
    ].concat(model.deadline ? [{ label: "Reageren", value: model.deadline.replace(/^Reageren tot /, "tot ") }] : [])));
    if (item.waarom) box.appendChild(el("p", null, item.waarom));
    if (item.omschrijving) box.appendChild(el("p", "samenvatting", "Uit de omschrijving: " + A.samenvatting(item.omschrijving)));
    A.locatieWaarschuwingen(item).forEach(function (text) { box.appendChild(el("p", "stale", text)); });
    if (how) box.appendChild(el("p", how.soort === "adres" ? "bronregel" : "stale", how.tekst));
    if (L.safeUrl(item.url)) { var row = el("p", "links"); row.appendChild(link(item.url, "Open de bekendmaking bij de bron")); box.appendChild(row); }
    box.appendChild(el("p", "bronregel", "Bron: " + item.publicatie + " " + (item.overheid || "") + ", gepubliceerd op " + model.date +
      (loaded && loaded.bijgewerkt ? "; in de app sinds de verversing, opgevraagd op " + L.shortDate(String(loaded.bijgewerkt).slice(0, 10)) : "") + "."));
  }

  var NO_ADDRESS = "Pand (BAG), energielabel en publicaties over het adres zijn daarom overgeslagen.";

  /* Fill the tab from a notice: with the one address it names when the address search finds it
     unambiguously, else with its point (parcel and zoning plan only), else with the notice alone. */
  function chooseLocation(item) {
    var mine = ++chosen;
    typed++;
    clearTimeout(timer);
    hideSuggestions();
    message("");
    $("adres-zoek").value = "";
    current = { address: null, parcels: [], withParcel: false, regios: [], extra: [], regioFout: false };
    $("adres-uitkomst").setAttribute("data-rapport", "locatie");
    $("adres-uitkomst").hidden = false;
    $("adres-naam").textContent = window.TilburgSignalen.cardModel(item, { centre: CENTRE, nieuw: {}, ranks: {}, today: "" }).place;
    $("adres-sub").textContent = "Locatie uit een bekendmaking" + (item.gemeente ? " · gemeente " + item.gemeente : "");
    boxes(function (vak) { return vak.id === "vak-bekendmaking"; });
    renderNotice(item, { soort: "bezig", tekst: "Het adres in de bekendmaking wordt opgezocht…" });

    function withoutAddress(how) {
      if (mine !== chosen) return;
      if (how.soort === "punt") {
        var rd = A.wgs84ToRd(item.lat, item.lon), point = { lon: item.lon, lat: item.lat, rd: rd, percelen: [], punt: true, straat: "", huisnummer: null, huisletter: "", toevoeging: "", postcode: "" };
        renderNotice(item, { soort: "punt", tekst: "Geen eenduidig adres. " + how.reden + " Perceel en bestemmingsplan zijn opgevraagd op het punt uit de bekendmaking; dat geeft een beperkte nauwkeurigheid. " + NO_ADDRESS });
        boxes(function (vak) { return vak.id === "vak-bekendmaking" || vak.id === "vak-perceel" || vak.id === "vak-plan"; });
        loadParcels(point, mine);
        loadPlan(point, mine);
      } else {
        renderNotice(item, { soort: "geen", tekst: "Geen eenduidig adres en geen vaste plek. " + how.reden + " Perceel en bestemmingsplan zijn niet opgevraagd. " + NO_ADDRESS });
      }
    }

    var place = item.plaats && /\d/.test(item.plaats) && item.locatieSoort === "exact" ? item.plaats : "";
    if (!place) { withoutAddress(A.locatieVanBericht(item, [])); return; }
    var loaded = data(), text = A.searchText(place.replace(/\bte\b/g, " ")) + (item.gemeente && place.toLowerCase().indexOf(item.gemeente.toLowerCase()) === -1 ? " " + item.gemeente : "");
    getJson(A.suggestUrl(text, (loaded && loaded.centrum) || CENTRE)).then(function (response) {
      if (mine !== chosen) return;
      var how = A.locatieVanBericht(item, A.addresses(response));
      if (how.soort !== "adres") { withoutAddress(how); return; }
      choose(how.adres, item);
      renderNotice(item, { soort: "adres", tekst: "Adres afgeleid uit de tekst van de bekendmaking en gevonden in de adressenregistratie (PDOK Locatieserver). Controleer of het het bedoelde adres is." });
    }).catch(function () {
      withoutAddress({ soort: item.locatieSoort === "exact" ? "punt" : "geen", reden: "De adreszoeker (PDOK Locatieserver) antwoordde niet." });
    });
  }

  window.TilburgAdresApp = { kiesLocatie: chooseLocation };

  var input = $("adres-zoek");
  input.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(suggest, WAIT);
  });
  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && shown.length) { event.preventDefault(); choose(shown[0]); }
    else if (event.key === "Escape") hideSuggestions();
  });
})();
