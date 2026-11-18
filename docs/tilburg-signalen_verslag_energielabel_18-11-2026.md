# Tilburg Signalen: verslag energielabel op het tabblad Adres, via een tweede Worker

| | |
|---|---|
| Datum | 18-11-2026, 15:35 – 16:07 uur |
| Versie | versie 2 van de app met de regio's, branch `claude/optimistic-gauss-sb0xpy`, gelijk aan `main` op commit `a435e03` (na PR 25) bij de start |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen`; Node 22, wrangler 4.164.0, Chromium via Playwright |
| Brondata | De documentatie van de openbare API van EP-Online, versie 5 (`public.ep-online.nl/swagger/v5/swagger.json`), gelezen op 18-11-2026, 15:36 uur. **EP-Online zelf is niet aangeroepen: er is geen sleutel** |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_tabblad-adres_17-11-2026.md` en `tilburg-signalen_verslag_tests-bij-pull-request_18-11-2026.md` |

## Stand

De Worker en het vak op het tabblad zijn gebouwd en staan op de werkbranch, in een pull request die
**open blijft en niet is samengevoegd**. Er is niets bij Cloudflare geplaatst en er is geen sleutel
aangevraagd. De instelling met het adres van de Worker staat leeg, dus na samenvoegen verandert er in
de app niets tot Wim de Worker plaatst en het adres invult.

**Niet getest: de echte sleutel en de echte dienst.** Alles wat hier over EP-Online staat, komt uit de
documentatie en uit een nagebootst EP-Online.

## Correcties en aanvullingen op eerdere verslagen

| Tijdstip | Wat |
|---|---|
| 18-11-2026, 16:07 uur | **"Geen sleutels, geen tussenserver" uit het verslag van het tabblad Adres geldt niet meer voor het energielabel.** Wim vroeg op 17-11 om een tabblad zonder sleutels, tokens of Worker, en vraagt nu om het energielabel via een Worker met een sleutel. Voor adres, pand, perceel en publicaties blijft de oude afspraak gelden: die gaan rechtstreeks vanuit de browser naar open bronnen. De twee tests die de oude afspraak bewaakten, zijn daarop aangepast; zie "Tests". |
| 18-11-2026, 16:07 uur | **De planner is niet gewijzigd.** De nieuwe Worker staat in een eigen map met een eigen naam; een test bewaakt dat de instellingen van de planner hem niet noemen. |
| 18-11-2026, 16:07 uur | **Het aantal tests is 503 (was 440).** Er zijn er 63 bij: 50 voor de Worker, 8 voor de logica van het vak en 5 in de browser. |

## Opdracht

Een aparte Cloudflare Worker in `tools/energielabel/` die het energielabel van één adres opvraagt bij
EP-Online, met de sleutel als geheim, alleen voor de herkomst van de site en begrensd per minuut en per
dag. Het tabblad toont het label in het bestaande vak, met drie andere uitkomsten elk met eigen tekst;
het adres van de Worker is een instelling die leeg mag zijn. Tests met een nagebootst EP-Online, een
README voor het plaatsen, en duidelijk zeggen wat niet getest is.

## Wat de documentatie van EP-Online zegt

Gelezen, niet geraden. Uit `swagger.json` van versie 5:

| Onderdeel | Wat er staat |
|---|---|
| Het adres | `GET /api/v5/PandEnergielabel/Adres` op `public.ep-online.nl` |
| De parameters | `postcode` (`^[1-9][0-9]{3}[A-Z]{2}$`), `huisnummer` (`^[1-9][0-9]{0,4}$`), `huisletter` (`^[a-zA-Z]{1}$`, optioneel), `huisnummertoevoeging` (`^[a-zA-Z0-9]{4}$`, optioneel), `detailaanduiding` (optioneel) |
| De sleutel | "De API-key moet in de Authorization header meegeven worden"; aanvragen bij RVO op `apikey.ep-online.nl` |
| De antwoorden | 200 met een lijst van registraties; 400 de parameters voldoen niet; 401 geen geldige sleutel; 404 geen informatie gevonden |
| De velden die ik gebruik | `Energieklasse` ("de letter van het energielabel"), `Registratiedatum`, `Geldig_tot`, `Gebouwklasse` ("het soort gebouw: een woning of een utiliteitsgebouw") |
| Wat er niet staat | Of er een grens is op het aantal verzoeken; of verlopen labels in de lijst zitten; de volgorde van de lijst; wat er achter een doorverwijzing zou zitten |

**Eén plek waar ik van de letter afwijk, en waarom.** De documentatie geeft voor de toevoeging precies
vier tekens. In de BAG is een toevoeging één tot vier tekens lang. Ik vermoed een slordigheid in de
documentatie, maar weet het niet. De Worker laat daarom één tot vier tekens door en laat EP-Online
beslissen; weigert EP-Online, dan komt dat terug als "ongeldig". `detailaanduiding` gebruik ik niet: het
tabblad kent die niet.

## De Worker (`tools/energielabel/`)

| Stap | Wat hij doet |
|---|---|
| 1. Herkomst | Alleen een verzoek met precies `Origin: https://wim1201.github.io` gaat verder. Al het andere: 403, zonder EP-Online te vragen en zonder mee te tellen |
| 2. Invoer | Postcode, huisnummer, huisletter en toevoeging in de vorm van de documentatie. Past het niet: 400, zonder EP-Online te vragen |
| 3. Begrenzing | Hoogstens 20 per klokminuut en 300 per Nederlandse dag, over iedereen samen. Eroverheen: 429 met het aantal seconden tot het weer kan |
| 4. EP-Online | Eén verzoek, de sleutel in `Authorization`, acht seconden wachttijd, een doorverwijzing wordt niet gevolgd |
| 5. Het label | Van de registraties die vandaag nog geldig zijn, de laatst geregistreerde |
| 6. Het antwoord | Alleen labelklasse, registratiedatum, geldig tot en soort gebouw |

