# Tilburg Signalen: uitleg en voorstel voor de ranglijst bij een gekozen regio

| | |
|---|---|
| Datum | 18-11-2026, 13:08 – 13:13 uur |
| Versie | versie 2 van de app met de regio's, `main` op commit `37f8183` (na PR 21) |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | De gegevens van de live site, bijgewerkt 18-11-2026, 13:07 uur, opgehaald om 13:08 uur: de kern (1.140 berichten, 83 ontwikkellocaties) en de drie regiobestanden. Geen opvraging bij de bronnen |
| Van / aan | Claude Code aan Wim |
| Status | **Voorstel. Niets hiervan is gebouwd.** |

## De vraag

Waarom staat in de ranglijst met Zeeland erbij het voornemen in Tholen (100 woningen, geen locatie)
boven het vastgestelde plan Bellinistraat (141 woningen)? En wat doen we met de ranglijst bij een
gekozen regio: gemengd zoals nu, of een keuze "alleen deze regio"?

## Waarom Tholen boven de Bellinistraat staat

De twee berichten zoals de app ze nu heeft:

| | Tholen, Scherpenisse Oost | Tilburg, Bellinistraat |
|---|---|---|
| Bericht | `gmb-2026-502250`, kennisgeving voornemen wijziging omgevingsplan | `gmb-2026-465755`, wijzigingsbesluit TAM-omgevingsplan Hoofdstuk 22s |
| Fase | Voornemen | Vastgesteld |
| Woningen | 100 | 141 |
| Locatie | Alleen de gemeente (59,3 km) | Benaderd: omgeving Bellinistraat (3,3 km) |
| Datum | 27-10-2026 | 06-10-2026 |
| **Score** | **108** | **108** |
| Plaats in de lijst, kern met Zeeland | 1 | 2 |

Ze hebben dezelfde score, en bij een gelijke score gaat het nieuwste bericht voor. Dat de scores gelijk
zijn, komt door vier dingen in de regels (`signalen/relevantie.py` en `site/logic.js`); het zijn feiten
uit de code:

| Regel | Wat hij doet | Gevolg hier |
|---|---|---|
| Een plan dat wonen mogelijk maakt, begint op 100 | Er komt 1 punt bij per 10 woningen, **tot hoogstens 8** | Vanaf 80 woningen krijgt elk plan 108. Honderd en 141 woningen tellen dus even zwaar |
| De fase telt bij een plan niet mee | Er gaat alleen iets af bij ingetrokken, geweigerd, vernietigd of een verlengde termijn | Een voornemen scoort gelijk aan een vastgesteld plan |
| De locatie telt bij een plan niet mee | Of de plek exact, benaderd of alleen als gemeente bekend is, verandert de score niet | "Geen locatie" kost Tholen niets |
| De afstand telt niet mee | De score kent geen kilometers | 59 km scoort gelijk aan 3 km |
| Gelijke score | Eerst het nieuwste bericht, dan het dichtstbijzijnde | 27 oktober gaat voor 6 oktober |

**Dit ligt niet aan de regio's.** Dezelfde regels gelden in de kern; daar viel het niet op, omdat de
Bellinistraat er het enige plan met 108 punten is. Zodra een regio een tweede plan met 80 of meer
woningen meebrengt, beslist de datum.

## Wat een regio met de ranglijst doet (gemeten, 18-11-2026, 13:07 uur)

| Regio erbij | Locaties in de regio | Samen met de kern (83) | Uit de regio in de top 10 | Uit de regio in de top 25 | Waar de top 10 van de kern dan staat |
|---|---:|---:|---:|---:|---|
| Midden-Brabant | 21 | 104 | 1 | 3 | 1, 2, 3, 4, 6, 7, 8, 9, 10, 11 |
| Zeeland | 121 | 204 | 5 | 14 | 2, 3, 4, 5, 10, 16, 17, 18, 19, 20 |
| West-Brabant | 149 | 232 | 6 | 18 | 2, 6, 7, 8, 13, 19, 25, 28, 32, 34 |

Met Zeeland of West-Brabant erbij is de helft of meer van de top 10 van buiten de kern. Dat komt
doordat veel berichten dezelfde score delen: van de 204 locaties in de kern met Zeeland delen er 189
hun score met een ander. Een plan dat wonen noemt zonder aantal woningen krijgt precies 100: dat zijn
er 13 in de kern en 18 in Zeeland. Binnen zo'n groep beslist alleen de datum.

## Voorstel

Twee losse onderdelen. Het eerste gaat over de vraag "gemengd of alleen deze regio"; het tweede over
de volgorde die de aanleiding was. **Het eerste lost het tweede niet op:** ook in een lijst met alleen
Zeeland staat het voornemen in Tholen bovenaan, en in de gemengde lijst blijft het boven de
Bellinistraat staan.

