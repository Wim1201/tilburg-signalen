"""Put the settings from config.json into site/data/berichten.json, and nothing else.

For tests.yml: a pull request tests the data as they are in the repository, and those get a changed
setting only at the next refresh. Run 46 (19-11-2026) failed in the live check after a pull request
that filled in energielabel_worker, while the test run on that pull request was green. This step
lets the browser tests of a pull request see the settings that go live after merging. It fetches
nothing; on GitHub it changes only the copy of the checkout, which is never pushed back.

Usage: python -m signalen.instellingen"""
import json
import sys

from signalen import gebied, update


def zet(document, config):
    """The document with the settings of `config`; everything else stays as it was."""
    return dict(document, **update.instellingen(config))


def main(argv=None):
    config = json.loads(gebied.CONFIG.read_text(encoding="utf-8"))
    document = json.loads(update.OUTPUT.read_text(encoding="utf-8"))
    nieuw = zet(document, config)
    veranderd = sorted(key for key in nieuw if nieuw[key] != document.get(key))
    update.OUTPUT.write_text(json.dumps(nieuw, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("Instellingen uit config.json in de gegevens gezet; gewijzigd: " + (", ".join(veranderd) or "niets"))


if __name__ == "__main__":
    main(sys.argv[1:])
