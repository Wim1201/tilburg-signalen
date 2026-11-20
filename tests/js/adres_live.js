/* The tab "Adres" against the real registers of PDOK, at the width of the narrowest phone.
   Usage: node adres_live.js <base url> [map with screenshots]. Not part of the normal test run,
   because it depends on PDOK answering; see tests/test_adres.py (EchteBronnen). Ruimtelijke plannen
   is played back, never asked. Reports per
   address what the page showed, as JSON. Uses HTTPS_PROXY when the machine needs a proxy. */
"use strict";
var chromium = require("playwright").chromium;
var path = require("path");

// Only the public test address and public buildings (town halls and town offices), so that no
// address of a private person is sent to PDOK or stands in the repository.
var ADDRESSES = [
  { typed: "Burg. van de Mortelplein 118a Tilburg", label: "Burgemeester van de Mortelplein 118a, 5037PL Tilburg" },
  // The town hall of Dongen, and a small object with an addition on the same building.
  { typed: "Hoge Ham 62 Dongen", label: "Hoge Ham 62, 5104JJ Dongen" },
  { typed: "Hoge Ham 62-NU01 Dongen", label: "Hoge Ham 62-NU01, Dongen" },
  // The town hall of Goirle.
  { typed: "Oranjeplein 1 Goirle", label: "Oranjeplein 1, 5051LT Goirle" },
  // Outside the core: the notices come from the file of the region (Zeeland, West-Brabant). The
  // town offices of Middelburg and Breda, and in Breda also the part with a house letter.
  { typed: "Kanaalweg 3 Middelburg", label: "Kanaalweg 3, 4337PA Middelburg", regio: "regio-zeeland.json", gemeente: "Middelburg" },
  { typed: "Claudius Prinsenlaan 10 Breda", label: "Claudius Prinsenlaan 10, 4811DJ Breda", regio: "regio-west-brabant.json", gemeente: "Breda" },
  { typed: "Claudius Prinsenlaan 10A Breda", label: "Claudius Prinsenlaan 10A, 4811DJ Breda" },
];

/* A public building has no notices of its own as a rule. So that the search in the file of a region
   is still tested, one made-up notice about each address outside the core is added to the file the
   page reads; the file on disk is not touched. */
function proefbericht(address) {
  return { id: "proef-" + address.regio, bron: "officielebekendmakingen", publicatie: "Gemeenteblad", overheid: address.gemeente, gemeente: address.gemeente,
    type: "vergunning", soort: null, fase: "Aanvraag", datum: "2026-11-16", titel: "Proefbericht: aanvraag omgevingsvergunning, " + address.label,
    omschrijving: null, activiteiten: [], plaats: "", regio: address.regio === "regio-zeeland.json" ? "Zeeland" : "West-Brabant", afstandKm: 30,
    locatieSoort: "gemeente", lat: null, lon: null, reactieTot: null, planId: null, url: "https://zoek.officielebekendmakingen.nl/proef.html", urlTekst: null,
    klasse: "weggefilterd", score: 0, waarom: "Proefbericht.", signalen: [], woningen: null, perceelM2: null };
}

