# Tilburg Signalen: verslag ontwikkellocaties, relevantie en nieuwe bronnen

| | |
|---|---|
| Datum | 16-11-2026 |
| Versie | tweede versie, branch `claude/dazzling-darwin-04no0e` (herstart vanaf `main` na samenvoegen van PR #1) |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | Live opgehaald op 16-11-2026 om 14:27 uur; zie referentiewaarden |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_bouw_16-11-2026.md` |

## Correcties en aanvullingen op het vorige verslag

| Tijdstip | Wat |
|---|---|
| 16-11-2026, 17:45 uur | PR #7 (schema in Nederlandse tijd en het verslag tot 17:40 uur) is samengevoegd. GitHub accepteert het workflowbestand met `timezone`: run 8 startte er direct mee en slaagde. Run 8 deed 31 verzoeken. Zie "Run 8". Of een geplande run werkelijk start, is daarmee nog niet bewezen. |
| 16-11-2026, 17:40 uur | **Het schema van de geplande runs is gewijzigd en staat nu in Nederlandse tijd.** De tijden "Zondag 03:30 UTC (04:30 of 05:30 uur Nederlandse tijd)" onder "Volledige verversing" en "08:40 of 09:40 uur" onder "Nog te doen (stand 17:25 uur)" gelden niet meer. Zie "Schema van de geplande runs". |
| 16-11-2026, 17:40 uur | **Het vermoeden "een derde run op GitHub komt rond de 34 verzoeken uit" is bevestigd.** Run 7 deed 34 verzoeken. PR #6 (herstel van de twee gebreken en het verslag tot 17:25 uur) is samengevoegd; de regels "Herstel van de twee gebreken samenvoegen" en "Derde run op GitHub" onder "Nog te doen (stand 17:25 uur)" zijn daarmee afgehandeld. |
| 16-11-2026, 17:40 uur | **De drie "ongelezen" rechtbankpublicaties waren geen blijvende fout.** Run 7 las ze alle drie bij de eerste poging. Zie "De drie overgebleven rechtbankpublicaties". |
| 16-11-2026, 17:40 uur | De opmerking in de workflow "Gemeenten publiceren op werkdagen rond 09:00 uur" was een aanname. Nu gemeten: tussen 09:00 en 09:21 uur. Het oude schema had in de winter de eerste run om 08:40 uur, dus vóór de publicatie; de berichten van de dag kwamen toen pas met de run van 09:40 uur. |
| 16-11-2026, 17:25 uur | **De cache is samengevoegd en op GitHub gemeten; de kop "Cache (… werkbranch, nog niet samengevoegd)" en de zin "Op GitHub is dit nog niet gemeten" zijn achterhaald.** PR #5 is samengevoegd met `main`. Run 5 schreef de eerste cache zelf (1.056 verzoeken), run 6 gebruikte hem (98 verzoeken). Zie "Cache op GitHub: run 5 en run 6". |
| 16-11-2026, 17:25 uur | **De 209 bij "insolventie" in de tabel "Wat er in de cache staat" is een lokaal getal.** Op GitHub stonden er na run 5 maar 157 en na run 6 206, omdat een deel van de rechtbankpublicaties niet werd gelezen zonder dat dat werd geteld. Zie "Twee gebreken gevonden in run 5". |
| 16-11-2026, 17:25 uur | **"Cache op GitHub controleren" onder "Nog te doen" is gedaan voor het terugzetten van de cache en het aantal verzoeken.** De handmatige en de wekelijkse volledige verversing zijn nog niet op GitHub uitgevoerd. |
| 16-11-2026, 17:25 uur | **Claude Code kan geen run starten.** GitHub weigert dat voor de toegang van deze sessie (403 bij handmatig starten en bij opnieuw draaien). De geplande run van 16:10 uur is niet gestart; Wim heeft run 6 om 17:21 uur handmatig gestart. |
| 16-11-2026, 15:40 uur | **"Elke verversing haalt het hele venster opnieuw op en onthoudt niets" (onder "Onvolledige dagen en inhalen") geldt niet meer letterlijk.** De lijst met publicaties wordt nog steeds elke run volledig opgevraagd, dus gemiste dagen komen nog steeds vanzelf binnen. Maar de tekst, perceelgrootte en adreslocatie per publicatie komen nu uit een cache; alleen nieuwe publicaties worden opgehaald. Zie "Cache". |
| 16-11-2026, 15:40 uur | PR #4 (dit verslag tot en met "Run na PR #3") is samengevoegd met `main`. De storing bij de bron is voorbij: om 15:35 uur meldde de dagcontrole 16-11 niet meer als onvolledig. |
| 16-11-2026, 15:20 uur | **Oorzaak van de mislukte verzoeken op GitHub vastgesteld; "oorzaak niet vastgesteld" en het vermoeden onder "Na de eerste run op GitHub" zijn daarmee vervangen door een waarneming.** De bron antwoordde met HTTP 429 (te veel verzoeken). In de run na PR #3 zijn alle 11 geweigerde verzoeken bij opnieuw proberen alsnog gelukt. Zie "Run na PR #3". |
| 16-11-2026, 15:20 uur | De zoekindex van de bron loopt de achterstand van 16-11 in: 0 publicaties om 15:01 uur, 266 om 15:08 uur, 744 om 15:11 uur, van gebruikelijk 2.097. De app heeft de eerste berichten van 16-11 al binnen en meldt de dag nog als onvolledig. |
| 16-11-2026, 15:00 uur | **De eerste run op GitHub (14:53 uur) leverde slechtere gegevens dan de lokale runs; de zin "Lokaal draait alles" onder "Bekende beperkingen" gaf dus een te gunstig beeld.** De run slaagde en de app is live, maar 56 teksten en 3 perceelgroottes konden vanaf GitHub niet worden opgehaald. Die berichten kwamen onterecht onder "Onzeker" (80 in plaats van 22). Oorzaak van het mislukken is niet vastgesteld: de fout werd niet gelogd. Zie "Na de eerste run op GitHub". |
| 16-11-2026, 15:00 uur | PR #2 is samengevoegd; "Samenvoegen met `main` is niet gedaan" onder "Buiten dit verslag" is achterhaald. Wat daarna is gebouwd (onvolledige dagen, robuuster ophalen) staat op de werkbranch en is nog niet samengevoegd. |
| 16-11-2026, ca. 12:35 uur | Het vorige verslag noemt de livegang als open punt. Dat is achterhaald: PR #1 is samengevoegd, Wim heeft GitHub Pages aangezet en `https://wim1201.github.io/tilburg-signalen/` geeft de app. Die draait nog op de eerste versie tot deze branch is samengevoegd. |
| 16-11-2026, ca. 13:00 uur | Het vorige verslag noemt de hoofdbron en PDOK "openbaar, geen sleutel" zonder de robots.txt te noemen. Aanvulling: `repository.overheid.nl/robots.txt` bevat `Disallow: /` en `api.pdok.nl/robots.txt` sluit de Locatieserver uit. Dat zijn aanwijzingen voor zoekmachines. De app gebruikt de gedocumenteerde koppelingen die de beheerders juist voor geautomatiseerd gebruik aanbieden (zie "Wat mag"). Het punt staat hier zodat Wim het zelf kan wegen. |
| 16-11-2026, 14:50 uur | **Oorzaak ontbrekende publicaties van 16-11 gevonden; de regel hieronder ("oorzaak niet vastgesteld") is daarmee achterhaald.** De vertraging ligt bij de bron, niet bij de app. Zie "Onderzoek: publicaties van 16-11". |
| 16-11-2026, 14:50 uur | **Telregel voor woningen gewijzigd op verzoek van Wim.** Alleen getallen die direct voor een woord op "woning(en)" of "appartement(en)" staan tellen, en ze worden opgeteld. De beperking "aantal woningen is het grootste genoemde getal" verderop geldt niet meer. De referentiewaarden van 14:27 uur zijn vervangen door die van 14:50 uur in "Referentiewaarden na de wijziging"; de oude tabel is blijven staan. |
| 16-11-2026, 14:27 uur | Het vorige verslag vermoedde een vertraging bij de bron voor de publicaties van 16-11. Om 14:27 uur stond er landelijk nog steeds niets van 16-11 in de zoekdienst. De oorzaak is niet vastgesteld. De laatste publicatiedag in de gegevens is vrijdag 13-11. |

## Wat er is veranderd

De app toont standaard alleen ontwikkellocaties, gerangschikt op relevantie, met per bericht één zin
die zegt waarom het relevant is. Berichten waarvan de omvang niet te bepalen is staan onder
"Onzeker". Een schakelaar "Toon ook wat is weggefilterd" laat de rest zien, elk met de reden.

### Regels

| Rang | Regel | Score |
|---|---|---|
| 1 | Wijziging van omgevingsplan of bestemmingsplan die ontwikkeling mogelijk maakt: de tekst noemt wonen (100), een andere bouwhoogte (96) of nieuwe bouw- of gebruiksmogelijkheden (92) | 92 – 108 |
| 2 | Twee of meer nieuwe woningen (nieuwbouw, of woningen in een bestaand gebouw); meer woningen geeft een hogere score | 75 – 100 |
| 3 | Overheid wil grond of vastgoed van minstens 400 m² verkopen | 45 – 57 |
| 4 | Perceel van minstens 400 m² met een signaal: sloop, functiewijziging, kavelsplitsing, bestemmingswijziging, leegstaand bedrijfspand; meer signalen en een groter perceel geven een hogere score | 40 – 70 |
| 5 | Failliet bedrijf met een bedrijfspand op een perceel van minstens 400 m² | 35 – 47 |
| Onzeker | Wel een signaal, maar aantal woningen of perceelgrootte niet te bepalen; of de bekendmaking beschrijft niet wat er gebeurt | apart tabblad |
| Weggefilterd | Al het andere | achter de schakelaar |

Ingetrokken of buiten behandeling: 25 punten eraf. Geweigerd: 15 eraf. Beslistermijn verlengd: 5 eraf.
Bij gelijke score staat het nieuwste bericht bovenaan. De drempel van 400 m² staat in `config.json`.

### Waar de gegevens voor de regels vandaan komen

| Gegeven | Herkomst |
|---|---|
| Aantal woningen en signalen | Titel en omschrijving van de bekendmaking. Ontbreekt de omschrijving (387 van de 974 vergunningen), dan leest de app de eerste regels van de bekendmaking zelf, tot de standaardalinea's over bezwaar en inzage. |
| Perceelgrootte | Kadastrale kaart via PDOK: het perceel op de locatie van het bericht. Noemt de bekendmaking zelf percelen, dan telt de grootste van beide. Alleen opgezocht waar de grootte de uitkomst bepaalt. |
| Bedrijfspand of woning (faillissementen) | BAG via PDOK: gebruiksdoel van het adres. |
| Omvang bij verkoop | De tekst van de bekendmaking ("circa 1.250 m²"), anders het Kadaster. |

## Onderzoek nieuwe signalen: wat is openbaar en wat mag

### 1. Faillissementen

| Bron | Openbaar | Mag geautomatiseerd | Besluit |
|---|---|---|---|
| Staatscourant, rubriek "faillissement, surseance van betaling of schuldsanering" (per rechtbank, per dag), via de zoekdienst van officielebekendmakingen.nl | Ja | Ja. Overheid.nl: "Voor bulkafname van officiële bekendmakingen kan de hieronder beschreven API worden gebruikt. Dit geniet de voorkeur boven de afname via geautomatiseerde 'scraping'." De dataset staat op data.overheid.nl met licentie CC-0. | **Gebouwd** |
| Centraal Insolventieregister, website | Ja | Nee. `robots.txt` sluit zoekresultaten en detailpagina's uit. | Niet gebouwd |
| Centraal Insolventieregister, webservice | Ja, gratis | Alleen met abonnement en een ondertekende overeenkomst die per post wordt ingestuurd, met voorwaarden voor gebruik en opslag. De voorwaardenpagina zelf was vanuit de bouwomgeving niet te lezen (403); dit komt uit de zoekresultaten. | Niet gebouwd; alleen Wim kan dit aanvragen |
| Commerciële faillissementssites | Deels | Niet onderzocht; ze putten uit dezelfde openbare bron | Niet gebouwd |

Overheid.nl vraagt afnemers bij "privacygevoelige content … zoals bepaalde gerechtelijke aankondigingen"
om "gelijksoortige maatregelen" als de bron zelf. Genomen maatregelen:

| Maatregel | Uitwerking |
|---|---|
| Alleen bedrijven | Alleen rechtspersonen (bv, nv, stichting, coöperatie, vereniging). Elke vermelding met "geb." of "woonadr." (natuurlijk persoon, eenmanszaak) wordt overgeslagen, net als vof, cv en maatschap en alle schuldsaneringen. |
| Geen woonadressen | Staat het bedrijf op een adres dat volgens de BAG alleen woning is, dan wordt het helemaal niet opgenomen, ook niet onder "weggefilterd". |
| Geen namen van personen | Namen van curatoren en rechters-commissarissen worden niet bewaard. |
| Korte bewaartermijn | De bron haalt de leesbare tekst na ongeveer een maand weg (alleen een pdf blijft). De app bewaart faillissementen 28 dagen en leest geen pdf's. |
| Niet vindbaar | De app heeft nu `noindex` en een `robots.txt` die zoekmachines weert. |
| Alleen nieuwe uitspraken | "Uitspraak faillissement" en "verlening surseance"; geen einde, verificatie of uitdelingslijsten. |

Uitkomst nu: de bron werkt, maar levert op dit moment **0 berichten**. In de leesbare periode
(ruim een maand) waren er landelijk 278 nieuwe faillissementen en surseances van rechtspersonen;
10 daarvan in het postcodegebied rond Tilburg, waarvan 5 op een woonadres of zonder BAG-adres en
5 buiten de 15 km. Dat is een waarneming over één maand, geen voorspelling.

### 2. Bedrijfspanden te koop of leeg

| Bron | Openbaar | Mag geautomatiseerd | Besluit |
|---|---|---|---|
| Voornemens van overheden om grond of vastgoed te verkopen ("Didam-publicaties") in Gemeenteblad en Provinciaal blad | Ja | Ja, zelfde zoekdienst als hierboven | **Gebouwd** |
| Funda in Business | Aanbod is zichtbaar | Nee. De site toont geautomatiseerde bezoekers een verificatiepagina ("verifiëren dat onze bezoekers echte mensen zijn"), ook voor de gebruiksvoorwaarden. Het verbodsartikel zelf heb ik daardoor niet kunnen lezen. | Niet gebouwd, niet gescrapet |
| Bedrijfspand.com | Aanbod is zichtbaar | Nee voor de zoekpagina's (`robots.txt`: `Disallow: /zoeken/`) | Niet gebouwd, niet gescrapet |
| Biedboek (Rijksvastgoedbedrijf) | Ja | Onbekend: geen voorwaarden, feed of koppeling gevonden | Niet gebouwd; eerst navragen |
| Leegstand per pand | Nee | n.v.t. Het CBS publiceert alleen cijfers per gebied; gemeentelijke leegstandslijsten zijn niet openbaar | Niet gebouwd |
| BAG-status "buiten gebruik" (PDOK) | Ja | Ja | Niet gebouwd: binnen de straal 4 objecten, 3 daarvan woning |

Wat dus wél binnenkomt over leegstand en verkoop: verkoopvoornemens van overheden, faillissementen
(pand kan vrijkomen) en bekendmakingen waarin woorden als "leegstaand", "voormalig kantoor" of
"herontwikkeling" staan. Particulier aanbod van bedrijfspanden komt niet binnen.

### Wat mag: de robots.txt van de gebruikte overheidsdiensten

| Dienst | robots.txt | Waarom toch gebruikt |
|---|---|---|
| `repository.overheid.nl` (zoekdienst en teksten) | `Disallow: /` | Het is de koppeling die overheid.nl zelf aanwijst voor bulkafname, met handleiding en CC-0-licentie. |
| `api.pdok.nl` | `Allow: /`, behalve de Locatieserver | De Locatieserver is een gedocumenteerde open dienst van PDOK. De app gebruikt hem alleen voor bekendmakingen zonder eigen locatie (enkele tientallen aanvragen per run). |
| Mercator Vlaanderen | Geen beperking voor deze laag | Open kaartdienst. |

Vindt Wim dit te ruim, dan kan de Locatieserver uit zonder dat er berichten verdwijnen: die
berichten krijgen dan "geen exacte locatie".

## Referentiewaarden (run van 16-11-2026, 14:27 uur)

| Meting | Waarde |
|---|---|
| Berichten totaal | 1077 |
| Ontwikkellocatie / onzeker / weggefilterd | 87 / 15 / 975 |
| Ontwikkellocaties per soort | 56 vergunningen, 28 plannen, 3 verkoopvoornemens, 0 faillissementen |
| waarvan vergunningen met 2 of meer woningen | 32 |
| Signalen bij niet-weggefilterde berichten | bestemmingswijziging 22, functiewijziging 16, sloop 10, leegstaand bedrijfspand 7, kavelsplitsing 0 |
| Berichten met vastgestelde perceelgrootte | 104 |
| Weggefilterd: geen woningbouw en geen signaal | 879 |
| Weggefilterd: één woning | 36 |
| Weggefilterd: thematisch plan / plan zonder locatie | 19 / 10 |
| Weggefilterd: verkoop van groenstrook of te klein | 21 |
| Per bron | officielebekendmakingen 1068, Vlaanderen 9, faillissementen 0 |
| Duur van een verversing | ongeveer 85 seconden (was 40) |
| Grootte gegevensbestand | 991 kB |
| Unittests | 44, alle geslaagd |

## Referentiewaarden na de wijziging van de telregel (run van 16-11-2026, 14:50 uur)

| Meting | 14:27 uur | 14:50 uur |
|---|---|---|
| Ontwikkellocatie / onzeker / weggefilterd | 87 / 15 / 975 | 79 / 22 / 976 |
| Ontwikkellocaties: vergunningen / plannen / verkoop | 56 / 28 / 3 | 48 / 28 / 3 |
| Vergunningen met 2 of meer woningen | 32 | 23 |
| Unittests | 44 | 49 |

Acht berichten gingen van "ontwikkellocatie" naar "onzeker", omdat het getal niet direct voor het
woord staat of omdat het woord geen woning of appartement is. Voorbeelden: "zeven aaneen gebouwde
woningen", "23 sociale huurappartementen", "6 wooneenheden", "71 wooneenheden". Eén bericht ging van
"onzeker" naar "weggefilterd". Het voorbeeld "19 grondgebonden woningen … in totaal 98
appartementen" telt als 98, omdat "19" niet direct voor "woningen" staat; "19 woningen en 98
appartementen" telt als 117.

Twee aanvullingen die niet letterlijk gevraagd zijn, maar zonder welke het optellen fout gaat:

| Aanvulling | Waarom |
|---|---|
| Dezelfde vermelding telt één keer | Titel en tekst van een bekendmaking herhalen elkaar. Zonder dit werd "een woning" 2 en "98 appartementen" 196. Deze fout zat kort in de code en is door de voor-en-na-vergelijking gevonden, vóór het samenvoegen. |
| Gesloopte woningen tellen niet mee | "Sloop van 2 woningen en nieuwbouw van 14 woningen" telt als 14. |

Een huisnummer telt niet: staat het getal direct na een straatnaam ("Hoofdstraat 120 woningen"),
dan wordt het overgeslagen.

## Onderzoek: publicaties van 16-11

| Waarneming | Tijdstip | Uitkomst |
|---|---|---|
| Startpagina officielebekendmakingen.nl | 14:47 uur | "In totaal 2565 publicaties op maandag 16 november 2026": Gemeenteblad 2153, Staatscourant 160, Waterschapsblad 141, Provinciaal blad 103 |
| Melding op diezelfde pagina | 14:47 uur | "Mogelijk ervaart u problemen met het zoeken naar publicaties. We begrijpen dat dit hinder veroorzaakt en werken aan een oplossing." |
| Zoekpagina van overheid.nl voor 16-11 en 13-11 | 14:47 uur | Foutcode 503 |
| Zoekdienst (SRU) die de app gebruikt, publicatiedatum 16-11 | 14:48 uur | 4 publicaties (Kamerstukken en één Provinciaal blad, binnengekomen na 14:20 uur); geen Gemeenteblad of Staatscourant |
| Zoekdienst, publicatiedatum 13-11 | 14:47 uur | 2692 publicaties; de Staatscourant-publicaties kwamen die dag binnen tussen 09:08 en 09:31 uur |
| Vijf Staatscourant-publicaties van 16-11 rechtstreeks in de repository opgevraagd | 14:48 uur | Alle vijf aanwezig, met datum 16-11 |
| Dezelfde publicaties in de zoekdienst | 14:48 uur | Niet bekend |

Conclusie: overheid.nl heeft de publicaties van 16-11 gewoon geplaatst, maar de zoekindex is niet
bijgewerkt. De zoekpagina van overheid.nl zelf en de zoekdienst van de app hebben hetzelfde
probleem. De vertraging ligt dus bij de bron. De app haalt bij elke verversing het hele venster
opnieuw op, dus de berichten van 16-11 komen vanzelf binnen zodra de index is bijgewerkt; er gaat
niets verloren.

Toegevoegd naar aanleiding hiervan: de app toont een melding als de bron bij de laatste verversing
(werkdag, na 10 uur) nog niets van die dag had.

## Na de eerste run op GitHub (16-11-2026, 14:53 uur)

| Meting | Lokaal, 14:50 uur | GitHub, 14:53 uur |
|---|---|---|
| Ontwikkellocatie / onzeker / weggefilterd | 79 / 22 / 976 | 75 / 80 / 922 |
| Onzeker met reden "beschrijft niet wat er gebeurt" | 0 | 56 |
| Berichten met perceelgrootte | 105 | 102 |
| Duur stap "Berichten ophalen" | ongeveer 85 seconden | 3 minuten 51 seconden |
| Uitkomst workflow | n.v.t. | geslaagd, gepubliceerd |

Waarneming: op GitHub mislukte het ophalen van de tekst bij 56 bekendmakingen, verspreid over
minstens acht gemeenten. Vermoeden: de bron begrenst of vertraagt gelijktijdige verzoeken vanaf GitHub; de
langere looptijd past daarbij. Dat is niet bewezen, want de fout werd weggevangen zonder melding.

Wat daarop is aangepast (werkbranch, nog niet samengevoegd):

| Aanpassing | Uitwerking |
|---|---|
| Minder gelijktijdige verzoeken | 4 in plaats van 8 |
| Mislukte verzoeken opnieuw | Na de eerste ronde één voor één, maximaal drie minuten lang |
| Mislukken wordt geteld en gelogd | De eerste drie foutmeldingen staan in het log; het totaal staat in de gegevens (`ophaalfouten`) en als waarschuwing in de run |
| Eerlijke reden bij het bericht | "De tekst van deze bekendmaking kon niet worden opgehaald; de volgende verversing probeert het opnieuw." |
| Melding in de app | Aantal bekendmakingen dat niet volledig is gelezen |

Lokaal geeft de aangepaste versie 0 ophaalfouten in ruim 2 minuten. Of het op GitHub nu goed gaat,
blijkt pas na samenvoegen; het log laat dan in elk geval de oorzaak zien.

## Run na PR #3 (16-11-2026, 15:10 – 15:17 uur)

PR #3 is samengevoegd; de run die daardoor startte is geslaagd en gepubliceerd.

| Meting | Run na PR #2 (14:53 uur) | Run na PR #3 (15:11 uur) | Lokaal (15:08 uur) |
|---|---|---|---|
| Duur hele run | 4 min 41 s | 6 min 3 s | n.v.t. |
| Duur stap "Berichten ophalen" | 3 min 51 s | 5 min 8 s | 2 min 11 s |
| Teksten gevraagd | niet gemeten | 485 | 483 |
| Teksten mislukt in de eerste ronde | niet gemeten | 11, alle met reden HTTP 429 | 0 |
| Teksten hersteld bij opnieuw proberen | geen herhaling | 11 | 0 |
| Teksten die ontbreken | 56 | 0 | 0 |
| Perceelgroottes gevraagd / mislukt / ontbreken | niet gemeten / niet gemeten / 3 | 38 / 0 / 0 | 38 / 0 / 0 |
| Ontwikkellocatie / onzeker / weggefilterd | 75 / 80 / 922 | 80 / 23 / 980 | 80 / 23 / 977 |
| Berichten met perceelgrootte | 102 | 106 | n.v.t. |
| Onvolledige dag gemeld | n.v.t. | 16-11: 744 van 2.097 | 16-11: 266 van 2.097 |

Herkomst van de cijfers: de tijden komen uit de stappen van de run op GitHub. De aantallen en de
reden komen uit `ophaalstatistiek` in het gegevensbestand dat deze run publiceerde; dat is dezelfde
telling als de regel die de stap in het log schrijft. De logregel zelf heb ik niet gelezen: het
opgevraagde deel van het log (de laatste 100 van 320 regels) bevatte die stap niet. Er stond geen
waarschuwing over definitief mislukte verzoeken in, wat past bij 0 ontbrekende teksten.

Conclusie: de bron begrenst het aantal verzoeken vanaf GitHub (HTTP 429). Met minder gelijktijdige
verzoeken en opnieuw proberen met oplopende wachttijd komt alles binnen. De prijs is een langere
run: ruim 5 minuten ophalen in plaats van bijna 4.

Opgemerkt in het log, niet aangepast: GitHub meldt dat `actions/checkout@v4`, `configure-pages@v5`,
`setup-python@v5` en `upload-artifact@v4` op Node.js 20 zijn gebouwd en nu op Node.js 24 worden
gedraaid. Het werkt, maar de versies in de workflow moeten op termijn omhoog.

### Opnieuw proberen: oplopende wachttijd met een maximum

| Niveau | Wachttijd | Maximum |
|---|---|---|
| Binnen één verzoek (`signalen/http.py`) | 2, 4, 8, 16 seconden, telkens verdubbeld; een Retry-After van de bron wordt gevolgd | 30 seconden |
| Tussen herhaalde verzoeken na de eerste ronde (`signalen/update.py`) | 1, 2, 4, 8, 16 seconden zolang het blijft mislukken; terug naar 1 na een geslaagd verzoek | 20 seconden per pauze, 3 minuten in totaal |

### Gebruikelijk aantal publicaties, bestand tegen storingsdagen

Het gebruikelijke aantal was de mediaan over alle werkdagen. Bij een storing van meerdere dagen
zakt die mee. Nu: begin bij de volste dag, houd de dagen over die minstens de helft daarvan halen,
neem daarvan de mediaan, en herhaal tot de groep niet meer verandert. Storingsdagen tellen zo niet
mee in wat "gebruikelijk" is.

| Geval (test) | Gewone mediaan | Nieuwe methode |
|---|---|---|
| 10 gewone werkdagen | 2.080 | 2.080 |
| Dezelfde 10 plus 5 storingsdagen (0, 4, 0, 12, 300) | 1.951 | 2.080 |
| 3 gewone dagen en 9 storingsdagen | 0 | 2.070 |
| Storing van 9 werkdagen op rij in een venster van 28 dagen | n.v.t. | alle 9 gemeld, gebruikelijk 2.100 |
| Minder dan 3 volledige dagen | n.v.t. | geen oordeel, geen melding |

Beperking: is de bron het hele venster van 28 dagen gestoord, dan is er geen volledige dag om mee te
vergelijken en volgt er geen melding over onvolledige dagen. De melding "niet ververst" of de
foutstatus van de bron dekt dat geval.

Tests: 66 in totaal (5 nieuw voor dit onderdeel).

## Cache (toegevoegd 16-11-2026, 15:40 uur; werkbranch, nog niet samengevoegd)

### Wat er in de cache staat

Bestand: `cache/ophaalcache.json`, in het repository. De workflow zet het na elke run terug met een
eigen commit ("Cache bijgewerkt [skip ci]").

| Soort | Sleutel | Waarde | Aantal nu |
|---|---|---|---|
| tekst | publicatienummer | de eerste regels van de bekendmaking | 495 |
| perceel | coördinaat | perceelgrootte in m², of "geen perceel" | 39 |
| locatie | gemeente en titel van een bericht zonder locatie | gevonden adres, of "niet gevonden" | 54 |
| gemeente | coördinaat | gemeente op die plek | 31 |
| insolventie | nummer van de rechtbankpublicatie | alleen het oordeel "gelezen, geen bedrijf binnen de straal" | 209 |

Wat er bewust niet in staat: de inhoud van faillissementspublicaties. Die bevatten persoonsgegevens
en de geschiedenis van een repository is blijvend. Een publicatie mét een treffer wordt daarom elke
run opnieuw gelezen. Verandert de straal of het postcodegebied, dan vervallen de bewaarde oordelen.

Niet in de cache: de lijst met publicaties zelf en de dagtelling. Die worden elke run opgevraagd
(30 verzoeken), zodat nieuwe, gemiste en ingetrokken publicaties elke run meekomen.

Mislukte verzoeken worden niet bewaard; de volgende run probeert ze opnieuw. Wat een run niet
gebruikt (publicaties die uit het venster zijn gevallen) verdwijnt bij het opslaan. Het bestand is
284 kB en heeft één regel per vermelding, zodat een dagelijkse commit maar enkele regels wijzigt.

### Meting vóór en na (lokaal, 16-11-2026, 15:35 en 15:37 uur, zelfde stand van de bron)

| Meting | Zonder cache | Met volle cache |
|---|---|---|
| Verzoeken totaal | 849 | 31 |
| waarvan repository.overheid.nl | 734 | 30 |
| waarvan PDOK (percelen, adressen, BAG) | 114 | 0 |
| waarvan Vlaanderen | 1 | 1 |
| Duur | 121 seconden | 24 seconden |
| Berichten | 1.116 | 1.116 |
| Berichten met een verschil | n.v.t. | 0 |
| Volgorde gelijk | n.v.t. | ja |
| Ontwikkellocatie / onzeker / weggefilterd | 81 / 23 / 1.012 | 81 / 23 / 1.012 |

Een eerdere meting om 15:30 en 15:32 uur, vóór de adreslocaties in de cache zaten, gaf 856 tegenover
102 verzoeken en 132 tegenover 69 seconden, ook met 0 verschillen.

Op een gewone dag komen er nieuwe publicaties bij; dan haalt de run alleen die op. Het aantal
verzoeken ligt dan tussen 31 en enkele tientallen meer. Op GitHub is dit nog niet gemeten.

### Volledige verversing

| Wanneer | Hoe |
|---|---|
| Wekelijks | Zondag 03:30 UTC (04:30 of 05:30 uur Nederlandse tijd), in de workflow |
| Handmatig | Tabblad Actions → Dagelijkse verversing → Run workflow → vinkje "Volledige verversing" |
| Lokaal | `python -m signalen.update --volledig` |

Een volledige verversing leest de cache niet, haalt alles opnieuw op en schrijft een verse cache.
Daarmee komen gecorrigeerde teksten binnen. Ingetrokken publicaties verdwijnen al bij elke gewone
run, omdat de lijst met publicaties altijd opnieuw wordt opgevraagd.

### Tests

12 nieuwe tests (78 in totaal). De belangrijkste: dezelfde invoer zonder cache, met lege cache en met
volle cache geeft exact dezelfde uitkomst, en met volle cache wordt er niets opgehaald. Verder: alleen
een nieuwe publicatie wordt opgehaald; een mislukt verzoek komt niet in de cache; een volledige
verversing vervangt een gecorrigeerde tekst; ongebruikte vermeldingen verdwijnen; het bestand is bij
gelijke invoer byte voor byte gelijk; van een faillissementspublicatie staat geen naam, KvK-nummer of
curator in het bestand; een mislukte adrescontrole wordt niet bewaard als "geen treffer".

### Punten om te wegen

| Punt | Toelichting |
|---|---|
| Teksten staan blijvend in de geschiedenis van een openbaar repository | Het gaat om de eerste regels van officiële bekendmakingen (vergunningen, plannen), die de overheid met licentie CC-0 aanbiedt. Geen faillissementsgegevens. Wil Wim dit niet, dan kan de cache in plaats daarvan in de tijdelijke opslag van GitHub Actions; dan staat hij niet in het repository. |
| De workflow schrijft nu naar `main` | Daarvoor is het recht `contents: write` toegevoegd. Lukt het terugzetten niet (bijvoorbeeld omdat er net is samengevoegd), dan geeft de run een waarschuwing en haalt de volgende run het ontbrekende opnieuw op. |
| Bijvangst | De dagelijkse commit telt als activiteit, waardoor GitHub de geplande runs niet na 60 dagen stilte uitzet. |

### Nog te doen

| Punt | Toelichting |
|---|---|
| **Actions-versies (Node) bijwerken** | GitHub waarschuwt in het log dat `actions/checkout@v4`, `actions/setup-python@v5`, `actions/configure-pages@v5` en `actions/upload-pages-artifact@v3` (met daarin `upload-artifact@v4`) op Node.js 20 zijn gebouwd en gedwongen op Node.js 24 draaien. Het werkt nu, maar de versienummers in `.github/workflows/dagelijks.yml` moeten omhoog naar uitgaven die Node.js 24 ondersteunen. Nog niet gedaan. |
| Cache op GitHub controleren | Na samenvoegen: slaagt het terugzetten van de cache, hoeveel verzoeken doet een gewone run, en werkt de handmatige volledige verversing. |

## Cache op GitHub: run 5 en run 6 (toegevoegd 16-11-2026, 17:25 uur)

### Wat er is samengevoegd (PR #5)

| Punt | Uitwerking |
|---|---|
| Cachebestand niet meegeleverd | `cache/ophaalcache.json` was lokaal aangemaakt en is vóór het samenvoegen uit de branch gehaald. De eerste cache is door de workflow zelf geschreven. |
| Eén run tegelijk | `concurrency` met groep `dagelijkse-verversing` en `cancel-in-progress: false`. Een geplande, handmatige of merge-run wacht tot de lopende run klaar is. GitHub houdt per groep één wachtende run vast; komt er nog een bij, dan vervalt de oudste wachtende. |
| Actuele stand ophalen | De checkout neemt de laatste stand van de branch en niet de commit waarmee de run is aangevraagd. Een run die heeft gewacht krijgt zo de cache van de run vóór hem. |
| Alleen vanaf `main` | De stap die de cache terugzet draait alleen op `main`. |
| Manier van samenvoegen | Squash, zodat de commit waarin het lokale cachebestand stond niet in de geschiedenis van `main` komt. |

### Meting

| | Run 5 | Run 6 | Lokaal, met de cache van `main` na run 6 |
|---|---|---|---|
| Tijdstip | 15:42 uur | 17:21 uur | 17:24 uur |
| Aanleiding | samenvoegen van PR #5 | handmatig gestart door Wim | controle door Claude Code |
| Cache bij de start | geen | die van run 5 | die van run 6 |
| Verzoeken totaal | 1.056 | 98 | 34 |
| waarvan repository.overheid.nl | 940 | 94 | niet uitgesplitst |
| waarvan PDOK | 112 | 2 | niet uitgesplitst |
| waarvan Vlaanderen | 4 (mislukt) | 2 | niet uitgesplitst |
| Teksten: uit cache / opgehaald | 0 / 495 | 495 / 0 | 495 / 0 |
| Perceelgroottes: uit cache / opgehaald | 0 / 40 | 40 / 0 | 40 / 0 |
| Rechtbankpublicaties: uit cache / gelezen | 0 / 157 | 157 / 49 | 206 / 3 |
| Geweigerde verzoeken (HTTP 429) bij teksten | 43, alle 43 hersteld | 0 | 0 |
| Teksten of perceelgroottes die ontbreken | 0 | 0 | 0 |
| Duur stap "Berichten ophalen" | 7 minuten 56 | 58 seconden | 30 seconden |
| Duur hele run | 8 minuten 30 | 2 minuten 0 | n.v.t. |
| Cache teruggezet in `main` | ja, commit `9e76b01` | ja, commit `3b28c5e` (49 regels erbij) | n.v.t. (niets vastgelegd) |
| Berichten | 1.107 | 1.116 | 1.116 |
| Ontwikkellocatie / onzeker / weggefilterd | 78 / 23 / 1.006 | 81 / 23 / 1.012 | niet vergeleken |

Feiten:

- Het terugzetten van de cache is in beide runs geslaagd. De commit is van `github-actions[bot]` en
  heet "Cache bijgewerkt [skip ci]".
- Run 6 heeft geen enkele tekst, perceelgrootte of adreslocatie opnieuw opgehaald. De cache wordt
  dus gebruikt.
- Run 6 deed 98 verzoeken en niet rond de dertig. De 49 rechtbankpublicaties die run 5 niet had
  gelezen, zijn in run 6 alsnog gelezen. Daarna bleven er 3 ongelezen; die las de lokale run.
- Met de cache van `main` zoals die nu is, doet een run 34 verzoeken (lokaal gemeten).
- Het verschil van 9 berichten tussen run 5 en run 6 zijn de 9 Vlaamse berichten. De Vlaamse bron
  was in run 5 onbereikbaar en in run 6 niet.

Vermoedens:

- Een derde run op GitHub komt rond de 34 verzoeken uit. Dat is lokaal gemeten, niet op GitHub.
- Van de 94 verzoeken aan repository.overheid.nl in run 6 zijn er ongeveer 30 voor de lijsten en de
  dagtelling en 49 voor rechtbankpublicaties. De overige circa 15 zijn waarschijnlijk herhaalde
  pogingen na een weigering. `main` telt dat voor rechtbankpublicaties nog niet.
- Run 5 duurde lang door het wachten na de 43 weigeringen en door de 52 rechtbankpublicaties die
  na vier pogingen werden opgegeven. De wachttijd zelf staat niet in het log.

Niet vastgesteld: waarom de geplande run van 16:10 uur niet is gestart. Tot 17:25 uur is er geen
enkele geplande run geweest; alle zes de runs zijn gestart door samenvoegen of met de hand. Bekend
is dat GitHub geplande runs bij drukte later start of overslaat.

### Twee gebreken gevonden in run 5

| Gebrek | Gevolg in run 5 | Stand |
|---|---|---|
| Uitval van een bron stond alleen op het tabblad Bronnen | De Vlaamse bron gaf een naamfout op de GitHub-machine ("Temporary failure in name resolution", vier pogingen). 9 Vlaamse berichten ontbraken zonder melding bij de berichten. | Hersteld op de werkbranch: de app meldt een onbereikbare bron boven de berichten en het log krijgt een waarschuwing. In run 6 was de bron weer bereikbaar. |
| Niet gelezen rechtbankpublicaties werden niet geteld | 52 van de 209 publicaties zijn niet gelezen; in run 6 nog 3. Ze kwamen niet in de cache, dus een volgende run leest ze alsnog. Er was geen melding. | Hersteld op de werkbranch: zelfde manier van opnieuw proberen als bij teksten, telling in de gegevens, waarschuwing in het log en melding in de app. |

De herstelcode staat op de werkbranch (commit `ab0318f`, 80 tests geslaagd) en is niet samengevoegd
met `main`. De live app heeft deze meldingen dus nog niet.

### Waarom de cache in `main` staat, en de alternatieven

Wim vroeg de cache in het repository te bewaren. Binnen het repository is gekozen voor `main`.

| Mogelijkheid | Voor | Tegen |
|---|---|---|
| **Commit in `main` (gekozen)** | Eén plek. De inhoud is in te zien en elke wijziging is na te gaan. Verloopt niet. Een lokale run gebruikt dezelfde cache. Geen extra stappen in de workflow. | Per run waarin de cache verandert een commit van de robot in de geschiedenis van `main` (vier geplande runs per werkdag, dus meestal een tot vier commits per dag). De teksten staan blijvend in de geschiedenis van een openbaar repository. De workflow heeft schrijfrecht op `main` nodig. Een werkbranch loopt na elke run achter op `main`. |
| Aparte branch alleen voor de cache | De geschiedenis van `main` blijft schoon. De branch kan telkens worden overschreven, zodat oude teksten niet blijven staan. | Twee checkouts in de workflow. Een lokale run heeft de cache niet vanzelf. Nog steeds openbaar. |
| Tijdelijke opslag van GitHub Actions (`actions/cache`) | Staat niet in het repository en niet in de geschiedenis. | Niet in te zien. Vervalt na 7 dagen zonder gebruik en kan door GitHub worden opgeruimd. Een bewaarde cache kan niet worden overschreven, dus elke run heeft een nieuwe sleutel nodig. Lokaal niet beschikbaar. Voldoet niet aan "in het repository". |
| Artifact van de vorige run | Staat niet in de geschiedenis. | De run moet het artifact van een eerdere run opzoeken en downloaden; bewaartermijn hoogstens 90 dagen. Breekbaar als een run mislukt. |
| De vorige publicatie op Pages teruglezen | Geen schrijfrecht nodig. | De cache moet dan openbaar op de site staan. Na een mislukte publicatie is de keten gebroken. |
| Geen cache | Eenvoudigst. | 1.056 verzoeken en ruim 8 minuten per run, met weigeringen door de bron (run 5). |

Advies van Claude Code: laten staan in `main`. Storen de commits van de robot in de geschiedenis,
dan is de aparte branch de kleinste stap; die houdt de cache in het repository.

Twee dingen om te weten bij de gekozen opzet:

- De commit van de robot start zelf geen nieuwe run ("[skip ci]", en GitHub start geen runs op
  commits van de eigen workflow).
- Het cachebestand is van de workflow. Een pull request moet het niet wijzigen, anders botst hij
  met de commit van de robot. De werkbranch raakt het bestand niet aan.

### Nog te doen (stand 17:25 uur)

| Punt | Toelichting |
|---|---|
| Herstel van de twee gebreken samenvoegen | Staat op de werkbranch, samen met deze aanvulling op het verslag. Er is nog geen pull request; Wim beslist. |
| Derde run op GitHub | Om de circa 34 verzoeken op GitHub zelf te zien. Start vanzelf bij de volgende geplande of handmatige run. |
| Geplande runs volgen | Nagaan of de run van morgenochtend (08:40 of 09:40 uur) vanzelf start. |
| Volledige verversing op GitHub | Handmatig (vinkje "Volledige verversing") en wekelijks (zondag) zijn nog niet uitgevoerd. |
| **Actions-versies (Node) bijwerken** | Ongewijzigd open; de waarschuwing stond ook in het log van run 6. Zie "Nog te doen" onder "Cache". |

## Schema, run 7 en rechtbankpublicaties (toegevoegd 16-11-2026, 17:40 uur)

### Waarom de geplande run van 16:10 uur niet is gestart

| Vraag | Uitkomst |
|---|---|
| Cron-regel | `10 15 * * 1-5` |
| Tijdzone | UTC. Zonder aanduiding rekent GitHub in UTC. |
| Tijd in Amsterdam | 16:10 uur in de winter (nu), 17:10 uur in de zomer |
| Staat het schema op `main`? | Ja. De regel staat er sinds de eerste versie (PR #1, 12:32 uur) en is door PR #5 niet gewijzigd. `main` is de standaardbranch; GitHub draait geplande runs alleen vanaf die branch. |
| Is de workflow actief? | Ja, status "active". |
| Liep er op dat moment een andere run? | Nee. Run 5 was om 15:50 uur klaar, run 6 begon om 17:21 uur. De concurrency-regel heeft dus niets tegengehouden. |
| Aantal geplande runs tot 17:38 uur | 0. Alle zeven runs zijn gestart door samenvoegen of met de hand. |

Feit: het schema stond goed en op de juiste plek; de run is door GitHub niet gestart. Het was het
enige geplande moment sinds de workflow bestaat (het moment van 12:10 uur viel vóór het samenvoegen
van PR #1).

Niet vastgesteld: de oorzaak. GitHub geeft geen log van een run die niet is gestart. De
documentatie van GitHub zegt dat geplande runs bij drukte later starten en dat ze bij grote drukte
kunnen vervallen. Of dat hier speelde, of dat een nieuw schema pas na enige tijd gaat lopen, is niet
na te gaan. Of geplande runs hier wel werken, blijkt pas als de eerste is gestart.

### Schema van de geplande runs

Gemeten bij de bron (tijdstip van publicatie per Gemeenteblad-bericht, landelijk):

| Dag | Publicaties | Vroegste | Midden | 95% binnen | Later op de dag |
|---|---|---|---|---|---|
| Donderdag 12-11 | 2.630 | 09:07 | 09:14 | 09:20 | 3 (10, 11 en 14 uur) |
| Vrijdag 13-11 | 2.083 | 09:08 | 09:14 | 09:20 | 0 |
| Maandag 16-11 | 2.147 | 09:00 | 09:06 | 09:12 | 1 (12:53 uur) |

De bron publiceert dus één keer per werkdag, tussen 09:00 en 09:21 uur. Berichten van vandaag kunnen
niet eerder in de app staan dan kort daarna.

Nieuw schema, in Nederlandse tijd (`timezone: "Europe/Amsterdam"` bij elke regel, zomer en winter
gelijk):

| Tijd | Dagen | Doel |
|---|---|---|
| 06:45 uur | ma–vr | Alles tot en met gisteren staat klaar bij het opstaan, inclusief wat een eerdere run miste. |
| 09:35 uur | ma–vr | De publicaties van vandaag. |
| 10:20 uur | ma–vr | Vangnet voor de ochtend. Vanaf 10 uur beoordeelt de dagcontrole ook de lopende dag. |
| 12:10 uur | elke dag | Vangnet, ook in het weekend. |
| 16:10 uur | ma–vr | Publicaties die later op de dag verschijnen. |
| 04:30 uur | zondag | Wekelijkse volledige verversing (cache negeren). |

Wat dit betekent voor de ochtend: om 06:45 uur is de app bij tot en met de vorige werkdag; de
berichten van de dag zelf staan er rond 09:40 uur in. Eerder kan niet, omdat de bron ze dan nog niet
heeft. De minuten liggen bewust niet op het hele uur, omdat GitHub het daar het drukst heeft.

Meer runs dan strikt nodig, omdat GitHub een geplande run kan overslaan. Een run met cache kost
ongeveer 34 verzoeken en anderhalve minuut.

De wekelijkse volledige verversing wordt herkend aan de klok (een geplande run op zondag vóór 9 uur
Nederlandse tijd) en niet meer aan de tekst van de cron-regel.

Herkomst van `timezone`: de documentatie van GitHub (Workflow syntax, `on.schedule`): "By default,
scheduled workflows run in UTC. You can optionally specify a timezone using an IANA timezone string".

Nog niet bewezen: dat een geplande run met dit schema ook werkelijk start. De eerste kans is
dinsdag 17-11 om 06:45 uur.

### Run 7 (na het samenvoegen van PR #6, 17:34 uur)

| | Run 7 |
|---|---|
| Verzoeken totaal | 34 (repository.overheid.nl 33, Vlaanderen 1) |
| Teksten: uit cache / opgehaald | 495 / 0 |
| Perceelgroottes: uit cache / opgehaald | 40 / 0 |
| Rechtbankpublicaties: uit cache / gelezen | 206 / 3 |
| Mislukt in de eerste ronde (tekst, perceel, rechtbankpublicatie) | 0 / 0 / 0 |
| Duur stap "Berichten ophalen" | 34 seconden |
| Duur hele run | 1 minuut 29 |
| Cache teruggezet in `main` | ja, commit `0e7cec1` (3 regels erbij; 209 rechtbankpublicaties) |
| Berichten | 1.116 (ontwikkellocatie 81, onzeker 23, weggefilterd 1.012) |
| Bronnen | alle drie bereikbaar |

Reeks van vandaag: 1.056 verzoeken zonder cache (run 5), 98 (run 6), 34 (run 7).

### Run 8 (na het samenvoegen van PR #7, 17:38 uur; toegevoegd 17:45 uur)

| | Run 8 |
|---|---|
| Verzoeken totaal | 31 (repository.overheid.nl 30, Vlaanderen 1) |
| Teksten, perceelgroottes, rechtbankpublicaties opgehaald | 0 / 0 / 0 (alles uit de cache: 495, 40 en 209) |
| Mislukte verzoeken | 0 |
| Duur stap "Berichten ophalen" | 24 seconden |
| Duur hele run | 52 seconden |
| Cache teruggezet in `main` | niet nodig: de cache was ongewijzigd, dus geen commit |
| Berichten | 1.116 (ontwikkellocatie 81, onzeker 23, weggefilterd 1.012) |

Reeks van vandaag: 1.056 verzoeken zonder cache (run 5), 98 (run 6), 34 (run 7), 31 (run 8). De 31
zijn gelijk aan de lokale meting met volle cache.

### De drie overgebleven rechtbankpublicaties

| Publicatie | Rechtbank | Datum | Run 5 | Run 6 | Run 7 | Lokaal (17:35 uur) |
|---|---|---|---|---|---|---|
| stcrt-2026-38162 | Noord-Holland | 28-10-2026 | niet gelezen | niet gelezen | gelezen | gelezen, eerste poging |
| stcrt-2026-38802 | Noord-Nederland | 02-11-2026 | niet gelezen | niet gelezen | gelezen | gelezen, eerste poging |
| stcrt-2026-40679 | Den Haag | 16-11-2026 | niet gelezen | niet gelezen | gelezen | gelezen, eerste poging |

Feiten:

- Het zijn dezelfde drie in run 5 en run 6. Dat kan ook niet anders: run 6 vroeg alleen op wat run 5
  niet had gelezen.
- In run 7 zijn ze alle drie bij de eerste poging gelezen, zonder fout. Ze staan nu in de cache.
- Aan de publicaties zelf is niets bijzonders: gewone omvang (8 tot 10 kB, 5 tot 12 vermeldingen),
  drie verschillende rechtbanken en data, geen bedrijf binnen het postcodegebied.
- Een foutmelding van run 5 en run 6 is er niet. De code op `main` telde en logde mislukte
  rechtbankpublicaties toen nog niet; dat doet ze pas sinds PR #6, en run 7 had geen fouten.

Vermoeden: in run 5 en 6 weigerde de bron ze met HTTP 429 (te veel verzoeken), net als de 43 teksten
in run 5. Daarvoor pleit dat run 6 ongeveer 15 verzoeken meer deed dan nodig en dat het bij een
rustige run (3 verzoeken in plaats van 49 of 209) meteen lukte.

Sinds PR #6 staat een volgende keer de oorzaak in het log, in de gegevens en in de app.

### Nog te doen (stand 17:40 uur)

| Punt | Toelichting |
|---|---|
| Eerste geplande run afwachten | Dinsdag 17-11, 06:45 en 09:35 uur. Start er geen, dan werkt het schema bij GitHub niet en is een andere aanjager nodig (bijvoorbeeld een externe dienst die de workflow op tijd start). |
| Volledige verversing op GitHub | Handmatig en wekelijks (zondag 04:30 uur) nog niet uitgevoerd. |
| **Actions-versies (Node) bijwerken** | Ongewijzigd open. |

## Onvolledige dagen en inhalen (toegevoegd 16-11-2026, 15:00 uur)

| Onderdeel | Uitwerking |
|---|---|
| Gemiste dagen alsnog ophalen | Elke verversing haalt het hele venster opnieuw op (vergunningen 42 dagen) en onthoudt niets. Een dag die de bron miste, komt daardoor binnen bij de eerste verversing waarin de bron hem wel heeft. Dit was al zo; het is nu vastgelegd in een test. |
| Onvolledige dag herkennen | Per werkdag in de laatste 28 dagen telt de app het aantal Gemeenteblad-publicaties dat de zoekdienst kent. Een dag in de laatste 14 dagen met minder dan de helft van het gebruikelijke aantal (de mediaan) geldt als onvolledig. |
| Niet beoordeeld | Weekenden, feestdagen (Nieuwjaar, tweede paasdag, Koningsdag, 5 mei, Hemelvaart, tweede pinksterdag, Kerst) en de lopende dag vóór 10 uur. |
| Melding in de app | "De gegevens van maandag 16 november zijn onvolledig: de bron gaf 0 van de gebruikelijke circa 2.097 publicaties door." Bij sorteren op datum staat "onvolledig" ook bij de dag. |
| Storing zonder verversing | Is het gegevensbestand ouder dan 26 uur, dan meldt de app dat er niet ververst is. Faalt de hoofdbron helemaal, dan publiceert de workflow niets en blijft de vorige versie staan. |

Referentie (15:01 uur): Gemeenteblad per werkdag tussen 1.860 en 2.973, mediaan 2.097; 16-11 staat op 0.

Tests: 12 nieuwe (61 in totaal), waaronder een dag met 4 in plaats van ruim 2.000 publicaties, een
half geleverde dag, weekend en Kerst, en twee opeenvolgende runs waarin de gemiste dag in de tweede
run binnenkomt en de melding verdwijnt.

Beperking: een nieuwe, onbekende feestdag of een dag waarop gemeenten uit zichzelf weinig
publiceren kan onterecht als onvolledig worden gemeld. De melding noemt daarom de aantallen.

## Getest

| Wat | Hoe | Uitkomst |
|---|---|---|
| Regels | 28 nieuwe unittests: elke regel, elk signaal, de drempel van 400 m² (399 valt af, 400 telt), rangorde plan > woningen > signaal, strafpunten, één zin per oordeel | Geslaagd |
| Privacyfilter faillissementen | Tests met een particulier, een eenmanszaak, een vof, een schuldsanering, een woonadres en een curatornaam | Geen van alle komt in de gegevens |
| Verrijking | Tests met nagebootste tekst- en perceeldienst: perceel wordt alleen opgezocht waar het de uitkomst bepaalt; zonder tekst of perceel wordt het "onzeker" | Geslaagd |
| Echte gegevens | Drie volledige runs; top, midden en onderkant van de ranglijst en een steekproef uit "weggefilterd" nagelopen | Eén fout gevonden en hersteld: een huisnummer werd als aantal woningen gelezen ("Bredaseweg 90 bouwen 12 appartementen" gaf 90) |
| App | Chromium op telefoonformaat, licht en donker: volgorde aflopend op score, tabblad Onzeker, schakelaar weggefilterd, filters op soort en signaal, sorteren op datum | Werkt, geen fouten in de console |

## Bekende beperkingen

| Punt | Toelichting |
|---|---|
| Aantal woningen is het grootste genoemde getal | "19 woningen en 98 appartementen" telt als 98, niet 117. Optellen gaat mis bij "sloop van 2 en nieuwbouw van 14". |
| Perceelgrootte is één kadastraal perceel | Bij projecten over meer percelen is de werkelijke omvang groter. Bij verkoop van een deel van een perceel is ze kleiner; de zin zegt daarom "of een deel daarvan". |
| Planberichten zonder ontwikkelwoorden in de eerste 1.500 tekens | Die staan onder "Onzeker" (12 stuks), ook als verderop wel staat wat er mogelijk wordt. |
| Afwijken van het omgevingsplan | Telt als bestemmingswijziging, behalve als het alleen om klein werk gaat (dakkapel, schutting, carport en dergelijke). Dat is een keuze; de schakelaar laat zien wat daardoor afvalt. |
| Woningsplitsing | Telt niet als nieuwbouw en is geen signaal; staat onder "weggefilterd". |
| Eén locatie, meer berichten | Aanvraag, verlenging en besluit voor dezelfde locatie staan los van elkaar in de lijst. |
| Faillissement zegt niets over eigendom | Of het bedrijf eigenaar of huurder van het pand is, is niet bekend. |
| De workflow met de nieuwe stappen is niet op GitHub uitgevoerd | Dat kan pas na samenvoegen met `main`. Lokaal draait alles; de run duurt nu ongeveer 85 seconden. |

## Buiten dit verslag

- **Samenvoegen met `main` is niet gedaan.** De live app toont nog de eerste versie. Wim beslist of en wanneer er een pull request komt.
- **Webservice Insolventieregister.** Kan alleen Wim aanvragen (ondertekende overeenkomst). Voegt weinig toe zolang de Staatscourant-route werkt.
- **Biedboek.** Navragen bij het Rijksvastgoedbedrijf of geautomatiseerd uitlezen mag; daarna pas bouwen.
- **Bewust niet gedaan:** pdf's van oudere faillissementspublicaties lezen, commerciële vastgoedsites uitlezen, eigenaren of KvK-gegevens opvragen, berichten per locatie samenvoegen.
- **De regels zijn een eerste afstelling.** De schakelaar "Toon ook wat is weggefilterd" is bedoeld om te controleren of er te veel of te weinig afvalt; bijstellen kan in `signalen/relevantie.py`.
