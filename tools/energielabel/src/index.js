/* Energielabel: the Worker that the tab "Adres" of Tilburg Signalen asks for the energy label of an
   address. It asks EP-Online (the register of the Rijksdienst voor Ondernemend Nederland) with a key
   that only this Worker knows, and returns the label class, the dates and the kind of building.

   Needs the secret EP_ONLINE_KEY and the settings in wrangler.jsonc. What it does with a request is
   in energielabel.js; this file holds only what exists at Cloudflare. */

import { DurableObject } from "cloudflare:workers";
import { MAX_INVOER, behandel, leesTekst, telOp } from "./energielabel.js";

/* The counter for the limits per minute and per day: one object for the whole Worker. Cloudflare
   handles the calls to one object one at a time, so two requests can never take the same turn. */
export class Teller extends DurableObject {
  async neem(perMinuut, perDag, nu) {
    return telOp(this.ctx.storage, perMinuut, perDag, nu);
  }
}

export default {
  async fetch(request, env) {
    const teller = env.TELLER.get(env.TELLER.idFromName("alle"));
    const antwoord = await behandel(
      // Not the address of the request: the address asked for is in the body, and nowhere else.
      { method: request.method, herkomst: request.headers.get("Origin"), tekst: () => leesTekst(request.body, MAX_INVOER) },
      env,
      { fetch: (url, opties) => fetch(url, opties), neem: (perMinuut, perDag, nu) => teller.neem(perMinuut, perDag, nu), nu: Date.now() },
    );
    return new Response(antwoord.body ? JSON.stringify(antwoord.body) : null, { status: antwoord.status, headers: antwoord.headers });
  },
};
