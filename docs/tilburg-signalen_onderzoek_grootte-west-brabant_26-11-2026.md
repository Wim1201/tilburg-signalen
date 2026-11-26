# Tilburg Signalen: onderzoek grootte `regio-west-brabant.json`

| | |
|---|---|
| Datum | 26-11-2026, 08:00 – 09:00 uur; aangevuld om 09:15 uur met het besluit van Wim, het open punt en de herkomst van 1,5 MB |
| Versie | `main` op commit `eae2055`, branch `claude/charming-goodall-lvhulj`; niets gebouwd |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | logs van de runs 69, 71, 77, 87, 97 – 103, 106 en 107 (via GitHub); het Pages-pakket van run 102 (`regio-west-brabant.json` van 25-11, 17:09 uur); de live site, opgehaald 26-11 rond 08:00 uur (stand van run 107) |
| Van / aan | Claude Code aan Wim |
| Aanleiding | Run 102 (25-11, 17:07 uur): "regio-west-brabant.json is 1.456 kB, 97 procent" |
| Vervolg op | `tilburg-signalen_meting_west-brabant-andere-rubrieken_19-11-2026.md`, `tilburg-signalen_verslag_dekking-en-regios_17-11-2026.md` |

**Dit is een onderzoek. Er is niets gebouwd; code, cache en databestanden zijn niet gewijzigd.**

## Besluit van Wim (26-11-2026)

| Keuze | Besluit |
|---|---|
| Optie d (afleidbare `url` en `urlTekst` niet meer opschrijven) | Gepland voor januari 2027; nu niet bouwen. Zie "Open punt" |
| Opties a, b en c | Niet |

## 1. Het bestand groeit niet sneller: de 97% is de piek van de woensdag

### Grootte per run

| Run | Moment | Berichten West-Brabant | `regio-west-brabant.json` | Deel van 1.500 kB |
|---|---|---:|---:|---:|
| 69 | za 21-11, 12:10 | 1.471 | 1.379 kB | 91% |
| 71 | zo 22-11, 04:30 (volledig) | 1.470 | 1.378 kB | 91% |
| 77 | ma 23-11, 06:45 | 1.470 | 1.378 kB | 91% |
| 87 | di 24-11, 06:45 | 1.479 | 1.385 kB | 92% |
| 97 | wo 25-11, 06:45 | 1.466 | 1.373 kB | 91% |
| 98 | **wo 25-11, 09:35** | **1.550** | **1.456 kB** | **97%** |
| 99 – 103 | wo 25-11, 10:20 – 19:48 | 1.550 | 1.456 kB | 97% |
| 106 | do 26-11, 00:35 | 1.455 | 1.364 kB | 90% |
| 107 | do 26-11, 06:45 (nu live) | 1.455 | 1.364 kB | 90% |

Van zaterdag tot woensdagochtend lag het bestand vlak rond 1.375 kB. Woensdag om 09:35 uur kwam er
84 berichten bij, om middernacht vielen er 95 af. Op donderdag is het kleiner dan zaterdag.

### Waarom de woensdag

| Feit | Waar gezien |
|---|---|
| De meeste West-Brabantse gemeenten publiceren op woensdag. Van de 1.403 vergunningen in het bestand van 25-11 zijn er 625 van een woensdag (do 319, vr 199, ma 179, di 81). Op woensdag vooral Bergen op Zoom, Halderberge, Breda, Etten-Leur en Rucphen | bestand van run 102 |
| Per woensdag 73 tot 95 berichten: 14-10 95, 21-10 95, 28-10 94, 04-11 73, 11-11 95, 18-11 91, 25-11 82 | idem |
| Het venster van 42 dagen telt de grensdag mee. Op 25-11 stonden de berichten van 14-10 er nog in (25-11 min 42 dagen); om middernacht vielen ze eruit. Alle 95 berichten die verdwenen, waren van 14-10 | verschil tussen run 102 en run 107 |
| Van woensdag 09:35 uur tot middernacht staan er dus twee woensdagen in het venster: ongeveer 85 – 95 kB extra, zo'n 15 uur per week | idem |
| Dat was vóór de extra rubrieken ook al zo: op wo 18-11 ging West-Brabant van 1.274 kB (08:20) naar 1.334 kB (09:15) | dekkingsverslag van 17-11 |

