# Tilburg Signalen: verslag bouw eerste versie

| | |
|---|---|
| Datum | 16-11-2026 |
| Versie | eerste versie, branch `claude/dazzling-darwin-04no0e` |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | Live opgehaald op 16-11-2026 rond 10:10 uur; zie referentiewaarden |
| Van / aan | Claude Code aan Wim |
| Vervolg op | geen eerder verslag; de repo bevatte alleen een README |

## Correcties

| Tijdstip | Correctie |
|---|---|
| 16-11-2026, 10:15 uur | Onder "Buiten dit verslag" staat dat er naar de werkbranch is gepusht. Dat is niet gelukt: GitHub weigerde de push (403, de Claude GitHub-app heeft geen schrijftoegang tot de repo). Het werk is lokaal gecommit en als zip aan Wim overgedragen. De oorspronkelijke zin is blijven staan, met deze correctie erboven. |

## Wat er is gebouwd

Een mobiele webapp (installeerbaar op de telefoon) die berichten toont over omgevingsvergunningen
en wijzigingen in omgevingsplannen en bestemmingsplannen binnen 15 km van de Heuvel in Tilburg.
Bij elk bericht staan de bron (met link naar het origineel) en de afstand tot Tilburg-centrum.

De app heeft geen server of database. Een Python-script haalt de gegevens op en schrijft twee
JSON-bestanden; de app is een statische pagina die die bestanden leest. Een GitHub Actions-workflow
draait het script op werkdagen om 08:40/09:40, 12:10 en 16:10 uur en publiceert het resultaat op GitHub Pages.

## Bronnenonderzoek

### Aangesloten

| Bron | Wat het levert | Toegang |
|---|---|---|
| Officiële bekendmakingen (overheid.nl), zoekdienst `repository.overheid.nl/sru` | Gemeenteblad, Provinciaal blad, Waterschapsblad en Staatscourant; rubrieken "omgevingsvergunning" en "ruimtelijk plan of omgevingsdocument"; elk bericht met eigen coördinaten | Openbaar, geen sleutel |
| Omgevingsloket Vlaanderen (Mercator-kaartdienst, laag `lu:lu_omv_gd_v2`) | Vlaamse omgevingsvergunningen in het Belgische deel van de straal | Openbaar, geen sleutel |
| PDOK: BRK Bestuurlijke Gebieden, BAG-woonplaatsen, Locatieserver | Gemeente- en woonplaatsgrenzen; adres opzoeken als een bericht geen eigen locatie heeft | Openbaar, geen sleutel |
| Digitaal Vlaanderen: gemeentegrenzen (VRBG) | Bepalen welk Belgisch gebied binnen de straal valt | Openbaar, geen sleutel |

### Bestaat wel, niet aangesloten

| Bron | Waarom niet |
|---|---|
| Omgevingsloket "Regels op de kaart" (DSO, API Omgevingsdocumenten Presenteren) | Gegevens zijn openbaar, maar de koppeling vraagt een sleutel (gratis aan te vragen). Zonder sleutel geeft de dienst een 401. |
| Ruimtelijkeplannen.nl | De open koppelingen voor afnemers zijn per 1 juli 2024 beëindigd; de opvolger (Ruimtelijke Plannen API v4) vraagt ook een sleutel. |

Dat deze twee ontbreken kost geen meldingen: elke planwijziging wordt ook in het Gemeenteblad
bekendgemaakt en komt zo binnen. Wat ontbreekt is de inhoud van het plan zelf (regels, kaart).

## Gebied

Middelpunt: de Heuvel, Tilburg (RD 134459, 396511). Er liggen 17 gemeenten geheel of deels binnen
15 km: 16 Nederlandse en het Belgische Ravels (grensgebied bij Poppel). De volledige lijst met
plaatsen en afstanden staat in de app onder "Gebied" en in `site/data/gebied.json`.

| Gemeente | Dichtste punt | Verste punt | Binnen de straal |
|---|---|---|---|
| Tilburg | 0,0 km | 11,6 km | geheel |
| Hilvarenbeek | 2,3 km | 15,7 km | deels |
| Goirle | 2,4 km | 11,0 km | geheel |
| Oisterwijk | 3,2 km | 14,1 km | geheel |
| Loon op Zand | 5,5 km | 14,9 km | geheel |
| Gilze en Rijen | 7,9 km | 18,4 km | deels |
| Dongen | 8,2 km | 17,4 km | deels |
| Alphen-Chaam | 8,5 km | 24,3 km | deels |
| Ravels (België) | 8,7 km | 23,9 km | deels |
| Heusden | 8,8 km | 22,0 km | deels |
| Oirschot | 10,3 km | 22,9 km | deels |
| Vught | 10,3 km | 20,2 km | deels |
| Boxtel | 11,0 km | 21,8 km | deels |
| Waalwijk | 11,8 km | 21,7 km | deels |
| Baarle-Nassau | 12,3 km | 27,3 km | deels |
| Oosterhout | 12,9 km | 24,5 km | deels |
| Reusel-De Mierden | 14,3 km | 27,9 km | deels |

