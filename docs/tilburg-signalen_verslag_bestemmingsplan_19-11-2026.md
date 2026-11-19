# Verslag: bestemmingsplan op het tabblad Adres (19-11-2026)

Stap 2, na het onderzoek in `tilburg-signalen_onderzoek_bestemmingsplan_19-11-2026.md`. Keuzes van Wim: 1a (rechtstreeks vanuit de app), 2b (bestemming met getallen, plus de namen van dubbelbestemmingen), 3a (zonder getal op de kaart: melden en linken naar de regels).

## Wat de app nu doet

Het vak "Bestemmingsplan en omgevingsplan" vraagt bij een gekozen adres één keer PDOK Ruimtelijke plannen (`service.pdok.nl/kadaster/plu/wms/v1_0`, GetFeatureInfo, platte tekst, geen sleutel) om vier lagen op het adrespunt: enkelbestemming, dubbelbestemming, maatvoering en bestemmingsplangebied.

Per vastgestelde bestemming: naam, plan, datum, status, de getallen op de plankaart, direct daaronder de waarschuwing en een link naar het artikel in de regels (alleen naar `ruimtelijkeplannen.nl`). Daarna de dubbelbestemmingen, wat niet getoond is en de bron. De link naar Regels op de kaart (Omgevingsloket) staat er altijd onder.

| Situatie | Wat het vak toont |
|---|---|
| Getallen op de kaart | De getallen, bijv. "Maximum bouwhoogte 40 m" |
| Geen getal op de kaart | "Geen getal op de kaart betekent niet: geen beperking." met link naar de regels |
| Twee of meer vastgestelde plannen op het punt | Alle plannen, nieuwste eerst, met de melding dat de app er geen uit kiest |
| Geen vastgesteld plan | "Op dit punt staat geen vastgesteld bestemmingsplan op de kaart" plus de waarschuwing |
| Geen antwoord, fout of tijdslimiet | Melding "antwoordt niet" en een knop Opnieuw proberen |
| 404 of 410 (dienst weg) | Melding "verplaatst of gestopt", knop, link naar Regels op de kaart |
| Antwoord in een onbekende vorm (foutmelding, webpagina, leeg) | Melding "antwoord dat de app niet kent", knop, link naar Regels op de kaart |

Waarschuwing: "Let op: wijzigingen sinds 1-1-2024 (Omgevingswet, omgevingsplan) ontbreken hier. Wat nu geldt, staat in Regels op de kaart van het Omgevingsloket."

## Statusfilter

Getoond worden alleen de planstatussen vastgesteld, onherroepelijk, vigerend, goedgekeurd en geconsolideerd. Elke andere status (ontwerp, voorontwerp, concept, leeg of onbekend) wordt weggelaten en geteld ("Niet getoond: ..."). Ook weggelaten: objecten met `historisch` = 1 en dossiers met status afgebroken, vernietigd of niet in werking.

## Tests

- `tests/test_adres.py`, klasse `Bestemmingsplan` (13 tests): het webadres, de echte antwoorden voor het testadres en het stadhuis, een voorbeeld van elke status, vervallen en historische plannen, overlap, de vormen van getallen, getallen van een ander plan, de tekst bij geen getal, de waarschuwing, alle foutsoorten, en de link naar de regels.
- `tests/test_site.py` (browser, 320 px): het vak met het nagespeelde antwoord, de volgorde getallen-waarschuwing, en drie storingen (geen verbinding met herstel via de knop, 404, webpagina in plaats van tekst).
- Geen test roept PDOK Ruimtelijke plannen echt aan. De antwoorden staan in `tests/js/adres_fixtures.json` (opgehaald op 19-11-2026). Ook de handmatige livetest (`adres_live.js`) speelt deze dienst na.
- Gedraaid in de cloud: `python -m unittest discover tests` (554 tests, groen) en de browsertests `InDeBrowser` en `Droogloop` (groen, ook na `python -m signalen.instellingen`, zoals op GitHub).

## Gewijzigde bestanden

`site/adres.js`, `site/adres-app.js`, `site/styles.css`, `site/sw.js` (cacheversie v15), `tests/test_adres.py`, `tests/test_site.py`, `tests/js/adres_smoke.js`, `tests/js/adres_live.js`, `tests/js/adres_fixtures.json`. Niet geraakt: `signalen/update.py`, workflows, cache, Workers.

## Controle van het onderzoeksdocument

`tilburg-signalen_onderzoek_bestemmingsplan_19-11-2026.md` noemt alleen Stadhuisplein 130 (zonder postcode). Geen andere adressen of postcodes; er is niets verwijderd. De steekproef van 80 adrespunten staat er alleen als tellingen in.

## Niet gecontroleerd

- Op een iPhone: weergave in Safari, afbreken van lange woorden (`-webkit-hyphens`), snelheid over mobiel internet, en of Safari de dienst zonder problemen rechtstreeks aanroept (CORS is alleen in Chromium getest).
- De handmatige livetest (`TILBURG_ADRES_LIVE=1`) is niet gedraaid; de nieuwe controle daarin (7 nagespeelde vragen) is dus niet uitgevoerd.
- Gemeenten buiten Tilburg, en plannen waarvan de getallen in een vorm staan die niet in de steekproef voorkwam.
- Hoe lang PDOK deze dienst nog aanbiedt.
