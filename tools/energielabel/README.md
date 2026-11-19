# Energielabel: één adres opvragen bij EP-Online

Een Cloudflare Worker die voor het tabblad **Adres** het energielabel van één adres opvraagt bij
EP-Online, het register van de Rijksdienst voor Ondernemend Nederland (RVO). EP-Online vraagt een
sleutel; die kent alleen deze Worker. De app vraagt de Worker, de Worker vraagt EP-Online.

Dit is een tweede Worker, los van de planner in `tools/planner/`. De planner is niet gewijzigd.

**Stand 19-11-2026, 08:58 uur: geplaatst door Wim, nog niet aan de app gekoppeld.** De Worker staat
bij Cloudflare met een echte sleutel van EP-Online, in de versie van vóór de wijziging hieronder. De
instelling `energielabel_worker` in `config.json` is leeg; de app roept de Worker dus niet aan.

**Gewijzigd op 18-11-2026 (na het plaatsen):** het adres staat niet meer in het webadres van de vraag
maar in de inhoud, en Cloudflare bewaart geen logboek meer. Zie "Wat Cloudflare vastlegt". Na het
samenvoegen moet de Worker opnieuw geplaatst worden (stap 4); de oude vorm van de vraag (`GET` met
`?postcode=`) werkt daarna niet meer.

## Wat hij doet

| Onderdeel | Wat |
|---|---|
| Vraag | `POST https://<adres van de Worker>/` met als inhoud `{"postcode":"5037PL","huisnummer":"118","huisletter":"a","toevoeging":"2"}`, alle waarden als tekst. Huisletter en toevoeging mogen ontbreken. Het adres staat nooit in het webadres: een webadres kan onderweg worden vastgelegd, een inhoud niet. Een inhoud van meer dan 400 bytes wordt niet gelezen |
| Controle van de invoer | De vormen uit de documentatie van EP-Online: postcode vier cijfers en twee letters, huisnummer 1 tot en met 99999, huisletter één letter, toevoeging één tot vier letters of cijfers. Wat niet past, wordt geweigerd zonder EP-Online te vragen |
| Wat hij EP-Online vraagt | `GET https://public.ep-online.nl/api/v5/PandEnergielabel/Adres` met `postcode`, `huisnummer`, `huisletter` en `huisnummertoevoeging`, en de sleutel in de kop `Authorization`. Zo staat het in de documentatie (public.ep-online.nl/swagger, versie 5) |
| Welk label | Van de registraties die vandaag nog geldig zijn, de laatst geregistreerde |
| Wat hij teruggeeft | Alleen: labelklasse, registratiedatum, geldig tot en het soort gebouw. Niets anders uit de registratie |
| Wachttijd | EP-Online krijgt acht seconden |
| Bewaren | Niets, behalve twee tellers (zie "Begrenzing"). Geen adressen, geen antwoorden |
| Logregel | Eén regel per verzoek met de uitkomst en tellingen, bijvoorbeeld `{"energielabel":"gevonden","bron":200,"registraties":2,"zonderKlasse":0,"zonderDatum":0,"verlopen":1}`. De regel zelf bevat geen adres en geen sleutel. Cloudflare bewaart hem niet; je ziet hem alleen als je live meekijkt (stap 7) |

De antwoorden:

| Status | Inhoud | Betekenis |
|---:|---|---|
| 200 | `{"status":"gevonden","klasse":"A","registratiedatum":"2023-06-12","geldigTot":"2033-06-12","gebouw":"Woningbouw"}` | Een geldig label |
| 404 | `{"status":"geen"}` | EP-Online vindt niets voor dit adres, of de Worker telde geen van de registraties als geldig label. EP-Online maakt geen verschil tussen "geen label" en "adres onbekend": beide zijn daar dezelfde `404`. Welke van de twee zegt de logregel: zie "Als het antwoord 'geen' is" |
| 400 | `{"status":"ongeldig","veld":"postcode"}` | De invoer past niet (`"veld":"invoer"`: de inhoud is geen adres in de vorm hierboven), of EP-Online weigert haar |
| 405 | `{"status":"ongeldig"}` | Geen `POST`. Ook de oude vorm met het adres in het webadres komt hier uit |
| 403 | `{"status":"geweigerd"}` | Het verzoek komt niet van de pagina van de app |
| 429 | `{"status":"teveel","grens":"minuut"}` of `"dag"` | De grens is bereikt; `Retry-After` zegt over hoeveel seconden het weer kan |
| 502, 503 | `{"status":"onbereikbaar"}` | EP-Online antwoordt niet, geeft een fout of weigert de sleutel; of de teller antwoordt niet |

