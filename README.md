<img src="site/icons/beeldmerk.svg" alt="Beeldmerk Tilburg Signalen" width="72">

# Tilburg Signalen

Mobiele webapp die elke ochtend laat zien waar binnen 15 km van Tilburg-centrum (de Heuvel)
ontwikkellocaties ontstaan. De app leest omgevingsvergunningen, wijzigingen in omgevingsplannen en
bestemmingsplannen, verkoopvoornemens van overheden en faillissementen van bedrijven, houdt alleen
de ontwikkellocaties over en rangschikt die op relevantie. Het eerste scherm is de top 10: de
hoogste rang bovenaan, per bericht eerst de zin waarom het relevant is, dan de locatie, de afstand
tot Tilburg en de bron.

De app gebruikt alleen openbare gegevens van overheden en heeft geen server of database nodig.

Rond die kern liggen drie **regio's**: Midden-Brabant, West-Brabant en Zeeland (indeling van het CBS).
De app haalt hun berichten ook op, maar opent altijd met alleen de kern. Op het tabblad Gebied kies
je een regio erbij; bij een volgend bezoek staat de app weer op de kern.

Met een regio erbij kies je op het tabblad Berichten wat de lijsten tonen: **Samen** (de standaard),
**Alleen de kern** of **Alleen** die regio. De rang telt binnen wat je ziet. De ochtendregel bovenaan
blijft over de kern gaan.

De ranglijst zet de hoogste score bovenaan. Bij een gelijke score gaat het bericht met de meeste
woningen voor, daarna het nieuwste. Het filter **Fase** kent drie treden: vroeg (voornemen, aanvraag),
midden (ontwerp, bekendmaking, besluit) en laat (vastgesteld, verleend, herstelbesluit). Die indeling
is een keuze van deze app en komt niet uit de bronnen. Wat in geen trede valt, staat onder **Overig**.

Het tabblad **Adres** staat daar los van: typ een adres en zie het pand (BAG), het kadastrale perceel
met een kaartje, en de publicaties over dat adres uit de berichten die de app al heeft. Het vraagt
de gegevens rechtstreeks vanuit de browser op bij PDOK, zonder sleutel. Met **Rapport afdrukken** komt
alles wat het tabblad toont op papier of in een PDF, met de waarschuwingen en bronnen (`site/rapport.js`).

Blijft de app open staan, dan haalt hij de berichten opnieuw op zodra hij weer in beeld komt en de
laatste keer meer dan een kwartier geleden is. "Bijgewerkt" volgt dan mee; een gekozen regio, een
zoekopdracht, de filters en een opgezocht adres blijven staan.

## Hoe het werkt

| Onderdeel | Wat het doet |
|---|---|
| `signalen/gebied.py` | Bepaalt welke gemeenten en plaatsen binnen de straal vallen (de kern), meet de gemeenten van de regio's uit `config.json` en schrijft `site/data/gebied.json` |
| `signalen/update.py` | Haalt de berichten op bij alle bronnen en schrijft `site/data/berichten.json` (de kern) en per regio een eigen bestand, zoals `site/data/regio-zeeland.json` |
| `signalen/bekendmakingen.py` | Leest officielebekendmakingen.nl (Gemeenteblad, Provinciaal blad, Waterschapsblad, Staatscourant) |
| `signalen/vlaanderen.py` | Leest Vlaamse omgevingsvergunningen voor het Belgische deel van de straal |
| `signalen/relevantie.py` | De regels: wat is een ontwikkellocatie, wat is onzeker, wat valt af, en de zin waarom |
| `signalen/insolventies.py` | Leest faillissementen van bedrijven uit de Staatscourant (alleen rechtspersonen met een bedrijfspand) |
| `signalen/perceel.py` | Zoekt perceelgrootte (Kadaster) en gebruiksdoel van een pand (BAG) op |
| `signalen/cache.py` | Bewaart opgehaalde teksten, perceelgroottes en adreslocaties in `cache/ophaalcache.json`, zodat een run alleen nieuwe publicaties ophaalt |
| `signalen/volledigheid.py` | Herkent dagen waarop de bron vrijwel niets doorgaf, zodat de app dat kan melden |
| `signalen/tekst.py` | Leest de eerste regels van een bekendmaking als de omschrijving ontbreekt |
| `signalen/bronnen.json` | De bronnenlijst die de app toont (aangesloten en niet aangesloten) |
| `site/` | De app zelf: statische bestanden, installeerbaar op de telefoon |
| `site/logic.js` | Wat de app toont, zonder de pagina: rangorde, filters, "nieuw sinds vorig bezoek" en de inhoud van een kaart. `site/app.js` bouwt daar de pagina van |
| `site/adres.js` | Het tabblad Adres zonder de pagina: schrijfwijzen van adressen gelijktrekken, publicaties aan een adres koppelen, en wat de antwoorden van BAG en Kadaster betekenen. `site/adres-app.js` bouwt daar het tabblad van en vraagt de bronnen op. `site/rapport.js` maakt er het adresrapport voor de afdrukweergave van |
| `site/styles.css` | De huisstijl: kleuren, lettertypen en opmaak, licht en donker |
| `.github/workflows/dagelijks.yml` | Ververst de gegevens op vaste tijden (werkdagen 06:45, 09:35, 10:20, 12:10 en 16:10 uur Nederlandse tijd) en publiceert de app op GitHub Pages. Bij een push en een handmatige run draaien vooraf ook de tests in een echte browser; na elk publiceren test een eigen job de pagina op de live site |
| `.github/workflows/tests.yml` | Draait bij elke pull request alleen de tests en de tests in een echte browser, zodat een fout zichtbaar is vóór het samenvoegen. Haalt niets op, publiceert niets en schrijft niets terug; het schema en de planner kennen dit bestand niet |
| `.github/actions/browser/` | Zet voor die tests Node, Playwright en Chromium klaar op de GitHub-runner |
| `package.json`, `package-lock.json` | Leggen Playwright op één versie vast. Alleen voor de tests in een echte browser; de app zelf heeft geen pakketten nodig |
| `config.json` | Middelpunt, straal en hoe lang berichten in de lijst blijven |
| `tools/planner/` | Voorbereid, niet live: een Cloudflare Worker die de workflow op de tijden van het schema start als GitHub dat zelf niet doet. Zie `tools/planner/README.md` |
| `tools/energielabel/` | Geplaatst en aan de app gekoppeld: een tweede Cloudflare Worker, los van de planner, die voor het tabblad Adres het energielabel van één adres opvraagt bij EP-Online. Zie `tools/energielabel/README.md` |
| `tools/video/` | Maakt de video van de ochtendronde door de app zelf te bedienen. De film zelf staat niet in de repo; hij komt in `tools/video/uit/`, dat git overslaat. Zie het verslag over de video in `docs/` |

