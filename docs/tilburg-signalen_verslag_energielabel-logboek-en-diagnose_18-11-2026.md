# Tilburg Signalen: verslag energielabel, wat Cloudflare vastlegt en waarom twee adressen "geen" geven

| | |
|---|---|
| Datum | 18-11-2026, 22:30 – 22:47 uur |
| Versie | versie 2 van de app met de regio's, branch `claude/optimistic-gauss-sb0xpy`, gelijk aan `main` op commit `33c3d11` (na PR 27) bij de start |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen`; Node 22, wrangler 4.164.0, Chromium via Playwright |
| Brondata | De documentatie van EP-Online (`public.ep-online.nl/swagger/v5/swagger.json`, opnieuw opgehaald 22:31 uur) en vijf verzoeken aan EP-Online **zonder sleutel** (22:31 uur); de documentatie van Cloudflare over Workers Logs, Real-time logs en de instellingen van wrangler (gelezen 22:30 – 22:36 uur); de melding van Wim over de geplaatste Worker |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_energielabel_18-11-2026.md` |

## Stand

Wim heeft de Worker geplaatst met een echte sleutel. De sleutel wordt aangenomen. Twee adressen geven
`404` met `"geen"`; van één weet Wim zeker dat het een geldig label heeft. Daarnaast stelde Wim vast
dat Cloudflare bij elk verzoek de volledige vraag vastlegt, met postcode, huisnummer en het IP-adres
van de bezoeker, terwijl de README zei dat het logboek geen adres bevat.

| Vraag | Uitkomst |
|---|---|
| 1. Wat klopt er niet aan de vraag aan EP-Online of aan het lezen van het antwoord? | **Niet gevonden.** Zonder sleutel kan ik het antwoord van EP-Online op een adres niet zien. Wat ik wel kon nagaan, sluit één oorzaak uit (een verkeerd pad). Er blijven twee mogelijkheden over; de logregel of het ruwe antwoord zegt welke. Hoe je beide bekijkt, staat hieronder |
| 2. Het logboek | **Hersteld, nog niet bij Cloudflare.** Het adres staat niet meer in het webadres van de vraag en Cloudflare bewaart geen logboek meer. Dat werkt pas nadat de pull request is samengevoegd en de Worker opnieuw is geplaatst |

De instelling `energielabel_worker` in `config.json` is leeg gebleven. De pull request staat open en
is niet samengevoegd.

## Correcties en aanvullingen op eerdere verslagen

| Tijdstip | Wat |
|---|---|
| 18-11-2026, 22:44 uur | **"Het logboek: geen adres, geen sleutel, geen IP-adres" (verslag energielabel en de README van de Worker) klopte niet.** Het gold voor de regel die de Worker zelf schrijft. Cloudflare bewaarde daarnaast per verzoek een eigen regel met de hele vraag. Ik had bij het bouwen `observability` aangezet zonder na te lezen wat Cloudflare dan zelf vastlegt, en de bewering alleen getest op de regel van de Worker. De correctie staat ook bovenaan het eerdere verslag. |
| 18-11-2026, 22:44 uur | **"Niets geplaatst, geen sleutel" is achterhaald:** Wim heeft de Worker geplaatst met een echte sleutel. |
| 18-11-2026, 22:44 uur | **De vraag aan de Worker is nu een `POST` met het adres in de inhoud**, geen `GET` met het adres in het webadres. De oude vorm geeft na het opnieuw plaatsen `405`. |
| 18-11-2026, 22:44 uur | **Het aantal tests is 513 (was 503).** Negen erbij voor de Worker (59, was 50) en één voor het tabblad. |
| 18-11-2026, 22:44 uur | **De naam van de opslag van de app op het toestel is `tilburg-signalen-v14` (was `v13`)**, omdat twee bestanden van het tabblad Adres zijn gewijzigd. |

## Vraag 1: waarom "geen"?

### Wat ik heb nagegaan

| Wat | Hoe | Uitkomst | Soort |
|---|---|---|---|
| Bestaat het pad dat de Worker vraagt? | `GET /api/v5/PandEnergielabel/Adres` zonder sleutel, met een verzonnen adres (1000AA 1) | `401`, "Valid API key required" | Feit |
| Wat doet EP-Online met een pad dat niet bestaat? | `GET /api/v5/PandEnergielabel/Bestaatniet` en `/api/v9/...` zonder sleutel | `404` met `"title":"Not Found"` | Feit |
| Namen van de parameters | Opnieuw vergeleken met de documentatie | `postcode`, `huisnummer`, `huisletter`, `huisnummertoevoeging`: gelijk aan wat de Worker stuurt | Feit |
| Namen van de velden in het antwoord | Idem | `Energieklasse`, `Registratiedatum`, `Geldig_tot`, `Gebouwklasse`: gelijk aan wat de Worker leest | Feit (over de documentatie, niet over een echt antwoord) |
| Hoofdletters in het pad | `/api/v5/pandenergielabel/adres` zonder sleutel | `401`: het pad is niet hoofdlettergevoelig | Feit |
| De documentatie op GitHub waar EP-Online naar verwijst (`Dictu/EP-online-API`) | Gelezen via een subsessie | Gaat over het aanleveren van labels, niet over het opvragen. Niets over hoe een adres wordt vergeleken, geen voorbeeld van een antwoord | Feit |

Daarmee is uitgesloten dat de Worker een pad vraagt dat niet bestaat: dan zou een `404` niets over
het adres zeggen. Een verkeerde sleutel gaf bij Wim `502` (de Worker maakt dat van een `401`) en een
goede sleutel `404`; dat past bij een pad dat bestaat.

**De twee adressen zelf heb ik niet aan EP-Online gevraagd** (ik heb geen sleutel) en ze staan niet
in dit verslag of in de repo.

### Wat overblijft

De Worker geeft `"geen"` in twee gevallen. Welke van de twee het was, staat in de logregel.

| Geval | Logregel van de Worker | Wat het betekent |
|---|---|---|
| A. EP-Online antwoordt zelf `404` | `{"energielabel":"geen","bron":404}` | EP-Online vindt op deze schrijfwijze van het adres niets. Dan ligt het aan de vraag. **Vermoeden**, niet nagegaan: het label staat bij EP-Online onder een andere schrijfwijze (een huisletter als toevoeging of andersom, een hoofdletter of kleine letter, of een "detailaanduiding"), of het adres-eindpunt geeft minder terug dan het zoekscherm op ep-online.nl |
| B. EP-Online antwoordt `200` met registraties, en de Worker telt er geen als geldig label | `{"energielabel":"geen geldig label","bron":200,"registraties":N}` | De Worker leest het antwoord verkeerd, of het label is verlopen. **Vermoeden**, niet nagegaan: een veld heet in het echte antwoord anders dan in de documentatie, of een datum heeft een andere vorm |

Welk geval waarschijnlijker is, weet ik niet. Voor het adres zonder huisletter is A vreemd (een kaal
huisnummer laat weinig ruimte voor een andere schrijfwijze) en B dus goed mogelijk; voor het adres met
huisletter is A goed mogelijk. Dat is redeneren, geen meting.

### Wat de Worker nu extra meldt

Bij geval B zegt de logregel voortaan waarom er niets overbleef, in tellingen:

```
{"energielabel":"geen geldig label","bron":200,"registraties":2,"zonderKlasse":0,"zonderDatum":2,"verlopen":0}
```

`zonderKlasse`: geen leesbare labelklasse. `zonderDatum`: geen leesbare registratiedatum of "geldig
tot". `verlopen`: geldig tot een dag vóór vandaag. Alleen aantallen; niets uit het antwoord zelf.

### Wat je uitvoert om het ruwe antwoord te zien

In Terminal (zsh of bash). De eerste regel vraagt om de sleutel; wat je plakt, wordt niet getoond en
komt niet in de geschiedenis van de terminal:

```bash
printf 'Plak de sleutel en druk op Enter (je ziet niets): '; read -rs EPKEY; echo
```

Vul de postcode en het huisnummer in:

```bash
curl -sS -i -H "Authorization: $EPKEY" -H "Accept: application/json" "https://public.ep-online.nl/api/v5/PandEnergielabel/Adres?postcode=<postcode>&huisnummer=<huisnummer>"
```

Voor het adres met een letter drie keer, met achter het huisnummer: `&huisletter=a`, `&huisletter=A`
en `&huisnummertoevoeging=a`. Gebruik niet `-v`: dat toont de sleutel. Daarna:

```bash
unset EPKEY
```

Dit is precies de vraag die de Worker stelt, met dezelfde twee koppen. Je ziet de status, de koppen
van het antwoord en de inhoud. De inhoud bevat openbare gegevens van het label, geen sleutel.

| Je ziet | Dan |
|---|---|
| `HTTP/1.1 404` | Geval A. Vergelijk met het zoekscherm op ep-online.nl: staat het label daar onder een toevoeging of een andere letter? |
| `HTTP/1.1 200` en een lijst | Geval B. Ik heb de **namen van de velden** nodig en de vorm van `Registratiedatum` en `Geldig_tot` van één registratie; de waarden zelf niet |

### Waar je de regel met "bron" vindt

| Versie van de Worker | Waar |
|---|---|
| **De versie die nu geplaatst is** (logboek aan) | Dashboard van Cloudflare: **Workers & Pages** → `tilburg-signalen-energielabel` → **Observability**. Per verzoek staan er twee regels: die van Cloudflare zelf (`GET https://...`) en die van de Worker (`{"energielabel":"geen","bron":...}`). Zoeken op `energielabel` kan in de zoekbalk. De regels van je twee proeven staan er nog; in het gratis abonnement drie dagen |
| **De nieuwe versie** (logboek uit) | Alleen live. In een tweede venster `npx wrangler tail tilburg-signalen-energielabel`, daarna het verzoek doen. Of in het dashboard: **Workers & Pages** → de Worker → **Logs** → **Live** |

