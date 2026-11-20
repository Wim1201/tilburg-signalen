# Tilburg Signalen: verslag proefadressen vervangen

| | |
|---|---|
| Datum | 20-11-2026 |
| Versie | branch `claude/proefadressen`, vanaf `main` op commit `6e3e390` (na PR #36); niet samengevoegd |
| Omgeving | Claude Code in de cloud (tijdelijke container) |
| Brondata | PDOK Locatieserver, BAG en kadastrale kaart, opgevraagd 20-11-2026 voor de nieuwe proefadressen; overheid.nl (organisaties) voor de bezoekadressen |
| Van / aan | Claude Code aan Wim |
| Vervolg op | het onderzoek naar geheimen en adressen van 20-11-2026 (niet in de repo) |

## Opdracht

De vijf proefadressen van de livetest stonden met postcode in `tests/` en `docs/`. Het ging om
woningen in Dongen en Goirle, een appartement in Tilburg en panden in Middelburg en Breda. Ze moesten
overal in de huidige bestanden worden vervangen: door openbare gebouwen, of in unit-tests door
verzonnen adressen. De geschiedenis is niet herschreven en de adressen uit echte bekendmakingen zijn
niet aangeraakt.

## Wat er nu staat

| Waar | Oud | Nieuw |
|---|---|---|
| Livetest (`tests/js/adres_live.js`, `tests/test_adres.py`, klasse `EchteBronnen`) | Woning in Dongen | Gemeentehuis Dongen |
| | Twee woningen in Goirle (met en zonder huisletter) | Gemeentehuis Goirle; de huisletter nu in het stadskantoor van Breda |
| | Appartement in Tilburg (toevoeging) | Een klein object met toevoeging op het gemeentehuis van Dongen ("NU01") |
| | Pand in Middelburg | Stadskantoor Middelburg |
| | Kantoor in Breda | Stadskantoor Breda |
| Browsertest met nagespeelde bronnen (`tests/js/adres_fixtures.json`, `adres_smoke.js`, `tests/test_site.py`) | Pand in Middelburg | Stadskantoor Middelburg: echte antwoorden van PDOK van 20-11-2026, ingekort |
| Unit-tests (`tests/test_adres.py`, `tests/test_regio.py`) | De vijf adressen, hun postcodes en hun coördinaten | Verzonnen: Teststraat en Lage Teststraat in Teststad, postcodes 9999 ZX, ZY en ZZ, coördinaten buiten bebouwing; het punt in Middelburg is het stadskantoor |
| Verslagen (`..._tabblad-adres_17-11-2026.md`, `..._dekking-en-regios_17-11-2026.md`) | Adressen, postcodes en perceelnummers | Een omschrijving ("woning A in Dongen"), met een regel "Aangepast" bovenaan. De uitkomsten van toen blijven kloppen; daarom geen ander adres ingevuld |
| `CLAUDE.md` | | Afspraak: alleen het testadres en openbare gebouwen als proefadres, in unit-tests Teststraat met 9999 |

### Wat de livetest nu anders doet

| Punt | Was | Nu |
|---|---|---|
| Huisletter | Twee woningen op één nummer met elk een eigen perceel | De huisletter in het stadskantoor van Breda is een eigen adresobject met een eigen oppervlakte, op hetzelfde perceel als het hoofdnummer. Dat een huisletter een eigen perceel kan hebben, wordt alleen nog getest met verzonnen antwoorden |
| Toevoeging | Appartement met het grondperceel van het gebouw | Toevoeging "NU01" op het gemeentehuis van Dongen: eigen naam, hetzelfde perceel. Het grondperceel bij een appartement wordt niet meer live getest |
| Berichten in een regio | Echte berichten over de twee panden in de regiobestanden | Een openbaar gebouw heeft zelden een bericht. De livetest voegt daarom één verzonnen proefbericht per adres toe aan het regiobestand dat de pagina leest. Het bestand op schijf blijft gelijk |
| Kern zonder regiobestand | Het appartement in Tilburg | Het object op het gemeentehuis van Dongen (Dongen hoort bij de kern) |
| Ruimtelijke plannen, energielabel | Nagespeeld | Ongewijzigd nagespeeld |

## Tests

| | |
|---|---|
| Hele reeks | 568 tests geslaagd, 10 overgeslagen (de livetests en de filmtests) |
| Livetest tegen PDOK (`TILBURG_ADRES_LIVE=1 python -m unittest tests.test_adres.EchteBronnen`) | 4 tests geslaagd, 7 adressen. Alleen PDOK gevraagd; Ruimtelijke plannen nagespeeld |
| Gezocht na afloop | Geen van de vijf oude adressen, hun postcodes, perceelnummers of coördinaten staat nog in `tests/`, `docs/`, `tools/`, `README.md` of de code van de site |

## Wat Wim moet nakijken

| Adres | Nakijken |
|---|---|
| Gemeentehuis Dongen | Of dit het huidige bezoekadres is. Bron: organisaties.overheid.nl |
| Object "NU01" op het gemeentehuis van Dongen | Volgens de BAG 7 m², "overige gebruiksfunctie", op hetzelfde perceel. Waarschijnlijk een technische ruimte of voorziening van het gemeentehuis; dat heb ik niet kunnen bevestigen. Twijfel je, dan kan de toevoeging alleen in unit-tests (verzonnen) worden getest |
| Gemeentehuis Goirle | Of dit het huidige bezoekadres is |
| Stadskantoor Middelburg | Bezoekadres volgens organisaties.overheid.nl; ook het KVK-kantoor zit daar |
| Stadskantoor Breda | Bezoekadres volgens organisaties.overheid.nl en DUO |
| Huisletter A bij het stadskantoor Breda | Volgens de BAG een kantoor van 7.749 m² op hetzelfde perceel als het stadskantoor. Of het de gemeente zelf is of een huurder in het gebouw, heb ik niet kunnen vaststellen |

## Wat er bewust niet is veranderd

| Punt | Waarom |
|---|---|
| De geschiedenis van de repo | Herschrijven mag niet. De oude adressen staan in eerdere commits en in de pull-request-refs op GitHub |
| `site/data/` | Vier van de vijf oude adressen staan daar in echte bekendmakingen. Dat zijn gegevens van de bron, geen proefadressen |
| Adressen uit echte bekendmakingen in tests | Niet aangeraakt, ook niet een ander huisnummer in dezelfde Goirlese straat in `tests/test_signalen.py`. Uitzondering: in de test "bericht op hetzelfde perceel" stonden het nummer ernaast en een buurnummer van de woning in Dongen, aan de woning gekoppeld met haar coördinaten. Die zijn mee vervangen door Teststraat 40 en 44; anders wees de test nog naar die woning |

## Wat ik niet heb kunnen controleren

| Punt | Toelichting |
|---|---|
| Wat object "NU01" en huisletter A precies zijn | Alleen de BAG en de Locatieserver gezien |
| Of de livetest later blijft slagen | De registers veranderen; vandaag geslaagd |
| De pull request op GitHub | De testrun volgt bij het openen |
| iPhone | Niets veranderd aan de app; niet nodig |
