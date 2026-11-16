"""Detect publication days for which the source delivered (almost) nothing.

The search service of officielebekendmakingen.nl sometimes lags behind the publications themselves.
Every update fetches the whole window again, so a missed day is picked up by a later run without
any bookkeeping; this module only makes the gap visible.

Method: count the Gemeenteblad publications the service knows per working day, and compare each
recent day with the median of the other working days.
"""
import datetime
import re
import statistics

from . import http

SRU_URL = "https://repository.overheid.nl/sru"
REFERENTIE_DAGEN = 28   # working days in this period set the normal level
CONTROLE_DAGEN = 14     # days in this period are checked
DREMPEL = 0.5           # below this share of the normal level a day counts as incomplete
PUBLICATIE_UUR = 10     # the current day is only judged from this hour (publication is around nine)


def _pasen(jaar):
    """Easter Sunday (Gregorian calendar, Meeus/Jones/Butcher)."""
    a, b, c = jaar % 19, jaar // 100, jaar % 100
    d, e = b // 4, b % 4
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    j, k = c // 4, c % 4
    m = (a + 11 * h) // 319
    r = (2 * e + 2 * j - k - h + m + 32) % 7
    maand = (h - m + r + 90) // 25
    dag = (h - m + r + maand + 19) % 32
    return datetime.date(jaar, maand, dag)


def feestdagen(jaar):
    """Dutch public holidays on which no official publications appear."""
    pasen = _pasen(jaar)
    koningsdag = datetime.date(jaar, 4, 27)
    if koningsdag.weekday() == 6:
        koningsdag = datetime.date(jaar, 4, 26)
    return {
        datetime.date(jaar, 1, 1), pasen + datetime.timedelta(days=1), koningsdag, datetime.date(jaar, 5, 5),
        pasen + datetime.timedelta(days=39), pasen + datetime.timedelta(days=50),
        datetime.date(jaar, 12, 25), datetime.date(jaar, 12, 26),
    }


def is_publicatiedag(dag):
    return dag.weekday() < 5 and dag not in feestdagen(dag.year)


def publicatiedagen(vandaag, dagen=REFERENTIE_DAGEN):
    """Working days in the last `dagen` days, up to and including today."""
    reeks = [vandaag - datetime.timedelta(days=offset) for offset in range(dagen, -1, -1)]
    return [dag for dag in reeks if is_publicatiedag(dag)]


def tel_gemeenteblad(dag):
    """Number of Gemeenteblad publications the search service knows for one day."""
    query = f'c.product-area==officielepublicaties AND w.publicatienaam=="Gemeenteblad" AND dt.date=={dag.isoformat()}'
    body = http.get(SRU_URL, {"query": query, "maximumRecords": 0}).decode("utf-8", "replace")
    found = re.search(r"numberOfRecords>(\d+)<", body)
    if not found:
        raise RuntimeError(f"Geen telling ontvangen voor {dag.isoformat()}")
    return int(found.group(1))


def onvolledige_dagen(telling, nu, controle_dagen=CONTROLE_DAGEN, drempel=DREMPEL):
    """Days in the check period with far fewer publications than normal.

    `telling` maps dates to counts. Returns a list of {"datum", "aantal", "verwacht"}, oldest first.
    The current day is skipped before publication time; weekends and holidays are never judged.
    """
    vandaag = nu.date()
    werkdagen = {dag: aantal for dag, aantal in telling.items() if is_publicatiedag(dag)}
    eerdere = [aantal for dag, aantal in werkdagen.items() if dag != vandaag]
    if len(eerdere) < 3:
        return []  # too little to say what is normal
    verwacht = statistics.median(eerdere)
    if verwacht <= 0:
        return []
    start = vandaag - datetime.timedelta(days=controle_dagen)
    gaten = []
    for dag in sorted(werkdagen):
        if dag < start or (dag == vandaag and nu.hour < PUBLICATIE_UUR):
            continue
        if werkdagen[dag] < drempel * verwacht:
            gaten.append({"datum": dag.isoformat(), "aantal": werkdagen[dag], "verwacht": round(verwacht)})
    return gaten


def controleer(nu, tel=tel_gemeenteblad):
    """Count the recent working days at the source and return the incomplete ones."""
    telling = {dag: tel(dag) for dag in publicatiedagen(nu.date())}
    return onvolledige_dagen(telling, nu)
