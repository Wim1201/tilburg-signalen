# Tilburg Signalen: verslag tabblad Adres

| | |
|---|---|
| Datum | 17-11-2026, 16:51 – 17:25 uur |
| Versie | versie 2 van de app plus het tabblad Adres, branch `claude/optimistic-gauss-sb0xpy`, gestart vanaf `main` op commit `68f4660` (na PR #14) |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | `site/data/berichten.json` zoals het in de repo staat (bijgewerkt 16-11-2026, 15:37 uur, 1.116 berichten); antwoorden van PDOK van 17-11-2026 tussen 16:53 en 17:20 uur |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_video_16-11-2026.md` |

## Stand

Het tabblad Adres is gebouwd en staat op de werkbranch. Het is **niet samengevoegd met `main` en
staat niet live**; er is geen pull request. De gegevens, de regels, de cache en de workflow zijn niet
gewijzigd: `signalen/`, `config.json`, `site/data/`, `cache/` en `.github/` zijn onaangeroerd
(`git status` leeg voor die mappen).

Alle bronnen die het tabblad gebruikt, mag de browser aanroepen. Er is geen onderdeel om een omweg
heen gebouwd.

**Niet door mij te beoordelen:** of het tabblad op een echte telefoon prettig werkt. Getest is in
Chromium op 320 en 390 pixels breed.

## Correcties en aanvullingen op eerdere verslagen

| Tijdstip | Wat |
|---|---|
| 17-11-2026, 17:25 uur | **De app heeft vier tabbladen in plaats van drie.** Waar eerdere verslagen de tabbalk met Berichten, Gebied en Bronnen beschrijven, staat daar nu Adres naast. De drie bestaande tabbladen zijn zelf niet gewijzigd; op 320 pixels is elke tab 72 pixels breed (was 96). |
| 17-11-2026, 17:25 uur | **De app vraagt nu zelf gegevens op bij een externe dienst, maar alleen op het tabblad Adres.** Tot nu toe haalde alleen de workflow gegevens op en las de app alleen zijn eigen bestanden. Het ochtendscherm doet dat nog steeds: een test bewaakt dat er bij het openen van de app nul verzoeken naar PDOK gaan. "De app heeft geen server of database" blijft gelden. |
| 17-11-2026, 17:25 uur | **Het aantal tests is 287 (was 223).** Er zijn er 64 bij: 50 voor de logica en de pagina, 11 in de browser en 3 die alleen op verzoek tegen de echte bronnen draaien. Zes filmtests worden hier overgeslagen omdat de film in deze container niet is gemaakt; dat was al zo. |
| 17-11-2026, 17:25 uur | **De naam van de opslag van de app op het toestel is `tilburg-signalen-v8` (was `v7`)**, omdat er twee bestanden bij zijn gekomen die zonder verbinding beschikbaar moeten zijn. Een geïnstalleerde app haalt daardoor na het samenvoegen één keer alles opnieuw op. |

## Opdracht

Een tabblad Adres naast de bestaande tabbladen, voor eigen gebruik. De gebruiker typt een adres en
ziet: het pand volgens de BAG, het kadastrale perceel met een kaartje en de grootte, en de
gemeentelijke publicaties over dat adres uit de bestaande gegevens, ook de weggefilterde. Voor
energielabel en bestemmingsplan alleen "nog niet beschikbaar" met een link. Alleen open bronnen,
rechtstreeks vanuit de browser, zonder sleutel, Worker of betaalde dienst. Vooraf per bron
controleren of de browser hem mag aanroepen. Los daarvan onderzoeken, zonder te bouwen, of het
bestemmingsplan of omgevingsplan zonder sleutel op te vragen is. Het ochtendscherm en de bestaande
tabbladen mogen niet veranderen, de verversing mag niet zwaarder worden, en er wordt niets in de
cache geschreven.

## Bronnen: mag de browser ze aanroepen

Gecontroleerd op twee manieren: de kopregel `Access-Control-Allow-Origin` in het antwoord (16:53 uur),
en daarna een echte pagina in Chromium die elke bron ophaalt zoals de app dat doet (16:58 uur). Een
browser weigert het antwoord van een bron die dat niet toestaat; de tweede controle is daarom de
doorslaggevende.

| Bron | Waarvoor | Adres van de dienst | Uitkomst in de browser | Sleutel |
|---|---|---|---|---|
| PDOK Locatieserver | Adres zoeken met suggesties | `api.pdok.nl/bzk/locatieserver/search/v3_1/suggest` | Toegestaan (`*`), status 200 | Geen |
| BAG, verblijfsobject | Gebruiksdoel, oppervlakte | `api.pdok.nl/kadaster/bag/ogc/v2/collections/verblijfsobject` | Toegestaan (`*`), status 200 | Geen |
| BAG, pand | Bouwjaar, pandstatus | `api.pdok.nl/kadaster/bag/ogc/v2/collections/pand` | Toegestaan (`*`), status 200 | Geen |
| Kadastrale kaart, perceel | Aanduiding, grootte, omtrek | `api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1/collections/perceel` | Toegestaan (`*`), status 200 | Geen |
| Kadastrale kaart, kaartbeeld | Achtergrond van het kaartje | `service.pdok.nl/kadaster/kadastralekaart/wms/v5_0` | Wordt als afbeelding geladen; daarvoor is geen toestemming nodig. De dienst geeft die overigens wel (`*`) | Geen |

Niet gebruikt, wel geprobeerd (zie het onderzoek hieronder):

| Bron | Uitkomst in de browser |
|---|---|
| DSO, Omgevingsdocumenten presenteren (`service.omgevingswet.overheid.nl/publiek/omgevingsdocumenten/api/presenteren/v8`) | Geblokkeerd. Zonder sleutel antwoordt de dienst met 401 "Inloggegevens ontbreken", zonder toestemming voor de browser |
| Ruimtelijke plannen, opvragen v4 (`ruimte.omgevingswet.overheid.nl/ruimtelijke-plannen/api/opvragen/v4`) | Geblokkeerd. Zonder sleutel 401 "Niet geauthenticeerd" |
| EP-Online, openbare koppeling (`public.ep-online.nl/api/v5`) | Geblokkeerd. Deze koppeling werkt met een sleutel |

## Onderzoek: bestemmingsplan of omgevingsplan zonder sleutel (niet gebouwd)

Uitgevoerd als aparte stap, tussen 16:55 en 17:02 uur. Er is niets van gebouwd; het tabblad toont
"Nog niet beschikbaar in de app" met een link.

| Vraag | Bevinding |
|---|---|
| Kan het via het DSO (Omgevingsloket)? | **Nee, niet zonder sleutel.** Beide koppelingen antwoorden met 401 en de browser mag ze niet aanroepen. Een sleutel in de app zetten kan niet, want alles in de app is openbaar; het zou een tussenserver vragen. |
| Kan het via PDOK? | **Ja, voor bestemmingsplannen.** PDOK heeft een kaartdienst "Ruimtelijke plannen" (`service.pdok.nl/kadaster/ruimtelijke-plannen/wms/v1_0`). Die geeft op een punt de gegevens van het plan terug (`GetFeatureInfo`, als JSON), zonder sleutel, en de browser mag hem aanroepen (in Chromium getest, status 200). |
| Wat komt er dan terug? | Geprobeerd op Hoge Ham 12 in Dongen: enkelbestemming "Wonen", het bouwvlak, "maximale goothoogte (m) = 6", en drie plannen die daar gelden: "Zuid en West Dongen" (2010), de partiële herziening daarvan (2015) en "Parapluplan Parkeren Dongen" (2020), elk met plannummer, status en datum. Bij de bestemming staat een verwijzing naar de planregels op ruimtelijkeplannen.nl. |
| Wat komt er niet terug? | Wijzigingen van het omgevingsplan die onder de Omgevingswet zijn gepubliceerd (sinds 1-1-2024). Die staan alleen in het DSO. De website ruimtelijkeplannen.nl meldt zelf: "de informatie op deze website is niet volledig en mogelijk verouderd. Maak gebruik van het Omgevingsloket voor een volledig beeld van de geldende regels." |
| Bestaat er een andere vorm bij PDOK? | Nee: een OGC-koppeling en een WFS voor ruimtelijke plannen bestaan niet op de adressen die ik heb geprobeerd (beide 404). Alleen de kaartdienst. |

**Niet vastgesteld:** hoe actueel de gegevens in de kaartdienst van PDOK zijn, en of de verwijzing naar
de planregels (een adres dat met `http://` begint) nog werkt. Dat is niet nagekeken.

**Wat dit betekent:** de bestemming, het bouwvlak en de maximale maten uit het oude bestemmingsplan
zijn zonder sleutel in de app te tonen, met de duidelijke kanttekening dat latere wijzigingen van het
omgevingsplan ontbreken. Of dat de moeite waard is, is aan Wim.

### Energielabel

EP-Online heeft een openbaar zoekscherm en een koppeling met sleutel. Het zoekscherm verstuurt het
adres met een formulier dat een eenmalig controlegetal meestuurt; een link die het adres al invult,
bestaat daardoor niet. Het tabblad linkt naar het zoekscherm en zet erbij wat je daar invult
(postcode en huisnummer).

## Wat er is gebouwd

| Onderdeel | Wat het toont | Bron |
|---|---|---|
| Zoekveld | Suggesties tijdens het typen, vanaf drie tekens, na 250 ms stilte. Adressen dichtbij Tilburg-centrum staan bovenaan. Enter kiest de bovenste | Locatieserver |
| Gekozen adres | Straat en huisnummer met toevoeging, postcode, woonplaats, gemeente | Locatieserver |
| Pand (BAG) | Bouwjaar, gebruiksdoel, oppervlakte, pandstatus, en de status van het adres zelf | BAG |
| Kadastraal perceel | Aanduiding (bijvoorbeeld "Tilburg Q 4688"), grootte, direct daaronder de waarschuwing, en een kaartje | Kadastrale kaart |
| Publicaties over dit adres | Per bericht datum, gemeente, soort en stand, de titel en een link naar de bron | De berichten die de app al heeft |
| Energielabel | "Nog niet beschikbaar in de app" en een link naar EP-Online | Geen aanroep |
| Bestemmingsplan en omgevingsplan | "Nog niet beschikbaar in de app" en een link naar Regels op de kaart | Geen aanroep |

De waarschuwing bij de grootte luidt letterlijk: "Let op: de kadastrale kaart geeft alleen een
indicatie van de ligging en de grootte. Er zijn geen maten aan te ontlenen."

### Bestanden

| Bestand | Wat |
|---|---|
| `site/adres.js` (nieuw) | De logica zonder de pagina: schrijfwijzen, huisnummers lezen, publicaties koppelen, antwoorden van de bronnen omzetten |
| `site/adres-app.js` (nieuw) | De pagina van het tabblad en de aanroepen naar PDOK |
| `site/index.html` | Het vierde tabblad en zijn inhoud toegevoegd; geen bestaande regel gewijzigd of verwijderd |
| `site/app.js` | Twee regels: "adres" in de lijst van tabbladen, en de geladen berichten beschikbaar voor het tabblad |
| `site/styles.css` | Opmaak van het tabblad toegevoegd; de tabbalk heeft vier kolommen in plaats van drie |
| `site/sw.js` | De twee nieuwe bestanden in de lijst voor gebruik zonder verbinding; opslag `v8` |
| `tests/test_adres.py` (nieuw) | 53 tests: 50 voor de logica en de pagina, 3 alleen op verzoek tegen de echte bronnen |
| `tests/js/adres_smoke.js`, `adres_fixtures.json`, `adres_live.js` (nieuw) | Het tabblad in een echte browser, met nagespeelde bronnen; de echte antwoorden die daarvoor zijn vastgelegd; dezelfde proef tegen de echte bronnen |
| `tests/test_site.py`, `tests/js/browser_smoke.js` | 11 browsertests voor het tabblad; twee bestaande tests aangepast aan vier tabbladen en vier scripts |
| `README.md` | Het tabblad en zijn bronnen beschreven |

## Gemaakte keuzes

| Keuze | Waarom |
|---|---|
| Het tabblad staat in eigen bestanden; `app.js` wisselt er alleen naartoe | Het ochtendscherm en de drie bestaande tabbladen blijven zoals ze zijn. Wat het tabblad nodig heeft, wordt pas opgevraagd als je er iets typt |
| Publicaties worden gezocht in de berichten die de app al geladen heeft (`data/berichten.json`) | Daarin staan alle berichten, ook de weggefilterde (1.012 van de 1.116). Er gaat geen extra verzoek uit en de verversing verandert niet. **`cache/ophaalcache.json` wordt niet gelezen**: dat bestand staat niet op de site, dus de browser kan er niet bij. Het is niet aangeraakt |
| Het tabblad schrijft nergens iets weg | Geen opslag op het toestel, geen verzoek dat iets wijzigt. Een test bewaakt dat zoeken de berichten ongewijzigd laat |
| Het perceel komt uit de koppeling tussen adres en perceel van het Kadaster, niet uit het punt op de kaart | De Locatieserver geeft per adres het gekoppelde perceel, per huisletter. Tilburgseweg 172 in Goirle heeft perceel E 1061, 172e heeft E 5983. Het adrespunt alleen kan net op het perceel van de buren vallen |
| Staat die koppeling er niet, dan het perceel op de plek van het adrespunt, met een regel die dat zegt | Kwam voor bij Lage Ham 42 in Dongen (nieuwbouw). Zonder die terugval was er geen perceel |
| De grootte is de grootte die het Kadaster registreert, niet uit het kaartje gemeten | Dat is het officiële getal. Erachter staat "vastgesteld" of "voorlopig", zoals de bron het geeft. De waarschuwing staat er direct onder |
| Het kaartje is het officiële kaartbeeld van de kadastrale kaart met het perceel eroverheen getekend | Eén afbeelding geeft perceelgrenzen, perceelnummers, gebouwen en huisnummers. Het perceel zelf tekent de app, zodat het ook zichtbaar is als de afbeelding niet komt |
| Het kaartje heeft ook in het donkere thema een witte ondergrond | De kaartdienst tekent zwart op wit |
| Pand en adresobject worden apart opgevraagd; komt het pand niet, dan toont het tabblad wat er wel is | Gebruiksdoel en oppervlakte horen bij het adres, bouwjaar en status bij het pand |
| Elk vak laadt apart en meldt zelf als zijn bron niet antwoordt, met een knop "Opnieuw proberen" | Eén bron die uitvalt, mag de rest niet meenemen |
| Na 12 seconden zonder antwoord stopt de app met wachten | Anders blijft een vak eindeloos "wordt geraadpleegd" tonen |
| Energielabel en plan zijn gewone links; de app roept daar niets aan | Zo gevraagd. Een test bewaakt dat er alleen verzoeken naar PDOK gaan |
| De browsertests van het tabblad zitten in de bestaande browsertest | Die draait al op GitHub bij een push en na elk publiceren. De workflow hoefde daardoor niet te veranderen |
| De browsertests spelen de bronnen na met echte, vastgelegde antwoorden | Een test die van PDOK afhangt, faalt als PDOK hapert, en kan een bron niet bewust laten uitvallen |

## Publicaties aan een adres koppelen

De bronnen schrijven adressen niet in een vaste vorm. De app trekt beide kanten gelijk voordat ze
vergelijkt: het adres uit de BAG en de tekst van het bericht (plaats, titel en omschrijving).

| Wat wordt gelijkgetrokken | Voorbeeld |
|---|---|
| Hoofdletters, accenten, punten, apostroffen | "'s Gravenmoer", "HEUVELSTRAAT" |
| "straat" en "str." | "Heuvelstr. 5", "Heuvelstr 5", "Heuvel straat 5" |
| Titels in straatnamen | "Burg." en "Burgemeester", "St." en "Sint", "Dr.", "Doctor" en "Dokter", "Prof.", "Past.", "Kard.", "Gen.", "Mgr.", "Mr.", "Ir.", "Pres.", "Ds.", "Pr." en "Prins(es)", "Kon." en "Koning(in)" |
| Spaties en streepjes in de straatnaam | "Waspikse weg" en "Waspikseweg", "Ringbaan-Oost" en "Ringbaan Oost" |
| De toevoeging | "118a", "118 a", "118-A", "40 a 1" en "40a-1", "1V-3004", "67-12" en "67-01" naast "67-1" |

| Uitkomst | Wanneer | Waar het staat |
|---|---|---|
| Dit adres | De tekst noemt straat, huisnummer en dezelfde toevoeging | Onder "Dit adres" |
| Mogelijk dit adres | Hetzelfde huisnummer met een andere of geen toevoeging aan één kant; een reeks waar het nummer in valt ("529-721", "12 t/m 18"); of de tekst noemt het adres niet, maar de locatie van het bericht ligt op hetzelfde perceel | Onder "Mogelijk dit adres", met de reden erbij |
| Zelfde straat | De tekst noemt de straat zonder enig huisnummer | Ingeklapt onder "Zelfde straat, zonder huisnummer" |
| Niet | Ander huisnummer, andere toevoeging aan beide kanten (12a en 12b), andere gemeente, of dezelfde straat en nummer op meer dan 250 meter | Niet getoond |

Verder: een getal dat iets telt ("3 woningen", "4 bomen") is geen huisnummer. Een postcode wordt niet
als huisnummer of toevoeging gelezen. "Korte Heuvel 12" is niet "Heuvel 12". Noemt een bericht een
andere postcode dan de BAG maar ligt het op de plek van het adres, dan staat het onder "Dit adres"
met een opmerking; dat kwam echt voor (zie "Gevonden tijdens het werk").

### Bekende beperkingen van het koppelen

Dit blijft de zwakste schakel. Een gemist bericht is in de app niet te zien.

| Beperking | Gevolg |
|---|---|
| De lijst bevat alleen wat de app nu heeft: vergunningen 42 dagen, planberichten 180 dagen | Oudere publicaties over een adres staan er niet in. Het tabblad zegt dat onder de lijst |
| Een bericht dat het adres alleen als kadastraal perceel of als omschrijving noemt ("hoek X-straat en Y-laan") | Wordt alleen gevonden als de locatie van het bericht op het perceel ligt; 68 van de 1.116 berichten hebben geen exacte locatie |
| Een straatnaam die in een langere straatnaam zit ("Vincent van den Heuvelstraat 5" tegenover "Heuvelstraat 5") | Wordt alleen uit elkaar gehouden door de postcode of de locatie van het bericht. Ontbreken beide, dan komt het bericht onterecht onder "Dit adres" |
| Een straatnaam die ook een gewoon woord is ("Markt", "Heuvel") | Kan onterecht onder "Zelfde straat" verschijnen |
| Twee verschillende toevoegingen (12a en 12b) | Het bericht over 12b wordt bij 12a niet getoond, tenzij het op hetzelfde perceel ligt |
| Afkortingen buiten de lijst hierboven, en schrijffouten in de straatnaam | Worden niet herkend |
| Faillissementen en verkoopvoornemens | Worden op dezelfde manier doorzocht; niet apart getest met een echt voorbeeld |

## Getest

| Wat | Hoe | Uitkomst |
|---|---|---|
| Adresnormalisatie | 7 tests: hoofdletters en accenten, "straat" en "str.", titels, spaties en streepjes, toevoegingen | Geslaagd |
| Huisnummers lezen | 6 tests op 23 schrijfwijzen, waarvan 16 letterlijk uit berichten in de gegevens | Geslaagd |
| Publicaties koppelen | 13 tests: andere schrijfwijzen, toevoeging, reeksen en lijsten, zelfde adres in een andere plaats, verkeerde postcode, langere straatnaam, alleen de straat, zelfde perceel, weggefilterde berichten, de inhoud van een regel, gegevens blijven ongewijzigd | Geslaagd |
| Alle echte berichten met een gewoon adres | Voor elk bericht in `site/data/berichten.json` met een adres in de vorm "straat nummer, postcode plaats": zoeken op dat adres moet dat bericht onder "Dit adres" geven | Geslaagd |
| Een bron die niets of iets kapots teruggeeft (logica) | 3 tests: lege antwoorden, een pand dat niet komt, onvolledige berichten | Geslaagd |
| Een bron die niet antwoordt (browser) | De adreszoeker zonder verbinding; de adreszoeker die de aanvraag aanneemt en zwijgt (melding na 12,4 seconden); de BAG met een foutcode en het Kadaster zonder verbinding; alleen het pand en het kaartbeeld weg | Telkens een melding in het eigen vak, de rest van het tabblad blijft staan, geen fout in de pagina. "Opnieuw proberen" vult het vak als de bron terug is |
| Compact op 320 pixels | Niets breder dan het scherm (leeg, met suggesties, met uitkomst, met de straatlijst open); vier tabbladen even breed met de naam op één regel; kaartje vierkant en binnen het scherm; geen datum over twee regels; links en suggesties groot genoeg om te tikken (41 en 64 pixels hoog) | Geslaagd |
| Het ochtendscherm verandert niet | Nul verzoeken naar PDOK bij het openen; na een bezoek aan Adres toont Berichten dezelfde ochtendzin, telling en kaarten | Geslaagd |
| Alleen PDOK, zonder sleutel | De verzoeken die de pagina echt doet zijn geteld: zes naar `api.pdok.nl` en `service.pdok.nl`, geen naar een andere dienst, geen sleutel in een adres | Geslaagd |
| Alle bestaande tests | `python -m unittest discover tests` | 287 tests, geslaagd; 9 overgeslagen (6 filmtests, 3 tests tegen de echte bronnen) |
| De browsertests drie keer achter elkaar | `python -m unittest tests.test_site.InDeBrowser` | Drie keer geslaagd, telkens ongeveer 19 seconden, waarvan 12 het wachten op de bron die zwijgt. De hele testreeks duurt hier 47 seconden (was 25) |
| Tegen de echte bronnen | `TILBURG_ADRES_LIVE=1 python -m unittest tests.test_adres.EchteBronnen`, 17:20 uur | Geslaagd, 12 seconden; zie hieronder |
| Donker thema | Twee schermafbeeldingen bekeken op 320 pixels | Leesbaar; het kaartje houdt een witte ondergrond |

### Echte adressen (17-11-2026, 17:20 uur, 320 pixels breed)

| Adres | Pand volgens BAG | Perceel | Publicaties in de app |
|---|---|---|---|
| Burgemeester van de Mortelplein 118a, Tilburg | 1962, gezondheidszorgfunctie, 280 m², verbouwing pand | Twee gekoppelde percelen: Tilburg Q 4688 (46 m²) en Q 4489 (248 m²) | Dit adres: 2 (aanvraag 10-11, besluit 13-11) |
| Lage Ham 42, Dongen | 2027, woonfunctie, 173 m², bouwvergunning verleend | Dongen B 5732 (382 m², voorlopig), bepaald op de plek van het adrespunt | Dit adres: 1 (besluit 16-11, met de opmerking over de postcode). Mogelijk: 1 (termijnverlenging "Lage Ham 40" van 15-10, op hetzelfde perceel). Zelfde straat: 1 |
| Tilburgseweg 172e, Goirle | 2024, woonfunctie, 304 m², pand in gebruik | Goirle E 5983 (2.510 m²) | Dit adres: 1 (04-11; het bericht noemt zelf perceel E 5983) |
| Tilburgseweg 172, Goirle | 1921, woonfunctie, 262 m², pand in gebruik | Goirle E 1061 (2.580 m²) | Mogelijk: 2 (berichten over 172c en 172e, met de reden erbij) |
| Heuvelring 67-12, Tilburg | 1982, woonfunctie, 62 m², pand in gebruik | Tilburg M 10348 (527 m²), het grondperceel van het gebouw | Geen |

Bij alle vijf: het kaartbeeld geladen, het perceel getekend, niets breder dan het scherm, geen
fouten, en alleen verzoeken naar `api.pdok.nl` en `service.pdok.nl`.

De proef van 172 tegenover 172e laat zien dat een toevoeging haar eigen perceel krijgt.

## Gevonden tijdens het werk

| Tijdstip | Wat | Wat ermee gedaan is |
|---|---|---|
| rond 17:08 uur | **Een bericht met een andere postcode dan de BAG.** Het besluit van 16-11 voor Lage Ham 42 in Dongen noemt "5102 AD"; de BAG geeft 5102 AC. De eerste versie verwierp het bericht daarom als "dezelfde straatnaam in een andere plaats" | Een afwijkende postcode verwerpt een bericht niet meer als het op de plek van het adres ligt. Het staat onder "Dit adres" met de opmerking "Het bericht noemt postcode 5102 AD; het adres heeft 5102 AC." Test toegevoegd |
| rond 17:08 uur | **Hetzelfde perceel, ander huisnummer.** Een termijnverlenging van 15-10 noemt "Lage Ham 40" en ligt op het perceel van Lage Ham 42 | Staat onder "Mogelijk dit adres". Zonder het koppelen op ligging was dit bericht gemist |
| rond 17:08 uur | **Lage Ham 42 is in de bron niet aan een perceel gekoppeld** | De terugval op de plek van het adrespunt gaf het perceel; het tabblad zegt dat erbij |
| rond 17:15 uur | **Bij een heel groot perceel zou het kaartbeeld leeg zijn.** De kaartdienst tekent niets boven schaal 1:6000. Een test met een perceel van ruim een kilometer liet zien dat de eerste versie daaroverheen ging | De afbeelding wordt groter gevraagd naarmate het kader breder is, tot 2.048 pixels (goed voor ruim 2,8 kilometer). Daarboven blijft alleen de getekende omtrek over |
| rond 17:17 uur | **Eén browsertest las het scherm uit voordat het tabblad gewisseld was** en faalde daardoor bij één van de runs | De test wacht nu tot het tabblad zichtbaar is |

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| **Op een echte telefoon** | Niet te doen vanuit deze container. Getest is in Chromium; het schermtoetsenbord, Safari en de installatie als app zijn niet geprobeerd |
| **De link naar Regels op de kaart** | De link heeft de vorm `…/regels-op-de-kaart/documenten?locatie-stelsel=RD&locatie-x=…&locatie-y=…`. **Ik heb niet kunnen vaststellen dat het Omgevingsloket daarmee op het adres opent**: de kaart van het loket laadde in de testbrowser niet verder dan een leeg raamwerk, omdat het loket geautomatiseerde bezoekers tegenhoudt. De pagina zelf antwoordde wel. Graag één keer aantikken |
| **Wat EP-Online verwacht bij een toevoeging** | Het tabblad zegt "Vul daar in: 5037PL 118 a". Of EP-Online de toevoeging in die vorm aanneemt, is niet geprobeerd |
| **De live site en GitHub** | Niets is samengevoegd. Een push naar de werkbranch start geen run, dus de browsertests zijn voor deze wijziging nog niet op GitHub gedraaid. Dat kan met een handmatige run vanaf de branch (test en bouwt, zet niets live); niet gedaan zonder het te vragen |
| **Een standplaats of ligplaats** | Het tabblad zegt dan dat er geen verblijfsobject is. Alleen met de logica getest, niet met een echt adres |
| **Een adres buiten het werkgebied** | Pand en perceel werken voor heel Nederland; publicaties zijn er dan niet. Niet apart geprobeerd. Belgische adressen kent de adreszoeker niet |
| **Zonder verbinding** | De app zelf opent zonder verbinding; het tabblad geeft dan de melding van de adreszoeker. De installeerbare app met de nieuwe opslag `v8` is niet op een toestel geprobeerd |
| **Hoeveel de bronnen aankunnen** | PDOK noemt geen limiet voor dit gebruik die ik heb nagezocht. Eén gekozen adres kost vier tot negen verzoeken, plus één per keer dat de suggesties verversen |

## Bronnen die niet bereikbaar bleken

Van de bronnen die het tabblad gebruikt: geen. Locatieserver, BAG en kadastrale kaart antwoordden
bij elke aanroep.

Wel niet bruikbaar zonder sleutel, en daarom niet aangesloten: het DSO (omgevingsdocumenten), de
koppeling Ruimtelijke plannen v4 en de koppeling van EP-Online. De kaart van het Omgevingsloket was
vanuit de testbrowser niet te bekijken.

## Buiten dit verslag

- **Niet samengevoegd, geen pull request.** Zo afgesproken: niets samenvoegen en niets forceren zonder
  eerst te vragen. De afspraak van 16-11 (geen force push of andere wijziging van de geschiedenis
  zonder het voor te leggen) is aangehouden; er is alleen gewoon gepusht naar de werkbranch.
- **Het schema van de workflow is niet gewijzigd**; het hele bestand `.github/workflows/dagelijks.yml`
  is onaangeroerd.
- **Wat Wim zelf wil nakijken** (uit de opdracht): of een adres met een toevoeging het goede perceel
  geeft; of de publicaties bij een adres kloppen; of het tabblad op de telefoon bruikbaar is. Voor
  het eerste punt is Tilburgseweg 172 tegenover 172e in Goirle een goede proef.
- **Het tabblad Bronnen noemt de drie registers van het tabblad Adres niet.** Die lijst komt uit
  `signalen/bronnen.json` en de verversing; die zijn bewust niet aangeraakt. De bronnen staan op het
  tabblad Adres zelf, in elk vak.
- **Bewust niet gedaan:** het bestemmingsplan via de kaartdienst van PDOK tonen (alleen onderzocht);
  het laatst gezochte adres onthouden (het tabblad bewaart niets); een link van een bericht naar het
  tabblad Adres (de bestaande tabbladen zouden daardoor veranderen); een tussenserver voor het DSO of
  EP-Online.
- **Geen subsessie** deze ronde. Er is ook niets met ElevenLabs gedaan.
- **Schermafbeeldingen** van de vijf echte adressen zijn in de sessie gemaakt en staan niet in de repo.