| Bestand | Wat |
|---|---|
| `src/index.js` | Het hoofdbestand: de aanroep en de teller, de twee dingen die alleen bij Cloudflare bestaan |
| `src/energielabel.js` | Alles wat de Worker met een verzoek doet |
| `wrangler.jsonc` | De instellingen voor Cloudflare. De sleutel staat er niet in |
| `tests/test_energielabel.py` (in de map `tests/` van de repo) | 67 tests, zonder Cloudflare, zonder netwerk en zonder sleutel |

## Wat Cloudflare vastlegt

**Correctie, 18-11-2026.** Dit bestand zei eerder dat het logboek nooit het adres bevat. Dat klopte
alleen voor de regel die de Worker zelf schrijft. Wim stelde na het plaatsen vast dat Cloudflare bij
elk verzoek zelf ook een regel bewaart, met de volledige vraag: het webadres met postcode en
huisnummer, en het IP-adres van de bezoeker. Ik had dat niet nagezocht.

| | Vóór de wijziging | Nu |
|---|---|---|
| Het adres dat gevraagd wordt | In het webadres van de vraag (`?postcode=...`) | In de inhoud van een `POST`. De Worker kijkt niet meer naar het webadres |
| Het logboek bij Cloudflare (`observability` in `wrangler.jsonc`) | Aan: Cloudflare bewaart per verzoek een eigen regel met het verzoek en het antwoord, plus de regel van de Worker | Uit: Cloudflare bewaart van deze Worker geen logboek en geen sporen (traces) |
| Live meekijken (`wrangler tail`, of **Logs → Live** in het dashboard) | Kan | Kan nog steeds. Dat wordt getoond en niet bewaard |

Wat hiervan uit de documentatie van Cloudflare komt (gelezen op 18-11-2026) en wat niet:

| Punt | Bron |
|---|---|
| Een bewaarde regel per aanroep bevat "details such as the Request, Response, and related metadata" | Documentatie (Workers Logs) |
| `observability.enabled` aan betekent dat het logboek van de Worker bewaard wordt; uit dus niet | Documentatie (Wrangler configuration) |
| Wat je live ziet, wordt niet bewaard | Documentatie (Real-time logs) |
| Bewaartermijn van wat al is vastgelegd: 3 dagen in het gratis abonnement, 7 dagen in het betaalde | Documentatie (Workers Logs) |
| Of je bewaarde regels zelf kunt wissen | Staat niet in de documentatie die ik las. Ik ga ervan uit dat ze na de bewaartermijn verdwijnen |
| Of de regel van de Worker zelf (`{"energielabel":...}`) bij Cloudflare ook het webadres en de koppen van het verzoek meekrijgt | Staat niet in de documentatie. Daarom staat het hele logboek uit en niet alleen de regel per aanroep |
| Dat het logboek na het opnieuw plaatsen echt leeg blijft | **Niet gecontroleerd**: dat kan alleen in jouw account. Zie stap 8 |

Wat blijft, en niet uit te zetten is:

- **Live meekijken toont het verzoek van dat moment.** Het webadres bevat geen adres meer. In de vorm
  `--format json` toont `wrangler tail` ook de koppen van elk verzoek; ik ga ervan uit dat daar het
  IP-adres van de bezoeker bij zit (niet uitgeprobeerd). Gebruik de gewone vorm, en kijk alleen mee
  als je iets uitzoekt.
