/* Runs the energy label Worker (tools/energielabel/src/energielabel.js) for the Python tests, without
   Cloudflare and without network: EP-Online and the storage of the counter are played here. Reads a
   JSON list of calls from stdin and writes the list of results.
     ["reeks", {env, stand, tellerKapot, verzoeken: [{method, url, herkomst, nu, antwoord}]}]
         requests one after another on one counter. `antwoord` is what EP-Online says to that
         request: {status, body}, {status, tekst} (a body that is not JSON) or {fout: "TimeoutError"}.
         Without `antwoord`, a request that reaches EP-Online is itself a fault.
     ["leesAdres", "postcode=...&huisnummer=..."] ["bronUrl", basis, adres] ["kiesLabel", list, day]
     ["dagVan", iso] ["WACHT_MS"] ["PAD"] */
import { readFileSync } from "node:fs";
import * as worker from "../../tools/energielabel/src/energielabel.js";

async function reeks(scenario) {
  const opslag = { waarden: scenario.stand ? { stand: scenario.stand } : {}, lees: 0, schrijf: 0,
    async get(sleutel) { this.lees++; return this.waarden[sleutel]; },
    async put(sleutel, waarde) { this.schrijf++; this.waarden[sleutel] = JSON.parse(JSON.stringify(waarde)); } };
  const uit = [], echt = console.log;
  for (const verzoek of scenario.verzoeken) {
    const naarBron = [], logboek = [];
    console.log = (regel) => logboek.push(regel);
    let antwoord, fout = null;
    try {
      antwoord = await worker.behandel({ method: verzoek.method || "GET", url: verzoek.url, herkomst: verzoek.herkomst }, scenario.env, {
        nu: Date.parse(verzoek.nu),
        neem: async (perMinuut, perDag, nu) => {
          if (scenario.tellerKapot) throw new Error("de teller antwoordt niet");
          return worker.telOp(opslag, perMinuut, perDag, nu);
        },
        fetch: async (url, opties) => {
          naarBron.push({ url: String(url), method: opties.method, headers: opties.headers, redirect: opties.redirect, metTijdslimiet: opties.signal instanceof AbortSignal });
          const gespeeld = verzoek.antwoord;
          if (!gespeeld) throw new Error("onverwacht verzoek aan " + url);
          if (gespeeld.fout) { const error = new Error("verbinding met " + url + " mislukt"); error.name = gespeeld.fout; throw error; }
          return { status: gespeeld.status, json: async () => (gespeeld.tekst !== undefined ? JSON.parse(gespeeld.tekst) : gespeeld.body) };
        },
      });
    } catch (error) {
      fout = error.message;
    } finally {
      console.log = echt;
    }
    uit.push({ antwoord, fout, naarBron, logboek, stand: opslag.waarden.stand || null });
  }
  return uit;
}

const results = [];
for (const call of JSON.parse(readFileSync(0, "utf8"))) {
  if (call[0] === "reeks") results.push(await reeks(call[1]));
  else if (call[0] === "leesAdres") results.push(worker.leesAdres(new URLSearchParams(call[1])));
  else if (call[0] === "bronUrl") results.push(worker.bronUrl(call[1], call[2]));
  else if (call[0] === "kiesLabel") results.push(worker.kiesLabel(call[1], call[2]));
  else if (call[0] === "dagVan") results.push(worker.dagVan(Date.parse(call[1])));
  else results.push(worker[call[0]]);
}
process.stdout.write(JSON.stringify(results));
