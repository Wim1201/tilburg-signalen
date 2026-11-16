# Tilburg Signalen: verslag versie 2, eigen huisstijl en ochtendscherm

| | |
|---|---|
| Datum | 16-11-2026, 18:29 – 19:00 uur |
| Versie | versie 2 van de app, branch `claude/awesome-brown-i18j4o`, gestart vanaf `main` op commit `b315ab0` (na PR #7) |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | `site/data/berichten.json` zoals het in de repo staat (bijgewerkt 16-11-2026, 15:37 uur); er is niets opnieuw opgehaald |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_ontwikkellocaties_16-11-2026.md` |

## Correcties en aanvullingen op het vorige verslag

| Tijdstip | Wat |
|---|---|
| 16-11-2026, 19:00 uur | **Correctie op de eerste versie van dit verslag (commit `3ad8641`, 18:46 uur): de schakelaar "Toon ook wat is weggefilterd" staat niet in het filterpaneel.** De review vond dat hij daar verstopt zat. Hij staat nu onder de lijst, zichtbaar zonder iets te openen. "Filters wissen" zet hem niet meer uit (zoals in versie 1). |
| 16-11-2026, 19:00 uur | **Correctie: nieuwe onzekere berichten zijn weer vindbaar.** In de eerste versie van dit verslag stond dat er voor onzekere berichten geen filter "alleen nieuw" meer was. De review liet zien dat ze daardoor uit beeld raakten. Nu staan ze onder de tegel Nieuw, onder de kop "Nieuw onder Onzeker", en de regel onder de ochtendzin meldt ze ("Ook 1 nieuw bericht onder Onzeker."). |
| 16-11-2026, 19:00 uur | **Correctie: het aantal tests is 139, niet 124**, en de referentiewaarden voor de kaarthoogte zijn opnieuw gemeten. Zie "Referentiewaarden" en "Review door een subsessie". |
| 16-11-2026, 18:46 uur | **De beschrijving van de app onder "Wat er is veranderd" en "Getest → App" in het vorige verslag geldt niet meer letterlijk.** "Tabblad Onzeker" is nu de tegel Onzeker. De schakelaar "Toon ook wat is weggefilterd" staat nu onder de lijst (om 18:46 uur stond hier: in het filterpaneel; zie de correctie hierboven). Het label "relevantie 108" op de kaart is vervangen door het rangnummer; de score staat onder Details. |
| 16-11-2026, 18:46 uur | **Het eerste scherm toont 10 berichten in plaats van 60.** De knop "Toon alle 81 ontwikkellocaties" toont de rest in één keer. Weggefilterde berichten komen nog per 60. |
| 16-11-2026, 18:46 uur | **Het getal "nieuw sinds vorig bezoek" telt anders.** In versie 1 was het ontwikkellocaties plus onzeker samen. Nu telt de tegel Nieuw alleen ontwikkellocaties; nieuwe onzekere berichten staan op de tegel Onzeker ("Onzeker · 1 nieuw"). Het vinkje "Alleen nieuw sinds mijn vorige bezoek" in het filterpaneel is vervallen; de tegel Nieuw doet hetzelfde voor ontwikkellocaties. Nieuwe onzekere berichten staan ook onder de tegel Nieuw, onder een eigen kop (om 18:46 uur stond hier dat er geen filter meer voor was; zie de correctie hierboven). |
| 16-11-2026, 18:46 uur | **Bij een bericht zonder exacte locatie staat geen afstand meer op de kaart.** Versie 1 toonde het getal (bijvoorbeeld 0,0 km voor de hele gemeente Tilburg) met de toelichting eronder. Nu staat er "geen exacte locatie"; het getal en de toelichting staan onder Details. Sorteren en filteren op afstand rekenen nog met hetzelfde getal. |
| 16-11-2026, 18:46 uur | **Kostenraming ElevenLabs was te laag; zie "ElevenLabs".** De raming vooraf (970 credits voor vier varianten) gold voor een ander model dan waarmee daarna is gegenereerd. Werkelijk verbruik: 12.726 credits. |

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
| `site/icons/icon.svg`, `icon-192.png`, `icon-512.png` | Zelfde tekening | Op een nachtblauw vlak, ruit in papierkleur, signaal in `#ff5a2b` (hetzelfde oranje als in de kopbalk); de PNG's zijn daarvan gerenderd met Chromium |
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
| Filters | Knop Filters, schakelaar weggefilterd erbuiten | Knop Filters toont hoeveel filters aan staan ("Filters · 2"); de schakelaar weggefilterd staat onder de lijst |

Standaard opent de app op de Ranglijst: alle ontwikkellocaties, hoogste rang bovenaan, nieuwe
berichten gemarkeerd met een oranje rand en het label Nieuw. De tegel Nieuw toont alleen de nieuwe,
ook in rangorde, met daaronder de nieuwe onzekere berichten.

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

## Referentiewaarden (16-11-2026, 19:00 uur, gegevens van 15:37 uur)

| Meting | Versie 1 | Versie 2 |
|---|---|---|
| Berichten: ontwikkellocatie / onzeker / weggefilterd | 81 / 23 / 1.012 | gelijk (zelfde bestand) |
| Hoogte van de top 10 op een telefoon van 390 × 844 | 3.348 px tot onderkant tiende kaart (4,0 schermen) | 2.658 px (3,1 schermen) |
| Gemiddelde hoogte per kaart | 294 px | 220 px |
| Bovenkant eerste kaart | 407 px | 454 px |
| Berichten op het eerste scherm geladen | 60 | 10 |
| `app.js` + `logic.js` | 25,6 kB | 24,6 + 9,8 kB |
| `styles.css` | 13,3 kB | 15,6 kB |
| Beeldmerk en illustratie | — | 3 kB per SVG-icoon, 28 kB per illustratie |
| Unittests | 80 | 139, alle geslaagd |

De eerste kaart begint 47 px lager dan in versie 1, door de ochtendregel (met de gegevens van nu
twee regels, omdat er een nieuw onzeker bericht is). De tien kaarten samen zijn 690 px korter. De
waarden van 18:46 uur (2.599, 216 en 435 px) golden vóór het herstel van de reviewpunten; de knop
Details is sindsdien 40 px hoog gemaakt.

Of de top 10 werkelijk in een minuut te lezen is, is niet gemeten; dat kan alleen Wim beoordelen.

## Getest

| Wat | Hoe | Uitkomst |
|---|---|---|
| Rangorde | 6 tests: hoogste score eerst, bij gelijke score nieuwste en dan dichtstbijzijnde; rang per klasse; rang verandert niet door filteren; sorteren laat de gegevens ongemoeid | Geslaagd |
| Lijsten | 9 tests: Ranglijst toont alleen ontwikkellocaties; Nieuw alleen nieuwe, in rangorde, met nieuwe onzekere berichten eronder; Onzeker apart; weggefilterd alleen met de schakelaar en wel volgens zoekwoord en filters; elk filter; de grens van de periode; de drie tellingen | Geslaagd |
| Nieuw sinds vorig bezoek | 4 tests: eerste bezoek markeert alleen de laatste publicatiedag; later bezoek markeert wat dit toestel nog niet zag; de grens van 14 uur op de milliseconde; de ochtendregel in enkelvoud, meervoud en nul | Geslaagd |
| Kaart | 8 tests: de zin waarom komt letterlijk uit de gegevens; rang, plaats, afstand en windrichting; geen exacte locatie; reactietermijn alleen zolang die loopt; alleen https-links | Geslaagd |
| Echte gegevens | 2 tests op `berichten.json`: rang loopt van 1 tot 81 zonder gaten en aflopend op score; elk van de 104 getoonde berichten heeft een rang, een plaats, een link en precies één zin waarom | Geslaagd |
| Huisstijl | 3 tests: donker thema heeft dezelfde kleuren als licht; 13 combinaties van tekst en achtergrond halen contrast 4,5 op 1 in beide thema's; kleur van de browserbalk is de balkkleur | Geslaagd |
| Beeldmerk | 4 tests: de SVG's bevatten alleen vormen (geen script, geen externe verwijzing); beeldmerk gebruikt de huiskleuren; kopbalk, los beeldmerk en app-icoon zijn dezelfde tekening; PNG's hebben de maat uit het manifest | Geslaagd |
| Pagina | 8 tests: elk bestand waar de pagina naar verwijst bestaat; elk element dat de app opzoekt staat op de pagina; de service worker bewaart alles wat de app nodig heeft; de app bouwt tekst, geen HTML; **de zeven regels op het tabblad Bronnen zijn woord voor woord die van versie 1**; de schakelaar weggefilterd staat op het tabblad zelf | Geslaagd |
| In de browser | 15 tests in Chromium op 390 × 844 en 320 × 844: geen fouten in de console, niets breder dan het scherm, eerste scherm is rang 1 tot en met 10 met de zin waarom als eerste op de kaart, "Toon alle" geeft 1 tot en met 81, eerste bezoek telt de laatste publicatiedag als nieuw, weggefilterd achter de schakelaar, sorteren op datum met dagkoppen, doorklikken vanaf een gemeente, de regels op Bronnen, meldingen bij onvolledige gegevens, een nieuw onzeker bericht onder Nieuw, "niets nieuws" toont de illustratie, geen afgebroken datum op 320 px, knoppen minstens 40 px hoog | Geslaagd |
| Tests vangen fouten | Tien fouten met opzet ingebouwd en weer teruggedraaid: sortering omgekeerd, de zin waarom van de kaart gehaald, grijze tekst te licht gemaakt, één woord in een regeltekst gewijzigd, de meldingen weggehaald, nieuwe onzekere berichten weggelaten, de grens van 14 uur en van de periode één stap verschoven, de markering Nieuw weggehaald, de datum weer afbreekbaar gemaakt | Elke fout liet minstens één test falen |
| Schermafbeeldingen | Tien schermen bekeken, licht en donker: ranglijst, open kaart, Nieuw, Onzeker, filters, Gebied, Bronnen, niets nieuws | Twee gebreken gevonden en hersteld: de knop Details kreeg de opmaak van de knop "Toon alle"; de ondertitel in de kopbalk werd afgekapt |
| Onafhankelijke review (subsessie) | Een tweede sessie liep de wijziging na op gemiste functies, fouten en opmaak op 320, 390 en 1280 px, licht en donker | 5 punten om te herstellen en 6 kleine; alle 11 verwerkt. Zie "Review door een subsessie" |

De tests voor de logica draaien `site/logic.js` onder Node. Op GitHub is Node aanwezig, dus daar
draaien ze mee in de stap Tests van de workflow. De browsertests hebben Playwright nodig; dat
staat niet op de GitHub-runner, dus daar worden die vijftien overgeslagen. In deze container draaien ze.

## Review door een subsessie (18:44 – 18:55 uur, verwerkt om 19:00 uur)

De subsessie kreeg de code en de opdracht, niet mijn conclusies, en mocht niets wijzigen.

| Nr. | Bevinding | Zwaarte | Wat ermee is gedaan |
|---|---|---|---|
| 1 | Nieuwe onzekere berichten waren onvindbaar: de tegel zei "Onzeker · 2 nieuw", maar de ochtendzin zei "Geen nieuwe", Nieuw zei "Niets nieuws" en de nieuwe stonden buiten de top 10 van Onzeker | Herstellen | Ze staan nu onder Nieuw onder een eigen kop, en de regel onder de ochtendzin noemt ze. Test toegevoegd |
| 2 | De regel met plaats, afstand en datum brak slecht af: de datum over twee regels ("03-06-/2026") op 47 van de 81 kaarten bij 320 px en 25 van de 81 bij 390 px | Herstellen | Afstand en datum breken niet meer; het scheidingsteken staat aan het eind van de regel. Test op 320 px toegevoegd: 0 afgebroken |
| 3 | De links naar de bron stonden in versie 1 direct op de kaart en nu achter een knop van 24 px hoog; de links zelf waren 19 px hoog | Herstellen | Knop Details en de links zijn nu minstens 40 px hoog. Ze staan nog steeds achter Details; dat is de keuze voor een kortere kaart. Test toegevoegd |
| 4 | De schakelaar weggefilterd zat verstopt in het dichte filterpaneel, terwijl de tekst op Bronnen zegt "Met de schakelaar op het tabblad Berichten"; "Filters wissen" zette hem uit | Herstellen | Schakelaar staat onder de lijst; "Filters wissen" laat hem staan. Twee tests toegevoegd |
| 5 | Tests die niet konden falen of hun doel misten: één controleerde een lijst die Node nooit zag; de ochtendzin en het getal op de tegel Nieuw werden wel opgehaald maar niet gecontroleerd; geen test voor meldingen, doorklikken vanaf een gemeente, dagkoppen, de regelteksten, de markering Nieuw; grenzen van periode en 14 uur ongetest | Herstellen | Alle genoemde gaten gedicht: 15 tests erbij, en voor elk gat een fout ingebouwd om te zien dat de test hem vangt |
| 6 | Bij sorteren op datum telde de dagkop de hele dag ("5") terwijl er 4 kaarten onder stonden | Klein | Kop zegt nu "4 van 5" |
| 7 | Lege lijst: "De ranglijst is ongewijzigd" ook bij een eerste bezoek; "met deze filters" terwijl er geen filter aan stond | Klein | Teksten aangepast |
| 8 | De naam in de kopbalk heette "naar de ranglijst" maar bleef op de gekozen lijst | Klein | Gaat nu naar de Ranglijst. Test toegevoegd |
| 9 | Op 320 px schoof het label "Ingetrokken of buiten behandeling" over de knop Details | Klein | Labels breken af. Test toegevoegd: 0 overlappingen |
| 10 | Drie tinten oranje: app-icoon `#ff5226`, kopbalk `#ff5a2b`, los beeldmerk `#f23d0c` | Klein | App-icoon gebruikt nu het oranje van de kopbalk. Het losse beeldmerk houdt `#f23d0c`: dat staat op licht, de andere twee op nachtblauw. Test bewaakt beide |
| 11 | Een opengeklapte kaart klapte dicht bij "Toon alle" | Klein | Blijft open. Test toegevoegd |

Door de subsessie gecontroleerd en in orde bevonden: gegevens en regels ongewijzigd; de teksten op
Gebied en Bronnen gelijk aan versie 1; de lijsten van versie 2 gelijk aan die van versie 1 bij
standaard, onzeker, sorteren op datum en afstand, soort, gemeente, periode, stand en zoeken; nieuw
sinds vorig bezoek, ook als de opslag van de browser weigert; alle meldingen; lege gegevens zonder
fouten; de app werkt zonder verbinding (service worker op localhost getest); geen horizontaal
schuiven op 320, 390 en 1280 px.

Door de subsessie gezien, bestond al in versie 1, **niet hersteld**:

| Punt | Toelichting |
|---|---|
| Plaatsnamen op het kaartje overlappen | Goirle en Hilvarenbeek staan door elkaar |
| Toetsenbordfocus kan onder de vaste tabbalk vallen | 7 van de 34 stops; speelt op de telefoon niet |
| De schakelaar is in uit-stand weinig zichtbaar | Contrast 1,3 op 1 tegen de achtergrond |

Twee vermoedens van de subsessie, niet waargenomen: een bericht zonder afstand zou de kaart laten
vastlopen (de bron schrijft altijd een getal; toch afgevangen), en één test vergeleek de hoogste
score met alle klassen in plaats van alleen de ontwikkellocaties (hersteld).

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| Op een echte telefoon | Alleen getest in Chromium op telefoonformaat. Niet op iPhone/Safari en niet als geïnstalleerde app. |
| Installatie-icoon | De nieuwe iconen zijn gemaakt en hebben de juiste maat; hoe het icoon er op het beginscherm uitziet (afgeronde hoeken, rand) is niet bekeken. |
| Bestaande installaties | Wie versie 1 heeft geïnstalleerd, krijgt versie 2 bij de eerste keer openen mét verbinding (de service worker haalt eerst vers op). Het icoon op het beginscherm verandert op iOS pas na opnieuw installeren. Niet getest. |
| De workflow op GitHub | Niet uitgevoerd met deze wijziging; dat kan pas na samenvoegen met `main`. Verwachting: de stap Tests draait 124 tests en slaat er 15 over. Dat is een verwachting, geen waarneming. |
| Lettertypen zonder verbinding | De terugval op het systeemlettertype is niet apart bekeken. |

## Buiten dit verslag

- **Samenvoegen met `main` is niet gedaan.** De branch `claude/awesome-brown-i18j4o` is gepusht; er is geen pull request gemaakt. De live app toont versie 1 tot Wim samenvoegt.
- **ElevenLabs.** Het verbruik (12.726 credits) gaat van Wims maandtegoed af. De niet gekozen varianten en de lege proefwerkstroom staan nog in het account; opruimen kan alleen Wim.
- **Subsessie.** Eén subsessie heeft de wijziging onafhankelijk nagelopen (zie "Getest"). Het genereren van de beelden en het bouwen is in de hoofdsessie gedaan.
- **Bewust niet gedaan:** de rang uit de regels (1 tot en met 5) aan de gegevens toevoegen; berichten per locatie samenvoegen; de regels of de teksten op het tabblad Bronnen aanpassen; een eigen naam of woordmerk laten genereren (de naam blijft Tilburg Signalen, gezet in het huislettertype); een pull request openen.
- **Smaak.** Kleuren, lettertype en beeldmerk zijn een voorstel. De drie andere varianten van het beeldmerk staan in het ElevenLabs-account als Wim liever een andere kiest; omwisselen is één bestand en drie afgeleiden.
