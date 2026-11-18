/* The tab "Adres" in a real browser, for browser_smoke.js. The registers of PDOK are played back
   from adres_fixtures.json (real answers, shortened), so the test does not depend on PDOK and can
   let a register fail on purpose. Notices about the test address are added to the data the page
   loads; the data on disk is not touched. Returns what the page showed, as plain values. */
"use strict";
var fixtures = require("./adres_fixtures.json");
var A = require("../../site/adres.js");

var PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==", "base64");
var ADDRESS = A.addresses(fixtures.suggest)[0];
var TYPED = "Burg. van de Mortelplein 118a";
// An address outside the core: Noordweg 402 in Middelburg, a municipality of the region Zeeland.
var OUTSIDE = A.addresses(fixtures.buitenKern.suggest)[0];
var TYPED_OUTSIDE = "Noordweg 402 Middelburg";

/* A point inside the second parcel of the address, away from the address point itself. */
function insideParcel() {
  var parcel = A.parcels(fixtures.perceel["4489"])[0], ring = parcel.rings[0].slice(0, -1);
  var lon = ring.reduce(function (sum, p) { return sum + p[0]; }, 0) / ring.length, lat = ring.reduce(function (sum, p) { return sum + p[1]; }, 0) / ring.length;
  if (!A.contains(parcel, lon, lat)) throw new Error("het testpunt ligt niet in het perceel");
  return { lon: lon, lat: lat };
}

/* Notices about the test address in the ways sources write one, plus one about the neighbours. */
function addNotices(data) {
  var base = data.berichten[0], spot = insideParcel();
  function notice(id, titel, extra) {
    return Object.assign({}, base, {
      id: id, titel: titel, omschrijving: null, plaats: "", gemeente: "Tilburg", overheid: "Tilburg", publicatie: "Gemeenteblad",
      bron: "officielebekendmakingen", type: "vergunning", soort: null, fase: "Aanvraag", datum: "2026-11-10", klasse: "weggefilterd", score: 0, regio: "kern",
      waarom: "Geen nieuwbouw van woningen en geen ontwikkelsignaal in de bekendmaking.", signalen: [], woningen: null, perceelM2: null,
      locatieSoort: "exact", lat: ADDRESS.lat, lon: ADDRESS.lon, afstandKm: 2.4, reactieTot: null,
      url: "https://zoek.officielebekendmakingen.nl/" + id + ".html", urlTekst: null,
    }, extra || {});
  }
  // A notice about the address outside the core: it belongs in the file of its region, not in the core.
  data.regioTest = notice("test-regio-zeeland", "Aanvraag omgevingsvergunning reguliere procedure Noordweg 402, 4333 KK Middelburg",
    { gemeente: "Middelburg", overheid: "Middelburg", regio: "Zeeland", lat: OUTSIDE.lat, lon: OUTSIDE.lon, afstandKm: 103.1 });
  data.berichten = [
    notice("test-adres-zelf", "Aanvraag omgevingsvergunning, Burg. van de Mortelplein 118A, 5037 PL Tilburg"),
    notice("test-adres-zonder", "Besluit omgevingsvergunning, Burgemeester van de Mortelplein 118 te Tilburg", { fase: "Verleend", klasse: "onzeker", waarom: "Sloop, maar de perceelgrootte is niet te bepalen.", datum: "2026-11-03" }),
    notice("test-adres-buren", "Aanvraag omgevingsvergunning, Burgemeester van de Mortelplein 120, 5037PL Tilburg", { lat: ADDRESS.lat + 0.0006, lon: ADDRESS.lon }),
    notice("test-adres-straat", "Kappen van drie bomen, Burgemeester van de Mortelplein Tilburg", { locatieSoort: "benaderd" }),
    notice("test-adres-perceel", "Aanvraag omgevingsvergunning, Ingetekende geometrie", { lat: spot.lat, lon: spot.lon }),
    notice("test-adres-elders", "Aanvraag omgevingsvergunning, Burgemeester van de Mortelplein 118a te Goirle", { gemeente: "Goirle", overheid: "Goirle", lat: 51.5205, lon: 5.0655 }),
  ].concat(data.berichten);
}

