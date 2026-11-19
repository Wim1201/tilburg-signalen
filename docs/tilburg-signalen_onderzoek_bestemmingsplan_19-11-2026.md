# Onderzoek: bestemmingsplan op het tabblad Adres (19-11-2026)

Stap 1 van de taak "bestemmingsplan en omgevingsplan op het tabblad Adres". Alleen onderzoek, nog niets gebouwd.

## Welke dienst

| Dienst | Sleutel | Uitkomst |
|---|---|---|
| PDOK WMS Ruimtelijke plannen: `https://service.pdok.nl/kadaster/plu/wms/v1_0` | Nee | Werkt. GetFeatureInfo per punt (RD-coördinaten, EPSG:28992). Licentie CC0, geen kosten. |
| PDOK WFS Ruimtelijke plannen (`.../plu/wfs/v1_0`, `.../ruimtelijkeplannen/...`) | - | 404, bestaat (niet meer). |
| Oude adres `geodata.nationaalgeoregister.nl/plu/wfs` | - | Niet bereikbaar. |
| DSO Ruimtelijke Plannen API v4 (`ruimte.omgevingswet.overheid.nl`) | Ja | 401 zonder sleutel. Valt nu af. |

CORS: de WMS stuurt `Access-Control-Allow-Origin: *`. De browser kan de dienst dus rechtstreeks aanroepen, net als de Locatieserver, BAG en de kadastrale kaart die de app al gebruikt.

## Bruikbare lagen

`enkelbestemming`, `dubbelbestemming`, `bouwvlak`, `maatvoering`, `functieaanduiding`, `bouwaanduiding`, `gebiedsaanduiding`, `bestemmingsplangebied`.

Per object onder meer: `naam` (bijv. "Wonen", "Centrum-Binnenstad"), `planstatus`, `dossierstatus`, `datum`, `typeplan`, `versieimro`, `dossierid`, `verwijzingnaartekst` (link naar het artikel in de regels op ruimtelijkeplannen.nl; getest, opent), `historisch`.

Maatvoering staat als tekst, bijvoorbeeld:
`"maximum bebouwingspercentage terrein (%)"="75", "maximum bouwhoogte (m)"="15"`.

## Voorbeeld: Stadhuisplein 130 (openbaar adres)

- Enkelbestemming: Centrum-Binnenstad, plan "Binnenstad 2010" (2012), onherroepelijk.
- Maatvoering: maximum bouwhoogte 40 m. Bouwvlak: ja.
- Dubbelbestemmingen (paraplu): Parkeren, Terrassen, Appartementen, Flitsbezorging (TAM-omgevingsplan, vastgesteld 31-3-2025), plus een ontwerp en een voorontwerp.
- Gebiedsaanduidingen: waterbergingseis, luchtvaartverkeerzone.

Let op: ook enkele besluiten na 1-1-2024 staan erin (TAM-omgevingsplannen in IMRO). Wijzigingen van het omgevingsplan die via het DSO in STOP/TPOD zijn gepubliceerd, staan er niet in.

## Steekproef (80 adrespunten in de gemeente Tilburg, alleen tellingen bewaard)

| | Aantal |
|---|---|
| Met een geldende enkelbestemming | 74 van 80 |
| Met twee of meer geldende enkelbestemmingen (overlappende plannen) | 5 |
| Met een bouwvlak | 59 |
| Met maatvoering op de kaart | 31 |
| Daarvan met bouwhoogte | 28 |
| Daarvan met bebouwingspercentage | 6 |

Conclusie: de bestemming is bijna altijd beschikbaar. De getallen staan bij ongeveer 6 van de 10 adressen niet op de kaart maar alleen in de regels (tekst). Bij oude plannen (IMRO2006, "bestemmingsplan artikel 10", status "vigerend") ontbreken ze vrijwel altijd.

Planstatussen die voorkwamen: onherroepelijk, vastgesteld, vigerend, geconsolideerd, ontwerp, voorontwerp. "Vastgesteld" kan nog in beroep zijn; `dossierstatus` zegt meer ("geheel onherroepelijk in werking").

## Techniek

- Formaat `application/json` bevat de hele vorm van het plangebied: tot 650-930 kB per laag bij paraplu­plannen. Te zwaar voor een iPhone.
- Formaat `text/plain` geeft dezelfde velden zonder vorm: circa 5 kB. Het is wel MapServer-eigen tekst die we zelf moeten ontleden.
- Snelheid: gemiddeld 0,4 s, hoogstens 0,7 s per laag (gemeten vanuit de cloud, niet vanaf een iPhone).

## Keuzes voor Wim

1. Waar ophalen
   - a. Rechtstreeks vanuit de browser, `text/plain` (advies: geen extra Worker, geen deploy, PDOK is al een bron).
   - b. Via een eigen Cloudflare Worker die JSON zonder vorm teruggeeft (netter, maar Wim moet deployen en onderhouden).
2. Wat tonen
   - a. Alleen de enkelbestemming van het nieuwste geldende plan, met getallen en link naar het regelsartikel (advies).
   - b. Als a, plus de namen van dubbelbestemmingen en gebiedsaanduidingen als korte lijst.
   - c. Alles, ook ontwerp- en voorontwerpplannen (apart gemarkeerd).
3. Als er geen getallen op de kaart staan
   - a. Melden "Geen getallen op de kaart; zie de regels" met link naar het artikel (advies).
   - b. Getallen uit de regels-HTML halen (foutgevoelig, per gemeente anders; afraden).

## Niet gecontroleerd

- Snelheid en werking vanaf een iPhone (Safari).
- Of PDOK deze WMS blijft aanbieden en hoe vaak hij wordt bijgewerkt; er is geen einddatum gevonden, maar ook geen garantie.
- Of de steekproef representatief is: 80 punten, verdeeld over adressen die de Locatieserver op volgorde gaf, niet echt willekeurig.
- Gemeenten buiten Tilburg.
- Juridische volledigheid: welk plan voorgaat bij overlap is uit deze gegevens niet altijd zeker af te leiden.
