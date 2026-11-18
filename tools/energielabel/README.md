# Energielabel: één adres opvragen bij EP-Online

Een Cloudflare Worker die voor het tabblad **Adres** het energielabel van één adres opvraagt bij
EP-Online, het register van de Rijksdienst voor Ondernemend Nederland (RVO). EP-Online vraagt een
sleutel; die kent alleen deze Worker. De app vraagt de Worker, de Worker vraagt EP-Online.

Dit is een tweede Worker, los van de planner in `tools/planner/`. De planner is niet gewijzigd.

**Stand 18-11-2026: voorbereid, niet live.** Er is niets bij Cloudflare geplaatst en er is geen sleutel
aangevraagd. De stappen onder "Plaatsen" zijn niet uitgeprobeerd met een echte sleutel.

## Wat hij doet

| Onderdeel | Wat |
|---|---|
| Vraag | `GET https://<adres van de Worker>/?postcode=5037PL&huisnummer=118&huisletter=a&toevoeging=2`. Huisletter en toevoeging mogen ontbreken |
| Controle van de invoer | De vormen uit de documentatie van EP-Online: postcode vier cijfers en twee letters, huisnummer 1 tot en met 99999, huisletter één letter, toevoeging één tot vier letters of cijfers. Wat niet past, wordt geweigerd zonder EP-Online te vragen |
| Wat hij EP-Online vraagt | `GET https://public.ep-online.nl/api/v5/PandEnergielabel/Adres` met `postcode`, `huisnummer`, `huisletter` en `huisnummertoevoeging`, en de sleutel in de kop `Authorization`. Zo staat het in de documentatie (public.ep-online.nl/swagger, versie 5) |
| Welk label | Van de registraties die vandaag nog geldig zijn, de laatst geregistreerde |
| Wat hij teruggeeft | Alleen: labelklasse, registratiedatum, geldig tot en het soort gebouw. Niets anders uit de registratie |
| Wachttijd | EP-Online krijgt acht seconden |
| Bewaren | Niets, behalve twee tellers (zie "Begrenzing"). Geen adressen, geen antwoorden |
| Logboek | Eén regel per verzoek met de uitkomst, bijvoorbeeld `{"energielabel":"gevonden","bron":200,"registraties":2}`. Nooit het adres en nooit de sleutel |

De antwoorden:

| Status | Inhoud | Betekenis |
|---:|---|---|
| 200 | `{"status":"gevonden","klasse":"A","registratiedatum":"2023-06-12","geldigTot":"2033-06-12","gebouw":"Woningbouw"}` | Een geldig label |
| 404 | `{"status":"geen"}` | EP-Online kent geen label voor dit adres, of alleen verlopen labels |
| 400 | `{"status":"ongeldig","veld":"postcode"}` | De invoer past niet, of EP-Online weigert haar |
| 403 | `{"status":"geweigerd"}` | Het verzoek komt niet van de pagina van de app |
| 429 | `{"status":"teveel","grens":"minuut"}` of `"dag"` | De grens is bereikt; `Retry-After` zegt over hoeveel seconden het weer kan |
| 502, 503 | `{"status":"onbereikbaar"}` | EP-Online antwoordt niet, geeft een fout of weigert de sleutel; of de teller antwoordt niet |

| Bestand | Wat |
|---|---|
| `src/index.js` | Het hoofdbestand: de aanroep en de teller, de twee dingen die alleen bij Cloudflare bestaan |
| `src/energielabel.js` | Alles wat de Worker met een verzoek doet |
| `wrangler.jsonc` | De instellingen voor Cloudflare. De sleutel staat er niet in |
| `tests/test_energielabel.py` (in de map `tests/` van de repo) | 50 tests, zonder Cloudflare, zonder netwerk en zonder sleutel |

## Afscherming: wat ze wel en niet tegenhoudt

