# Tilburg Signalen: verslag video van de ochtendronde

| | |
|---|---|
| Datum | 16-11-2026, 20:00 – 22:20 uur; aangevuld op 17-11-2026, 08:20 – 08:50 uur (browsertests op GitHub) |
| Versie | versie 2 van de app, branch `claude/awesome-brown-i18j4o` |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | `site/data/berichten.json` zoals het in de repo staat (bijgewerkt 16-11-2026, 15:37 uur); vergeleken met de nieuwste run op de live app (17:38 uur) |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_versie-2-huisstijl_16-11-2026.md` |

## Stand

De video is gemaakt: 70 seconden, 1920 × 1080, 5,2 MB (5.167.073 bytes), met Nederlandse stem en drie
zachte geluidjes. **Hij staat niet in de repo** (zie de correctie hieronder); hij is via de sessie
aan Wim geleverd. Opnieuw maken kan met `tools/video/` en kost geen credits.

**Ik heb de video niet kunnen beluisteren.** Beeld, lengte, pauzes, volume en de gelijkloop van
beeld en stem zijn gemeten. Uitspraak en klank zijn niet beoordeeld; dat moet Wim doen.

**Aanvulling 17-11-2026:** de tests in een echte browser draaien nu ook op GitHub, en na elk
publiceren wordt de live site getest. Zie "Browsertests op GitHub (17-11-2026)".

## Correcties en aanvullingen

| Tijdstip | Wat |
|---|---|
| 17-11-2026, 09:07 uur | **Voorbereid, niet live: een planner op Cloudflare die de workflow start als GitHub dat zelf niet doet.** Op verzoek van Wim. Staat op de werkbranch, niet op `main`; er is niets bij Cloudflare geplaatst en er is geen token. Zie "Planner op Cloudflare (voorbereid)". |
| 17-11-2026, 09:07 uur | **De workflow op de werkbranch heeft een tweede invoer bij de handmatige run: `gepland`.** Daarmee gedraagt een run die de planner start zich als een geplande run (geen browsertests vooraf). Het schema zelf is niet gewijzigd. Dit vult "Wat er nu staat" onder "Browsertests op GitHub" aan en geldt pas na samenvoegen. |
| 17-11-2026, 08:45 uur | **Het plan voor de browsertests op GitHub is uitgevoerd; "Dit plan is niet uitgevoerd" onder "Plan voor later" geldt niet meer.** Wim koos mogelijkheid C. Zie "Browsertests op GitHub (17-11-2026)". |
| 17-11-2026, 08:45 uur | **Mijn schatting van de extra duur klopte voor de helft, en de bewaarde browser maakt het niet sneller.** Geschat: 30 tot 60 seconden erbij zonder bewaarde browser, 15 tot 25 met. Gemeten zonder: 35 seconden erbij in de job bouwen. Met bewaarde browser duurde het terugzetten 13,5 seconden, tegen 5,3 en 6,4 seconden voor opnieuw downloaden. Zie "Gemeten duur". |
| 17-11-2026, 08:45 uur | **Stap 5 van het plan noemde `OK (skipped=7)` in het logboek; bij mogelijkheid C staat dat er niet letterlijk.** De snelle stap Tests toont nog steeds `OK (skipped=31)`; de 24 browsertests draaien in een eigen stap, die `Ran 24 tests` en `OK` toont. Samen blijven dezelfde 7 tests over. Zie "Run 12 op GitHub". |
| 17-11-2026, 08:45 uur | **Het bolletje "+1" op de tegel Onzeker staat nu op de bovenrand van de tegel, niet meer rechtsboven naast het getal.** De eerste run met browsertests op GitHub faalde erop. Door Wim gekozen aan de hand van een voor/na-beeld. Dit wijzigt punt 1 onder "Gevonden tijdens het opnemen"; de film toont nog de oude plaats. Zie "Run 11 mislukte". |
| 17-11-2026, 08:45 uur | **Een handmatige run vanaf een andere branch dan `main` publiceert niet meer.** Voorheen probeerde de job publiceren dat wel. Met Wim afgestemd. |
| 17-11-2026, 08:45 uur | **De geplande run van 06:45 uur is niet gestart.** Onder "Buiten dit verslag" stond dat dit vandaag te zien zou zijn. Om 08:43 uur stond er bij Actions geen enkele run met de aanleiding "schedule", ook niet van eerdere dagen. De live site stond tot 08:40 uur op de stand van 16-11-2026, 22:10 uur. Oorzaak niet onderzocht; het schema is niet gewijzigd. |
| 16-11-2026, 22:12 uur | **Een push die alleen `docs/` raakt, start geen run meer; "een push naar `main` start een nieuwe run" onder "Buiten dit verslag" geldt daarvoor niet meer.** Op verzoek van Wim in de workflow gezet. Zie "Workflow: verslagen starten geen run". Of het op GitHub werkelijk zo werkt, blijkt pas bij de eerstvolgende push die alleen `docs/` raakt. |
| 16-11-2026, 22:12 uur | **Het stuk "Samengevoegd en live" stond op de werkbranch en nog niet in `main`.** Wim vroeg het samen te voegen; dat gebeurt in dezelfde pull request als de wijziging van de workflow. |
| 16-11-2026, 22:03 uur | **Versie 2 is samengevoegd met `main` en staat live; "Samenvoegen met `main` is niet gedaan en er is geen pull request" onder "Buiten dit verslag" geldt niet meer.** Wim keurde de film goed en vroeg om de pull request en het samenvoegen. Zie "Samengevoegd en live". |
| 16-11-2026, 21:34 uur | **De film is opnieuw gemaakt met een lager videoniveau; de film van 20:51 uur is daarmee vervangen.** Wim vroeg het geluidsspoor te controleren. Het geluid was in orde, maar het beeld stond op H.264-niveau 5.0, boven wat Apple voor de iPhone opgeeft (High Profile niveau 4.2). Zie "Controle van het geluidsspoor". De grootte is nu 5.239.918 bytes; overal waar dit verslag 5.167.073 bytes of 5,2 MB voor de film noemt, gaat het om de eerste versie. |
| 16-11-2026, 21:00 uur | **De film is uit de repository gehaald; "De video staat in `docs/video/`" in de versie van 20:52 uur van dit verslag geldt niet meer.** Ik had de film (5,2 MB) en een stilstaand beeld (0,1 MB) in git gezet en gepusht zonder de grootte te noemen of te vragen of dat de bedoeling was. Wim wees erop dat zo'n bestand in een openbare repo voorgoed in de geschiedenis blijft. Zie "Film uit de repository". |
| 16-11-2026, 21:00 uur | **De geschiedenis van de branch is herschreven.** De commit `4626889` (20:51 uur) is vervangen door `7523af7`, met dezelfde inhoud zonder de film en het stilstaande beeld. Wie `4626889` al had opgehaald, moet de branch opnieuw ophalen. Er was geen pull request en niets is samengevoegd met `main`. |
| 16-11-2026, 21:00 uur | **Aanvulling op wat ik over "Bijgewerkt ma 16 nov, 15:37" schreef.** Dat is het tijdstip van de laatste geslaagde verversing van het gegevensbestand dat de film gebruikte, niet van de laatste wijziging van de berichten. Het bestand in de repo is een momentopname van 15:37 uur; de live app stond op dat moment op 17:38 uur. Zie "Wat Bijgewerkt betekent". |
| 16-11-2026, 21:00 uur | **Het inkorten van twee geluidjes had ik moeten voorleggen.** Het akkoord gold voor het voorstel zoals het er lag (signaal 1,5 s, veeg 0,8 s). Ik heb ze ingekort om onder de 920 credits te blijven en dat pas achteraf gemeld. |
| 16-11-2026, 20:52 uur | **Correctie op de tussenstand van dit verslag (commits `a04749b` en `54d570b`, 20:12 en 20:13 uur): de tabel "Voorstel dat op akkoord wacht" is vervangen door "Raming en werkelijk verbruik".** De tekst is op verzoek van Wim op twee plaatsen gewijzigd, twee geluidjes zijn korter gemaakt en de geluidjes kostten een derde van wat ik had berekend. |
| 16-11-2026, 20:52 uur | **Mijn verdeling van de raming over de geluidjes (11 credits per seconde) klopte niet.** Dat getal had ik zelf afgeleid uit de raming van ElevenLabs voor de drie samen. Afgerekend is ongeveer 3,3 credits per seconde. De raming voor de stem klopte wel. |
| 16-11-2026, 20:11 uur | **De tegel Onzeker toont nieuwe berichten niet meer als "Onzeker · 1 nieuw" maar als een bolletje "+1".** De tekst brak af over twee regels, waardoor die tegel er anders uitzag dan de andere twee. Gevonden in de proefopname. Dit wijzigt wat in het vorige verslag over die tegel staat. |
| 16-11-2026, 20:11 uur | **De lege proefwerkstroom in het ElevenLabs-account is niet meer leeg.** Verwijderen kan niet via de koppeling. Het oude knooppunt is eruit gehaald en de werkstroom is hergebruikt voor de stem en de geluidjes van de video. Zie "Opruimen". |

De gegevens en de regels zijn niet gewijzigd: `signalen/`, `config.json`, `site/data/` en `cache/`
zijn onaangeroerd (`git diff` leeg).

## Opdracht

Een schermopname van 60 tot 90 seconden waarin de app wordt gebruikt zoals een projectontwikkelaar
dat 's ochtends doet (ochtendscherm, top 10, Details, de tegel Onzeker), met een cursor die
aanwijst wat er getoond wordt, een Nederlandse stem van ElevenLabs en een paar zachte geluidjes in
de huisstijl. Vooraf model, stem, raming en tekst voorleggen en op akkoord wachten. Alleen spraak
en geluidjes, geen videomodellen. Niet meer dan twee generaties per stem. Fouten uit het opnemen
vastleggen en herstellen, met tests. De ongebruikte afbeeldingsvarianten en de lege
proefwerkstroom opruimen of melden dat het niet kan.

## ElevenLabs

### Verloop

| Tijdstip | Handeling | Uitkomst |
|---|---|---|
| 20:05 – 20:10 uur | Alleen gelezen en klaargezet, niets gegenereerd: lijst met Nederlandse stemmen, modellen en instellingen, verbruik; oud knooppunt uit de proefwerkstroom verwijderd; vier knooppunten klaargezet (stem, tik, signaal, veeg); raming opgevraagd | Raming 919,7 credits, voorgelegd als 920. Verbruik 17.958 |
| 20:12 uur | Voorstel aan Wim: model, stem, raming, tekst | — |
| ca. 20:38 uur | Akkoord van Wim op model, stem Daan en 920 credits, met twee tekstwijzigingen en de opdracht eerst de Bellinistraat en de 141 woningen te controleren | — |
| 20:40 uur | Controle tegen de nieuwste run | Zie "Controle van de tekst tegen de gegevens" |
| 20:41 – 20:43 uur | Tekst aangepast en de raming drie keer opnieuw opgevraagd | Zie "Binnen de 920 blijven" |
| 20:44 uur | Gegenereerd: één opname van de stem, één variant van elk geluidje | Stem 64,4 seconden; geluidjes 0,5, 1,0 en 0,5 seconde |
| 20:51 uur | Verbruik afgelezen | 18.862 |

### Raming en werkelijk verbruik

| Onderdeel | Model | Raming bij het voorstel (20:10 uur) | Raming vlak voor het uitvoeren (20:43 uur) | Werkelijk |
|---|---|---|---|---|
| Stem "Daan", één opname | `eleven_multilingual_v2` | 888,9 | 896,9 | 897 |
| Tik, 0,5 s | `eleven_text_to_sound_v2` | 5,5 | 5,5 | 1,7 |
| Signaal (voorstel 1,5 s, uitgevoerd 1,0 s) | `eleven_text_to_sound_v2` | 16,5 | 11,0 | 3,3 |
| Veeg (voorstel 0,8 s, uitgevoerd 0,5 s) | `eleven_text_to_sound_v2` | 8,8 | 5,5 | 1,7 |
| **Samen** | | **919,7 (goedgekeurd: 920)** | **918,9** | **904** |

| Meting | Waarde |
|---|---|
| Verbruik vóór / na (accountteller) | 17.958 / 18.862 van 110.153 credits |
| Verbruik deze ronde | 904 credits, 16 onder de goedgekeurde 920 |
| Generaties met de stem | 1 van de toegestane 2; de tweede is niet gebruikt |
| Verbruik van de drie rondes samen | 13.630 credits (12.726 voor beeldmerk en illustratie, 904 voor de video) |

De ramingen per geluidje in de eerste twee kolommen zijn door mij berekend uit de raming voor de
drie samen (30,8 en 22,0 credits); alleen die totalen komen van ElevenLabs. De werkelijke bedragen
per geluidje (1,67, 3,33 en 1,67) komen uit het resultaat van de generatie.

### Binnen de 920 blijven

De twee tekstwijzigingen maakten de tekst 16 tekens langer. De raming voor de stem ging daardoor
van 888,9 naar 904,9 en het totaal naar 935,7: boven de goedgekeurde 920. Ik heb niet opnieuw om
akkoord gevraagd maar het totaal teruggebracht zonder de gesproken woorden te veranderen:

| Stap | Wat | Raming totaal |
|---|---|---|
| 1 | Tekst met de twee wijzigingen | 935,7 |
| 2 | Spaties rond de vier pauzetekens weggehaald (8 tekens) | 927,7 |
| 3 | Signaal van 1,5 naar 1,0 seconde, veeg van 0,8 naar 0,5 seconde | 918,9 |

Uit de ramingen bleek: de stem kost 1 credit per teken, en elk pauzeteken kost ongeveer 10 credits,
hoe het ook geschreven is. Achteraf was stap 3 niet nodig geweest: de geluidjes kostten samen 6,7
credits in plaats van de geraamde 22. Dat wist ik vooraf niet.

### De stem

| | |
|---|---|
| Stem | In de stemmenlijst: "Daan - Calm, Professional Narrator". In het resultaat van de generatie heet dezelfde stem (zelfde id `NZxSzTQSMSWwkdFLuZsv`) "Dean - Calm, Professional, versatile". |
| Lengte | 64,4 seconden voor 151 woorden |
| Tempo | Rustig: tussen zinnen pauzes van 0,9 tot 1,3 seconde, binnen zinnen van 0,3 tot 0,5 seconde. Tussen de scènes 1,4 tot 1,6 seconde |
| Volume in de film | −18,2 LUFS, piek −2,8 dB |

### Gesproken tekst (zoals gegenereerd)

1. **Ochtendscherm.** Goedemorgen. Tilburg Signalen zet elke ochtend op een rij waar rond Tilburg ontwikkellocaties ontstaan. Bovenaan staat wat er sinds je vorige bezoek bij is gekomen: in dit voorbeeld twee nieuwe locaties. Eén tik op Nieuw laat alleen die twee zien.
2. **Top 10.** Terug naar de ranglijst. De hoogste rang staat bovenaan. Elke kaart begint met het rangnummer en één zin die zegt waarom dit bericht telt. Nummer één: een planwijziging bij de Bellinistraat in Tilburg, waarin honderdeenenveertig woningen worden genoemd. Daaronder de rest van de top tien.
3. **Details.** Wil je meer weten, dan open je de details. Daar staan de score, de bron en een link naar de bekendmaking zelf en naar de kaart.
4. **Onzeker.** Onder Onzeker staan berichten met een signaal waarvan de omvang nog niet vaststaat. Ze blijven zichtbaar, zodat je zelf kunt oordelen.
5. **Slot.** Tilburg Signalen. Ontwikkellocaties rond Tilburg, op een rij.

Wijzigingen van Wim ten opzichte van het voorstel: "in dit voorbeeld twee nieuwe locaties" (was:
"vandaag twee nieuwe locaties") en de slotzin (was: "Elke ochtend in beeld wat er speelt."). De
slotzin staat ook op het slotbeeld.

### Controle van de tekst tegen de gegevens (20:40 uur)

| Bron | Bijgewerkt | Nummer één | Woningen | Berichten |
|---|---|---|---|---|
| `site/data/berichten.json` in de repo | 16-11-2026, 15:37 uur | Wijzigingsbesluit TAM-omgevingsplan Hoofdstuk 22s, Bellinistraat | 141 | 81 ontwikkellocaties, 23 onzeker, 1.012 weggefilterd |
| Live app (`wim1201.github.io/tilburg-signalen/data/berichten.json`), nieuwste run | 16-11-2026, 17:38 uur | Hetzelfde bericht | 141 | Gelijk; geen enkel bericht verschilt, top 10 identiek |

De tekst is dus niet aangepast. De volgende geplande run is dinsdag 06:45 uur; die kan de
rangorde veranderen. De video toont de gegevens van 16-11.

### Opruimen

| Gevraagd | Uitkomst |
|---|---|
| Vier ongebruikte afbeeldingsvarianten verwijderen | **Kan niet via de koppeling.** Er is geen functie om een gegenereerde afbeelding uit de geschiedenis te verwijderen; bij het verwijderen van een knooppunt blijven de afbeeldingen in de geschiedenis staan. Wim kan ze zelf verwijderen in ElevenLabs onder Image & Video → History. |
| Lege proefwerkstroom verwijderen | **Kan niet via de koppeling**: er is geen functie om een werkstroom te verwijderen. Wel gedaan: het ongebruikte afbeeldingsknooppunt eruit verwijderd (20:08 uur) en de werkstroom hergebruikt voor de video, zodat er geen vierde bij is gekomen. |

Stand van het account: drie werkstromen, alle drie "Untitled flow" (hernoemen kan ook niet via de
koppeling): beeldmerk, illustratie, en de voormalige proefwerkstroom met nu vier knooppunten
"Video ochtendronde: stem / tik / signaal / veeg".

## De video

| | |
|---|---|
| Bestand | `tilburg-signalen_ochtendronde.mp4` (H.264 en AAC, 30 beelden per seconde); niet in de repo, geleverd via de sessie. Wie hem opnieuw maakt, krijgt hem in `tools/video/uit/`, een map die git overslaat |
| Lengte | 70,0 seconden |
| Beeld | 1920 × 1080: links de scène en de gesproken tekst, rechts de app in een telefoon van 390 × 844 |
| Cursor | Een oranje rondje dat beweegt naar wat getoond wordt; bij een tik krimpt het en loopt er een ring uit |
| Geluid | Stem; tik bij elk van de vijf tikken; veeg bij het begin van de drie scrollbewegingen; signaal bij de opening en op het slotbeeld |

| Scène | Op de film | Wat er gebeurt |
|---|---|---|
| 1 Ochtendscherm | 1,2 – 19,7 s | Aanwijzen: naam, ochtendzin, tegel Nieuw. Tik op Nieuw (16,4 s): de twee nieuwe locaties |
| 2 Top 10 | 19,7 – 41,1 s | Tik op Ranglijst (20,1 s). Aanwijzen: rangnummer, de zin waarom, titel. Scrollen tot kaart 10 |
| 3 Details | 41,1 – 51,9 s | Terug naar kaart 1, tik op Details (43,6 s). Aanwijzen: score, bron, link naar de bron, link naar de kaart. Terug naar boven |
| 4 Onzeker | 51,9 – 60,9 s | Tik op de tegel Onzeker (52,2 s). Aanwijzen: rangnummer en zin van het eerste bericht |
| 5 Slot | 60,9 – 70,0 s | Tik op de naam (61,3 s): terug naar de ranglijst. Slotbeeld met beeldmerk |

Vier van de vijf tikken vallen binnen 0,1 seconde na het begin van de woorden die erbij horen
("Eén tik op Nieuw", "Terug naar de ranglijst", "Onder Onzeker", "Tilburg Signalen"). De tik op
Details valt aan het eind van "dan open je de details", ongeveer een seconde na het begin van die
woorden. Dat is berekend uit de gemeten pauzes in de stem, niet beluisterd.

### Wat voor de opname is gezet

De app wordt gebruikt zoals hij is, met echte muisbewegingen en tikken in Chromium. Twee dingen
zijn gezet:

| Wat | Waarde | Waarom |
|---|---|---|
| De klok | Dinsdag 17-11-2026, 07:28 uur | Zodat er "Goedemorgen" staat en de laatste publicatiedag "gisteren" is |
| Wat het toestel eerder zag | Alles behalve de berichten van 16-11 | Zodat de app twee nieuwe locaties en één nieuw onzeker bericht toont; daarom zegt de stem "in dit voorbeeld" |

In beeld staat "Bijgewerkt ma 16 nov, 15:37" terwijl het dinsdagochtend is: de gegevens in de repo
zijn van dat moment. In werkelijkheid ververst de run van 06:45 uur ze.

### Opnieuw maken

```bash
python3 tools/video/geluid.py timing --stem tools/video/geluid/stem.mp3 --uit tools/video/timing.json
```

```bash
node tools/video/opname.js --timing tools/video/timing.json --uit stil.mp4 --gebeurtenissen gebeurtenissen.json
```

```bash
python3 tools/video/geluid.py mix --film stil.mp4 --stem tools/video/geluid/stem.mp3 --gebeurtenissen gebeurtenissen.json --timing tools/video/timing.json --tik tools/video/geluid/tik.mp3 --signaal tools/video/geluid/signaal.mp3 --veeg tools/video/geluid/veeg.mp3 --uit tools/video/uit/tilburg-signalen_ochtendronde.mp4
```

Dat kost geen credits: de stem en de geluidjes staan in `tools/video/geluid/`. Nodig: Node,
Playwright en ffmpeg. Na een wijziging van de gesproken tekst is een nieuwe opname van de stem
nodig.

| Bestand | Wat |
|---|---|
| `tools/video/scenario.json` | De vijf scènes: wat er gezegd wordt en wat er op het scherm gebeurt |
| `tools/video/podium.html` | Het beeld van 1920 × 1080 in de huisstijl |
| `tools/video/opname.js` | Bedient de echte app (aanwijzen, tikken, scrollen) en schrijft elk beeld naar ffmpeg; `--droog` loopt het scenario door zonder te filmen |
| `tools/video/tijdlijn.js` | Wanneer elke scène begint en elke stap valt |
| `tools/video/geluid.py` | Zoekt de pauzes in de stem, bepaalt daaruit de lengte van de scènes en mengt stem en geluidjes onder de film |
| `tools/video/timing.json` | De gemeten lengte van elke scène voor deze opname van de stem |
| `tools/video/geluid/` | De stem en de drie geluidjes van ElevenLabs, ongewijzigd |

## Workflow: verslagen starten geen run (22:12 uur)

| | |
|---|---|
| Wat | In `.github/workflows/dagelijks.yml` staat onder `push` nu `paths-ignore: "docs/**"` |
| Gevolg | Een push naar `main` waarin alleen bestanden onder `docs/` veranderen, start geen run en publiceert niets. Dat is juist: verslagen veranderen de app en de gegevens niet |
| Wat gelijk blijft | Raakt een push ook iets buiten `docs/` (ook `README.md` of `tests/`), dan start de run gewoon. De zes geplande runs en de handmatige run staan hier los van |
| Test | `tests/test_workflow.py`, 5 tests: push naar `main` start een run; alleen `docs/**` is uitgezonderd; niets anders is uitgezonderd; geplande en handmatige runs ongemoeid; de run test nog steeds vóór het publiceren |
| Niet getest | Of GitHub de run werkelijk overslaat. De pull request met deze wijziging raakt ook de workflow zelf en start dus wel een run; dat laat alleen zien dat het bestand geldig is. De eerste push die alleen `docs/` raakt, is de proef |

## Browsertests op GitHub (17-11-2026)

Uitvoering van het plan hieronder. Wim koos **mogelijkheid C**: browsertests bij een push en een
handmatige run, en na elk publiceren een test van de live site.

### Wat er nu staat

| Onderdeel | Wat |
|---|---|
| `package.json`, `package-lock.json` | Playwright vast op 1.63.0. `node_modules/` staat in `.gitignore` |
| `.github/actions/browser/action.yml` | Eén plek voor wat een job met browsertests nodig heeft: Node 22, `npm ci`, de browser bewaren tussen runs (`actions/cache`, sleutel `playwright-1.63.0-chromium-Linux`), `npx playwright install --with-deps chromium` |
| Job `bouwen`, stappen "Browser klaarzetten" en "Browsertests" | Alleen bij een push en een handmatige run. Na de snelle tests en vóór het ophalen: de droogloop rekent op de gegevens zoals ze in de repo staan. De 21 tests van de pagina en de 3 van de droogloop. Faalt er een, dan wordt er niet opgehaald en niet gepubliceerd |
| Job `publiceren` | Alleen vanaf `main` |
| Job `live-controleren` (nieuw) | Na elk publiceren, ook bij geplande runs: de 21 tests van de pagina tegen `https://wim1201.github.io/tilburg-signalen`. Staat ná publiceren en houdt dat niet tegen. Faalt hij, dan staat de site al live en toont Actions een rood kruis bij de run |
| Beveiliging tegen stil overslaan | Beide teststappen controleren eerst of Playwright te vinden is. Zonder die controle slaan de tests zichzelf over en is de stap groen zonder iets te testen |
| Beveiliging tegen hangen | 10 minuten per browserstap en voor de hele job `live-controleren`. Er loopt één run tegelijk; een hangende stap zou anders de volgende verversingen ophouden |

Niet gewijzigd: `signalen/`, `config.json`, `site/data/`, `cache/`, het schema van de geplande runs
en `paths-ignore: "docs/**"`.

### Verloop

| Tijdstip | Handeling | Uitkomst |
|---|---|---|
| 08:26 uur | Stand bij Actions bekeken | Laatste run was run 10 van 16-11, 22:09 uur. Geen geplande run van 06:45 uur |
| 08:31 uur | Lokaal: alle tests, en de paginatest tegen de live site | 198 tests geslaagd, 6 overgeslagen (de film staat niet in de repo); tegen de live site 21 geslaagd |
| 08:32 uur | Handmatige run op de werkbranch proberen te starten | **Geweigerd (403):** via de koppeling mag ik geen run starten. Wim koos daarop voor een pull request |
| 08:33 uur | Pull request [Wim1201/tilburg-signalen#10](https://github.com/Wim1201/tilburg-signalen/pull/10) gemaakt en samengevoegd (gewone merge) | Merge-commit `e334b1b` |
| 08:33 – 08:34 uur | Run 11 | **Mislukt** op één browsertest. Niets opgehaald, niets gepubliceerd. Zie hieronder |
| 08:35 – 08:39 uur | Fout lokaal nagemaakt, herstel gemaakt, voor/na-beeld aan Wim voorgelegd | Wim koos: bolletje op de bovenrand |
| 08:39 uur | Pull request [Wim1201/tilburg-signalen#11](https://github.com/Wim1201/tilburg-signalen/pull/11) gemaakt en samengevoegd (gewone merge) | Merge-commit `78fe563` |
| 08:39 – 08:42 uur | Run 12 | Geslaagd: bouwen, publiceren en live-controleren |
| 08:41 uur | Live site | `bijgewerkt` 17-11-2026, 08:40:31 uur; de nieuwe opmaak van het bolletje staat in `styles.css` |

### Run 11 mislukte: het bolletje over het getal

| Vraag | Antwoord |
|---|---|
| Welke test? | `test_tiles_keep_their_label_on_one_line_and_the_same_height`, op de telefoon van 320 px breed: "het bolletje staat over het getal". De andere 23 browsertests slaagden |
| Waarom op GitHub wel en in de cloudsessie niet? | De test blokkeert de webfonts, zodat hij niet van de fontdienst afhangt. De pagina valt dan terug op het lettertype van de machine. In de cloudsessie is dat Inter, op de GitHub-runner DejaVu Sans, en dat is breder: het getal "23" is 41,8 px breed in plaats van 38,7 px |
| Hoeveel scheelde het? | Op 320 px was er met Inter 5,9 px ruimte tussen getal en bolletje; met DejaVu Sans overlapten ze 2,0 px |
| Was het ook in de echte app mis? | Met het lettertype van de app zelf (Bricolage Grotesque) was er bij "23" op 320 px 9,7 px ruimte. Bij een getal van drie cijfers overlapten ze 8,9 px. Nu staan er 23 berichten onder Onzeker; het was dus nog niet te zien, maar de opmaak had geen marge |
| Hoe nagemaakt? | Lokaal DejaVu Sans als terugvallettertype afgedwongen: dezelfde ene test faalde |
| Wat is gedaan? | `site/styles.css`: het bolletje staat op de bovenrand van de tegel (17 px hoger). Het kan dan bij geen enkel lettertype of aantal cijfers over het getal staan |
| Test erbij | De smalste telefoon wordt ook gemeten met het getal 188 en een bolletje "+12". Die meting faalt op de oude opmaak en slaagt op de nieuwe, met beide lettertypen |
| Gevolg van de mislukte run | Tussen 08:33 en 08:41 uur is er niets gepubliceerd; de live site bleef op de stand van 16-11, 22:10 uur. Run 11 blijft als mislukt in de lijst bij Actions staan |

De wijziging is samengevoegd met `main` voordat de browsertests één keer op de runner hadden
gedraaid. Mijn voorstel was eerst een handmatige run op de werkbranch; die kon ik niet zelf starten,
en bij de keuze voor de pull request had ik gemeld dat een fout dan op `main` zou staan. De schade
bleef beperkt tot één mislukte run. Het laat zien waarvoor deze tests op GitHub dienen: de runner
is een andere machine dan de cloudsessie.

### Run 12 op GitHub

| Job | Stap | Uitkomst |
|---|---|---|
| bouwen | Tests | `Ran 198 tests in 2.285s`, `OK (skipped=31)` |
| bouwen | Browsertests | `Ran 24 tests in 15.261s`, `OK` |
| bouwen | Berichten ophalen | 1.087 berichten geschreven; 31 verzoeken in 28 seconden, alles uit de cache, geen mislukte verzoeken |
| bouwen | Cache bewaren | Gewijzigd; commit `d0cc81d` op `main` |
| publiceren | | Geslaagd |
| live-controleren | Paginatest tegen de live site | `Ran 21 tests in 5.314s`, `OK` |

De snelle stap toont nog `skipped=31`, omdat Playwright op dat moment nog niet is geïnstalleerd.
Van die 31 draaien er 24 daarna in de stap Browsertests. Er blijven er 7 over die op GitHub niet
draaien: de 6 tests van de film (de film staat niet in de repo) en de ene test die ffmpeg nodig
heeft. Dat is het aantal uit het plan.

De paginatest tegen de live site begon 62 seconden nadat het publiceren klaar was. Hij bevat de
nieuwe meting met drie cijfers, die op de oude opmaak faalt. Dat hij slaagde, laat zien dat de live
site op dat moment de nieuwe versie gaf.

### Gemeten duur

| | Run 9 (16-11) | Run 10 (16-11) | Run 12 (17-11) |
|---|---|---|---|
| Job bouwen | 52 s | 41 s | 81 s |
| Job publiceren | 12 s | 9 s | 8 s |
| Job live-controleren | – | – | 71 s |
| Van start tot de site live staat | 72 s | 58 s | 95 s |
| Hele run | 72 s | 58 s | 169 s |

De stappen die erbij zijn gekomen:

| Stap | Run 11, bouwen (zonder bewaarde browser) | Run 12, bouwen (zonder bewaarde browser) | Run 12, live-controleren (met bewaarde browser) |
|---|---|---|---|
| Node klaarzetten | 0,5 s | 0,5 s | 4,4 s |
| `npm ci` | 0,8 s | 0,8 s | 1,9 s |
| Bewaarde browser zoeken of terugzetten | 0,2 s (niet gevonden) | 0,2 s (niet gevonden) | 13,5 s (271 MB teruggezet) |
| Systeempakketten (`--with-deps`) | 9,0 s | 7,9 s | 29,6 s |
| Browser downloaden | 5,3 s | 6,4 s | – (stond er al) |
| **Stap "Browser klaarzetten" samen** | **16 s** | **16 s** | **49 s** |
| De tests zelf | 17 s (24 tests, 1 mislukt) | 16 s (24 tests) | 8 s (21 tests) |
| Browser bewaren na afloop | – (run mislukt) | 3,2 s | – (stond er al) |

| Vraag | Antwoord |
|---|---|
| Hoeveel langer duurt bouwen bij een push of handmatige run? | 35 seconden (16 + 16 + 3), zonder bewaarde browser. De site staat daardoor ongeveer 35 seconden later live |
| En met bewaarde browser? | **Niet als geheel gemeten in bouwen:** daarvoor is nog een push of handmatige run nodig. Uit de gemeten stappen afgeleid: ongeveer 40 seconden, dus niet korter. Terugzetten kostte 13,5 seconden, downloaden 5,3 en 6,4 seconden |
| Hoeveel langer duurt een geplande run? | bouwen en publiceren blijven gelijk: de browserstappen worden overgeslagen en de site staat even snel live. Daarna komt de controle van de live site: 71 seconden in run 12. **Op een geplande run nog niet gemeten:** er is er nog geen gestart |
| Waar zit de tijd? | In de systeempakketten: 8 tot 30 seconden, sterk wisselend per runner (in live-controleren duurde alleen het verversen van de pakketlijst al 16 seconden). Er worden daarbij 9 pakketten geïnstalleerd, alle lettertypen; de bibliotheken die Chromium nodig heeft, staan al op de runner |

Elke meting hierboven is één run. De spreiding tussen runners is groot (Node klaarzetten 0,5 tegen
4,4 seconden); de getallen zijn een indicatie, geen gemiddelde.

### Mogelijke versnellingen (niet uitgevoerd, keuze aan Wim)

| Mogelijkheid | Wat het scheelt | Nadeel |
|---|---|---|
| De bewaarde browser weglaten | Ongeveer 7 seconden per job waarin hij wordt teruggezet, en 3 seconden bij het bewaren | De run hangt dan elke keer af van de downloadserver van Playwright |
| Alleen de browser zonder venster (`--only-shell`) | De download gaat van ruim 300 naar ruim 110 MiB (afgelezen uit het logboek van run 12; de optie zelf is niet uitgeprobeerd); ook het bewaren en terugzetten wordt kleiner | Wie op GitHub ooit een film wil opnemen, heeft de volledige browser nodig. Nu gebeurt dat daar niet |
| `--with-deps` weglaten | 8 tot 30 seconden per job | Verandert de runner, dan kan Chromium op een dag niet starten. De terugvallettertypen kunnen ook anders uitvallen |

### Tests

| Test | Wat hij vastlegt |
|---|---|
| Playwright op één versie | `package.json` noemt een exacte versie; `package-lock.json` heeft dezelfde voor `playwright` en `playwright-core` |
| Geïnstalleerde pakketten blijven buiten git | `node_modules/` in `.gitignore` en niets ervan in git |
| Volgorde | Tests, Browser klaarzetten, Browsertests, Berichten ophalen, klaarzetten voor publiceren |
| Een geplande run wacht niet op een browser | De twee browserstappen hebben de voorwaarde; de snelle tests en het verversen niet |
| Beide klassen draaien, en de stap faalt zonder Playwright | De opdracht in de stap; de klassen bestaan |
| Een hangende browser houdt de volgende runs niet op | Tijdslimiet op de stappen en op de job |
| Node en Playwright uit het lockbestand, alleen Chromium | De inhoud van `.github/actions/browser/action.yml` |
| De browser wordt bewaard onder de versie van Playwright | Map, sleutel en volgorde |
| Alleen een run vanaf `main` publiceert | Voorwaarde op de job publiceren; bouwen heeft er geen |
| De live site wordt na elk publiceren getest | `live-controleren` volgt op publiceren en heeft geen eigen voorwaarde |
| De controle houdt het publiceren niet tegen | publiceren wacht alleen op bouwen; er zijn precies drie jobs |
| De controle test het live adres en faalt zonder Playwright | `TILBURG_SITE_URL` en de opdracht |
| Dezelfde browser en dezelfde stand van de repo als bouwen | De test vergelijkt de live site met de huisstijl in de repo |
| De controle kan niet schrijven | Alleen leesrecht op de repo |
| Drie cijfers op de smalste telefoon (in de browser) | Het bolletje staat niet over het getal, de tegels zijn even hoog, niets is breder dan het scherm |

198 tests in totaal (was 184): 14 erbij voor de workflow; de meting met drie cijfers is een
uitbreiding van een bestaande test.

### Niet getest of nog open

| Punt | Toelichting |
|---|---|
| Een geplande run met de nieuwe workflow | Nog niet gezien. Dat de browserstappen in bouwen dan worden overgeslagen en `live-controleren` wel draait, is alleen door de tests op de tekst van de workflow vastgelegd |
| De geplande runs zelf | Er is er nog geen gestart (zie de correcties bovenaan). De eerstvolgende staan op 09:35 en 10:20 uur |
| bouwen met bewaarde browser | Afgeleid, niet gemeten |
| Vals alarm van `live-controleren` | De test begint zodra de job klaarstaat. Geeft GitHub Pages op dat moment nog de vorige versie en is in dezelfde push de pagina én een test gewijzigd, dan faalt de controle ten onrechte. In run 12 ging het goed (62 seconden na het publiceren) |
| Een rood kruis moet iemand zien | GitHub kan bij een mislukte run een e-mail sturen; dat hangt af van de meldingsinstellingen van Wim. Of er na run 11 een is aangekomen, weet ik niet |
| Handmatige run vanaf een andere branch | Niet uitgeprobeerd: ik mag via de koppeling geen run starten. Dat publiceren dan wordt overgeslagen, is vastgelegd door een test op de tekst |
| Verouderde versies van de actions | GitHub meldt bij elke run dat `actions/checkout@v4`, `setup-python@v5`, `setup-node@v4`, `cache@v4`, `configure-pages@v5` en `upload-artifact@v4` voor Node 20 zijn gemaakt en nu op Node 24 worden gedraaid. Het werkt; bijwerken is niet gedaan |
| De film | Toont het bolletje nog op de oude plaats. Niet opnieuw gemaakt |

## Planner op Cloudflare (voorbereid, 17-11-2026)

Wim vroeg als voorbereiding de code voor een Cloudflare Worker met een cron-trigger die de workflow
via de API van GitHub start, zonder iets live te zetten; het token maakt hij zelf aan. De
handleiding met de stappen en het token staat in `tools/planner/README.md`.

| Vraag | Antwoord |
|---|---|
| Wat staat er? | `tools/planner/` (de Worker en zijn instellingen), `tests/test_planner.py` (24 tests) en `tests/js/run_planner.mjs` (draait de Worker voor de tests) |
| Is er iets live? | Nee. Niets geplaatst bij Cloudflare, geen token, niets op `main` |
| Hoe weet hij de Nederlandse tijd? | Cloudflare kent alleen UTC. De Worker wordt elke vijf minuten aangeroepen en rekent zelf uit of het in Nederland een slot is. Voor heel 2027 doorgerekend: elk slot valt precies één keer op elk van zijn dagen, ook als de klok verspringt |
| Blijft hij gelijk aan het schema? | Een test vergelijkt de slots in de Worker met `schedule` in de workflow |
| Wat als GitHub zelf ook start? | Loopt of wacht er een run, of is er net een geslaagd, dan start de planner niets. Start GitHub later alsnog, dan komt er een extra verversing |
| Wat is in de workflow gewijzigd? | Een invoer `gepland` bij de handmatige run, en de voorwaarde op de twee browserstappen in bouwen. Zonder die invoer zou elke run van de planner eerst de browsertests draaien, en dat was bij de keuze voor B en C juist niet de bedoeling. Het schema is niet aangeraakt |
| Volgorde bij live zetten | Eerst de workflow met `gepland` op `main`, dan pas de Worker. Andersom weigert GitHub elke start (422) |

### Gevonden bij het proberen

| Nr. | Wat | Hersteld |
|---|---|---|
| 1 | **De runtime van Cloudflare weigerde de Worker te starten.** Het hoofdbestand exporteerde naast de aanroep ook het schema en een getal; Cloudflare accepteert daar alleen aanroepbare onderdelen. De droge run van wrangler (`deploy --dry-run`) merkte dat niet; het bleek pas bij lokaal draaien in de runtime | Ja: de logica staat in `src/planner.js`, het hoofdbestand exporteert alleen de aanroep. Test toegevoegd |
| 2 | **Bij het lokaal proberen zijn drie echte verzoeken naar GitHub gegaan, die ik niet had bedoeld.** Wrangler las een omgevingsvariabele `GITHUB_TOKEN` uit de cloudsessie (een plaatshouder van 14 tekens, geen echt token) en gaf die aan de Worker. GitHub weigerde alle drie (401, "Bad credentials"). Het waren verzoeken om de lijst met runs; er is geen run gestart en er is niets gewijzigd | N.v.t. Het liet wel zien dat een geweigerd token wordt gemeld zoals bedoeld |

### Getest en niet getest

| Wat | Hoe | Uitkomst |
|---|---|---|
| Schema, klok, beslissing, verzoeken, foutafhandeling | 24 tests met een nagebootst GitHub | Geslaagd. Vijf opzettelijke fouten in de Worker (verkeerde tijdzone, lopende run negeren, invoer weglaten, eindeloos herhalen, token in het logboek) lieten elk tests falen |
| Instellingen en bundel | `wrangler deploy --dry-run`, wrangler 4.163.0 | Geaccepteerd |
| In de runtime van Cloudflare, lokaal | De cron-trigger nagebootst op vijf tijdstippen | Buiten een slot geen verzoek; op een slot in winter- en zomertijd en op zondag 04:30 uur wel |
| Alle tests samen | `python -m unittest discover tests` | 223 (was 198), geslaagd, 6 overgeslagen |
| **Niet getest** | Plaatsen bij Cloudflare, een echt token, een werkelijk gestarte run, de workflow met de invoer `gepland` op GitHub, en of Cloudflare de cron-trigger stipt afvuurt | |

## Plan voor later: de browsertests ook op GitHub

**Uitgevoerd op 17-11-2026; zie "Browsertests op GitHub (17-11-2026)" hierboven.** De tekst hieronder
is het plan zoals het op 16-11 is vastgelegd.

Nu worden op GitHub 24 tests overgeslagen omdat Playwright daar ontbreekt: de 21 tests van de
pagina in een echte browser en de 3 van de droogloop. Ze draaien alleen in een cloudsessie. Dit
plan is niet uitgevoerd; Wim vroeg het voor later vast te leggen.

| Stap | Wat | Toelichting |
|---|---|---|
| 1 | Playwright vastleggen | `package.json` met `playwright` op één vaste versie (hier draait 1.63.0) en `package-lock.json`; `node_modules/` in `.gitignore`. De tests vinden Playwright dan vanzelf |
| 2 | Workflow: Node en de browser | `actions/setup-node` met een vaste Node-versie, `npm ci`, en `npx playwright install --with-deps chromium`. Alleen Chromium |
| 3 | Workflow: de browser bewaren tussen runs | `actions/cache` op de map met de browser, met de Playwright-versie als sleutel, zodat het downloaden niet elke run terugkomt |
| 4 | Waar de tests draaien | Zie de keuze hieronder |
| 5 | Controleren | Een run waarvan het logboek `OK (skipped=7)` toont in plaats van `skipped=31`: dan blijven alleen de 6 tests van de film en de ene test met ffmpeg over |

**Keuze die Wim moet maken (stap 4).** De stap Tests staat nu vóór het ophalen en publiceren: een
falende test houdt de verversing tegen. Voor de snelle tests is dat goed. Een browsertest kan ook
falen door iets buiten de app (een trage runner, een hapering). Drie mogelijkheden:

| Mogelijkheid | Voordeel | Nadeel |
|---|---|---|
| A. Browsertests in de bestaande stap Tests, bij elke run | Eenvoudig; niets komt live zonder dat de pagina is getest | Een hapering houdt de verversing van 06:45 uur tegen; elke run duurt langer |
| B. Browsertests alleen bij een push en bij een handmatige run, in een eigen stap vóór het publiceren | De pagina verandert alleen door een push; de geplande verversingen blijven zo snel en zo robuust als nu | Een geplande run test de pagina niet |
| C. Als B, en daarnaast na elk publiceren de paginatest tegen de live site (`TILBURG_SITE_URL`), in een eigen job die het publiceren niet tegenhoudt | Elke run laat zien of de live pagina met de verse gegevens werkt; een rood kruis bij Actions als dat niet zo is | Meer onderhoud; een rood kruis moet iemand ook zien |

Mijn advies is C, te beginnen met B. De test tegen de live site heeft vanavond in deze sessie al
gedraaid en onderscheidde versie 1 van versie 2.

Wat ik niet weet en bij het uitvoeren gemeten moet worden: hoeveel langer een run duurt. Nu duurt
"bouwen" 52 seconden. Mijn schatting is 30 tot 60 seconden erbij zonder bewaarde browser en 15 tot
25 seconden met; dat is een schatting, geen meting.

Niet in dit plan: ffmpeg op de runner zetten (één test), en de tests van de film (de film staat
niet in de repo).

## Samengevoegd en live (21:58 – 22:03 uur)

| Tijdstip | Handeling | Uitkomst |
|---|---|---|
| 21:58 uur | Paginatest geschikt gemaakt om tegen de live site te draaien (`TILBURG_SITE_URL`); tegen de toen nog live versie 1 gedraaid | Faalde, zoals verwacht: versie 1 heeft de tegels en het rangnummer niet. De test onderscheidt de twee versies dus |
| 21:59 uur | Pull request [Wim1201/tilburg-signalen#8](https://github.com/Wim1201/tilburg-signalen/pull/8) gemaakt en samengevoegd (gewone merge, geen wijziging van de geschiedenis) | Merge-commit `cd614ea` op `main` |
| 22:00 uur | Run 9 "Dagelijkse verversing" gestart door het samenvoegen | Geslaagd: bouwen 52 seconden, publiceren 12 seconden |
| 22:01:37 uur | Live site serveert de nieuwe kopbalkkleur | Ongeveer 80 seconden na het begin van het wachten |
| 22:02 uur | Live site gecontroleerd | Zie hieronder |

### Run 9 op GitHub

| Stap | Uitkomst |
|---|---|
| Tests | `Ran 179 tests in 2.570s`, `OK (skipped=31)` |
| Gebied bijwerken | Geslaagd, 17 gemeenten |
| Berichten ophalen | 1.116 berichten: 81 ontwikkellocaties, 23 onzeker, 1.012 weggefilterd. 31 verzoeken in 33 seconden, alles uit de cache, geen mislukte verzoeken |
| Cache bewaren | Cache ongewijzigd, geen commit |
| Publiceren op GitHub Pages | Geslaagd |

De 31 overgeslagen tests op GitHub: de 21 tests van de pagina in een echte browser en de 3 van de
droogloop (Playwright staat niet op de runner), de 6 tests van de film zelf (de film staat niet in
de repo) en 1 test die ffmpeg nodig heeft. Daarmee is ook bekend wat in dit verslag nog open stond:
**ffmpeg staat niet op de GitHub-runner.** De 148 andere tests draaiden en slaagden, waaronder de 8
tests van de pagina die geen browser nodig hebben (verwijzingen, elementen, service worker, de
regelteksten) en alle tests van de logica onder Node.

### De live site (22:02 uur)

| Controle | Hoe | Uitkomst |
|---|---|---|
| Nachtblauwe huisstijl | `theme-color` in de pagina en de berekende achtergrondkleur van de kopbalk in Chromium | `#0c1049`, gelijk aan de huisstijl in `main` |
| Bestanden | `styles.css`, `logic.js`, `app.js`, `sw.js` en `icons/icon.svg` van de live site byte voor byte vergeleken met `main` | Alle vijf gelijk |
| Paginatest in een echte browser tegen de live site | `TILBURG_SITE_URL=https://wim1201.github.io/tilburg-signalen python -m unittest tests.test_site.InDeBrowser`, vanuit deze sessie | 21 tests, alle geslaagd |
| Gegevens | `bijgewerkt` in het live gegevensbestand | 16-11-2026, 22:00:28 uur: het moment van run 9 |

Niet gecontroleerd: een echte telefoon, en een toestel waarop versie 1 al als app was geïnstalleerd.

## Controle van het geluidsspoor (21:25 – 21:34 uur)

Gemeten op de film zoals hij om 20:51 uur is geleverd (5.167.073 bytes):

| Meting | Uitkomst |
|---|---|
| Geluidsspoor aanwezig | Ja, één spoor, als standaardspoor gemarkeerd |
| Codec | AAC-LC, 48 kHz, stereo, 149 kbit/s |
| Duur | 70,02 seconden (beeld: 70,03) |
| Gemiddeld / maximaal volume | −22,7 dB / −2,8 dB |
| Luidheid | −18,2 LUFS |
| Per kanaal | Links −22,7 / −2,8 dB, rechts −22,7 / −3,7 dB; opgeteld tot mono −22,7 / −3,5 dB (de kanalen heffen elkaar niet op) |
| Stiltes langer dan 2 seconden | Alleen het slotbeeld na de laatste woorden, van 65,4 tot 70,0 seconden |

Het spoor was er dus en was niet stil. De voorwaarde voor herstel ("geen of een stil audiospoor")
gold niet. Wat ik bij deze controle wel vond:

| Bevinding | Toelichting | Gedaan |
|---|---|---|
| Beeld op H.264 High Profile **niveau 5.0** | De instelling "slow" van de encoder gebruikt vijf referentiebeelden en komt daardoor bij 1920 × 1080 op niveau 5.0 uit. Apple geeft voor de iPhone niveau 4.2 als bovengrens op. Veel toestellen spelen 5.0 toch af; dat is een vermoeden, niet getest | Opnamescript aangepast: niveau 4.0, hoogstens vier referentiebeelden. Film opnieuw opgenomen en gemengd (geen credits). Tests toegevoegd |

De nieuwe film: H.264 High Profile niveau 4.0, 1920 × 1080, 30 beelden per seconde, yuv420p; AAC-LC,
48 kHz, stereo; 70,03 seconden; 5.239.918 bytes. Het geluid is hetzelfde spoor uit dezelfde bron
(−22,7 / −2,8 dB). De opname verliep gelijk: dezelfde 34 gebeurtenissen op dezelfde momenten, geen
fouten in de console.

**Of de eerste film op de iPhone van Wim zonder geluid speelde, en zo ja waardoor, weet ik niet.**
Ik kan niets afspelen. Een te hoog videoniveau geeft doorgaans geen beeld, niet alleen geen geluid.
Andere mogelijke oorzaken liggen buiten het bestand: de stilteschakelaar van de iPhone, of een
voorvertoning in de app die gedempt begint.

## Film uit de repository (21:00 uur)

| Vraag | Antwoord |
|---|---|
| Hoe groot is de film? | 5.167.073 bytes (5,2 MB) |
| Stond hij in git? | Ja: sinds commit `4626889` (20:51 uur) op de branch `claude/awesome-brown-i18j4o`, gepusht naar GitHub. Niet in `main`. Het stilstaande beeld (110.830 bytes) ook |
| Wat is gedaan? | De commit is herschreven zonder beide bestanden en de branch op GitHub is daardoor vervangen (`7523af7`). Een gewone verwijdering in een nieuwe commit had de film in de geschiedenis gelaten |
| Staat hij nu nog ergens in de branch? | Nee: geen enkel bestand in de geschiedenis van de branch heet nog zo (gecontroleerd op de stand van GitHub na het pushen) |

| Meting | Vóór de film (`54d570b`) | Met de film (`4626889`) | Na het verwijderen (`7523af7`) |
|---|---|---|---|
| Bestanden | 54 | 61 | 59 |
| Werkmap (alle bestanden samen) | 1,84 MB | 8,27 MB | 3,00 MB |
| Geschiedenis van de branch (gecomprimeerd, wat een kloon ophaalt) | 0,59 MB | 6,73 MB | 1,71 MB |
| Ter vergelijking: `main` | 37 bestanden, 1,57 MB, 0,33 MB | | |

De 1,1 MB die er ten opzichte van vóór de film bij blijft, zijn de bron van de film: de stem
(1.048.692 bytes) en de drie geluidjes (86.197 bytes) van ElevenLabs, plus het gereedschap. Die
geluidsbestanden zijn bewust gehouden: zonder ze kost opnieuw maken ongeveer 900 credits. Ze
blijven net als de film voorgoed in de geschiedenis zodra de branch wordt samengevoegd; wil Wim dat
niet, dan moeten ze er vóór het samenvoegen uit.

**Wat ik niet kan afdwingen:** GitHub bewaart een vervangen commit nog enige tijd. Wie de oude hash
`4626889` kent, kan de film daar mogelijk nog opvragen tot GitHub opruimt. De film bevat niets
vertrouwelijks: de app met openbare gegevens.

Om herhaling te voorkomen: `.gitignore` slaat `tools/video/uit/` en filmbestanden over, en een test
faalt als er een film, een bestand uit die map of een bestand groter dan 1,5 MB in git staat.

## Wat Bijgewerkt betekent (21:00 uur)

| Vraag | Antwoord |
|---|---|
| Wat toont "Bijgewerkt" bovenaan de app? | Het tijdstip waarop de laatste **geslaagde verversing** begon. Niet het tijdstip waarop de berichten voor het laatst veranderden |
| Waar komt het vandaan? | `signalen/update.py` schrijft bij elke run het moment van die run in het veld `bijgewerkt`, ook als er niets nieuws is gevonden |
| Wat als een run mislukt of wordt overgeslagen? | Dan wordt het bestand niet geschreven en blijft het oude tijdstip staan. Na 26 uur toont de app bovendien de melding "De gegevens zijn sinds … niet ververst" |
| Waarom stond er in de film 15:37 uur terwijl de laatste run van 17:38 uur was? | De film gebruikte `site/data/berichten.json` uit de repo. Dat bestand is een momentopname: de runs op GitHub maken het opnieuw en zetten het op de live app, maar schrijven het niet terug in de repo. De live app toonde 17:38 uur |

Er hoefde dus niets aan het gedrag te veranderen; het was al het tijdstip van de laatste
verversing. Code van de app en van het ophalen is niet gewijzigd. Wel toegevoegd: tests die dit
vastleggen, zodat het niet ongemerkt kan verschuiven.

| Test | Wat hij vastlegt |
|---|---|
| Tijdstip is het moment van de run | Een run om 06:45:12 uur geeft `2026-11-17T06:45:12+01:00` |
| Niets nieuws verzet het tijdstip toch | Twee runs met dezelfde berichten, maandag 17:38 uur en dinsdag 06:45 uur: gelijke berichten, verschillend tijdstip |
| Volgt niet de datum van het nieuwste bericht | Nieuwste bericht van 1 oktober, run op 17 november: het tijdstip is 17 november |
| Geslaagde run schrijft zijn eigen moment, in Nederlandse tijd | Het geschreven bestand, met nagebootste bronnen |
| Mislukte run laat het oude tijdstip staan | Hoofdbron onbereikbaar: het bestand blijft onaangeroerd |
| De app toont dat tijdstip | In de browser: "Bijgewerkt" met dag en tijd uit het bestand |
| Overgeslagen verversing is zichtbaar | Bestand van 30 uur oud: oud tijdstip bovenaan én de melding "niet ververst" |

Wat een test niet kan vastleggen: of GitHub de geplande run van 06:45 uur werkelijk start. Dat is
te zien bij Actions, en aan het tijdstip bovenaan de live app.

## Gevonden tijdens het opnemen

### Proefopname zonder geluid (20:03 – 20:11 uur)

De stille proefopname van 66 seconden is beeld voor beeld (één per seconde) nagekeken.

| Nr. | Waar | Wat | Hersteld |
|---|---|---|---|
| 1 | App | De tekst op de tegel Onzeker ("Onzeker · 1 nieuw") brak af over twee regels | Ja: een bolletje "+1" rechtsboven; schermlezers krijgen "+1 nieuw". Tests op 320 en 390 px: label op één regel, drie tegels even hoog, bolletje niet over het getal |
| 2 | App | De telregel "Top 10 van 23 onzekere berichten, hoogste rang eerst" liet één woord alleen op de tweede regel | Ja: de regel verdeelt zich gelijk. Test toegevoegd |
| 3 | Opname | Na terugscrollen stond de bovenrand van kaart 1 onder de kopbalk | Ja: meer ruimte onder de kopbalk |
| 4 | Opname | De tik op de naam in de kopbalk viel vlak voor het slotbeeld en was niet te zien | Ja: de tik komt aan het begin van de slotscène |

### Definitieve opname met geluid (20:40 – 20:51 uur)

| Nr. | Waar | Wat | Hersteld |
|---|---|---|---|
| 5 | Geluid | **De scènegrenzen werden niet gevonden.** Het script zocht de vier langste stiltes en eiste dat die duidelijk langer waren dan alle andere. Deze stem pauzeert tussen zinnen bijna even lang (tot 1,27 s) als tussen scènes (vanaf 1,43 s); het script weigerde de opname | Ja: per scène wordt nu de langste stilte gezocht rond de plek waar de grens op grond van de tekstlengte hoort. Test met de gemeten stiltes van deze opname |
| 6 | Geluid | **De geluidjes verschilden sterk in volume**: de tik piekte op −28 dB (nauwelijks hoorbaar), de veeg op −2,8 dB (harder dan de stem) | Ja: elk geluidje wordt naar een vast zacht niveau gebracht (tik en signaal −15 dB, veeg −24 dB). Test toegevoegd |
| 7 | Opname | **Het opnamescript liep vast met een onbegrijpelijke fout** toen de lokale server niet draaide | Ja: het script serveert de app nu zelf en meldt een onbereikbare app in gewone taal. Test toegevoegd |
| 8 | Geluid | **De film werd afgekapt waar de stem ophield** (65,7 in plaats van 70 seconden): het slotbeeld bleef geen 4 seconden staan | Ja: het geluid loopt stil door tot het eind van het beeld. Twee tests: de mengopdracht, en de lengte van de film tegen de timing |

Niet gevonden: fouten in de console (0), stappen die hun doel niet vonden (0), functionele fouten
in de app. De twee punten in de app (1 en 2) zijn opmaak.

## Referentiewaarden (16-11-2026, 20:51 uur)

| Meting | Waarde |
|---|---|
| Lengte film / stem | 70,03 s / 64,44 s |
| Lengte per scène | 18,51 / 21,38 / 10,75 / 9,07 / 6,53 s, plus 1,2 s aanloop en 2,6 s uitloop |
| Scènegrenzen in de stem | 18,51 / 39,89 / 50,64 / 59,71 s |
| Grootte | Film 5,2 MB; stem 1,0 MB; geluidjes samen 86 kB |
| Tikken / scrollbewegingen | 5 / 3 |
| Opnemen | 2.101 beelden, enkele minuten rekentijd (niet precies gemeten) |
| Unittests | 198 op 17-11-2026 (zie "Browsertests op GitHub"); op 16-11: 184, alle geslaagd (was 139; 167 om 20:51 uur, 175 om 21:00 uur, 178 om 21:34 uur, 179 om 21:58 uur, daarna 5 erbij voor de workflow) |

## Getest

| Wat | Hoe | Uitkomst |
|---|---|---|
| Scenario | 4 tests: de vijf scènes in de gevraagde volgorde; elk doel bestaat in de app; de spreektekst is de scènes met een pauze ertussen en bevat geen cijfers; wat over nummer één gezegd wordt (Bellinistraat, 141 woningen) staat in de gegevens | Geslaagd |
| Tijdlijn | 5 tests: scènes sluiten op elkaar aan en stappen vallen binnen hun scène; een scène zonder lengte wordt geweigerd; fouten in een scenario worden benoemd; het scenario in de repo is in orde; de cursor versnelt en remt | Geslaagd |
| Geluid | 9 tests: stiltes lezen; scènegrens vlak voor de stem verdergaat; verwachte plek uit de tekstlengte; de gemeten stiltes van deze opname; ontbrekende, dubbelzinnige en verkeerd geordende pauzes worden geweigerd; lengtes tellen op; geluidjes volgen wat er op het scherm gebeurt; de mengopdracht; het zachte niveau; pauzes vinden in een echt geluidsbestand | Geslaagd |
| Droogloop | 3 tests in Chromium: elke stap wordt uitgevoerd zonder fouten, vijf tikken in de juiste volgorde; het is ochtend met iets nieuws en eindigt op de ranglijst; een onbereikbare app wordt duidelijk gemeld | Geslaagd |
| De film zelf | 4 tests: tussen 60 en 90 seconden; loopt tot het eind van het slotbeeld; H.264 van 1920 × 1080 met AAC-geluid; kleiner dan 15 MB | Geslaagd |
| Tegels en telregel | 3 nieuwe tests in de browser (zie punten 1 en 2) | Geslaagd |
| Beeld | 70 beelden (één per seconde) van de definitieve film bekeken, plus drie op volle resolutie | Scènes, cursor, tikken en slotbeeld kloppen met het scenario |
| Geluid | Gemeten: lengte, pauzes, luidheid van de film, piek van elk geluidje op zijn moment in de mix | Zie referentiewaarden. Niet beluisterd |

Op GitHub draaien de tests voor scenario, tijdlijn en de rekenkant van het geluid mee. De droogloop
heeft Playwright nodig en wordt daar overgeslagen. Of ffmpeg op de GitHub-runner staat weet ik niet;
zonder ffmpeg worden de vijf tests die het nodig hebben overgeslagen. Dat is niet uitgeprobeerd.

## Niet getest of nog open

| Punt | Toelichting |
|---|---|
| Hoe het klinkt | Uitspraak ("Bellinistraat", "honderdeenenveertig", "Onzeker"), klank van de stem en van de drie geluidjes, en of het volume van de geluidjes prettig is. Ik kan geen geluid beluisteren. |
| Of alle woorden gezegd zijn | Niet gecontroleerd met spraakherkenning; dat had extra credits gekost. De lengte van elk stuk past bij de tekst. |
| Het tempo | De stem laat veel pauzes van ongeveer een seconde vallen. Als dat te traag is, kan de tweede en laatste generatie met dezelfde stem daarvoor gebruikt worden (ongeveer 897 credits), of kan de stem sneller worden gezet. Niet gedaan. |
| Afspelen | De film is niet in een speler afgespeeld; de opbouw is gecontroleerd met ffprobe. |
| De workflow op GitHub | Niet uitgevoerd met deze wijziging. De geluidsbestanden staan in `tools/`, niet in `site/`, en gaan dus niet mee naar de live app. |

## Buiten dit verslag

- **Afspraak van Wim (16-11-2026, na het herschrijven van de branch): geen force push of andere wijziging van de geschiedenis zonder dat eerst voor te leggen.** Het herschrijven van commit `4626889` heb ik gedaan zonder het te vragen; dat had ik moeten voorleggen. Dit geldt voor elke volgende sessie.
- **De film gaat via de sessie naar Wim, niet via de repository.**

- **Pushnotificatie.** Verstuurd toen de video klaar was en gepusht.
- **Samengevoegd met `main` om 21:59 uur** (zie "Samengevoegd en live"). Dit stuk van het verslag is daarna op de werkbranch bijgeschreven en staat nog niet in `main`; een push naar `main` start een nieuwe run.
- **Morgen te zien, niet door mij te controleren:** of GitHub de geplande run van 06:45 uur start. Het tijdstip bovenaan de live app moet dan dinsdag 06:45 uur of later zijn. *Uitkomst 17-11-2026: niet gestart; zie de correcties bovenaan.*
- **ElevenLabs opruimen** kan alleen Wim zelf, in de app (zie "Opruimen").
- **Stem uit de bibliotheek.** "Daan" is een stem uit de openbare bibliotheek van ElevenLabs. De teller van stemplekken staat na afloop nog op 0 van 30. Onder welke voorwaarden zo'n stem in eigen materiaal gebruikt mag worden heb ik niet uitgezocht.
- **Geen subsessie** deze ronde: het werk hing aan één stem en één opname en liet zich niet verdelen.
- **Bewust niet gedaan:** een tweede opname van de stem; muziek; ondertiteling als apart bestand (de gesproken tekst staat wel per scène in beeld); een staande versie voor de telefoon; de video in de app of op de live site zetten.