De paden in het dashboard komen uit de documentatie van Cloudflare; ik heb ze niet in een account
gezien.

## Vraag 2: wat Cloudflare vastlegt

### Wat er mis was

| Punt | Toelichting |
|---|---|
| Wat de README zei | "Logboek: één regel per verzoek met de uitkomst. Nooit het adres en nooit de sleutel" |
| Wat waar was | De regel van de Worker bevat geen adres. Maar met `observability` aan bewaart Cloudflare per aanroep ook een eigen regel. Volgens de documentatie bevat die "details such as the Request, Response, and related metadata"; Wim zag daarin het webadres met postcode en huisnummer en het IP-adres van de bezoeker |
| Waardoor | Het adres stond in het webadres van de vraag, en ik had `observability` aangezet zonder na te lezen wat dat vastlegt. De tests keken alleen naar de regel van de Worker |

### Wat er gewijzigd is

| Wijziging | Waarom |
|---|---|
| **Het adres gaat in de inhoud van een `POST`**, niet meer in het webadres. De Worker kijkt niet meer naar het webadres van de vraag | Een webadres kan onderweg op meer plekken worden vastgelegd (logboek, sporen, live meekijken). Een inhoud legt Cloudflare niet vast. Dit blijft werken als iemand het logboek later weer aanzet |
| **Cloudflare bewaart van deze Worker niets meer**: `observability` uit, logboek uit, regel per aanroep uit, sporen uit | Zie "De keuze" |
| De inhoud wordt tot 400 bytes gelezen | Een adres is ongeveer 80 bytes. Een langere inhoud wordt niet tot het einde gelezen en geweigerd |
| De app stuurt de inhoud als platte tekst, zonder eigen koppen | Een browser stelt dan geen vraag vooraf (preflight): één adres blijft één aanroep |
| `GET` wordt geweigerd met `405` | Zodat de oude vorm, met het adres in het webadres, niet per ongeluk in gebruik blijft |

