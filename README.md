<img src="site/icons/beeldmerk.svg" alt="Beeldmerk Tilburg Signalen" width="72">

# Tilburg Signalen

Mobiele webapp die elke ochtend laat zien waar binnen 15 km van Tilburg-centrum (de Heuvel)
ontwikkellocaties ontstaan. De app leest omgevingsvergunningen, wijzigingen in omgevingsplannen en
bestemmingsplannen, verkoopvoornemens van overheden en faillissementen van bedrijven, houdt alleen
de ontwikkellocaties over en rangschikt die op relevantie. Het eerste scherm is de top 10: de
hoogste rang bovenaan, per bericht eerst de zin waarom het relevant is, dan de locatie, de afstand
tot Tilburg en de bron.

De app gebruikt alleen openbare gegevens van overheden en heeft geen server of database nodig.

## Hoe het werkt

| Onderdeel | Wat het doet |
|---|---|
| `signalen/gebied.py` | Bepaalt welke gemeenten en plaatsen binnen de straal vallen en schrijft `site/data/gebied.json` |
| `signalen/update.py` | Haalt de berichten op bij alle bronnen en schrijft `site/data/berichten.json` |
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
| `site/styles.css` | De huisstijl: kleuren, lettertypen en opmaak, licht en donker |
| `.github/workflows/dagelijks.yml` | Ververst de gegevens op vaste tijden (werkdagen 06:45, 09:35, 10:20, 12:10 en 16:10 uur Nederlandse tijd) en publiceert de app op GitHub Pages |
| `config.json` | Middelpunt, straal en hoe lang berichten in de lijst blijven |
| `tools/video/` | Maakt de video van de ochtendronde door de app zelf te bedienen. De film zelf staat niet in de repo; hij komt in `tools/video/uit/`, dat git overslaat. Zie het verslag over de video in `docs/` |

## Zelf draaien

Alleen Python 3.9 of nieuwer is nodig, geen extra pakketten.

```bash
python -m signalen.gebied
```

```bash
python -m signalen.update
```

Een gewone run haalt alleen op wat nog niet in de cache staat. Alles opnieuw ophalen
(wekelijks gebeurt dat vanzelf) kan met:

```bash
python -m signalen.update --volledig
```

```bash
python -m http.server 8000 --directory site
```

Open daarna `http://localhost:8000`. Tests draaien met:

```bash
python -m unittest discover tests
```

De tests voor de app zelf (`tests/test_site.py`) draaien `site/logic.js` onder Node en worden
overgeslagen als Node ontbreekt. De test in een echte browser heeft daarnaast Playwright nodig.

## Online zetten

1. Zet de code op de `main`-branch.
2. Kies in GitHub bij **Settings → Pages → Build and deployment → Source** voor **GitHub Actions**.
3. Start de workflow **Dagelijkse verversing** één keer met de hand (tabblad Actions) of wacht op de eerste ochtend.

De app staat dan op `https://wim1201.github.io/tilburg-signalen/`. Op de telefoon: open die
pagina en kies "Zet op beginscherm" om hem als app te installeren.

## Instellingen aanpassen

In `config.json` staan het middelpunt, de straal (`straal_km`), de bewaartermijnen
(`venster_dagen`) en de drempel voor de perceelgrootte (`drempel_perceel_m2`). Draai na een wijziging van middelpunt of straal eerst `signalen.gebied`.

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