- **Cloudflare verwerkt elk verzoek** en ziet daarbij het IP-adres, zoals elke partij die een site
  aanbiedt. De tellingen in het dashboard (aantallen verzoeken en fouten) blijven.
- **EP-Online krijgt het adres**, in het webadres van de vraag van de Worker; zo schrijft zijn
  documentatie het voor. De Worker geeft de koppen van de bezoeker niet door. Wat EP-Online zelf
  vastlegt, weet ik niet.
- **De regels van vóór het opnieuw plaatsen** staan nog bij Cloudflare tot de bewaartermijn om is,
  met de adressen die toen zijn opgevraagd.

## Afscherming: wat ze wel en niet tegenhoudt

| Maatregel | Houdt tegen | Houdt niet tegen |
|---|---|---|
| **Alleen de herkomst van de site** (`https://wim1201.github.io`) | Een andere website die de Worker door de browser van haar bezoekers laat aanroepen: een browser zet de herkomst zelf en een pagina kan die niet vervalsen. Zonder de juiste herkomst vraagt de Worker EP-Online niets | **Iemand met een eigen programma.** Wie buiten een browser om een verzoek stuurt, kan elke herkomst opgeven. Het adres van de Worker staat in het gegevensbestand van de app en is dus voor iedereen te vinden. De herkomst is daarmee een drempel, geen slot |
| **De sleutel als geheim bij Cloudflare** | Dat de sleutel in de repo, in de app, in een antwoord of in een logregel komt. Niemand kan hem via de Worker te zien krijgen | Dat de sleutel gebruikt wordt: iedereen die de Worker bereikt, vraagt via de sleutel op. Alleen wat de Worker toelaat, maar wel op jouw naam |
| **Begrenzing** (20 per minuut, 300 per dag, over iedereen samen) | Dat de sleutel zwaar belast wordt. Wat er ook gebeurt: EP-Online krijgt van deze Worker nooit meer dan 300 verzoeken per dag | **Dat iemand de dag opmaakt.** De telling is niet per bezoeker. Wie 300 verzoeken stuurt, zorgt dat het vak Energielabel voor de rest van de dag "te veel verzoeken" toont. Meer dan dat vak raakt het niet |
| **Alleen één adres, alleen vier gegevens** | Dat de Worker gebruikt wordt om het register leeg te lezen in grote stappen, of om meer uit een registratie te halen dan het tabblad toont | Dat iemand binnen de grens adressen één voor één opvraagt. EP-Online heeft daarvoor zelf een openbaar zoekscherm per adres |

Bewust niet gedaan: tellen per bezoeker. Dat vraagt het IP-adres van een bezoeker bij te houden; de
Worker zelf leest dat adres niet. (Cloudflare legde het tot de wijziging van 18-11-2026 wel vast: zie
"Wat Cloudflare vastlegt".)

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
   postcode en huisnummer. Het adres gaat mee als inhoud (`--data`), niet in het webadres:

   ```bash
   curl -i -H "Origin: https://wim1201.github.io" --data '{"postcode":"5037PL","huisnummer":"118"}' "https://tilburg-signalen-energielabel.<jouw-subdomein>.workers.dev/"
   ```

   Met een huisletter of toevoeging: `--data '{"postcode":"5037PL","huisnummer":"118","huisletter":"a"}'`
   of `"toevoeging":"2"`.

   Je hoort `HTTP/2 200` te zien met `"status":"gevonden"` en het label, of `404` met
   `"status":"geen"`. Zie je `502` met `"status":"onbereikbaar"`, kijk dan live mee (stap 7):
   `"sleutel geweigerd"` betekent dat EP-Online de sleutel niet aanneemt.

   En zonder herkomst, dat hoort geweigerd te worden (`403`):

   ```bash
   curl -i --data '{"postcode":"5037PL","huisnummer":"118"}' "https://tilburg-signalen-energielabel.<jouw-subdomein>.workers.dev/"
   ```

