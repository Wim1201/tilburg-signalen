# Tilburg Signalen: verslag vangnet voor de cache

| | |
|---|---|
| Datum | 18-11-2026, 10:44 – 10:55 uur |
| Versie | versie 2 van de app met de regio's, branch `claude/optimistic-gauss-sb0xpy`, opnieuw gestart vanaf `main` op commit `80e974b` (na PR 17) |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | Geen nieuwe opvraging bij de bronnen. Voor de proef: de cache met alle regio's van 17-11-2026, 20:36 uur (922 kB) en de berichten van de run van 20:31 uur |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_dekking-en-regios_17-11-2026.md`, onderdeel "Groei van de cache en de regiobestanden", voorstel A |

## Stand

PR 17 is samengevoegd op verzoek van Wim (18-11-2026, 10:44 uur, merge-commit `80e974b`). De run die
daarop volgde (run 26) heeft opgehaald en gepubliceerd; de regio's staan live. **De run
eindigde rood:** de controle van de live site keurde 1 van de 42 tests af. De site zelf is in orde; de
fout zit in een test van mij en is in PR 18 hersteld. Zie "De rode controle van de live site".

Onderdeel A is gebouwd en staat op de werkbranch, in een aparte pull request (PR 18) die **open
blijft en niet is samengevoegd**. De workflow en het schema zijn niet gewijzigd. B en C zijn niet
gebouwd, zoals besloten.

## Correcties en aanvullingen op eerdere verslagen

| Tijdstip | Wat |
|---|---|
| 18-11-2026, 10:55 uur | **Gevonden gebrek in PR 17, van mij: een test van de live-controle klopte niet met de app zodra een regio ongelezen berichten heeft. Run 26 eindigde daardoor rood.** De app toont op de regioknop terecht "9 locaties · 56 ongelezen"; de test verwachtte alleen "9 locaties". In de repo staat een momentopname zonder ongelezen berichten, dus daar slaagde de test, ook in run 23. Hersteld in PR 18 (alleen de test); niet samengevoegd. **Tot dat is samengevoegd eindigt elke run vanaf `main` rood zolang er regioberichten wachten**, naar verwachting de runs van 12:10 en 16:10 uur vandaag. De verversing en het publiceren gaan wel door: de controle komt daarna. |
| 18-11-2026, 10:55 uur | **"De browsertests op 320 pixels slagen" en "361 tests geslaagd" in het vorige verslag en in PR 17 waren waar voor de momentopname in de repo, niet voor de live gegevens.** De controle tegen de live site kon ik vóór het samenvoegen niet draaien; dat had ik als risico moeten noemen. |
| 18-11-2026, 10:55 uur | **Afwijking van het voorstel waarvoor akkoord is gegeven: niet "de oudste regioteksten" gaan eerst, maar de regioteksten die het eerst uit het venster vallen.** Een plan blijft 180 dagen in de lijst en een vergunning 42 dagen. "Oudste eerst" zou daardoor vooral plannen van mei en juni weglaten, die nog weken tot maanden blijven staan en dus bij elke run opnieuw opgehaald zouden worden. Zie "Gemaakte keuzes". Zeg het als je toch "oudste eerst" wilt; dat is één regel. |
| 18-11-2026, 10:55 uur | **PR 17 is samengevoegd; "open en niet samengevoegd" in het vorige verslag is daarmee achterhaald.** |
| 18-11-2026, 10:55 uur | **Het aantal tests is 377 (was 361).** Er zijn er 16 bij, alle voor het vangnet en de meldingen. |

## Opdracht

Akkoord van Wim op voorstel A: een run schrijft nooit een cache boven 1,4 MB en waarschuwt vanaf
1,2 MB. Als aparte pull request, te bouwen nadat PR 17 is samengevoegd. B (cache per regio) en C
(West-Brabant in twee bestanden) niet.

## Waarom

De workflow zet `cache/ophaalcache.json` na elke run terug in `main`. Een test keurt de repo af bij
een bestand boven 1.500.000 bytes, en die test is de eerste stap van elke run. Een te grote cache zou
dus elke volgende run laten stranden vóór het ophalen, tot iemand hem met de hand verkleint.

## Wat er is gebouwd

| Onderdeel | Wat het doet |
|---|---|
| Grens bij het bewaren (`signalen/cache.py`) | Is de cache groter dan 1.400.000 bytes, dan laat de run regioteksten weg tot hij past, niet meer dan nodig. Teksten van de kern, percelen, locaties en de andere soorten blijven altijd staan |
| Volgorde (`signalen/update.py`) | Eerst de regiotekst die het eerst uit zijn venster valt |
| Wat er met een weggelaten tekst gebeurt | Het bericht zelf staat in die run gewoon in de app, met zijn gelezen tekst. Alleen de cache onthoudt de tekst niet; de volgende run haalt hem opnieuw op, binnen de grens van 300 regioteksten per run |
| Melding in het log | Elke run: de grootte van de cache en het deel van 1,5 MB. Vanaf 1,2 MB een waarschuwing. Bij weglaten een waarschuwing met het aantal. Is de cache ook zonder regioteksten boven 1,4 MB, dan een aparte waarschuwing |
| README | Eén alinea over de grens |

De drie meldingen, zoals ze in het log komen:

```
  cache: 922 kB bewaard, 61 procent van de 1.500 kB die een bestand in de repository mag zijn
