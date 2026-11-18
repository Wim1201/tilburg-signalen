# Tilburg Signalen: verslag ondertitel en inleiding die meebewegen, en de ranglijst bij een regio

| | |
|---|---|
| Datum | 18-11-2026, 13:05 – 13:16 uur |
| Versie | versie 2 van de app met de regio's, branch `claude/optimistic-gauss-sb0xpy`, opnieuw gestart vanaf `main` op commit `37f8183` (na PR 21) |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen`; Chromium via Playwright |
| Brondata | Geen opvraging bij de bronnen. Voor de uitleg van de ranglijst: de gegevens van de live site van 18-11-2026, 13:07 uur |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_verversen-en-kaartje_18-11-2026.md` |

## Stand

PR 21 is samengevoegd op verzoek van Wim (13:05 uur, merge-commit `37f8183`). Run 30, de run die
daarop volgde, is groen, ook de controle van de live site.

Punt 1 (ondertitel en inleiding bewegen mee) is gebouwd en staat op de werkbranch, in een pull request
die **open blijft en niet is samengevoegd**. Punt 2 is een uitleg met een voorstel, in
`tilburg-signalen_voorstel_ranglijst-met-regio_18-11-2026.md`; **daarvan is niets gebouwd**.

## Correcties en aanvullingen op eerdere verslagen

| Tijdstip | Wat |
|---|---|
| 18-11-2026, 13:16 uur | **PR 21 is samengevoegd en heeft op GitHub gedraaid; "open blijft en niet is samengevoegd" en "Op GitHub: de pull request start geen run" in het vorige verslag zijn daarmee achterhaald.** Zie "Run 30 op GitHub". |
| 18-11-2026, 13:16 uur | **Het aantal tests is 409 (was 402).** Er zijn er 7 bij: 4 voor de logica en 3 in de browser. |
| 18-11-2026, 13:16 uur | **De kop is op de smalste telefoons iets compacter gemaakt; dat stond niet in de opdracht.** Met "Kern: " ervoor liep de ondertitel op 320 pixels over drie regels. Tot 350 pixels breed is het beeldmerk daarom 34 in plaats van 38 pixels en is de ruimte ernaast iets kleiner. Zie "Gemaakte keuzes". |

## Run 30 op GitHub, na het samenvoegen van PR 21 (18-11-2026, 13:05 – 13:09 uur)

| Stap | Duur | Verzoeken | Weigeringen (HTTP 429) | Uitkomst |
|---|---:|---:|---:|---|
| Tests | 17 s | geen | | 402 tests geslaagd; 68 overgeslagen, omdat de browser in die stap nog niet klaarstaat |
| Browser klaarzetten | 35 s | | | Geslaagd |
| **Browsertests** | 46 s | geen naar de bronnen | | **57 tests geslaagd** (was 49): de acht nieuwe draaien mee |
| Gebied bijwerken | 14 s | 29 | 0 | Geslaagd |
| Berichten ophalen | 52 s | 38 | 0 | Geslaagd, zonder waarschuwing; niets mislukt in de eerste ronde |
| Cache bewaren | minder dan 1 s | | | "Cache ongewijzigd": er was niets nieuws |
| Publiceren | 9 s | | | Geslaagd |
| **Controle van de live site** | 29 s | | | **54 tests geslaagd** (was 46) |
| **Hele run** | **4 min 6 s** | **67** | **0** | **Groen** |

| Wat | Waarde |
|---|---|
| Berichten | 3.888, waarvan 1.140 in de kern; alle teksten uit de cache |
| Wachtende regioberichten | Geen |
| Cache | 963 kB, 64 procent van 1,5 MB, ongewijzigd |
| Dit is de eerste gewone run met de regio's gevuld | 38 verzoeken in 52 seconden. Vóór de regio's deed een gewone run rond de 34 verzoeken |

De nieuwe app staat daarmee live: het opnieuw ophalen bij terugkeer en het kaartje zonder overlap.

## Opdracht

1. De ondertitel in de kop en de inleiding op het tabblad Gebied beschrijven alleen de kern. Laat ze
   meebewegen: standaard "Kern: binnen 15 km van De Heuvel, Tilburg-centrum", met een gekozen regio
   bijvoorbeeld "Kern en Zeeland". De naam Tilburg Signalen blijft. Met tests, ook op 320 pixels.
2. Leg uit waarom het voornemen in Tholen boven het vastgestelde plan Bellinistraat staat, en doe een
   voorstel voor de ranglijst bij een gekozen regio. Nog niet bouwen.

## 1. De ondertitel en de inleiding

| Keuze in de app | Ondertitel in de kop | Inleiding op het tabblad Gebied |
|---|---|---|
| Alleen de kern | Kern: binnen 15 km van De Heuvel, Tilburg-centrum | Kern: alles binnen 15 km hemelsbreed van De Heuvel, Tilburg-centrum. Daarin liggen 17 gemeenten, waarvan de meeste maar voor een deel. Een bericht telt mee als de locatie zelf binnen de straal valt. |
| Zeeland erbij | Kern en Zeeland | Kern en Zeeland. De kern is alles binnen 15 km hemelsbreed van De Heuvel, Tilburg-centrum: 17 gemeenten, waarvan de meeste maar voor een deel. Van Zeeland telt elke gemeente in haar geheel mee. Samen staan er nu 30 gemeenten op de lijst. |
| Alle drie erbij | Kern, Midden-Brabant, West-Brabant en Zeeland | Kern, Midden-Brabant, West-Brabant en Zeeland. De kern is ... Van de gekozen regio's telt elke gemeente in haar geheel mee. Samen staan er nu 43 gemeenten op de lijst. |

De ondertitel staat op elk tabblad en verandert zodra je een regio kiest of terugzet, ook via "Alleen
de kern" op het tabblad Berichten. De naam Tilburg Signalen is niet gewijzigd.

Gemeten in Chromium:

| Breedte | Alleen de kern | Zeeland erbij | Alle drie erbij |
|---|---|---|---|
| 320 pixels | 2 regels | 1 regel | 2 regels |
| 375 pixels | 2 regels | 1 regel | 2 regels |

Niets loopt buiten het scherm en de ondertitel raakt het tijdstip rechts niet.

## 2. De ranglijst bij een gekozen regio

Kort: de twee plannen hebben dezelfde score (108), en bij een gelijke score gaat het nieuwste bericht
voor. De score van een plan stopt met oplopen bij 80 woningen, en de fase, de locatie en de afstand
tellen niet mee. De volledige uitleg, de meting en het voorstel staan in
`tilburg-signalen_voorstel_ranglijst-met-regio_18-11-2026.md`.

Het advies daarin, in twee losse onderdelen:

| Onderdeel | Advies |
|---|---|
| Gemengd of alleen deze regio | Een keuze op het tabblad Berichten: "Samen", "Alleen Zeeland", "Alleen de kern"; standaard "Samen" |
| De volgorde die de aanleiding was | Bij gelijke score eerst het plan dat het verst is, dan het grootste aantal woningen, dan het nieuwste. Dit raakt ook de kern en vraagt een besluit over de volgorde van de fasen |

Het eerste lost het tweede niet op: ook in een lijst met alleen Zeeland staat Tholen bovenaan.

## Gemaakte keuzes

| Keuze | Waarom |
|---|---|
| Met een regio erbij alleen de namen in de ondertitel, zonder de straal | Zoals het voorbeeld in de opdracht ("Kern en Zeeland"), en het blijft kort |
| De namen in de volgorde van de knoppen, niet in de volgorde van kiezen | Anders staat er de ene keer "Kern, Zeeland en West-Brabant" en de andere keer andersom |
| De kop iets compacter tot 350 pixels breed | Zie de correctie bovenaan. Zonder dat stond er op 320 pixels "Kern: binnen 15 km van / De Heuvel, Tilburg- / centrum" |
| De regel "Met Zeeland erbij" op het tabblad Berichten blijft | Daar zit de knop "Alleen de kern" aan vast. De ondertitel zegt nu hetzelfde, korter |
| De hint onder de regioknoppen blijft | Die zegt wat de keuze doet; de inleiding zegt wat je ziet |

## Tests

409 tests geslaagd in de container (was 402; 10 overgeslagen: 6 van de film, 4 die alleen op verzoek
tegen de echte bronnen draaien).

| Wat | Aantal |
|---|---:|
| Logica: de ondertitel zonder regio, met één, twee en drie regio's; de inleiding zonder en met regio's | 4 |
| Browser, 320 pixels: de ondertitel volgt de keuze op beide tabbladen, in de volgorde van de knoppen, ook na terugzetten en opnieuw openen; hoogstens twee regels; raakt het tijdstip niet; de naam blijft Tilburg Signalen | 1 |
| Browser, 320 pixels: de inleiding volgt de keuze, met de aantallen gemeenten die op de lijst staan | 1 |
| Browser: in de vaste situatie staan de regels er letterlijk zoals hier beschreven | 1 |

De twee eerste browsertests draaien in beide situaties: met de regio's zoals de site ze levert en in
de vaste situatie. De test van het opnieuw ophalen controleert nu ook dat de ondertitel "Kern en
Zeeland" blijft na een verversing.

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| Op een echte telefoon | Niet te doen vanuit deze container; gemeten in Chromium op 320 en 375 pixels |
| De kop wordt lager of hoger bij het kiezen van een regio | Van twee regels naar één ("Kern en Zeeland") scheelt 13 tot 15 pixels; de pagina eronder schuift dan mee. Niet opgelost |
| Een regio met een langere naam | De drie namen van nu passen op twee regels. Een vierde regio of een langere naam is niet geprobeerd |
| Het breekpunt "Tilburg-/centrum" | Op 320 en 375 pixels breekt de ondertitel niet meer in die naam; bij andere breedtes is het niet gemeten |
| Op GitHub | De pull request start geen run. De eerste run na het samenvoegen draait de nieuwe tests |
| Het voorstel voor de ranglijst | Niet gebouwd; wacht op jouw keuze per onderdeel |
| Het opnieuw ophalen bij terugkeer op een echte iPhone | Staat nu live en is alleen in Chromium getest |

## Buiten dit verslag

- **Niet samengevoegd:** de nieuwe pull request blijft open tot Wim het zegt.
- **PR 21 is samengevoegd**, met akkoord van Wim.
- **De workflow en het schema zijn niet gewijzigd.** `cache/ophaalcache.json` is niet gecommit en
  niets is geforceerd.
- **De regels van de ranglijst zijn niet aangeraakt.**
- **De bronnen zijn niet belast.** De live site is één keer gelezen (vier bestanden).
- **Geen subsessie voor het bouwen;** de logs van run 30 zijn door een hulpsessie uitgelezen. Niets
  met ElevenLabs.
