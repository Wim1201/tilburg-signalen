/* The timeline of the screen recording, without a browser: when each scene starts and when each
   step of the scenario happens. opname.js records along it; the tests run it under Node. */
"use strict";

var FPS = 30;
var ACTIES = ["wijs", "tik", "scroll", "slot"];

/* How long a text takes to say when no recording of it exists yet (trial run): about 15 characters a second. */
function schatDuur(tekst) { return Math.round((tekst.length / 15 + 0.6) * 10) / 10; }

function controleer(scenario) {
  var fouten = [];
  scenario.scenes.forEach(function (scene) {
    var vorige = -1;
    if (!scene.tekst || !scene.tekst.trim()) fouten.push(scene.id + ": geen tekst");
    scene.stappen.forEach(function (stap, index) {
      var waar = scene.id + " stap " + (index + 1);
      if (ACTIES.indexOf(stap.actie) === -1) fouten.push(waar + ": onbekende actie " + stap.actie);
      if (!(stap.op >= 0 && stap.op <= 1)) fouten.push(waar + ": op moet tussen 0 en 1 liggen");
      if (stap.op < vorige) fouten.push(waar + ": begint voor de vorige stap");
      if (stap.actie !== "slot" && !stap.doel) fouten.push(waar + ": geen doel");
      if (stap.actie === "scroll" && !(stap.tot > stap.op && stap.tot <= 1)) fouten.push(waar + ": scroll heeft een eind (tot) na het begin nodig");
      vorige = stap.actie === "scroll" ? stap.tot : stap.op;
    });
  });
  return fouten;
}

/* timing: { aanloop, uitloop, scenes: { id: seconds } }. Returns scenes with start and end, the
   steps with their moment in seconds, and the total length. */
function bouw(scenario, timing) {
  var t = timing.aanloop, scenes = [], stappen = [];
  scenario.scenes.forEach(function (scene, index) {
    var duur = timing.scenes[scene.id];
    if (!(duur > 0)) throw new Error("geen duur voor scene " + scene.id);
    scenes.push({ id: scene.id, kop: scene.kop, tekst: scene.tekst, nummer: index + 1, start: t, eind: t + duur });
    scene.stappen.forEach(function (stap) {
      stappen.push(Object.assign({}, stap, { scene: scene.id, start: t + stap.op * duur, eind: stap.tot !== undefined ? t + stap.tot * duur : null }));
    });
    t += duur;
  });
  var totaal = t + timing.uitloop;
  return { scenes: scenes, stappen: stappen, totaal: totaal, frames: Math.round(totaal * FPS) };
}

function proefTiming(scenario) {
  var scenes = {};
  scenario.scenes.forEach(function (scene) { scenes[scene.id] = schatDuur(scene.tekst) + 0.8; });
  return { aanloop: 1.2, uitloop: 2.4, scenes: scenes };
}

function ease(p) { p = Math.min(1, Math.max(0, p)); return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; }
function tussen(van, naar, p) { return van + (naar - van) * ease(p); }

module.exports = { FPS: FPS, schatDuur: schatDuur, controleer: controleer, bouw: bouw, proefTiming: proefTiming, ease: ease, tussen: tussen };
