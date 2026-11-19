/* Energielabel: asks EP-Online for the energy label of one address, for the tab "Adres".

   Everything here is plain JavaScript without Cloudflare, so that the tests can run it under Node:
   what comes in, what is asked of EP-Online and what goes out. index.js holds the two pieces that
   only exist at Cloudflare: the handler and the counter object.

   The address comes in the body of a POST, never in the address of the request: Cloudflare can
   record the address of every request (logs, traces, a live tail), and never records a body.

   EP-Online, public REST API version 5 (public.ep-online.nl/swagger, read on 18-11-2026):
     GET /api/v5/PandEnergielabel/Adres?postcode=&huisnummer=&huisletter=&huisnummertoevoeging=
     header Authorization: <API key>
     200 a list of registrations, 400 input refused, 401 key refused, 404 nothing found.

   As the real service answers (seen by Wim on 19-11-2026): with a label, 200 and a list of one
   registration; without, 404 with a problem description, the same for "no label" and "address
   unknown". The dates carry no time zone: Registratiedatum is "yyyy-mm-ddThh:mm:ss.fff", Geldig_tot
   "yyyy-mm-ddT00:00:00". Fields without a value are left out of a registration. */

export const PAD = "/api/v5/PandEnergielabel/Adres";
export const WACHT_MS = 8000; // how long EP-Online gets to answer
export const MAX_INVOER = 400; // bytes of a request body; an address needs about 80

// The formats EP-Online documents. The documentation gives exactly four characters for the addition
// (^[a-zA-Z0-9]{4}$); additions in the BAG are one to four long, so one to four are let through
// here and EP-Online itself decides (a refusal there comes back as "ongeldig").
const POSTCODE = /^[1-9][0-9]{3}[A-Z]{2}$/;
const HUISNUMMER = /^[1-9][0-9]{0,4}$/;
const HUISLETTER = /^[a-zA-Z]$/;
const TOEVOEGING = /^[a-zA-Z0-9]{1,4}$/;

const DAG = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Amsterdam", year: "numeric", month: "2-digit", day: "2-digit" });

/* The Dutch calendar day of a moment, as "yyyy-mm-dd". */
export function dagVan(ms) {
  return DAG.format(new Date(ms));
}

/* The text of a request body, read up to `grens` bytes. `stroom` is the body (a ReadableStream) or
   null. Returns the text, or null when the body is longer or is no UTF-8: such a body is not read
   to its end. */
export async function leesTekst(stroom, grens) {
  if (!stroom) return "";
  const lezer = stroom.getReader(), stukken = [];
  let lengte = 0;
  for (;;) {
    const { done, value } = await lezer.read();
    if (done) break;
    lengte += value.byteLength;
    if (lengte > grens) {
      await lezer.cancel().catch(() => {});
      return null;
    }
    stukken.push(value);
  }
  const bytes = new Uint8Array(lengte);
  let plek = 0;
  for (const stuk of stukken) { bytes.set(stuk, plek); plek += stuk.byteLength; }
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch (fout) {
    return null;
  }
}

/* The address as asked, checked. `invoer` is the body of the request as text: a JSON object with
   postcode and huisnummer, and huisletter and toevoeging when the address has them, all as text.
   Returns { adres } or { fout } with the name of the field ("invoer" when the body is no such object). */
export function leesAdres(invoer) {
  let gevraagd;
  try {
    gevraagd = JSON.parse(invoer);
  } catch (fout) {
    return { fout: "invoer" };
  }
  if (!gevraagd || typeof gevraagd !== "object" || Array.isArray(gevraagd)) return { fout: "invoer" };
  const een = (naam) => {
    const waarde = Object.prototype.hasOwnProperty.call(gevraagd, naam) ? gevraagd[naam] : "";
    return typeof waarde === "string" ? waarde.trim() : null;
  };
  const postcode = een("postcode"), huisnummer = een("huisnummer"), huisletter = een("huisletter"), toevoeging = een("toevoeging");
  if (postcode === null || !POSTCODE.test((postcode || "").replace(/\s+/g, "").toUpperCase())) return { fout: "postcode" };
  if (huisnummer === null || !HUISNUMMER.test(huisnummer)) return { fout: "huisnummer" };
  if (huisletter === null || (huisletter && !HUISLETTER.test(huisletter))) return { fout: "huisletter" };
  if (toevoeging === null || (toevoeging && !TOEVOEGING.test(toevoeging))) return { fout: "toevoeging" };
  return { adres: { postcode: postcode.replace(/\s+/g, "").toUpperCase(), huisnummer, huisletter, toevoeging } };
}

/* The address at EP-Online for a checked address. Only the documented parameters, and only the
   documented host: `basis` comes from the settings, never from the request. */
