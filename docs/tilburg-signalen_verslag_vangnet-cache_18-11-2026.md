# Tilburg Signalen: verslag vangnet voor de cache

| | |
|---|---|
| Datum | 18-11-2026, 10:44 – 10:55 uur; aangevuld 11:03 – 11:12 uur (PR 18 samengevoegd, run 27, vaste testsituatie in PR 19) |
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
| 18-11-2026, 11:12 uur | **PR 18 is samengevoegd op verzoek van Wim (11:03 uur, merge-commit `32cd758`); "open blijft en niet is samengevoegd" onder "Stand" en "Buiten dit verslag" is daarmee achterhaald.** Wim gaf ook akkoord op de volgorde bij het weglaten (eerst wat het eerst uit het venster valt). |
| 18-11-2026, 11:12 uur | **Run 27, de run na het samenvoegen, is groen, ook de controle van de live site; "Run 26 is rood en de volgende runs worden het ook" onder "Niet getest of nog open" is daarmee afgehandeld.** De live site had op dat moment 429 wachtende regioberichten, dus de herstelde test is tegen de echte situatie gedraaid. Zie "Run 27 op GitHub". |
| 18-11-2026, 11:12 uur | **Het vangnet heeft nu op GitHub gedraaid, voor het deel dat altijd draait:** het log van run 27 meldt "cache: 630 kB bewaard, 42 procent". Weggelaten is er niets; daar is de cache te klein voor. |
| 18-11-2026, 11:12 uur | **De stap "Berichten ophalen" duurde in run 27 langer dan in run 26, met minder verzoeken:** 5 minuten en 35 seconden voor 449 verzoeken, tegen 3 minuten en 54 seconden voor 568. De hele run duurde 8 minuten en 17 seconden: onder de tien minuten, maar dichterbij dan run 23 en 26. Zie "Run 27 op GitHub". |
| 18-11-2026, 11:12 uur | **Er is een vaste testsituatie met ongelezen regioberichten bijgekomen, in PR 19 (open, niet samengevoegd). Het aantal tests is daarmee 385 (was 377).** Zie "Vaste testsituatie met ongelezen regioberichten". |
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

## Run 27 op GitHub, na het samenvoegen van PR 18 (18-11-2026, 11:03 – 11:11 uur)

Gestart door het samenvoegen, vanaf `main`, met het vangnet en de herstelde test.

| Stap | Duur | Verzoeken | Weigeringen (HTTP 429) | Uitkomst |
|---|---:|---:|---:|---|
| Tests | 14 s | geen | | Geslaagd |
| Browser klaarzetten en browsertests | 22 s en 36 s | geen naar de bronnen | | Geslaagd |
| Gebied bijwerken | 19 s | 29 | 0 | Geslaagd |
| **Berichten ophalen** | **5 min 35 s** | **449** | **58** | Geslaagd, zonder waarschuwing: 26 teksten mislukten in de eerste ronde en lukten alle bij herhaling |
| Cache bewaren | 1 s | | | Cache teruggezet in `main` (commit `dc87079`) |
| Publiceren | 11 s | | | Geslaagd |
| **Controle van de live site** | 22 s | | | **Geslaagd, alle 42 tests** |
| **Hele run** | **8 min 17 s** | **478** | **58** | **Groen** |

| Wat | Waarde |
|---|---|
| Berichten | 3.888, waarvan 1.140 in de kern (gelijk aan run 26: er zijn geen nieuwe publicaties bijgekomen) |
| Melding voor het ochtendscherm | Op nul; geen onvolledige dagen; de drie bronnen in orde |
| Regioteksten gelezen | 300; nog 429 wachten: West-Brabant 253, Zeeland 145, Midden-Brabant 31 |
| Vulling | Nog twee runs (300 en 129), als er geen nieuwe bijkomen |
| Locaties in de regio's | Midden-Brabant 14 (was 9), West-Brabant 75 (was 56), Zeeland 80 (was 65): gelezen teksten maken van "Onzeker" een ontwikkellocatie of filteren het bericht weg |
| Cache op `main` | 630 kB (was 482 kB): 148 kB erbij. Het log meldt het zelf: "cache: 630 kB bewaard, 42 procent van de 1.500 kB die een bestand in de repository mag zijn" |
| De controle van de live site | Draaide tegen de live gegevens van 11:04 uur, met ongelezen berichten in alle drie de regio's. De test die run 26 afkeurde, slaagt nu daar |

