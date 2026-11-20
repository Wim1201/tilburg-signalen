/* Tilburg Signalen, tab "Adres": the address report on paper, through the print view of the browser.
   No PDF library: the browser prints, and on a phone "print" can also give a PDF.

   The report is built from what the tab shows at that moment, without a list of boxes: every
   section.vak inside #adres-uitkomst is copied, in the order of the page, so a box added later
   comes along by itself. In the copy everything that was folded, small or hidden on the screen is
   opened, buttons go, and links become readable text with a number, listed together at the end.
   A box can keep a part off paper with data-afdruk="nee".

   The report is built when the button is pressed and again just before printing (beforeprint),
   so that printing through the menu of the browser gives the same. As soon as the tab changes
   after that, the copy is thrown away: paper never shows an older state than the screen. The print
   style (styles.css, @media print) shows only the report while the tab "Adres" is open. */
(function (root) {
  "use strict";

  var TIJDZONE = "Europe/Amsterdam";

  // The first box on paper, before any register: what the report is not, and how to read an empty answer.
  var LEES_DIT_EERST = [
    "Dit rapport is geen advies. Het zet op een rij wat openbare bronnen over dit adres zeggen op het moment van opvragen. Laat een besluit over koop, verbouwing of bezwaar controleren door de gemeente of een deskundige.",
    "Wijzigingen sinds 1-1-2024 (Omgevingswet, omgevingsplan) ontbreken bij het bestemmingsplan. Wat nu geldt, staat in Regels op de kaart van het Omgevingsloket.",
    "Geen getal betekent niet: geen beperking. Bouwhoogte, bebouwingspercentage en andere maten kunnen in de regels staan.",
    "Geen resultaat betekent alleen: niet gevonden in die bron, op dat moment. Het betekent niet dat er niets is.",
  ];

  var LIJNEN = 12; // lines for own notes

  function tweeCijfers(n) { return (n < 10 ? "0" : "") + n; }

  /* Date and time in the Netherlands, e.g. "20 november 2026 om 14:05". */
  function moment(date) {
    var dag = date.toLocaleDateString("nl-NL", { timeZone: TIJDZONE, day: "numeric", month: "long", year: "numeric" });
    var tijd = date.toLocaleTimeString("nl-NL", { timeZone: TIJDZONE, hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
    return dag + " om " + tijd;
  }

  /* The day in the Netherlands as 2026-11-20, for the file name. */
  function isoDag(date) {
    var parts = {};
    new Intl.DateTimeFormat("en-GB", { timeZone: TIJDZONE, year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(date)
      .forEach(function (part) { parts[part.type] = part.value; });
    return parts.year + "-" + parts.month + "-" + parts.day;
  }

  /* The title of the page while printing: most browsers name the PDF after it. Only the address as
     the user chose it, never stored; the old title comes back after printing. */
  function afdrukTitel(adres, date) {
    var naam = String(adres || "").replace(/[\\\/:*?"<>|]+/g, " ").replace(/\s+/g, " ").trim();
    return "Adresrapport" + (naam ? " " + naam : "") + " " + isoDag(date);
  }

  /* Links numbered in order of first appearance; the same address twice keeps one number. */
  function Links() { this.lijst = []; }
  Links.prototype.nummer = function (url, label) {
    for (var i = 0; i < this.lijst.length; i++) if (this.lijst[i].url === url) return i + 1;
    this.lijst.push({ url: url, label: label });
    return this.lijst.length;
  };

  /* How far the box got: still waiting, an answer with a retry button (a register that did not
     answer, or answered only partly), or an answer. Read from the box, not from the box's code. */
  function stand(vak) {
    if (vak.querySelector(".bezig")) return "bezig";
    if (vak.querySelector("button")) return "onvolledig";
    return "beantwoord";
  }

  var STAND_TEKST = {
    bezig: "Nog geen antwoord toen dit rapport werd gemaakt.",
    onvolledig: "Niet of niet volledig beantwoord; zie de melding in het vak.",
    beantwoord: "Beantwoord.",
  };

  /* The lines of a box that name a source or say when it was asked. */
  function bronregels(vak) {
    return [].map.call(vak.querySelectorAll(".bronregel"), function (node) { return node.textContent.replace(/\s+/g, " ").trim(); })
      .filter(function (text) { return /^bron\b|opgevraagd/i.test(text); });
  }

  var exported = { LEES_DIT_EERST: LEES_DIT_EERST, moment: moment, isoDag: isoDag, afdrukTitel: afdrukTitel, Links: Links, STAND_TEKST: STAND_TEKST };
  if (typeof module === "object" && module.exports) module.exports = exported;
  if (!root.document) return;
  root.TilburgRapport = exported;

  /* ---------- In the browser ---------- */

  var document = root.document;
  function $(id) { return document.getElementById(id); }
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  var uitkomst = $("adres-uitkomst"), rapport = $("adres-rapport"), knop = $("rapport-afdrukken");
  if (!uitkomst || !rapport) return;

  // When the address was chosen and when each box last got its content. A box fills itself by
  // emptying and refilling its .vak-inhoud; that change is the moment it was asked.
  var gekozen = null, gevuld = new WeakMap();
  new MutationObserver(function (changes) {
    var nu = new Date();
    changes.forEach(function (change) {
      var target = change.target.nodeType === 1 ? change.target : change.target.parentNode;
      if (target && target.id === "adres-naam") gekozen = nu;
      if (target && target.classList && target.classList.contains("vak-inhoud")) gevuld.set(target.closest(".vak"), nu);
    });
    weg(); // the screen changed: the copy is no longer what the screen shows (the copy itself lies outside)
  }).observe(uitkomst, { childList: true, subtree: true, characterData: true, attributes: true });

  function weg() {
    rapport.textContent = "";
    rapport.classList.remove("klaar");
  }

  /* A copy of the content of one box, made fit for paper. */
  function kopie(inhoud, links) {
    var copy = inhoud.cloneNode(true);
    [].slice.call(copy.querySelectorAll('button, input, select, textarea, [data-afdruk="nee"]')).forEach(function (node) { node.remove(); });
    [].forEach.call(copy.querySelectorAll("[id]"), function (node) { node.removeAttribute("id"); });
    copy.removeAttribute("id");
    [].forEach.call(copy.querySelectorAll("[hidden]"), function (node) { node.removeAttribute("hidden"); });
    [].forEach.call(copy.querySelectorAll("details"), function (node) { node.open = true; });
    [].forEach.call(copy.querySelectorAll("summary .toggle"), function (node) { node.remove(); });
    [].slice.call(copy.querySelectorAll("a[href]")).forEach(function (a) {
      var label = a.textContent.replace(/\s+/g, " ").trim() || a.href, ref = el("span", "rapport-link");
      ref.appendChild(document.createTextNode(label + " "));
      ref.appendChild(el("span", "rapport-ref", "[" + links.nummer(a.href, label) + "]"));
      a.replaceWith(ref);
    });
    copy.className = "vak-inhoud";
    return copy;
  }

  function sectie(titel, className) {
    var box = el("section", "rapport-vak" + (className ? " " + className : ""));
    box.appendChild(el("h2", null, titel));
    return box;
  }

  /* Build the report from the tab as it is now. Returns false when no address is chosen. */
  function bouw() {
    if (uitkomst.hidden) return false;
    var nu = new Date(), links = new Links(), bronnen = [];
    rapport.textContent = "";

    var kop = el("header", "rapport-kop");
    kop.appendChild(el("p", "rapport-merk", "Tilburg Signalen"));
    kop.appendChild(el("h1", null, "Adresrapport"));
    kop.appendChild(el("p", "rapport-adres", $("adres-naam").textContent));
    kop.appendChild(el("p", "rapport-sub", $("adres-sub").textContent));
    kop.appendChild(el("p", "rapport-tijd", "Opgevraagd op " + moment(gekozen || nu) + ". Dit rapport is gemaakt op " + moment(nu) + "."));
    rapport.appendChild(kop);

    var eerst = sectie("Lees dit eerst", "rapport-eerst"), lijst = el("ul");
    LEES_DIT_EERST.forEach(function (text) { lijst.appendChild(el("li", null, text)); });
    eerst.appendChild(lijst);
    rapport.appendChild(eerst);

    [].forEach.call(uitkomst.querySelectorAll("section.vak"), function (vak) {
      if (vak.getAttribute("data-afdruk") === "nee") return;
      var kopTekst = (vak.querySelector("h3, h2") || {}).textContent || "Vak", inhoud = vak.querySelector(".vak-inhoud") || vak;
      var toen = gevuld.get(vak) || gekozen || nu, hoe = stand(vak);
      var box = sectie(kopTekst);
      box.appendChild(el("p", "rapport-stand", "Opgevraagd op " + moment(toen) + ". " + STAND_TEKST[hoe]));
      box.appendChild(kopie(inhoud, links));
      rapport.appendChild(box);
      bronnen.push({ titel: kopTekst, toen: toen, stand: hoe, regels: bronregels(vak) });
    });

    var notities = sectie("Eigen aantekeningen", "rapport-notities"), lijnen = el("div", "rapport-lijnen");
    for (var i = 0; i < LIJNEN; i++) lijnen.appendChild(el("div", "rapport-lijn"));
    notities.appendChild(lijnen);
    rapport.appendChild(notities);

    var bron = sectie("Bronnen en beperkingen", "rapport-bronnen"), lijstBronnen = el("ul");
    var adresRegel = el("li");
    adresRegel.appendChild(el("strong", null, "Adres"));
    adresRegel.appendChild(document.createTextNode(": PDOK Locatieserver (Kadaster), opgevraagd op " + moment(gekozen || nu) + "."));
    lijstBronnen.appendChild(adresRegel);
    var gegevens = root.TilburgSignalenGegevens;
    bronnen.forEach(function (item) {
      var regel = el("li");
      regel.appendChild(el("strong", null, item.titel));
      regel.appendChild(document.createTextNode(": opgevraagd op " + moment(item.toen) + ". " + STAND_TEKST[item.stand]));
      item.regels.forEach(function (text) { regel.appendChild(document.createTextNode(" ")); regel.appendChild(el("span", "rapport-bronregel", text)); });
      lijstBronnen.appendChild(regel);
    });
    if (gegevens && gegevens.bijgewerkt) {
      var app = el("li");
      app.appendChild(el("strong", null, "Berichten van de app"));
      app.appendChild(document.createTextNode(": laatst ververst op " + moment(new Date(gegevens.bijgewerkt)) + ". Een bericht kan ontbreken of na die tijd zijn verschenen."));
      lijstBronnen.appendChild(app);
    }
    bron.appendChild(lijstBronnen);
    bron.appendChild(el("p", "rapport-voet", "Gemaakt met Tilburg Signalen (wim1201.github.io/tilburg-signalen). Alleen openbare gegevens, zonder garantie op volledigheid of juistheid."));
    rapport.appendChild(bron);

    if (links.lijst.length) {
      var linkVak = sectie("Links", "rapport-links"), lijstLinks = el("ol");
      links.lijst.forEach(function (link) {
        var regel = el("li");
        regel.appendChild(document.createTextNode(link.label + ": "));
        regel.appendChild(el("span", "rapport-url", link.url));
        lijstLinks.appendChild(regel);
      });
      linkVak.appendChild(lijstLinks);
      rapport.appendChild(linkVak);
    }

    rapport.classList.add("klaar");
    return true;
  }

  var oudeTitel = null;
  function voorAfdrukken() {
    if ($("view-adres").hidden || !bouw()) return;
    if (oudeTitel === null) oudeTitel = document.title;
    document.title = afdrukTitel($("adres-naam").textContent, new Date());
  }
  function naAfdrukken() {
    if (oudeTitel !== null) { document.title = oudeTitel; oudeTitel = null; }
  }

  root.addEventListener("beforeprint", voorAfdrukken);
  root.addEventListener("afterprint", naAfdrukken);
  if (knop) {
    knop.addEventListener("click", function () {
      voorAfdrukken();
      root.print();
    });
  }
  exported.bouw = bouw;
})(typeof window !== "undefined" ? window : globalThis);
