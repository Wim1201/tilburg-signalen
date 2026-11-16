# Tilburg Signalen: verslag video van de ochtendronde

| | |
|---|---|
| Datum | 16-11-2026, 20:00 – 21:35 uur |
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

## Correcties en aanvullingen

| Tijdstip | Wat |
|---|---|
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
| Unittests | 178, alle geslaagd (was 139; 167 om 20:51 uur, 175 om 21:00 uur, daarna 3 erbij voor het formaat en het geluid van de film) |

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
- **Samenvoegen met `main` is niet gedaan en er is geen pull request.** Wim beoordeelt eerst de film.
- **ElevenLabs opruimen** kan alleen Wim zelf, in de app (zie "Opruimen").
- **Stem uit de bibliotheek.** "Daan" is een stem uit de openbare bibliotheek van ElevenLabs. De teller van stemplekken staat na afloop nog op 0 van 30. Onder welke voorwaarden zo'n stem in eigen materiaal gebruikt mag worden heb ik niet uitgezocht.
- **Geen subsessie** deze ronde: het werk hing aan één stem en één opname en liet zich niet verdelen.
- **Bewust niet gedaan:** een tweede opname van de stem; muziek; ondertiteling als apart bestand (de gesproken tekst staat wel per scène in beeld); een staande versie voor de telefoon; de video in de app of op de live site zetten.
