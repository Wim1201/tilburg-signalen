# Tilburg Signalen: verslag dekkingsoverzicht en regio-uitbreiding

| | |
|---|---|
| Datum | 17-11-2026, 20:22 – 20:53 uur; aangevuld 17-11-2026, 21:18 – 21:35 uur (voorstel andere rubrieken) en 18-11-2026, 08:15 – 08:37 uur (run 22 op GitHub) en 08:49 – 09:05 uur (grens, telling per regio, wekelijkse beurt) en 09:20 – 09:29 uur (run 23 op GitHub) en 09:31 – 09:48 uur (toelichting in de workflow, groei van de bestanden, pull request) |
| Versie | versie 2 van de app met het tabblad Adres, branch `claude/optimistic-gauss-sb0xpy`, gestart vanaf `main` op commit `edf4150` (na PR #16) |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | officielebekendmakingen.nl (zoekdienst SRU), opgevraagd 17-11-2026 tussen 20:25 en 20:37 uur; gemeente-indeling van het CBS, "Gebieden in Nederland 2026" (tabel 86247NED) |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_tabblad-adres_17-11-2026.md` |

## Stand

Deel 1 (onderzoek) is gedaan: alle 42 gemeenten leveren berichten. Geen enkele gemeente is
onbruikbaar; één is beperkt bruikbaar (Roosendaal).

Deel 2 (uitbreiding) is gebouwd en staat op de werkbranch. Het is **niet samengevoegd met `main`
en staat niet live**; er is geen pull request. De kern is bericht voor bericht gelijk gebleven.
`cache/ophaalcache.json` en het schema van de workflow zijn niet gewijzigd.

De stopregel is niet geraakt: een gewone run doet 35 verzoeken in 43 seconden (was 31 in 31
seconden), zonder één weigering. **Die meting is gedaan vanuit deze container, niet op GitHub.**
Wat de eerste run na samenvoegen en de wekelijkse volledige run op GitHub doen, is geschat en niet
gemeten; zie "Open punten".

## Correcties en aanvullingen op eerdere verslagen

| Tijdstip | Wat |
|---|---|
| 18-11-2026, 09:48 uur | **Er is nu een pull request: PR 17, open en niet samengevoegd; "er is geen pull request" onder "Stand" en "Buiten dit verslag" is daarmee achterhaald.** Hij blijft open tot Wim zegt dat hij samengevoegd mag worden. |
| 18-11-2026, 09:48 uur | **De toelichting in de workflow is aangepast (commit `2d21868`); "dat bestand heb ik niet aangeraakt" hieronder en "`.github/` is onaangeroerd" onder "Buiten dit verslag" gelden niet meer.** Gewijzigd zijn twee teksten: de omschrijving bij het vinkje "volledig" en het commentaar boven de stap "Berichten ophalen". Het schema is niet gewijzigd: het blok met de twee cron-regels is teken voor teken gelijk aan `main`. **Eén toelichting zegt nog "cache negeren": het commentaar achter de cron-regel van zondag 04:30 uur.** Die staat op dezelfde regel als het schema en heb ik daarom laten staan. |
| 18-11-2026, 09:48 uur | **De groei van de cache en de regiobestanden is gemeten; de open punten "De cache wordt ruim drie keer zo groot" (met "Geen actie nodig") en "`regio-west-brabant.json` zit dicht bij de grens" zijn daarmee uitgewerkt.** De bestanden groeien niet door maar volgen de drukte in het venster. De cache blijft bij het verloop van het afgelopen jaar onder 1,5 MB (hoogstens rond 1,2 MB); West-Brabant komt er in het voorjaar en in juli tegenaan. Zie "Groei van de cache en de regiobestanden" met een voorstel dat niet gebouwd is. |
| 18-11-2026, 09:48 uur | **In de kopregel stond bij run 23 "09:30 – 09:29 uur"; de begintijd was fout.** Verbeterd naar 09:20 uur. Dat is een vermoeden en geen genoteerd tijdstip: run 23 eindigde om 09:19 uur en het deel was om 09:29 uur klaar. |
| 18-11-2026, 09:29 uur | **De grens is op GitHub gemeten; "Op GitHub nog niet gemeten" onder "Open punten bij dit onderdeel" is daarmee afgehandeld voor een gewone run.** Run 23 (handmatig, vanaf de werkbranch) duurde 6 minuten en 9 seconden; de stap "Berichten ophalen" 4 minuten en 23 seconden, met 613 verzoeken en 89 weigeringen. De melding voor het ochtendscherm staat op nul en de kern is gelijk aan die van run 22, plus de 21 berichten van vandaag. Zie "Run 23 op GitHub". De wekelijkse volledige run is op GitHub nog niet gedraaid. |
| 18-11-2026, 09:05 uur | **De drie voorstellen uit "Run 22 op GitHub" zijn gebouwd; "Voorstel (niet doorgevoerd)" daar is achterhaald voor de punten 1, 2 en 4.** Grens van 300 nieuwe regioteksten per run, telling per regio en de wekelijkse volledige run in delen. Zie "Grens, telling per regio en wekelijkse beurt". Niet samengevoegd. |
| 18-11-2026, 09:05 uur | **De volledige verversing leest niet meer alles opnieuw.** `--volledig` leest de kern en de regio van de week opnieuw en de rest uit de cache. Wat eerdere verslagen over "cache negeren en alles opnieuw ophalen" zeggen, geldt alleen nog voor de nieuwe optie `--alles`, die de workflow niet gebruikt. **De toelichting in de workflow zelf zegt nog "cache negeren"; dat bestand heb ik niet aangeraakt.** |
| 18-11-2026, 09:05 uur | **De vier ontbrekende teksten uit run 22 zijn verklaard; "Ik vond er 31 terug" was dus geen telfout.** Bij vier berichten besliste de titel al over de uitkomst, waardoor niets in het bericht liet zien dat de tekst ontbrak. Zie "Waar de vier teksten bleven". |
| 18-11-2026, 09:05 uur | **Het aantal tests is 361 (was 336).** Er zijn er 25 bij: 24 voor de grens, de telling, de beurt en de meldingen, en 1 in de browser. |
| 18-11-2026, 08:37 uur | **Op GitHub is de eerste run met de regio's over de tien minuten gegaan, met 173 weigeringen; "De stopregel is niet geraakt" onder "Stand" geldt alleen voor de meting vanuit de container.** Run 22 (handmatig, vanaf de werkbranch, door Wim gestart) deed in de stap "Berichten ophalen" 1.404 verzoeken in 12 minuten en 49 seconden; 35 teksten kwamen niet binnen. De run eindigde zonder fout. Volgens de afspraak is er niet verder uitgebreid; zie "Run 22 op GitHub" met het voorstel. |
| 18-11-2026, 08:37 uur | **Mijn schatting voor die eerste run was te laag.** Ik schatte 1.300 verzoeken "rond de tien minuten" en ging uit van de 43 weigeringen van run 5. Het werden 1.404 verzoeken, bijna 13 minuten en 173 weigeringen. |
| 18-11-2026, 08:37 uur | **Gevonden gebrek in de uitbreiding: de melding bovenaan het ochtendscherm telt ook niet-gelezen teksten uit de regio's.** In run 22 zaten alle teruggevonden niet-gelezen teksten in de regio's en geen in de kern, maar de app zou na publiceren melden dat 35 bekendmakingen niet volledig gelezen konden worden. Niet hersteld; zie het voorstel. |
| 17-11-2026, 21:21 uur | **De handmatige run vanaf de werkbranch kon ik niet starten; "Graag je akkoord voordat ik die start" onder "Open punten" is daarmee achterhaald.** Wim gaf akkoord, maar de koppeling van deze sessie mag geen workflow starten (GitHub antwoordde met 403). Niet omzeild. Wim kan de run zelf starten; zie het voorstel hieronder, "Buiten dit voorstel". |
| 17-11-2026, 21:21 uur | **Het open punt over Roosendaal is uitgewerkt in een apart voorstel**, `tilburg-signalen_voorstel_andere-rubrieken_17-11-2026.md`. Daarin staat ook een correctie: van de vijf berichten van Vught ligt er één in de kern, en bij Dongen zit de afwijking in de titel en niet in de rubriek. |
| 17-11-2026, 21:21 uur | **De stap "Gebied bijwerken" meldt nu verzoeken, duur en weigeringen** (commit `d5ab774`), zodat het log van een run per stap de cijfers geeft. |
| 17-11-2026, 20:53 uur | **De app leest nu meer dan twee eigen bestanden.** Naast `data/berichten.json` en `data/gebied.json` zijn er drie regiobestanden. Die worden alleen gelezen als iemand een regio kiest of op het tabblad Adres een adres buiten de kern opzoekt. Het ochtendscherm leest ze niet; een test bewaakt dat. |
| 17-11-2026, 20:53 uur | **"`site/data/` is onaangeroerd" uit eerdere verslagen geldt voor dit werk niet.** `gebied.json` is opnieuw gemaakt (de kern daarin is gelijk; de gemeenten van de regio's zijn erbij gekomen), er zijn drie regiobestanden bij, en in `berichten.json` is één sleutel toegevoegd (`regios`). De berichten in `berichten.json` zelf zijn nog die van 16-11-2026, 15:37 uur: de tests van de video rekenen op die momentopname. |
| 17-11-2026, 20:53 uur | **Het tabblad Adres zoekt niet meer alleen in de berichten die de app al geladen had.** Voor een adres buiten de kern leest het ook het bestand van de regio van dat adres. Wat in het verslag van het tabblad Adres staat over "geen extra verzoek" geldt nog voor een adres dat geheel in de kern ligt. |
| 17-11-2026, 20:53 uur | **Het aantal tests is 336 (was 290).** Er zijn er 46 bij: 37 voor de gemeentelijst, het ophalen en het regiofilter, 8 in de browser en 1 die alleen op verzoek tegen de echte bronnen draait. |
| 17-11-2026, 20:53 uur | **Een run meldt nu hoe vaak de bron een verzoek weigerde (HTTP 429)**, ook als een herhaling daarna slaagde. Tot nu toe was dat alleen te zien voor verzoeken die in de eerste ronde definitief mislukten. |

## Opdracht

Deel 1, alleen onderzoek: per gemeente in Midden-Brabant, West-Brabant en Zeeland uitzetten wat
officielebekendmakingen.nl levert, met de gemeenten van de bestaande kern als vertrekpunt. Deel 2:
de uitbreiding bouwen met de bruikbare gemeenten: een gemeentelijst met regio in `config.json`,
een regiofilter op het tabblad Gebied, en het tabblad Adres dat ervan meeprofiteert. De kern en het
ochtendscherm blijven ongewijzigd. Vóór en na meten; stoppen bij een gewone run boven de tien
minuten of structurele weigeringen. De Vlaamse bron niet onderzoeken, het schema van de workflow
niet wijzigen, de cache niet vanaf een branch committen.

# Deel 1: dekkingsoverzicht

## De gemeentelijst en haar bron

De lijst komt van het **CBS, "Gebieden in Nederland 2026" (tabel 86247NED)**, opgevraagd via de open
dienst van het CBS op 17-11-2026. Die tabel deelt elke gemeente in bij een COROP-gebied en een
provincie.

| Regio in de app | Indeling van het CBS | Gemeenten |
|---|---|---|
| Midden-Brabant | COROP-gebied Midden-Noord-Brabant (CR34) | 11: Alphen-Chaam, Altena, Baarle-Nassau, Dongen, Gilze en Rijen, Goirle, Hilvarenbeek, Loon op Zand, Oisterwijk, Tilburg, Waalwijk |
| West-Brabant | COROP-gebied West-Noord-Brabant (CR33) | 13: Bergen op Zoom, Breda, Drimmelen, Etten-Leur, Geertruidenberg, Halderberge, Moerdijk, Oosterhout, Roosendaal, Rucphen, Steenbergen, Woensdrecht, Zundert |
| Zeeland | Provincie Zeeland (COROP-gebieden Overig Zeeland en Zeeuwsch-Vlaanderen) | 13: Borsele, Goes, Hulst, Kapelle, Middelburg, Noord-Beveland, Reimerswaal, Schouwen-Duiveland, Sluis, Terneuzen, Tholen, Veere, Vlissingen |
| Alleen kern | Liggen in een ander COROP-gebied | 5: Boxtel, Heusden, Vught (Noordoost-Noord-Brabant), Oirschot, Reusel-De Mierden (Zuidoost-Noord-Brabant) |

Samen 42 Nederlandse gemeenten. De kern telt er 16 (plus het Belgische Ravels); 11 daarvan horen
ook bij Midden-Brabant of West-Brabant. Van Midden-Brabant ligt alleen Altena helemaal buiten de
kern.

**Keuze:** "Midden-Brabant" en "West-Brabant" zijn geen vaste bestuurlijke eenheden. Ik heb de
COROP-indeling van het CBS genomen omdat die elke gemeente bij precies één gebied indeelt. De
samenwerkingsregio's (Hart van Brabant, Regio West-Brabant) wijken daar op een paar gemeenten van af:
Heusden hoort bij Hart van Brabant, maar bij het CBS niet bij Midden-Noord-Brabant.

## Werkwijze

| Wat | Hoe |
|---|---|
| Vergunningen | Eén zoekvraag voor de rubriek "omgevingsvergunning" van de 42 gemeenten, vanaf 06-10-2026 (42 dagen): 3.678 berichten |
| Plannen | Eén zoekvraag voor de rubriek "ruimtelijk plan of omgevingsdocument", vanaf 21-05-2026 (180 dagen): 249 berichten |
| Andere soorten | Per gemeente het totaal van alle publicaties in 42 dagen, en alle publicaties van de laatste 7 dagen met hun rubriek (1.134 berichten) |
| Ontwerp of vastgesteld | De bron kent daar geen eigen rubriek voor; het is afgeleid uit de titel, met dezelfde regels als de app |
| Belasting van de bron | 56 verzoeken, na elkaar, met een pauze ertussen; geen enkele fout of weigering |

De bron heeft één rubriek voor alles wat met plannen te maken heeft. "Ontwerpplannen",
"vastgestelde plannen" en "ruimtelijke plannen" uit de vraag zijn dus dezelfde rubriek, uitgesplitst
naar de stand die uit de titel blijkt.

## Per gemeente

"Met omschrijving" is het aantal vergunningen waarbij de bron een omschrijving meelevert; bij de
rest leest de app de tekst van de bekendmaking zelf (één verzoek per bericht). "Andere soorten" is
alles wat de gemeente in 42 dagen publiceerde buiten vergunningen en plannen. Inwonertal: CBS,
2026.

| Gemeente | Regio (CBS) | Kern | Vergunningen 42 d | Per 1.000 inw. | Met omschrijving | Plannen 180 d | Ontwerp of voornemen | Vastgesteld | Overig | Plannen met locatie | Andere soorten 42 d | Opmerking |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Boxtel | geen van de drie | ja | 126 | 3,67 | 2 | 8 | 2 | 4 | 2 | 3 | 36 |  |
| Heusden | geen van de drie | ja | 90 | 1,93 | 0 | 6 | 2 | 3 | 1 | 1 | 26 |  |
| Oirschot | geen van de drie | ja | 55 | 2,78 | 54 | 4 | 0 | 1 | 3 | 1 | 33 |  |
| Reusel-De Mierden | geen van de drie | ja | 28 | 2,04 | 28 | 2 | 0 | 2 | 0 | 2 | 26 | Weinig plannen |
| Vught | geen van de drie | ja | 105 | 3,16 | 0 | 7 | 1 | 2 | 4 | 5 | 95 | 5 berichten over een omgevingsvergunning onder een andere rubriek |
| Alphen-Chaam | Midden-Brabant | ja | 25 | 2,38 | 3 | 9 | 4 | 3 | 2 | 2 | 22 |  |
| Altena | Midden-Brabant |  | 107 | 1,82 | 101 | 3 | 0 | 0 | 3 | 0 | 55 |  |
| Baarle-Nassau | Midden-Brabant | ja | 24 | 3,31 | 0 | 3 | 1 | 2 | 0 | 2 | 21 |  |
| Dongen | Midden-Brabant | ja | 67 | 2,42 | 67 | 5 | 0 | 5 | 0 | 3 | 104 | 10 berichten over een omgevingsvergunning onder een andere rubriek |
| Gilze en Rijen | Midden-Brabant | ja | 50 | 1,76 | 1 | 6 | 0 | 4 | 2 | 3 | 38 |  |
| Goirle | Midden-Brabant | ja | 46 | 1,85 | 0 | 4 | 0 | 4 | 0 | 3 | 20 |  |
| Hilvarenbeek | Midden-Brabant | ja | 49 | 3,0 | 1 | 8 | 1 | 3 | 4 | 3 | 37 |  |
| Loon op Zand | Midden-Brabant | ja | 45 | 1,87 | 2 | 1 | 0 | 1 | 0 | 1 | 44 | Weinig plannen |
| Oisterwijk | Midden-Brabant | ja | 67 | 2,01 | 2 | 4 | 1 | 1 | 2 | 1 | 34 |  |
| Tilburg | Midden-Brabant | ja | 494 | 2,14 | 494 | 12 | 2 | 10 | 0 | 0 | 130 | Geen enkel plan met locatie |
| Waalwijk | Midden-Brabant | ja | 81 | 1,57 | 2 | 2 | 0 | 2 | 0 | 1 | 69 | Weinig plannen |
| Bergen op Zoom | West-Brabant |  | 117 | 1,66 | 117 | 5 | 0 | 3 | 2 | 1 | 76 |  |
| Breda | West-Brabant |  | 400 | 2,1 | 400 | 13 | 0 | 10 | 3 | 12 | 155 |  |
| Drimmelen | West-Brabant |  | 51 | 1,8 | 51 | 4 | 2 | 1 | 1 | 1 | 57 |  |
| Etten-Leur | West-Brabant |  | 61 | 1,32 | 58 | 10 | 5 | 5 | 0 | 0 | 99 | 8 berichten over een omgevingsvergunning onder een andere rubriek; Geen enkel plan met locatie |
| Geertruidenberg | West-Brabant |  | 38 | 1,73 | 38 | 2 | 0 | 0 | 2 | 1 | 26 | Weinig plannen |
| Halderberge | West-Brabant |  | 104 | 3,3 | 0 | 3 | 0 | 0 | 3 | 0 | 33 |  |
| Moerdijk | West-Brabant |  | 97 | 2,52 | 97 | 7 | 0 | 4 | 3 | 1 | 36 |  |
| Oosterhout | West-Brabant | ja | 94 | 1,6 | 1 | 3 | 0 | 2 | 1 | 2 | 60 |  |
| Roosendaal | West-Brabant |  | 44 | 0,56 | 44 | 34 | 21 | 0 | 13 | 7 | 149 | **Opvallend weinig vergunningen**: 58 aanvragen en termijnverlengingen staan onder de rubriek "andere beschikking" |
| Rucphen | West-Brabant |  | 58 | 2,42 | 1 | 7 | 1 | 5 | 1 | 5 | 8 |  |
| Steenbergen | West-Brabant |  | 42 | 1,71 | 0 | 5 | 0 | 1 | 4 | 1 | 27 |  |
| Woensdrecht | West-Brabant |  | 58 | 2,6 | 21 | 4 | 1 | 0 | 3 | 0 | 14 |  |
| Zundert | West-Brabant |  | 60 | 2,6 | 1 | 11 | 0 | 11 | 0 | 0 | 42 | Geen enkel plan met locatie |
| Borsele | Zeeland |  | 47 | 2,03 | 0 | 4 | 2 | 2 | 0 | 2 | 35 |  |
| Goes | Zeeland |  | 82 | 2,03 | 82 | 3 | 0 | 1 | 2 | 1 | 92 |  |
| Hulst | Zeeland |  | 64 | 2,34 | 63 | 2 | 0 | 0 | 2 | 0 | 60 | Weinig plannen |
| Kapelle | Zeeland |  | 27 | 2,05 | 27 | 2 | 2 | 0 | 0 | 0 | 28 | Weinig plannen |
| Middelburg | Zeeland |  | 83 | 1,65 | 0 | 1 | 0 | 0 | 1 | 0 | 25 | Weinig plannen |
| Noord-Beveland | Zeeland |  | 56 | 6,94 | 56 | 7 | 3 | 0 | 4 | 0 | 50 | 4 berichten over een omgevingsvergunning onder een andere rubriek; Geen enkel plan met locatie |
| Reimerswaal | Zeeland |  | 49 | 2,1 | 48 | 3 | 1 | 0 | 2 | 0 | 50 |  |
| Schouwen-Duiveland | Zeeland |  | 171 | 4,97 | 168 | 11 | 6 | 3 | 2 | 3 | 65 |  |
| Sluis | Zeeland |  | 71 | 3,06 | 0 | 4 | 0 | 2 | 2 | 2 | 125 |  |
| Terneuzen | Zeeland |  | 108 | 1,93 | 99 | 7 | 1 | 6 | 0 | 6 | 252 |  |
| Tholen | Zeeland |  | 82 | 3,03 | 82 | 6 | 3 | 3 | 0 | 3 | 48 |  |
| Veere | Zeeland |  | 106 | 4,81 | 106 | 1 | 1 | 0 | 0 | 0 | 44 | Weinig plannen |
| Vlissingen | Zeeland |  | 49 | 1,07 | 0 | 6 | 2 | 0 | 4 | 1 | 98 | Aan de lage kant; geen oorzaak gevonden |
| **Totaal (42 gemeenten)** | | | **3678** | 2,15 | 2317 | **249** | 65 | 106 | 78 | 80 | 2544 | |

Alle berichten komen uit het Gemeenteblad. **Elke vergunning heeft een locatie** (3.678 van 3.678).
Van de plannen heeft een derde een locatie (80 van 249); voor de rest zoekt de app een adres in de
titel of rekent hij met de gemeente als geheel.

Soort plan, alle 42 gemeenten samen: 180 over een omgevingsplan, 27 over een bestemmingsplan, 15
programma's, 9 omgevingsvisies en 18 overige. Stand: 91 vastgesteld, 36 ontwerp, 29 voornemen, 12
herstelbesluit, 6 voorbereidingsbesluit, 3 onherroepelijk en 72 zonder herkenbare stand.

### Andere soorten (laatste 7 dagen, 42 gemeenten samen)

| Rubriek | Aantal |
|---|---:|
| omgevingsvergunning | 694 |
| evenementenvergunning | 66 |
| andere beschikking | 59 |
| andere vergunning | 54 |
| omgevingsmelding | 47 |
| ander besluit van algemene strekking | 37 |
| verkeersbesluit of -mededeling | 29 |
| uitschrijving basisregistratie personen | 27 |
| overige overheidsinformatie | 26 |
| verordening | 23 |
| andere melding | 22 |
| beleidsregel, voorlichting | 12 en 12 |
| ruimtelijk plan of omgevingsdocument | 11 |
| exploitatievergunning, evenementmelding, mandaatbesluit, exploitatiemelding | 8, 4, 2 en 1 |

## Waar de bron niets of opvallend weinig levert

| Gemeente of soort | Waarneming | Vermoeden waarom |
|---|---|---|
| **Roosendaal, vergunningen** | 44 in 42 dagen, 0,56 per 1.000 inwoners; de middelste gemeente zit op 2,1 | **Vastgesteld, geen vermoeden:** Roosendaal zet aanvragen ("Ingediende aanvraag voor een Omgevingsvergunning") en termijnverlengingen onder de rubriek "andere beschikking". In 42 dagen 58 berichten. De app leest alleen de rubriek "omgevingsvergunning" en mist ze dus. Verleende en geweigerde vergunningen staan wel in de goede rubriek |
| Dongen, Etten-Leur, Vught, Noord-Beveland | 10, 8, 5 en 4 berichten over een omgevingsvergunning onder een andere rubriek | Zelfde oorzaak, in het klein. Bij Dongen en Vught (kern) gaat het deels om andere vergunningen die "omgevingsvergunning" in de titel hebben; bij Etten-Leur om ambtshalve intrekkingen; bij Noord-Beveland om ontwerpbesluiten ter inzage |
| Vlissingen, vergunningen | 49, 1,07 per 1.000 inwoners | Geen oorzaak gevonden. Aanvragen en verleende vergunningen staan beide in de goede rubriek; in de laatste 7 dagen staat er niets onder een andere rubriek |
| Plannen in Middelburg, Veere, Loon op Zand (1 elk), Hulst, Kapelle, Geertruidenberg, Waalwijk, Reusel-De Mierden (2 elk) | Weinig in 180 dagen | Vermoeden: er lopen daar weinig planprocedures. Dat de gemeente elders publiceert is niet gebleken; de berichten die er zijn, hebben de gewone vorm |
| Plannen zonder locatie | Tilburg 12 van 12, Zundert 11 van 11, Etten-Leur 10 van 10, Roosendaal 27 van 34, Noord-Beveland 7 van 7 | De gemeente vult bij de kennisgeving geen gebied in. De app valt terug op een adres uit de titel of op de gemeente als geheel, zoals nu al voor Tilburg |
| Omschrijving bij vergunningen | 19 gemeenten leveren er (vrijwel) geen, waaronder Middelburg, Sluis, Vlissingen, Borsele, Halderberge, Rucphen, Steenbergen en Zundert | Verschil in het systeem waarmee de gemeente publiceert. Gevolg: één extra verzoek per bericht, eenmalig; daarna uit de cache |

## Onbruikbare gemeenten

**Geen.** Elke gemeente levert vergunningen met een locatie en plannen in dezelfde vorm als de kern.

| Gemeente | Oordeel | Waarom |
|---|---|---|
| Roosendaal | Beperkt bruikbaar, wel opgenomen | Aanvragen ontbreken; besluiten en plannen komen wel binnen. De app zegt dit bij de gemeente op het tabblad Gebied |
| De overige 41 | Bruikbaar | |

Roosendaal weglaten zou ook de 80 berichten kosten die wel binnenkomen. Het gemis is te herstellen
door voor Roosendaal ook de rubriek "andere beschikking" te lezen, gefilterd op de titel; dat is
niet gebouwd, zie "Open punten".

# Deel 2: regio-uitbreiding

## Wat er is gebouwd

| Onderdeel | Wat |
|---|---|
| `config.json` | `gemeenten`: 42 gemeenten met per gemeente `regio` (kern, Midden-Brabant, West-Brabant of Zeeland), en `regios`. Niets bestaands is gewijzigd |
| Verversing | Haalt de gemeenten van de regio's in dezelfde zoekvragen mee op. Elk bericht krijgt `regio` |
| Uitvoer | `data/berichten.json` houdt alleen de kern, zoals nu. Elke regio krijgt een eigen bestand: `regio-midden-brabant.json`, `regio-west-brabant.json`, `regio-zeeland.json` |
| Tabblad Gebied | Drie knoppen onder de inleiding: Midden-Brabant, West-Brabant, Zeeland, elk met het aantal ontwikkellocaties. Kies er een en de gemeenten van die regio komen in de lijst |
| Tabblad Berichten | Alleen als er een regio is gekozen: één regel "Met West-Brabant erbij." met de knop "Alleen de kern". Ranglijst, Onzeker, weggefilterd en de filters tellen dan over kern plus regio |
| Tabblad Adres | Leest voor een adres buiten de kern het bestand van de regio van dat adres en zoekt daar ook in |
| Bij een nieuw bezoek | De app opent altijd met alleen de kern; de keuze wordt niet bewaard |

## Gemaakte keuzes

| Keuze | Waarom |
|---|---|
| **De kern blijft wat binnen 15 km ligt; de lijst in `config.json` verandert dat niet** | Zo is de kern aantoonbaar ongewijzigd. Gecontroleerd: 1.105 berichten vóór en na, dezelfde, met dezelfde inhoud en in dezelfde volgorde |
| De 16 gemeenten van de kern hebben het label `kern`; 11 daarvan hebben daarnaast `buiten_straal` | Anders zou de rest van een kerngemeente nergens bij horen. Van Oosterhout liggen 2 berichten binnen de 15 km en 96 erbuiten; die 96 staan nu onder West-Brabant. Boxtel, Heusden, Oirschot, Vught en Reusel-De Mierden horen bij geen van de drie regio's en houden bij de straal op, zoals nu |
| Een bericht hoort bij `kern` als het binnen de straal ligt, anders bij de regio van zijn gemeente | Eén regel voor elk bericht, ook voor een bericht van de provincie of het Rijk dat in Breda ligt |
| Ligt een bericht buiten de straal en is de gemeente onbekend, dan vervalt het, zonder die gemeente op te zoeken | De landelijke zoekvraag (Staatscourant) levert berichten uit heel Nederland. Voor elk daarvan de gemeente opzoeken zou per run honderden verzoeken kosten |
| **Per regio een eigen bestand, pas gelezen als het nodig is** | Met alles in één bestand werd `berichten.json` 3,5 MB (was 1,0 MB). De repo heeft een test die bestanden boven 1,5 MB weert, en het ochtendscherm zou bij elk openen ruim drie keer zoveel moeten laden. Nu blijft dat gelijk |
| De keuze voor een regio wordt niet bewaard | Zo gevraagd: de standaardweergave blijft de kern |
| "Nieuw sinds je vorige bezoek" blijft een zaak van de kern | Een regio zou anders bij de eerste keer kiezen honderden berichten als nieuw aanmerken. De ochtendzin en de tegel Nieuw veranderen dus niet door een regio |
| Het kaartje op het tabblad Gebied blijft de kern tonen | De ringen lopen tot 15 km; Middelburg ligt op 103 km |
| Het filter op afstand loopt mee | Met een regio erbij reikt de schuif tot het verste bericht (Midden-Brabant 32 km, Zeeland 123 km, West-Brabant 106 km, zie de regel over Bergen op Zoom onder "Open punten"); zonder regio blijft hij 15 km |
| Faillissementen en de Vlaamse bron blijven bij de kern | De opdracht gaat over gemeentelijke publicaties. Voor faillissementen zou het postcodegebied uitgebreid moeten worden, met per zaak een opzoeking in de BAG |
| Van een regiogemeente worden geen plaatsen (woonplaatsen) opgehaald | Dat zijn de grenzen van enkele honderden plaatsen, bij elke run. De rij op het tabblad Gebied zegt "Hele gemeente, buiten de straal" |
| De momentopname van `berichten.json` in de repo is niet vervangen | De tests van de video rekenen op de berichten van 16-11-2026. Alleen het overzicht van de regio's is eraan toegevoegd |

## Hoe een bericht zijn regio krijgt

| Bericht | Regio |
|---|---|
| Locatie binnen 15 km | kern (zoals altijd) |
| Locatie buiten 15 km, in een gemeente van een regio (Breda, Middelburg) | Die regio |
| Locatie buiten 15 km, in een kerngemeente met `buiten_straal` (Oosterhout, Waalwijk) | De regio uit `buiten_straal` |
| Locatie buiten 15 km, in een kerngemeente zonder `buiten_straal` (Vught) | Vervalt, zoals nu |
| Locatie buiten 15 km, gemeente onbekend of niet in de lijst | Vervalt, zoals nu |
| Geen locatie, gemeente van een regio | Die regio, met "geen exacte locatie" |
| Geen locatie, kerngemeente | kern, zoals nu |

## Wat de regio's toevoegen (run van 17-11-2026, 20:31 uur)

| Regio | Berichten | Ontwikkellocatie | Onzeker | Weggefilterd | Bestand | Gecomprimeerd |
|---|---:|---:|---:|---:|---:|---:|
| kern | 1.105 | 80 | 23 | 1.002 | 999.997 bytes | 99.153 |
| Midden-Brabant | 192 | 21 | 6 | 165 | 178.890 bytes | 17.835 |
| West-Brabant | 1.382 | 143 | 31 | 1.208 | 1.291.562 bytes | 111.211 |
| Zeeland | 1.089 | 118 | 9 | 962 | 1.020.486 bytes | 95.725 |
| Samen | 3.768 | 362 | 69 | 3.337 | | |

Midden-Brabant is klein omdat 10 van de 11 gemeenten al grotendeels in de kern liggen: het is
Altena (114 berichten) plus wat van Waalwijk, Baarle-Nassau, Alphen-Chaam, Dongen en Gilze en Rijen
buiten de 15 km valt.

# Meten

Gemeten vanuit deze container, met een telling van elk verzoek en elk antwoord, ook van pogingen die
werden herhaald. "Vóór" is de code van `main` (commit `edf4150`), "na" de werkbranch. Elke
volledige run begon zonder cache; de gewone run erna gebruikte de cache die de volledige run had
geschreven.

| | Vóór (kern) | Na (kern en drie regio's) |
|---|---:|---:|
| **Volledige run, verzoeken** | 841 | 2.047 |
| waarvan aan de bron (repository.overheid.nl) | 726 | 1.722 |
| waarvan aan PDOK (Kadaster, Locatieserver) | 114 | 324 |
| Volledige run, duur | 137 seconden | 295 seconden |
| Volledige run, weigeringen (HTTP 429) | 0 | 0 |
| **Gewone run, verzoeken** | 31 | 35 |
| waarvan aan de bron | 30 | 34 |
| Gewone run, duur | 31 seconden | 43 seconden |
| Gewone run, weigeringen (HTTP 429) | 0 | 0 |
| Berichten | 1.105 | 3.768 |
| Teksten die gelezen moesten worden | 486 | 1.478 |
| Percelen opgezocht | 40 | 194 |
| `data/berichten.json` | 983.084 bytes | 999.997 bytes |
| Regiobestanden samen | geen | 2.490.938 bytes |
| `cache/ophaalcache.json` | 280.181 bytes | 921.648 bytes |
| Stap "Gebied bijwerken", verzoeken | 3 | 29 |
| Stap "Gebied bijwerken", duur | 4 seconden | 17 seconden |
| `data/gebied.json` | 10.869 bytes | 19.081 bytes |

De tijdstippen: nulmeting volledig 20:28 – 20:30 uur en gewoon 20:31 uur; met regio's volledig
20:31 – 20:36 uur en gewoon 20:37 uur.

Een gewone run kost 4 verzoeken meer: de lijsten zijn langer en komen in meer bladen van 500. Op een dag met nieuwe publicaties komen daar de teksten van die dag bij. De
regio's leveren ongeveer 57 vergunningen per dag; voor ruim een derde daarvan moet de tekst gelezen
worden. Dat is naar schatting 20 tot 30 extra verzoeken, verdeeld over de runs van die dag.

**Wat dit niet zegt.** Vanuit deze container weigerde de bron niets. Op GitHub was dat eerder anders:
run 5 (16-11-2026, zonder cache) deed 1.056 verzoeken in ruim 8 minuten en kreeg 43 weigeringen, die
bij herhaling alle slaagden. Zie "Open punten".

# Getest

| Wat | Hoe | Uitkomst |
|---|---|---|
| De kern is ongewijzigd | De nulmeting met de code van `main` (20:30 uur) en de volledige run met de werkbranch (20:31 uur), 49 seconden na elkaar gestart; de berichten met regio kern vergeleken met de nulmeting | 1.105 om 1.105, dezelfde berichten, dezelfde inhoud, dezelfde volgorde |
| Gemeentelijst | 5 tests: elke gemeente één keer met een bestaand label; de kern is de kern van voorheen; de regio's zijn de indeling van het CBS; kerngemeenten buiten de drie regio's houden op bij de straal; de beperking van Roosendaal staat erbij | Geslaagd |
| `gebied.json` en `gebied.py` | 4 tests: elke gemeente uit de lijst staat erin met haar label; de kern ligt binnen de straal en de rest erbuiten; regio's worden toegevoegd zonder de kern opnieuw op te vragen; een gemeente die niet bestaat stopt de stap | Geslaagd |
| Regio van een bericht | 10 tests met nagemaakte berichten: binnen de straal, gemeente van een regio, rest van een kerngemeente, kerngemeente zonder regio, onbekende gemeente (zonder opzoeking), bericht van de provincie, zonder locatie, locatie uit de titel, en het gebied van vóór de regio's | Geslaagd |
| Verversing | 4 tests: bronnen die alleen de kern dekken krijgen het label kern; de uitvoer wordt gesplitst in kern en een bestand per regio; zonder regio's blijft alles in één bestand; een geweigerd verzoek wordt geteld, ook als de herhaling slaagt | Geslaagd |
| Regiofilter, logica | 9 tests: de kern alleen is de lijst zoals hij is; een regio wordt ingevoegd op datum en afstand; de gegevens blijven ongewijzigd; gemeenten volgen de keuze; wat een regio toevoegt; gegevens van vóór de regio's bieden geen keuze; welk regiobestand bij een gemeente hoort; het bereik van het afstandsfilter; namen in een zin | Geslaagd |
| De bestanden in de repo | 5 tests: `berichten.json` houdt alleen de kern en noemt de regio's; elk regiobestand houdt alleen zijn regio en klopt met het overzicht; geen bericht staat in twee bestanden; faillissementen en de Vlaamse bron blijven in de kern; elk bestand blijft onder 1,5 MB | Geslaagd |
| Regiofilter in de browser, op 320 pixels | 7 tests: de keuze wordt aangeboden en niets is gekozen bij het openen; alles past op 320 pixels (knoppen 44 pixels hoog of meer); een gekozen regio komt erbij op Gebied en Berichten, het kaartje verandert niet, en er wordt precies één bestand gelezen; tikken op een gemeente van de regio toont haar berichten; terug naar de kern en alle regio's tegelijk; de app opent weer met de kern en bewaart de keuze niet; een regiobestand dat niet komt laat de kern staan met een melding | Geslaagd |
| Ochtendscherm | De app leest bij het openen geen regiobestand; met een regio erbij blijven de ochtendzin en de tegel Nieuw gelijk; na "Alleen de kern" is het scherm gelijk aan het begin | Geslaagd |
| Tabblad Adres met een adres buiten de kern (browser, nagespeelde bronnen) | Noordweg 402 in Middelburg: het bericht uit het bestand van Zeeland staat onder "Dit adres", het bestand is één keer gelezen, en de app zelf toont nog alleen de kern | Geslaagd |
| Alle tests | `python -m unittest discover tests` | 336 tests, geslaagd; 10 overgeslagen (6 filmtests zoals voorheen, 4 die alleen op verzoek tegen de echte bronnen draaien) |
| Tegen de echte bronnen | `TILBURG_ADRES_LIVE=1 python -m unittest tests.test_adres.EchteBronnen`, 20:47 uur, 320 pixels | Geslaagd, 26 seconden, zeven adressen; zie hieronder |

## Eén adres in Middelburg en één in Breda (echte bronnen, 20:47 uur)

| Adres | Pand volgens BAG | Perceel | Publicaties | Regiobestand |
|---|---|---|---|---|
| Noordweg 402, Middelburg | 1622, industriefunctie en woonfunctie, 391 m², pand in gebruik | Middelburg T 3010, 6.249 m² | Dit adres: 1 (aanvraag omgevingsvergunning, 16-11-2026) | `regio-zeeland.json`, één keer gelezen; "Doorzocht: 2.205 berichten … en die van Zeeland" |
| Prinsenkade 10, Breda | 1900, kantoorfunctie, 699 m², pand in gebruik | Breda F 1290, 566 m² | Dit adres: 1 (beslistermijn opgeschort, 16-11-2026) | `regio-west-brabant.json`, één keer gelezen; "Doorzocht: 2.498 berichten … en die van West-Brabant" |

Bij beide: het kaartbeeld geladen, niets breder dan het scherm, geen fouten. Voor de twee adressen
in Tilburg uit dezelfde proef is geen regiobestand gelezen.

Deze proef liep tegen de bestanden van de werkbranch vanaf de container, met de regiobestanden van
de run van 20:31 uur. Op de live site kan het pas na samenvoegen.

## Bekeken op schermafbeeldingen (320 pixels)

Het tabblad Gebied zonder en met West-Brabant gekozen, de rij van Roosendaal met de opmerking over de
aanvragen, en het tabblad Berichten met de regel "Met West-Brabant erbij." Geen afbreking of
overlap gezien.

# Run 22 op GitHub (18-11-2026, 08:19 – 08:33 uur)

De handmatige run vanaf de werkbranch (commit `6075815`), zonder "volledig". Ik kon hem niet zelf
starten: de koppeling van deze sessie mag geen workflow starten (403, twee keer geprobeerd). Wim
heeft hem gestart; ik heb het log en het resultaat gelezen. De run begon met de cache van `main` van
17-11, die de regio's nog niet kent: dit is dus de situatie van de eerste run na samenvoegen.

| Stap | Duur | Verzoeken | Weigeringen (HTTP 429) | Uitkomst |
|---|---:|---:|---:|---|
| Tests | 11 s | geen | | 336 tests geslaagd; 55 overgeslagen, omdat de browser in die stap nog niet klaarstaat |
| Browser klaarzetten | 18 s | | | Geslaagd; Chromium uit de bewaarde map |
| Browsertests | 34 s | geen naar de bronnen (PDOK wordt nagespeeld) | | 44 tests geslaagd, met die van het regiofilter en het adres buiten de kern |
| Gebied bijwerken | 17 s | 29 | 0 | Geslaagd |
| **Berichten ophalen** | **12 min 49 s** | **1.404** | **173** | Geslaagd, met een waarschuwing: 35 teksten niet opgehaald |
| Cache bewaren | | | | Overgeslagen: alleen vanaf `main` |
| publiceren, live-controleren | | | | Overgeslagen: alleen vanaf `main` |
| **Hele run** | **14 min 20 s** | **1.433** | **173** | **Geslaagd (groen), niets gepubliceerd, geen cache geschreven** |

### De stap "Berichten ophalen" in cijfers

| | |
|---|---:|
| Verzoeken aan de bron (repository.overheid.nl) | 1.191 |
| Verzoeken aan PDOK | 209 |
| Verzoeken aan de Vlaamse bron | 4 (de bron antwoordde uiteindelijk; 8 berichten) |
| Teksten gevraagd | 1.461, waarvan 480 uit de cache |
| Teksten in de eerste ronde mislukt | 49: 37 door een weigering, 12 door "netwerk onbereikbaar" op de runner |
| Daarvan bij herhaling gelukt | 14 |
| **Teksten definitief niet opgehaald** | **35** |
| Percelen gevraagd / mislukt | 192 / 0 |
| Berichten | 3.699: kern 1.080, Midden-Brabant 187, West-Brabant 1.363, Zeeland 1.069 |

De 173 weigeringen tellen elke geweigerde poging, ook de pogingen die bij herhaling slaagden; daarom
zijn het er meer dan de 37 in de regel over de teksten.

### Wat er met de 35 niet-gelezen teksten gebeurt

Het resultaat van de run is opgehaald en nagelezen (het bestand dat de run voor de site klaarzet).
De berichten waarvan de tekst niet kwam, staan tijdelijk onder Onzeker met die reden. Ik vond er 31
terug: 20 in West-Brabant, 9 in Zeeland, 2 in Midden-Brabant en **geen in de kern**. De kern is in
deze run heel: 1.080 berichten, 80 ontwikkellocaties, 22 onzeker. De volgende run probeert de
ontbrekende teksten opnieuw; vanaf de branch kan dat niet worden aangetoond, omdat de cache daar
niet bewaard wordt.

### Wat dit betekent voor de afspraak

De afspraak was: stoppen met uitbreiden als een gewone run de tien minuten overschrijdt of er
structureel weigeringen komen. **Deze run ging erover.** Het is de eerste run met een cache zonder
regio's, niet de dagelijkse toestand; maar of de dagelijkse toestand op GitHub binnen de grens
blijft, heb ik niet gemeten en kan vanaf een branch ook niet gemeten worden. Er is daarom niets meer
toegevoegd.

### Voorstel (op 18-11-2026 gebouwd: 1, 2 en 4; zie "Grens, telling per regio en wekelijkse beurt")

| Voorstel | Wat het oplost | Prijs |
|---|---|---|
| **1. Een grens per run aan het aantal nieuwe teksten voor de regio's**, bijvoorbeeld 300 | De eerste vulling verspreidt zich over vier runs in plaats van één run van 13 minuten; een dag met veel nieuws loopt niet uit. De kern gaat altijd voor en wordt nooit begrensd | Een regiobericht waarvan de tekst nog niet gelezen is, staat tot de volgende run onder Onzeker met die reden, of blijft zolang weg. Dat is een keuze |
| **2. Niet-gelezen teksten per regio tellen** | De melding bovenaan het ochtendscherm gaat dan alleen over de kern. Nu zou ze na deze run "35 bekendmakingen" melden terwijl de kern heel is | Klein; de regio's melden hun eigen tekort bij de regio |
| 3. Minder verzoeken tegelijk als er veel te halen is (2 in plaats van 4) | Minder weigeringen | De run duurt langer; lost de tien minuten niet op |
| 4. De wekelijkse volledige run in delen | Die run zou anders ruim twee keer zo zwaar zijn als run 22 | Elke regio eens per drie weken volledig ververst |
| 5. Regio's één voor één toevoegen | De eerste vulling is per keer een derde | Drie keer samenvoegen; lost dagen met veel nieuws niet op |

Mijn advies: 1 en 2 samen, en 4 voordat de eerste zondag aanbreekt. Daarna opnieuw meten met een
handmatige run. Ik bouw hiervan niets zonder akkoord.

# Grens, telling per regio en wekelijkse beurt (18-11-2026)

Gebouwd op verzoek van Wim na run 22. Niet samengevoegd; het schema van de workflow en de cache
zijn niet gewijzigd.

## Wat er is gebouwd

| Onderdeel | Wat |
|---|---|
| **1. Grens per run** | Een run leest hoogstens 300 nieuwe teksten van de regio's (`grens_regioteksten` in `config.json`). De kern wordt eerst en helemaal gelezen, in een eigen ronde: pas als die klaar is, herhalingen inbegrepen, wordt de eerste regiotekst gevraagd |
| Welke 300 | De nieuwste berichten eerst. Een tekst die al in de cache staat, is niet nieuw en telt niet mee |
| Een bericht dat wacht | Staat in zijn regio onder Onzeker, onderaan, met de zin "Tekst nog niet gelezen; een volgende verversing haalt hem op." Dat geldt voor elk wachtend bericht, ook als de titel al veel zegt. Voor zo'n bericht wordt ook geen perceel opgezocht |
| **2. Telling per regio** | De run telt per regio hoeveel berichten een tekst of perceel missen. `ophaalfouten` in `berichten.json`, waar de melding op het ochtendscherm uit komt, telt alleen nog de kern. Het overzicht van de regio's noemt per regio `ongelezen` en `mislukt` |
| Meldingen in de app | Het ochtendscherm meldt alleen de kern. De knop van een regio op het tabblad Gebied zegt "143 locaties · 146 ongelezen". Wie een regio kiest, krijgt op het tabblad Berichten de meldingen van die regio erbij |
| **3. Wekelijkse beurt** | De volledige verversing leest de kern en één regio opnieuw; de andere twee komen uit de cache |
| Mislukt het opnieuw lezen | Dan blijft de tekst van vorige keer staan in plaats van te verdwijnen. Run 22 liet zien dat er bij veel verzoeken teksten uitvallen; bij een verversing kost dat nu niets meer |
| Het log van een run | Meldt per regio wat wacht en wat mislukte, en welke regio's opnieuw gelezen zijn |

## Welke regio wanneer

De week loopt van maandag tot en met zondag en wordt doorgeteld, zodat de beurt bij de jaarwisseling
niet verspringt. De geplande volledige run is zondag 04:30 uur. Een handmatige volledige run neemt
de regio van de lopende week; deze week (16 tot en met 22 november) is dat Midden-Brabant.

| Zondag | Kern | Regio die opnieuw gelezen wordt |
|---|---|---|
| 22-11-2026 | ja | Midden-Brabant |
| 29-11-2026 | ja | West-Brabant |
| 06-12-2026 | ja | Zeeland |
| 13-12-2026 | ja | Midden-Brabant |
| 20-12-2026 | ja | West-Brabant |
| 27-12-2026 | ja | Zeeland |
| 03-01-2027 | ja | Midden-Brabant |
| 10-01-2027 | ja | West-Brabant |
| 17-01-2027 | ja | Zeeland |

Daarna gaat het zo door: elke regio eens per drie weken, de kern elke week. Een andere regio
afdwingen kan alleen buiten de workflow om (`--volledig --regio Zeeland`).

## Waar de vier teksten bleven

Run 22 meldde 35 niet-opgehaalde teksten; in het resultaat vond ik 31 berichten met de zin "kon niet
worden opgehaald".

| Vraag | Antwoord |
|---|---|
| Waar zijn de andere vier? | In het resultaat, met een gewone uitkomst. De regels van de app kijken eerst naar de titel en de omschrijving. Zegt de titel al genoeg (een thematisch plan, "het bouwen van 12 woningen", een herkenbaar signaal), dan krijgt het bericht die uitkomst en komt de zin over de ontbrekende tekst er niet aan te pas |
| Is er één aan te wijzen? | Ja, één: `gmb-2026-383525`, "Kennisgeving 'Omgevingsprogramma Centrum West'" (Roosendaal). In run 22 weggefilterd als thematisch plan, zonder signaal; in de volledige run van 17-11 met het signaal "functiewijziging", dat uit de tekst komt. De uitkomst is gelijk, alleen dat ene veld verschilt |
| En de andere drie? | Niet aan te wijzen. Ik heb alle 1.461 berichten die een tekst nodig hadden vergeleken met de run van 17-11: bij deze drie is elk veld gelijk. De tekst ontbrak, maar veranderde niets aan wat de app toont |
| Was er iets kwijt? | Nee. De telling van 35 klopte; alleen was aan vier berichten niet te zien dat ze erbij hoorden |
| Wat is eraan gedaan | De telling per regio telt een ontbrekende tekst ook als de titel al beslist. Daar is een test voor |

## Proef vanuit de container (18-11-2026, 08:58 – 09:03 uur)

Drie runs achter elkaar, beginnend met de cache van `main` van 17-11 zonder regio's: dezelfde
uitgangspositie als run 22.

| Run | Verzoeken | waarvan aan de bron | Duur | Weigeringen | Regioteksten gelezen | Wachten nog |
|---|---:|---:|---:|---:|---:|---:|
| Gewone run 1 | 494 | 334 | 117 s | 0 | 300 | 681 (Midden-Brabant 50, West-Brabant 398, Zeeland 233) |
| Gewone run 2 | 353 | 334 | 77 s | 0 | 300 | 381 (28, 238, 115) |
| Volledige run (kern en Midden-Brabant) | 1.215 | 1.063 | 196 s | 0 | 300 nieuw, plus Midden-Brabant opnieuw | 81 (3, 52, 26) |

Ter vergelijking: zonder grens deed dezelfde eerste run op GitHub 1.404 verzoeken in 769 seconden
(run 22).

| Controle op het resultaat | Uitkomst |
|---|---|
| De kern | 1.080 berichten, dezelfde als in run 22, met dezelfde inhoud; geen enkel bericht met "Tekst nog niet gelezen" |
| `ophaalfouten` (ochtendscherm) | 0 teksten, 0 percelen, 0 rechtbankpublicaties |
| De wachtende berichten | Staan alle onder Onzeker met het label; het aantal per regio in het overzicht is gelijk aan het aantal in het regiobestand |
| Volgorde | Na drie runs wachten alleen nog berichten van 22-05 tot en met 23-07-2026; alles daarna is gelezen |
| De volledige run | Las de 200 rechtbankpublicaties en de kern opnieuw; West-Brabant en Zeeland kwamen uit de cache (552 teksten) |

Na een vierde run wacht er niets meer. Op GitHub is dit nog niet gedraaid; dat is de volgende
handmatige run.

## Tests

| Wat | Tests |
|---|---|
| Grens per run | 6: de kern helemaal en eerst, daarna de nieuwste van de regio's; de grens raakt de kern nooit; zonder grens alles zoals voorheen; het label is één zin en gaat voor wat de titel zegt; geen perceel voor een bericht dat wacht; een tekst uit de cache is niet nieuw en de volgende run leest verder |
| Telling per regio | 7: een mislukking in een regio is geen mislukking van de kern; een mislukking in de kern wordt gemeld zoals voorheen; een ontbrekende tekst telt ook als de titel beslist (de vier van run 22); een mislukt perceel telt bij zijn regio; statistiek zonder uitsplitsing; wat de run voor het ochtendscherm schrijft gaat over de kern; elke regio krijgt haar eigen telling in het overzicht |
| Wekelijkse beurt | 9: welke regio welke zondag; de hele week dezelfde regio en geen week overgeslagen (120 weken, ook over de jaarwisseling); kern en regio van de week opnieuw, de rest uit de cache; een mislukte verversing houdt wat er was; een nooit gelezen tekst die mislukt wordt opnieuw geprobeerd; opzoekingen volgen het label van de gemeente; de run leest opnieuw wat zijn opties zeggen; een onbekende regio stopt de run; de grens in `config.json` is 300 |
| Meldingen, logica | 2: een gekozen regio meldt wat ze mist, in enkelvoud en meervoud, en zonder gekozen regio niets; het tekort reist mee met de regio die wordt aangeboden |
| Meldingen, browser op 320 pixels | 1: de kern mist niets en een regio mist 146 teksten en 20 bekendmakingen. Het ochtendscherm zegt daar niets over; de knop van de regio zegt "· 146 ongelezen"; na kiezen staan beide meldingen op het tabblad Berichten; na "Alleen de kern" zijn ze weer weg |
| Alle tests | 361, geslaagd; 10 overgeslagen zoals voorheen |

## Open punten bij dit onderdeel

| Punt | Toelichting |
|---|---|
| **De week van West-Brabant blijft zwaar** | De volledige run leest dan de kern (480 teksten), West-Brabant (550) en de 200 rechtbankpublicaties opnieuw: naar schatting 1.250 tot 1.300 verzoeken aan de bron, iets meer dan run 22. Op GitHub is dat geschat op 12 tot 14 minuten met weigeringen. Het verschil met run 22: een tekst die nu niet komt, blijft staan zoals hij was. De weken van Midden-Brabant (rond 800) en Zeeland (rond 1.100) zijn lichter. Eerste keer: zondag 29-11-2026. Wil je dit lichter, dan kan West-Brabant in tweeën, of de kern om de week |
| De toelichting in de workflow klopt niet meer | Daar staat "cache negeren en alles opnieuw ophalen" bij de wekelijkse run en bij het vinkje "volledig". Ik heb het bestand niet aangeraakt, omdat het schema niet mocht wijzigen. Twee regels tekst; zeg het als ik ze mag aanpassen |
| Op GitHub nog niet gemeten | De cijfers hierboven komen uit de container, waar de bron niets weigert. De volgende handmatige run laat zien wat 334 verzoeken aan de bron daar doen |
| Een wachtend bericht verbergt wat de titel al zegt | Zo afgesproken: elk wachtend regiobericht staat onder Onzeker. Een aanvraag met "12 woningen" in de titel staat dus hooguit een paar runs te laag. Het gaat om de oudste berichten eerst |
| Vier runs voor de eerste vulling | 300, 300, 300 en 81 teksten. Met vijf runs per werkdag is dat binnen een dag rond |

# Run 23 op GitHub (18-11-2026, 09:13 – 09:19 uur)

De tweede handmatige run vanaf de werkbranch (commit `2548356`), zonder "volledig", door Wim gestart.
Dezelfde beginstand als run 22: de cache van `main` zonder regio's. Nu met de grens van 300.

| Stap | Duur | Verzoeken | Weigeringen (HTTP 429) | Uitkomst |
|---|---:|---:|---:|---|
| Tests | 14 s | geen | | 361 tests geslaagd; 56 overgeslagen, omdat de browser in die stap nog niet klaarstaat |
| Browser klaarzetten | 28 s | | | Geslaagd |
| Browsertests | 37 s | geen naar de bronnen | | 45 tests geslaagd |
| Gebied bijwerken | 15 s | 29 | 0 | Geslaagd |
| **Berichten ophalen** | **4 min 23 s** | **613** | **89** | Geslaagd, met één waarschuwing: 1 tekst in Zeeland niet opgehaald |
| Cache bewaren, publiceren, live-controleren | | | | Overgeslagen: alleen vanaf `main` |
| **Hele run** | **6 min 9 s** | **642** | **89** | **Geslaagd (groen), niets gepubliceerd, geen cache geschreven** |

| Run 22 en run 23 naast elkaar | Run 22 (zonder grens) | Run 23 (grens 300) |
|---|---:|---:|
| Duur van "Berichten ophalen" | 12 min 49 s | 4 min 23 s |
| Verzoeken in die stap | 1.404 | 613 |
| waarvan aan de bron | 1.191 | 451 |
| Weigeringen | 173 | 89 |
| Teksten definitief niet opgehaald | 35 | 1 |
| Regioteksten gelezen | 946 (alles in één keer) | 300 |
| Regioberichten die nog wachten | 0 | 713 |

### Wat het resultaat laat zien

Het resultaat van de run is opgehaald en nagelezen.

| Vraag | Antwoord |
|---|---|
| Staat de melding op het ochtendscherm op nul? | **Ja.** `ophaalfouten` is 0 teksten, 0 percelen, 0 rechtbankpublicaties; geen onvolledige dagen; alle drie de bronnen in orde |
| Hoeveel regioberichten wachten nog? | **713**: West-Brabant 415, Zeeland 243, Midden-Brabant 55. Ze staan alle onder Onzeker met "Tekst nog niet gelezen"; het aantal in het overzicht is gelijk aan het aantal in elk regiobestand |
| Welke wachten? | De oudste: alles tot en met 02-11-2026. Wat daarna gepubliceerd is, is gelezen |
| Is de kern gelijk aan die van run 22? | **Ja.** Alle 1.080 berichten van run 22 staan erin met dezelfde inhoud. Er zijn er 21 bij, alle van vandaag (18-11-2026) en alle weggefilterd: de publicaties van 9 uur. De kern telt nu 1.101 berichten, 80 ontwikkellocaties en 22 onzeker, zoals in run 22 |
| Heeft de kern iets gemist? | Nee: 0 mislukt, 0 wachtend, geen bericht met het label of met de zin over een niet-opgehaalde tekst |
| De ene tekst die niet kwam | Hoort bij Zeeland en is daar geteld (`mislukt: 1`); het log meldt het bij Zeeland. De volgende run probeert het opnieuw |

De teksten: 800 gevraagd, waarvan 480 uit de cache; 319 opgehaald (300 van de regio's en 19 nieuwe
van de kern van vandaag). In de eerste ronde mislukten er 23 (21 door een weigering, 2 doordat het
netwerk van de runner even onbereikbaar was); 22 lukten bij herhaling.

### Wat dit betekent

| Punt | Toelichting |
|---|---|
| De tien minuten | Gehaald: ruim zes minuten voor de hele run |
| Weigeringen | Die blijven er op GitHub zodra een run een paar honderd teksten leest: 89 op 451 verzoeken aan de bron. Bij herhaling komt bijna alles binnen. De gewone dagelijkse run van `main` doet rond de 34 verzoeken en krijgt er geen |
| De vulling | Nog drie runs van deze omvang (300, 300 en 113 teksten). Vanaf een branch telt dat niet door, omdat de cache daar niet bewaard wordt; na samenvoegen gebeurt het vanzelf, in de eerste vier runs |
| Daarna | Per run alleen de nieuwe teksten van die dag: voor de regio's naar schatting 20 tot 30 per dag, ver onder de grens |
| De wekelijkse volledige run | Niet in deze run gemeten. Zie "Open punten bij dit onderdeel": de week van West-Brabant blijft de zwaarste |

# Groei van de cache en de regiobestanden (18-11-2026, 09:31 – 09:48 uur)

## Wat de grens van 1,5 MB is en wat hij raakt

De grens is een test: `tests/test_ververst.py` keurt de repo af zodra er een bestand groter dan
1.500.000 bytes in staat. Die test draait in de stap "Tests", de eerste stap van elke run.

| Bestand | Schrijft een run het terug in de repo? | Wat gebeurt er boven 1,5 MB |
|---|---|---|
| `cache/ophaalcache.json` | **Ja**, vanaf `main`, bij elke wijziging | De run die hem schrijft slaagt nog. **Elke run daarna strandt in "Tests", vóór het ophalen**: er wordt niet ververst en niets gepubliceerd, tot iemand de cache met de hand verkleint. De live site blijft op de laatste stand staan |
| `site/data/berichten.json` en de drie regiobestanden | Nee. Een run schrijft ze en publiceert ze, maar zet ze niet in de repo | Geen run strandt erop: na het ophalen controleert niets de grootte. Het raakt alleen de telefoon (een groter bestand) en de momentopname in de repo, als iemand die ooit vernieuwt |

Alleen de cache kan de verversing dus stilzetten. Dat is een feit uit de code en de workflow; het is
niet op GitHub uitgeprobeerd.

## Stand nu

| Bestand | Grootte | Inhoud | Deel van de grens |
|---|---:|---|---:|
| Cache op `main` (alleen de kern), zeven versies van 16-11 tot 18-11-2026 | 277 – 284 kB | rond 480 teksten | 19% |
| Cache met alle regio's gelezen (container, 17-11-2026, 20:36 uur) | 922 kB | 1.478 teksten, 175 locaties, 169 percelen | 61% |
| `berichten.json` (kern), run 23 | 996 kB | 1.101 berichten | 66% |
| `regio-midden-brabant.json`, run 23 | 173 kB | 187 berichten | 12% |
| `regio-west-brabant.json`, run 23 | **1.334 kB** | 1.433 berichten | **89%** |
| `regio-zeeland.json`, run 23 | 1.001 kB | 1.074 berichten | 67% |

Een bericht kost 900 tot 955 bytes; 1,5 MB is dus ongeveer 1.600 berichten in één bestand. Een tekst
in de cache kost gemiddeld 600 bytes (vergunning rond 490, plan rond 1.340).

Over de lijn gaan de databestanden gecomprimeerd, als GitHub Pages dat doet zoals gebruikelijk:
West-Brabant is met gzip 117 kB, de kern 103 kB, Zeeland 97 kB, Midden-Brabant 18 kB. Dat is hier
met gzip nagerekend, niet op de live site gemeten.

## Ze groeien niet door; ze volgen het venster

**Feit:** een vergunning verdwijnt na 42 dagen uit de lijst, een plan na 180 dagen. De cache bewaart
alleen wat een run gebruikt heeft; wat uit het venster valt, valt bij de volgende run ook uit de
cache. De bestanden worden dus niet elke dag groter. Hun grootte volgt het aantal publicaties in het
venster en gaat met de drukte op en neer.

Dat is van dag tot dag te zien aan West-Brabant: 1.292 kB op 17-11 (1.382 berichten), 1.274 kB op
18-11 om 08:20 uur (1.363) en 1.334 kB om 09:15 uur (1.433; de 70 publicaties van die ochtend waren
erbij gekomen).

**Daarmee vervalt het voorbeeld uit de opdracht:** teksten ouder dan 180 dagen laten vervallen gebeurt
al. Het zou niets opleveren.

## Meting over een jaar

De bron is per week gevraagd hoeveel vergunningen er waren (alleen de aantallen, één klein verzoek
per week en per groep), over 59 weken van 29-09-2025 tot en met 15-11-2026, en per 30 dagen hoeveel
plannen. Samen 316 verzoeken in 224 seconden, zonder weigering (09:36 – 09:39 uur). Daaruit zijn 54 vensters
van zes weken gemaakt. De grootte per venster is geschat met de bytes per bericht van de run van
17-11-2026.

| Groep | Vergunningen in 42 dagen, nu | Laagste van het jaar | Hoogste van het jaar | Zelfde venster een jaar eerder |
|---|---:|---:|---:|---:|
| Kern | 1.426 | 1.223 (begin september 2026) | 1.712 (half juli 2026) | 1.497 |
| Midden-Brabant buiten de kern (Altena) | 102 | 84 (begin februari 2026) | 163 (begin april 2026) | 106 |
| West-Brabant | 1.084 | 966 (half januari 2026) | 1.299 (tweede helft juli 2026) | 1.261 |
| Zeeland | 972 | 793 (begin september 2026) | 1.134 (tweede helft april 2026) | 911 |
| Alles samen | 3.584 | 3.148 | 4.285 (tweede helft juli 2026) | 3.775 |

Een stijgende lijn is er niet: het eerste halfjaar telde gemiddeld 3.751 vergunningen per venster,
het tweede 3.688. Wat er te zien is, is seizoen: druk van februari tot en met april en in juni en
juli, rustig rond de jaarwisseling en van half augustus tot oktober.

| Bestand | Laagste schatting | Hoogste schatting | Deel van de grens op het hoogst | Vensters boven 1,5 MB | Gemiddelde verandering per week |
|---|---:|---:|---:|---:|---:|
| Cache (met alle regio's) | 0,83 MB (september) | 1,20 MB (tweede helft april) | 80% | 0 van 54 | 23 kB |
| `berichten.json` (kern) | 0,87 MB (september) | 1,18 MB (half juli) | 79% | 0 van 54 | 24 kB |
| `regio-midden-brabant.json` | 0,15 MB | 0,29 MB | 19% | 0 van 54 | 14 kB |
| `regio-west-brabant.json` | 1,17 MB (januari) | **1,46 MB** (april en juli) | **97%** | 0 van 54; 22 van de 54 boven 90% | 35 kB |
| `regio-zeeland.json` | 0,84 MB (september) | 1,26 MB (tweede helft april) | 84% | 0 van 54 | 27 kB |

Als de drukste weken voor vergunningen en voor plannen zouden samenvallen, wat het afgelopen jaar niet
gebeurde, komt de cache op 1,25 MB (84%) en West-Brabant op 1,55 MB (103%).

**Hoe nauwkeurig dit is.** Het is een schatting, geen meting van de bestanden zelf: die bestaan pas
sinds 17-11-2026. De telling is per groep van gemeenten en gaat ervan uit dat een bericht even groot
blijft en dat van evenveel berichten de tekst gelezen moet worden. Voor vandaag geeft de schatting
voor West-Brabant 1,28 MB, terwijl run 23 op 1,33 MB uitkwam: 4 procent ernaast. Reken dus met een
marge van ongeveer 5 procent naar beide kanten. Er is één jaar geteld; wat een drukker jaar doet,
staat er niet in.

## Wanneer ze de grens bereiken

| Bestand | Wanneer | Toelichting |
|---|---|---|
| **Cache** | **Bij het verloop van het afgelopen jaar: niet.** Het hoogst in de tweede helft van april, rond 1,2 MB | Er blijft dan ongeveer 20 procent over. De grens komt pas in zicht als er iets bijkomt: de rubriek "andere beschikking", de provincie Zeeland, een vierde regio, of een jaar dat een vijfde drukker is dan het drukste van nu |
| Cache, direct na samenvoegen | Van 0,28 MB naar ongeveer 0,9 MB in de eerste vier runs | 300 teksten per run is ongeveer 180 kB erbij per run. Dat is de vulling, geen doorlopende groei |
| **`regio-west-brabant.json`** | **Mogelijk in maart – april 2027 en in juli 2027**: de schatting komt dan op 1,45 tot 1,46 MB, binnen de marge van de grens | Er strandt geen run op. Het bestand zit het grootste deel van het jaar boven 90 procent, ook nu |
| `berichten.json` (kern) en `regio-zeeland.json` | Niet; hoogstens 79 en 84 procent | |
| `regio-midden-brabant.json` | Niet; hoogstens 19 procent | |

## Voorstel (niet gebouwd)

| | Wat | Wat het oplost | Wat het kost |
|---|---|---|---|
| **A** | **Vangnet en waarschuwing voor de cache.** Een run schrijft nooit een cache boven 1,4 MB: hij laat dan de oudste regioteksten weg (de kern blijft altijd staan) en meldt het in het log. Vanaf 1,2 MB meldt het log de grootte als waarschuwing. De weggelaten teksten haalt de volgende run opnieuw op, binnen de grens van 300 | De verversing kan zichzelf niet meer stilzetten, ook niet als de schatting te laag blijkt of er iets bijkomt | Klein: `signalen/cache.py`, `signalen/update.py` en tests. De workflow blijft ongewijzigd. Een waarschuwing staat in het overzicht van de run; je krijgt er geen bericht van |
| **B** | **De cache per regio in een eigen bestand**: `cache/ophaalcache.json` blijft van de kern, daarnaast één bestand per regio | Structureel. Het grootste deel (West-Brabant) is nu ongeveer 0,37 MB en op het drukst naar schatting 0,45 MB; elk bestand blijft onder een derde van de grens. Er is dan ruimte voor een vierde regio of een extra rubriek | Middelgroot: `signalen/cache.py`, `signalen/update.py`, tests, en één regel in de stap "Cache bewaren" van de workflow (de map in plaats van het ene bestand). Het schema blijft gelijk |
| **C** | **West-Brabant in twee bestanden**, bijvoorbeeld Breda met de buurgemeenten en de rest. In de app blijft het één knop | Het bestand blijft ver onder 1,5 MB en de telefoon haalt per keer minder op | Middelgroot: `signalen/update.py`, `site/app.js`, `site/adres-app.js`, tests. Raakt geen run; nu niet nodig |
| D | Teksten eerder laten vervallen | Niets: de cache laat nu al alles vallen wat buiten het venster valt. Een kortere termijn zou betekenen dat plannen eerder uit de lijst verdwijnen | Niet aangeraden |
| E | De grens in de test verhogen, of de bewaarde teksten korter maken | Verschuift het probleem; kortere teksten veranderen het oordeel over een bericht | Niet aangeraden |

**Advies:** A nu, omdat het klein is en het enige risico wegneemt dat een run kan stilzetten. B op het
moment dat je iets toevoegt ("andere beschikking", de provincie Zeeland, een regio) of als de
waarschuwing van A zich meldt. C alleen als je de download op de telefoon kleiner wilt of de
momentopname in de repo wilt vernieuwen. Geen van de drie is gebouwd; graag je akkoord per onderdeel.

## Niet getest of nog open bij dit onderdeel

| Punt | Toelichting |
|---|---|
| De schatting is niet aan echte bestanden getoetst | Er zijn pas twee dagen bestanden met regio's. De eerste echte toets is de drukte van februari tot en met april 2027 |
| Wat er gebeurt boven 1,5 MB is niet uitgeprobeerd | Afgeleid uit de test en de volgorde van de stappen in de workflow |
| De geschiedenis van de repo | Niet gemeten. Elke wijziging van de cache is een nieuwe versie in `main` (twee tot drie per dag); gecomprimeerd is de cache met regio's 191 kB per versie. Of GitHub daar last van krijgt, weet ik niet |
| Verkoop van gemeentegrond | Niet apart geteld; meegeschaald met de plannen. Het is 3 procent van de berichten |
| Compressie op de live site | Aangenomen, niet gemeten |

# De Vlaamse bron

Niet onderzocht, zoals gevraagd. Wat ik zonder onderzoek kan zeggen: de bron geeft **niet bij elke run
een melding**. Op de live site stond hij om 19:36 uur op "in orde" met 9 berichten. De enige uitval die ik in de verslagen terugvind is run 13 (17-11-2026, 11:33 uur), toen de
runner de naam van de dienst niet kon vinden. Er is daarom niets voorgesteld en niets gewijzigd. Bij
de vier metingen vanuit de container antwoordde de bron elke keer.

# Open punten

| Punt | Toelichting | Voorstel |
|---|---|---|
| **De eerste run na samenvoegen is zwaar** | De cache op `main` kent de regio's nog niet en mag niet vanaf de branch mee. De eerste run leest daarom ongeveer 1.000 teksten en zoekt ruim 150 percelen op: naar schatting 1.300 verzoeken. Op GitHub duurde 1.056 verzoeken ruim 8 minuten, met 43 weigeringen die bij herhaling slaagden. Deze run zal daar dus omheen liggen, mogelijk boven de tien minuten. Daarna is het een gewone run | Niet doorgevoerd. De eerste run op een rustig moment laten vallen (niet vlak voor 06:45 uur), en vooraf een handmatige run vanaf de werkbranch doen om het op GitHub te meten: die test en haalt op, maar zet niets live en schrijft geen cache |
| **De wekelijkse volledige run wordt ruim twee keer zo lang** | Zondag 04:30 uur leest alles opnieuw: 2.047 verzoeken hier, tegen 841 nu. Op GitHub geschat op 17 tot 20 minuten en rond de 100 weigeringen. Dat is geen gewone run en raakt de stopregel dus niet, maar het is wel de run met het meeste risico | Niet doorgevoerd. De volledige verversing in delen doen: elke week de kern en één regio, zodat elke regio eens per drie weken volledig ververst wordt. Dat vraagt een extra invoer voor de run, geen ander schema |
| **Op GitHub is niets gemeten** | Alle cijfers komen uit deze container. Of de bron vanaf GitHub bij een gewone run met 35 tot 65 verzoeken gaat weigeren, weet ik niet; bij de huidige 34 gebeurt het niet | De handmatige run vanaf de werkbranch hierboven geeft het antwoord. Graag je akkoord voordat ik die start |
| Roosendaal: aanvragen ontbreken | 58 berichten in 42 dagen staan onder "andere beschikking" | Voor Roosendaal ook die rubriek lezen en filteren op "omgevingsvergunning" in de titel: één extra zoekvraag per run. Dezelfde ingreep vangt de handvol berichten in Dongen, Etten-Leur, Vught en Noord-Beveland. Raakt de kern (Dongen, Vught) en is daarom niet gedaan |
| Provincie Zeeland en waterschap Scheldestromen | Hun bladen worden niet opgevraagd; die van Noord-Brabant en de drie Brabantse waterschappen wel, en hun berichten in West-Brabant komen nu ook mee | Toevoegen aan `extra_overheden` als je ze wilt; niet onderzocht hoeveel dat oplevert |
| Faillissementen buiten de kern | Blijven bij de kern | Vraagt een groter postcodegebied en per zaak een opzoeking in de BAG; apart te meten |
| "Nieuw" geldt niet voor een regio | Wie elke ochtend West-Brabant erbij kiest, ziet niet wat daar sinds gisteren bij is gekomen, behalve door op datum te sorteren | Per regio bijhouden wat gezien is, zodra je een regio dagelijks gaat gebruiken |
| Eén bericht met een verkeerde locatie in de bron | Een aanvraag van Bergen op Zoom (`gmb-2026-509724`) ligt volgens de bron op 105,8 km van Tilburg, terwijl de gemeente tot 60,8 km reikt. Het is 1 van de 2.663 regioberichten; in de kern komt het niet voor | Een bericht waarvan de locatie buiten zijn eigen gemeente valt, als "geen exacte locatie" behandelen. Niet gedaan: het zou ook voor de kern gelden |
| De cache wordt ruim drie keer zo groot | 922 KB in plaats van 280 KB. De workflow zet hem bij elke wijziging terug in `main`; de geschiedenis van de repo groeit dus sneller | Geen actie nodig; noem het als de repo traag wordt |
| `regio-west-brabant.json` zit dicht bij de grens van 1,5 MB | 1,29 MB. De test die grote bestanden weert, kijkt naar wat in de repo staat, niet naar wat een run schrijft. De live site heeft er geen last van | West-Brabant splitsen (bijvoorbeeld Breda apart) als de momentopname in de repo ooit vernieuwd wordt en groter uitvalt |
| De stap "Gebied bijwerken" doet 26 verzoeken meer | Eén per regiogemeente, aan PDOK, bij elke run; 17 seconden in plaats van 4 | De grenzen van gemeenten wijzigen hooguit per 1 januari. Ze kunnen bewaard worden in plaats van elke run opgevraagd |
| De momentopname in de repo loopt uiteen | `berichten.json` is van 16-11-2026, de regiobestanden zijn van 17-11-2026 | Hoort bij de keuze om de video-tests niet te breken; op de live site schrijft elke run alles tegelijk |
| Op een echte telefoon | Niet te doen vanuit deze container; getest in Chromium op 320 pixels | Aan jou, na samenvoegen |
| De live site | Niets is samengevoegd; de browsertests op GitHub hebben voor deze wijziging nog niet gedraaid | Na je akkoord: pull request, samenvoegen en de run volgen, zoals bij het tabblad Adres |

# Buiten dit verslag

- **Niet samengevoegd, geen pull request**, zoals gevraagd. Er is alleen gewoon gepusht naar de
  werkbranch; niets geforceerd. De werkbranch is na het samenvoegen van PR 16 gelijkgetrokken met
  `main` (vooruitspoelen, geen herschrijving).
- **`cache/ophaalcache.json` is niet gecommit.** De metingen schreven er lokaal in; het bestand is
  daarna teruggezet naar de stand van `main`.
- **Het schema van de workflow is niet gewijzigd**; `.github/` is onaangeroerd. De planner bij
  Cloudflare is niet aangeraakt.
- **De bron is vandaag vanuit deze container belast met** 56 verzoeken voor het onderzoek en vier
  runs voor de metingen (726, 30, 1.722 en 34 verzoeken), tussen 20:25 en 20:37 uur.
- **Bewust niet gedaan:** de Vlaamse bron onderzoeken of aanpassen; Roosendaal repareren; de
  wekelijkse run in delen knippen; een handmatige run op GitHub starten; faillissementen en de
  provincie Zeeland toevoegen; het tabblad Bronnen aanpassen.
- **Geen subsessie** deze ronde, en niets met ElevenLabs.
- **Schermafbeeldingen** zijn in de sessie gemaakt en staan niet in de repo.
