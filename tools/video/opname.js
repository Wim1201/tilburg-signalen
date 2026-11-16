/* Records the screen video by using the app: opens it in a phone on the stage (podium.html), moves
   a pointer, taps and scrolls along the scenario, and writes every frame to ffmpeg.

   node opname.js --uit stil.mp4 --gebeurtenissen gebeurtenissen.json [--timing timing.json] [--droog] [--base http://...]

   Without --base the script serves the folder site/ itself for as long as it runs.

   Without --timing the length of each scene is estimated from its text (trial run without sound).
   With --droog nothing is filmed: the scenario is walked through quickly to see that every step
   finds its target (the tests use this).
   Needs Playwright and ffmpeg. The app is used as it is; only the clock and "what this device has
   seen before" are set, so that the recording shows a morning with something new. */
"use strict";
var fs = require("fs"), path = require("path"), http = require("http"), spawn = require("child_process").spawn;
var chromium = require("playwright").chromium;
var tijdlijn = require("./tijdlijn.js");

var DROOG = process.argv.indexOf("--droog") !== -1;
var W = 1920, H = 1080, FPS = DROOG ? 6 : tijdlijn.FPS;
var BEWEEG = 0.9, NAAR_TIK = 0.35, RIMPEL = 0.5, KOPRUIMTE = 96, SEEN = "tilburg-signalen.gezien";

function optie(naam, standaard) {
  var index = process.argv.indexOf("--" + naam);
  return index === -1 ? standaard : process.argv[index + 1];
}

function podium() {
  var merk = fs.readFileSync(path.join(__dirname, "..", "..", "site", "icons", "beeldmerk.svg"), "utf8");
  var vormen = merk.match(/\sd="[^"]+"/g);
  var svg = '<svg viewBox="349 344 1360 1360" aria-hidden="true"><path fill="currentColor" fill-rule="evenodd"' + vormen[0] +
    '/><path class="sig" fill="#ff5a2b"' + vormen[1] + "/></svg>";
  return fs.readFileSync(path.join(__dirname, "podium.html"), "utf8").split("<!--MARK-->").join(svg);
}

/* Serves site/ on a free port; only what the app itself needs. */
function serveerSite() {
  var map = path.join(__dirname, "..", "..", "site");
  var soorten = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json",
    ".svg": "image/svg+xml", ".png": "image/png", ".webmanifest": "application/manifest+json" };
  var server = http.createServer(function (vraag, antwoord) {
    var pad = path.normalize(path.join(map, decodeURIComponent(vraag.url.split("?")[0])));
    if (pad.indexOf(map) !== 0) { antwoord.writeHead(403); antwoord.end(); return; }
    fs.readFile(pad, function (fout, inhoud) {
      if (fout) { antwoord.writeHead(404); antwoord.end(); return; }
      antwoord.writeHead(200, { "Content-Type": soorten[path.extname(pad)] || "application/octet-stream" });
      antwoord.end(inhoud);
    });
  });
  return new Promise(function (resolve) { server.listen(0, "127.0.0.1", function () { resolve(server); }); });
}

