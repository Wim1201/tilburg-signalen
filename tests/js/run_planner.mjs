/* Runs the planner (tools/planner/src) for the Python tests, without Cloudflare and without
   network. Reads a JSON list of calls from stdin and writes the list of results.
     ["ROOSTER"]                        the schedule
     ["slotOp", iso] ["plaatselijk", iso] ["besluit", runs, iso]
     ["exports"]                        what the Worker's main module exports
     ["jaar", year]                     how often a slot falls on each local day of that year
     ["loop", {tijd, env, antwoorden}]  one invocation of the cron trigger at `tijd`; GitHub answers
                                        with `antwoorden` in order ({status, body} or {fout}) */
import { readFileSync } from "node:fs";
import * as planner from "../../tools/planner/src/planner.js";
import * as worker from "../../tools/planner/src/index.js";

const DATUM = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Amsterdam", year: "numeric", month: "2-digit", day: "2-digit" });

function jaar(year) {
  // Every tick of the cron trigger (five minutes, UTC) from a day before to a day after the year.
  const perDag = {}, slots = {};
  for (let ms = Date.UTC(year, 0, 0); ms < Date.UTC(year + 1, 0, 2); ms += 5 * 60 * 1000) {
    const slot = planner.slotOp(ms);
    if (!slot) continue;
    const dag = DATUM.format(new Date(ms));
    if (!dag.startsWith(year + "-")) continue;
    perDag[dag] = (perDag[dag] || 0) + 1;
    const naam = dag + " " + slot.uur + ":" + slot.minuut;
    slots[naam] = (slots[naam] || 0) + 1;
  }
  return { perDag, dubbel: Object.keys(slots).filter((naam) => slots[naam] !== 1) };
}

async function loop(scenario) {
  const verzoeken = [], logboek = [], antwoorden = scenario.antwoorden.slice();
  const echt = { fetch: globalThis.fetch, log: console.log, error: console.error };
  globalThis.fetch = async (url, opties) => {
    verzoeken.push({ url: String(url), method: (opties && opties.method) || "GET", headers: (opties && opties.headers) || {}, body: opties && opties.body ? JSON.parse(opties.body) : null });
    const antwoord = antwoorden.shift();
    if (!antwoord) throw new Error("onverwacht verzoek aan " + url);
    if (antwoord.fout) throw new Error(antwoord.fout);
    const tekst = antwoord.body === undefined ? "" : JSON.stringify(antwoord.body);
    return { status: antwoord.status, ok: antwoord.status >= 200 && antwoord.status < 300, text: async () => tekst, json: async () => JSON.parse(tekst) };
  };
  console.log = (regel) => logboek.push(regel);
  console.error = (regel) => logboek.push(regel);
  let fout = null;
  try {
    await worker.default.scheduled({ scheduledTime: Date.parse(scenario.tijd), cron: "*/5 * * * *" }, scenario.env, {});
  } catch (error) {
    fout = error.message;
  } finally {
    Object.assign(globalThis, { fetch: echt.fetch });
    console.log = echt.log;
    console.error = echt.error;
  }
  return { verzoeken, logboek, fout, ongebruikt: antwoorden.length };
}

const results = [];
for (const call of JSON.parse(readFileSync(0, "utf8"))) {
  if (call[0] === "jaar") results.push(jaar(call[1]));
  else if (call[0] === "loop") results.push(await loop(call[1]));
  else if (call[0] === "slotOp" || call[0] === "plaatselijk") results.push(planner[call[0]](Date.parse(call[1])));
  else if (call[0] === "besluit") results.push(planner.besluit(call[1], Date.parse(call[2])));
  else if (call[0] === "exports") results.push(Object.keys(worker));
  else results.push(planner[call[0]]);
}
process.stdout.write(JSON.stringify(results));
