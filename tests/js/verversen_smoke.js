/* Coming back to the app, for browser_smoke.js, at the width of an iPhone (375 px).

   1. The app comes back into view while its data was fetched more than fifteen minutes ago: it
      fetches again and shows the new moment, and what the user had set stays: a chosen region, a
      search, a filter, an opened card and an address that was looked up. The clock of the page is
      moved forward instead of waiting; the data files are played back so that the second fetch
      brings something new (regions from regio_ongelezen.json, registers from adres_fixtures.json).
   2. The small map on the tab Gebied, with the data of the site itself: where every text stands,
      at 375 and at 320 px. */
"use strict";
var fixture = require("./regio_ongelezen.json");
var adres = require("./adres_smoke.js");

var LATER = ["2026-12-31T23:57:00+01:00", "2026-12-31T23:58:00+01:00", "2026-12-31T23:59:00+01:00"];
var REGION = "Zeeland", REGION_FILE = "regio-zeeland.json";

module.exports = async function (browser, base) {
  var result = {}, errors = [], pdok = [];
  var served = { version: 0, fail: false, failRegion: false, berichten: 0, gebied: 0, regio: [] };
  var context = await browser.newContext({ viewport: { width: 375, height: 812 }, locale: "nl-NL", timezoneId: "Europe/Amsterdam", serviceWorkers: "block" });
  var page = await context.newPage();
  page.on("pageerror", function (error) { errors.push(error.message); });
  page.on("console", function (message) {
    if (message.type() === "error" && !/Failed to load resource|net::ERR_/.test(message.text())) errors.push(message.text());
  });
  // The clock of the page can be moved forward: the app decides on Date.now() whether it is time.
  await page.addInitScript(function () {
    var real = Date.now.bind(Date);
    window.__vooruit = 0;
    Date.now = function () { return real() + window.__vooruit; };
  });
  await page.route(/^https:\/\/fonts\./, function (route) { route.fulfill({ status: 200, contentType: "text/css", body: "" }); });
  await adres.pdok(page, pdok);
  await page.route("**/data/gebied.json", function (route) { served.gebied++; return served.fail ? route.abort("connectionfailed") : route.continue(); });
  await page.route("**/data/berichten.json", async function (route) {
    served.berichten++;
    if (served.fail) return route.abort("connectionfailed");
    var data = await (await route.fetch()).json();
    adres.addNotices(data);
    delete data.regioTest;
    data.regios = fixture.regios;
    if (served.version) {
      // A later run: a new moment, a new location in the core and a new notice about the test address.
      var base0 = data.berichten[0], latest = data.berichten.reduce(function (day, item) { return item.datum > day ? item.datum : day; }, "");
      data.bijgewerkt = LATER[served.version - 1];
      data.berichten = [
        Object.assign({}, base0, { id: "test-ververst-kern", titel: "Aanvraag omgevingsvergunning, nieuw na het verversen, Teststraat 1 Tilburg", klasse: "ontwikkellocatie", score: 99,
          waarom: "12 nieuwe woningen.", woningen: 12, datum: latest, lat: 51.56, lon: 5.09, afstandKm: 0.4 }),
        Object.assign({}, base0, { id: "test-ververst-adres", titel: "Verleende omgevingsvergunning na het verversen, Burg. van de Mortelplein 118A, 5037 PL Tilburg", fase: "Verleend" }),
      ].concat(data.berichten);
    }
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
  });
  await page.route("**/data/regio-*.json", function (route) {
    var name = /\/data\/(regio-[a-z-]+\.json)/.exec(route.request().url())[1];
    served.regio.push(name);
    if (served.fail || served.failRegion) return route.abort("connectionfailed");
    var file = JSON.parse(JSON.stringify(fixture.bestanden[name]));
    if (served.version && name === REGION_FILE) {
      var goes = file.berichten.filter(function (item) { return item.gemeente === "Goes" && item.klasse === "ontwikkellocatie"; })[0];
      file.berichten.unshift(Object.assign({}, goes, { id: "test-ververst-regio", titel: "Aanvraag omgevingsvergunning, nieuw in de regio na het verversen, Goes", score: 97 }));
    }
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(file) });
  });

  function requests() { return { berichten: served.berichten, gebied: served.gebied, regio: served.regio.slice(), pdok: pdok.length }; }
  function show() {
    return page.evaluate(function () {
      function text(id) { return document.getElementById(id).textContent; }
      return {
        hash: location.hash, updated: text("updated"), tiles: [].map.call(document.querySelectorAll(".tile b"), function (node) { return node.textContent; }),
        count: text("result-count"), cards: [].map.call(document.querySelectorAll("#list .card"), function (node) { return node.getAttribute("data-id"); }),
        open: [].map.call(document.querySelectorAll("#list .card:has(details[open])"), function (node) { return node.getAttribute("data-id"); }),
        zoek: document.getElementById("zoek").value, type: document.getElementById("f-type").value, filtersOpen: !document.getElementById("filters").hidden,
        line: document.getElementById("regio-regel").hidden ? null : text("regio-regel"),
        pressed: [].map.call(document.querySelectorAll('#regios .regio[aria-pressed="true"]'), function (node) { return node.firstChild.textContent; }),
        adres: text("adres-naam"), adresVisible: !document.getElementById("adres-uitkomst").hidden,
        bag: text("adres-bag"), perceel: text("adres-perceel"),
        pubs: [].map.call(document.querySelectorAll("#adres-publicaties .pub"), function (node) { return node.getAttribute("data-id"); }),
        searched: (document.querySelector("#adres-publicaties .bronregel") || {}).textContent || "",
        loadError: !document.getElementById("load-error").hidden, scope: text("scope"),
      };
    });
  }
  function forward(minutes) { return page.evaluate(function (ms) { window.__vooruit += ms; }, minutes * 60000); }
  /* The app comes back into view. Waits until it has fetched and shown what it wanted to fetch. */
  async function backInView(expectFetch) {
    var before = served.berichten;
    await page.evaluate(function () { document.dispatchEvent(new Event("visibilitychange")); });
    if (expectFetch) await page.waitForFunction(function () { return true; }, null, { timeout: 100 }).catch(function () {});
    for (var i = 0; i < 40 && expectFetch && served.berichten === before; i++) await page.waitForTimeout(50);
    await page.waitForTimeout(400); // the answers are played back at once; this is for the page to draw
    return { state: await show(), requests: requests() };
  }

  await page.goto(base + "/index.html");
  await page.waitForSelector("#list .card");
  // What the user sets: a region, a search, a filter, an opened card, and an address.
  await page.click("#tab-gebied");
  await page.click('#regios .regio:has-text("' + REGION + '")');
  await page.waitForSelector('#regios .regio[aria-pressed="true"]');
  await page.click("#tab-berichten");
  await page.waitForSelector("#view-berichten:not([hidden])");
  await page.click("#filter-toggle");
  await page.selectOption("#f-type", "vergunning");
  await page.fill("#zoek", "Goes");
  await page.waitForFunction(function () { return /^1 ontwikkellocatie/.test(document.getElementById("result-count").textContent); });
  await page.click("#list .card summary");
  await page.waitForSelector("#list .card details[open]");
  await page.click("#tab-adres");
  await page.fill("#adres-zoek", adres.typed);
  await page.waitForSelector("#adres-suggesties .suggestie");
  await page.click("#adres-suggesties .suggestie");
  await page.waitForFunction(function () { return !document.getElementById("adres-uitkomst").hidden && !document.querySelector("#adres-uitkomst .bezig"); });
  result.before = { state: await show(), requests: requests() };

  // --- Back in view within fifteen minutes: nothing is fetched.
  await forward(14);
  result.early = await backInView(false);

  // --- Back in view after more than fifteen minutes, and a later run has come in.
  await forward(2);
  served.version = 1;
  result.after = await backInView(true);

  // --- Straight away again: it is not time yet.
  result.atOnce = await backInView(false);

  // --- More than fifteen minutes later with the same run: fetched, and nothing changes.
  await forward(16);
  result.sameRun = await backInView(true);

  // --- No connection: everything stays, no error on the page; the next time tries again at once.
  await forward(16);
  served.fail = true;
  result.noConnection = await backInView(true);
  served.fail = false;
  served.version = 2;
  result.connectionBack = await backInView(true);

  // --- A later run, but the file of the chosen region does not come: the region stays with what it had.
  await forward(16);
  served.version = 3;
  served.failRegion = true;
  result.regionDown = await backInView(true);
  served.failRegion = false;

  // --- And the page behind the tab Berichten, to see the search and the opened card after all of it.
  await page.click("#tab-berichten");
  await page.waitForSelector("#view-berichten:not([hidden])");
  result.end = await show();
  result.later = LATER;
  result.errors = errors;
  await context.close();

  // --- The small map: where every text stands, with the data of the site itself.
  result.radar = {};
  for (var width of [375, 320]) {
    context = await browser.newContext({ viewport: { width: width, height: 812 }, locale: "nl-NL", timezoneId: "Europe/Amsterdam", serviceWorkers: "block" });
    page = await context.newPage();
    await page.route(/^https:\/\/fonts\./, function (route) { route.fulfill({ status: 200, contentType: "text/css", body: "" }); });
    await page.goto(base + "/index.html#gebied");
    await page.waitForSelector("#radar circle.centre");
    result.radar[width] = await page.evaluate(function () {
      var svg = document.getElementById("radar");
      function box(node) { var b = node.getBoundingClientRect(); return { l: b.left, t: b.top, r: b.right, b: b.bottom }; }
      function hit(a, b) { return a.l < b.r && b.l < a.r && a.t < b.b && b.t < a.b; }
      var texts = [].map.call(svg.querySelectorAll("text"), function (node) {
        return { text: node.textContent, kind: node.getAttribute("class") || "", krap: node.hasAttribute("data-krap"), box: box(node) };
      });
      var dots = [].map.call(svg.querySelectorAll("circle.p-ontwikkellocatie, circle.p-onzeker, circle.centre"), box);
      var frame = box(svg), overlaps = [], behind = [], outside = [];
      texts.forEach(function (a, index) {
        texts.slice(index + 1).forEach(function (b) { if (!a.krap && !b.krap && hit(a.box, b.box)) overlaps.push(a.text + " over " + b.text); });
        if (a.kind === "ring-label" && !a.krap && dots.some(function (dot) { return hit(a.box, dot); })) behind.push(a.text);
        if (a.box.l < frame.l || a.box.r > frame.r || a.box.t < frame.t || a.box.b > frame.b) outside.push(a.text);
      });
      return { width: Math.round(frame.r - frame.l), overlaps: overlaps, behind: behind, outside: outside, dots: dots.length - 1,
        rings: texts.filter(function (t) { return t.kind === "ring-label"; }).map(function (t) { return t.text; }),
        towns: texts.filter(function (t) { return t.kind === "town"; }).map(function (t) { return t.text; }),
        krap: texts.filter(function (t) { return t.krap; }).map(function (t) { return t.text; }),
        overflow: document.documentElement.scrollWidth - window.innerWidth };
    });
    await context.close();
  }
  return result;
};
