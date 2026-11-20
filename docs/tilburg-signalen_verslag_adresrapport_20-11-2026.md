# Tilburg Signalen: verslag adresrapport (afdrukken en PDF)

| | |
|---|---|
| Datum | 20-11-2026 |
| Versie | branch `claude/serene-maxwell-le3mmw`, vanaf `main` op commit `41cab8c`; niet samengevoegd |
| Omgeving | Claude Code in de cloud (tijdelijke container), Chromium 157 met Playwright |
| Van / aan | Claude Code aan Wim |

## Opdracht

Een knop "Rapport afdrukken" op het tabblad Adres. Het rapport gebruikt de afdrukweergave van de
browser, zonder PDF-bibliotheek. Het neemt alles mee wat het tabblad toont, ook vakken die later
bijkomen. Alle waarschuwingen, bronnen en tijden van opvragen komen op papier, ook als ze op het
scherm ingeklapt, klein of verborgen zijn.

## Wat er is gebouwd

| Bestand | Wat |
|---|---|
| `site/rapport.js` (nieuw) | Bouwt het rapport vlak voor het afdrukken: bij de knop en bij `beforeprint` (afdrukken via het menu van de browser). Kopieert elk `section.vak` in `#adres-uitkomst`, in de volgorde van de pagina, zonder vaste lijst van vakken. In de kopie gaat alles open en zichtbaar (`details`, `hidden`), knoppen en velden gaan weg, en links worden tekst met een nummer: "Open bij de bron [3]". Verandert er daarna iets op het scherm, dan wordt de kopie weggegooid, zodat papier nooit een oudere stand toont dan het scherm |
| `site/index.html` | De knop met uitleg voor de iPhone, direct onder het gekozen adres; hij staat in `#adres-uitkomst` en is dus pas te zien na een keuze. Een lege `section#adres-rapport` aan het eind van `main`. Het script `rapport.js` na `adres-app.js` |
| `site/styles.css` | `@page`: A4, marges, paginanummer rechtsonder ("Pagina 1 van 6"). `@media print`: lichte kleuren, ook als het scherm donker is; tabbalk, kopbalk, knoppen en zoekvelden weg; met het tabblad Adres open en het rapport gebouwd staat alleen het rapport op papier; een vak wordt niet doorbroken; waarschuwingen in een kader, nooit kleiner dan 8 punt |
| `site/sw.js` | `rapport.js` in de offline-schil, cache `v15` naar `v16` |
| `README.md`, `CLAUDE.md` | Waar het rapport zit en de afspraak voor nieuwe vakken |

### Opbouw op papier

1. Kop: "Tilburg Signalen", "Adresrapport", het adres, postcode en plaats, en de tijd van opvragen en van het rapport.
2. "Lees dit eerst", in een zwart kader: geen advies; wijzigingen sinds 1-1-2024 ontbreken bij het bestemmingsplan; geen getal betekent niet geen beperking; geen resultaat betekent alleen niet gevonden in die bron, op dat moment.
3. Elk vak onder elkaar, met zijn eigen waarschuwingen en bronregels, en per vak "Opgevraagd op ... Beantwoord." (of "Nog geen antwoord" of "Niet of niet volledig beantwoord").
4. "Eigen aantekeningen": twaalf lijnen.
5. "Bronnen en beperkingen": het adres (PDOK Locatieserver), elk vak met tijd van opvragen, stand en zijn regels met "Bron:" of "opgevraagd", en de berichten van de app met de tijd van de laatste verversing.
6. "Links": elke link van het tabblad, genummerd, met het volledige webadres.

### Regels voor een nieuw vak

Het rapport leest de pagina, niet de code van de vakken. Een nieuw vak komt vanzelf mee als het:

- een `section class="vak"` in `#adres-uitkomst` is, met een `h3` en een `div class="vak-inhoud"`;
- zich vult door `.vak-inhoud` leeg te maken en opnieuw te vullen (dat moment geldt als tijd van opvragen);
- waarschuwingen de klasse `stale` geeft en bronregels de klasse `bronregel`, met "Bron:" aan het begin of "opgevraagd" erin;
- een knop "Opnieuw proberen" toont als een bron niet antwoordt (dan staat er "Niet of niet volledig beantwoord").

Wat alleen voor het scherm is, krijgt `data-afdruk="nee"`.

### Titel en bestandsnaam

Tijdens het afdrukken is de titel van de pagina "Adresrapport <adres> <datum>", want de meeste
browsers noemen de PDF naar de titel. Na `afterprint` komt "Tilburg Signalen" terug. Het adres staat
nergens in de code: het komt van wat de gebruiker koos.

## iPhone: van rapport naar PDF

De tekst bij de knop: "Op een iPhone: tik op de knop, of in Safari op Delen en dan Afdrukken. Spreid
in het voorbeeld twee vingers: het rapport opent als PDF. Tik dan op Delen en Bewaar in Bestanden."