## Zelf draaien

Alleen Python 3.9 of nieuwer is nodig, geen extra pakketten.

```bash
python -m signalen.gebied
```

```bash
python -m signalen.update
```

Een gewone run haalt alleen op wat nog niet in de cache staat. Van de regio's leest een run
hoogstens 300 nieuwe teksten (`grens_regioteksten` in `config.json`); de kern wordt altijd eerst en
helemaal gelezen. Een regiobericht dat op zijn tekst wacht, staat onder Onzeker met "Tekst nog niet
gelezen" tot een volgende run het ophaalt.

De volledige verversing (wekelijks gebeurt dat vanzelf) leest de kern opnieuw en één regio, bij
toerbeurt per week; de andere regio's komen uit de cache:

```bash
python -m signalen.update --volledig
```

Een bepaalde regio opnieuw lezen in plaats van de regio van de week:

```bash
python -m signalen.update --volledig --regio Zeeland
```

Echt alles opnieuw, zonder cache en zonder grens (zwaar voor de bron; niet voor de dagelijkse gang):

```bash
python -m signalen.update --alles
```

De cache staat in de repository, en een bestand daar mag niet groter zijn dan 1,5 MB (een test
bewaakt dat). Een run schrijft daarom nooit een cache boven 1,4 MB: is hij groter, dan bewaart de run
een deel van de regioteksten niet (eerst wat het eerst uit het venster valt; de kern blijft altijd
staan) en haalt de volgende run die opnieuw op. Het log van de run meldt de grootte, en waarschuwt
vanaf 1,2 MB.

```bash
python -m http.server 8000 --directory site
```

Open daarna `http://localhost:8000`. Tests draaien met:

```bash
python -m unittest discover tests
```

De tests voor de app zelf (`tests/test_site.py`) draaien `site/logic.js` onder Node en worden
overgeslagen als Node ontbreekt. De tests in een echte browser hebben daarnaast Playwright en
Chromium nodig en worden zonder Playwright overgeslagen. Installeren, eenmalig:

```bash
npm ci
```

```bash
npx playwright install chromium
```

Het tabblad Adres wordt in die browsertests getest met nagespeelde antwoorden van PDOK
(`tests/js/adres_fixtures.json`), zodat de test niet van PDOK afhangt. Tegen de echte bronnen, met
echte adressen in Tilburg, Dongen en Goirle, alleen op verzoek:

```bash
TILBURG_ADRES_LIVE=1 python -m unittest tests.test_adres.EchteBronnen
```

De paginatest draait ook tegen de live site:

```bash
TILBURG_SITE_URL=https://wim1201.github.io/tilburg-signalen python -m unittest tests.test_site.InDeBrowser
```

## Online zetten

1. Zet de code op de `main`-branch.
2. Kies in GitHub bij **Settings → Pages → Build and deployment → Source** voor **GitHub Actions**.
3. Start de workflow **Dagelijkse verversing** één keer met de hand (tabblad Actions) of wacht op de eerste ochtend.

De app staat dan op `https://wim1201.github.io/tilburg-signalen/`. Op de telefoon: open die
pagina en kies "Zet op beginscherm" om hem als app te installeren.