### De keuze: het hele logboek uit, niet alleen de regel per aanroep

Cloudflare kent een instelling om alleen de eigen regel per aanroep uit te zetten
(`invocation_logs`). Dan zouden de regels van de Worker bewaard blijven. Ik heb dat niet gekozen:
de documentatie zegt niet of Cloudflare aan de regel van de Worker ook het webadres en de koppen van
het verzoek hangt. Zonder toegang tot een account kan ik dat niet controleren, en een tweede keer
iets beweren dat niet klopt wil ik niet. Daarom staat alles uit.

| Gevolg | Toelichting |
|---|---|
| Geen geschiedenis | Wat je niet live zag, is niet terug te vinden. Een storing van gisteren is niet meer uit te zoeken |
| Wil je wel een bewaard logboek | Dan kan het zo: `observability` aan met `invocation_logs` uit, één verzoek doen, en in het dashboard de bewaarde regel openen en kijken of er een webadres, koppen of een IP-adres bij staan. Het adres staat dan in elk geval niet meer in het webadres. Zeg het als je dat wilt; ik bouw het niet zonder dat jij die regel hebt gezien |

### Wat uit de documentatie komt en wat niet

| Punt | Bron |
|---|---|
| Een bewaarde regel per aanroep bevat het verzoek, het antwoord en verwante gegevens | Documentatie (Workers Logs) |
| `observability.enabled` aan: het logboek wordt bewaard | Documentatie (Wrangler configuration) |
| Live meekijken wordt niet bewaard | Documentatie (Real-time logs): "Real-time logs does not store Workers Logs" |
| Bewaartermijn: 3 dagen gratis, 7 dagen betaald | Documentatie (Workers Logs) |
| De instellingen `redact_query_string`, `logs.persist`, `traces` | Het schema van wrangler 4.164.0; `wrangler deploy --dry-run` accepteert ze |
| Bewaarde regels zelf wissen | Staat niet in de documentatie die ik las |
| Dat het logboek bij Cloudflare na het opnieuw plaatsen leeg blijft | **Niet gecontroleerd**; stap 8 in de README van de Worker |
| Dat `wrangler tail --format json` het IP-adres van de bezoeker toont | **Vermoeden**: het voorbeeld in de documentatie toont de koppen van het verzoek, leeg |