Gecontroleerd tegen [iGeeksBlog, 13-05-2025](https://www.igeeksblog.com/how-to-save-webpages-as-pdf-on-iphone-ipad/),
methode 2: "Choose Print from the Share Sheet", daarna "two-finger outward swipe to expand the
preview", daarna Share en Save to Files. Een artikel van Apple zelf heb ik niet gevonden. Dat bron
noemt geen iOS-versie; op iOS 26 of 27 is het niet nagegaan. Het oudere artikel van
[MacRumors, 19-01-2018](https://www.macrumors.com/how-to/turn-a-webpage-into-a-pdf-on-ios) noemt alleen "Create PDF" in Delen.

Let op: de app staat als beginscherm-app (`display: standalone`). Daar is geen knop Delen van
Safari. Of `window.print()` daar werkt, kon ik niet vaststellen; een melding uit 2015 (iOS 9) zegt van
niet. Werkt de knop vanuit het beginscherm niet, open de site dan in Safari.

## Tests

| | |
|---|---|
| Hele reeks | 568 tests geslaagd, 10 overgeslagen (de tests tegen de echte bronnen en de filmtests). Ook de browsertests in Chromium |
| Nieuw in de browser (`tests/js/adres_smoke.js`, deel "rapport") | Telefoon van 390 px in het donkere thema, met het openbare testadres en de nagespeelde antwoorden van PDOK en de Worker; `window.print` telt alleen. Ook een proefvak dat de test zelf toevoegt, met een verborgen waarschuwing |
| Nieuw in Python (`tests/test_site.py`, 14) | Knop pas na een adres en de uitleg voor de iPhone; op papier alleen het rapport, zonder tabbalk, kopbalk of knoppen; wit met zwarte tekst bij een donker scherm; de onderdelen in volgorde met elk vak, ook het proefvak; de vier waarschuwingen van "Lees dit eerst"; elke waarschuwing en bronregel van het scherm op papier, zichtbaar en niet kleiner dan 8 punt; het ingeklapte deel open; geen links meer, alle webadressen in de lijst; per vak de tijd van opvragen in "Bronnen en beperkingen"; vakken niet doorbroken; de titel alleen tijdens het afdrukken; afdrukken via het menu bouwt het rapport; een wijziging op het scherm gooit de kopie weg; een ander tabblad drukt af zonder rapport; in de code van het rapport geen vak en geen postcode; de afdrukopmaak (A4, paginanummer, lichte kleuren) |
| Externe aanroepen | Geen: de test controleert dat het rapport niets opvraagt buiten de nagespeelde diensten |

### Afdrukvoorbeeld op de pc

Geen echt afdrukvenster: in de container is geen scherm. Wel met Chromium een PDF gemaakt van het
rapport (`page.pdf`, A4, de opmaak voor afdrukken) en die pagina voor pagina als plaatje bekeken.
Zet `TILBURG_RAPPORT_PDF` op een bestandsnaam om die PDF zelf te laten maken bij de browsertests.

| Gezien | |
|---|---|
| Formaat | A4 (595 x 842 punt), 6 pagina's voor het testadres met het proefvak |
| Paginanummer | "Pagina 1 van 6" tot "Pagina 6 van 6" rechtsonder, ook in de tekst van de PDF |
| Vakken | Geen vak doorbroken. Gevolg: wit onder aan een pagina als het volgende vak niet meer past |
| Kleuren | Wit papier, zwarte tekst, waarschuwingen in een licht geel kader, het energielabel zwart op wit |
| Kaartje | Het perceel en het adrespunt staan erop. In de test is de achtergrondkaart een nagespeeld plaatje van één pixel; met de echte kaart niet gezien |

## Wat ik niet heb kunnen controleren

| Punt | Toelichting |
|---|---|
| iPhone | Niets op een iPhone gedaan: niet de knop, niet Delen en dan Afdrukken, niet het spreiden met twee vingers, niet de naam van de PDF |
| Beginscherm-app | Of `window.print()` werkt als de app vanaf het beginscherm is geopend |
| `beforeprint` in Safari | Afdrukken via Delen zonder de knop rekent op `beforeprint`. Zonder dat event drukt Safari het tabblad zelf af, zonder het rapport: zonder tabbalk en knoppen, maar met ingeklapte delen dicht |
| Paginanummer buiten Chromium | De nummering gebruikt `@page`-margevakken. Chromium toont ze; Safari en Firefox niet gecontroleerd. Daar kan het nummer ontbreken; de rest van het rapport blijft gelijk |
| Echt afdrukvenster op Windows | Alleen de PDF uit Chromium bekeken. In Edge of Chrome kan de optie "Kop- en voetteksten" er een eigen regel met titel en webadres bij zetten; die kun je in het afdrukvenster uitzetten |
| Echte achtergrondkaart op papier | In de test nagespeeld |

## Samenvoegen

Niet samengevoegd. Raakt `site/` en tests, geen workflow en geen `signalen/update.py`. Samenvoegen
start een verversing: niet vlak voor of tijdens een slot (zaterdag alleen 12:10 uur). Wacht na het
samenvoegen die run af: pas daar draait de controle van de live site.
