"""Decide whether a notice marks a development location, how relevant it is, and why.

Rules (from the assignment):
- new construction of two or more dwellings, or
- a parcel of at least 400 m² combined with a development signal: demolition, change of use,
  plot split, zoning change or a vacant commercial building;
- plan changes that enable development (to housing, more building height) rank highest;
- when the size cannot be determined the notice is not hidden but marked 'onzeker'.

Everything here is pure text logic so it can be tested without a network.
"""
import math
import re

ONTWIKKELLOCATIE, ONZEKER, WEGGEFILTERD = "ontwikkellocatie", "onzeker", "weggefilterd"

_NUMBER_WORDS = {
    "een": 1, "één": 1, "twee": 2, "drie": 3, "vier": 4, "vijf": 5, "zes": 6, "zeven": 7, "acht": 8,
    "negen": 9, "tien": 10, "elf": 11, "twaalf": 12, "dertien": 13, "veertien": 14, "vijftien": 15,
    "zestien": 16, "zeventien": 17, "achttien": 18, "negentien": 19, "twintig": 20,
}
_NUMBER = r"\d{1,4}|" + "|".join(sorted(_NUMBER_WORDS, key=len, reverse=True))
_DWELLINGS = r"woningen|appartementen|wooneenheden|woonunits|studio's|woonkavels|bouwkavels|kavels"
# A number only counts when it stands directly before a word ending in woning(en) or appartement(en),
# e.g. "19 woningen" or "98 huurappartementen". "3 dakkapellen op woningen" does not count.
_COUNTED = re.compile(rf"(?<![\w/.,\-])({_NUMBER})\s+[\w\-]*?(?:woningen|woning|appartementen|appartement)\b")
_STREET_END = re.compile(r"(?:straat|weg|laan|kade|dijk|plein|pad|dreef|hof|ring|steeg|baan|singel|park|veld|akker|"
                         r"heide|hoek|eind|berg|gracht|markt|wal|erf|plantsoen|dam)$")
_DEMOLISHED = re.compile(r"^(?:sloop|slopen|gesloopt|gesloopte|amoveren|sloopwerk)")
_SINGLE = re.compile(
    r"\b(?:bouwen|oprichten|realiseren|nieuwbouw|herbouwen|herbouw|bouw)\s+(?:van\s+)?(?:een\s+|één\s+|1\s+)?"
    r"((?:[\w\-]+\s+){0,2}?)[\w\-]*(?:woning|woonhuis|villa|bungalow|woonboerderij)\b")
# Words between the number and the noun that show the number belongs to something else,
# e.g. "3 dakkapellen op woningen".
_BREAKERS = {"op", "aan", "bij", "van", "voor", "in", "naast", "achter", "tussen", "met", "en", "of", "de", "het",
             "te", "tot", "naar", "bomen", "boom", "dakkapellen", "zonnepanelen", "bouwen", "verbouwen", "realiseren",
             "oprichten", "nieuwbouw", "plaatsen", "slopen", "uitbreiden", "wijzigen", "herbouwen", "splitsen",
             "transformeren", "renoveren", "bouw", "sloop"}
_NEW_BUILD = re.compile(r"\bnieuwbouw|\bbouwen\b|oprichten|realiseren|\bbouw van|te bouwen|\bherbouw|woningbouw|toevoegen|"
                        r"transformatie|transformeren|ombouwen|omzetten|verbouwen\b.{0,80}?\b(?:tot|naar)\b")
_PLURAL_UNKNOWN = re.compile(
    rf"\b[\w\-]*(?:{_DWELLINGS})\b|woongebouw|appartementencomplex|appartementengebouw|woningbouw|woontoren|"
    r"woonzorgcomplex|twee-onder-een-kap|2-onder-1-kap|tweekapper")
_RENOVATION = re.compile(r"verduurzam|renover|renovatie|isoler|zonnepanelen|kozijn|onderhoud|funderingsherstel|"
                         r"dakkapel|gevelwijziging|schilderwerk")