| Maatregel | Houdt tegen | Houdt niet tegen |
|---|---|---|
| **Alleen de herkomst van de site** (`https://wim1201.github.io`) | Een andere website die de Worker door de browser van haar bezoekers laat aanroepen: een browser zet de herkomst zelf en een pagina kan die niet vervalsen. Zonder de juiste herkomst vraagt de Worker EP-Online niets | **Iemand met een eigen programma.** Wie buiten een browser om een verzoek stuurt, kan elke herkomst opgeven. Het adres van de Worker staat in het gegevensbestand van de app en is dus voor iedereen te vinden. De herkomst is daarmee een drempel, geen slot |
| **De sleutel als geheim bij Cloudflare** | Dat de sleutel in de repo, in de app, in een antwoord of in het logboek komt. Niemand kan hem via de Worker te zien krijgen | Dat de sleutel gebruikt wordt: iedereen die de Worker bereikt, vraagt via de sleutel op. Alleen wat de Worker toelaat, maar wel op jouw naam |
| **Begrenzing** (20 per minuut, 300 per dag, over iedereen samen) | Dat de sleutel zwaar belast wordt. Wat er ook gebeurt: EP-Online krijgt van deze Worker nooit meer dan 300 verzoeken per dag | **Dat iemand de dag opmaakt.** De telling is niet per bezoeker. Wie 300 verzoeken stuurt, zorgt dat het vak Energielabel voor de rest van de dag "te veel verzoeken" toont. Meer dan dat vak raakt het niet |
| **Alleen één adres, alleen vier gegevens** | Dat de Worker gebruikt wordt om het register leeg te lezen in grote stappen, of om meer uit een registratie te halen dan het tabblad toont | Dat iemand binnen de grens adressen één voor één opvraagt. EP-Online heeft daarvoor zelf een openbaar zoekscherm per adres |

Bewust niet gedaan: tellen per bezoeker. Dat vraagt het IP-adres van een bezoeker bij te houden; de
Worker leest dat adres nu niet eens.

**Niet uitgezocht:** of de voorwaarden van RVO bij de sleutel toestaan dat je hem zo gebruikt, via een
eigen dienst voor bezoekers van een site. Lees dat bij het aanvragen.

## Plaatsen

Doe dit in deze volgorde. Je hebt het account bij Cloudflare en `npx wrangler` van de planner.

1. **Vraag de sleutel aan** bij RVO, op `https://apikey.ep-online.nl` (dat adres noemt de documentatie
   van EP-Online). Bewaar hem zoals een wachtwoord; zet hem niet in een bestand in de repo en niet in
   een chat. Hoe RVO de sleutel levert en hoe lang dat duurt, heb ik niet uitgeprobeerd.

2. **Log in bij Cloudflare** vanuit deze map:

   ```bash
   cd tools/energielabel
   ```

   ```bash
   npx wrangler login
   ```

3. **Zet de sleutel als geheim.** Wrangler vraagt om de waarde; plak de sleutel daar. Bestaat de Worker
   nog niet, dan vraagt wrangler of hij hem mag aanmaken: ja.

   ```bash
   npx wrangler secret put EP_ONLINE_KEY
   ```

4. **Plaats de Worker.** Dit mislukt zolang het geheim ontbreekt; dat is de bedoeling.

   ```bash
   npx wrangler deploy
   ```

   Wrangler toont aan het eind het adres, in de vorm
   `https://tilburg-signalen-energielabel.<jouw-subdomein>.workers.dev`. Noteer het.

5. **Controleer met een adres waarvan je het label kent.** Vul het adres van stap 4 in en je eigen
   postcode en huisnummer:

   ```bash
   curl -i -H "Origin: https://wim1201.github.io" "https://tilburg-signalen-energielabel.<jouw-subdomein>.workers.dev/?postcode=5037PL&huisnummer=118"
   ```

   Je hoort `HTTP/2 200` te zien met `"status":"gevonden"` en het label, of `404` met
   `"status":"geen"` als er geen geldig label is. Zie je `502` met `"status":"onbereikbaar"`, kijk dan
   in het logboek (stap 7): `"sleutel geweigerd"` betekent dat EP-Online de sleutel niet aanneemt.

   En zonder herkomst, dat hoort geweigerd te worden (`403`):

   ```bash
   curl -i "https://tilburg-signalen-energielabel.<jouw-subdomein>.workers.dev/?postcode=5037PL&huisnummer=118"
   ```

