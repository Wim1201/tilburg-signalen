"""Small HTTP helper with retries (standard library only)."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "tilburg-signalen/1.0 (open data reader)"


def get(url, params=None, timeout=90, attempts=4):
    """GET a URL and return the response body as bytes; retries on network and 5xx errors."""
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)
    last_error = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code < 500 and error.code != 429:
                raise
            last_error = error
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            last_error = error
        time.sleep(2 ** attempt * 2)
    raise RuntimeError(f"Ophalen mislukt na {attempts} pogingen: {url} ({last_error})")


def get_json(url, params=None, **kwargs):
    return json.loads(get(url, params, **kwargs))