6. **Vul het adres van de Worker in.** In `config.json`, in de hoofdmap van de repo:

   ```json
   "energielabel_worker": "https://tilburg-signalen-energielabel.<jouw-subdomein>.workers.dev",
   ```

   Zet dat via een pull request in `main`. De verversing die daarop volgt, zet het adres in de app;
   daarna toont het vak Energielabel op het tabblad Adres het label. Staat de instelling leeg, dan
   blijft het vak zoals het was: alleen de link naar EP-Online.

7. **Live meekijken**, als je wilt zien hoe een verzoek afloopt. Start dit in een tweede venster en
   doe daarna het verzoek van stap 5; bij elk verzoek verschijnt de logregel van de Worker. Stop met
   Ctrl-C.

   ```bash
   npx wrangler tail tilburg-signalen-energielabel
   ```

   In het dashboard kan het ook: **Workers & Pages** → `tilburg-signalen-energielabel` → **Logs** →
   **Live**. Er wordt niets bewaard: wat je niet live zag, is er niet meer.

8. **Controleer dat Cloudflare niets meer bewaart.** Doe na het plaatsen één verzoek (stap 5) en kijk
   in het dashboard: **Workers & Pages** → `tilburg-signalen-energielabel` → **Observability**. Daar
   horen alleen regels van vóór het plaatsen te staan, en geen nieuwe. Onder **Settings** →
   **Observability** hoort het logboek uit te staan. Staan er toch nieuwe regels, meld het dan: dit
   heb ik niet kunnen controleren.

## Hoe EP-Online echt antwoordt

Door Wim rechtstreeks opgevraagd op 19-11-2026, met hetzelfde pad, dezelfde parameters en dezelfde
koppen als de Worker. Ik heb het antwoord zelf niet gezien; dit is zijn beschrijving.

| Geval | Antwoord |
|---|---|
| Adres met een label | `200`, `application/json; x-api-version=5`. Een lijst met één registratie |
| Adres zonder label, of een adres dat EP-Online niet kent | `404`, `application/problem+json` met alleen `type`, `title`, `status` en `traceId`. De twee gevallen zijn niet te onderscheiden |

De velden van een registratie, in deze volgorde: `Registratiedatum`, `Opnamedatum`, `Geldig_tot`,
`Certificaathouder`, `Soort_opname`, `Status`, `Berekeningstype`, `Op_basis_van_referentiegebouw`,
`Gebouwklasse`, `Gebouwtype`, `Postcode`, `Huisnummer` (een getal), `BAGVerblijfsobjectID`,
`BAGPandIDs`, `Bouwjaar`, `Gebruiksoppervlakte_thermische_zone`, `Compactheid`, `Energieklasse`,
`Energiebehoefte`, `PrimaireFossieleEnergie`, `Aandeel_hernieuwbare_energie`,
`Temperatuuroverschrijding`, `Warmtebehoefte`, `BerekendeCO2Emissie`, `BerekendeEnergieverbruik`. Er is
geen veld `Labelklasse` of `Registratienummer`. Velden zonder waarde ontbreken.

| Wat de Worker leest | Veld | Vorm | Wat de Worker ermee doet |
|---|---|---|---|
| Labelklasse | `Energieklasse` | Tekst, bijvoorbeeld `"A"` | Overgenomen |
| Registratiedatum | `Registratiedatum` | `"JJJJ-MM-DDTuu:mm:ss.fff"`, zonder tijdzone | De eerste tien tekens zijn de dag. Het hele tijdstip bepaalt welke registratie de laatste is |
| Geldig tot | `Geldig_tot` | `"JJJJ-MM-DDT00:00:00"`, zonder tijdzone | De eerste tien tekens zijn de dag. Geldig tot en met die dag, Nederlandse tijd |
| Soort gebouw | `Gebouwklasse` | Tekst | Overgenomen |

De datums worden niet omgerekend: een datum zonder tijdzone kan bij omrekenen een dag verschuiven. De
dag die EP-Online schrijft, is de dag die het tabblad toont.

## Als het antwoord "geen" is terwijl je een label verwacht

De Worker geeft `404` met `"status":"geen"` in twee gevallen, en de logregel zegt welke:

