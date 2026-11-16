# Tilburg Signalen: verslag versie 2, eigen huisstijl en ochtendscherm

| | |
|---|---|
| Datum | 16-11-2026, 18:29 – 18:55 uur |
| Versie | versie 2 van de app, branch `claude/awesome-brown-i18j4o`, gestart vanaf `main` op commit `b315ab0` (na PR #7) |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | `site/data/berichten.json` zoals het in de repo staat (bijgewerkt 16-11-2026, 15:37 uur); er is niets opnieuw opgehaald |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_ontwikkellocaties_16-11-2026.md` |

## Correcties en aanvullingen op het vorige verslag

| Tijdstip | Wat |
|---|---|
| 16-11-2026, 18:45 uur | **De beschrijving van de app onder "Wat er is veranderd" en "Getest → App" in het vorige verslag geldt niet meer letterlijk.** "Tabblad Onzeker" is nu de tegel Onzeker. De schakelaar "Toon ook wat is weggefilterd" staat nu in het filterpaneel (nog steeds op het tabblad Berichten). Het label "relevantie 108" op de kaart is vervangen door het rangnummer; de score staat onder Details. |
| 16-11-2026, 18:45 uur | **Het eerste scherm toont 10 berichten in plaats van 60.** De knop "Toon alle 81 ontwikkellocaties" toont de rest in één keer. Weggefilterde berichten komen nog per 60. |
| 16-11-2026, 18:45 uur | **Het getal "nieuw sinds vorig bezoek" telt anders.** In versie 1 was het ontwikkellocaties plus onzeker samen. Nu telt de tegel Nieuw alleen ontwikkellocaties; nieuwe onzekere berichten staan op de tegel Onzeker ("Onzeker · 1 nieuw"). Het vinkje "Alleen nieuw sinds mijn vorige bezoek" in het filterpaneel is vervallen; de tegel Nieuw doet hetzelfde voor ontwikkellocaties. Voor onzekere berichten is er geen filter "alleen nieuw" meer; ze dragen wel het label Nieuw. |
| 16-11-2026, 18:45 uur | **Bij een bericht zonder exacte locatie staat geen afstand meer op de kaart.** Versie 1 toonde het getal (bijvoorbeeld 0,0 km voor de hele gemeente Tilburg) met de toelichting eronder. Nu staat er "geen exacte locatie"; het getal en de toelichting staan onder Details. Sorteren en filteren op afstand rekenen nog met hetzelfde getal. |
| 16-11-2026, 18:45 uur | **Kostenraming ElevenLabs was te laag; zie "ElevenLabs".** De raming vooraf (970 credits voor vier varianten) gold voor een ander model dan waarmee daarna is gegenereerd. Werkelijk verbruik: 12.726 credits. |

De gegevens en de regels zijn niet gewijzigd: `signalen/`, `config.json`, `site/data/` en `cache/`
zijn onaangeroerd (`git diff` leeg). De tekst van de regels op het tabblad Bronnen is letterlijk
gelijk gebleven.

## Opdracht

Versie 2 met een eigen huisstijl. De gebruiker is een projectontwikkelaar die elke ochtend in een
minuut wil zien welke ontwikkellocaties er zijn. Hoogste rang bovenaan, per bericht één zin waarom
het relevant is. Beeldmerk en eventuele illustraties met ElevenLabs Image Gen. Gegevens en regels
ongewijzigd, tests voor wat is aangepast.

## ElevenLabs

| Tijdstip | Handeling | Uitkomst |
|---|---|---|
| 18:30 uur | Bereikbaarheid gecontroleerd vóór enig ander werk | Bereikbaar via de ElevenLabs-koppeling van deze sessie. Een kostenraming (zonder iets te genereren) kwam terug: 970 credits voor vier varianten met model `recraft-v4.1`. Rechtstreeks op `api.elevenlabs.io/v1/` antwoordt de dienst ook, maar de sleutel mist daar leesrechten (`user_read`, `models_read`); dat pad is niet gebruikt. |
| 18:32 uur | Beeldmerk: vier varianten, model `recraft-v4.1-pro-vector` | Vier SVG's. Variant 2 gekozen: de dikste lijn, leesbaar op 32 pixels. Kosten 4 × 2.121 = 8.484 credits. |
| 18:33 uur | Illustratie "ochtend": twee varianten, zelfde model | Twee SVG's. Variant 1 gekozen: vlak, zonder kleurverloop, de zon met ringen sluit aan op het beeldmerk. Kosten 2 × 2.121 = 4.242 credits. |

| Meting | Waarde |
|---|---|
| Verbruik vóór / na (accountteller) | 5.232 / 17.958 van 110.153 credits |
| Verbruik deze sessie | 12.726 credits, volgens ElevenLabs ongeveer 2,31 dollar |
| Niet gebruikte varianten | 3 van het beeldmerk, 1 van de illustratie; ze staan in de ElevenLabs-geschiedenis van het account |

**Fout van mijn kant:** de raming vooraf was gemaakt met het gewone model. Het vectormodel, dat ik
daarna koos omdat het echte SVG levert, kost ruim het achtvoudige per afbeelding. Ik heb voor dat
model geen nieuwe raming opgevraagd. Het bedrag is klein, maar de raming die ik zag was niet de
raming van wat ik uitvoerde.

Door de proeframing van 18:30 uur staat er één lege werkstroom (flow) in het ElevenLabs-account,
zonder gegenereerde afbeelding. Naast de twee werkstromen met de afbeeldingen zijn dat er drie.

### Wat er met de gegenereerde bestanden is gedaan

| Bestand in de app | Herkomst | Bewerking |
|---|---|---|
| `site/icons/beeldmerk.svg` | Beeldmerk variant 2 | Witte achtergrond weggehaald, uitgesneden op de ruit, buiten- en binnenruit samengevoegd tot één vorm met een echt gat, kleuren gezet op nachtblauw `#0c1049` en signaaloranje `#f23d0c` |
| `site/icons/icon.svg`, `icon-192.png`, `icon-512.png` | Zelfde tekening | Op een nachtblauw vlak, ruit in papierkleur, signaal in `#ff5226`; de PNG's zijn daarvan gerenderd met Chromium |
| Kopbalk in `site/index.html` | Zelfde tekening | Als SVG in de pagina, zodat de ruit de tekstkleur van de balk volgt |
| `site/img/ochtend.svg`, `ochtend-donker.svg` | Illustratie variant 1 | Achtergrond weggehaald, uitgesneden op de strook met de skyline, kleuren omgezet naar de huisstijl; de donkere versie heeft lichte gebouwen op de donkere achtergrond |

De vormen zelf zijn niet aangepast. De originelen van ElevenLabs staan ongewijzigd in
`docs/huisstijl/`, inclusief de herkomstgegevens (C2PA) die ElevenLabs erin zet. In de bestanden
van de app zijn die herkomstgegevens weggelaten: ze maken het beeldmerk 26 kB in plaats van 3 kB.

## Wat er is veranderd

### Het ochtendscherm

| Onderdeel | Versie 1 | Versie 2 |
|---|---|---|
| Bovenaan | Drie getallen en "Laatste publicatiedag" | Eén zin: "3 nieuwe ontwikkellocaties sinds je vorige bezoek." (of "Geen nieuwe …"), met dag en groet erboven |
| Kiezen van de lijst | Twee knoppen (Ontwikkellocaties, Onzeker), losse schakelaar, vinkje "alleen nieuw" | Drie tegels met het aantal erin: Ranglijst, Nieuw, Onzeker |
| Kaart | Labels, afstandsbord, zin, titel, omschrijving, locatie, bron en links: alles open | Rangnummer, de zin waarom, titel (twee regels), plaats · afstand · datum, labels. Omschrijving, score, bron en links achter "Details" |
| Volgorde op de kaart | Labels eerst, dan de zin | De zin waarom is het eerste dat er staat |
| Rang | Alleen de score ("relevantie 108") | Plaats in de rangorde: 1 is de hoogste. Het nummer hoort bij het bericht en verandert niet door filteren of anders sorteren |
| Eerste scherm | 60 berichten | Top 10, daarna "Toon alle 81 ontwikkellocaties" |
| Niets nieuws | Lege lijst met een regel tekst | Illustratie, "Niets nieuws sinds je vorige bezoek", knop naar de ranglijst |
| Filters | Knop Filters, schakelaar weggefilterd erbuiten | Alles in het filterpaneel; de knop toont hoeveel filters aan staan ("Filters · 2") |

Standaard opent de app op de Ranglijst: alle ontwikkellocaties, hoogste rang bovenaan, nieuwe
berichten gemarkeerd met een oranje rand en het label Nieuw. De tegel Nieuw toont alleen de nieuwe,
ook in rangorde.

### Rang

De rang op de kaart is de plaats in de volgorde die de app al had: hoogste score eerst, bij gelijke
score het nieuwste bericht, daarna het dichtstbijzijnde. Ontwikkellocaties en onzekere berichten
hebben elk hun eigen telling. Weggefilterde berichten hebben geen rang (streepje).

De vijf rangen uit de regels (planwijziging, woningen, verkoop, signaal op perceel, faillissement)
staan niet in de gegevens; alleen de score staat erin, en de scores van rang 1 en rang 2
overlappen (92–108 en 75–100). De app kan dus niet tonen "dit is een rang 1-bericht" zonder de
gegevens of de regels aan te passen. Dat is niet gedaan. De zin waarom zegt het wel.

### Huisstijl

| Onderdeel | Keuze | Waarom |
|---|---|---|
| Beeldmerk | Bouwkavel van bovenaf (ruit) met een signaal erin | Zegt wat de app doet: een signaal op een locatie |
| Nachtblauw `#0c1049` | Kopbalk, rangnummer, gekozen tegel, app-icoon | Uit het beeldmerk |
| Signaaloranje `#f23d0c` | Alleen voor wat aandacht vraagt: nieuw, de stip op het kaartje, de actieve tab | Eén kleur die "kijk hier" betekent |
| Papier `#f6f2e9` | Achtergrond; kaarten iets lichter (`#fffdf8`) | Rustig leesvlak, onderscheidt zich van het groen van versie 1 |
| Bricolage Grotesque | Naam, ochtendregel, rangnummer, de zin waarom | Eigen karakter in de koppen |
| Instrument Sans, IBM Plex Mono | Lopende tekst; tijdstip en tellingen | Leesbaar op klein formaat |
| Donkere weergave | Volgt de instelling van de telefoon | Bestond al; opnieuw afgesteld op de nieuwe kleuren |

De kleuren en lettertypen staan ook in `README.md` onder "Huisstijl". De lettertypen komen van
Google Fonts, net als in versie 1; zonder verbinding valt de app terug op het systeemlettertype.

### Bestanden

| Bestand | Wat |
|---|---|
| `site/logic.js` (nieuw) | Rangorde, filters, "nieuw sinds vorig bezoek", de ochtendregel en de inhoud van een kaart, zonder de pagina. Daardoor testbaar |
| `site/app.js` | Bouwt de pagina uit wat `logic.js` teruggeeft. De meldingen over onvolledige dagen en storingen, het kaartje, de gemeentelijst en het tabblad Bronnen zijn inhoudelijk gelijk gebleven |
| `site/index.html`, `site/styles.css` | Nieuwe opbouw en huisstijl |
| `site/sw.js` | Cache naar `v7`; `logic.js` en de illustratie erbij, zodat de app zonder verbinding compleet is |
| `site/manifest.webmanifest` | Nieuwe kleuren en omschrijving |
| `site/icons/`, `site/img/` | Beeldmerk, app-iconen, illustratie |
| `docs/huisstijl/` | De ongewijzigde originelen van ElevenLabs |
| `tests/test_site.py`, `tests/js/` | Nieuwe tests, zie hieronder |
| `README.md` | Beeldmerk, onderdelen, sectie Huisstijl |

## Referentiewaarden (16-11-2026, 18:45 uur, gegevens van 15:37 uur)

| Meting | Versie 1 | Versie 2 |
|---|---|---|
| Berichten: ontwikkellocatie / onzeker / weggefilterd | 81 / 23 / 1.012 | gelijk (zelfde bestand) |
| Hoogte van de top 10 op een telefoon van 390 × 844 | 3.348 px tot onderkant tiende kaart (4,0 schermen) | 2.599 px (3,1 schermen) |
| Gemiddelde hoogte per kaart | 294 px | 216 px |
| Bovenkant eerste kaart | 407 px | 435 px |
| Berichten op het eerste scherm geladen | 60 | 10 |
| `app.js` + `logic.js` | 25,6 kB | 24,6 + 9,8 kB |
| `styles.css` | 13,3 kB | 15,6 kB |
| Beeldmerk en illustratie | — | 3 kB per SVG-icoon, 28 kB per illustratie |
| Unittests | 80 | 124, alle geslaagd |

De eerste kaart begint 28 px lager dan in versie 1, door de ochtendregel. De tien kaarten samen
zijn 750 px korter.

Of de top 10 werkelijk in een minuut te lezen is, is niet gemeten; dat kan alleen Wim beoordelen.

## Getest

| Wat | Hoe | Uitkomst |
|---|---|---|
| Rangorde | 6 tests: hoogste score eerst, bij gelijke score nieuwste en dan dichtstbijzijnde; rang per klasse; rang verandert niet door filteren; sorteren laat de gegevens ongemoeid | Geslaagd |
| Lijsten | 6 tests: Ranglijst toont alleen ontwikkellocaties; Nieuw alleen nieuwe, in rangorde; Onzeker apart; weggefilterd alleen met de schakelaar; elk filter; de drie tellingen | Geslaagd |
| Nieuw sinds vorig bezoek | 3 tests: eerste bezoek markeert alleen de laatste publicatiedag; later bezoek markeert wat dit toestel nog niet zag (14 uur); de ochtendregel in enkelvoud, meervoud en nul | Geslaagd |
| Kaart | 8 tests: de zin waarom komt letterlijk uit de gegevens; rang, plaats, afstand en windrichting; geen exacte locatie; reactietermijn alleen zolang die loopt; alleen https-links | Geslaagd |
| Echte gegevens | 2 tests op `berichten.json`: rang loopt van 1 tot 81 zonder gaten en aflopend op score; elk van de 104 getoonde berichten heeft een rang, een plaats, een link en precies één zin waarom | Geslaagd |
| Huisstijl | 3 tests: donker thema heeft dezelfde kleuren als licht; 13 combinaties van tekst en achtergrond halen contrast 4,5 op 1 in beide thema's; kleur van de browserbalk is de balkkleur | Geslaagd |
| Beeldmerk | 4 tests: de SVG's bevatten alleen vormen (geen script, geen externe verwijzing); beeldmerk gebruikt de huiskleuren; kopbalk, los beeldmerk en app-icoon zijn dezelfde tekening; PNG's hebben de maat uit het manifest | Geslaagd |
| Pagina | 6 tests: elk bestand waar de pagina naar verwijst bestaat; elk element dat de app opzoekt staat op de pagina; de service worker bewaart alles wat de app nodig heeft; de app bouwt tekst, geen HTML | Geslaagd |
| In de browser | 6 tests in Chromium op 390 × 844: geen fouten in de console, niets breder dan het scherm, eerste scherm is rang 1 tot en met 10 met de zin waarom als eerste op de kaart, "Toon alle" geeft 1 tot en met 81, weggefilterd achter de schakelaar, "niets nieuws" toont de illustratie | Geslaagd |
| Tests vangen fouten | Drie fouten met opzet ingebouwd en weer teruggedraaid: sortering omgekeerd (9 tests falen), de zin waarom van de kaart gehaald (browsertest faalt), grijze tekst te licht gemaakt (3 tests falen) | Elke fout werd gevonden |
| Schermafbeeldingen | Tien schermen bekeken, licht en donker: ranglijst, open kaart, Nieuw, Onzeker, filters, Gebied, Bronnen, niets nieuws | Twee gebreken gevonden en hersteld: de knop Details kreeg de opmaak van de knop "Toon alle"; de ondertitel in de kopbalk werd afgekapt |
| Onafhankelijke review (subsessie) | Een tweede sessie loopt de wijziging na op gemiste functies, fouten en opmaak op 320, 390 en 1280 px | **Loopt nog op het moment van deze commit (18:50 uur).** De uitkomst wordt in dit verslag bijgeschreven |

De tests voor de logica draaien `site/logic.js` onder Node. Op GitHub is Node aanwezig, dus daar
draaien ze mee in de stap Tests van de workflow. De browsertests hebben Playwright nodig; dat
staat niet op de GitHub-runner, dus daar worden die zes overgeslagen. In deze container draaien ze.

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| Op een echte telefoon | Alleen getest in Chromium op telefoonformaat. Niet op iPhone/Safari en niet als geïnstalleerde app. |
| Installatie-icoon | De nieuwe iconen zijn gemaakt en hebben de juiste maat; hoe het icoon er op het beginscherm uitziet (afgeronde hoeken, rand) is niet bekeken. |
| Bestaande installaties | Wie versie 1 heeft geïnstalleerd, krijgt versie 2 bij de eerste keer openen mét verbinding (de service worker haalt eerst vers op). Het icoon op het beginscherm verandert op iOS pas na opnieuw installeren. Niet getest. |
| De workflow op GitHub | Niet uitgevoerd met deze wijziging; dat kan pas na samenvoegen met `main`. Verwachting: de stap Tests draait 118 tests en slaat er 6 over. Dat is een verwachting, geen waarneming. |
| Lettertypen zonder verbinding | De terugval op het systeemlettertype is niet apart bekeken. |

## Buiten dit verslag

- **Samenvoegen met `main` is niet gedaan.** De branch `claude/awesome-brown-i18j4o` is gepusht; er is geen pull request gemaakt. De live app toont versie 1 tot Wim samenvoegt.
- **ElevenLabs.** Het verbruik (12.726 credits) gaat van Wims maandtegoed af. De niet gekozen varianten en de lege proefwerkstroom staan nog in het account; opruimen kan alleen Wim.
- **Subsessie.** Eén subsessie heeft de wijziging onafhankelijk nagelopen (zie "Getest"). Het genereren van de beelden en het bouwen is in de hoofdsessie gedaan.
- **Bewust niet gedaan:** de rang uit de regels (1 tot en met 5) aan de gegevens toevoegen; berichten per locatie samenvoegen; de regels of de teksten op het tabblad Bronnen aanpassen; een eigen naam of woordmerk laten genereren (de naam blijft Tilburg Signalen, gezet in het huislettertype); een pull request openen.
- **Smaak.** Kleuren, lettertype en beeldmerk zijn een voorstel. De drie andere varianten van het beeldmerk staan in het ElevenLabs-account als Wim liever een andere kiest; omwisselen is één bestand en drie afgeleiden.
