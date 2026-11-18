# Tilburg Signalen: verslag opnieuw ophalen bij terugkeer en het kaartje op het tabblad Gebied

| | |
|---|---|
| Datum | 18-11-2026, 12:49 – 13:02 uur |
| Versie | versie 2 van de app met de regio's, branch `claude/optimistic-gauss-sb0xpy`, opnieuw gestart vanaf `main` op commit `43e2f69` (na PR 20) |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen`; Chromium via Playwright |
| Brondata | Geen opvraging bij de bronnen. Voor het kaartje en de controle: de gegevens van de live site van 18-11-2026, 12:28 uur, opgehaald om 12:51 en 12:58 uur |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_vangnet-cache_18-11-2026.md` |

## Stand

Beide verbeteringen zijn gebouwd en staan op de werkbranch, in een pull request die **open blijft en
niet is samengevoegd**. De app is gewijzigd, de workflow en het schema niet.

PR 20 (het verslag van run 29) is op verzoek van Wim gemaakt en samengevoegd (12:49 uur, merge-commit
`43e2f69`). Die raakt alleen `docs/` en start daarom geen run.

## Correcties en aanvullingen op eerdere verslagen

| Tijdstip | Wat |
|---|---|
| 18-11-2026, 13:02 uur | **De verslagcommit van run 29 staat nu in `main` (PR 20); "staat op de werkbranch en nog niet in `main`" uit mijn melding van 12:35 uur is daarmee achterhaald.** |
| 18-11-2026, 13:02 uur | **Het aantal tests is 402 (was 385).** Er zijn er 17 bij: 9 voor de logica en 8 in de browser. |
| 18-11-2026, 13:02 uur | **"De gegevens zijn ouder dan 15 minuten" heb ik gelezen als: de app heeft ze meer dan 15 minuten geleden voor het laatst opgehaald.** De gegevens zelf zijn bijna altijd ouder dan een kwartier, want er wordt een paar keer per dag ververst; met de letterlijke lezing zou de app bij elke terugkeer ophalen. Zie "Gemaakte keuzes". Zeg het als je het anders bedoelde. |

## Opdracht

1. Als de app weer zichtbaar wordt en de gegevens zijn ouder dan 15 minuten, haalt hij ze opnieuw op
   en werkt hij "Bijgewerkt" bij, zonder dat een gekozen regio, een zoekopdracht of een geopend adres
   verloren gaat.
2. Op het kaartje van het tabblad Gebied overlappen plaatsnamen elkaar (Goirle en Hilvarenbeek) en
   valt het label "15 km" achter een stip, op een iPhone van 375 pixels breed.

Op een werkbranch, met tests, niets samenvoegen zonder akkoord.

## 1. Opnieuw ophalen bij terugkeer

| Onderdeel | Wat de app doet |
|---|---|
| Wanneer | Als de pagina weer in beeld komt (het toestel ontgrendeld, de app naar voren gehaald, of teruggekomen via de terugknop) en de laatste keer ophalen 15 minuten of langer geleden is |
| Wat hij ophaalt | `berichten.json` en `gebied.json`, en het bestand van elke regio die gekozen is |
| Is er een nieuwe run | Dan toont hij de nieuwe berichten en het nieuwe tijdstip achter "Bijgewerkt" |
| Is er geen nieuwe run | Dan verandert er niets; over een kwartier kijkt hij weer |
| Geen verbinding | Alles blijft staan, zonder foutmelding. Bij de volgende terugkeer probeert hij het meteen opnieuw |
| Het bestand van een gekozen regio komt niet | De regio blijft gekozen met de berichten die ze had; de kern is wel nieuw |

Wat blijft staan bij een verversing:

| Wat | Hoe |
|---|---|
| De gekozen regio's | Blijven gekozen; hun bestand wordt opnieuw gelezen |
| De zoekopdracht en de filters | Blijven staan, ook als geen bericht meer bij een gekozen filter past: de keuze staat dan in de lijst met (0) |
| Het filterpaneel | Blijft open als het open stond |
| De gekozen lijst (Ranglijst, Nieuw, Onzeker), "toon alles" en de afstand | Worden door een verversing niet aangeraakt. Dat volgt uit de code; het is niet apart getest |
| Geopende kaarten | Blijven open |
| Het tabblad | Blijft hetzelfde |
| Een opgezocht adres | Blijft staan met pand en perceel. Alleen de publicaties worden opnieuw gezocht, in de nieuwe berichten; PDOK wordt niet opnieuw bevraagd |
| "Nieuw" | Wat met de verversing binnenkomt, telt als nieuw; wat al nieuw was, blijft dat |

## 2. Het kaartje op het tabblad Gebied

**Nagemaakt (feit).** Op 375 pixels, met de gegevens van de live site van 12:28 uur: "Hilvarenbeek" en
"Goirle" liepen door elkaar, "15 km" en "5 km" lagen elk achter twee stippen en "10 km" stond over
"Loon op Zand". Dat laatste stond niet in de melding.

**Oorzaak (feit).** Elke naam stond gecentreerd boven zijn plaats en elk ringlabel op een vaste plek
in het noorden, zonder dat iets rekening hield met wat er al stond. De stippen werden bovendien na de
ringlabels getekend, dus eroverheen.

| Onderdeel | Wat er nu gebeurt |
|---|---|
| Plaatsnamen | De eerste naam blijft staan. Een volgende die een naam zou raken, schuift eerst opzij, weg van die naam en niet verder dan nodig, zodat ze op de hoogte van haar plaats blijft. Lukt dat niet, dan gaat ze onder, boven of naast haar plaats |
| Ringlabels | Elk label loopt langs zijn ring, te beginnen in het noorden, tot het geen stip, geen naam en geen ander label raakt. Het staat net binnen zijn ring |
| Volgorde van tekenen | De teksten komen als laatste, met een lichte rand, zodat ze nooit achter een stip liggen |
| Geen vrije plek | De tekst staat waar ze het minst hindert en krijgt een merkteken in de pagina; dat kan alleen op een heel drukke dag |

Uitkomst op 375 en op 320 pixels, met de gegevens van de live site: geen tekst over een andere, geen
ringlabel achter een stip, alles binnen het kaartje. Goirle staat links naast Hilvarenbeek op dezelfde
hoogte; "15 km" staat linksboven, "10 km" links van Loon op Zand en "5 km" rechts van het midden.

## Gemaakte keuzes

| Keuze | Waarom |
|---|---|
| Een kwartier sinds de laatste keer ophalen, niet de leeftijd van de gegevens | Zie de correctie bovenaan. Het is één regel om het anders te doen |
| Alleen bij terugkeer in beeld, geen klok die doorloopt | Zo stond het in de opdracht. Een app die open en in beeld blijft staan, ververst dus niet vanzelf |
| Na een mislukte poging meteen opnieuw bij de volgende terugkeer | Anders blijft de app na een tunnel of een lift een kwartier op oude gegevens staan |
| Een gekozen filter dat niets meer vindt, blijft staan met (0) | Anders verdwijnt de keuze stil en toont de lijst ineens alles |
| De tekstbreedtes op het kaartje zijn geschat, aan de ruime kant | De plaatsing wordt uitgerekend zonder de browser te vragen hoe breed een tekst is. De browsertest meet daarna de echte tekst |
| De plaats van een naam is het midden van het gebied van de woonplaats | Ongewijzigd. Daardoor staan Hilvarenbeek en Goirle op de kaart dichter bij elkaar dan de dorpskernen in werkelijkheid liggen |
| Service worker: nieuwe versie van de opslag (v9) | De bestanden van de app zijn gewijzigd |

## Tests

402 tests geslaagd in de container (was 385; 10 overgeslagen: 6 van de film, 4 die alleen op verzoek
tegen de echte bronnen draaien).

| Wat | Aantal |
|---|---:|
| Logica: de grens van 15 minuten | 1 |
| Logica van het kaartje: namen die elkaar niet raken blijven staan, Goirle schuift naast Hilvarenbeek en blijft op zijn hoogte, een naam die niet kan schuiven gaat onder of boven, een ringlabel begint in het noorden binnen zijn ring, wijkt voor een stip en voor een naam, een volle ring wordt gemerkt, alles blijft op het kaartje | 8 |
| Browser, terugkeer (375 pixels): binnen een kwartier niets opgehaald; na een kwartier nieuwe berichten en nieuw tijdstip; regio, zoekopdracht, filter en geopende kaart blijven; het adres blijft en krijgt de nieuwe publicatie zonder nieuwe vraag aan PDOK; dezelfde run verandert niets; zonder verbinding blijft alles en de volgende keer probeert opnieuw; een regiobestand dat niet komt | 7 |
| Browser, kaartje (375 en 320 pixels): geen tekst over een andere, geen ringlabel achter een stip, alles binnen het kaartje | 1 |

In de browsertest wordt niet gewacht: de klok van de pagina wordt vooruitgezet en de bestanden worden
afgespeeld, zodat de tweede keer ophalen iets nieuws brengt.

Ook gedraaid: de 54 browsertests tegen een kopie van de site met de vijf gegevensbestanden van de live
site van 12:28 uur. Alle 54 geslaagd.

## Bekeken op schermafbeeldingen

Het kaartje op 375 pixels, voor en na, met de gegevens van de live site. De afbeeldingen zijn in de
sessie gemaakt en aan Wim gestuurd; ze staan niet in de repo.

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| Op een echte iPhone | Niet te doen vanuit deze container. Getest in Chromium op 375 en 320 pixels. Safari kan een tekst iets breder of smaller tekenen dan Chromium; de schatting is daarom ruim genomen |
| Of iOS het terugkeren meldt zoals Chromium | Niet getest. De app luistert naar twee seinen (`visibilitychange` en `pageshow`); een app op het beginscherm van een iPhone geeft het eerste bij het naar voren halen. Dat is de bekende werking, niet door mij gemeten |
| De plek op de pagina | Niet getest. Een verversing zet de pagina niet naar boven, maar de lijst wordt opnieuw opgebouwd; komt er boven de plek waar je leest een bericht bij, dan verschuift wat je ziet |
| De gekozen lijst, "toon alles" en de afstand na een verversing | Niet apart getest; zie de tabel bij onderdeel 1 |
| Op GitHub | De pull request start geen run. De eerste run na het samenvoegen draait de nieuwe tests vóór het publiceren en tegen de live site |
| Een dag met heel veel stippen op één ring | Dan kan een ringlabel geen vrije plek vinden. De logica is daarop getest; op de live site is het niet voorgekomen |
| Het kaartje bij andere schermbreedtes dan 320 en 375 | Niet gemeten. De plaatsing wordt uitgerekend in kilometers en schaalt mee; alleen de verhouding tussen tekst en kaart is op die twee breedtes gecontroleerd |
| De plaats van Hilvarenbeek op het kaartje | Zie "Gemaakte keuzes"; niet gewijzigd |

## Buiten dit verslag

- **Niet samengevoegd:** de pull request met de twee verbeteringen blijft open tot Wim het zegt.
- **PR 20 is samengevoegd**, met akkoord van Wim; alleen `docs/`.
- **De workflow en het schema zijn niet gewijzigd.** `cache/ophaalcache.json` is niet gecommit en
  niets is geforceerd.
- **De bronnen zijn niet belast.** De live site is twee keer gelezen (vijf bestanden).
- **Geen subsessie**, en niets met ElevenLabs.
