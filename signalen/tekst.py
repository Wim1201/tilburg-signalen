"""Fetch the opening lines of a notice, for notices whose metadata has no description."""
import re

from . import http

# Standard paragraphs that follow the actual description.
_BOILERPLATE = re.compile(r"\b(?:Bezwaar|Inzage|Inzien|Waarom publiceert|Zienswijze|Beroep|Rechtsbescherming|"
                          r"Tegen dit besluit|Wilt u reageren|Meer informatie|Voorlopige voorziening|Hoe kunt u|"
                          r"Wat kunt u|Belanghebbenden|Ter inzage|Reageren)\b")


def uittreksel(xml_text, titel, limiet=600):
    """Return the descriptive part of a publication: the text after the title, up to the boilerplate."""
    body = xml_text.split("</metadata>")[-1]
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
    title = re.sub(r"\s+", " ", titel).strip()
    position = text.find(title)
    if position >= 0:
        text = text[position + len(title):]
    cut = _BOILERPLATE.search(text, 40)
    if cut:
        text = text[:cut.start()]
    return text[:limiet].strip()


def haal_op(url, titel, limiet=600):
    """Download a publication (XML) and return its descriptive part. Raises when the download fails."""
    return uittreksel(http.get(url, timeout=20, attempts=2).decode("utf-8-sig", "replace"), titel, limiet)