### Per week

Publicaties per week in het bestand van 25-11 (alleen vergunningen; plannen en verkoop samen 147
berichten, 129 kB, met een venster van 180 dagen).

| Week | Dagen | Berichten | kB | Meeste berichten |
|---|---|---:|---:|---|
| 42 | 14 – 18 okt (deels) | 185 | 176 | Breda 49, Bergen op Zoom 25, Oosterhout 20 |
| 43 | 19 – 25 okt | 235 | 220 | Breda 61, Oosterhout 21, Bergen op Zoom 20 |
| 44 | 26 okt – 1 nov | 201 | 189 | Breda 60, Bergen op Zoom 18, Halderberge 17 |
| 45 | 2 – 8 nov | 219 | 204 | Breda 76, Roosendaal 19, Drimmelen 17 |
| 46 | 9 – 15 nov | 217 | 206 | Breda 61, Moerdijk 27, Roosendaal 25 |
| 47 | 16 – 22 nov | 231 | 219 | Breda 78, Bergen op Zoom 24, Drimmelen 21 |
| 48 | 23 – 25 nov (deels) | 115 | 111 | Breda 45, Bergen op Zoom 27, Halderberge 16 |

Er komt per week 200 tot 235 berichten bij (190 – 220 kB), en er valt evenveel af. Een stijgende
lijn is er in deze zes weken niet. Gemiddeld 939 bytes per bericht.

| Gemeente (hele bestand, 25-11) | Berichten | kB |
|---|---:|---:|
| Breda | 447 | 412 |
| Bergen op Zoom | 153 | 167 |
| Roosendaal | 136 | 131 |
| Halderberge | 125 | 110 |
| Etten-Leur | 110 | 100 |
| Moerdijk | 103 | 101 |
| Overige zeven | 476 | 434 |

Welke berichten uit de extra rubrieken ("andere beschikking", "andere vergunning") komen, staat niet
in het bestand: een bericht houdt zijn rubriek niet bij. Volgens de meting van 19-11 gaat het om
ongeveer 66 berichten, waarvan 61 van Roosendaal.

### Wat de schatting van 19-11 miste

| | Schatting 19-11 | Gemeten |
|---|---:|---:|
| Gewone dag na het samenvoegen | 1.423 kB (94%) | 1.364 – 1.385 kB (90 – 92%) |
| Woensdagmiddag | niet geschat | 1.456 kB (97%) |

De schatting voor een gewone dag was 40 – 60 kB te hoog. De piek op woensdag zat er niet in: de meting
van 19-11 is op een donderdag gedaan, en de jaartelling werkt met vensters van hele weken.

## 2. De grens van 1.500 kB is een eigen keuze

| Waar | Regel | Wat |
|---|---|---|
| `tests/test_ververst.py` | regel 101 | Geen bestand in git groter dan 1.500.000 bytes. Ingevoerd op 16-11-2026, zie "Waarom 1,5 MB" hieronder |
| `tests/test_regio.py` | regel 931 | Elk databestand in de momentopname `site/data/` kleiner dan 1.500.000 bytes |
| `signalen/cache.py` | regel 37 | `REPO_BYTES = 1_500_000`, de maat voor de percentages in het log; `tests/test_cache.py` regel 294 houdt hem gelijk aan de test |
| `signalen/update.py` | regel 319 en 322 – 337 | `BESTAND_WAARSCHUW_BYTES = 1_350_000`: de waarschuwing vanaf 90% |

GitHub weigert pas bestanden boven 100 MB en waarschuwt vanaf 50 MB. Dat heb ik niet nagelezen in deze
sessie; het staat in de documentatie van GitHub zoals ik die ken.

### Waarom 1,5 MB (16-11-2026)

