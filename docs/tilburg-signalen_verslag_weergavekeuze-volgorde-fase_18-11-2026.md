# Tilburg Signalen: verslag weergavekeuze, volgorde bij gelijke score en fasefilter

| | |
|---|---|
| Datum | 18-11-2026, 13:39 – 14:00 uur |
| Versie | versie 2 van de app met de regio's, branch `claude/optimistic-gauss-sb0xpy`, opnieuw gestart vanaf `main` op commit `382539a` (na PR 22) |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen`; Chromium via Playwright |
| Brondata | Geen opvraging bij de bronnen. Voor de telling en de controle: de gegevens van de live site, bijgewerkt 18-11-2026, 13:07 uur, opgehaald om 13:56 uur |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_ondertitel-en-ranglijst_18-11-2026.md` (daarin staat run 31) |

## Stand

**`main` is rood.** PR 22 is samengevoegd op verzoek van Wim (13:39 uur), maar run 31 strandde in de
browsertests vóór het publiceren, op een test van mij. Er is niets gepubliceerd. De oorzaak en het
herstel staan in het vorige verslag, onder "Run 31 op GitHub". Het herstel is nog **niet
samengevoegd**.

De drie nieuwe onderdelen zijn gebouwd en staan op de werkbranch. **Ze zitten in dezelfde pull request
als het herstel (PR 23)**, als eigen commits erna: ik mag alleen naar deze ene werkbranch pushen, en
het herstel stond daar al. De pull request blijft open en is niet samengevoegd.

## Correcties en aanvullingen op eerdere verslagen

| Tijdstip | Wat |
|---|---|
| 18-11-2026, 14:00 uur | **De indeling van de fasen in drie treden komt van mij en niet uit de bron.** De bronnen noemen alleen de fase zelf ("Aanvraag", "Vastgesteld"); dat een aanvraag "vroeg" is en een vastgesteld plan "laat", heb ik zo ingedeeld en Wim heeft die indeling overgenomen. |
| 18-11-2026, 14:00 uur | **In de kern wisselen 5 van de 83 locaties van plaats door de nieuwe volgorde bij gelijke score, niet 40.** De 40 uit het voorstel gold voor een andere regel: daar telde ook de fase mee. Wim koos voor alleen het aantal woningen en dan het nieuwste bericht. |
| 18-11-2026, 14:00 uur | **De knop "Alleen de kern" op het tabblad Berichten doet iets anders dan voorheen.** Hij zette de regio's uit; nu laat hij alleen de kern zien en blijven de regio's gekozen, zodat je terug kunt naar "Samen". Een regio uitzetten doe je op het tabblad Gebied, waar je haar ook aanzet. |
| 18-11-2026, 14:00 uur | **De aparte pull request waar Wim om vroeg, is er niet gekomen:** de drie onderdelen staan samen met het herstel van run 31 in PR 23. Zie "Stand". |
| 18-11-2026, 14:00 uur | **Het aantal tests is 430 (was 410).** Er zijn er 20 bij: 15 voor de logica en 5 in de browser. |

## Opdracht

1. Een keuze op het tabblad Berichten: "Samen", "Alleen de kern" en per gekozen regio "Alleen …", met
   "Samen" als standaard. Het ochtendscherm blijft de kern.
2. Bij gelijke score: eerst het grootste aantal woningen, dan het nieuwste bericht. De fase en de
   locatie tellen niet mee in de volgorde, en de scores zelf blijven ongewijzigd.
3. Een filter op fase met drie treden: vroeg (voornemen, aanvraag), midden (ontwerp, bekendmaking,
   besluit), laat (vastgesteld, verleend, herstelbesluit).

In een nieuwe pull request die open blijft. Melden hoeveel locaties in de kern van plaats wisselen.

## 1. De keuze van wat de lijsten tonen

Met een regio gekozen staat op het tabblad Berichten, onder de tegels, de regel "Met Zeeland erbij."
met daaronder de keuze.

| Keuze | Wat de lijsten tonen | Regel onder de naam van de app |
|---|---|---|
| Samen (standaard) | De kern en de gekozen regio's door elkaar, zoals tot nu toe | Kern en Zeeland |
| Alleen de kern | Alleen de kern; de regio blijft gekozen | Alleen de kern |
| Alleen Zeeland | Alleen die regio | Alleen Zeeland |

| Onderdeel | Hoe het werkt |
|---|---|
| De tegels Ranglijst en Onzeker | Tellen wat de lijsten tonen |
| De rang | Telt binnen wat je ziet: in "Alleen Zeeland" is nummer 1 de hoogste van Zeeland |
| De ochtendregel ("3 ontwikkellocaties op de laatste publicatiedag") | Blijft over de kern gaan, bij elke keuze |
| De tegel Nieuw | Telt wat nieuw is in de lijsten. "Nieuw" bestaat alleen voor de kern, dus bij "Alleen Zeeland" staat er 0 |
| De zoekopdracht en de filters | Blijven staan als je van keuze wisselt |
| Het tabblad Gebied | Verandert niet door de keuze: de regio blijft daar gekozen |
| Een andere regio aan- of uitzetten | De keuze springt terug naar "Samen" |
| Een verversing bij terugkeer in de app | De keuze blijft staan |
| De melding dat een regio teksten mist | Staat er alleen als die regio in de lijsten zit |
| Bij een volgend bezoek | De app opent op de kern, zoals altijd |

## 2. De volgorde bij gelijke score

De regel staat op één plek, `site/logic.js`: hoogste score eerst; bij gelijke score het bericht met de
meeste woningen; dan het nieuwste; dan het dichtstbijzijnde. Een bericht zonder aantal woningen telt
als nul. De fase en het soort locatie spelen geen rol. De scores komen ongewijzigd uit de run;
`signalen/relevantie.py` is niet aangeraakt.

**Hoeveel locaties in de kern van plaats wisselen** (gegevens van de live site, 18-11-2026, 13:07 uur):

| Lijst in de kern | Aantal | Van plaats gewisseld | Waar | Top 10 |
|---|---:|---:|---|---|
| Ontwikkellocaties | 83 | **5** | De plaatsen 19 tot en met 23, alle met score 95; niemand verschuift meer dan twee plaatsen | Ongewijzigd |
| Onzeker | 25 | 0 | | Ongewijzigd |

| Was | Wordt | Woningen | Datum | Bericht |
|---:|---:|---:|---|---|
| 20 | 19 | 98 | 11-11-2026 | Loon op Zand, rectificatie aanvraag 19 grondgebonden woningen |
| 22 | 20 | 98 | 28-10-2026 | Loon op Zand, aanvraag 19 grondgebonden woningen |
| 19 | 21 | 57 | 18-11-2026 | Loon op Zand, toestemming voor 27 eengezinswoningen en 30 appartementen |
| 23 | 22 | 24 | 16-10-2026 | Tilburg, Den Bogerd |
| 21 | 23 | 23 | 10-11-2026 | Goirle, Dorpsstraat 47 |

Met Zeeland erbij staat het vastgestelde plan Bellinistraat (141 woningen) nu op 1 en het voornemen in
Tholen (100 woningen) op 2. Beide houden score 108.

In de momentopname in de repo (16-11-2026) wisselen 3 van de 81 locaties van plaats, ook rond plaats 20;
de video en zijn tests zijn daardoor niet geraakt.

## 3. Het filter Fase

Het bestaande filter "Stand" heet nu "Fase" en heeft twee groepen in één keuzelijst: eerst de drie
treden, daaronder elke stand apart, zoals voorheen. Zo staan er geen twee filters die elkaar kunnen
tegenspreken.

| Trede | Standen | In de kern nu (ontwikkellocaties en onzeker samen: 108) | Ontwikkellocaties (83) |
|---|---|---:|---:|
| Vroeg | Voornemen, Aanvraag | 27 | 24 |
| Midden | Ontwerp, Bekendmaking, Besluit | 26 | 22 |
| Laat | Vastgesteld, Verleend, Herstelbesluit | 36 | 27 |
| In geen trede | Beslistermijn verlengd (8), Voornemen tot verkoop (5), Onherroepelijk (3), Ontwerpbesluit (1), Geweigerd (1), Surseance verleend (1) | 19 | 10 |

**De indeling is van mij, niet van de bron** (zie de correctie bovenaan). Ik heb precies de acht standen
ingedeeld die Wim noemde. Wat in geen trede valt, vind je met een trede dus niet; die standen staan wel
los in de lijst eronder. In de keuzelijst staat bij elke trede welke standen erin zitten, bijvoorbeeld
"Laat: vastgesteld, verleend, herstelbesluit (36)".

## Gemaakte keuzes

| Keuze | Waarom |
|---|---|
| "Alleen de kern" laat de regio's gekozen | Anders kun je niet met één tik terug naar "Samen" of naar de regio. Zie de correctie bovenaan |
| De regel onder de naam volgt de keuze | Ze zegt wat je nu ziet: "Alleen Zeeland" in plaats van "Kern en Zeeland" |
| De rang telt binnen wat je ziet | Zoals voorgesteld. Het nummer van een bericht is daardoor in "Samen" anders dan in "Alleen Zeeland" |
| Eén keuzelijst voor de fase, niet twee | Een trede en een losse stand tegelijk kiezen zou een lege lijst kunnen geven zonder dat je ziet waarom |
| Alleen de acht genoemde standen in een trede | Zo is het afgesproken. "Ontwerpbesluit" bij midden en "Onherroepelijk" bij laat liggen voor de hand, maar dat is een nieuw besluit |
| De namen van de regio's in de regel "Met … erbij" staan nu in de volgorde van de knoppen | Gelijk aan de regel onder de naam van de app |
| Een fout bij het openen van de app komt nu in de console van de browser | Tijdens het bouwen bleef de pagina leeg zonder dat iets zei waarom; de tests letten op die console |

## Tests

430 tests geslaagd in de container (was 410; 10 overgeslagen: 6 van de film, 4 die alleen op verzoek
tegen de echte bronnen draaien).

| Wat | Aantal |
|---|---:|
| Logica, volgorde: een hogere score wint altijd; bij gelijke score de meeste woningen (met het geval Bellinistraat en Tholen); dan het nieuwste en het dichtstbijzijnde; geen aantal telt als nul; de fase en de locatie spelen geen rol; de rangnummers volgen en geen score verandert | 6 |
| Logica, fase: de drie treden zijn deze acht standen; een stand daarbuiten hoort bij geen trede; het filter neemt een trede of één stand; de keuzes tonen de treden altijd | 4 |
| Logica, weergave: zonder regio niets te kiezen; de keuzes; "Samen" als standaard en als terugval; elke keuze toont haar eigen berichten; de regel onder de naam volgt de keuze | 5 |
| Browser, 320 pixels, in beide situaties: de drie keuzes met tegels, telling, rang, regel onder de naam en ochtendregel; terug naar "Samen"; het tabblad Gebied blijft gelijk; een nieuwe regiokeuze begint bij "Samen" | 1 |
| Browser, in beide situaties: de kaarten staan in de nieuwe volgorde, in "Samen", "Alleen de regio" en "Alleen de kern" | 1 |
| Browser: het filter Fase heeft de twee groepen, de juiste aantallen per trede en de juiste kaarten; na wissen staat alles zoals bij het openen | 1 |
| Browser, vaste situatie: de keuzes en de tellingen staan er letterlijk; een zoekopdracht blijft staan bij het wisselen | 1 |
| Browser: een verversing bij terugkeer houdt de keuze "Alleen Zeeland" vast | 1 |

Bestaande tests zijn aangepast waar de pagina veranderd is: de regel "Met … erbij" zonder de oude knop,
terug naar de kern via het tabblad Gebied, en de melding van een regio die niet verschijnt bij "Alleen
de kern". De knoppen van de keuze worden op 320 pixels gecontroleerd op hoogte en op de rechterrand, ook
met drie regio's (vijf knoppen).

Ook gedraaid: de 63 browsertests tegen een kopie van de site met de gegevens van de live site van 13:07
uur. Alle 63 geslaagd.

## Bekeken op een schermafbeelding

Het tabblad Berichten op 320 pixels met de drie regio's gekozen en "Alleen Zeeland" aan: de vijf knoppen
staan op drie regels, niets loopt buiten beeld. In de sessie gemaakt; niet in de repo.

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| **`main` is rood tot het herstel is samengevoegd** | Zie "Stand". De geplande run van 16:10 uur ververst en publiceert wel, maar eindigt rood in de controle van de live site |
| Op GitHub | Niets hiervan heeft daar gedraaid. Na run 26 en run 31 zeg ik er nadrukkelijk bij: wat hier slaagt, is hier getest. De breedte van de knoppen hangt, net als de ondertitel, af van het lettertype; de test eist dat ze binnen 320 pixels blijven en niet op hoeveel regels ze staan |
| De ochtendregel en de tegel Nieuw zeggen bij "Alleen Zeeland" iets anders | De regel telt de kern ("3 ontwikkellocaties"), de tegel telt de lijst (0). Zo volgt het uit "het ochtendscherm blijft de kern"; het kan verwarren |
| Standen in geen trede | 19 van de 108 berichten in de kern. Voorstel, niet gedaan: "Ontwerpbesluit" bij midden, "Onherroepelijk" bij laat, "Voornemen tot verkoop" bij vroeg; "Beslistermijn verlengd", "Geweigerd" en "Surseance verleend" in geen trede laten |
| Een aantal woningen dat de app verkeerd leest | De volgorde bij gelijke score leunt nu op dat getal. Bij de aanvraag in Loon op Zand staat 98 woningen bij een titel over 19 grondgebonden woningen; of dat klopt met de tekst, heb ik niet nagegaan |
| Op een echte telefoon | Niet te doen vanuit deze container |
| De video | De droogloop slaagt; de video zelf is niet opnieuw opgenomen. De eerste plaatsen, die erin voorkomen, zijn niet veranderd |

## Buiten dit verslag

- **Niet samengevoegd:** PR 23 (herstel en de drie onderdelen) blijft open tot Wim het zegt.
- **De scores en `signalen/relevantie.py` zijn niet aangeraakt.** De workflow en het schema ook niet.
- **`cache/ophaalcache.json` is niet gecommit** en niets is geforceerd.
- **De bronnen zijn niet belast.** De live site is één keer gelezen (vijf bestanden).
- **De logs van run 31 zijn door een hulpsessie uitgelezen.** Niets met ElevenLabs.
