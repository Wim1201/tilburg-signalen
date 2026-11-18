# Tilburg Signalen: verslag tests bij een pull request, de ochtendregel bij één regio, en "Overig"

| | |
|---|---|
| Datum | 18-11-2026, 14:50 – 15:01 uur |
| Versie | versie 2 van de app met de regio's, branch `claude/optimistic-gauss-sb0xpy`, opnieuw gestart vanaf `main` op commit `7555b87` (na PR 23) |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen`; Chromium via Playwright |
| Brondata | Geen opvraging bij de bronnen. Voor de controle: de gegevens van de live site, bijgewerkt 18-11-2026, 14:52 uur |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_weergavekeuze-volgorde-fase_18-11-2026.md` |

## Stand

PR 23 is samengevoegd op verzoek van Wim (14:50 uur, merge-commit `7555b87`). **Run 32, de run die
daarop volgde, is groen**, ook de controle van de live site. `main` is daarmee niet meer rood. De
weergavekeuze, de nieuwe volgorde bij gelijke score en het fasefilter staan live.

De drie nieuwe onderdelen zijn gebouwd en staan op de werkbranch, in een pull request die **open blijft
en niet is samengevoegd**. `dagelijks.yml` en het schema zijn niet gewijzigd.

## Correcties en aanvullingen op eerdere verslagen

| Tijdstip | Wat |
|---|---|
| 18-11-2026, 15:01 uur | **`main` is weer groen; "`main` is rood" in het vorige verslag is daarmee achterhaald.** Run 32 slaagde op alle onderdelen. |
| 18-11-2026, 15:01 uur | **De nieuwe test met de lettertypen van de app zelf heeft op GitHub echt gedraaid en is geslaagd; "Niet nagelopen: of de nieuwe test op de runner van GitHub de lettertypen binnenkrijgt" is daarmee afgehandeld.** De browsertests telden 66 tests zonder één overgeslagen, de controle van de live site 63 zonder één overgeslagen. Was de lettertypedienst niet bereikbaar geweest, dan had er een overgeslagen test gestaan. |
| 18-11-2026, 15:01 uur | **"De ochtendregel en de tegel Nieuw zeggen bij Alleen Zeeland iets anders" en "Standen in geen trede" uit het vorige verslag zijn opgepakt**, in deze pull request. |
| 18-11-2026, 15:01 uur | **Het aantal tests is 440 (was 430).** Er zijn er 10 bij: 8 voor de nieuwe workflow en 2 voor de logica. Bestaande browsertests zijn uitgebreid. |

## Run 32 op GitHub, na het samenvoegen van PR 23 (18-11-2026, 14:50 – 14:55 uur)

| Stap | Duur | Verzoeken | Weigeringen (HTTP 429) | Uitkomst |
|---|---:|---:|---:|---|
| Tests | 15 s | geen | | 430 tests geslaagd; 77 overgeslagen, omdat de browser in die stap nog niet klaarstaat |
| Browser klaarzetten | 18 s | | | Geslaagd |
| **Browsertests** | 47 s | geen naar de bronnen | | **66 tests geslaagd, geen overgeslagen** (was 57 in run 30) |
| Gebied bijwerken | 18 s | 29 | 0 | Geslaagd |
| Berichten ophalen | 1 min 10 s | 39 | 0 | Geslaagd, zonder waarschuwing; niets mislukt |
| Cache bewaren | minder dan 1 s | | | "Cache ongewijzigd" |
| Publiceren | 13 s | | | Geslaagd |
| **Controle van de live site** | 34 s | | | **63 tests geslaagd, geen overgeslagen** (was 54 in run 30) |
| **Hele run** | **4 min 30 s** | **68** | **0** | **Groen** |

Berichten: 3.888, waarvan 1.140 in de kern; geen wachtende regioberichten; cache 963 kB (64 procent).

## Opdracht

1. Een tweede workflow in een eigen bestand die bij elke pull request alleen de tests en de
   browsertests draait, zonder ophalen, publiceren of cache. `dagelijks.yml` en het schema blijven
   ongewijzigd, zodat de planner er niets van merkt.
2. In de weergave "Alleen …" een regio: duidelijk maken dat de ochtendregel over de kern gaat.
3. Een vierde keuze "Overig" in het filter Fase voor standen die in geen trede vallen.

## 1. Tests bij een pull request

Nieuw bestand: `.github/workflows/tests.yml`.

| Onderdeel | Hoe het is ingericht |
|---|---|
| Wanneer | Bij elke pull request: bij het openen en bij elke nieuwe push ernaar. Nergens anders: geen schema, geen push naar `main`, niet met de hand |
| Wat het draait | Dezelfde twee stappen als `dagelijks.yml`, met dezelfde opdrachten: de tests, dan de browser klaarzetten en de browsertests |
| Wat het test | De samenvoeging van de pull request met `main`: wat er na het samenvoegen zou staan |
| Wat het niet doet | Geen gebied bijwerken, geen berichten ophalen, geen cache, geen publiceren, geen controle van de live site |
| Rechten | Alleen lezen. Het kan niets terugschrijven in de repo en heeft geen geheimen nodig |
| Naast de verversing | Een eigen wachtrij per pull request. Een verversing wacht er nooit op en andersom; een nieuwe push breekt de testrun van de vorige af |
| De planner | Kent alleen `dagelijks.yml` en vraagt alleen de runs van dat bestand op. Het nieuwe bestand komt daar niet in voor |
| `dagelijks.yml` | Niet gewijzigd, geen teken |

**Waarom dit helpt (feit uit vandaag).** Run 26 en run 31 werden rood na het samenvoegen, op een test
die hier slaagde en op GitHub niet. Met deze workflow draait dezelfde test op GitHub vóór het
samenvoegen, op de pull request zelf.

**Wat het niet vangt.** De controle van de live site blijft achteraf: die kan pas na het publiceren.
Een verschil tussen de momentopname in de repo en de live gegevens ziet deze workflow dus alleen voor
zover de vaste testsituaties het nabootsen.

## 2. De ochtendregel bij "Alleen" een regio

Tonen de lijsten één regio alleen, dan staat direct onder de ochtendregel, met een rode streep ervoor:

> Dit gaat over de kern. De lijsten hieronder tonen alleen Zeeland.

Bij "Samen", bij "Alleen de kern" en zonder gekozen regio staat de regel er niet: dan gaan de
ochtendregel en de lijsten over dezelfde berichten, of de lijsten over meer.

## 3. "Overig" in het filter Fase

De groep "Trede" in het filter heeft nu vier keuzes. De vierde is alles wat in geen van de drie treden
valt, ook een bericht zonder stand. De vier samen zijn dus alle berichten, en geen bericht valt in twee.

| Keuze | Standen | In de kern nu (ontwikkellocaties en onzeker: 108) |
|---|---|---:|
| Vroeg | Voornemen, Aanvraag | 27 |
| Midden | Ontwerp, Bekendmaking, Besluit | 26 |
| Laat | Vastgesteld, Verleend, Herstelbesluit | 36 |
| **Overig** | Wat overblijft; nu: Beslistermijn verlengd (8), Voornemen tot verkoop (5), Onherroepelijk (3), Ontwerpbesluit (1), Geweigerd (1), Surseance verleend (1) | 19 |

In de lijst staat het als "Overig: standen in geen trede (19)". De indeling in treden blijft een keuze
van deze app en komt niet uit de bronnen; "Overig" is daarvan het restant.

## Gemaakte keuzes

| Keuze | Waarom |
|---|---|
| De workflow draait bij elke pull request, ook als die alleen `docs/` raakt | Zo stond het in de opdracht, en een run kost ongeveer twee minuten |
| Twee stappen zoals in `dagelijks.yml`, niet alles in één keer | Dan zijn de uitkomsten naast elkaar te leggen: dezelfde stap, dezelfde opdracht, hetzelfde aantal tests |
| Een test bewaakt dat de opdrachten in beide bestanden gelijk blijven | Anders test de pull request op den duur iets anders dan de run erna |
| De regel over de kern alleen bij één regio alleen | Alleen daar spreken de ochtendregel en de tegels elkaar tegen |
| "Overig" telt ook een bericht zonder stand | Zo vormen de vier keuzes samen het geheel |
| "Ontwerpbesluit" en "Onherroepelijk" blijven onder Overig | Ze horen duidelijk bij midden en laat, maar de drie treden zijn afgesproken met acht standen; ze verplaatsen is een nieuw besluit |

## Tests

440 tests geslaagd in de container (was 430; 10 overgeslagen: 6 van de film, 4 die alleen op verzoek
tegen de echte bronnen draaien).

| Wat | Aantal |
|---|---:|
| De nieuwe workflow: start alleen bij een pull request; `dagelijks.yml` start daar niet; dezelfde tests met dezelfde opdrachten; geen stap wordt overgeslagen; haalt niets op, publiceert niets en schrijft niets; eigen wachtrij; stopt vanzelf als hij blijft hangen; de planner kent alleen `dagelijks.yml` | 8 |
| Logica: "Overig" is alles wat in geen trede valt, en de vier keuzes samen zijn het geheel | 1 |
| Logica: de regel over de kern staat er alleen bij één regio alleen | 1 |

Uitgebreid, zonder nieuwe testnaam:

| Bestaande browsertest | Wat erbij is gekomen |
|---|---|
| De weergavekeuze, 320 pixels, in beide situaties | De regel over de kern staat er bij "Alleen" de regio, met de naam van de regio, en op zeven andere momenten niet |
| Het filter Fase | De vierde keuze met haar aantal en haar kaarten; de vier keuzes samen zijn de hele ranglijst |
| De vaste situatie | De regel over de kern staat er letterlijk |

Ook gedraaid: de 63 browsertests tegen een kopie van de site met de gegevens van de live site van 14:52
uur. Alle 63 geslaagd.

**Gevonden tijdens het bouwen:** de browsertest wachtte bij "Overig" een halve minuut op een knop "Toon
alles" die er bij tien of minder kaarten niet is. De test slaagde wel, maar de hele reeks duurde
daardoor ruim twee minuten. Hersteld: de test tikt de knop alleen aan als hij er staat.

## Bekeken op een schermafbeelding

Het tabblad Berichten op 320 pixels met "Alleen Zeeland": de regel over de kern staat op twee regels
onder de ochtendregel. In de sessie gemaakt; niet in de repo.

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| De nieuwe workflow op GitHub | Zie "De eerste run van de nieuwe workflow" hieronder, als die er bij het schrijven al is |
| Een pull request van buiten de repo | Niet geprobeerd. De workflow heeft alleen leesrechten en geen geheimen nodig; GitHub kan voor zo'n pull request eerst om goedkeuring vragen |
| De lettertypedienst als die traag is | De test met de echte lettertypen slaat zichzelf dan over. Dat is in run 32 niet gebeurd; hoe vaak het voorkomt, weet ik niet |
| De regel over de kern op een echte telefoon | Niet te doen vanuit deze container; bekeken in Chromium op 320 pixels |
| De wekelijkse volledige run | Nog niet gedraaid op GitHub; de eerste is zondag 22-11-2026, 04:30 uur |

## Buiten dit verslag

- **Niet samengevoegd:** de nieuwe pull request blijft open tot Wim het zegt.
- **PR 23 is samengevoegd**, met akkoord van Wim.
- **`dagelijks.yml`, het schema en de planner zijn niet gewijzigd.** `cache/ophaalcache.json` is niet
  gecommit en niets is geforceerd.
- **De scores en `signalen/relevantie.py` zijn niet aangeraakt.**
- **De bronnen zijn niet belast.** De live site is één keer gelezen (vijf bestanden).
- **De logs van run 32 zijn door een hulpsessie uitgelezen.** Niets met ElevenLabs.