| | |
|---|---|
| Aanleiding | Op 16-11 om 20:51 uur was de film (5.167.073 bytes) met een stilstaand beeld in git gezet en gepusht, zonder dat de grootte was genoemd. Wim wees erop dat zo'n bestand in een openbare repo voorgoed in de geschiedenis blijft; de commit is herschreven |
| Maatregel | Commit `1b3b453` (16-11, 21:05 uur): `.gitignore` slaat films over, en een test faalt bij een film in git of een bestand boven 1,5 MB. Doel: herhaling voorkomen (`tilburg-signalen_verslag_video_16-11-2026.md`, "Film uit de repository") |
| Waarom juist 1,5 MB | **Nergens vastgelegd.** Het verslag en de commit noemen het getal zonder onderbouwing. Wat wel vaststaat: het grootste bestand in die commit was de stem van de film (`tools/video/geluid/stem.mp3`, 1.048.692 bytes, bewust gehouden), daarna `berichten.json` (992.806 bytes). 1,5 MB ligt daar net boven en ver onder de film. Dat het getal zo gekozen is, is mijn afleiding, geen vastgelegd feit |
| Waar het niet voor bedoeld was | De regiobestanden bestonden nog niet (17-11). De grens is een bewaker tegen grote bestanden in de geschiedenis van git, geen maat voor wat de site of de telefoon aankan. Hij is daarna overgenomen als maat voor de databestanden (17-11, `tests/test_regio.py`) en de cache (18-11, `signalen/cache.py`) |

De grens geldt alleen voor wat in git staat. De verversing schrijft `regio-west-brabant.json`,
publiceert het en zet het niet terug in de repo (alleen de cache gaat terug). Boven 1.500 kB gebeurt er
bij de verversing en op de site dus niets; alleen de momentopname in de repo kan dan niet meer met een
vers bestand worden vernieuwd.

## 3. Wanneer boven de grens

| Situatie | Schatting |
|---|---|
| Bij het tempo van nu (oktober – november) | Niet. Gewone dagen 1,36 – 1,39 MB, woensdagmiddag tot ongeveer 1,47 MB bij een woensdag van 95 berichten |
| Als het venster 3 tot 4 procent drukker wordt (40 berichten meer in zes weken) | Op woensdagmiddag boven 1,5 MB |
| Drukke maanden volgens de jaartelling (februari – april, juni – juli; tot 20% meer vergunningen dan nu) | Gewone dagen 1,55 – 1,6 MB, woensdagmiddag 1,65 – 1,7 MB |
| Eerste keer | Waarschijnlijk vanaf februari 2027, eerst alleen op woensdag. Rond de jaarwisseling niet (rustig) |

De drukte wisselt ook per jaar: hetzelfde venster in november 2025 telde 16% meer vergunningen dan nu
(dekkingsverslag). Reken met een marge van minstens 5%.

## 4. Opties

