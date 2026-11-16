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
| 16-11-2026, ca. 12:35 uur | Het vorige verslag noemt de livegang als open punt. Dat is achterhaald: PR #1 is samengevoegd, Wim heeft GitHub Pages aangezet en `https://wim1201.github.io/tilburg-signalen/` geeft de app. Die draait nog op de eerste versie tot deze branch is samengevoegd. |
| 16-11-2026, ca. 13:00 uur | Het vorige verslag noemt de hoofdbron en PDOK "openbaar, geen sleutel" zonder de robots.txt te noemen. Aanvulling: `repository.overheid.nl/robots.txt` bevat `Disallow: /` en `api.pdok.nl/robots.txt` sluit de Locatieserver uit. Dat zijn aanwijzingen voor zoekmachines. De app gebruikt de gedocumenteerde koppelingen die de beheerders juist voor geautomatiseerd gebruik aanbieden (zie "Wat mag"). Het punt staat hier zodat Wim het zelf kan wegen. |
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