### Wat blijft

- De regels die Cloudflare al bewaard heeft, met de adressen van de proeven van Wim en zijn
  IP-adres, blijven staan tot de bewaartermijn om is. De app heeft de Worker nooit aangeroepen (de
  instelling is leeg), dus er staan geen adressen van bezoekers in.
- Wie live meekijkt, ziet de verzoeken van dat moment.
- EP-Online krijgt het adres in het webadres van de vraag van de Worker; zo schrijft de
  documentatie het voor. De Worker geeft de koppen van de bezoeker niet door.

## Gewijzigde bestanden

| Bestand | Wat |
|---|---|
| `tools/energielabel/src/energielabel.js` | Adres uit de inhoud (`leesTekst`, `leesAdres`), alleen `POST`, tellingen in de logregel (`weeg`) |
| `tools/energielabel/src/index.js` | Geeft de inhoud door, niet het webadres |
| `tools/energielabel/wrangler.jsonc` | `observability` uit, met uitleg |
| `tools/energielabel/README.md` | Correctie, "Wat Cloudflare vastlegt", de nieuwe vorm van de vraag, live meekijken, controle na het plaatsen, "Als het antwoord 'geen' is" met het ruwe antwoord |
| `site/adres.js`, `site/adres-app.js`, `site/sw.js` | Het tabblad stuurt het adres in de inhoud; opslag `v14` |
| `tests/test_energielabel.py`, `tests/js/run_energielabel.mjs`, `tests/test_adres.py`, `tests/test_site.py`, `tests/js/adres_smoke.js` | Aangepast en uitgebreid |
| `README.md`, het eerdere verslag | Bijgewerkt; correctie bovenaan |

Niet gewijzigd: `config.json` (de instelling blijft leeg), de planner, `dagelijks.yml`, `tests.yml`,
het schema, de scores.

## Getest