| | Wat | Cache | Site en telefoon | Tests | Oordeel |
|---|---|---|---|---|---|
| a | **West-Brabant in twee bestanden**, bv. Breda met buren en de rest; in de app één knop | Geen verschil: de cache is één bestand per alles, niet per regio | Bij West-Brabant twee downloads, samen even groot. `site/app.js` (laden van de regio), `site/logic.js` (overzicht), `site/adres-app.js` (zoeken in regio's) | `tests/test_regio.py`, `tests/js/regio_smoke.js`, `tests/js/regio_ongelezen.json`, nieuwe momentopname | Lost het per bestand op, met de meeste wijzigingen. Raakt `signalen/update.py` |
| b | **Roosendaal uitzetten** | Ongeveer 3 teksten minder, verwaarloosbaar | Ongeveer 64 kB minder (4%), minder dan één woensdag. Roosendaal verliest dan de meeste vergunningen: het publiceert ze onder "andere beschikking" | Alleen `config.json` | **Kan niet zoals bedoeld:** `andere_rubrieken` in `config.json` werkt per regio, niet per gemeente. Uit voor West-Brabant betekent uit voor alle dertien gemeenten. Lost het niet op |
| c | **De grens verhogen**, bv. naar 2.000 kB | Geen. `REPO_BYTES` verandert mee, de percentages in het log dalen; het vangnet van 1,4 MB voor de cache blijft | Geen | `tests/test_ververst.py`, `tests/test_regio.py`, `tests/test_cache.py`, `signalen/cache.py`, `signalen/update.py` | Mag, het is een eigen keuze. Maar het bestand en de download op de telefoon worden er niet kleiner van; eerder ontraden (voorstel E van 18-11) |
| d | **Afleidbare velden niet meer opschrijven** in de regiobestanden: `url` en `urlTekst` zijn bij alle 1.550 berichten uit het `id` af te leiden (samen 298 kB, 20%). De app maakt ze weer uit het `id`; een afwijkende `urlTekst` blijft staan | Geen | Bestand 20% kleiner: nu 1,16 MB op woensdag, in drukke maanden 1,3 – 1,35 MB. Gecomprimeerd weinig verschil (nu 125 kB) | `tests/test_regio.py`, een test voor het afleiden in `site/logic.js`, nieuwe momentopname | Lost het voor alle regio's op, met weinig code. Raakt `signalen/update.py` en `site/logic.js` |

Kleinere besparingen bij d, als het nodig is: `regio` (36 kB) en `bron` (51 kB) zijn in een regiobestand
voor elk bericht gelijk.

**Advies: d.** Het is de kleinste wijziging die het bestand blijvend kleiner maakt, ook voor de kern en
Zeeland, en geeft ruim 20% ruimte voor de drukke maanden. a pas als er een regio of rubriek bijkomt.
b werkt niet per gemeente en levert te weinig op. c alleen als je de waarschuwing wilt stillen zonder
iets aan het bestand te doen. Er is geen haast: boven 1,5 MB strandt geen run en blijft de site werken.

## Open punt: optie d, gepland voor januari 2027

Niet gebouwd. Voorwaarden van Wim (26-11-2026):

| Voorwaarde | Uitwerking |
|---|---|
| Een test vergelijkt voor **alle bestaande berichten** de afgeleide `url` en `urlTekst` met de echte | Over elk bericht in de momentopname (`site/data/berichten.json` en de drie regiobestanden), niet over een steekproef. Dat kan alleen zolang de momentopname de echte velden nog bevat: de test moet er dus zijn vóórdat de velden uit de bestanden gaan |
| Waar afleiden niet lukt, blijft de echte url staan | Per bericht en per veld: het veld vervalt alleen als de afgeleide waarde gelijk is aan de echte. Anders wordt het gewoon opgeschreven en gebruikt de app wat er staat |

Nog uit te zoeken bij het bouwen:

| Punt | Toelichting |
|---|---|
| De kern en Zeeland | Afleiden is alleen voor West-Brabant gecontroleerd (1.550 van 1.550). In de kern staan ook faillissementen en de Vlaamse bron, met andere adressen; daar blijft de echte url waarschijnlijk staan |
| Een tweede versie van een publicatie | `urlTekst` bevat een versienummer (`/1/`); bij een rectificatie kan dat anders zijn |
| Volgorde | Eerst de app zo maken dat hij een ontbrekend veld afleidt en een aanwezig veld gebruikt, en dat live hebben; pas daarna de velden weglaten. Anders toont een telefoon met de oude app berichten zonder link |
| Momentopname | Daarna vernieuwen, zodat tests en browsertests de nieuwe vorm gebruiken |
| Raakt | `signalen/update.py`, `site/logic.js`, tests. Geen workflow |

Tot januari: de waarschuwing vanaf 90 procent blijft in het log van elke run staan, op woensdag tot
ongeveer 97 procent. Dat is geen reden om in te grijpen; boven 1,5 MB strandt geen run.

## Wat ik niet heb kunnen controleren

| Punt | Toelichting |
|---|---|
| Runs van 19-11 en 20-11 | Niet bekeken; de reeks begint bij run 69 (21-11) |
| Andere woensdagen | Alleen de woensdag van 25-11 is in de logs gezien; dat de piek elke woensdag komt, volgt uit de data en de code, niet uit logs van eerdere woensdagen |
| Rubriek per bericht | Staat niet in het bestand; het aandeel van de extra rubrieken komt uit de meting van 19-11 |
| De schatting voor 2027 | Gebaseerd op de jaartelling van 17-11 (één jaar, per groep geteld); geen meting |
| Grens van GitHub | Niet nagelezen in deze sessie |
| Waarom juist 1,5 MB | Niet vastgelegd in het verslag of de commit van 16-11; de sessie van toen kan ik niet inzien |
| Dat `urlTekst` altijd uit het `id` af te leiden is | Gecontroleerd voor West-Brabant (1.550 van 1.550); niet voor de kern en Zeeland, en niet voor publicaties met een tweede versie |
| Gedrag op een iPhone bij 1,5 MB of meer | Niet gemeten |