/* The data without anything about the test address: nothing that names the square, nothing near it. */
function removeNotices(data) {
  data.berichten = data.berichten.filter(function (item) {
    var near = typeof item.lat === "number" && Math.abs(item.lat - ADDRESS.lat) < 0.003 && Math.abs(item.lon - ADDRESS.lon) < 0.005;
    return !near && !/mortelplein/i.test([item.titel, item.omschrijving, item.plaats].join(" "));
  });
}

function part(url) {
  if (/\/locatieserver\//.test(url)) return "zoeker";
  if (/\/verblijfsobject\/items/.test(url)) return "adresobject";
  if (/\/pand\/items\//.test(url)) return "pand";
  if (/\/brk-kadastrale-kaart\//.test(url)) return "perceel";
  if (/\/kadastralekaart\/wms\//.test(url)) return "kaart";
  return "onbekend";
}

function answer(url) {
  var which = part(url), params = new URL(url).searchParams, outside = fixtures.buitenKern;
  if (which === "zoeker") return /middelburg/i.test(params.get("q")) ? outside.suggest : fixtures.suggest;
  if (which === "adresobject") return params.get("identificatie") === OUTSIDE.objectId ? outside.vbo : fixtures.vbo;
  if (which === "pand") { var id = url.split("?")[0].split("/").pop(); return fixtures.pand[id] || outside.pand[id]; }
  if (which === "perceel") return fixtures.perceel[params.get("perceelnummer")] || outside.perceel[params.get("perceelnummer")];
  return null;
}

module.exports = async function (browser, base) {
  var result = {};

  /* `down` lists what does not answer: a part name fails to connect, "name:503" answers with an
     error, "name:stil" never answers. The list can be changed while the page is open. */
  async function open(width, down, withoutNotices) {
    var context = await browser.newContext({ viewport: { width: width, height: 844 }, locale: "nl-NL", timezoneId: "Europe/Amsterdam", serviceWorkers: "block" });
    var page = await context.newPage(), seen = { errors: [], pdok: [], elsewhere: [] };
    page.on("pageerror", function (error) { seen.errors.push(error.message); });
    page.on("console", function (message) {
      // A register that fails on purpose makes the browser log the failed request; that is not an error of the app.
      if (message.type() === "error" && !/Failed to load resource|net::ERR_/.test(message.text())) seen.errors.push(message.text());
    });
    page.on("request", function (request) {
      var url = request.url();
      if (url.indexOf(base) !== 0 && !/^(data:|blob:|https:\/\/fonts\.|https:\/\/(api|service)\.pdok\.nl\/)/.test(url)) seen.elsewhere.push(url);
    });
    await page.route(/^https:\/\/fonts\./, function (route) { route.fulfill({ status: 200, contentType: "text/css", body: "" }); });
    await page.route("**/data/berichten.json", async function (route) {
      var data = await (await route.fetch()).json();
      if (withoutNotices) removeNotices(data); else addNotices(data);
      seen.regioTest = data.regioTest;
      seen.regios = (data.regios || []).map(function (regio) { return regio.naam; });
      delete data.regioTest;
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
    });
    await page.route("**/data/regio-zeeland.json", async function (route) {
      seen.regionFile = (seen.regionFile || 0) + 1;
      var file = await (await route.fetch()).json();
      if (seen.regioTest) file.berichten = [seen.regioTest].concat(file.berichten);
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(file) });
    });
    await page.route(/^https:\/\/(api|service)\.pdok\.nl\//, function (route) {
      var url = route.request().url(), which = part(url);
      seen.pdok.push({ part: which, url: url });
      if (down.indexOf(which) !== -1) return route.abort("connectionfailed");
      if (down.indexOf(which + ":503") !== -1) return route.fulfill({ status: 503, contentType: "text/plain", body: "Service Unavailable" });
      if (down.indexOf(which + ":stil") !== -1) return undefined; // never answered
      if (which === "kaart") return route.fulfill({ status: 200, contentType: "image/png", body: PNG });
      var body = answer(url);
      return body ? route.fulfill({ status: 200, contentType: "application/json", headers: { "access-control-allow-origin": "*" }, body: JSON.stringify(body) })
        : route.fulfill({ status: 404, contentType: "text/plain", body: "onbekend in de test" });
    });
    await page.goto(base + "/index.html");
    await page.waitForSelector("#list .card");
    return { page: page, seen: seen, context: context };
  }

  async function choose(page, typed) {
    await page.fill("#adres-zoek", typed || TYPED);
    await page.waitForSelector("#adres-suggesties .suggestie");
    await page.click("#adres-suggesties .suggestie");
    await page.waitForFunction(function () { return !document.getElementById("adres-uitkomst").hidden && !document.querySelector("#adres-uitkomst .bezig"); });
  }
  function overflow(page) { return page.evaluate(function () { return document.documentElement.scrollWidth - window.innerWidth; }); }
  function text(page, selector) { return page.$eval(selector, function (node) { return node.innerText.replace(/\s+/g, " ").trim(); }); }
  function facts(page, selector) {
    return page.$$eval(selector + " .feiten", function (lists) {
      return lists.map(function (list) {
        var out = {}, terms = list.querySelectorAll("dt"), values = list.querySelectorAll("dd");
        for (var i = 0; i < terms.length; i++) out[terms[i].textContent] = values[i].textContent;
        return out;
      });
    });
  }
  function notices(page) {
    return page.evaluate(function () {
      var out = { groups: {}, rows: {} };
      document.querySelectorAll("#adres-publicaties > .pubs, #adres-publicaties > details").forEach(function (group) {
        var head = group.querySelector(".day, summary .tags"), name = head ? head.firstChild.textContent : "";
        out.groups[name.replace(/ \(\d+\)$/, "")] = Array.from(group.querySelectorAll(".pub")).map(function (row) { return row.getAttribute("data-id"); });
      });
      document.querySelectorAll("#adres-publicaties .pub").forEach(function (row) {
        var a = row.querySelector("a");
        out.rows[row.getAttribute("data-id")] = {
          meta: row.querySelector(".pub-meta").textContent, titel: row.querySelector(".pub-titel").textContent,
          reden: Array.from(row.querySelectorAll(".pub-reden")).map(function (p) { return p.textContent; }), link: a ? a.href : null, linkText: a ? a.textContent : null,
        };
      });
      return out;
    });
  }

  // --- The narrowest phone, every register answers.
  var session = await open(320, []), page = session.page;
  result.requestsBeforeUse = session.seen.pdok.length;
  result.morningBefore = { count: await page.textContent("#result-count"), cards: await page.$$eval("#list .card", function (nodes) { return nodes.length; }), brief: await page.textContent("#brief-title") };
  await page.click("#tab-adres");
  await page.waitForSelector("#view-adres:not([hidden])");
  result.hash = await page.evaluate(function () { return location.hash; });
  result.views = await page.$$eval("main .view", function (nodes) { return nodes.filter(function (node) { return !node.hidden; }).map(function (node) { return node.id; }); });
  result.tabs = await page.$$eval(".tabs a", function (nodes) {
    return nodes.map(function (node) {
      var range = document.createRange(); range.selectNodeContents(node);
      var tops = Array.from(range.getClientRects()).filter(function (box) { return box.width > 0 && box.height < 20; }).map(function (box) { return Math.round(box.top); });
      var box = node.getBoundingClientRect();
      return { label: node.textContent.trim(), current: node.getAttribute("aria-current"), width: Math.round(box.width), right: Math.round(box.right),
        lines: tops.filter(function (top, i) { return tops.indexOf(top) === i; }).length, textWidth: Math.round(node.scrollWidth) };
    });
  });
  result.emptyOverflow = await overflow(page);
  result.resultHiddenAtStart = await page.$eval("#adres-uitkomst", function (node) { return node.hidden; });

  await page.fill("#adres-zoek", "Bu");
  await page.waitForTimeout(500);
  result.requestsForTwoLetters = session.seen.pdok.length;
  await page.fill("#adres-zoek", TYPED);
  await page.waitForSelector("#adres-suggesties .suggestie");
  result.suggestions = await page.$$eval("#adres-suggesties .suggestie", function (nodes) {
    return nodes.map(function (node) { var box = node.getBoundingClientRect(); return { text: node.textContent, height: Math.round(box.height), right: Math.round(box.right) }; });
  });
  result.suggestOverflow = await overflow(page);
  result.suggestRequest = session.seen.pdok.filter(function (entry) { return entry.part === "zoeker"; }).pop().url;
  await page.click("#adres-suggesties .suggestie");
  await page.waitForFunction(function () { return !document.querySelector("#adres-uitkomst .bezig"); });
  await page.waitForFunction(function () { var image = document.querySelector(".kaartvlak img"); return image && image.complete; });

  result.name = await text(page, "#adres-naam");
  result.sub = await text(page, "#adres-sub");
  result.input = await page.inputValue("#adres-zoek");
  result.bag = (await facts(page, "#adres-bag"))[0];
  result.bagText = await text(page, "#adres-bag");
  result.parcels = await facts(page, "#adres-perceel");
  result.parcelText = await text(page, "#adres-perceel");
  result.parcelWarning = await page.$eval("#adres-perceel .stale", function (node) { return node.textContent; });
  result.warningRightAfterSize = await page.$eval("#adres-perceel", function (box) {
    var lists = box.querySelectorAll(".feiten"), last = lists[lists.length - 1];
    return !!last && last.nextElementSibling === box.querySelector(".stale");
  });
  result.map = await page.$eval(".kaartvlak", function (frame) {
    var image = frame.querySelector("img"), box = frame.getBoundingClientRect(), dot = frame.querySelector(".p-adres"), bar = frame.querySelector(".schaal");
    var shapes = Array.from(frame.querySelectorAll(".p-perceel")).map(function (shape) { var b = shape.getBoundingClientRect(); return b.width > 4 && b.height > 4 && b.left >= box.left - 1 && b.right <= box.right + 1; });
    return { image: !!image && image.naturalWidth > 0, src: image ? image.src : "", width: Math.round(box.width), height: Math.round(box.height), right: Math.round(box.right),
      shapes: shapes, dot: !!dot && dot.getBoundingClientRect().left > box.left && dot.getBoundingClientRect().right < box.right, bar: bar ? bar.textContent : null,
      barInside: !!bar && bar.getBoundingClientRect().right < box.right };
  });
  result.notices = await notices(page);
  result.noticesText = await text(page, "#adres-publicaties");
  result.period = await page.evaluate(function () {
    var box = document.getElementById("adres-publicaties"), line = box.querySelector(".periode");
    return { text: line ? line.textContent : null, first: !!line && box.firstElementChild === line, lines: box.querySelectorAll(".periode").length,
      windows: window.TilburgSignalenGegevens.vensterDagen };
  });
  result.energy = { text: await text(page, "#adres-energie"), links: await page.$$eval("#adres-energie a", function (nodes) { return nodes.map(function (a) { return a.href; }); }) };
  result.plan = { text: await text(page, "#adres-plan"), links: await page.$$eval("#adres-plan a", function (nodes) { return nodes.map(function (a) { return a.href; }); }) };
  result.overflow = await overflow(page);
  result.brokenDates = await page.$$eval("#adres-publicaties .pub-datum", function (nodes) {
    return nodes.filter(function (node) { var tops = Array.from(node.getClientRects()).map(function (box) { return Math.round(box.top); }); return tops.some(function (top) { return top !== tops[0]; }); }).length;
  });
  result.linkHeights = await page.$$eval("#adres-uitkomst .links a", function (nodes) { return nodes.map(function (a) { return Math.round(a.getBoundingClientRect().height); }); });
  result.widest = await page.$$eval("#adres-uitkomst *", function (nodes) { return Math.max.apply(null, nodes.map(function (node) { return Math.round(node.getBoundingClientRect().right); })); });
  result.newTabLinks = await page.$$eval("#adres-uitkomst a", function (nodes) { return nodes.every(function (a) { return a.target === "_blank" && a.rel === "noopener" && /^https:\/\//.test(a.href); }); });
  await page.click("#adres-publicaties details summary");
  result.streetOpenOverflow = await overflow(page);
  result.asked = session.seen.pdok.map(function (entry) { return entry.part; });
  result.askedHosts = session.seen.pdok.map(function (entry) { return new URL(entry.url).host; }).filter(function (host, i, all) { return all.indexOf(host) === i; }).sort();
  result.keys = session.seen.pdok.filter(function (entry) { return /key|token|apikey|authorization/i.test(entry.url); }).length;
  result.elsewhere = session.seen.elsewhere;

  // Back to the morning screen: nothing there has changed.
  await page.click("#tab-berichten");
  await page.waitForSelector("#view-berichten:not([hidden])");
  result.morningAfter = { count: await page.textContent("#result-count"), cards: await page.$$eval("#list .card", function (nodes) { return nodes.length; }), brief: await page.textContent("#brief-title") };
  result.viewsAfter = await page.$$eval("main .view", function (nodes) { return nodes.filter(function (node) { return !node.hidden; }).map(function (node) { return node.id; }); });
  result.errors = session.seen.errors;
  await session.context.close();

  // --- The address search does not connect: a message, and the rest of the tab stays.
  session = await open(390, ["zoeker"]); page = session.page;
  await page.click("#tab-adres");
  await page.fill("#adres-zoek", TYPED);
  await page.waitForSelector("#adres-melding:not([hidden])");
  result.searchDown = { message: await text(page, "#adres-melding"), input: await page.isVisible("#adres-zoek"), heading: await text(page, "#view-adres h2"),
    result: await page.isVisible("#adres-uitkomst"), suggestions: await page.isVisible("#adres-suggesties"), errors: session.seen.errors };
  await session.context.close();

  // --- The building register answers with an error and the cadastre does not connect.
  var down = ["adresobject:503", "perceel"];
  session = await open(390, down); page = session.page;
  await page.click("#tab-adres");
  await choose(page);
  result.registersDown = {
    bag: await text(page, "#adres-bag"), bagRetry: await page.$$eval("#adres-bag button", function (nodes) { return nodes.map(function (node) { return node.textContent; }); }),
    parcel: await text(page, "#adres-perceel"), parcelRetry: await page.$$eval("#adres-perceel button", function (nodes) { return nodes.length; }),
    name: await text(page, "#adres-naam"), notices: await notices(page), noticesText: await text(page, "#adres-publicaties"),
    energy: await text(page, "#adres-energie"), plan: await text(page, "#adres-plan"), overflow: await overflow(page),
  };
  down.length = 0; // both registers are back
  await page.click("#adres-bag button");
  await page.waitForSelector("#adres-bag .feiten");
  await page.click("#adres-perceel button");
  await page.waitForSelector("#adres-perceel .feiten");
  result.afterRetry = { bag: (await facts(page, "#adres-bag"))[0], parcels: (await facts(page, "#adres-perceel")).length, notices: await notices(page), errors: session.seen.errors };
  await session.context.close();

  // --- Only the building and the background map are missing: what did come is shown.
  session = await open(390, ["pand", "kaart"]); page = session.page;
  await page.click("#tab-adres");
  await choose(page);
  await page.waitForFunction(function () { return !document.querySelector(".kaartvlak img"); });
  result.partsDown = {
    bag: (await facts(page, "#adres-bag"))[0], bagText: await text(page, "#adres-bag"),
    shapes: await page.$$eval(".kaartvlak .p-perceel", function (nodes) { return nodes.length; }), mapText: await text(page, ".perceelkaart"), errors: session.seen.errors,
  };
  await session.context.close();

  // --- No notices about the address: the period comes first, then that nothing was found.
  session = await open(320, [], true); page = session.page;
  await page.click("#tab-adres");
  await choose(page);
  await page.waitForSelector("#adres-perceel .feiten");
  result.noNotices = {
    lines: await page.$$eval("#adres-publicaties > *", function (nodes) { return nodes.map(function (node) { return { cls: node.className, text: node.textContent }; }); }),
    rows: await page.$$eval("#adres-publicaties .pub", function (nodes) { return nodes.length; }), overflow: await overflow(page), errors: session.seen.errors,
  };
  await session.context.close();

  // --- An address outside the core, while the app itself shows the core: its notices are found.
  session = await open(320, []); page = session.page;
  await page.click("#tab-adres");
  await choose(page, TYPED_OUTSIDE);
  await page.waitForSelector("#adres-perceel .feiten");
  if (session.seen.regios.indexOf("Zeeland") !== -1) await page.waitForSelector('#adres-publicaties [data-id="test-regio-zeeland"]');
  result.outside = {
    name: await text(page, "#adres-naam"), sub: await text(page, "#adres-sub"), bag: (await facts(page, "#adres-bag"))[0], parcels: await facts(page, "#adres-perceel"),
    notices: await notices(page), overflow: await overflow(page), errors: session.seen.errors,
    regionLine: await page.$eval("#regio-regel", function (node) { return !node.hidden; }),
    pressed: await page.$$eval('#regios .regio[aria-pressed="true"]', function (nodes) { return nodes.length; }),
    searched: await text(page, "#adres-publicaties .bronregel:last-of-type"), regios: session.seen.regios, regionFile: session.seen.regionFile || 0,
  };
  await page.click("#tab-berichten");
  await page.waitForSelector("#view-berichten:not([hidden])");
  result.outside.coreCards = await page.$$eval("#list .card", function (nodes) { return nodes.length; });
  result.outside.coreCount = await page.textContent("#result-count");
  await session.context.close();

  // --- The address search accepts the request and then stays silent: the app stops waiting.
  session = await open(390, ["zoeker:stil"]); page = session.page;
  await page.click("#tab-adres");
  await page.fill("#adres-zoek", TYPED);
  var started = Date.now();
  await page.waitForSelector("#adres-melding:not([hidden])", { timeout: 30000 });
  result.searchSilent = { message: await text(page, "#adres-melding"), seconds: (Date.now() - started) / 1000, errors: session.seen.errors };
  await session.context.close();

  return result;
};

/* For verversen_smoke.js: the same played-back registers and the same notices about the test address. */
module.exports.typed = TYPED;
module.exports.addNotices = addNotices;
module.exports.pdok = function (page, seen) {
  return page.route(/^https:\/\/(api|service)\.pdok\.nl\//, function (route) {
    var url = route.request().url(), which = part(url);
    seen.push(which);
    if (which === "kaart") return route.fulfill({ status: 200, contentType: "image/png", body: PNG });
    var body = answer(url);
    return body ? route.fulfill({ status: 200, contentType: "application/json", headers: { "access-control-allow-origin": "*" }, body: JSON.stringify(body) })
      : route.fulfill({ status: 404, contentType: "text/plain", body: "onbekend in de test" });
  });
};