| Eis uit de opdracht | Hoe |
|---|---|
| De sleutel staat nergens in de repo, het log of een antwoord | Hij is een geheim bij Cloudflare (`EP_ONLINE_KEY`); plaatsen mislukt zonder. Een test stuurt de sleutel expres mee in nagebootste foutmeldingen van EP-Online en controleert dat hij in geen antwoord en geen logregel terugkomt |
| Slaat niets op in de repo | Niets. Bij Cloudflare bewaart hij alleen twee tellers (deze minuut, deze dag) |
| Het logboek | Eén regel per verzoek met de uitkomst. Geen adres, geen sleutel, geen IP-adres; de Worker leest het IP-adres niet |

**De teller.** De documentatie van Cloudflare zegt over haar ingebouwde begrenzer dat die bij benadering
telt en per vestiging, en verwijst voor een strikte grens naar een Durable Object. Zo is het gebouwd: één
klein object met eigen opslag. Dat kan op het gratis abonnement.

## Afscherming: wat ze wel en niet tegenhoudt

| Maatregel | Houdt tegen | Houdt niet tegen |
|---|---|---|
| Alleen de herkomst van de site | Een andere website die de Worker door de browser van haar bezoekers laat aanroepen. Een browser zet de herkomst zelf; een pagina kan die niet vervalsen | **Iemand met een eigen programma**: die kan elke herkomst opgeven. Het adres van de Worker staat in het gegevensbestand van de app en is voor iedereen te vinden. De herkomst is een drempel, geen slot |
| De sleutel als geheim | Dat iemand de sleutel te zien krijgt | Dat de sleutel gebruikt wordt door wie de Worker bereikt: binnen wat de Worker toelaat, maar op jouw naam |
| De begrenzing | Dat EP-Online van deze Worker meer dan 300 verzoeken per dag krijgt | **Dat één iemand de dag opmaakt**: er wordt niet per bezoeker geteld. Het vak toont dan de rest van de dag "te veel verzoeken". Meer dan dat vak raakt het niet |
| Eén adres, vier gegevens | Dat de Worker meer uit het register haalt dan het tabblad toont | Dat iemand binnen de grens adressen één voor één opvraagt |

**Eerlijk samengevat:** de Worker is voor wie moeite doet een openbare opvraagdienst voor hoogstens 300
labels per dag. De schade van misbruik is begrensd tot dat aantal op jouw sleutel en een vak dat een dag
niets toont. Echt afsluiten kan alleen met een inlog, en die heeft de app niet.

**Niet uitgezocht:** of de voorwaarden van RVO bij de sleutel dit gebruik toestaan.

## Het tabblad

| Uitkomst | Wat het vak toont |
|---|---|
| Label gevonden | De klasse in een blokje, daaronder "Geregistreerd", "Geldig tot" en "Soort gebouw", en: "Bron: EP-Online (Rijksdienst voor Ondernemend Nederland), opgevraagd op 18-11-2026. Getoond is het laatst geregistreerde label dat nog geldig is." |
| Geen geldig label | "Geen geldig energielabel gevonden voor dit adres." met de datum van opvragen |
| Te veel verzoeken | "Er worden op dit moment te veel energielabels opgevraagd. Probeer het over een minuut opnieuw." met een knop; is de dag op: "Er zijn vandaag te veel energielabels opgevraagd. Probeer het morgen opnieuw.", zonder knop |
| Dienst niet bereikbaar | "Het energielabel kon niet worden opgevraagd: de dienst is niet bereikbaar." met een knop "Opnieuw proberen" |
| EP-Online weigert het adres | "Voor dit adres kan geen energielabel worden opgevraagd." |
| In elk geval | De link "Zoek op EP-Online" met de zoekwaarde blijft staan |

