# Tilburg Signalen: verslag vergunningen onder een andere rubriek

| | |
|---|---|
| Datum | 19-11-2026, 18:00 – 18:45 uur |
| Versie | branch `claude/peaceful-hopper-sfniv3`, vanaf `main` op commit `78a816e`; niet samengevoegd |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | officielebekendmakingen.nl en PDOK, opgevraagd 19-11-2026 rond 18:25 uur; venster vergunningen 08-10-2026 tot en met 19-11-2026 |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_voorstel_andere-rubrieken_17-11-2026.md` en `tilburg-signalen_meting_west-brabant-andere-rubrieken_19-11-2026.md` |

## Opdracht en besluiten van Wim (19-11-2026)

| Keuze | Besluit |
|---|---|
| Breedte | Variant A: alleen gemeenten, rubrieken "andere beschikking" en "andere vergunning", "omgevingsvergunning" in de titel |
| Aan/uit | Een instelling per regio voor deze extra zoekvraag, standaard overal aan |
| Berichten van Dongen die geen omgevingsvergunning zijn | Zo laten: label "Vergunning", onder weggefilterd |
| Eenmalig "nieuw" | Accepteren; het exacte aantal staat hieronder |
| West-Brabant boven 1,5 MB | Accepteren, met een waarschuwing in het log van de verversing vanaf 90 procent; in de docs vastleggen wat er gebeurt bij het vernieuwen van de momentopname boven de grens |
| Oplevering | Eén pull request, met tests, niet samenvoegen |

## Wat er is gebouwd

| Bestand | Wat |
|---|---|
| `signalen/bekendmakingen.py` | Een extra zoekvraag per run, na de gewone: de gemeenten (niet de provincie en de waterschappen), de twee rubrieken, "omgevingsvergunning" in de titel, het venster van de vergunningen (42 dagen). Een bericht wordt een vergunning en gaat door dezelfde regels als alle andere. Een bericht dat al onder de gewone rubriek binnenkwam, blijft zoals het was |
| `config.json` | `andere_rubrieken`: per deel aan of uit (`kern`, `Midden-Brabant`, `West-Brabant`, `Zeeland`), alle vier `true`. Een deel dat er niet in staat, staat aan. Staat een deel uit, dan worden zijn gemeenten niet gevraagd en zijn berichten niet bewaard; staat alles uit, dan is er geen extra zoekvraag. De opmerking "Aanvragen ontbreken" bij Roosendaal is weg |
| `site/data/gebied.json` | Dezelfde opmerking uit de momentopname gehaald; de stap "Gebied bijwerken" schrijft dit bestand elke run opnieuw uit `config.json` |
| `signalen/update.py` | **Buiten het voorstel, op jouw verzoek:** na het schrijven een regel in het log met de grootte van elk databestand, en een waarschuwing (`::warning::`, zichtbaar in het overzicht van de run) voor elk bestand vanaf 1.350.000 bytes, 90 procent van 1,5 MB. Dat geldt voor de drie regiobestanden en ook voor `berichten.json`: daar geldt dezelfde grens |

De workflow, het schema en de cache zijn niet gewijzigd.

Een deel uitzetten: in `config.json` bijvoorbeeld `"West-Brabant": false`. Dat is een wijziging buiten
`docs/`, dus via een pull request; na het samenvoegen geldt het vanaf de run die daarop volgt.

## Tests

| | |
|---|---|
| Hele reeks | 537 tests, geslaagd (was 525). 10 overgeslagen: de tests tegen de echte bronnen die alleen op verzoek draaien, en de filmtests. Ook de browsertests in Chromium zijn gedraaid |
| Nieuw: extra rubrieken (8) | De zoekvraag; één extra zoekvraag, alleen voor gemeenten, zonder waterschap en zonder Ravels; een bericht uit zo'n rubriek wordt een vergunning met regio en stand; geen dubbeling en geen wijziging van een bericht dat al binnen was; met alles uit precies dezelfde berichten als zonder deze wijziging en geen extra zoekvraag; een deel uit wordt niet gevraagd en niet bewaard (ook de kern, waarbij het deel van Dongen buiten de straal blijft); een deel dat niet genoemd is, staat aan; de standen van de titels van Roosendaal |
| Nieuw: grootte van de bestanden (3) | Eén gewone regel onder 90 procent; vanaf 90 procent een waarschuwing per bestand; 90 procent is 1.350.000 bytes |
| Nieuw: instelling (1) | In `config.json` staan de kern en de drie regio's, alle aan |
| Aangepast (2) | "Roosendaal zegt waarom" is "geen gemeente heeft nog een opmerking" geworden; de test van de run kijkt ook naar de regel over de bestanden |

Geen test roept de bron, de energielabel-Worker of EP-Online aan; de zoekvragen zijn nagespeeld.

## Meting vóór en na

Twee runs na elkaar vanuit deze container met de cache van `main`, alleen gelezen. Eerst met alles
uit (gelijk aan de app van nu), daarna met alles aan. Niets is weggeschreven.

| | Vóór | Na |
|---|---:|---:|
| Berichten in totaal | 3.877 | 3.962 |
| Verzoeken | 22 | 32: 4 aan de bron (de zoekvraag en 3 teksten), 6 aan PDOK (adressen uit de titel, daarna in de cache) |
| Weigeringen (HTTP 429) | 0 | 0 |
| Bestaande berichten verdwenen of veranderd | | **0** |
| Ranglijst van de kern | 86 | 87; het bericht van Dongen komt op rang 60; de top 10 is gelijk |

Een gewone run daarna kost 1 verzoek extra (de zoekvraag), plus een tekst of adres voor een nieuw bericht.

| Erbij | Ontwikkellocatie | Onzeker | Weggefilterd | Samen |
|---|---:|---:|---:|---:|
| Kern | 1 (Dongen, 23 woningen, Europaplein) | 0 | 12 | 13 |
| Midden-Brabant | 0 | 0 | 1 | 1 |
| West-Brabant | 2 (Roosendaal) | 1 | 63 | 66 |
| Zeeland | 3 (Noord-Beveland) | 0 | 2 | 5 |
| **Samen** | **6** | **1** | **78** | **85** |

## Hoeveel de eerste run als nieuw telt

De app houdt per toestel bij welk bericht het al gezien heeft, alleen voor de kern. Bij het eerste
bezoek na de eerste run met deze wijziging (gemeten met het venster van vandaag):

| | Aantal |
|---|---:|
| Berichten van de kern die als nieuw gemarkeerd worden | **13**, ook de 10 die al 3 tot 6 weken oud zijn |
| Daarvan in de tegel Nieuw en in de ochtendzin ("1 nieuwe ontwikkellocatie sinds je vorige bezoek") | **1**: Dongen, van 27-10 |
| Daarvan als nieuw onder Onzeker | 0 |
| Daarvan alleen te zien met de schakelaar weggefilterd | 12 |
| Regio's | 0: "nieuw" geldt niet voor de regio's |

Wordt er later samengevoegd, dan schuift het venster op. Het bericht van Dongen staat er tot en met
08-12-2026 in; daarna telt de eerste run 0 nieuwe ontwikkellocaties extra.

## Grootte van de bestanden

| Bestand | Vóór | Na | Deel van 1,5 MB, na |
|---|---:|---:|---:|
| `berichten.json` (kern) | 1.036.582 | 1.048.752 | 69% |
| `regio-midden-brabant.json` | 179.328 | 180.261 | 12% |
| `regio-west-brabant.json` | 1.358.825 | 1.422.848 | **94%: waarschuwing** |
| `regio-zeeland.json` | 1.016.620 | 1.021.627 | 68% |
| Cache | 963 kB | ongeveer 965 kB | 64% |

West-Brabant met gzip: van 121 naar 127 kB, hier nagerekend. Vanaf de eerste run na het samenvoegen
toont **elke** run een waarschuwing voor `regio-west-brabant.json`; volgens de schatting uit de meting
blijft dat zo tot de rustige weken rond de jaarwisseling, en komt het bestand in april en juli 2027
op 1,51 tot 1,54 MB. Dat is volgens de afspraak geen reden om in te grijpen.

## Wat er gebeurt bij het vernieuwen van de momentopname boven de grens

In de repo staat een momentopname van de databestanden (`site/data/*.json`), van 16 en 17-11-2026.
De tests en de browsertests gebruiken die; de verversing schrijft hem op GitHub wel, maar zet hem
nooit terug in de repo. Alleen de cache gaat terug in `main`.

| Stap | Wat er gebeurt |
|---|---|
| Iemand vernieuwt de momentopname met een bestand boven 1.500.000 bytes en maakt een pull request | De testrun van die pull request (`tests.yml`) wordt rood: `tests/test_ververst.py` (geen bestand boven 1,5 MB in de repo) en `tests/test_regio.py` (elk databestand kleiner dan 1,5 MB) keuren hem af |
| Die pull request wordt toch samengevoegd | De verversing die daarop start, en elke run daarna, strandt in de eerste stap "Tests", vóór het ophalen. Er wordt niet ververst en niets gepubliceerd; de live site blijft op de laatste stand staan. Je ziet het aan een rood kruis in Actions |
| Herstel | Het bestand in de repo kleiner maken (de oude momentopname terugzetten, of een momentopname uit een rustige week nemen) en dat samenvoegen. De volgende run is dan weer gewoon |
| Niet aangeraden | De grens in de test verhogen. Dat verschuift het probleem (voorstel E van 18-11-2026) |

Kortom: **vernieuw de momentopname alleen met bestanden onder 1,5 MB.** Kan dat voor West-Brabant
niet meer, dan is splitsen (voorstel C van 17-11) de uitweg, of de oude momentopname laten staan.

## Wat ik niet heb kunnen controleren

| Punt | Toelichting |
|---|---|
| GitHub | Niets op GitHub gedraaid. De testrun op de pull request volgt bij het openen; de controle van de live site draait pas na het samenvoegen |
| De waarschuwing in het overzicht van de run | Getest dat de regel `::warning::` begint; niet gezien hoe GitHub hem toont |
| Op een iPhone | Niet getest. De app zelf is niet veranderd; er staan alleen meer berichten in |
| Of 42 dagen representatief is | Eén venster; de jaartelling voor West-Brabant staat in de meting |
| Berichten zonder het woord "omgevingsvergunning" in de titel | Niet gezocht, zoals in het voorstel |

## Samenvoegen

Niet samengevoegd. Raakt `config.json` en code, dus het samenvoegen start een verversing. Niet vlak
voor of tijdens een slot (werkdagen 06:45, 09:35, 10:20, 16:10; dagelijks 12:10; zondag 04:30). Wacht
na het samenvoegen de run af: pas daar draaien de controle van de live site en de eerste echte
waarschuwing.