6. **Vul het adres van de Worker in.** In `config.json`, in de hoofdmap van de repo:

   ```json
   "energielabel_worker": "https://tilburg-signalen-energielabel.<jouw-subdomein>.workers.dev",
   ```

   Zet dat via een pull request in `main`. De verversing die daarop volgt, zet het adres in de app;
   daarna toont het vak Energielabel op het tabblad Adres het label. Staat de instelling leeg, dan
   blijft het vak zoals het was: alleen de link naar EP-Online.

7. **Het logboek volgen**, als je wilt zien wat er gebeurt:

   ```bash
   npx wrangler tail tilburg-signalen-energielabel
   ```

Stoppen kan op twee manieren. De instelling in `config.json` weer leegmaken haalt het label uit de app
en laat de Worker staan. De Worker weghalen:

```bash
npx wrangler delete tilburg-signalen-energielabel
```

## Goed om te weten

| Punt | Toelichting |
|---|---|
| De sleutel vervangen | Vraag bij RVO een nieuwe aan en herhaal stap 3. De Worker hoeft niet opnieuw geplaatst |
| De grenzen wijzigen | `PER_MINUUT` en `PER_DAG` in `wrangler.jsonc`, daarna stap 4. De dag loopt van middernacht tot middernacht, Nederlandse tijd |
| Een andere site toelaten | `HERKOMST` in `wrangler.jsonc` is precies één adres. De app lokaal draaien tegen de echte Worker kan daardoor niet; dat is de bedoeling |
| De teller | Eén klein object bij Cloudflare met eigen opslag (een Durable Object). Het telt exact, waar een verzoek ook binnenkomt. Antwoordt het niet, dan vraagt de Worker EP-Online niets |
| Grenzen van het gratis abonnement | 100.000 aanroepen van Workers per dag over het hele account; de planner gebruikt er 288. De teller valt onder het gratis gebruik van Durable Objects. Bij 300 labels per dag blijft dit er ver onder |
| Verlopen of ingetrokken sleutel | Het vak toont "de dienst is niet bereikbaar" en het logboek meldt `"sleutel geweigerd"` |
| Toevoeging | De documentatie van EP-Online noemt voor de toevoeging precies vier tekens. In de BAG is een toevoeging één tot vier tekens. De Worker laat één tot vier door; weigert EP-Online een kortere, dan komt dat terug als "ongeldig" en toont het vak dat er voor dit adres geen label kan worden opgevraagd |

## Getest

| Wat | Hoe | Uitkomst |
|---|---|---|
| Invoer, herkomst, begrenzing, keuze van het label, alle uitkomsten, sleutel en adres buiten het logboek | `python -m unittest tests.test_energielabel`: 50 tests, EP-Online nagebootst naar zijn documentatie | Geslaagd |
| Instellingen en bundel | `npx wrangler deploy --dry-run` met wrangler 4.164.0 (plaatst niets) | Geaccepteerd, 8 KiB |
| In de runtime van Cloudflare, lokaal | `npx wrangler dev` tegen een nagebootst EP-Online op dezelfde machine, met een verzonnen sleutel | Gevonden, toevoeging, niet gevonden, foute invoer, verkeerde en ontbrekende herkomst, een bron die een fout geeft, een bron die niet antwoordt (afgebroken na 8,0 seconden) en een bron die weg is: alle zoals bedoeld. De grens per minuut en de grens per dag grepen in, en de teller bleef staan na een herstart |

In die lokale runtime kwam één fout aan het licht die de tests onder Node niet zagen: de Worker vroeg
EP-Online op een manier die Cloudflare niet kent (doorverwijzingen weigeren met `"error"`), waardoor elk
verzoek mislukte. Hersteld; een test bewaakt het.

**Niet getest: de echte sleutel en de echte dienst.** Er is geen sleutel, dus EP-Online is nooit
aangeroepen. Niet getest is daarmee: of de sleutel zonder iets ervoor in `Authorization` hoort (zo staat
het in de documentatie), hoe een echt antwoord eruitziet, of EP-Online verlopen labels meestuurt, wat het
met een korte toevoeging doet, en of het zelf een grens kent. Ook niet getest: het plaatsen bij
Cloudflare, en de teller in het echte netwerk van Cloudflare.