_SIGNALS = [
    ("sloop", re.compile(r"\bslopen\b|\bsloop\b|\bgesloopt|\bamover|sloopwerk")),
    ("functiewijziging", re.compile(
        r"functiewijziging|gebruikswijziging|wijzig\w* van (?:de |het )?(?:functie|gebruik)|(?:functie|gebruik) wijzigen|"
        r"omzetten van|omzetting van|transformatie|transformeren|herbestemm|ombouwen|"
        r"(?:kantoor|winkel|bedrijfs|school|kerk|praktijk|horeca)[\w\-]* (?:naar|tot|in) (?:\w+ ){0,2}?[\w\-]*(?:woning|appartement|woon)")),
    ("kavelsplitsing", re.compile(
        r"kavelsplitsing|perceelsplitsing|splits\w* van (?:het |een |de )?(?:perceel|kavel|bouwkavel)|"
        r"(?:perceel|kavel) (?:te )?splitsen|verkaveling|verkavelen")),
    ("bestemmingswijziging", re.compile(
        r"bestemmingswijziging|wijzig\w* (?:van )?(?:het |de )?bestemming|bestemming (?:te )?wijzigen")),
    ("leegstaand bedrijfspand", re.compile(
        r"leegstaand|leegstand|leeg staand|herontwikkeling|"
        r"voormalig\w* (?:bedrijfs|kantoor|winkel|school|fabriek|kerk|bank|garage|supermarkt)")),
]
# Deviating from the plan counts as a zoning change, unless it only serves a small job.
_DEVIATION = re.compile(r"buitenplanse|\bbopa\b|afwijk\w* van (?:het |de regels van het )?(?:bestemmingsplan|omgevingsplan)|"
                        r"in strijd met (?:het |de regels van het )?(?:bestemmingsplan|omgevingsplan)|planologisch")
_SMALL_JOB = re.compile(r"dakkapel|erfafscheiding|schutting|carport|overkapping|aanbouw|uitbouw|bijgebouw|tuinhuis|"
                        r"zonnepanelen|reclame|inrit|uitweg|kappen|airco|warmtepomp|veranda|serre|dakopbouw|schuur|"
                        r"berging|garage|kozijn|terras|zwembad|paardenbak|mantelzorg|hekwerk|poort|vlaggenmast")

_PLAN_HOUSING = re.compile(r"woning|wonen|woongebied|appartement|woonzorg|wooneenhe|woonfunctie")
_PLAN_HEIGHT = re.compile(r"bouwhoogte|goothoogte|bouwlagen|hoger bouwen")
_PLAN_OTHER = re.compile(r"herontwikkeling|transformatie|nieuwbouw|bouwmogelijkhe|ontwikkelgebied|bedrijfsgebouw|"
                         r"bedrijfsruimte|bouwvlak|uitbreiding van|supermarkt|realiseren van|\bbouw van|mogelijk (?:te )?mak|"
                         r"maakt (?:het )?(?:\w+ ){0,6}?mogelijk")
_PLAN_THEMATIC = re.compile(r"parapluplan|technische herpublicatie|bruidsschat|omgevingsvisie|programma|datacentra|"
                            r"mestverwerking|riolering|kostenverhaal|basisregeling|fundament|energie assets|tegengaan|"
                            r"voorbeschermingsregels|^(?:kennisgeving )?omgevingsplan gemeente [\w\-]+$")
_SALE_MINOR = re.compile(r"snippergroen|groenstrook|reststrook|enexis|trafo|nutsvoorziening|watergang|landbouwgrond")

_PHASE_PENALTY = {"Ingetrokken of buiten behandeling": 25, "Geweigerd": 15, "Vernietigd": 25,
                  "Beslistermijn verlengd": 5, "Niet rechtsgeldig": 25}


def m2(value):
    """1850 -> '1.850 m²' (Dutch thousands separator)."""
    return f"{round(value):,}".replace(",", ".") + " m²"


def _number(token):
    return int(token) if token.isdigit() else _NUMBER_WORDS[token]


def count_dwellings(text):
    """Number of dwellings named in the text: the sum of all counted numbers, or None.

    Two kinds of numbers are left out: a house number ("Hoofdstraat 120 woningen") and dwellings
    that are demolished ("sloop van 2 woningen"), because the count is about what is added.
    """
    mentions = set()
    for match in _COUNTED.finditer(text):
        before = text[:match.start()].split()
        if before and _STREET_END.search(before[-1].rstrip(",")):
            continue
        if any(_DEMOLISHED.match(word) for word in before[-3:]):
            continue
        # Title and body of a notice repeat each other; the same mention counts once.
        mentions.add((_number(match.group(1)), match.group(0).split()[-1]))
    return sum(number for number, _ in mentions) if mentions else None