## Tabblad Adres: bronnen

| Onderdeel | Bron | Opmerking |
|---|---|---|
| Adres zoeken | PDOK Locatieserver | Suggesties tijdens het typen, dichtbij Tilburg eerst |
| Pand | BAG (Kadaster, via PDOK) | Bouwjaar, gebruiksdoel, oppervlakte, pandstatus |
| Perceel | Kadastrale kaart (Kadaster, via PDOK) | Het perceel dat het Kadaster aan het adres koppelt. De kaart geeft alleen een indicatie; er zijn geen maten aan te ontlenen |
| Publicaties | `data/berichten.json`, zoals de app het al geladen heeft | Ook de weggefilterde berichten. Er wordt niets opgehaald en niets weggeschreven |
| Energielabel | EP-Online (RVO), via de Worker in `tools/energielabel/` | Alleen als `energielabel_worker` in `config.json` is ingevuld. Zonder die instelling: alleen een link naar EP-Online. Het adres gaat in de inhoud van de vraag aan de Worker, niet in het webadres; Cloudflare bewaart van de Worker geen logboek |
| Bestemmingsplan | Niet aangesloten | Alleen een link naar het Omgevingsloket |

Adres, pand, perceel en publicaties gaan zonder sleutel en zonder tussenserver. Het energielabel is de
uitzondering: EP-Online vraagt een sleutel, en die staat als geheim bij Cloudflare, niet in deze repo
en niet in de app. De keuzes en de beperkingen van het koppelen van publicaties staan in
`docs/tilburg-signalen_verslag_tabblad-adres_17-11-2026.md`; het energielabel in
`docs/tilburg-signalen_verslag_energielabel_18-11-2026.md`, en wat Cloudflare van een vraag vastlegt in
`docs/tilburg-signalen_verslag_energielabel-logboek-en-diagnose_18-11-2026.md`.

## Instellingen aanpassen

In `config.json` staan het middelpunt, de straal (`straal_km`), de bewaartermijnen
(`venster_dagen`) en de drempel voor de perceelgrootte (`drempel_perceel_m2`). Draai na een wijziging van middelpunt of straal eerst `signalen.gebied`.

`energielabel_worker` is het adres van de Worker voor het energielabel (`tools/energielabel/`), bijvoorbeeld
`https://tilburg-signalen-energielabel.<jouw-subdomein>.workers.dev`. Leeg betekent: de app roept de Worker
niet aan, en het vak Energielabel toont alleen de link naar EP-Online. De volgende verversing na het
invullen zet het adres in de app.

### Gemeenten en regio's

`gemeenten` in `config.json` is de lijst van gemeenten met per gemeente een regio:

| Veld | Betekenis |
|---|---|
| `regio` | `kern`, of een van de regio's uit `regios` (Midden-Brabant, West-Brabant, Zeeland) |
| `buiten_straal` | Alleen bij een gemeente van de kern: de regio waar de rest van die gemeente, buiten de straal, bij hoort |
| `opmerking` | Een beperking van de bron voor die gemeente; de app toont haar op het tabblad Gebied |

De kern is en blijft wat binnen de straal ligt; de lijst verandert dat niet. Een gemeente met een
andere regio dan `kern` telt in haar geheel mee. Elk bericht krijgt `regio`: `kern` binnen de straal,
anders de regio van zijn gemeente. Faillissementen en de Vlaamse bron blijven bij de kern. Draai na
een wijziging van de lijst `signalen.gebied`. Waarom deze gemeenten, en wat de bron per gemeente
levert, staat in `docs/tilburg-signalen_verslag_dekking-en-regios_17-11-2026.md`.

## Huisstijl

Het beeldmerk is een bouwkavel van bovenaf met een signaal erin. Het is gemaakt met ElevenLabs
Image Gen; de ongewijzigde originelen staan in `docs/huisstijl/`.

| Onderdeel | Waarde | Waar |
|---|---|---|
| Nachtblauw | `#0c1049` | Kopbalk, rangnummer, app-icoon |
| Signaaloranje | `#f23d0c` (vlakken), `#bf3208` (tekst op licht) | Nieuw, het signaal in het beeldmerk, actieve tab |
| Papier | `#f6f2e9` (achtergrond), `#fffdf8` (kaarten) | Pagina |
| Inkt | `#12163b`, gedempt `#5a5d78` | Tekst |
| Koppen en cijfers | Bricolage Grotesque | Naam, ochtendregel, rangnummer, de zin waarom |
| Lopende tekst | Instrument Sans | Alles daaronder |
| Gegevens | IBM Plex Mono | Tijdstip, tellingen |

Alle kleuren staan als variabelen bovenaan `site/styles.css`, met een donkere variant. Het
beeldmerk staat in `site/icons/beeldmerk.svg` (los), `site/icons/icon.svg` (app-icoon) en in de
kopbalk van `site/index.html`; een test bewaakt dat het drie keer dezelfde tekening is.

Meer achtergrond over de bronnen en de gemaakte keuzes staat in `docs/`.