(async function () {
  var eigen = optie("base") ? null : await serveerSite();
  var base = optie("base") || "http://127.0.0.1:" + eigen.address().port, uit = optie("uit", "stil.mp4"), gebeurtenissenPad = optie("gebeurtenissen", "gebeurtenissen.json");
  var scenario = JSON.parse(fs.readFileSync(optie("scenario", path.join(__dirname, "scenario.json")), "utf8"));
  var fouten = tijdlijn.controleer(scenario);
  if (fouten.length) throw new Error("Scenario klopt niet:\n" + fouten.join("\n"));
  var timing = optie("timing") ? JSON.parse(fs.readFileSync(optie("timing"), "utf8")) : tijdlijn.proefTiming(scenario);
  var plan = tijdlijn.bouw(scenario, timing);

  var browser = await chromium.launch();
  var context = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1, locale: "nl-NL", timezoneId: "Europe/Amsterdam", colorScheme: "light" });
  await context.clock.setFixedTime(new Date(scenario.moment));
  var page = await context.newPage(), meldingen = [];
  page.on("console", function (bericht) { if (bericht.type() === "error") meldingen.push(bericht.text()); });
  page.on("pageerror", function (fout) { meldingen.push(fout.message); });
  await page.setContent(podium());

  async function openApp() {
    await page.evaluate(function (url) { document.getElementById("app").src = url; }, base + "/index.html?opname=" + Date.now() + Math.random());
    var frame = null;
    for (var poging = 0; poging < 100 && !frame; poging++) {
      frame = page.frames().filter(function (f) { return f.url().indexOf(base) === 0; })[0] || null;
      if (!frame) await page.waitForTimeout(50);
    }
    if (!frame) throw new Error("De app is niet bereikbaar op " + base);
    await frame.waitForSelector("#list .card");
    return frame;
  }
  // First visit, then mark everything but the latest publication day as seen long ago, then the visit that is recorded.
  var app = await openApp();
  await app.evaluate(function (key) {
    return fetch("data/berichten.json").then(function (r) { return r.json(); }).then(function (data) {
      var latest = data.berichten.reduce(function (day, item) { return item.datum > day ? item.datum : day; }, "");
      var seen = {};
      data.berichten.forEach(function (item) { if (item.datum !== latest) seen[item.id] = 1; });
      localStorage.setItem(key, JSON.stringify(seen));
    });
  }, SEEN);
  app = await openApp();
  await page.evaluate(function () { return document.fonts.ready; });
  await app.evaluate(function () { return document.fonts.ready; });

  var ffmpeg = DROOG ? null : spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
    // High profile at level 4.0 with at most 4 reference frames: within what phones state they play (the preset alone gave level 5.0).
    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level:v", "4.0", "-refs", "4",
    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", uit], { stdio: ["pipe", "inherit", "inherit"] });
  var klaar = DROOG ? Promise.resolve() : new Promise(function (resolve, reject) { ffmpeg.on("close", function (code) { code ? reject(new Error("ffmpeg " + code)) : resolve(); }); });

  var wijzer = { x: W - 120, y: H + 80 }, beweging = null, rol = null, tik = null, slotVanaf = null, scene = null;
  var wachtrij = plan.stappen.slice(), gebeurtenissen = [];

  async function midden(doel) {
    var plek = app.locator(doel).first();
    var vak = await plek.boundingBox();
    if (!vak) throw new Error("Niet zichtbaar in de app: " + doel);
    return { x: vak.x + vak.width / 2, y: vak.y + Math.min(vak.height / 2, 60) };
  }
  function beweegNaar(doel, t, duur) { beweging = { x0: wijzer.x, y0: wijzer.y, x1: doel.x, y1: doel.y, t0: t, t1: t + duur }; }

  async function begin(stap, t) {
    gebeurtenissen.push({ t: Math.round(t * 1000) / 1000, soort: stap.actie, scene: stap.scene, doel: stap.doel || null });
    if (stap.actie === "wijs") beweegNaar(await midden(stap.doel), t, BEWEEG);
    else if (stap.actie === "tik") {
      var plek = await midden(stap.doel);
      beweegNaar(plek, t, NAAR_TIK);
      tik = { op: t + NAAR_TIK, x: plek.x, y: plek.y, gedaan: false, doel: stap.doel };
    } else if (stap.actie === "scroll") {
      var doelY = await app.evaluate(function (args) {
        var max = document.documentElement.scrollHeight - window.innerHeight;
        if (args.doel === "top") return [window.scrollY, 0];
        var node = document.querySelector(args.doel);
        if (!node) return null;
        return [window.scrollY, Math.max(0, Math.min(max, node.getBoundingClientRect().top + window.scrollY - args.ruimte))];
      }, { doel: stap.doel, ruimte: KOPRUIMTE });
      if (!doelY) throw new Error("Niet gevonden in de app: " + stap.doel);
      rol = { y0: doelY[0], y1: doelY[1], t0: t, t1: stap.eind };
    } else if (stap.actie === "slot") slotVanaf = t;
  }

  var beelden = Math.round(plan.totaal * FPS);
  for (var beeld = 0; beeld < beelden; beeld++) {
    var t = beeld / FPS;
    var nu = plan.scenes.filter(function (s) { return t >= s.start && t < s.eind; })[0] || null;
    if (nu && nu !== scene) {
      scene = nu;
      gebeurtenissen.push({ t: Math.round(t * 1000) / 1000, soort: "scene", scene: scene.id });
      await page.evaluate(function (s) {
        document.getElementById("step").textContent = s.nummer + " / " + s.aantal;
        document.getElementById("kop").textContent = s.kop;
        document.getElementById("say").textContent = s.tekst;
        var dots = document.getElementById("dots");
        dots.textContent = "";
        for (var i = 1; i <= s.aantal; i++) { var dot = document.createElement("i"); if (i <= s.nummer) dot.className = "on"; dots.appendChild(dot); }
      }, { nummer: scene.nummer, aantal: plan.scenes.length, kop: scene.kop, tekst: scene.tekst });
    }
    while (wachtrij.length && wachtrij[0].start <= t) await begin(wachtrij.shift(), t);

    if (rol) {
      await app.evaluate(function (y) { window.scrollTo(0, y); }, Math.round(tijdlijn.tussen(rol.y0, rol.y1, (t - rol.t0) / (rol.t1 - rol.t0))));
      if (t >= rol.t1) rol = null;
    }
    if (beweging) {
      var p = (t - beweging.t0) / (beweging.t1 - beweging.t0);
      wijzer = { x: tijdlijn.tussen(beweging.x0, beweging.x1, p), y: tijdlijn.tussen(beweging.y0, beweging.y1, p) };
      if (p >= 1) beweging = null;
    }
    await page.mouse.move(wijzer.x, wijzer.y);
    if (tik && !tik.gedaan && t >= tik.op) {
      await page.mouse.down(); await page.mouse.up();
      tik.gedaan = true;
      gebeurtenissen.push({ t: Math.round(t * 1000) / 1000, soort: "klik", scene: scene ? scene.id : null, doel: tik.doel });
    }
    var rimpel = tik && tik.gedaan ? (t - tik.op) / RIMPEL : -1;
    await page.evaluate(function (s) {
      var pointer = document.getElementById("pointer"), ripple = document.getElementById("ripple");
      pointer.style.transform = "translate(" + s.x + "px," + s.y + "px) scale(" + s.druk + ")";
      ripple.style.transform = "translate(" + s.x + "px," + s.y + "px) scale(" + (1 + 1.6 * s.rimpel) + ")";
      ripple.style.opacity = s.rimpel >= 0 && s.rimpel <= 1 ? String(0.9 * (1 - s.rimpel)) : "0";
      document.getElementById("veil").style.opacity = String(s.sluier);
      document.getElementById("end").style.opacity = String(s.slot);
    }, {
      x: Math.round(wijzer.x * 10) / 10, y: Math.round(wijzer.y * 10) / 10,
      druk: rimpel >= 0 && rimpel < 0.3 ? 0.82 : 1, rimpel: rimpel,
      sluier: 1 - tijdlijn.ease(t / 0.8), slot: slotVanaf === null ? 0 : tijdlijn.ease((t - slotVanaf) / 0.9),
    });
    if (DROOG) continue;
    var plaatje = await page.screenshot({ type: "jpeg", quality: 95 });
    if (!ffmpeg.stdin.write(plaatje)) await new Promise(function (resolve) { ffmpeg.stdin.once("drain", resolve); });
    if (beeld % 150 === 0) process.stderr.write("beeld " + beeld + " van " + beelden + "\n");
  }
  if (ffmpeg) ffmpeg.stdin.end();
  await klaar;
  var staat = await app.evaluate(function () {
    return {
      ochtend: document.getElementById("brief-day").textContent, zin: document.getElementById("brief-title").textContent,
      gekozen: document.querySelector('.tile[aria-pressed="true"]').id, kaarten: document.querySelectorAll("#list .card").length,
    };
  });
  await browser.close();
  if (eigen) eigen.close();
  var verslag = { fps: FPS, duur: plan.totaal, frames: beelden, scenes: plan.scenes, gebeurtenissen: gebeurtenissen, nietUitgevoerd: wachtrij.length, fouten: meldingen, eind: staat };
  if (DROOG) process.stdout.write(JSON.stringify(verslag));
  else fs.writeFileSync(gebeurtenissenPad, JSON.stringify(verslag, null, 1));
  process.stderr.write("klaar: " + plan.totaal.toFixed(1) + " s, " + meldingen.length + " fouten in de console\n");
})().catch(function (fout) { console.error(String(fout && fout.message || fout)); process.exit(1); });
