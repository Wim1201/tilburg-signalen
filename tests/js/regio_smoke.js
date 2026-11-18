/* The region choice on the tab "Gebied" in a real browser, for browser_smoke.js, at the width of
   the narrowest phone. Works with the data the page itself loads: the core, and per region the file
   the app reads when that region is chosen. What those files hold is reported next to what the page
   showed, and the Python test compares the two. With data from before the regions nothing is on
   offer; the report then says so.

   With `options.fixture` (regio_ongelezen.json) the same walk is done in a fixed situation: the
   overview of the regions and the region files are played back from the fixture, in which regions
   have notices whose text still waits. The site in the repository has none of those, the live site
   often has; this way the tests before publishing meet them too. */
"use strict";

module.exports = async function (browser, base, options) {
  var result = {}, errors = [], fixture = options && options.fixture;
  var context = await browser.newContext({ viewport: { width: 320, height: 844 }, locale: "nl-NL", timezoneId: "Europe/Amsterdam", serviceWorkers: "block" });
  var page = await context.newPage();
  page.on("console", function (message) { if (message.type() === "error") errors.push(message.text()); });
  page.on("pageerror", function (error) { errors.push(error.message); });
  await page.route(/^https:\/\/fonts\./, function (route) { route.fulfill({ status: 200, contentType: "text/css", body: "" }); });
  if (fixture) {
    // The core stays as the site has it; only what it says about the regions comes from the fixture.
    await page.route("**/data/berichten.json", async function (route) {
      var data = await (await route.fetch()).json();
      data.regios = fixture.regios;
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
    });
    await page.route("**/data/regio-*.json", function (route) {
      var file = fixture.bestanden[/\/data\/(regio-[a-z-]+\.json)/.exec(route.request().url())[1]];
      route.fulfill(file ? { status: 200, contentType: "application/json", body: JSON.stringify(file) } : { status: 404, body: "" });
    });
  }

  function overflow() { return page.evaluate(function () { return document.documentElement.scrollWidth - window.innerWidth; }); }
  /* The line under the name of the app, and whether it fits: on how many lines it stands. */
  function scope() {
    return page.$eval("#scope", function (node) {
      var range = document.createRange();
      range.selectNodeContents(node);
      var tops = [].map.call(range.getClientRects(), function (box) { return Math.round(box.top); });
      return { text: node.textContent, lines: tops.filter(function (top, index) { return tops.indexOf(top) === index; }).length,
        right: Math.round(node.getBoundingClientRect().right), updatedLeft: Math.round(document.getElementById("updated").getBoundingClientRect().left),
        name: document.querySelector(".masthead h1").textContent };
    });
  }
  async function berichten() {
    return {
      scope: (await scope()).text,
      // Next to the morning line: that it is about the core, when the lists show one region alone.
      kernNote: await page.$eval("#brief-kern", function (node) { return node.hidden ? null : node.textContent; }),
      count: await page.textContent("#result-count"), brief: await page.textContent("#brief-title"),
      tiles: await page.$$eval(".tile b", function (nodes) { return nodes.map(function (node) { return node.textContent; }); }),
      cards: await page.$$eval("#list .card", function (nodes) { return nodes.length; }),
      line: await page.$eval("#regio-regel", function (node) { return node.hidden ? null : node.firstChild.textContent.trim(); }),
      // The choice of what the lists show: everything together, the core alone or one region alone.
      toon: await page.$$eval("#regio-regel .keuzes button", function (nodes) {
        return nodes.map(function (node) { var box = node.getBoundingClientRect(); return { label: node.textContent, pressed: node.getAttribute("aria-pressed") === "true", height: Math.round(box.height), right: Math.round(box.right) }; });
      }),
      kmMax: await page.$eval("#f-km", function (node) { return node.max; }), kmOut: await page.textContent("#f-km-out"),
      gemeenten: await page.$$eval("#f-gemeente option", function (nodes) { return nodes.length - 1; }),
      removed: await page.textContent("#weg-aantal"),
    };
  }
  async function gebied() {
    return {
      scope: await scope(),
      buttons: await page.$$eval("#regios .regio", function (nodes) {
        return nodes.map(function (node) {
          var box = node.getBoundingClientRect();
          return { name: node.firstChild.textContent, sub: node.querySelector("span").textContent, pressed: node.getAttribute("aria-pressed"),
            height: Math.round(box.height), right: Math.round(box.right), left: Math.round(box.left) };
        });
      }),
      offered: await page.isVisible("#regios"),
      hint: await page.$eval("#regio-uitleg", function (node) { return node.hidden ? null : node.textContent; }),
      intro: await page.textContent("#gebied-intro"),
      rows: await page.$$eval("#gemeenten .gemeente", function (nodes) {
        return nodes.map(function (node) {
          return { name: node.querySelector("strong").textContent, chip: node.querySelector(".chip").textContent, towns: node.querySelector(".towns").textContent,
            counts: node.querySelector(".meta span:not(.chip)").textContent, right: Math.round(node.getBoundingClientRect().right) };
        });
      }),
      dots: await page.$$eval("#radar circle.p-ontwikkellocatie, #radar circle.p-onzeker", function (nodes) { return nodes.length; }),
      overflow: await overflow(),
    };
  }

  // The notices under Onzeker with the reason on each card: there the ones that wait for their text show.
  async function unsure() {
    await page.click("#tile-onzeker");
    await page.waitForSelector('#tile-onzeker[aria-pressed="true"]');
    if (await page.isVisible("#more")) await page.click("#more");
    var seen = { count: await page.textContent("#result-count"),
      notices: await page.$$eval("#notices .stale", function (nodes) { return nodes.map(function (node) { return node.textContent; }); }),
      reasons: await page.$$eval("#list .card .why", function (nodes) { return nodes.map(function (node) { return node.textContent; }); }),
      overflow: await overflow() };
    await page.click("#tile-ranglijst");
    await page.waitForSelector('#tile-ranglijst[aria-pressed="true"]');
    return seen;
  }

  var asked = [];
  page.on("request", function (request) { var found = /\/data\/(regio-[a-z-]+\.json)/.exec(request.url()); if (found) asked.push(found[1]); });
  await page.goto(base + "/index.html");
  await page.waitForSelector("#list .card");
  result.askedByThePage = asked.slice(); // opening the app reads no region
  result.data = await page.evaluate(function () {
    function json(path) { return fetch(path).then(function (r) { return r.json(); }); }
    function slim(regio) { return function (i) { return { id: i.id, klasse: i.klasse, regio: regio || i.regio || "kern", gemeente: i.gemeente, afstandKm: i.afstandKm, datum: i.datum, fase: i.fase, score: i.score, woningen: i.woningen, type: i.type }; }; }
    return Promise.all([json("data/berichten.json"), json("data/gebied.json")]).then(function (both) {
      var overview = (both[0].regios || []).filter(function (regio) { return regio.bestand; });
      return Promise.all(overview.map(function (regio) { return json("data/" + regio.bestand); })).then(function (files) {
        var berichten = both[0].berichten.map(slim());
        files.forEach(function (file, index) { berichten = berichten.concat(file.berichten.map(slim(overview[index].naam))); });
        return { straalKm: both[0].straalKm, centrum: both[0].centrum.naam, regios: overview.map(function (regio) { return regio.naam; }), overview: overview,
          core: both[0].berichten.length, inFiles: files.map(function (file) { return file.berichten.length; }),
          gemeenten: both[1].gemeenten.map(function (g) { return { naam: g.naam, land: g.land, regio: g.regio || "kern", buitenStraal: g.buitenStraal || null, dekking: g.dekking, opmerking: g.opmerking || null }; }),
          berichten: berichten };
      });
    });
  });
  asked.length = 0; // the test itself read the files just now
  function pressed(name, on) { return page.waitForSelector('#regios .regio[aria-pressed="' + on + '"]:has-text("' + name + '")'); }
  result.morning = await berichten();
  // The filter "Fase": three steps and every phase by itself.
  await page.click("#filter-toggle");
  result.fase = { label: await page.$eval('label[for="f-fase"]', function (node) { return node.firstChild.textContent.trim(); }),
    groups: await page.$$eval("#f-fase optgroup", function (groups) {
      return groups.map(function (group) { return { label: group.label, options: [].map.call(group.children, function (option) { return { value: option.value, label: option.textContent }; }) }; });
    }), counts: {}, cards: {} };
  var steps = ["trede:vroeg", "trede:midden", "trede:laat", "trede:overig"];
  for (var f = 0; f < steps.length; f++) {
    await page.selectOption("#f-fase", steps[f]);
    result.fase.counts[steps[f]] = await page.textContent("#result-count");
    if (await page.isVisible("#more")) await page.click("#more");
    result.fase.cards[steps[f]] = await page.$$eval("#list .card", function (nodes) { return nodes.map(function (node) { return node.getAttribute("data-id"); }); });
  }
  result.fase.overflow = await overflow();
  await page.click("#filter-reset");
  await page.click("#filter-toggle");
  result.afterFase = await berichten();
  await page.click("#tab-gebied");
  await page.waitForSelector("#view-gebied:not([hidden])");
  result.start = await gebied();
  if (!result.start.buttons.length) { // data from before the regions
    result.errors = errors;
    await context.close();
    return result;
  }

  // --- One region with the core. The region that adds most municipalities, so the list clearly grows.
  var names = result.start.buttons.map(function (button) { return button.name; });
  var first = result.data.regios.filter(function (name) { return names.indexOf(name) !== -1; }).sort(function (a, b) {
    function size(name) { return result.data.gemeenten.filter(function (g) { return g.regio === name; }).length; }
    return size(b) - size(a);
  })[0];
  result.first = first;
  await page.click('#regios .regio:has-text("' + first + '")');
  await pressed(first, true);
  result.askedForOne = asked.slice();
  result.one = await gebied();
  // A municipality of the region: tapping it shows its notices on the tab Berichten.
  var regionRow = result.one.rows.filter(function (row) { return row.chip === first; })[0];
  result.tapped = regionRow ? regionRow.name : null;
  if (regionRow) {
    await page.click('#gemeenten .gemeente:has(strong:text-is("' + regionRow.name + '"))');
    await page.waitForSelector("#view-berichten:not([hidden])");
    result.tap = { hash: await page.evaluate(function () { return location.hash; }), filter: await page.$eval("#f-gemeente", function (node) { return node.value; }),
      count: await page.textContent("#result-count"), cards: await page.$$eval("#list .card", function (nodes) { return nodes.length; }),
      distances: await page.$$eval("#list .card .dist", function (nodes) { return nodes.map(function (node) { return node.textContent; }); }),
      overflow: await overflow() };
    await page.click("#filter-reset");
  } else {
    await page.click("#tab-berichten");
    await page.waitForSelector("#view-berichten:not([hidden])");
  }
  result.withOne = await berichten();
  result.withOneOverflow = await overflow();
  await page.click("#more");
  result.withOneAllRanks = await page.$$eval("#list .card .rank b", function (nodes) { return nodes.map(function (node) { return node.textContent; }); });
  result.withOneAllIds = await page.$$eval("#list .card", function (nodes) { return nodes.map(function (node) { return node.getAttribute("data-id"); }); });
  result.withOneAllOverflow = await overflow();
  if (fixture) result.unsureWithOne = await unsure();

  // --- What the lists show: the region alone, the core alone, and together again. The region stays chosen.
  async function choose(label) {
    await page.click('#regio-regel .keuzes button:text-is("' + label + '")');
    await page.waitForSelector('#regio-regel .keuzes button[aria-pressed="true"]:text-is("' + label + '")');
    var seen = await berichten();
    seen.overflow = await overflow();
    if (await page.isVisible("#more")) await page.click("#more");
    seen.ranks = await page.$$eval("#list .card .rank b", function (nodes) { return nodes.map(function (node) { return node.textContent; }); });
    seen.ids = await page.$$eval("#list .card", function (nodes) { return nodes.map(function (node) { return node.getAttribute("data-id"); }); });
    return seen;
  }
  result.onlyRegion = await choose("Alleen " + first);
  result.onlyCore = await choose("Alleen de kern");
  result.together = await choose("Samen");
  if (fixture) { // a search stays when the choice changes
    await page.fill("#zoek", "Goes");
    result.searchTogether = { zoek: await page.inputValue("#zoek"), count: await page.textContent("#result-count") };
    var searched = await choose("Alleen " + first);
    result.searchOnlyRegion = { zoek: await page.inputValue("#zoek"), count: searched.count };
    searched = await choose("Alleen de kern");
    result.searchOnlyCore = { zoek: await page.inputValue("#zoek"), count: searched.count };
    await page.fill("#zoek", "");
    await choose("Samen");
  }
  await page.click("#tab-gebied");
  await page.waitForSelector("#view-gebied:not([hidden])");
  result.oneAfterChoice = await gebied(); // the tab Gebied still has the region chosen
  await page.click("#tab-berichten");
  await page.waitForSelector("#view-berichten:not([hidden])");

  // --- Back to the core: the region is switched off where it was switched on, on the tab Gebied.
  await page.click("#tab-gebied");
  await page.waitForSelector("#view-gebied:not([hidden])");
  await page.click('#regios .regio:has-text("' + first + '")');
  await pressed(first, false);
  result.backGebied = await gebied();
  await page.click("#tab-berichten");
  await page.waitForSelector("#view-berichten:not([hidden])");
  result.back = await berichten();
  await page.click("#tab-gebied");
  await page.waitForSelector("#view-gebied:not([hidden])");

  // --- Every region at once, then open the app again: it starts with the core.
  for (var i = 0; i < names.length; i++) {
    await page.click('#regios .regio:has-text("' + names[i] + '")');
    await pressed(names[i], true);
  }
  result.askedForAll = asked.slice(); // a region that was read is not read again
  result.all = await gebied();
  await page.click("#tab-berichten");
  await page.waitForSelector("#view-berichten:not([hidden])");
  result.withAll = await berichten();
  if (fixture) result.unsureWithAll = await unsure();
  result.storage = await page.evaluate(function () { return Object.keys(localStorage); });
  await page.reload();
  await page.waitForSelector("#list .card");
  result.reopened = await berichten();
  await page.click("#tab-gebied");
  await page.waitForSelector("#view-gebied:not([hidden])");
  result.reopenedGebied = await gebied();
  // Chosen in the opposite order: the line under the name keeps the order of the buttons.
  for (var j = names.length - 1; j >= 0; j--) {
    await page.click('#regios .regio:has-text("' + names[j] + '")');
    await pressed(names[j], true);
  }
  result.reversed = await gebied();

  result.errors = errors;
  await context.close();
  if (fixture) return result; // the two situations below change the data themselves

  // --- The file of a region does not come: the region is not chosen and the tab says so.
  context = await browser.newContext({ viewport: { width: 320, height: 844 }, locale: "nl-NL", timezoneId: "Europe/Amsterdam", serviceWorkers: "block" });
  page = await context.newPage();
  var failures = [];
  page.on("pageerror", function (error) { failures.push(error.message); });
  await page.route(/^https:\/\/fonts\./, function (route) { route.fulfill({ status: 200, contentType: "text/css", body: "" }); });
  await page.route("**/data/regio-*.json", function (route) { route.abort("connectionfailed"); });
  await page.goto(base + "/index.html#gebied");
  await page.waitForSelector("#regios .regio");
  await page.click('#regios .regio:has-text("' + first + '")');
  await page.waitForSelector("#regio-uitleg.stale");
  result.fileDown = { message: await page.textContent("#regio-uitleg"), overflow: await overflow(), errors: failures,
    pressed: await page.$$eval('#regios .regio[aria-pressed="true"]', function (nodes) { return nodes.length; }),
    rows: await page.$$eval("#gemeenten .gemeente", function (nodes) { return nodes.length; }) };
  await page.click("#tab-berichten");
  await page.waitForSelector("#view-berichten:not([hidden])");
  result.fileDown.count = await page.textContent("#result-count");
  result.fileDown.line = await page.$eval("#regio-regel", function (node) { return !node.hidden; });
  await context.close();

  // --- A region that still misses texts, while the core misses nothing: the morning screen says nothing,
  // the region says it on its button, and the tab Berichten says it once the region is chosen.
  context = await browser.newContext({ viewport: { width: 320, height: 844 }, locale: "nl-NL", timezoneId: "Europe/Amsterdam", serviceWorkers: "block" });
  page = await context.newPage();
  var missingErrors = [];
  page.on("pageerror", function (error) { missingErrors.push(error.message); });
  await page.route(/^https:\/\/fonts\./, function (route) { route.fulfill({ status: 200, contentType: "text/css", body: "" }); });
  await page.route("**/data/berichten.json", async function (route) {
    var data = await (await route.fetch()).json();
    data.ophaalfouten = { tekst: 0, perceel: 0, insolventie: 0 };
    data.regios.forEach(function (regio) { regio.ongelezen = regio.naam === first ? 146 : 0; regio.mislukt = regio.naam === first ? 20 : 0; });
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
  });
  function shown() { return page.$$eval("#notices .stale", function (nodes) { return nodes.map(function (node) { return node.textContent; }); }); }
  await page.goto(base + "/index.html");
  await page.waitForSelector("#list .card");
  result.missing = { morning: await shown() };
  await page.click("#tab-gebied");
  await page.waitForSelector("#regios .regio");
  result.missing.buttons = await page.$$eval("#regios .regio", function (nodes) {
    return nodes.map(function (node) { var box = node.getBoundingClientRect(); return { name: node.firstChild.textContent, sub: node.querySelector("span").textContent, right: Math.round(box.right) }; });
  });
  result.missing.buttonOverflow = await overflow();
  await page.click('#regios .regio:has-text("' + first + '")');
  await page.waitForSelector('#regios .regio[aria-pressed="true"]');
  await page.click("#tab-berichten");
  await page.waitForSelector("#view-berichten:not([hidden])");
  result.missing.chosen = await shown();
  result.missing.chosenOverflow = await overflow();
  // The core alone, with the region still chosen: what the region misses is not said then.
  await page.click('#regio-regel .keuzes button:text-is("Alleen de kern")');
  await page.waitForSelector('#regio-regel .keuzes button[aria-pressed="true"]:text-is("Alleen de kern")');
  result.missing.onlyCore = await shown();
  await page.click("#tab-gebied");
  await page.click('#regios .regio[aria-pressed="true"]');
  await page.waitForSelector("#regio-regel", { state: "hidden" });
  await page.click("#tab-berichten");
  await page.waitForSelector("#view-berichten:not([hidden])");
  result.missing.back = await shown();
  result.missing.errors = missingErrors;
  await context.close();
  return result;
};