def kenmerken(soort, titel, tekst, activiteiten=()):
    """Extract the facts the rules need from the title and description of a notice."""
    text = " ".join(filter(None, [titel, tekst])).lower()
    count = count_dwellings(text)
    new_build = bool(_NEW_BUILD.search(text))
    renovation_only = bool(_RENOVATION.search(text)) and not re.search(r"nieuwbouw|oprichten|woningbouw", text)
    single = any(not (set(m.group(1).split()) & _BREAKERS) for m in _SINGLE.finditer(text))

    dwellings, unknown = None, False
    if count and count >= 2 and new_build and not renovation_only:
        dwellings = count
    elif new_build and not renovation_only and _PLURAL_UNKNOWN.search(text) and not count:
        unknown = True
    elif single:
        dwellings = 1

    signals = [name for name, pattern in _SIGNALS if pattern.search(text)]
    if "slopen" in activiteiten and "sloop" not in signals:
        signals.insert(0, "sloop")
    small_job = bool(_SMALL_JOB.search(text))
    if "bestemmingswijziging" not in signals and _DEVIATION.search(text) and not (small_job and not signals):
        signals.append("bestemmingswijziging")

    plan = None
    if soort == "plan":
        if _PLAN_THEMATIC.search(titel.lower().strip()):
            plan = "thematisch"
        elif _PLAN_HOUSING.search(text):
            plan = "wonen"
        elif _PLAN_HEIGHT.search(text):
            plan = "bouwhoogte"
        elif _PLAN_OTHER.search(text):
            plan = "ontwikkeling"
    return {"woningen": dwellings, "woningenOnbekend": unknown, "signalen": signals, "plan": plan,
            "kleinWerk": small_job, "verkoopKlein": bool(_SALE_MINOR.search(text))}


_AREA = re.compile(r"(?:circa |ca\.? |ongeveer |groot )?(\d{1,3}(?:\.\d{3})+|\d{1,6})(?:,\d+)?\s?(?:m²|m2|vierkante meter)")


def area_in_text(text):
    """Largest area in m² named in a text ('circa 1.250 m²'), or None."""
    sizes = [int(match.replace(".", "")) for match in _AREA.findall(text.lower())]
    return max(sizes) if sizes else None


def needs_area(soort, facts):
    """True when the parcel size decides the outcome, so it is worth looking up."""
    if soort in ("faillissement", "verkoop"):
        return True
    if soort == "plan" or (facts["woningen"] or 0) >= 2:
        return False
    return bool(facts["signalen"])


def _join(words):
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " en " + words[-1]


def _size_bonus(parcel, threshold):
    return min(12, 6 * math.log10(max(parcel, threshold) / threshold)) if parcel else 0


ONGELEZEN = "Tekst nog niet gelezen; een volgende verversing haalt hem op."