| Logregel | Betekenis |
|---|---|
| `{"energielabel":"geen","bron":404}` | EP-Online zelf antwoordde "geen informatie gevonden" op deze schrijfwijze van het adres |
| `{"energielabel":"geen geldig label","bron":200,"registraties":2,"zonderKlasse":0,"zonderDatum":0,"verlopen":2}` | EP-Online stuurde registraties, maar de Worker telde er geen als geldig label. De tellingen zeggen waarom: geen labelklasse, geen leesbare datum, of verlopen |

Staat er `zonderKlasse` of `zonderDatum` bij een adres dat een geldig label heeft, dan leest de Worker
het antwoord verkeerd (de velden heten of zien er anders uit dan in "Hoe EP-Online echt antwoordt") en
moet de Worker worden aangepast. Staat er `"bron":404`, dan vindt EP-Online zelf niets: er is geen
label, of EP-Online kent het adres niet in deze schrijfwijze. Vergelijk dan met het zoekscherm op
ep-online.nl.

**Het ruwe antwoord van EP-Online bekijken, zonder dat de sleutel in beeld komt.** In Terminal (zsh
of bash). De eerste regel vraagt om de sleutel en toont niet wat je plakt; hij komt ook niet in de
geschiedenis van de terminal:

```bash
printf 'Plak de sleutel en druk op Enter (je ziet niets): '; read -rs EPKEY; echo
```

Vul je eigen postcode en huisnummer in:

```bash
curl -sS -i -H "Authorization: $EPKEY" -H "Accept: application/json" "https://public.ep-online.nl/api/v5/PandEnergielabel/Adres?postcode=5037PL&huisnummer=118"
```

Met een huisletter komt er `&huisletter=a` achter, met een toevoeging `&huisnummertoevoeging=2`.
Gebruik niet `-v`: dat toont de sleutel. Haal de sleutel daarna uit het geheugen van de terminal:

```bash
unset EPKEY
```

Je ziet de status (`HTTP/1.1 200` of `404`), de koppen van het antwoord en de inhoud. Bij `200` is de
inhoud een lijst registraties; de Worker leest daaruit `Energieklasse`, `Registratiedatum`,
`Geldig_tot` en `Gebouwklasse`. Het antwoord bevat openbare gegevens van het label, geen sleutel.

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
| Verlopen of ingetrokken sleutel | Het vak toont "de dienst is niet bereikbaar". Live meekijken (stap 7) toont dan `"sleutel geweigerd"`; achteraf is dat niet terug te zien, want er wordt niets bewaard |
| Het logboek weer aanzetten | Niet doen zonder te weten wat erin komt: zie "Wat Cloudflare vastlegt". `observability` in `wrangler.jsonc`, daarna stap 4. Een test bewaakt dat het uit staat |
| De vraag zonder voorvraag | De app stuurt de inhoud als platte tekst, zonder eigen koppen. Een browser stelt dan geen vraag vooraf (preflight), dus één adres is één aanroep van de Worker |
| Toevoeging | De documentatie van EP-Online noemt voor de toevoeging precies vier tekens. In de BAG is een toevoeging één tot vier tekens. De Worker laat één tot vier door; weigert EP-Online een kortere, dan komt dat terug als "ongeldig" en toont het vak dat er voor dit adres geen label kan worden opgevraagd |

## Getest

