# Tilburg Signalen: verslag locatierapport

| | |
|---|---|
| Datum | 20-11-2026 |
| Versie | branch `claude/locatierapport`, vanaf `main` op commit `6e3e390` (na PR #36); niet samengevoegd |
| Omgeving | Claude Code in de cloud (tijdelijke container), Chromium 157 met Playwright |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_adresrapport_20-11-2026.md` |

## Opdracht

Vanuit een gevonden ontwikkellocatie één rapport maken: de gegevens van de bekendmaking samen met de
vakken van het adresrapport, in één afdruk. Het rapport hergebruikt `rapport.js` en neemt nieuwe
vakken vanzelf mee. Alle waarschuwingen, bronnen en tijden van opvragen staan op papier. Het rapport
moest ook compacter worden.

## Stap 0: kan de Adres-tab vanuit een locatie gevuld worden?

Ja. Wat een bericht over zijn plek weet, staat in drie velden: `plaats` (de tekst), `locatieSoort` en
het punt (`lat`, `lon`).

| `locatieSoort` | Wat het is | Telling in `berichten.json` van 16-11 (zonder de weggefilterde) |
|---|---|---:|
| `exact` | Een punt uit de bekendmaking zelf: het punt van een adres of een perceel. Een vlak buiten de straal komt op het dichtstbijzijnde deel te liggen | 80: 53 met straat en huisnummer, 6 met een perceel, 21 zonder bruikbare plaatstekst |
| `benaderd` | Een punt dat de app uit een straatnaam in de titel heeft afgeleid | 10 |
| `gemeente` | Alleen de gemeente | 14 |

| Optie | Hoe | Gevolg |
|---|---|---|
| A (gebouwd) | Het adres uit de tekst opzoeken in de adreszoeker van PDOK. Precies één adres dat de bestaande koppeling van publicaties aan adressen als "dit adres" ziet: alle vakken. Anders, met een vast punt: alleen perceel en bestemmingsplan op dat punt, met een melding. Anders alleen de bekendmaking | Waar de bekendmaking één adres noemt, is het rapport even volledig als het adresrapport. Waar dat niet kan, zegt het rapport waarom |
| B | Altijd het punt, met het dichtstbijzijnde adres | Kan stil een verkeerd adres (de buren) opleveren. Afgeraden |
| C | Alleen de bekendmaking, met een link naar de Adres-tab | Eenvoudig, maar het rapport mist perceel en bestemmingsplan |

Over "de witte cirkels": op het kaartje is een witte cirkel een **onzeker bericht**. Of het een
ontwikkellocatie is, staat dan niet vast; de plek kan wel exact zijn. Waar de plek niet vaststaat
(`benaderd`, `gemeente`), staat in het rapport "De plek is niet vastgesteld". Een onzeker bericht
krijgt een eigen waarschuwing die naar de witte cirkel verwijst. Beide kunnen samen voorkomen.

Het kaartje heeft geen punten om op te tikken: de stippen zijn op een telefoon een paar pixels groot.
Vanaf het kaartje loop je daarom via de gemeente (tabblad Gebied) naar de kaarten in Berichten. Een
kaartje met aantikbare punten is niet gebouwd.

## Wat er is gebouwd

| Bestand | Wat |
|---|---|
| `site/app.js` | Onder "Details" van elke kaart de knop **Locatierapport**. Alleen kaarten die in de app te zien zijn, hebben die knop. Een weggefilterd bericht heeft een kaart alleen als de schakelaar aan staat |
| `site/adres-app.js` | `kiesLocatie(bericht)`: vult de Adres-tab volgens optie A. Het nieuwe vak "Bekendmaking" bovenaan bevat: titel, soort en fase, gemeente, datum, plek, de zin waarom, een samenvatting van de omschrijving (hoogstens ongeveer 280 tekens, nooit de hele tekst) en de waarschuwingen. Verder hoe de rest van het tabblad is gevuld, de link "Open de bekendmaking bij de bron" en de bronregel. Een vak dat niet van toepassing is, wordt verborgen. Wie daarna zelf een adres kiest, krijgt weer een gewoon adresrapport |
| `site/adres.js` | Zonder pagina, dus te testen: omrekening GPS naar RD (voor het bestemmingsplan op een punt, binnen ongeveer een meter), de keuze adres, punt of geen, de waarschuwingen en de samenvatting |
| `site/rapport.js` | Titel "Locatierapport" in plaats van "Adresrapport", en een vijfde punt bij "Lees dit eerst" (de bekendmaking is samengevat, de volledige tekst staat bij de bron). Een verborgen vak blijft van papier. Nog steeds geen vaste lijst van vakken |
| `site/index.html` | Het vak "Bekendmaking" (verborgen tot het gebruikt wordt); twee vakken kregen een `id` |
| `site/styles.css`, `site/sw.js` | Compactere afdruk (hieronder); cache `v17` |
| `CLAUDE.md`, `README.md` | De werking en de afspraak over verborgen vakken |

### Wanneer welke vakken

| De bekendmaking heeft | Vakken | Melding in het vak Bekendmaking |
|---|---|---|
| Eén adres, gevonden in de adreszoeker | Alle vakken van het adresrapport | "Adres afgeleid uit de tekst van de bekendmaking … Controleer of het het bedoelde adres is." |
| Geen eenduidig adres, wel een vast punt | Kadastraal perceel en bestemmingsplan op het punt | "Geen eenduidig adres. … beperkte nauwkeurigheid. Pand (BAG), energielabel en publicaties over het adres zijn daarom overgeslagen." Bij het perceel: het punt is omgerekend en kan enkele meters afwijken |
| Een benaderd punt of alleen de gemeente | Alleen de bekendmaking | "De plek is niet vastgesteld." en "Geen eenduidig adres en geen vaste plek. …" |

## Compacter

| Wat | Was | Nu |
|---|---|---|
| Marges van het papier | 16 / 15 / 18 mm | 13 / 14 / 15 mm |
| Vakken | Kader met ronde hoeken en binnenruimte | Een dunne lijn erboven en wit eronder. Alleen "Lees dit eerst" en de waarschuwingen houden een kader |
| Kopjes en kop van het rapport | 20 en 12,5 punt | 17 en 11,5 punt |
| Kaartje van het perceel | Onder de gegevens, 80 mm breed | Rechts naast de gegevens, 52 mm breed |
| Regels tussen gegevens en berichten | Ruimer | Krapper |
| Eigen aantekeningen | 12 lijnen | 8 lijnen |
| Lange vakken | Elk vak bleef heel; een lang vak schoof naar een nieuwe pagina en liet wit achter | Een vak met meer dan 4 berichten of lijstregels mag over een pagina doorlopen. Elk bericht en elke regel blijft heel. Ook "Bronnen en beperkingen" en "Links" mogen doorlopen. Andere vakken blijven heel |
| Waarschuwingen en bronregels | 9 en 8,5 punt | Ongewijzigd |

Gemeten met het testadres, alle vakken en een proefvak: van **6 naar 5 pagina's** A4. Het
locatierapport met adres is ook 5 pagina's, met de bekendmaking en 10 publicaties erbij.

Let op: dat een lang vak over een pagina mag doorlopen, is een wijziging ten opzichte van de afspraak
bij het adresrapport ("een vak mag niet midden doorbroken worden"). Gewone vakken blijven heel.

## Tests

| | |
|---|---|
| Hele reeks | 583 tests geslaagd, 10 overgeslagen (de tests tegen de echte bronnen en de filmtests). Ook de browsertests in Chromium |
| Nieuw in de browser (`tests/js/adres_smoke.js`) | Vijf verzonnen berichten over het openbare testadres (met adres, alleen een punt, benaderd, alleen de gemeente, weggefilterd), toegevoegd aan de gegevens die de pagina laadt. Telefoon van 390 px, donker thema. Per bericht: van de kaart naar de Adres-tab, de vakken, het vak Bekendmaking, en de afdruk in print-media. PDOK, de energielabel-Worker en Ruimtelijke plannen worden nagespeeld |
| Nieuw in Python (`tests/test_site.py`: 8, `tests/test_adres.py`: 7) | De knop vult de tab; het adres krijgt alle vakken; een samenvatting, niet de hele tekst; een punt zonder adres geeft perceel en bestemmingsplan met de melding; benaderd en gemeente geven "De plek is niet vastgesteld"; onzeker geeft de waarschuwing over de witte cirkel; een weggefilterd bericht alleen met de schakelaar; op papier "Locatierapport", alle vakken in volgorde, alle waarschuwingen en bronregels zichtbaar, geen tabbalk, de link naar de bekendmaking in de lijst Links; daarna een getypt adres geeft weer een adresrapport; RD binnen een meter; meer dan één adres in een bericht of een adres elders telt niet als één adres |
| Aangepast | Aantekeningen 8 lijnen; "vakken blijven heel" geldt nu voor vakken die niet lang zijn; het adresrapport is hoogstens 5 pagina's |
| Externe aanroepen | Geen; de test controleert dat er niets buiten de nagespeelde diensten wordt gevraagd |

## Wat ik niet heb kunnen controleren

| Punt | Toelichting |
|---|---|
| iPhone | Niets op een iPhone gedaan: niet de knop op een kaart, niet het afdrukken en niet de PDF |
| Echte berichten | Getest met verzonnen berichten over het testadres. Hoe vaak een echte bekendmaking precies één adres oplevert, is niet gemeten. Volgens de telling heeft ongeveer de helft van de zichtbare berichten een plaatstekst met een huisnummer |
| Echte adreszoeker | Nagespeeld. Een bekendmaking met een ongewone schrijfwijze kan in het echt geen of een ander antwoord geven; dan volgt het punt |
| Nauwkeurigheid van het punt | De omrekening is getest op het testadres (binnen een meter). Bij een groot plangebied ligt het punt op het deel dat het dichtst bij Tilburg-centrum ligt; dat staat bij het perceel |
| Kaartje | Geen aantikbare punten (zie stap 0) |
| Afdrukvenster op Windows | Alleen de PDF uit Chromium bekeken, als plaatje |
