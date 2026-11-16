# Tilburg Signalen: verslag video van de ochtendronde

| | |
|---|---|
| Datum | 16-11-2026, vanaf 20:00 uur |
| Versie | versie 2 van de app, branch `claude/awesome-brown-i18j4o` |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | `site/data/berichten.json` zoals het in de repo staat (bijgewerkt 16-11-2026, 15:37 uur) |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_versie-2-huisstijl_16-11-2026.md` |

## Stand

**Tussenstand van 20:12 uur: de video is nog niet gemaakt.** De opname-opzet is gebouwd en stil
proefgedraaid. Stem en geluidjes wachten op het akkoord van Wim op model, stem, raming en tekst.
Er is bij ElevenLabs niets gegenereerd; het verbruik staat op 17.958 credits, gelijk aan het eind
van de vorige ronde.

## Correcties en aanvullingen op het vorige verslag

| Tijdstip | Wat |
|---|---|
| 16-11-2026, 20:11 uur | **De tegel Onzeker toont nieuwe berichten niet meer als "Onzeker · 1 nieuw" maar als een bolletje "+1".** De tekst brak af over twee regels, waardoor die tegel er anders uitzag dan de andere twee. Gevonden in de proefopname. |
| 16-11-2026, 20:11 uur | **De lege proefwerkstroom in het ElevenLabs-account is niet meer leeg.** Verwijderen kan niet via de koppeling. Het oude knooppunt is eruit gehaald en de werkstroom wordt hergebruikt voor de stem en de geluidjes van de video. Zie "ElevenLabs". |

## ElevenLabs

### Opruimen

| Gevraagd | Uitkomst |
|---|---|
| Vier ongebruikte afbeeldingsvarianten verwijderen | **Kan niet via de koppeling.** Er is geen functie om een gegenereerde afbeelding uit de geschiedenis te verwijderen; bij het verwijderen van een knooppunt blijven de afbeeldingen in de geschiedenis staan. Wim kan ze zelf verwijderen in ElevenLabs onder Image & Video → History. |
| Lege proefwerkstroom verwijderen | **Kan niet via de koppeling**: er is geen functie om een werkstroom te verwijderen. Wel gedaan: het ongebruikte afbeeldingsknooppunt eruit verwijderd (20:08 uur) en de werkstroom hergebruikt voor de video, zodat er geen vierde bijkomt. |

### Voorstel dat op akkoord wacht (20:10 uur)

| Onderdeel | Model | Instelling | Raming |
|---|---|---|---|
| Stem | `eleven_multilingual_v2` | Stem "Daan - Calm, Professional Narrator", Nederlands, één opname van de hele tekst (933 tekens met de vier pauzes) | 889 credits |
| Tik | `eleven_text_to_sound_v2` | 0,5 seconde, één variant | 5,5 credits |
| Signaal | `eleven_text_to_sound_v2` | 1,5 seconde, één variant | 16,5 credits |
| Veeg | `eleven_text_to_sound_v2` | 0,8 seconde, één variant | 8,8 credits |
| Samen | | | 920 credits |

De raming is opgevraagd bij ElevenLabs voor precies de vier knooppunten die na akkoord worden
uitgevoerd (stem 888,9 credits; de drie geluidjes samen 30,8). De verdeling over de drie geluidjes
is door mij berekend uit de lengte (11 credits per seconde) en niet apart opgevraagd.

Wat er vóór het akkoord bij ElevenLabs is gedaan, zonder iets te genereren: de lijst met
Nederlandse stemmen gelezen, de beschikbare modellen en hun instellingen gelezen, het verbruik
gelezen, het oude knooppunt verwijderd, vier knooppunten klaargezet en de raming opgevraagd.

## Opname-opzet

| Bestand | Wat |
|---|---|
| `tools/video/scenario.json` | De vijf scènes: wat er gezegd wordt en wat er op het scherm gebeurt |
| `tools/video/podium.html` | Het beeld van 1920 × 1080 in de huisstijl: links de scène en de tekst, rechts de app in een telefoon |
| `tools/video/opname.js` | Bedient de echte app in Chromium (aanwijzen, tikken, scrollen) en schrijft elk beeld naar ffmpeg |
| `tools/video/tijdlijn.js` | Wanneer elke scène begint en elke stap valt |
| `tools/video/geluid.py` | Zoekt de pauzes in de stem, bepaalt daaruit de lengte van de scènes en mengt stem en geluidjes onder de film |

De app wordt gebruikt zoals hij is. Twee dingen zijn voor de opname gezet: de klok (dinsdag
17-11-2026, 07:28 uur) en wat het toestel eerder heeft gezien (alles behalve de berichten van de
laatste publicatiedag). De gegevens zelf zijn niet aangeraakt.

## Gevonden tijdens de proefopname (20:03 – 20:11 uur)

De stille proefopname van 66 seconden is beeld voor beeld (één per seconde) nagekeken.

| Nr. | Waar | Wat | Hersteld |
|---|---|---|---|
| 1 | App | De tekst op de tegel Onzeker ("Onzeker · 1 nieuw") brak af over twee regels | Ja: een bolletje "+1" rechtsboven; schermlezers krijgen "+1 nieuw". Tests toegevoegd op 320 en 390 px |
| 2 | App | De telregel "Top 10 van 23 onzekere berichten, hoogste rang eerst" liet één woord alleen op de tweede regel | Ja: de regel verdeelt zich nu gelijk. Test toegevoegd |
| 3 | Opname | Na terugscrollen stond de bovenrand van kaart 1 onder de kopbalk | Ja: meer ruimte onder de kopbalk |
| 4 | Opname | De tik op de naam in de kopbalk viel vlak voor het slotbeeld en was niet te zien | Ja: de tik komt eerder in de slotscène |

Niet gevonden: fouten in de console (0), stappen die hun doel niet vonden (0).

## Getest

Stand 20:12 uur: 162 tests, 159 geslaagd, 3 overgeslagen (die drie controleren de film zelf en
draaien zodra hij in `docs/video/` staat).

## Buiten dit verslag

- **Wacht op Wim:** akkoord op model, stem, raming en tekst.
- **Ik kan geluid niet beluisteren.** Na het genereren controleer ik lengte, pauzes en volume, niet
  de uitspraak of de klank. Wim moet de video zelf beluisteren.