| Wat | Hoe | Uitkomst |
|---|---|---|
| Alle tests, lokaal | `python -m unittest discover tests`, 22:42 uur | 513 tests, geslaagd, 10 overgeslagen (zoals eerder) |
| De Worker | 59 tests: adres uit de inhoud, foute en te lange inhoud, alleen `POST`, het webadres wordt niet gelezen, de tellingen, logboek uit, de README zegt niet meer wat niet klopte | Geslaagd |
| Het tabblad in de browser (320 pixels) | De vraag is een `POST` naar het kale adres van de Worker, het adres staat in de inhoud en in geen enkel webadres, de inhoud gaat als platte tekst | Geslaagd |
| In de runtime van Cloudflare, lokaal | `wrangler dev` tegen een nagebootst EP-Online, 22:37 uur: gevonden, huisletter en toevoeging, platte tekst, niet gevonden, foute invoer, geen JSON, 5000 bytes, lege inhoud, `GET` met adres in het webadres, zonder herkomst, de voorvraag | Alle zoals bedoeld |
| De instellingen | `wrangler deploy --dry-run` (plaatst niets) | Geaccepteerd |

De testrun op de pull request staat onderaan, onder "De testrun op de pull request".

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| **De oorzaak van "geen" bij de twee adressen** | Niet gevonden. Nodig: de logregel of het ruwe antwoord, zie hierboven |
| **De nieuwe versie bij Cloudflare** | Alleen lokaal geprobeerd. Niet geplaatst: dat doet Wim, na het samenvoegen |
| **Of het logboek bij Cloudflare daarna leeg blijft** | Niet te controleren zonder het account. Stap 8 in de README |
| Of een browser werkelijk geen vraag vooraf stelt | Volgt uit de regels voor een verzoek met platte tekst zonder eigen koppen. In de browsertest wordt de Worker nagespeeld; een vraag vooraf is daar niet te zien. De Worker beantwoordt hem wel als hij komt |
| Bron die een fout geeft, die niet antwoordt, de grenzen, de teller na een herstart | In de lokale runtime alleen bij de eerste versie geprobeerd; dat deel van de code is niet gewijzigd. De tests onder Node dekken het voor de nieuwe versie |
| Of EP-Online een hoofdletter in de huisletter anders leest | Onbekend; de Worker geeft de letter door zoals hij binnenkomt |
| De voorwaarden van RVO bij de sleutel | Niet gelezen. Een zoekresultaat noemt `apikey.ep-online.nl/Home/TermsOfUse` en vat samen dat de sleutel persoonlijk is en niet aan derden mag worden gegeven. De Worker geeft de sleutel niet door, maar biedt wel een dienst aan bezoekers op die sleutel. Of dat mag, is aan Wim om te lezen |
| Op een echte telefoon | Niet te doen vanuit deze container |

## Wat Wim doet, in volgorde

1. De regel met "bron" van de twee proeven opzoeken in het dashboard (nu nog bewaard), of het ruwe
   antwoord opvragen. De uitkomst melden.
2. Als de pull request akkoord is: samenvoegen laten, daarna in `tools/energielabel` opnieuw
   `npx wrangler deploy`. De sleutel blijft staan.
3. Stap 5 (de proef, nu met `--data`) en stap 8 (het logboek blijft leeg) uit de README van de Worker.
4. Het adres van de Worker pas in `config.json` zetten als "geen" is opgelost.

## Buiten dit verslag

- **Niet samengevoegd:** de pull request blijft open tot Wim het zegt.
- **`energielabel_worker` in `config.json` is niet ingevuld.**
- **Niets geplaatst bij Cloudflare** en het account van Wim niet aangeraakt.
- **EP-Online is vijf keer aangeroepen zonder sleutel**, met een verzonnen adres (1000AA 1) of zonder
  adres. De twee adressen van Wim zijn nergens heen gestuurd en staan niet in de repo.
- **De planner, `dagelijks.yml`, `tests.yml` en het schema zijn niet gewijzigd.** `cache/ophaalcache.json`
  is niet gecommit en niets is geforceerd.
- **Voor de proef in de runtime** is wrangler gebruikt in een werkmap buiten de repo, met een verzonnen
  sleutel die alleen daar stond.
- **Twee subsessies**, alleen om documentatie te lezen (GitHub van EP-Online, Cloudflare). Eén
  zoekopdracht op het web. Niets met ElevenLabs.
