/* The planner's logic: the schedule, the clock, the decision and the calls to GitHub. Kept apart from
   index.js, because Cloudflare accepts only handlers as exports of a Worker's main module. */

// The schedule in Dutch time, the same slots as under `schedule` in .github/workflows/dagelijks.yml
// (a test compares the two). Days as in cron: 0 is Sunday.
const WERKDAGEN = [1, 2, 3, 4, 5], ELKE_DAG = [0, 1, 2, 3, 4, 5, 6];
export const ROOSTER = [
  { uur: 6, minuut: 45, dagen: WERKDAGEN },
  { uur: 9, minuut: 35, dagen: WERKDAGEN },
  { uur: 10, minuut: 20, dagen: WERKDAGEN },
  { uur: 12, minuut: 10, dagen: ELKE_DAG },
  { uur: 16, minuut: 10, dagen: WERKDAGEN },
  // The weekly full refresh: the workflow recognises its own scheduled run by the clock, a run
  // started from here gets the input `volledig`.
  { uur: 4, minuut: 30, dagen: [0], volledig: true },
];

// A run that succeeded this short a time ago makes a new one pointless.
export const KORT_GELEDEN_MS = 10 * 60 * 1000;
const OPNIEUW_NA_MS = 1000;

const DAGEN = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const KLOK = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Amsterdam", weekday: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });

/** The day of the week (0 is Sunday), hour and minute in the Netherlands at the moment `ms`. */
export function plaatselijk(ms) {
  const delen = {};
  for (const deel of KLOK.formatToParts(new Date(ms))) delen[deel.type] = deel.value;
  return { dag: DAGEN.indexOf(delen.weekday), uur: Number(delen.hour), minuut: Number(delen.minute) };
}

/** The slot of the schedule that falls on the moment `ms`, or null. */
export function slotOp(ms) {
  const nu = plaatselijk(ms);
  return ROOSTER.find((slot) => slot.uur === nu.uur && slot.minuut === nu.minuut && slot.dagen.includes(nu.dag)) || null;
}

/** Whether to start a run at the moment `ms`, given the latest runs of the workflow (newest first). */
export function besluit(runs, ms) {
  const bezig = runs.find((run) => run.status !== "completed");
  if (bezig) return { starten: false, reden: "er loopt of wacht al een run (" + bezig.event + ", " + bezig.status + ")" };
  const net = runs.find((run) => run.conclusion === "success" && Date.parse(run.created_at) > ms - KORT_GELEDEN_MS);
  if (net) return { starten: false, reden: "er is zojuist een run geslaagd (" + net.event + ", " + net.created_at + ")" };
  return { starten: true, reden: "geen lopende of recente run" };
}

function tijd(slot) {
  return String(slot.uur).padStart(2, "0") + ":" + String(slot.minuut).padStart(2, "0");
}

export function meld(soort, slot, tekst, extra) {
  console[soort === "fout" ? "error" : "log"](JSON.stringify(Object.assign({ planner: soort, slot: tijd(slot), bericht: tekst }, extra)));
}

function github(env, pad, opties) {
  const headers = { Authorization: "Bearer " + env.GITHUB_TOKEN, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "tilburg-signalen-planner" };
  if (opties && opties.body) headers["Content-Type"] = "application/json";
  return fetch("https://api.github.com/repos/" + env.GITHUB_REPO + "/actions/workflows/" + env.WORKFLOW + pad, Object.assign({}, opties, { headers }));
}

async function uitleg(antwoord) {
  let tekst = "";
  try { tekst = (await antwoord.text()).slice(0, 300); } catch (fout) { /* the status says enough */ }
  return antwoord.status + (tekst ? " " + tekst : "");
}

/** The latest runs of the workflow, or null when GitHub does not give them. A refused token stops everything. */
async function laatsteRuns(env, slot) {
  let antwoord;
  try {
    antwoord = await github(env, "/runs?per_page=10");
  } catch (fout) {
    meld("waarschuwing", slot, "De lijst met runs is niet opgehaald; de run wordt toch gestart", { fout: String(fout) });
    return null;
  }
  if (antwoord.status === 401 || antwoord.status === 403) throw new Error("GitHub weigert het token: " + (await uitleg(antwoord)));
  if (!antwoord.ok) {
    meld("waarschuwing", slot, "De lijst met runs is niet opgehaald; de run wordt toch gestart", { status: antwoord.status });
    return null;
  }
  return (await antwoord.json()).workflow_runs || [];
}

/** Asks GitHub to start the workflow; one more try after a failure on GitHub's side. */
async function startRun(env, slot) {
  // `gepland` makes the run behave like a scheduled one (no browser tests before the refresh).
  const body = JSON.stringify({ ref: env.REF, inputs: { gepland: "true", volledig: slot.volledig ? "true" : "false" } });
  let laatste = "";
  for (let poging = 1; poging <= 2; poging++) {
    if (poging > 1) await new Promise((klaar) => setTimeout(klaar, OPNIEUW_NA_MS));
    try {
      const antwoord = await github(env, "/dispatches", { method: "POST", body });
      if (antwoord.ok) return poging;   // GitHub answers 204, without a body
      laatste = await uitleg(antwoord);
      if (antwoord.status < 500) break;
    } catch (fout) {
      laatste = String(fout);
    }
  }
  throw new Error("GitHub heeft de run niet gestart: " + laatste);
}

/** Starts a run for `slot` at the moment `ms`, unless one is running, waiting or has just succeeded. */
export async function start(slot, ms, env) {
  if (!env.GITHUB_TOKEN) throw new Error("Het geheim GITHUB_TOKEN ontbreekt; zet het met `wrangler secret put GITHUB_TOKEN`");
  const runs = await laatsteRuns(env, slot);
  if (runs) {
    const keuze = besluit(runs, ms);
    if (!keuze.starten) {
      meld("overgeslagen", slot, "Geen run gestart: " + keuze.reden);
      return false;
    }
  }
  const pogingen = await startRun(env, slot);
  meld("gestart", slot, slot.volledig ? "Volledige verversing gestart" : "Run gestart", { pogingen });
  return true;
}