export function bronUrl(basis, adres) {
  const url = new URL(PAD, basis);
  url.searchParams.set("postcode", adres.postcode);
  url.searchParams.set("huisnummer", adres.huisnummer);
  if (adres.huisletter) url.searchParams.set("huisletter", adres.huisletter);
  if (adres.toevoeging) url.searchParams.set("huisnummertoevoeging", adres.toevoeging);
  return url.toString();
}

/* The calendar day of a date of EP-Online: its first ten characters. The dates carry no time zone
   and are not converted: the day EP-Online writes is the day that is shown and compared. */
function datum(waarde) {
  const gevonden = typeof waarde === "string" && /^(\d{4}-\d{2}-\d{2})/.exec(waarde);
  return gevonden ? gevonden[1] : null;
}

function tekst(waarde, lengte) {
  return typeof waarde === "string" && waarde.trim() && waarde.trim().length <= lengte ? waarde.trim() : null;
}

/* What EP-Online registered at the address, weighed: of the registrations that are still valid on
   `vandaag`, the one registered last. Returns { label, telling }: the four values the tab shows (or
   null when there is no valid label), and for the log how many registrations there were and why
   the others do not count: no label class, no readable date, or expired. Only counts, so that a
   log line can say why an answer of EP-Online gave no label without saying anything of the answer.
   Nothing else of a registration leaves this function. */
export function weeg(registraties, vandaag) {
  const telling = { registraties: 0, zonderKlasse: 0, zonderDatum: 0, verlopen: 0 }, geldig = [];
  for (const registratie of Array.isArray(registraties) ? registraties : []) {
    telling.registraties++;
    const label = {
      klasse: tekst(registratie && registratie.Energieklasse, 10),
      registratiedatum: datum(registratie && registratie.Registratiedatum),
      geldigTot: datum(registratie && registratie.Geldig_tot),
      gebouw: tekst(registratie && registratie.Gebouwklasse, 40),
    };
    if (!label.klasse) telling.zonderKlasse++;
    else if (!label.registratiedatum || !label.geldigTot) telling.zonderDatum++;
    else if (label.geldigTot < vandaag) telling.verlopen++;
    // The moment of registration as EP-Online writes it, to the millisecond: of two registrations on
    // one day the later one is the last. Text in one form sorts as time does.
    else geldig.push({ label, moment: registratie.Registratiedatum.trim() });
  }
  geldig.sort((a, b) => (a.moment < b.moment ? 1 : a.moment > b.moment ? -1 : 0));
  return { label: geldig.length ? geldig[0].label : null, telling };
}

/* The label to show, or null: see weeg. */
export function kiesLabel(registraties, vandaag) {
  return weeg(registraties, vandaag).label;
}

/* The counter: at most `perMinuut` in a clock minute and `perDag` in a Dutch calendar day, counted
   over everyone together. `opslag` is the storage of the counter object (get and put). A request
   that is refused is not counted. Returns { door: true } or { door: false, grens, wacht } with the
   seconds until the limit opens again. */
export async function telOp(opslag, perMinuut, perDag, nu) {
  const minuut = Math.floor(nu / 60000), dag = dagVan(nu);
  const stand = (await opslag.get("stand")) || {};
  const inMinuut = stand.minuut === minuut ? stand.inMinuut : 0, inDag = stand.dag === dag ? stand.inDag : 0;
  if (inDag >= perDag) {
    // Until the next Dutch midnight: step by the minute, at most a day and an hour (the clock change).
    let wacht = 60 - Math.floor((nu % 60000) / 1000);
    for (let ms = (minuut + 1) * 60000; dagVan(ms) === dag && wacht < 25 * 3600; ms += 60000) wacht += 60;
    return { door: false, grens: "dag", wacht };
  }
  if (inMinuut >= perMinuut) return { door: false, grens: "minuut", wacht: 60 - Math.floor((nu % 60000) / 1000) };
  await opslag.put("stand", { minuut, inMinuut: inMinuut + 1, dag, inDag: inDag + 1 });
  return { door: true };
}

function getal(waarde, anders) {
  const n = Number.parseInt(waarde, 10);
  return Number.isFinite(n) && n > 0 ? n : anders;
}

/* One log line: how the request ended. Never the address and never the key. Cloudflare keeps no
   log of this Worker (wrangler.jsonc); the line is there for whoever watches live (wrangler tail). */
export function meld(uitkomst, extra) {
  console.log(JSON.stringify(Object.assign({ energielabel: uitkomst }, extra || {})));
}

/* One request. `verzoek` is { method, herkomst, tekst } with herkomst the Origin header and tekst()
   the body as text (null when it is too long); the address of the request is not looked at. `env`
   holds the settings and the secret, `hulp` what the Worker brings: { fetch, neem(perMinuut, perDag,
   nu), nu }. Returns { status, headers, body } with body an object or null. */