**De instelling.** `energielabel_worker` in `config.json`. Leeg: het vak blijft zoals het was ("Nog niet
beschikbaar in de app." met de link), en de app vraagt niets. Ingevuld: de verversing zet het adres in
het gegevensbestand en het tabblad gebruikt het. Alleen een `https`-adres zonder vraagteken of spaties
wordt doorgegeven; iets anders geldt als leeg.

De knop "Opnieuw proberen" vraagt alleen de Worker opnieuw; pand, perceel en publicaties blijven staan.

## Gemaakte keuzes

| Keuze | Waarom |
|---|---|
| "Het laatste label" is het laatst geregistreerde dat nog geldig is | De opdracht noemt "het laatste label" en de uitkomst "geen geldig label gevonden". Een verlopen label tonen als label zou misleiden |
| Geldig tot en met de laatste dag, in Nederlandse tijd | Een label dat vandaag afloopt, geldt vandaag nog |
| De grenzen: 20 per minuut, 300 per dag | Ruim voor één gebruiker en een enkele meekijker, en klein genoeg om de sleutel te sparen. Een schatting; aanpasbaar in `wrangler.jsonc` |
| Tellen over iedereen samen, niet per bezoeker | Per bezoeker vraagt het IP-adres bij te houden. Zie "Afscherming" |
| Antwoordt de teller niet, dan wordt EP-Online niet gevraagd | De sleutel beschermen gaat voor |
| De instelling in `config.json`, niet in een bestand van de app | Daar staan de andere instellingen; een test bewaakt dat ze leeg in de repo staat |
| Huisletter en toevoeging apart naar de Worker | Zo kent PDOK ze en zo vraagt EP-Online ze |
| Geen tussenopslag van labels | Minder om te bewaren en uit te leggen. Elk bezoek aan een adres is één verzoek |
| De Worker heet `tilburg-signalen-energielabel` | Naast `tilburg-signalen-planner`, in hetzelfde account |

## Tests

503 tests geslaagd in de container (was 440; 10 overgeslagen: 6 van de film, 4 die alleen op verzoek
tegen de echte bronnen draaien).

| Wat de opdracht vroeg | Tests | Aantal |
|---|---|---:|
| Gevonden | De vier gegevens en niets anders; de vraag aan EP-Online zoals de documentatie zegt; van meer registraties de laatste geldige; geldig tot en met de laatste dag; de Nederlandse dag; de koppen van het antwoord | 6 |
| Niet gevonden | 404 van EP-Online; een lege lijst; alleen verlopen labels; registraties zonder klasse of datum | 4 |
| Toevoeging | Huisletter en toevoeging naar hun eigen parameter; leeg wordt weggelaten; de postcode in de vorm van EP-Online | 3 |
| Foute invoer | 26 gevallen per veld worden geweigerd zonder EP-Online te vragen; de vormen van de documentatie; een weigering van EP-Online zelf; alleen GET; het adres van EP-Online komt nooit uit het verzoek | 5 |
| Verkeerde herkomst | 12 andere of ontbrekende herkomsten, waaronder `http` in plaats van `https` en adressen die erop lijken; een voorvraag van elders; een voorvraag van de app; zonder instelling niemand; de instelling is de live site | 5 |
| De begrenzing | De vierde in een minuut; de volgende minuut; een geweigerd verzoek telt niet; de zesde van een dag tot middernacht in Nederland; de dag gaat voor de minuut; elk verzoek aan EP-Online telt; een teller die niet antwoordt; instellingen die geen getal zijn; de grenzen in de instellingen | 9 |
| Een dienst die niet antwoordt | Te laat; geen verbinding; een foutstatus of doorverwijzing; iets dat geen lijst is; de sleutel geweigerd; EP-Online zegt zelf "te veel"; zonder sleutel wordt niets gevraagd | 7 |
| De sleutel en het adres | In elf uitkomsten staat de sleutel in geen antwoord en geen logregel, en het adres in geen logregel; geen sleutel in de repo; bestanden met geheimen blijven buiten git | 3 |
| De instellingen | De sleutel is een verplicht geheim; het adres van EP-Online; eigen naam, los van de planner; de teller; alleen de herkomst wordt van de bezoeker gelezen; niets bewaard dan de tellers; de doorverwijzing; geen pakketten | 8 |
| Het vak, logica | Zonder instelling niets vragen; het adres naar de Worker; een adres zonder postcode of huisnummer; het label met bron en datum; elke andere uitkomst haar eigen tekst; een vreemd antwoord is geen label; de instelling alleen als `https`-adres; de instelling staat leeg | 8 |
| Het vak, browser op 320 pixels | De vraag aan de Worker met het adres en zonder sleutel of cookie; het label met bron en datum; de drie andere uitkomsten elk met eigen tekst; de link blijft en het vak past; opnieuw proberen vraagt alleen de Worker | 5 |

Twee bestaande tests zijn aangepast. De ene eiste dat het tabblad op één plek iets ophaalt; dat zijn er nu
twee, de registers van PDOK en de Worker, en de test eist dat beide een kale vraag zijn zonder iets mee te
sturen. De andere zocht "Nog niet beschikbaar in de app." twee keer in één functie; het energielabel heeft
nu een eigen functie.

### In de runtime van Cloudflare, op deze machine (15:50 – 15:58 uur)

Niet onderdeel van de vaste tests: `npx wrangler dev` draait de Worker in de echte runtime van Cloudflare,
lokaal, tegen een nagebootst EP-Online en met een verzonnen sleutel.

| Geval | Uitkomst |
|---|---|
| Gevonden; huisletter en toevoeging | 200 met het label; het nagebootste EP-Online ontving `postcode=5037PL&huisnummer=12&huisletter=B&huisnummertoevoeging=2` en de sleutel in `Authorization` |
| Niet gevonden; foute invoer | 404 en 400 |
| Geen herkomst; een andere herkomst | 403, EP-Online niet gevraagd |
| Voorvraag; POST | 204 en 405 |
| EP-Online geeft een fout; antwoordt niet; is weg | 502; afgebroken na 8,0 seconden; 502 |
| De grens per minuut (voor de proef 6) en per dag (voor de proef 8) | 429 met `Retry-After`; de teller bleef staan na een herstart |
| De sleutel in het logboek of een antwoord | Nee |
| `npx wrangler deploy --dry-run` | Instellingen geaccepteerd, bundel 8 KiB, niets geplaatst |

**Gevonden gebrek, hersteld.** In die runtime mislukte eerst elk verzoek aan EP-Online: ik had ingesteld
dat een doorverwijzing een fout moet geven, op een manier die Cloudflare niet kent. Onder Node, waar de
vaste tests draaien, viel dat niet op. Nu wordt een doorverwijzing niet gevolgd en als fout behandeld; een
test bewaakt de instelling. Zonder deze proef was de Worker geplaatst en had hij nooit een label gegeven.

## Bekeken op schermafbeeldingen (320 pixels)

Het vak met een gevonden label (klasse in een blokje, drie regels, bronregel, link) en het vak met "te
veel verzoeken" (melding, knop, link). In de sessie gemaakt; niet in de repo.

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| **De echte sleutel en de echte dienst** | Er is geen sleutel. EP-Online is nooit aangeroepen. De eerste echte toets is stap 5 in de README |
| Of de sleutel zonder iets ervoor in `Authorization` hoort | Zo lees ik de documentatie. Mocht EP-Online hem weigeren, dan toont het vak "niet bereikbaar" en meldt het logboek "sleutel geweigerd" |
| Hoe een echt antwoord eruitziet | De datums zijn volgens de documentatie een tijdstip; de Worker neemt de eerste tien tekens als datum. Wat er in `Gebouwklasse` staat ("Woningbouw" is mijn voorbeeld, niet uit de documentatie), en of verlopen labels in de lijst zitten, weet ik niet |
| Meer registraties op één adres | Bij een gebouw met delen zonder eigen adres (`Detailaanduiding`) kan het laatste label van een ander deel zijn. Het tabblad zegt daar niets over |
| Een korte toevoeging | Zie "Wat de documentatie zegt" |
| Het plaatsen bij Cloudflare | Niet gedaan. De teller is lokaal in de runtime geprobeerd, niet in het netwerk van Cloudflare |
| De voorwaarden van RVO | Niet gelezen |
| De nieuwe tests op GitHub | Draaien op de pull request; de uitkomst staat in het bericht aan Wim en komt bij het samenvoegen in dit verslag |
| Op een echte telefoon | Niet te doen vanuit deze container |
| Het vak na een verversing bij terugkeer | Het label wordt dan niet opnieuw opgevraagd; het blijft staan zoals het was |

## Buiten dit verslag

- **Niet samengevoegd:** de pull request blijft open tot Wim het zegt.
- **Niets geplaatst, geen sleutel aangevraagd, EP-Online niet aangeroepen.**
- **De planner, `dagelijks.yml`, `tests.yml` en het schema zijn niet gewijzigd.** `cache/ophaalcache.json` is
  niet gecommit en niets is geforceerd.
- **Voor de proef in de runtime** is wrangler tijdelijk opgehaald in een werkmap buiten de repo; de
  verzonnen sleutel stond alleen daar en is na de proef verwijderd.
- **De documentatie van EP-Online** is één keer opgehaald (twee bestanden); die van Cloudflare is
  geraadpleegd voor de teller.
- **Geen subsessie**, en niets met ElevenLabs.
