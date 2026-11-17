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

  function getJson(url) {
    var controller = typeof AbortController === "function" ? new AbortController() : null;
    var clock = setTimeout(function () { if (controller) controller.abort(); }, TIMEOUT);
    function done() { clearTimeout(clock); }
    return fetch(url, controller ? { signal: controller.signal } : {}).then(function (response) {
      if (!response.ok) throw new Error(String(response.status));
      return response.json();
    }).then(function (data) { done(); return data; }, function (error) { done(); throw error; });
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
    if (!linked) box.appendChild(el("p", "bronregel", "Het adres is in de bron niet aan een perceel gekoppeld; dit is het perceel op de plek van het adrespunt."));
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
      renderNotices(address, found, true); // now also the notices that lie on the parcel
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

  /* The notices of the app about this address. `withParcel` says whether the parcel is known, so
     that notices can also be matched by where they lie. */
  function renderNotices(address, found, withParcel) {
    var box = $("adres-publicaties"), loaded = data();
    box.textContent = "";
    if (!loaded || !loaded.berichten) {
      box.appendChild(el("p", "stale", "De berichten van de app zijn niet geladen; er kan niet in worden gezocht."));
      return;
    }
    // First of all the period the list covers, so that an empty list is not read as "never anything".
    box.appendChild(el("p", "periode", A.periodLine(loaded.vensterDagen)));
    var result = A.findNotices(loaded.berichten, address, found);
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
    box.appendChild(el("p", "bronregel", "Doorzocht: " + result.doorzocht.toLocaleString("nl-NL") + " berichten die de app nu heeft, ook de weggefilterde. " +
      "De bronnen schrijven adressen niet in een vaste vorm: een bericht kan ontbreken."));
    if (!withParcel) box.appendChild(el("p", "bronregel", "Berichten zonder dit adres in de tekst worden pas gekoppeld als het perceel bekend is."));
  }

  function renderLinks(address) {
    var links = A.viewerLinks(address);
    var energy = $("adres-energie"), plan = $("adres-plan"), row;
    energy.textContent = ""; plan.textContent = "";
    energy.appendChild(el("p", null, "Nog niet beschikbaar in de app."));
    row = el("p", "links"); row.appendChild(link(links.energielabel.url, links.energielabel.label)); energy.appendChild(row);
    energy.appendChild(el("p", "bronregel", "De link opent het zoekscherm van EP-Online (Rijksdienst voor Ondernemend Nederland). Vul daar in: " + links.energielabel.zoekwaarde + "."));
    plan.appendChild(el("p", null, "Nog niet beschikbaar in de app."));
    row = el("p", "links"); row.appendChild(link(links.plan.url, links.plan.label)); plan.appendChild(row);
    plan.appendChild(el("p", "bronregel", "De link opent de kaart van het Omgevingsloket op de plek van dit adres."));
  }

  function choose(address) {
    var mine = ++chosen;
    typed++; // an answer of the address search that is still on its way no longer counts
    clearTimeout(timer);
    hideSuggestions();
    message("");
    $("adres-zoek").value = address.label;
    $("adres-naam").textContent = address.straat ? address.straat + " " + A.houseNumber(address) : address.label;
    $("adres-sub").textContent = [address.postcode, address.woonplaats].filter(Boolean).join(" ") +
      (address.gemeente && address.gemeente !== address.woonplaats ? " · gemeente " + address.gemeente : "");
    $("adres-uitkomst").hidden = false;
    renderLinks(address);
    renderNotices(address, [], false);
    loadBag(address, mine);
    loadParcels(address, mine);
  }

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
