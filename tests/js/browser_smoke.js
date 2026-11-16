/* Opens the app in a real browser at phone size and reports what the page shows, as JSON.
   Usage: node browser_smoke.js <base url>. Needs Playwright; the Python test skips without it.
   The base url may be the live site: the report includes the data the page loaded, and the service
   worker is kept out so that every request is seen. */
"use strict";
var chromium = require("playwright").chromium;
var SEEN = "tilburg-signalen.gezien";

(async function () {
  var base = process.argv[2], errors = [], result = { tiles: {} };
  var browser = await chromium.launch();

  async function open(width, changeData) {
    var context = await browser.newContext({ viewport: { width: width, height: 844 }, locale: "nl-NL", timezoneId: "Europe/Amsterdam", serviceWorkers: "block" });
    var page = await context.newPage();
    page.on("console", function (message) { if (message.type() === "error") errors.push(message.text()); });
    page.on("pageerror", function (error) { errors.push(error.message); });
    // Only the app itself: the test must not depend on the font service.
    await page.route(/^https:\/\/fonts\./, function (route) { route.fulfill({ status: 200, contentType: "text/css", body: "" }); });
    if (changeData) {
      await page.route("**/data/berichten.json", async function (route) {
        var data = await (await route.fetch()).json();
        changeData(data);
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
      });
    }
    await page.goto(base + "/index.html");
    await page.waitForSelector("#list .card");
    return page;
  }
  function cards(page, selector) {
    return page.$$eval(selector + " .card", function (nodes) {
      return nodes.map(function (node) {
        return {
          rank: node.querySelector(".rank b").textContent,
          why: node.querySelector(".why").textContent,
          firstText: node.querySelector(".card-main").firstElementChild.className,
          isNew: node.classList.contains("is-new"),
          klasse: node.className.replace(/.*is-(ontwikkellocatie|onzeker|weggefilterd).*/, "$1"),
          links: Array.from(node.querySelectorAll(".links a")).map(function (a) { return a.href; }),
        };
      });
    });
  }
  function overflow(page) { return page.evaluate(function () { return document.documentElement.scrollWidth - window.innerWidth; }); }
  function badge(page) { return page.$eval("#onzeker-nieuw", function (node) { return node.hidden ? null : node.textContent; }); }
  function tiles(page) {
    return page.$$eval(".tile", function (nodes) {
      return nodes.map(function (node) {
        var label = node.querySelector("span"), tops = Array.from(label.getClientRects()).map(function (box) { return Math.round(box.top); });
        var number = node.querySelector("b").getBoundingClientRect(), mark = node.querySelector(".badge");
        var box = mark && !mark.hidden ? mark.getBoundingClientRect() : null;
        return { label: label.textContent, lines: tops.filter(function (top, i) { return tops.indexOf(top) === i; }).length,
          height: Math.round(node.getBoundingClientRect().height), badgeOverNumber: !!box && box.left < number.right && box.bottom > number.top };
      });
    });
  }
  function pressed(page) { return page.$eval('.tile[aria-pressed="true"]', function (node) { return node.id; }); }

  // --- First visit at 390 px
  var page = await open(390);
  result.first = await cards(page, "#list");
  result.count = await page.textContent("#result-count");
  result.brief = await page.textContent("#brief-title");
  for (var name of ["ranglijst", "nieuw", "onzeker"]) result.tiles[name] = await page.textContent("#tile-" + name + " b");
  result.overflow = await overflow(page);
  result.updated = await page.textContent("#updated");
  result.themeColor = await page.$eval('meta[name="theme-color"]', function (node) { return node.content; });
  result.barColor = await page.$eval(".masthead", function (node) { return getComputedStyle(node).backgroundColor; });
  result.data = await page.evaluate(function () {
    return fetch("data/berichten.json", { cache: "no-cache" }).then(function (r) { return r.json(); }).then(function (d) {
      return { bijgewerkt: d.bijgewerkt, drempelPerceelM2: d.drempelPerceelM2, berichten: d.berichten.map(function (i) {
        return { id: i.id, klasse: i.klasse, score: i.score, datum: i.datum, waarom: i.waarom, gemeente: i.gemeente };
      }) };
    });
  });
  result.tileShapes = await tiles(page);
  result.badgeFirst = await badge(page);
  result.mark = await page.$$eval(".masthead svg.mark path", function (paths) { return paths.length; });
  result.switchVisible = await page.isVisible("#toon-weg") && !(await page.isVisible("#filters"));
  await page.click("#list .card summary");
  await page.click("#more");
  var all = await cards(page, "#list");
  result.all = all.map(function (card) { return card.rank; });
  result.newCards = all.filter(function (card) { return card.isNew; }).length;
  result.openAfterShowAll = await page.$$eval("#list details[open]", function (nodes) { return nodes.length; });
  result.linkHeight = await page.$eval("#list details[open] .links a", function (a) { return a.getBoundingClientRect().height; });
  result.toggleHeight = await page.$eval("#list summary", function (node) { return node.getBoundingClientRect().height; });

  await page.click("#tile-onzeker");
  result.onzeker = (await cards(page, "#list")).length;
  await page.click("#brand");
  result.afterBrand = await pressed(page);

  await page.click("#toon-weg");
  var removed = await cards(page, "#removed");
  result.removed = removed.length;
  result.removedRank = removed[0].rank;
  await page.fill("#zoek", "zzzzqqqq");
  result.removedWhileSearching = (await cards(page, "#removed")).length;
  await page.click("#filter-toggle");
  await page.click("#filter-reset");
  result.switchAfterReset = await page.isChecked("#toon-weg");
  await page.click("#toon-weg");

  await page.selectOption("#f-sort", "datum");
  result.dayHeads = await page.$$eval("#list .day", function (nodes) { return nodes.map(function (node) { return node.textContent; }); });
  result.dayCards = (await cards(page, "#list")).length;
  await page.click("#filter-reset");

  await page.goto(base + "/index.html#gebied");
  result.gemeente = await page.$eval("#gemeenten .gemeente strong", function (node) { return node.textContent; });
  await page.click("#gemeenten .gemeente");
  result.gemeenteHash = await page.evaluate(function () { return location.hash; });
  result.gemeenteFilter = await page.$eval("#f-gemeente", function (node) { return node.value; });
  result.gemeenteCount = await page.textContent("#result-count");
  result.gemeenteRanks = (await cards(page, "#list")).map(function (card) { return card.rank; });
  result.rules = await page.$$eval("#regels li", function (nodes) { return nodes.map(function (node) { return node.textContent; }); });

  // --- A later visit: only one unsure notice is new, then nothing is.
  var unsureId = await page.evaluate(function (key) {
    var seen = JSON.parse(localStorage.getItem(key));
    Object.keys(seen).forEach(function (id) { seen[id] = 1; });
    var card = null;
    return fetch("data/berichten.json").then(function (r) { return r.json(); }).then(function (data) {
      card = data.berichten.filter(function (item) { return item.klasse === "onzeker"; })[0];
      if (card) delete seen[card.id];
      localStorage.setItem(key, JSON.stringify(seen));
      return card ? card.id : null;
    });
  }, SEEN);
  await page.goto(base + "/index.html#berichten");
  await page.reload();
  await page.waitForSelector("#list .card");
  result.hasUnsure = unsureId !== null;
  result.briefLater = await page.textContent("#brief-title");
  result.briefSubLater = await page.textContent("#brief-sub");
  result.badgeLater = await badge(page);
  await page.click("#tile-nieuw");
  result.newUnsure = await cards(page, "#list");
  result.newUnsureHead = await page.$$eval("#list .day", function (nodes) { return nodes.map(function (node) { return node.textContent; }); });

  await page.reload(); // the unsure notice was stored as seen just now; make it old as well
  await page.evaluate(function (key) {
    var seen = JSON.parse(localStorage.getItem(key));
    Object.keys(seen).forEach(function (id) { seen[id] = 1; });
    localStorage.setItem(key, JSON.stringify(seen));
  }, SEEN);
  await page.reload();
  await page.waitForSelector("#list .card");
  await page.click("#tile-nieuw");
  result.emptyTitle = await page.textContent("#list .empty-title");
  result.badgeNone = await badge(page);
  await page.waitForFunction(function () {
    var images = Array.from(document.querySelectorAll("#list .empty-art img"));
    return images.length > 0 && images.every(function (image) { return image.complete; });
  });
  result.emptyArt = await page.$$eval("#list .empty-art img", function (images) {
    return images.filter(function (image) { return image.complete && image.naturalWidth > 0 && image.offsetParent !== null; }).length;
  });
  await page.context().close();

  // --- The narrowest phone: nothing wider than the screen, no date broken over two lines.
  page = await open(320);
  await page.click("#more");
  await page.click("#toon-weg");
  result.narrowOverflow = await overflow(page);
  result.narrowTileShapes = await tiles(page);
  result.countLines = await page.$eval("#result-count", function (node) {
    var range = document.createRange(); range.selectNodeContents(node);
    var tops = Array.from(range.getClientRects()).map(function (box) { return Math.round(box.top); });
    var last = tops[tops.length - 1], text = node.textContent, width = node.getBoundingClientRect().width;
    var lastLine = Array.from(range.getClientRects()).filter(function (box) { return Math.round(box.top) === last; }).reduce(function (sum, box) { return sum + box.width; }, 0);
    return { lines: tops.filter(function (top, i) { return tops.indexOf(top) === i; }).length, lastShare: lastLine / width, text: text };
  });
  result.brokenDates = await page.$$eval(".card .meta .date, .card .meta .dist", function (nodes) {
    return nodes.filter(function (node) {
      // on more than one line: boxes at different heights (the separator after it is a box of its own)
      var tops = Array.from(node.getClientRects()).map(function (box) { return Math.round(box.top); });
      return tops.some(function (top) { return top !== tops[0]; });
    }).length;
  });
  result.chipsOverToggle = await page.$$eval(".card summary", function (nodes) {
    return nodes.filter(function (node) {
      var toggle = node.querySelector(".toggle").getBoundingClientRect();
      return Array.from(node.querySelectorAll(".chip")).some(function (chip) {
        var box = chip.getBoundingClientRect();
        return box.right > toggle.left + 0.5 && box.bottom > toggle.top && box.top < toggle.bottom;
      });
    }).length;
  });
  await page.context().close();

  // --- Gaps in the data are reported.
  page = await open(390, function (data) {
    var latest = data.berichten.reduce(function (day, item) { return item.datum > day ? item.datum : day; }, "");
    data.onvolledigeDagen = [{ datum: latest, aantal: 4, verwacht: 2097 }];
    data.bronnen[0].status = "fout";
    data.ophaalfouten = { tekst: 2, perceel: 1, insolventie: 3 };
    data.bijgewerkt = new Date(Date.now() - 30 * 3600 * 1000).toISOString(); // a refresh was skipped
  });
  result.updatedStale = await page.textContent("#updated");
  result.staleDay = await page.evaluate(function () { return new Date(Date.now() - 30 * 3600 * 1000).getDate(); });
  result.notices = await page.$$eval("#notices .stale", function (nodes) { return nodes.map(function (node) { return node.textContent; }); });
  await page.click("#filter-toggle");
  await page.selectOption("#f-sort", "datum");
  result.gapHead = await page.$eval("#list .day", function (node) { return node.textContent; });
  await page.context().close();

  result.errors = errors;
  await browser.close();
  process.stdout.write(JSON.stringify(result));
})().catch(function (error) { console.error(error); process.exit(1); });
