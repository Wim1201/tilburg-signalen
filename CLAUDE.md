Afspraken voor Tilburg Signalen
Dit bestand geldt voor elke sessie en elk model. Lees het voordat je iets doet.
Wie en hoe

* Eigenaar: Wim Snoeren. Geen fulltime programmeur. Hij werkt op Windows met Windows PowerShell (gebruik `curl.exe`, niet `curl`) en test op een iPhone.
* Schrijf in het Nederlands. Geen marketingtaal, geen uitroeptekens.
* Verslag aan Wim: hoogstens tien regels. Details gaan in `docs/`.
* Noem in elk verslag expliciet wat je NIET hebt kunnen controleren.
* Iets is pas af als het getest én vastgelegd is.

Samenvoegen

* Niets samenvoegen zonder akkoord van Wim. Uitzondering: een pull request die alleen `docs/` raakt mag je zelf samenvoegen; meld het achteraf.
* Alleen samenvoegen als de testrun op de pull request groen is.
* Een groene testrun op een pull request is niet genoeg: de livetests draaien pas in de verversing na het samenvoegen. Meld dat Wim die run moet afwachten.
* Niet samenvoegen vlak voor of tijdens een slot van de planner: werkdagen 06:45, 09:35, 10:20, 16:10; dagelijks 12:10; zondag 04:30. Ook samenvoegen op main start een verversing; laat twee verversingen elkaar niet overlappen.
* Begin elke nieuwe taak op een nieuwe branch vanaf de actuele `main`.
* Eén onderwerp per pull request. Raakt een wijziging meer bestanden dan afgesproken (zeker `signalen/update.py` of een workflow), zeg dat vooraf.

Niet doen

* Niets forceren (`--force`, geschiedenis herschrijven).
* Het schema en de triggers van de workflows niet wijzigen. Een workflow aanpassen alleen na akkoord van Wim.
* De cache niet vanaf een branch committen.
* Je kunt geen workflow starten (403); handmatige runs start Wim zelf.
* Geen sleutels in code, tests, logs of verslagen. Vraag Wim nooit een sleutel in een chat te plakken.
* Geen adressen van Wim, zijn familie of bezoekers in de repo. Alleen openbare testadressen.
* Tests (ook de livetests) roepen nooit de echte energielabel-Worker of EP-Online aan. Gebruik nagespeelde antwoorden.
* Niet onderzoeken: de Vlaamse bron.

Opbouw

* Planner: Cloudflare Worker `tilburg-signalen-planner` (`tools/planner/`) start de verversing op de slots. GitHub's eigen schema is onbetrouwbaar.
* Energielabel: Cloudflare Worker `tilburg-signalen-energielabel` (`tools/energielabel/`), adres in een POST, logboek bij Cloudflare uit. Na een wijziging moet Wim zelf `npx wrangler deploy` doen in die map.
* Workflows: `Dagelijkse verversing` en `tests.yml` (tests bij elke pull request).
* Cache: let op de grens van 1,5 MB.
* Adresrapport en locatierapport: `site/rapport.js` kopieert bij het afdrukken elk zichtbaar `section.vak` van de Adres-tab, zonder vaste lijst. Een nieuw vak komt vanzelf mee; maak waarschuwingen `.stale` en bronregels `.bronregel` (met "Bron:" of "opgevraagd"), en zet wat alleen voor het scherm is op `data-afdruk="nee"`. Een vak dat niet in gebruik is, krijgt `hidden` en blijft van papier. Waarschuwingen, bron en datum mogen nooit van papier af.
* Locatierapport: de knop "Locatierapport" op een kaart vult de Adres-tab vanuit de bekendmaking (`kiesLocatie` in `site/adres-app.js`): met het ene adres uit de tekst, anders met het punt (alleen perceel en bestemmingsplan), anders alleen de bekendmaking.