def beoordeel(soort, facts, perceel_m2, fase, informatief=True, locatie_bekend=True, drempel=400, tekst_mislukt=False,
              tekst_uitgesteld=False):
    """Return (klasse, score, waarom). `waarom` is one Dutch sentence shown with the notice.

    `tekst_uitgesteld`: the text of a notice in a region was not read yet because the run had read
    its share of new texts. Such a notice is unsure whatever its title says, at the bottom of the
    list, until a later run reads it.
    """
    if tekst_uitgesteld:
        return ONZEKER, 5, ONGELEZEN
    signals = facts["signalen"]
    dwellings = facts["woningen"]
    on_parcel = f" op een perceel van {m2(perceel_m2)}" if perceel_m2 else ""
    penalty = _PHASE_PENALTY.get(fase, 0)

    def result(klasse, score, why):
        return klasse, max(0, round(score - (penalty if klasse != WEGGEFILTERD else 0))), why

    if soort == "plan":
        if facts["plan"] == "thematisch":
            return result(WEGGEFILTERD, 0, "Thematisch of gemeentebreed plan, niet gericht op één ontwikkellocatie.")
        if facts["plan"]:
            what = {"wonen": "de tekst noemt wonen of woningbouw", "bouwhoogte": "de tekst noemt een andere bouwhoogte",
                    "ontwikkeling": "de tekst noemt nieuwe bouw- of gebruiksmogelijkheden"}[facts["plan"]]
            if dwellings and dwellings >= 2:
                what += f" ({dwellings} woningen)"
            base = {"wonen": 100, "bouwhoogte": 96, "ontwikkeling": 92}[facts["plan"]]
            return result(ONTWIKKELLOCATIE, base + min(8, (dwellings or 0) / 10), f"Planwijziging die ontwikkeling mogelijk maakt: {what}.")
        if tekst_mislukt:
            return result(ONZEKER, 60, "De tekst van deze planbekendmaking kon niet worden opgehaald; de volgende verversing probeert het opnieuw.")
        if locatie_bekend:
            return result(ONZEKER, 60, "Planwijziging voor één locatie; uit de bekendmaking blijkt niet wat er mogelijk wordt.")
        return result(WEGGEFILTERD, 0, "Planbericht zonder locatie en zonder ontwikkelsignaal in de tekst.")

    if soort == "faillissement":
        if perceel_m2 is None:
            return result(ONZEKER, 30, "Failliet bedrijf met een bedrijfspand, maar de perceelgrootte is niet te bepalen.")
        if perceel_m2 >= drempel:
            return result(ONTWIKKELLOCATIE, 35 + _size_bonus(perceel_m2, drempel),
                          f"Failliet bedrijf met een bedrijfspand{on_parcel}; het pand kan vrijkomen.")
        return result(WEGGEFILTERD, 0, f"Failliet bedrijf{on_parcel}: kleiner dan {m2(drempel)}.")

    if soort == "verkoop":
        if facts["verkoopKlein"]:
            return result(WEGGEFILTERD, 0, "Verkoop van een groenstrook of grond voor een nutsvoorziening, geen ontwikkellocatie.")
        if perceel_m2 is None:
            return result(ONZEKER, 40, "De overheid wil grond of vastgoed verkopen, maar de omvang is niet te bepalen.")
        if perceel_m2 >= drempel:
            return result(ONTWIKKELLOCATIE, 45 + _size_bonus(perceel_m2, drempel),
                          f"De overheid wil grond of vastgoed verkopen: een perceel van {m2(perceel_m2)} of een deel daarvan.")
        return result(WEGGEFILTERD, 0, f"Verkoop van {m2(perceel_m2)}: kleiner dan {m2(drempel)}.")

    # Permits
    if dwellings and dwellings >= 2:
        extra = f", met {_join(signals)}" if signals else ""
        return result(ONTWIKKELLOCATIE, 70 + min(25, 5 * math.log2(dwellings)) + 2 * len(signals),
                      f"{dwellings} nieuwe woningen{extra}{on_parcel}.")
    if signals:
        label = _join(signals).capitalize()
        if facts["woningenOnbekend"]:
            label += " en nieuwbouw van woningen (aantal niet eenduidig)"
        if perceel_m2 is None:
            return result(ONZEKER, 38 + 4 * len(signals), f"{label}, maar de perceelgrootte is niet te bepalen.")
        if perceel_m2 >= drempel:
            score = 40 + 5 * (len(signals) - 1) + _size_bonus(perceel_m2, drempel) + (8 if facts["woningenOnbekend"] else 0)
            return result(ONTWIKKELLOCATIE, score, f"{label}{on_parcel}.")
        return result(WEGGEFILTERD, 0, f"{label}{on_parcel}: kleiner dan {m2(drempel)}.")
    if facts["woningenOnbekend"]:
        return result(ONZEKER, 55, "Nieuwbouw van woningen, maar het aantal is niet eenduidig uit de bekendmaking te halen.")
    if tekst_mislukt:
        return result(ONZEKER, 20, "De tekst van deze bekendmaking kon niet worden opgehaald; de volgende verversing probeert het opnieuw.")
    if not informatief:
        return result(ONZEKER, 20, "De bekendmaking beschrijft niet wat er gebeurt, dus de omvang is niet te bepalen.")
    if dwellings == 1:
        return result(WEGGEFILTERD, 0, "Nieuwbouw van één woning, zonder ander ontwikkelsignaal.")
    return result(WEGGEFILTERD, 0, "Geen nieuwbouw van woningen en geen ontwikkelsignaal in de bekendmaking.")