export async function behandel(verzoek, env, hulp) {
  const toegestaan = env.HERKOMST, herkomst = verzoek.herkomst || "";
  const klaar = (status, uitkomst, body, extra) => {
    meld(uitkomst, extra && extra.log);
    const headers = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", Vary: "Origin" };
    if (body) headers["Content-Type"] = "application/json; charset=utf-8";
    // Only the page of the app may read the answer; any other page gets no permission from the browser.
    if (herkomst === toegestaan) headers["Access-Control-Allow-Origin"] = toegestaan;
    return { status, headers: Object.assign(headers, (extra && extra.headers) || {}), body: body || null };
  };

  // 1. Only from the page of the app. Exactly that origin: no other scheme, host or port.
  if (!toegestaan || herkomst !== toegestaan) return klaar(403, "geweigerd", { status: "geweigerd" });
  if (verzoek.method === "OPTIONS") {
    return klaar(204, "voorvraag", null, { headers: { "Access-Control-Allow-Methods": "POST", "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Max-Age": "86400" } });
  }
  if (verzoek.method !== "POST") return klaar(405, "methode", { status: "ongeldig" }, { headers: { Allow: "POST, OPTIONS" } });

  // 2. The address, from the body, in the form EP-Online documents.
  let invoer;
  try {
    invoer = await verzoek.tekst();
  } catch (fout) {
    invoer = null;
  }
  const gelezen = typeof invoer === "string" ? leesAdres(invoer) : { fout: "invoer" };
  if (gelezen.fout) return klaar(400, "ongeldig", { status: "ongeldig", veld: gelezen.fout });

  if (!env.EP_ONLINE_KEY) return klaar(503, "sleutel ontbreekt", { status: "onbereikbaar" });

  // 3. The limits, before anything is asked of EP-Online. When the counter does not answer, nothing is asked.
  let beurt;
  try {
    beurt = await hulp.neem(getal(env.PER_MINUUT, 20), getal(env.PER_DAG, 300), hulp.nu);
  } catch (fout) {
    return klaar(503, "teller antwoordt niet", { status: "onbereikbaar" });
  }
  if (!beurt.door) return klaar(429, "te veel", { status: "teveel", grens: beurt.grens }, { headers: { "Retry-After": String(beurt.wacht) }, log: { grens: beurt.grens } });

  // 4. EP-Online. The key goes in the Authorization header and nowhere else.
  let antwoord;
  try {
    antwoord = await hulp.fetch(bronUrl(env.EP_ONLINE_URL, gelezen.adres), {
      // "manual": a redirect is not followed (the key must not travel on) and comes back as a fault below.
      // Cloudflare knows no redirect mode "error".
      method: "GET", headers: { Authorization: env.EP_ONLINE_KEY, Accept: "application/json" }, redirect: "manual", signal: AbortSignal.timeout(WACHT_MS),
    });
  } catch (fout) {
    // Only the kind of fault ("TimeoutError", "TypeError"): a message could repeat the address.
    return klaar(502, "bron antwoordt niet", { status: "onbereikbaar" }, { log: { fout: String((fout && fout.name) || "onbekend").slice(0, 40) } });
  }
  if (antwoord.status === 404) return klaar(404, "geen", { status: "geen" }, { log: { bron: 404 } });
  if (antwoord.status === 400) return klaar(400, "ongeldig bij de bron", { status: "ongeldig" }, { log: { bron: 400 } });
  if (antwoord.status === 429) return klaar(429, "te veel bij de bron", { status: "teveel", grens: "bron" }, { headers: { "Retry-After": "60" }, log: { bron: 429 } });
  if (antwoord.status === 401 || antwoord.status === 403) return klaar(502, "sleutel geweigerd", { status: "onbereikbaar" }, { log: { bron: antwoord.status } });
  if (antwoord.status !== 200) return klaar(502, "bron geeft een fout", { status: "onbereikbaar" }, { log: { bron: antwoord.status } });
  let registraties;
  try {
    registraties = await antwoord.json();
  } catch (fout) {
    return klaar(502, "bron onleesbaar", { status: "onbereikbaar" }, { log: { bron: 200 } });
  }
  if (!Array.isArray(registraties)) return klaar(502, "bron onleesbaar", { status: "onbereikbaar" }, { log: { bron: 200 } });
  const { label, telling } = weeg(registraties, dagVan(hulp.nu));
  if (!label) return klaar(404, "geen geldig label", { status: "geen" }, { log: Object.assign({ bron: 200 }, telling) });
  return klaar(200, "gevonden", { status: "gevonden", klasse: label.klasse, registratiedatum: label.registratiedatum, geldigTot: label.geldigTot, gebouw: label.gebouw },
    { log: Object.assign({ bron: 200 }, telling) });
}
