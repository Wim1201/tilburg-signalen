# Tilburg Signalen: voorstel vergunningen onder een andere rubriek

| | |
|---|---|
| Datum | 17-11-2026, 21:18 – 21:21 uur |
| Versie | werkbranch `claude/optimistic-gauss-sb0xpy` (commit `d5ab774`), nog niet samengevoegd |
| Omgeving | Claude Code in de cloud (tijdelijke container), repo `Wim1201/tilburg-signalen` |
| Brondata | officielebekendmakingen.nl, opgevraagd 17-11-2026 om 21:24 uur; venster 06-10-2026 tot en met 17-11-2026 (42 dagen) |
| Van / aan | Claude Code aan Wim |
| Vervolg op | `tilburg-signalen_verslag_dekking-en-regios_17-11-2026.md`, open punt "Roosendaal: aanvragen ontbreken" |

**Dit is een voorstel. Er is niets gebouwd.** De cijfers komen uit een proef: de berichten zijn
opgehaald en door de bestaande regels van de app gehaald, zonder iets weg te schrijven.

## Correctie op het vorige verslag

| Tijdstip | Wat |
|---|---|
| 17-11-2026, 21:21 uur | **Vught is in de kern één bericht, geen vijf.** In het dekkingsverslag staat "Dongen, Etten-Leur, Vught, Noord-Beveland: 10, 8, 5 en 4 berichten". Dat zijn de aantallen per gemeente als geheel. Van de vijf van Vught liggen er vier buiten de 15 km; die tonen we nu ook niet en dat blijft zo. |
| 17-11-2026, 21:21 uur | **Bij Dongen is het geen fout in de rubriek, maar in de titel.** Dongen zet "aanvraag omgevingsvergunning" ook boven berichten die geen omgevingsvergunning zijn (speelautomaten, een container, een ontheffing van het sluitingsuur) en plaatst die terecht onder "andere vergunning". Eén bericht daartussen is wel een omgevingsvergunning en wel belangrijk; zie hieronder. |

## Aanleiding

De app leest bij de bron alleen de rubriek "omgevingsvergunning". Een gemeente die een bericht over
een omgevingsvergunning onder een andere rubriek zet, valt daardoor weg. Bij Roosendaal gaat het om
alle aanvragen en termijnverlengingen.

## Wat is onderzocht

Eén zoekvraag: alle berichten van de laatste 42 dagen met "omgevingsvergunning" in de titel, die niet
onder de rubriek "omgevingsvergunning" of "ruimtelijk plan" staan, van dezelfde overheden die de
app nu al opvraagt. Die berichten zijn door de regels van de app gehaald (locatie, regio, stand,
ontwikkellocatie of niet).

| | |
|---|---:|
| Gevonden bij de bron | 218 |
| Buiten de kern en buiten de regio's (vooral waterschappen elders in Brabant) | 92 |
| Binnen de kern of een regio | 126 |
| Verzoeken voor deze proef | 40: 1 zoekvraag, 34 teksten, 5 percelen |
| Weigeringen (HTTP 429) | 0 |

Geen van de 126 staat nu al in de app (geen enkel bericht met hetzelfde nummer).

## Twee varianten

| | Variant A: alleen gemeenten, rubrieken "andere beschikking" en "andere vergunning" | Variant B: alles met "omgevingsvergunning" in de titel |
|---|---:|---:|
| Berichten erbij | 83 | 126 |
| waarvan in de kern | 14 | 34 |
| waarvan ontwikkellocatie in de kern | 1 | 1 |
| waarvan weggefilterd in de kern | 13 | 33 |
| Regio's: ontwikkellocatie / onzeker / weggefilterd | 5 / 1 / 63 | 5 / 2 / 85 |
| Wat B meer geeft dan A | | 37 berichten van waterschappen over wateractiviteiten en 6 losse berichten; alle 43 weggefilterd of beleid |

**Variant B voegt niets toe wat ertoe doet.** De 43 extra berichten zijn vergunningen van
waterschappen voor wateractiviteiten (taluds, lozingen, faunavoorzieningen) en een beleidsregel. Het
voorstel is daarom variant A.