(async function () {
  var base = process.argv[2], shots = process.argv[3], proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
  var browser = await chromium.launch(proxy ? { proxy: { server: proxy, bypass: "127.0.0.1,localhost" } } : {});
  var context = await browser.newContext({ viewport: { width: 320, height: 844 }, deviceScaleFactor: shots ? 2 : 1, locale: "nl-NL", timezoneId: "Europe/Amsterdam", serviceWorkers: "block" });
  var page = await context.newPage(), errors = [], asked = [], regionFiles = [], results = [];
  page.on("pageerror", function (error) { errors.push(error.message); });
  page.on("console", function (message) { if (message.type() === "error") errors.push(message.text()); });
  page.on("request", function (request) {
    var url = request.url();
    if (url.indexOf(base) !== 0 && !/^(data:|blob:|https:\/\/fonts\.)/.test(url)) asked.push(new URL(url).host);
    if (/\/data\/regio-[a-z-]+\.json/.test(url)) regionFiles.push(url.split("/").pop());
  });
  // Ruimtelijke plannen is never asked for real, not even here: its answer is played back as "no
  // plan at this point". The box itself is tested with played-back answers in adres_smoke.js.
  var plans = 0;
  await page.route(/^https:\/\/service\.pdok\.nl\/kadaster\/plu\//, function (route) {
    plans++;
    return route.fulfill({ status: 200, contentType: "text/plain", headers: { "access-control-allow-origin": "*" }, body: "GetFeatureInfo results:\n\n  Search returned no results.\n" });
  });
  await page.route(/\/data\/regio-[a-z-]+\.json$/, async function (route) {
    var file = await (await route.fetch()).json(), name = route.request().url().split("/").pop();
    ADDRESSES.filter(function (address) { return address.regio === name; }).forEach(function (address) { file.berichten.unshift(proefbericht(address)); });
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(file) });
  });
  await page.goto(base + "/index.html#adres");
  await page.waitForSelector("#view-adres:not([hidden])");

  function facts(selector) {
    return page.$$eval(selector + " .feiten", function (lists) {
      return lists.map(function (list) {
        var out = {}, terms = list.querySelectorAll("dt"), values = list.querySelectorAll("dd");
        for (var i = 0; i < terms.length; i++) out[terms[i].textContent] = values[i].textContent;
        return out;
      });
    });
  }

  for (var i = 0; i < ADDRESSES.length; i++) {
    var wanted = ADDRESSES[i], entry = { typed: wanted.typed, label: wanted.label };
    await page.fill("#adres-zoek", "");
    await page.type("#adres-zoek", wanted.typed, { delay: 10 });
    await page.waitForSelector("#adres-suggesties .suggestie", { timeout: 30000 });
    // The suggestions follow the typing; wait until the wanted address is among them.
    var option = page.locator("#adres-suggesties .suggestie", { hasText: wanted.label }).first();
    await option.waitFor({ timeout: 30000 });
    entry.suggestions = await page.$$eval("#adres-suggesties .suggestie", function (nodes) { return nodes.map(function (node) { return node.textContent; }); });
    await option.click();
    await page.waitForFunction(function () { return !document.querySelector("#adres-uitkomst .bezig"); }, null, { timeout: 40000 });
    await page.waitForFunction(function () { var image = document.querySelector(".kaartvlak img"); return !image || image.complete; }, null, { timeout: 40000 });
    entry.name = await page.textContent("#adres-naam");
    entry.sub = await page.textContent("#adres-sub");
    entry.bag = (await facts("#adres-bag"))[0] || null;
    entry.parcels = await facts("#adres-perceel");
    entry.parcelNotes = await page.$$eval("#adres-perceel .bronregel, #adres-perceel .stale", function (nodes) { return nodes.map(function (node) { return node.textContent; }); });
    entry.failed = await page.$$eval("#adres-uitkomst .vak-inhoud > button", function (nodes) { return nodes.length; });
    entry.map = await page.$eval("#adres-perceel", function (box) {
      var image = box.querySelector(".kaartvlak img");
      return { image: !!image && image.naturalWidth > 0, shapes: box.querySelectorAll(".p-perceel").length };
    });
    // The notices of a region arrive a moment after the core was searched.
    await page.waitForTimeout(1500);
    entry.notices = await page.$$eval("#adres-publicaties > .pubs", function (groups) {
      var out = {};
      groups.forEach(function (group) {
        out[group.querySelector(".day").firstChild.textContent] = Array.from(group.querySelectorAll(".pub")).map(function (row) {
          return row.querySelector(".pub-meta").textContent + " | " + row.querySelector(".pub-titel").textContent + " | " +
            Array.from(row.querySelectorAll(".pub-reden")).map(function (p) { return p.textContent; }).join(" ");
        });
      });
      return out;
    });
    entry.searched = await page.$$eval("#adres-publicaties .bronregel", function (nodes) { return nodes.map(function (node) { return node.textContent; }).filter(function (text) { return /^Doorzocht/.test(text); })[0]; });
    entry.regionFiles = regionFiles.splice(0);
    entry.links = await page.$$eval("#adres-energie a, #adres-plan a", function (nodes) { return nodes.map(function (a) { return a.href; }); });
    entry.overflow = await page.evaluate(function () { return document.documentElement.scrollWidth - window.innerWidth; });
    if (shots) await page.screenshot({ path: path.join(shots, "adres-" + (i + 1) + ".png"), fullPage: true });
    results.push(entry);
  }
  await browser.close();
  process.stdout.write(JSON.stringify({ addresses: results, errors: errors, plansPlayedBack: plans, hosts: asked.filter(function (host, i) { return asked.indexOf(host) === i; }).sort() }));
})().catch(function (error) { console.error(error); process.exit(1); });
