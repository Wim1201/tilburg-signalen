"""Derive a readable phase and plan kind from the title of a notice."""
import re

# Leading words that say nothing about the phase, e.g. "Gemeente Heusden - " or "Reguliere procedure - ".
_PREFIX = re.compile(r"^(?:(?:gemeente|provincie)\s[^-–]{2,40}[-–]\s*|(?:reguliere|uitgebreide) procedure\s*[-–]\s*|bopa-)+")
_EXTENSION = r"beslistermijn|termijnverlenging|verlengingsbesluit|^(?:kennisgeving )?verleng"
_WITHDRAWN = r"ingetrokken|intrekking|intrekken|buiten behandeling|niet in behandeling"
_REFUSED = r"geweigerd|weigering|weigeren"
_EXEMPT = r"vergunningvrij|vergunningsvrij|geen vergunning nodig"
# A title that opens like this announces an application, whatever the description after it says.
_APPLICATION_START = re.compile(
    r"^(?:kennisgeving )?(?:ingekomen|ingediende|ontvangst|ontvangen|binnengekomen|aangevraagde)\b"
    r"|^(?:kennisgeving )?(?:vergunning)?aanvraag\b(?! (?:verleend|geweigerd|ingetrokken|buiten))"
    r"|^omgevingsvergunning aangevraagd")

# Order matters: the first matching pattern wins.
_PERMIT_PHASES = [
    (_EXTENSION, "Beslistermijn verlengd"),
    (_WITHDRAWN, "Ingetrokken of buiten behandeling"),
    (_REFUSED, "Geweigerd"),
    (_EXEMPT, "Vergunningvrij"),
    (r"ontwerp", "Ontwerpbesluit"),
    (r"verleend|toegekend|verlening|verlenen|^toestemming|^vergunning voor", "Verleend"),
    (r"besluit|beschikking|beslissing", "Besluit"),
    (r"aanvraag|aangevraagd|aanvragen|ingediend|ingekomen|ontvangen", "Aanvraag"),
]

_PLAN_PHASES = [
    (r"onherroepelijk", "Onherroepelijk"),
    (r"voorbereidingsbesluit|voorbeschermingsregels", "Voorbereidingsbesluit"),
    (r"voornemen|vooraankondiging|voorontwerp", "Voornemen"),
    (r"ontwerp", "Ontwerp"),
    (r"herstel", "Herstelbesluit"),
    (r"vastgesteld|vaststelling|vaststellen|wijzigingsbesluit", "Vastgesteld"),
]

_PLAN_KINDS = [
    (r"bestemmingsplan|wijzigingsplan|uitwerkingsplan|inpassingsplan|parapluplan", "Bestemmingsplan"),
    (r"omgevingsplan", "Omgevingsplan"),
    (r"omgevingsvisie|structuurvisie", "Omgevingsvisie"),
    (r"projectbesluit", "Projectbesluit"),
    (r"programma", "Programma"),
    (r"omgevingsverordening|verordening", "Verordening"),
]


def _first_match(patterns, text, default):
    lowered = text.lower()
    for pattern, label in patterns:
        if re.search(pattern, lowered):
            return label
    return default


def permit_phase(title):
    text = _PREFIX.sub("", title.strip().lower())
    if _APPLICATION_START.search(text):
        if re.search(_EXTENSION, text):
            return "Beslistermijn verlengd"
        if re.search(_EXEMPT, text):
            return "Vergunningvrij"
        return "Aanvraag"
    return _first_match(_PERMIT_PHASES, text, "Bekendmaking")


def plan_phase(title):
    return _first_match(_PLAN_PHASES, title, "Bekendmaking")


def plan_kind(title):
    return _first_match(_PLAN_KINDS, title, "Ruimtelijk plan")
