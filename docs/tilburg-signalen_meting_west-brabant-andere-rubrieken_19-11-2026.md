# Tilburg Signalen: meting regiobestand West-Brabant bij "andere beschikking"

| | |
|---|---|
| Datum | 19-11-2026, 17:20 – 17:55 uur |
| Versie | `main` op commit `78a816e`, branch `claude/peaceful-hopper-sfniv3`; niets gebouwd |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | live site (wim1201.github.io/tilburg-signalen), opgehaald 19-11-2026 rond 17:30 uur; officielebekendmakingen.nl, opgevraagd 19-11-2026 rond 17:35 en 17:45 uur |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_voorstel_andere-rubrieken_17-11-2026.md` |

**Dit is een meting. Er is niets gebouwd, en de cache en de databestanden zijn niet gewijzigd.**

## Besluiten van Wim (19-11-2026)

| Keuze | Besluit |
|---|---|
| Breedte | Variant A: gemeenten, rubrieken "andere beschikking" en "andere vergunning", "omgevingsvergunning" in de titel |
| De zeven berichten van Dongen die geen omgevingsvergunning zijn | a: zo laten, label "Vergunning", onder weggefilterd |
| Eenmalig "nieuw" | a: accepteren, maar in het verslag het exacte aantal noemen |
| Aan/uit per regio | Nog open: in de opdracht stond de keuze nog als sjabloon |
| Volgorde | Eerst deze meting, daarna bouwen met een vers venster |

## Welke grens

| Grens | Waar | Geldt voor West-Brabant? |
|---|---|---|
| 1.500.000 bytes per bestand in de repo | `tests/test_ververst.py` (alle bestanden in de repo) en `tests/test_regio.py` (de databestanden in de repo) | Alleen voor de **momentopname** `site/data/regio-west-brabant.json` in de repo. Die is 1.291.562 bytes en verandert alleen als iemand hem met de hand vernieuwt |
| Na het ophalen | Niets. `signalen/update.py` schrijft het bestand, de workflow publiceert het en zet alleen de cache terug in `main` | Nee |
| Vangnet 1,4 MB | `signalen/cache.py` | Alleen de cache, niet de databestanden |

Dit is gelezen uit de code en `.github/workflows/dagelijks.yml`; het is niet op GitHub uitgeprobeerd.

## Stand nu en wat er bijkomt

| | Bytes | Deel van 1,5 MB |
|---|---:|---:|
| `regio-west-brabant.json` live, 19-11-2026 | 1.358.825 | 90,6% |
| De berichten van variant A in West-Brabant (66: Roosendaal 61, Etten-Leur 5), ongeveer 970 bytes per bericht | 64.023 | |
| **Samen** | **1.422.848** | **94,9%** |
| **Ruimte over** | **77.152** | ongeveer 80 berichten |

Met gzip, zoals de telefoon het binnenkrijgt: nu 125 kB, met variant A naar schatting 131 kB.

## Over het jaar

Per week geteld bij de bron: berichten van de 12 West-Brabantse gemeenten in de twee rubrieken met
"omgevingsvergunning" in de titel, van 29-09-2025 tot en met 15-11-2026. 59 verzoeken (alleen het
aantal), geen weigering.

| Venster van 42 dagen | Extra berichten | Extra bytes (970 per bericht) |
|---|---:|---:|
| Laagste (begin september 2026) | 45 | 44 kB |
| Nu (oktober tot half november 2026) | 62 | 60 kB |
| Hoogste (november 2025) | 90 | 87 kB |
| Rond de drukke weken van West-Brabant (maart – april, juli) | 55 – 78 | 53 – 76 kB |

Het dekkingsverslag schatte West-Brabant op het hoogst op 1,46 MB (april en juli), met een marge van
ongeveer 5 procent. Met variant A erbij:

| Moment | Schatting |
|---|---:|
| April 2027 | 1,51 – 1,52 MB |
| Juli 2027 | 1,52 – 1,54 MB |
| Januari 2027 (rustig voor West-Brabant, druk voor deze rubrieken) | ongeveer 1,25 MB |

**West-Brabant komt daarmee in het voorjaar en de zomer waarschijnlijk boven 1,5 MB.** Zonder variant A
zat het er net onder.

## Wat er gebeurt als de grens bereikt wordt

| Waar | Gevolg |
|---|---|
| De verversing | Niets. Geen stap kijkt na het ophalen naar de grootte; het bestand wordt geschreven en gepubliceerd |
| De live site en de telefoon | Een groter bestand: rond 1,55 MB, met gzip ongeveer 145 kB. Op een iPhone niet gemeten |
| De repo | Alleen als iemand de momentopname vernieuwt met een bestand boven 1,5 MB: dan keurt de testrun van die pull request het af. Wordt het toch samengevoegd, dan strandt elke run in de stap "Tests", vóór het ophalen, en blijft de site op de laatste stand staan |

## De proef met een vers venster

Variant A uitgevoerd met de regels van de app en de cache van `main` (alleen gelezen, niet bewaard).
Venster 08-10-2026 tot en met 19-11-2026.

| | |
|---|---:|
| Gevonden bij de bron | 87 |
| In de kern of een regio | 85: andere beschikking 79, andere vergunning 6 |
| Al in de live data | 0 |
| Verzoeken | 12 (6 aan de bron, 6 aan PDOK), geen weigering, 85 seconden |
| Teksten nodig | 3 (82 van de 85 hebben een omschrijving); percelen 6 |

| Waar | Berichten | Ontwikkellocatie | Onzeker | Weggefilterd | Bytes |
|---|---:|---:|---:|---:|---:|
| Kern | 13 (Dongen 9) | 1: Dongen, 23 woningen, score 52 | 0 | 12 | 12.170 |
| Midden-Brabant | 1 (Dongen) | 0 | 0 | 1 | 933 |
| West-Brabant | 66 | 2: Roosendaal, score 87 en 77 | 1 | 63 | 64.023 |
| Zeeland | 5 | 3: Noord-Beveland, scores 46 tot 52 | 0 | 2 | 5.007 |

Ten opzichte van 17-11 is het venster elf dagen opgeschoven. Het beeld is hetzelfde.

## Cache

3 teksten en 6 percelen erbij: ongeveer 2 kB. De cache blijft rond 963 kB.

## Wat ik niet heb kunnen controleren

| Punt | Toelichting |
|---|---|
| De piek van 2027 | Een schatting: de basis (1,46 MB) is zelf een schatting uit één jaar, en de extra berichten zijn per week geteld, niet per bestand gemeten |
| Gedrag op een iPhone bij een bestand van 1,55 MB | Niet gemeten |
| Gzip op de live site | Gemeten met curl vanuit de container (125 kB); op de telefoon niet |
| GitHub | Niets gedraaid; de proef liep vanuit deze container |