### Onderdeel 1: een keuze boven de lijst

| | Wat | Voor | Tegen |
|---|---|---|---|
| A | **Gemengd, zoals nu** | Eén lijst, niets te kiezen | De kern raakt uit beeld: met West-Brabant erbij staat de nummer 10 van de kern op plaats 34 |
| **B** | **Een keuze in de regel "Met Zeeland erbij" op het tabblad Berichten: "Samen", "Alleen Zeeland", "Alleen de kern"** | Je kijkt per gebied of gemengd, zonder terug te gaan naar het tabblad Gebied. De rangnummers tellen dan binnen wat je ziet | Eén regel met drie knoppen erbij op het tabblad Berichten; met drie regio's gekozen wordt het "Samen", "Alleen de regio's", "Alleen de kern" |
| C | Twee lijsten onder elkaar: eerst de kern, dan de regio | De kern blijft altijd bovenaan | Lange pagina; "Top 10" betekent dan twee keer iets anders |

**Advies: B.** De standaard blijft "Samen", zodat er niets verandert voor wie niets kiest. De
ochtendregel, de tegel Nieuw en het kaartje blijven van de kern, zoals nu. Bij een volgend bezoek
staat de app weer op de kern.

### Onderdeel 2: de volgorde bij gelijke score

Dit raakt ook de kern en is daarom een eigen besluit.

| | Wat | Wat het doet (gemeten op de gegevens van 13:07 uur) |
|---|---|---|
| **D** | **Bij gelijke score: eerst het plan dat het verst is (vastgesteld vóór ontwerp vóór voornemen), dan het grootste aantal woningen, dan het nieuwste bericht** | De Bellinistraat komt op 1 en Tholen op 2. De scores zelf blijven gelijk. In de kern krijgen 40 van de 83 locaties een andere plaats, alle binnen een groep met dezelfde score; de eerste vier blijven staan, vanaf plaats 5 schuift het. Met Zeeland erbij verschuiven 148 van de 204 |
| E | De score zelf aanpassen: de fase, de locatie en het aantal woningen boven de 80 laten meetellen | Grotere ingreep: elke score van een plan verandert, ook in de kern, en de drempels in de app (bijvoorbeeld wat "Onzeker" is) moeten opnieuw bekeken worden. Niet doorgerekend |
| F | Niets doen | De datum blijft beslissen bij gelijke score |

**Advies: D**, na jouw akkoord op de volgorde van de fasen. Het is de kleinste ingreep die de volgorde
uit je vraag omdraait, en ze laat elke score staan. E is alleen de moeite waard als je vindt dat een
voornemen zonder locatie structureel lager hoort dan een vastgesteld plan, ook als er geen gelijke
stand is.

Wat ik bij D van je moet weten:

| Vraag | Waarom |
|---|---|
| De volgorde van de fasen | In de kern komen nu voor: Aanvraag (21), Besluit (16), Vastgesteld (14), Verleend (8), Herstelbesluit (5), Beslistermijn verlengd (4), Voornemen (3), Bekendmaking (3), Voornemen tot verkoop (3), Ontwerp (3) en drie losse. Voor de meting hierboven heb ik gerekend met drie treden: vastgesteld, verleend en herstelbesluit eerst; ontwerp, bekendmaking en besluit daarna; voornemen en aanvraag als laatste. Dat is mijn indeling, niet een regel uit de bron |
| Geldt "het verst" ook tussen een plan en een vergunning | Bij gelijke score kunnen die naast elkaar staan |
| Moet de locatie meetellen | Dan komt er een trede bij: exact vóór benaderd vóór alleen de gemeente |

## Niet onderzocht of nog open

| Punt | Toelichting |
|---|---|
| Eén dag gemeten | De cijfers zijn van 18-11-2026, 13:07 uur. Op een andere dag liggen de aantallen anders; de regels niet |
| Waarom Tholen geen locatie heeft | De bron geeft bij dit bericht alleen de gemeente. Niet nagegaan of de tekst een plek noemt die de app zou kunnen vinden |
| Onderdeel B op 320 pixels | Niet getekend of geprobeerd; drie knoppen in één regel is krap |
| Het effect van D en E op de video | De tests van de video rekenen op de momentopname van 16-11-2026 en op de volgorde daarin; bij D moet dat mee worden bekeken |
| Rangnummers bij "Alleen Zeeland" | Voorgesteld: tellen binnen wat je ziet. Het alternatief is het nummer uit de gemengde lijst houden |

## Buiten dit voorstel

- **Niets is gebouwd.** De regels in `signalen/relevantie.py` en `site/logic.js` zijn niet aangeraakt.
- De live site is één keer gelezen (vier bestanden); de bronnen zijn niet belast.
