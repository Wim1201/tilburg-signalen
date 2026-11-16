"""Small HTTP helper with retries (standard library only)."""
import collections
import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "tilburg-signalen/1.0 (open data reader)"
MAX_WACHT = 30  # seconds; the wait between attempts never grows beyond this
RETRY_SECONDEN = 180  # time allowed for trying failed downloads once more
MAX_RETRY_WACHT = 20  # seconds; longest pause before such a retry
VERZOEKEN = collections.Counter()  # requests sent in this process, per host (every attempt counts)


class OphaalFout(RuntimeError):
    """A request that failed for good. `reden` is a short cause such as 'HTTP 429' or 'tijdslimiet'."""

    def __init__(self, url, reden, pogingen):
        super().__init__(f"{reden} na {pogingen} poging(en): {url[:150]}")
        self.reden = reden


def wachttijd(poging, basis=2, maximum=MAX_WACHT):
    """Seconds to wait after failed attempt number `poging` (0-based): 2, 4, 8, 16, 30, 30, ..."""
    return min(maximum, basis * 2 ** poging)


def reden(error):
    """Short, groupable description of what went wrong."""
    if isinstance(error, urllib.error.HTTPError):
        return f"HTTP {error.code}"
    if isinstance(error, (TimeoutError, socket.timeout)) or "timed out" in str(error).lower():
        return "tijdslimiet"
    if isinstance(error, urllib.error.URLError):
        return f"verbinding ({str(error.reason)[:60]})"
    return f"{type(error).__name__}"


def get(url, params=None, timeout=90, attempts=4, slaap=time.sleep):
    """GET a URL and return the response body as bytes.

    Network errors, 5xx and 429 are tried again; the wait doubles each time up to MAX_WACHT,
    and a Retry-After header from the server is respected (also up to MAX_WACHT).
    """
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)
    last = None
    host = urllib.parse.urlsplit(url).netloc
    for attempt in range(attempts):
        wait = wachttijd(attempt)
        VERZOEKEN[host] += 1
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code < 500 and error.code != 429:
                raise OphaalFout(url, reden(error), attempt + 1) from error
            last = error
            asked = (error.headers.get("Retry-After") or "") if error.headers else ""
            if asked.isdigit():
                wait = min(MAX_WACHT, max(wait, int(asked)))
        except (urllib.error.URLError, TimeoutError, ConnectionError, socket.timeout) as error:
            last = error
        if attempt < attempts - 1:
            slaap(wait)
    raise OphaalFout(url, reden(last), attempts) from last


def get_json(url, params=None, **kwargs):
    return json.loads(get(url, params, **kwargs))


def parallel(functie, argumenten, pool, slaap=time.sleep):
    """Call `functie` for every argument tuple in parallel. Returns (results, statistiek).

    results is a list of (value, ok). A call that fails is tried once more, one at a time, after the
    parallel round: a public service that refuses a burst of requests usually answers a calm one.
    Before each retry there is a pause that doubles while the service keeps failing, up to
    MAX_RETRY_WACHT seconds, and drops back after a success. The whole retry round stops after
    RETRY_SECONDEN.
    """
    def probeer(args):
        try:
            return functie(*args), True
        except Exception as error:
            return error, False

    def oorzaak(error):
        return getattr(error, "reden", None) or type(error).__name__

    results = list(pool.map(probeer, argumenten))
    eerste = [value for value, ok in results if not ok]
    redenen = collections.Counter(oorzaak(error) for error in eerste)
    deadline = time.monotonic() + RETRY_SECONDEN
    wacht = 1
    for index, (value, ok) in enumerate(results):
        if ok or time.monotonic() >= deadline:
            continue
        slaap(wacht)
        results[index] = probeer(argumenten[index])
        wacht = 1 if results[index][1] else min(MAX_RETRY_WACHT, wacht * 2)
    definitief = [value for value, ok in results if not ok]
    statistiek = {"gevraagd": len(argumenten), "eersteRondeMislukt": len(eerste),
                  "hersteld": len(eerste) - len(definitief), "definitiefMislukt": len(definitief),
                  "redenen": dict(redenen.most_common(5))}
    return [(value if ok else None, ok) for value, ok in results], statistiek