**Over de duur (feit en vermoeden).** Feit: de stap deed minder verzoeken dan in run 26 en duurde ruim
anderhalve minuut langer. In de eerste ronde mislukten 26 teksten: 11 door een weigering, 8 door de
tijdslimiet en 7 doordat het netwerk van de runner even onbereikbaar was; in run 26 waren dat er 5.
Vermoeden: de bron of het netwerk van de runner was trager, en het wachten en herhalen kostte de tijd.
Het vangnet is het niet: het bewaren van de cache kost milliseconden. De stopregel van tien minuten is
niet geraakt, maar een vulrun met 300 teksten kan er dus dichtbij komen.

## Vaste testsituatie met ongelezen regioberichten (PR 19, open)

**Opdracht van Wim:** een vaste testsituatie met een regio die ongelezen berichten heeft, zodat de
browsertests vóór het publiceren dit pad raken en niet alleen de controle achteraf. In een aparte pull
request die open blijft.

| Onderdeel | Wat het is |
|---|---|
| Het bestand | `tests/js/regio_ongelezen.json` (25 kB): drie kleine regiobestanden en het overzicht dat erbij hoort. Een vaste keuze van 21 berichten uit de uitkomst van run 23, ongewijzigd overgenomen |
| De situatie | Midden-Brabant: 6 berichten, 2 locaties, geen wachtende. West-Brabant: 9 berichten, 1 locatie, 4 wachtende (2 vergunningen, 1 plan, 1 verkoop). Zeeland: 6 berichten, 3 locaties, 1 wachtende |
| Hoe het draait | De browser krijgt de kern van de site zelf; alleen het overzicht van de regio's en de regiobestanden komen uit het vaste bestand |
| De wandeling, twee keer | Alle controles van de regiokeuze draaien met de regio's zoals de site ze levert én in de vaste situatie: beginstand, 320 pixels, één regio erbij, een gemeente aantikken, terug naar de kern, alle regio's tegelijk, opnieuw openen |
| Uitgeschreven controles | De regel op elke knop ("2 locaties", "1 locatie · 4 ongelezen", "3 locaties · 1 ongelezen"); de wachtende berichten onder Onzeker met "Tekst nog niet gelezen", bij één en bij alle regio's; de melding per gekozen regio in enkelvoud en meervoud; een aangetikte gemeente toont haar locatie |
| Controles van het bestand zelf | Zonder browser: het overzicht is wat een run voor deze bestanden schrijft, een wachtend bericht ziet eruit zoals de run het maakt, en elk bericht ligt in een gemeente van zijn regio |

**Waarom uitgeschreven.** De test die in run 26 faalde, rekende zijn verwachting uit op dezelfde manier
als de app. Zo'n test volgt de app in elke vergissing. De regel op de knop staat daarom nu ook
letterlijk in een test.

**Bewijs dat het pad nu vóór het publiceren geraakt wordt.** Met de oude verwachting, die van vóór het
herstel, faalt de test nu lokaal, in de vaste situatie: "'1 locatie · 4 ongelezen' != '1 locatie'".
Daarna is de herstelde verwachting teruggezet.

385 tests geslaagd in de container (was 377; 10 overgeslagen). Er zijn er 8 bij: 4 in de browser en 4
voor het bestand. Zes bestaande browsertests draaien nu in beide situaties. Alleen tests zijn
gewijzigd; de app en de workflow niet.

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| **Run 26 is rood en de volgende runs worden het ook** | Tot PR 18 is samengevoegd, of tot alle regioteksten gelezen zijn. Zie "De rode controle van de live site". Het herstel is niet tegen de live site zelf gedraaid; dat doet de eerste run na het samenvoegen |
| PR 19 heeft op GitHub nog niet gedraaid | Een pull request start hier geen run. De eerste run na het samenvoegen draait de vaste situatie in de browsertests vóór het publiceren en in de controle van de live site |
| De vaste situatie dekt alleen ongelezen regioberichten | Andere verschillen tussen de momentopname in de repo en de live site zijn er niet mee afgedekt, bijvoorbeeld een regio met mislukte teksten. De meldingen daarvoor hebben wel een eigen test |
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
- **PR 19 is niet samengevoegd** en blijft open tot Wim het zegt.
- **De bronnen zijn voor dit onderdeel niet belast.**
- **Geen subsessie**, en niets met ElevenLabs.