| Wat | Hoe | Uitkomst |
|---|---|---|
| Invoer, herkomst, begrenzing, keuze van het label, alle uitkomsten, de tellingen in de logregel, sleutel en adres buiten de logregel, logboek uit | `python -m unittest tests.test_energielabel`: 67 tests, EP-Online nagebootst naar zijn documentatie | Geslaagd |
| Het antwoord in de vorm van de echte dienst | 8 van die tests: de 25 velden in de volgorde die Wim zag, datums zonder tijdzone, de registratiedatum met milliseconden, een `404` met een probleembeschrijving. Verzonnen waarden | Geslaagd |
| Instellingen en bundel | `wrangler deploy --dry-run` met wrangler 4.164.0 (plaatst niets) | Geaccepteerd, 10 KiB |
| In de runtime van Cloudflare, lokaal (19-11-2026, 08:56 uur) | `wrangler dev` tegen een nagebootst EP-Online dat antwoordt in de vorm van de echte dienst, met dezelfde `Content-Type` | Gevonden (klasse, beide datums, soort gebouw), `404` met probleembeschrijving geeft "geen" met `"bron":404`, een verlopen label geeft "geen geldig label" met `"verlopen":1` |
| In de runtime van Cloudflare, lokaal (18-11-2026, 22:37 uur, de versie met het adres in de inhoud) | `wrangler dev` tegen een nagebootst EP-Online op dezelfde machine, met een verzonnen sleutel | Gevonden, huisletter en toevoeging, de inhoud als platte tekst zoals een browser hem stuurt, niet gevonden bij de bron, foute invoer, een inhoud die geen JSON is, een inhoud van 5000 bytes, een lege inhoud, `GET` met het adres in het webadres (405, niets gevraagd aan de bron), zonder herkomst, de voorvraag: alle zoals bedoeld |
| In de runtime van Cloudflare, lokaal (18-11-2026, de eerste versie) | Als hierboven | Ook: een bron die een fout geeft, een bron die niet antwoordt (afgebroken na 8,0 seconden), een bron die weg is, de grens per minuut en per dag, en de teller na een herstart. Niet herhaald voor de nieuwe versie; dat deel van de code is niet gewijzigd |

In die lokale runtime kwam bij de eerste versie één fout aan het licht die de tests onder Node niet
zagen: de Worker vroeg EP-Online op een manier die Cloudflare niet kent (doorverwijzingen weigeren met
`"error"`), waardoor elk verzoek mislukte. Hersteld; een test bewaakt het.

**Met de echte dienst, door Wim (18 en 19-11-2026):** de sleutel wordt aangenomen (eerst `502` met een
verkeerde sleutel, daarna een antwoord binnen 285 ms). Twee adressen gaven `404` met `"geen"`. **Die
waren terecht:** Wim vroeg EP-Online rechtstreeks en ook daar, en op de website van EP-Online, is voor
die adressen niets te vinden. De vraag van de Worker is dus goed. Voor adressen met een label
antwoordt EP-Online zoals onder "Hoe EP-Online echt antwoordt" staat.

**De Worker las die namen en vormen al goed.** Eén ding is hersteld: van twee registraties op dezelfde
dag koos de Worker de eerste uit de lijst en niet de laatst geregistreerde, omdat hij alleen de dag
vergeleek. Nu vergelijkt hij het hele tijdstip. In wat Wim zag kwam dat niet voor (de lijst had één
registratie).

**Niet getest door mij: de echte sleutel en de echte dienst.** Ik heb geen sleutel en heb EP-Online
alleen zonder sleutel aangeroepen; de vorm van het antwoord ken ik uit de beschrijving van Wim. Niet
gecontroleerd is daarmee:

- **De Worker zelf met een adres dat een label heeft.** Wims proef ging rechtstreeks naar EP-Online, niet
  via de Worker. De tests en de lokale runtime gebruiken een nagebootst antwoord in dezelfde vorm.
- Of EP-Online ooit meer dan één registratie in de lijst zet, en of het verlopen labels meestuurt of
  dan `404` geeft.
- Of "geldig tot" de laatste geldige dag is of de eerste dag daarna. De Worker rekent die dag nog als
  geldig; dat scheelt één dag.
- In welke tijdzone de datums bedoeld zijn. De Worker neemt de dag zoals hij er staat.
- Een adres met een huisletter of een toevoeging dat een label heeft: of EP-Online een hoofdletter
  anders leest dan een kleine, en wat het met een korte toevoeging doet.
- Of EP-Online zelf een grens aan het aantal verzoeken kent.
- De nieuwe versie bij Cloudflare zelf (alleen lokaal), of het logboek daar na het plaatsen leeg
  blijft, en de teller in het echte netwerk van Cloudflare.