::warning::Cache is 1.200 kB, boven 1.200 kB. Boven 1.400 kB bewaart een run een deel van de regioteksten niet meer
::warning::Cache te groot: 37 regioteksten niet bewaard (wat het eerst uit het venster valt), zodat het bestand onder 1.400 kB blijft; de volgende run haalt ze opnieuw op
```

## Gemaakte keuzes

| Keuze | Waarom |
|---|---|
| Eerst wat het eerst uit het venster valt, niet het oudste bericht | Zie de correctie bovenaan. In de proef met een grens van 900 kB laat "oudste eerst" 12 teksten weg, alle van plannen van 22-05 tot en met 01-06-2026. De gekozen volgorde laat er 30 weg: 27 vergunningen van 6 en 7 oktober, die binnen twee dagen toch uit de lijst vallen, en 3 plannen van 22 mei. Het zijn er meer, maar ze hoeven maar een of twee runs herhaald te worden |
| De kern blijft altijd staan | De kern is het ochtendscherm; die mag nooit op een tekst wachten door ruimtegebrek |
| Alleen teksten weglaten | Teksten zijn 96 procent van de cache. Percelen en locaties zijn klein en kosten per stuk een opzoeking |
| De grenzen staan in de code, niet in `config.json` | Ze horen bij de regel van de repo (1,5 MB), niet bij het gebied. Een test bewaakt dat ze onder die regel blijven |
| Alleen een melding in het log | Zoals voorgesteld. Een waarschuwing staat in het overzicht van de run op GitHub; je krijgt er geen bericht van |

## Proef op de echte cache (container, 10:47 uur)

De cache van 17-11-2026 met alle regio's (922 kB, 1.478 teksten waarvan 486 van de kern), bewaard met
steeds een lagere grens. De echte grens van 1,4 MB raakt hij niet, dus de grens is voor de proef
verlaagd.

| Grens in de proef | Bewaard | Weggelaten | Waarvan | Kernteksten behouden | Andere soorten gelijk |
|---:|---:|---:|---|---:|---|
| 1.400 kB (de echte) | 917 kB | 0 | | 486 van 486 | ja |
| 900 kB | 900 kB | 30 | 27 vergunningen (6 en 7 oktober), 3 plannen | 486 van 486 | ja |
| 800 kB | 800 kB | 229 | 207 vergunningen (tot en met 16 oktober), 10 plannen, 12 verkopen | 486 van 486 | ja |
| 600 kB | 600 kB | 628 | 577 vergunningen (tot en met 5 november), 34 plannen, 17 verkopen | 486 van 486 | ja |
| 200 kB (onder de kern) | 294 kB | 992: alle regioteksten | | 486 van 486 | ja; de run meldt dat de kern alleen al te groot is |

Het bewaren kost 7 tot 12 milliseconden. Het verschil tussen 922 en 917 kB is de schrijfwijze van de
proef, niet het vangnet.

## Tests

377 tests geslaagd in de container (10 overgeslagen: 6 van de film, 4 die alleen op verzoek tegen de
echte bronnen draaien). De 16 nieuwe:

| Wat | Aantal |
|---|---:|
| De grens bij het bewaren: onder de grens niets weg, erboven precies genoeg, de eerstgenoemde eerst, de kern en de andere soorten nooit, een weggelaten tekst wordt opnieuw opgehaald, het bestand houdt één regel per tekst | 8 |
| De volgorde: alleen regioberichten, eerst wat het eerst uit het venster valt, een oud plan blijft langer dan een recente vergunning | 2 |
| De meldingen: gewone regel, waarschuwing vanaf 1,2 MB, waarschuwing bij weglaten, de kern alleen al te groot | 4 |
| De grenzen blijven onder de regel van de repo | 1 |
| De hele run met een echte cache in een tijdelijke map: blijft onder de grens en meldt het | 1 |

Drie bestaande tests zijn aangepast. Twee kregen een namaak-cache die een grootte teruggeeft, omdat
de run die afdrukt. De derde is de test van de regioknop; zie "De rode controle van de live site".

## Run 26 op GitHub, na het samenvoegen van PR 17 (18-11-2026, 10:44 – 10:51 uur)

Gestart door het samenvoegen, vanaf `main`. Deze run draaide **zonder** het vangnet: dat zit in PR 18.

| Stap | Duur | Verzoeken | Weigeringen (HTTP 429) | Uitkomst |
|---|---:|---:|---:|---|
| Tests | 14 s | geen | | Geslaagd |
| Browser klaarzetten en browsertests | 16 s en 39 s | geen naar de bronnen | | Geslaagd |
| Gebied bijwerken | 20 s | 29 | 0 | Geslaagd |
| **Berichten ophalen** | **3 min 54 s** | **568** | **56** | Geslaagd, zonder waarschuwing: 5 teksten mislukten in de eerste ronde en lukten alle bij herhaling |
| Cache bewaren | 2 s | | | Cache teruggezet in `main` (commit `318bfdb`) |
| Publiceren | 9 s | | | Geslaagd; live sinds 10:50 uur |
| **Controle van de live site** | 25 s | | | **Mislukt: 1 van de 42 tests** |
| **Hele run** | **6 min 44 s** | **597** | **56** | **Rood, door de controle van de live site. Opgehaald en gepubliceerd is er wel** |

| Wat | Waarde |
|---|---|
| Berichten | 3.888, waarvan 1.140 in de kern |
| Melding voor het ochtendscherm | Op nul: 0 teksten, 0 percelen, 0 rechtbankpublicaties niet opgehaald; geen onvolledige dagen; de drie bronnen in orde |
| Regioteksten gelezen | 300 (de grens); nog 729 wachten: West-Brabant 422, Zeeland 251, Midden-Brabant 56 |
| Vulling | Nog drie runs van deze omvang (300, 300 en 129), als er geen nieuwe bijkomen |
| Cache op `main` | 482 kB (was 296 kB): 186 kB erbij voor 300 teksten, 79 percelen en 130 locaties. Geschat was ongeveer 180 kB per run |
| Regiobestanden op de live site | Midden-Brabant 175 kB, West-Brabant 1.357 kB (90 procent van 1,5 MB), Zeeland 1.028 kB |
| Compressie | **Gemeten:** GitHub Pages levert West-Brabant gecomprimeerd af als 123 kB. "Aangenomen, niet gemeten" in het vorige verslag is daarmee afgehandeld |

De gegevens op de live site zijn om 10:51 uur opgehaald en nagelezen: bijgewerkt om 10:46 uur, de
drie regio's staan in het overzicht met dezelfde aantallen als in het log.

### De rode controle van de live site

| | |
|---|---|
| Wat faalde | De test `test_region_choice_is_offered_but_nothing_is_chosen_at_the_start`: "'9 locaties · 56 ongelezen' != '9 locaties'" |
| Oorzaak (feit) | De app zet op de regioknop het aantal ongelezen berichten erbij, zoals bedoeld. De test rekende alleen het aantal locaties uit. In de momentopname in de repo heeft geen regio ongelezen berichten; op de live site sinds 10:50 uur wel |
| Is de site stuk? | Nee. De 41 andere tests van de controle slaagden, en de knop toont wat hij moet tonen |
| Waarom niet eerder gezien | De controle tegen de live site draait alleen vanaf `main`. Run 23 vanaf de werkbranch testte de momentopname |
| Herstel | De test verwacht nu ook het aantal ongelezen berichten als het overzicht dat meldt. Alleen `tests/test_site.py`; de app is niet gewijzigd |
| Nagelopen | De vijf gegevensbestanden van de live site zijn in een kopie van de site gezet en de 42 tests van de controle zijn daartegen gedraaid: met het herstel slagen alle 42, zonder het herstel faalt dezelfde test met dezelfde melding. Dat is dezelfde code en dezelfde gegevens als de live site, maar niet de live site zelf |
| Tot het herstel in `main` staat | Elke run vanaf `main` eindigt rood zolang er regioberichten wachten: naar verwachting 12:10 uur (dan wachten er nog ongeveer 429) en 16:10 uur (ongeveer 129). De run van morgen 06:45 uur leest de laatste en zou vanzelf groen zijn. GitHub stuurt bij een rode run een bericht |

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| **Run 26 is rood en de volgende runs worden het ook** | Tot PR 18 is samengevoegd, of tot alle regioteksten gelezen zijn. Zie "De rode controle van de live site". Het herstel is niet tegen de live site zelf gedraaid; dat doet de eerste run na het samenvoegen |
| Het vangnet heeft op GitHub nog niet gedraaid | De eerste run na het samenvoegen van deze pull request laat de regel met de grootte in het log zien. Het weglaten zelf komt pas in beeld als de cache boven 1,4 MB komt; volgens de meting is dat bij het verloop van het afgelopen jaar niet het geval (hoogstens rond 1,2 MB) |
| De waarschuwing kan zich in het voorjaar melden | De schatting voor de tweede helft van april is 1,20 MB, precies de drempel. Een waarschuwing betekent dan: nog 200 kB ruimte |
| Herhaald ophalen zolang de cache te groot blijft | Wat weggelaten is, haalt elke run opnieuw op tot het uit het venster valt of er ruimte komt. Dat zijn extra verzoeken aan de bron, hoogstens 300 per run. Niet gemeten, omdat het zich niet voordoet |
| Meer dan 300 weggelaten teksten | Dan passen ze niet in één run en staan de overige een run lang onder Onzeker met "Tekst nog niet gelezen". Getest is dat een weggelaten tekst opnieuw wordt opgehaald; deze samenloop met de grens van 300 is niet apart getest |
| De kern alleen boven 1,5 MB | Dan helpt het vangnet niet en strandt de volgende run alsnog; de run waarschuwt vanaf 1,4 MB. De kern is nu 0,28 MB |
| De regiobestanden | Vallen buiten het vangnet: geen run strandt erop. West-Brabant blijft dicht bij 1,5 MB (voorstel C, niet gebouwd) |
| De meting van de repo over een week | Ingepland voor 25-11-2026, 10:00 uur |

## Buiten dit verslag

- **PR 17 is samengevoegd op verzoek van Wim** ("Voeg #17 samen"). **PR 18 is niet samengevoegd** en blijft
  open tot Wim het zegt. Daarin zitten het vangnet en het herstel van de test.
- **De workflow en het schema zijn niet gewijzigd**; `.github/` is in deze pull request onaangeroerd.
- **`cache/ophaalcache.json` is niet gecommit** en niets is geforceerd. De werkbranch is na het
  samenvoegen van PR 17 opnieuw gestart vanaf `main`; dat was vooruitspoelen, geen herschrijving.
- **B en C zijn niet gebouwd.** De opmerking achter de cron-regel van zondag is blijven staan.
- **De bronnen zijn voor dit onderdeel niet belast.**
- **Geen subsessie**, en niets met ElevenLabs.
