# Planner: de workflow starten vanaf Cloudflare

Een Cloudflare Worker die de workflow **Dagelijkse verversing** op GitHub start op de tijden van het
schema, in Nederlandse tijd. Bedoeld voor het geval dat GitHub de geplande runs zelf niet start.

**Stand 17-11-2026: voorbereid, niet live.** Er is niets bij Cloudflare geplaatst en er bestaat geen
token. De stappen onder "Live zetten" zijn niet uitgeprobeerd.

## Wat hij doet

| Onderdeel | Wat |
|---|---|
| Wanneer | Cloudflare roept de Worker elke vijf minuten aan (één cron-trigger, in UTC; Cloudflare kent geen tijdzones). De Worker rekent zelf uit of het op dat moment in Nederland een slot van het schema is, in zomer- en wintertijd |
| Slots | Werkdagen 06:45, 09:35, 10:20 en 16:10 uur; elke dag 12:10 uur; zondag 04:30 uur (volledige verversing). Gelijk aan `schedule` in `.github/workflows/dagelijks.yml`; een test vergelijkt de twee |
| Buiten een slot | Niets: geen verzoek aan GitHub, geen regel in het logboek |
| Op een slot | Vraagt de laatste runs op. Loopt of wacht er een, of is er in de laatste tien minuten een geslaagd, dan start hij niets. Anders start hij de workflow op `main` |
| Hoe de run zich gedraagt | Als een geplande run: de invoer `gepland` slaat de browsertests vooraf over. De controle van de live site na het publiceren draait wel. Op zondag 04:30 uur gaat `volledig` mee |
| Mislukt het starten | Eén nieuwe poging bij een storing aan de kant van GitHub. Daarna mislukt de aanroep, met de reden in het logboek van Cloudflare |
| Bereikbaarheid | De Worker heeft geen adres op internet en beantwoordt geen verzoeken; niemand kan er van buitenaf een run mee starten |

| Bestand | Wat |
|---|---|
| `src/index.js` | Het hoofdbestand: alleen de aanroep door de cron-trigger |
| `src/planner.js` | Het schema, de klok, de beslissing en de verzoeken aan GitHub |
| `wrangler.jsonc` | De instellingen voor Cloudflare. Het token staat er niet in |
| `tests/test_planner.py` (in de map `tests/` van de repo) | 24 tests, zonder Cloudflare en zonder netwerk |

## Live zetten

Doe dit in deze volgorde.

1. **Zorg dat de invoer `gepland` in de workflow op `main` staat.** Zonder die invoer weigert GitHub
   elke start van de planner (422, "Unexpected inputs provided"). De wijziging staat in dezelfde
   commit als deze map.

2. **Maak het token aan**, op GitHub onder Settings → Developer settings → Personal access tokens →
   Fine-grained tokens → Generate new token:

   | Veld | Waarde |
   |---|---|
   | Resource owner | Wim1201 |
   | Repository access | Only select repositories → `tilburg-signalen` |
   | Repository permissions | **Actions: Read and write**. Verder niets (Metadata: Read-only komt er vanzelf bij) |
   | Expiration | Naar keuze. Noteer de datum: na afloop start de planner niets meer |

3. **Log in bij Cloudflare** vanuit deze map:

   ```bash
   cd tools/planner
   ```

   ```bash
   npx wrangler login
   ```

4. **Zet het token als geheim.** Wrangler vraagt om de waarde; plak het token daar, niet in een
   bestand en niet in een chat. Bestaat de Worker nog niet, dan vraagt wrangler of hij hem mag
   aanmaken: ja.

   ```bash
   npx wrangler secret put GITHUB_TOKEN
   ```

5. **Plaats de Worker.** Dit mislukt zolang het geheim ontbreekt; dat is de bedoeling.

   ```bash
   npx wrangler deploy
   ```

6. **Controleer.** Volg het logboek tot na het eerstvolgende slot:

   ```bash
   npx wrangler tail tilburg-signalen-planner
   ```

   Er hoort één regel te komen met `"planner":"gestart"` of `"planner":"overgeslagen"`, en bij
   Actions op GitHub een run met de aanleiding `workflow_dispatch`.

Stoppen kan met:

```bash
npx wrangler delete tilburg-signalen-planner
```

## Goed om te weten

| Punt | Toelichting |
|---|---|
| Dubbele runs | Het schema in de workflow blijft staan. Start GitHub een geplande run alsnog, later dan de planner, dan draait die er gewoon achteraan: een extra verversing, verder zonder gevolg. Loopt de run van GitHub al als het slot aanbreekt, dan slaat de planner over |
| Verlopen of ingetrokken token | De planner start dan niets en meldt bij elk slot "GitHub weigert het token" in het logboek van Cloudflare. Op GitHub is daar niets van te zien. De app zelf meldt na 26 uur dat de gegevens niet zijn ververst |
| Wie de run start | De runs staan op naam van de eigenaar van het token |
| Grenzen van het gratis abonnement | Eén van de vijf cron-triggers per account; 288 aanroepen per dag van de 100.000 |
| Het schema wijzigen | Pas `schedule` in de workflow en `ROOSTER` in `src/planner.js` samen aan; de test faalt als ze verschillen. Slots moeten op een veelvoud van vijf minuten vallen |
| Logboek | Wordt bij Cloudflare bewaard (`observability`), te zien bij de Worker onder Logs |

## Getest

| Wat | Hoe | Uitkomst |
|---|---|---|
| Schema, klok, beslissing, verzoeken, foutafhandeling | `python -m unittest tests.test_planner`: 24 tests, GitHub nagebootst | Geslaagd |
| Zomer- en wintertijd | Elke aanroep van een heel jaar (2027) doorgerekend: elk slot valt precies één keer op elk van zijn dagen, ook op de dagen dat de klok verspringt | Geslaagd |
| Instellingen en bundel | `npx wrangler deploy --dry-run` met wrangler 4.163.0 (plaatst niets) | Geaccepteerd, 5 KiB |
| In de runtime van Cloudflare, lokaal | `npx wrangler dev --test-scheduled` en de cron-trigger nagebootst op vijf tijdstippen | Buiten een slot: klaar zonder verzoek. Op een slot in winter- en zomertijd en op zondag 04:30 uur: verzoek aan GitHub, dat een niet-bestaand token weigerde (401), waarna de aanroep als mislukt werd gemeld |

Niet getest: plaatsen bij Cloudflare, een echt token, een werkelijk gestarte run, en of Cloudflare
de cron-trigger stipt op tijd afvuurt.