## Wat variant A oplevert

### In de kern: 14 berichten

| Gemeente | Datum | Rubriek bij de bron | Bericht | Uitkomst in de app |
|---|---|---|---|---|
| **Dongen** | 27-10-2026 | andere vergunning | **Besluit op aanvraag omgevingsvergunning voor wijzigen van winkels in 23 woningen, Europaplein 45 t/m 53** | **Ontwikkellocatie**, score 52, rang 55 van dan 81 |
| Dongen | 08-10 tot 17-11 | andere vergunning (4), andere beschikking (3) | Kappen van een boom, een uitweg, een kabelgoottegel, twee keer een container, speelautomaten, ontheffing sluitingsuur | Weggefilterd (7) |
| Oisterwijk | 07-10 en 14-10 | andere beschikking | Geweigerd omdat geen vergunning nodig is (2) | Weggefilterd |
| Hilvarenbeek | 13-10 | andere beschikking | Buiten behandeling gesteld, Molenstraat 20 Diessen | Weggefilterd |
| Oirschot | 26-10 | andere beschikking | Ingetrokken, ligboxenstal Meierijsebaan 9 | Weggefilterd |
| Tilburg | 12-10 | andere beschikking | Ambtshalve intrekking | Weggefilterd |
| Vught | 07-10 | andere vergunning | Binnengekomen aanvraag, Catharinastraat 11 Helvoirt | Weggefilterd |

De winst in de kern is één bericht in 42 dagen, maar wel een ontwikkellocatie van 23 woningen op 14
km van Tilburg die de app nu mist. Of dit bij Dongen vaker gebeurt, zegt één venster van 42 dagen
niet.

### In de regio's: 69 berichten

| Gemeente | Berichten | Wat | Uitkomst in de app |
|---|---:|---|---|
| Roosendaal | 58 | 44 aanvragen, 12 termijnverlengingen, 2 ontwerpbesluiten | 2 ontwikkellocaties (10 woningen President Kennedylaan 1, score 87; 2 woningen Plantagebaan 69a in Wouw, score 77), 1 onzeker, 55 weggefilterd |
| Etten-Leur | 5 | Ambtshalve intrekkingen | Weggefilterd |
| Noord-Beveland | 4 | Ontwerp- en conceptbesluiten ter inzage | 3 ontwikkellocaties (scores 46 tot 52), 1 weggefilterd |
| Hulst, Dongen (buiten de 15 km) | 1 en 1 | | Weggefilterd |

Hiermee is het gat bij Roosendaal dicht: de 58 berichten zijn precies de aanvragen en verlengingen
die nu ontbreken. De opmerking "Aanvragen ontbreken" bij Roosendaal kan dan weg.

## Wat het kost aan verzoeken

| | Nu | Met variant A |
|---|---:|---:|
| Gewone run | 35 | 36: één zoekvraag erbij (218 berichten passen in één blad van 500) |
| Volledige run | 2.047 | ongeveer 2.055: de zoekvraag, 5 teksten en een paar percelen |
| Nieuwe teksten per dag | | Vrijwel geen: 78 van de 83 berichten hebben een omschrijving bij de bron |

De zoekvraag vraagt de bron om op een woord in de titel te zoeken. Dat doet de app al voor
verkoopvoornemens; het duurde in de proef minder dan twee seconden.

## Wat het betekent voor de berichten die we nu al tonen