Net buiten de straal: Breda (15,2 km) en Baarle-Hertog (15,1 km).

## Gemaakte keuzes

| Keuze | Reden |
|---|---|
| Een bericht telt mee als de locatie zelf binnen 15 km valt, niet als de gemeente erbinnen valt | Anders komen bijvoorbeeld alle vergunningen uit Oosterhout-centrum mee |
| Afstand is hemelsbreed tot het dichtstbijzijnde punt van de locatie | Sluit aan bij "binnen 15 km" |
| Vergunningen blijven 42 dagen staan, planberichten 180 dagen | Bezwaartermijn is zes weken; planberichten zijn schaars (ongeveer 70 in een half jaar) |
| Bericht zonder eigen locatie: adres uit de titel opzoeken, anders "afstand geldt voor de gemeente" | Veel planberichten hebben alleen de gemeente als gebied; in de app staat steeds welke van de drie het is |
| Namen van aanvragers uit de Vlaamse bron worden niet opgehaald | Het veld bevat ook namen van particulieren |
| Geen server; statische app plus dagelijkse verversing via GitHub Actions | Geen hosting of kosten nodig, weinig dat stuk kan gaan |

## Referentiewaarden (run van 16-11-2026, 10:10 uur)

| Meting | Waarde |
|---|---|
| Berichten totaal | 1052 |
| waarvan vergunningen / plannen | 983 / 69 |
| uit officielebekendmakingen.nl / Omgevingsloket Vlaanderen | 1043 / 9 |
| per publicatie | Gemeenteblad 1000, Provinciaal blad 28, Staatscourant 9, Waterschapsblad 6 |
| locatie exact / uit titel afgeleid / alleen gemeente | 1001 / 9 / 42 |
| Laatste publicatiedag in de gegevens | vrijdag 13-11-2026 |
| Duur van een verversing | ongeveer 40 seconden |
| Unittests | 16, alle geslaagd |

## Getest

| Wat | Hoe | Uitkomst |
|---|---|---|
| Dataverwerking | 16 unittests zonder netwerk, plus meerdere volledige runs tegen de echte bronnen | Geslaagd |
| App op telefoonformaat | Chromium met Pixel 7-profiel, licht en donker: lijst, zoeken, filters, sorteren op afstand, tikken op een gemeente, "nieuw"-markering | Werkt, geen fouten in de console, geen horizontaal scrollen |
| Links naar de bron | Reservelink (repository.overheid.nl) geopend | Werkt |

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| De GitHub Actions-workflow | Draait pas vanaf de `main`-branch en nadat Pages is aangezet; vanuit deze sessie niet uit te voeren. Alleen de opmaak van het bestand is gecontroleerd. |
| Links naar zoek.officielebekendmakingen.nl | Die site gaf vanuit de cloudomgeving steeds een serverfout, ook voor de startpagina. Vermoeden: de site weert verkeer uit datacentra of had een storing. Daarom staat bij elk bericht ook een link "Alleen tekst" naar dezelfde bekendmaking in de open-datarepository; die werkt wel. Graag op de eigen telefoon controleren. |
| Publicaties van vandaag | Om 10:10 uur stond er landelijk nog geen enkele bekendmaking van 16-11-2026 in de zoekdienst, terwijl eerdere dagen rond 09:10 tot 09:20 uur binnenkwamen. Vermoeden: vertraging bij de bron vandaag. De workflow heeft daarom ook runs om 12:10 en 16:10 uur. |
| Installeren op het beginscherm | Kan pas getest worden als de app op een https-adres staat. |

## Buiten dit verslag

- **Livegang ligt bij Wim.** Er is alleen naar de werkbranch gepusht. Nodig: samenvoegen met `main`, en in GitHub bij Settings → Pages als bron "GitHub Actions" kiezen. Stappen staan in de README.
- **Geen meldingen op de telefoon.** De app laat bij het openen zien wat nieuw is sinds het vorige bezoek; echte pushmeldingen vragen een server en zijn bewust niet gebouwd.
- **GitHub zet geplande workflows uit na 60 dagen zonder activiteit in de repo.** GitHub stuurt daar vooraf een mail over; één klik zet ze weer aan.
- **DSO-sleutel niet aangevraagd.** Met een sleutel kan later de inhoud van planwijzigingen worden toegevoegd. Aanvragen kan alleen Wim zelf.
- **Bewust niet gedaan:** raadsstukken, uitspraken van de Raad van State en Vlaamse ruimtelijke uitvoeringsplannen. Die vielen buiten de vraag.
