/* Opens the app in a real browser at phone size and reports what the page shows, as JSON.
   Usage: node browser_smoke.js <base url>. Needs Playwright; the Python test skips without it. */
"use strict";
var chromium = require("playwright").chromium;

(async function () {
  var base = process.argv[2], errors = [];
  var browser = await chromium.launch();
  var context = await browser.newContext({ viewport: { width: 390, height: 844 }, locale: "nl-NL", timezoneId: "Europe/Amsterdam" });
  var page = await context.newPage();
  page.on("console", function (message) { if (message.type() === "error") errors.push(message.text()); });
  page.on("pageerror", function (error) { errors.push(error.message); });
  // Only the app itself: the test must not depend on the font service.
  await page.route(/^https:\/\/fonts\./, function (route) { route.fulfill({ status: 200, contentType: "text/css", body: "" }); });
  await page.goto(base + "/index.html");
  await page.waitForSelector("#list .card");

  function cards(selector) {
    return page.$$eval(selector + " .card", function (nodes) {
      return nodes.map(function (node) {
        return {
          rank: node.querySelector(".rank b").textContent,
          why: node.querySelector(".why").textContent,
          firstText: node.querySelector(".card-main").firstElementChild.className,
          links: Array.from(node.querySelectorAll(".links a")).map(function (a) { return a.href; }),
        };
      });
    });
  }
  var result = { tiles: {}, overflow: 0 };
  result.first = await cards("#list");
  result.count = await page.textContent("#result-count");
  result.brief = await page.textContent("#brief-title");
  for (var name of ["ranglijst", "nieuw", "onzeker"]) result.tiles[name] = await page.textContent("#tile-" + name + " b");
  result.overflow = await page.evaluate(function () { return document.documentElement.scrollWidth - window.innerWidth; });
  result.mark = await page.$$eval(".masthead svg.mark path", function (paths) { return paths.length; });
  await page.click("#more");
  result.all = (await cards("#list")).map(function (card) { return card.rank; });
  await page.click("#tile-onzeker");
  result.onzeker = (await cards("#list")).length;
  await page.click("#filter-toggle");
  await page.click("#toon-weg");
  result.removed = (await cards("#removed")).length;
  result.removedRank = (await cards("#removed"))[0].rank;
  await page.click("#filter-reset");
  // A later visit on which nothing is new: the empty state with the illustration.
  await page.evaluate(function () {
    var key = "tilburg-signalen.gezien", seen = JSON.parse(localStorage.getItem(key));
    Object.keys(seen).forEach(function (id) { seen[id] = 1; });
    localStorage.setItem(key, JSON.stringify(seen));
  });
  await page.reload();
  await page.waitForSelector("#list .card");
  result.briefLater = await page.textContent("#brief-title");
  await page.click("#tile-nieuw");
  result.emptyTitle = await page.textContent("#list .empty-title");
  await page.waitForFunction(function () {
    var images = Array.from(document.querySelectorAll("#list .empty-art img"));
    return images.length > 0 && images.every(function (image) { return image.complete; });
  });
  result.emptyArt = await page.$$eval("#list .empty-art img", function (images) {
    return images.filter(function (image) { return image.complete && image.naturalWidth > 0 && image.offsetParent !== null; }).length;
  });
  result.errors = errors;
  await browser.close();
  process.stdout.write(JSON.stringify(result));
})().catch(function (error) { console.error(error); process.exit(1); });