| Punt | Gevolg |
|---|---|
| Bestaande berichten | Veranderen niet. Er komen alleen berichten bij; geen bericht krijgt een andere klasse, score of zin |
| Dubbelingen | Geen. Een bericht staat bij de bron onder één rubriek; geen van de 126 staat nu al in de app |
| Ranglijst van de kern | Eén ontwikkellocatie erbij (81 in plaats van 80). Zij komt op rang 55; de 26 berichten daaronder schuiven één plaats op |
| Top 10 van het ochtendscherm | Verandert in dit venster niet |
| Weggefilterd in de kern | 13 erbij (1.015 in plaats van 1.002) |
| Soort op de kaart | De berichten krijgen het label "Vergunning", ook de zeven van Dongen die geen omgevingsvergunning zijn. Ze staan onder weggefilterd met de gewone reden; aan de titel is te zien wat het is |
| Stand (aanvraag, verleend, enzovoort) | Wordt voor deze titels goed afgeleid: "Ingediende aanvraag" wordt Aanvraag, "Verlengen beslistermijn" wordt Beslistermijn verlengd, "Intrekken" wordt Ingetrokken. Nagekeken op alle 83 |
| Hetzelfde dossier twee keer | Bij 14 van de 58 berichten van Roosendaal staat op dezelfde plek al een later bericht (de verleende vergunning). Dat is zoals het bij elke andere gemeente gaat: aanvraag en besluit zijn twee berichten |
| Tabblad Adres | Vindt deze berichten vanzelf, in de kern en in de regio's |
| "Nieuw sinds je vorige bezoek" | Bij de eerste run na het inbouwen is het bericht van Dongen van 27-10 voor de app nieuw, al is het drie weken oud. Het telt dan één keer mee in de ochtendzin |

## Voorstel

Bouw variant A: één extra zoekvraag per run, voor de gemeenten uit de lijst, de rubrieken "andere
beschikking" en "andere vergunning", met "omgevingsvergunning" in de titel. De berichten gaan als
vergunning door dezelfde regels als alle andere.

| Onderdeel | Wat er zou veranderen |
|---|---|
| `signalen/bekendmakingen.py` | Een derde zoekvraag naast vergunningen en plannen; de berichten krijgen het soort "vergunning" |
| `config.json` | De opmerking bij Roosendaal vervalt |
| Tests | De zoekvraag; een bericht uit zo'n rubriek wordt een vergunning; een bericht dat al onder de gewone rubriek binnenkwam, komt er niet dubbel in; de kern van vóór de wijziging blijft gelijk op de 14 nieuwe berichten na |
| Meting | Opnieuw vóór en na, zoals bij de regio's |

**Dit wijzigt de kern.** Dat is de reden dat het niet bij de regio-uitbreiding is meegenomen. Het
gaat om 14 berichten erbij in 42 dagen, waarvan 13 onder weggefilterd.

## Wat ik niet weet

| Punt | Toelichting |
|---|---|
| Of 42 dagen representatief is | Eén venster. De ontwikkellocatie in Dongen kan een uitschieter zijn |
| Of gemeenten nog andere woorden gebruiken | Gezocht is op "omgevingsvergunning" in de titel. Een bericht onder een andere rubriek zonder dat woord (bijvoorbeeld alleen "bouwen van een woning") is hiermee niet gevonden en niet geteld |
| Of andere rubrieken ook lekken | Buiten de twee rubrieken van variant A vond de zoekvraag in de gemeenten nog 6 berichten (overige overheidsinformatie, omgevingsmelding, evenementenvergunning, beleidsregel), alle weggefilterd of beleid. Die laat variant A liggen |
| Gedrag op GitHub | De proef liep vanuit deze container. Eén zoekvraag meer zal daar weinig uitmaken, maar gemeten is het niet |

## Buiten dit voorstel

- **De handmatige run op GitHub kon ik niet starten.** De koppeling van deze sessie mag lezen,
  pushen en pull requests maken, maar geen workflow starten (GitHub antwoordde met 403). Ik heb dat
  niet omzeild. Wim kan de run zelf starten: Actions, "Dagelijkse verversing", "Run workflow",
  branch `claude/optimistic-gauss-sb0xpy`, beide vinkjes uit. Het log kan ik daarna wel lezen.
- **Voor die run toegevoegd** (commit `d5ab774`): de stap "Gebied bijwerken" meldt nu ook het aantal
  verzoeken, de duur en de weigeringen, zodat het log per stap dezelfde cijfers geeft.
- **Niets samengevoegd**, niets geforceerd; de cache en het schema van de workflow zijn niet
  gewijzigd.
