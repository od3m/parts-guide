#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
druckpunkt — Parts-Guide Liquid-Generator
==========================================

Erzeugt aus den TATSÄCHLICHEN Bildordnern (images/parts/<sektion>/*.png) das
fertige Shopify-Template  page.parts-guide.liquid.

Warum Ordner-Scan statt manifest.json?
  Die manifest.json im Original ist veraltet (fehlende Sektionen, alte Slugs).
  Die Bildordner sind die echte Quelle der Wahrheit.

Workflow für ein Update:
  1. Original-Repo aktualisieren:  git -C base pull        (oder neu klonen)
  2. Generator laufen lassen:      python3 generate_parts_guide.py
  3. Drift-Report lesen  ->  zeigt NEU / ENTFERNT / fehlende Übersetzung
  4. page.parts-guide.liquid in Shopify einsetzen

Bilder-Host: EINE Variable (SITE_BASE) steuert ALLE Bild-URLs.
  Empfehlung: eure eigene GitHub-Pages aus dem od3m-Fork, damit die Shop-Seite
  NICHT mehr am Original-Ersteller hängt. Alternativ Shopify-CDN-Ordner.
"""

import os
import sys

# ─────────────────────────────────────────────────────────────────────────
#  KONFIG  (hier anpassen)
# ─────────────────────────────────────────────────────────────────────────

# Wurzel des Repos mit images/parts/
# Wenn das Skript IM Repo liegt (normaler Betrieb): Skript-Verzeichnis nutzen.
# Fallback auf ./base für das Container-/Dev-Setup.
_script_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.isdir(os.path.join(_script_dir, "images", "parts")):
    REPO_ROOT = _script_dir
else:
    REPO_ROOT = os.path.join(_script_dir, "base")

# Ausgabedatei
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "page.parts-guide.liquid")

# Bild-Host – steuert ALLE <img src>. Eine Zeile, ein Ort.
#   Empfohlen (eigene GitHub-Pages des Forks – Settings -> Pages aktivieren):
SITE_BASE = "https://od3m.github.io/parts-guide"
#   Alternative (Shopify-CDN-Ordner, falls du die Bilder dort hochlädst):
#   SITE_BASE = "https://cdn.shopify.com/s/files/1/0990/0903/6672/files"

# Aktuelle v2.1-PDF auf dem Shopify-CDN
PDF_URL = "https://cdn.shopify.com/s/files/1/0990/0903/6672/files/druckpunkt-parts-guide.pdf?v=1787936411"

# ─────────────────────────────────────────────────────────────────────────
#  DEUTSCHE LABELS  (slug -> Label).  Neue Teile hier ergänzen.
#  Bei mehrdeutigen Slugs greift bei Bedarf der per-Sektion-Override unten.
# ─────────────────────────────────────────────────────────────────────────
LABELS = {
    # Tiere / generisch
    "bee": "Biene", "boar": "Eber", "cat": "Katze", "caterpillar": "Raupe",
    "duck": "Ente", "dragon": "Drache", "eagle": "Adler", "elephant": "Elefant",
    "mouse": "Maus", "parrot": "Papagei", "pig": "Schwein", "snail": "Schnecke",
    "t-rex": "T-Rex", "dino": "Dino", "bird": "Vogel", "raptor": "Raptor",
    "generic": "Generisch", "round": "Rund", "base": "Basis", "small": "Klein",
    "axolotl": "Axolotl", "bulldog": "Bulldog", "dolphin": "Delfin",
    "french-bulldog": "Französische Bulldogge", "narwal": "Narwal", "pug": "Mops",
    "chibi": "Chibi", "folded": "Gefaltet",
    # Augen
    "big": "Groß", "black": "Schwarz", "color": "Farbe", "cute": "Süß",
    "heart": "Herz", "long": "Lang", "reptile": "Reptil", "sleep": "Schlaf",
    "smiley": "Smiley", "x": "X",
    # Hüte
    "cowboy": "Cowboy", "cowboy-hat": "Cowboy", "detective": "Detektiv", "detective-hat": "Detektiv",
    "party-hat": "Partyhut", "police-hat": "Polizeimütze", "police-hat.locked": "Polizeimütze",
    "sailor-hat": "Matrosenmütze", "traffic-cone": "Verkehrskegel",
    # Körper-/Untersegmente
    "base-small": "Basis Klein", "fur": "Fell", "flex": "Flex",
    "mini-flex": "Mini Flex",
    # Flexi
    "angel": "Engel", "feathered": "Gefiedert", "angel-wings": "Engelsflügel",
    "double": "Doppelt", "feathers": "Federn", "love-feathers": "Herzfedern", "standard": "Standard",
    # Schwänze
    "tufted": "Gebüschelt", "sting": "Stachel", "curly": "Lockig", "pointed": "Spitz",
    "bird-legs": "Vogelbeine", "bird-wings": "Vogelflügel", "fins": "Flossen",
    "sploot": "Sploot", "tiny-toes": "Kleine Zehen",
    # Accessoires
    "apple": "Apfel", "bow": "Schleife", "bunny-ears": "Hasenohren",
    "clover": "Klee", "crest": "Kamm", "crown": "Krone", "egg": "Ei",
    "flower": "Blume", "paw": "Pfote", "shell": "Muschel", "spike": "Spike",
    "spines": "Stacheln", "sprout": "Spross", "star": "Stern",
    "strawberry": "Erdbeere", "dragon-spikes": "Drachenspitzen", "fin": "Flosse",
    "lifebuoy": "Rettungsring", "wavy-fin": "Wellige Flosse", "axolotl-gills": "Axolotl-Kiemen",
    # Details
    "angry-eyelids": "Wütende Lider", "cheeks": "Wangen",
    "scales-top": "Schuppen Oben", "scales-side": "Schuppen Seite",
    "eyelashes": "Wimpern", "furry-cheeks": "Pelzwangen",
    "moustache": "Schnurrbart", "pois": "Punkte", "stripes": "Streifen", "blaze": "Blesse",
    "eyebrows": "Augenbrauen", "piercing": "Piercing", "spots": "Flecken", "tongue": "Zunge", "x-butt-mark": "X-Po-Marke",
    # Hörner
    "antennae": "Antennen", "tusk": "Stoßzahn", "reindeer": "Rentier",
    "spiky": "Stachelig", "unicorn": "Einhorn",
}

# ─────────────────────────────────────────────────────────────────────────
#  SEKTIONEN  (Reihenfolge = Anzeige-Reihenfolge in der Guide)
#  folder   : Bildordner unter images/parts/
#  anchor   : id im Liquid (dp-pg-…)
#  word     : Zähl-Wort für das Count-Badge ("13 Tiere")
#  order    : kuratierte Reihenfolge der Slugs; neue Teile werden hinten
#             angehängt + als NEU markiert. Entfernte werden gemeldet.
#  new      : Slugs, die ein "NEU"-Badge bekommen
# ─────────────────────────────────────────────────────────────────────────
SECTIONS = [
    dict(kat="01", anchor="base-animals", folder="base-animals", title="Basistiere",
         word="Tiere", desc="Starte mit einem Basistier. Der Drache ist die neueste Ergänzung.",
         notes=[], new={"dragon"},
         order=["bee","boar","cat","caterpillar","duck","dragon","eagle","elephant","mouse","parrot","pig","snail","t-rex"]),
    dict(kat="02", anchor="heads", folder="heads", title="Köpfe", word="Köpfe",
         desc="Wähle einen Kopf, um die Persönlichkeit deines Flexis festzulegen.",
         notes=[], new=set(),
         order=["base","bee","dragon","duck","elephant","parrot","pig","round","snail","t-rex"]),
    dict(kat="03", anchor="eyes", folder="eyes", title="Augen", word="Stile",
         desc="Verleihe deinem Flexi Ausdruck mit einem von elf Augenstilen.",
         notes=[], new=set(),
         order=["base","big","black","color","cute","heart","long","reptile","sleep","smiley","x"]),
    dict(kat="04", anchor="ears", folder="ears", title="Ohren", word="Stile",
         desc="", notes=[], new=set(),
         order=["cat","elephant","mouse","pig"]),
    dict(kat="05", anchor="hats", folder="hats", title="Hüte", word="Stile",
         desc="", notes=[], new=set(),
         order=["cowboy","detective"]),
    dict(kat="06", anchor="body-segments", folder="body-segments", title="Körpersegmente", word="Stile",
         desc="", notes=[], new=set(),
         order=["base","base-small","fur","flex"]),
    dict(kat="07", anchor="bottom-segs", folder="bottom-segments", title="Untersegmente", word="Stile",
         desc="", notes=[], new=set(),
         order=["bee","flex","mini-flex","round","snail"]),
    dict(kat="08", anchor="flexi-legs", folder="flexi-legs", title="Flexi-Beine (Flügel)", word="Stile",
         desc="", notes=[], new=set(),
         order=["angel","bird","dragon"]),
    dict(kat="09", anchor="flexi-tails", folder="flexi-tails", title="Flexi-Schwänze", word="Stile",
         desc="", notes=[], new=set(),
         order=["feathered","dragon","dino"]),
    dict(kat="10", anchor="legs", folder="legs", title="Beine", word="Stile",
         desc="",
         notes=["Beine werden, sofern verfügbar, angezeigt",
                "Gleiche Beine können je nach Segment unterschiedlich aussehen",
                "Beine nur am Kopfsegment bei Schneckenkopf"],
         new=set(),
         order=["bee","bird","cat","caterpillar","duck","dino","dragon","elephant","generic","pig","small","raptor"]),
    dict(kat="11", anchor="tails", folder="tails", title="Schwänze", word="Stile",
         desc="", notes=[], new=set(),
         order=["bird","cat","duck","tufted","mouse","pig","sting","dino"]),
    dict(kat="12", anchor="accessories", folder="accessories", title="Accessoires", word="Stile",
         desc="Accessoires werden, sofern verfügbar, angezeigt.", notes=[], new=set(),
         order=["apple","bird","bow","bunny-ears","clover","crest","crown","egg","flower","heart","paw","shell","spike","spines","sprout","star","strawberry"]),
    # 13 = Symbole (statisch, kein Karten-Grid) -> wird separat eingefügt
    dict(kat="14", anchor="details", folder="details", title="Details", word="Stile",
         desc="",
         notes=["Details werden, sofern verfügbar, angezeigt",
                "Mehrere Details können gleichzeitig kombiniert werden"],
         new=set(),
         order=["angry-eyelids","cheeks","scales-top","scales-side","eyelashes","furry-cheeks","moustache","pois","stripes"]),
    dict(kat="15", anchor="horns", folder="horns", title="Hörner", word="Stile",
         desc="Kröne deinen Flexi mit Hörnern, Antennen oder einem Einhornhorn. Bestimmte Hörner können gleichzeitig gewählt werden.",
         notes=[], new=set(),
         order=["antennae","dragon","tusk","reindeer","spiky","unicorn"]),
]

# v2.1 override: aktuelle Kategorien und Reihenfolge aus dem Parts Guide.
SECTIONS = [
    dict(kat="01", anchor="base-animals", folder="base-animals", title="Basistiere", word="Tiere", desc="Starte mit einem Basistier.", notes=[], new={"axolotl","bulldog","dolphin","french-bulldog","narwal","pug"}, order=["axolotl","bee","boar","bulldog","cat","caterpillar","dolphin","dragon","duck","eagle","elephant","french-bulldog","mouse","narwal","parrot","pig","pug","snail","t-rex"]),
    dict(kat="02", anchor="heads", folder="heads", title="Köpfe", word="Köpfe", desc="Wähle einen Kopf.", notes=[], new={"bulldog","chibi","dolphin"}, order=["base","bee","bulldog","chibi","dolphin","dragon","duck","elephant","parrot","pig","round","snail","t-rex"]),
    dict(kat="03", anchor="eyes", folder="eyes", title="Augen", word="Stile", desc="Verleihe deinem Flexi Ausdruck.", notes=[], new=set(), order=["base","big","black","color","cute","heart","long","reptile","sleep","smiley","x"]),
    dict(kat="04", anchor="ears", folder="ears", title="Ohren", word="Stile", desc="", notes=[], new={"big","folded"}, order=["big","cat","elephant","folded","mouse","pig"]),
    dict(kat="05", anchor="hats", folder="hats", title="Hüte", word="Stile", desc="", notes=[], new={"party-hat","police-hat","police-hat.locked","sailor-hat","traffic-cone"}, order=["cowboy-hat","crown","detective-hat","party-hat","police-hat.locked","sailor-hat","traffic-cone"]),
    dict(kat="06", anchor="body-segments", folder="body-segments", title="Körpersegmente", word="Stile", desc="", notes=[], new=set(), order=["base","base-small","flex","fur"]),
    dict(kat="07", anchor="bottom-segs", folder="bottom-segments", title="Untersegmente", word="Stile", desc="", notes=[], new=set(), order=["bee","flex","mini-flex","round","snail"]),
    dict(kat="08", anchor="flexi-legs", folder="flexi-legs", title="Flexi-Beine (Flügel)", word="Stile", desc="", notes=[], new=set(), order=["angel","bird","dragon"]),
    dict(kat="09", anchor="wings", folder="wings", title="Wings", word="Stile", desc="", notes=[], new={"angel-wings","double","feathers","love-feathers","standard"}, order=["angel-wings","double","feathers","love-feathers","standard"]),
    dict(kat="10", anchor="flexi-tails", folder="flexi-tails", title="Flexi-Schwänze", word="Stile", desc="", notes=[], new={"dolphin","pointed"}, order=["dino","dolphin","dragon","feathered","pointed"]),
    dict(kat="11", anchor="legs", folder="legs", title="Beine", word="Stile", desc="", notes=["Beine werden, sofern verfügbar, angezeigt"], new={"bird-legs","bird-wings","fins","sploot","tiny-toes"}, order=["bee","bird-legs","bird-wings","caterpillar","cute","dino","fins","dragon","duck","elephant","generic","pig","raptor","small","sploot","tiny-toes"]),
    dict(kat="12", anchor="tails", folder="tails", title="Schwänze", word="Stile", desc="", notes=[], new={"curly"}, order=["bird","cat","curly","dino","duck","mouse","round","sting","tufted"]),
    dict(kat="13", anchor="accessories", folder="accessories", title="Top-Accessoires", word="Stile", desc="Accessoires werden, sofern verfügbar, angezeigt.", notes=[], new={"dragon-spikes","fin","lifebuoy","wavy-fin"}, order=["apple","bird","bow","clover","crest","dragon-spikes","egg","fin","flower","heart","lifebuoy","paw","shell","spike","spines","sprout","star","strawberry","wavy-fin"]),
    dict(kat="14", anchor="side-accessories", folder="side-accessories", title="Side-Accessoires", word="Stile", desc="", notes=[], new={"axolotl-gills"}, order=["axolotl-gills","dragon-spikes"]),
    dict(kat="15", anchor="details", folder="details", title="Details", word="Stile", desc="", notes=["Details werden, sofern verfügbar, angezeigt"], new={"blaze","eyebrows","piercing","spots","tongue","x-butt-mark"}, order=["angry-eyelids","blaze","cheeks","eyebrows","eyelashes","furry-cheeks","moustache","piercing","pois","spots","stripes","tongue","x-butt-mark"]),
    dict(kat="16", anchor="horns", folder="horns", title="Hörner", word="Stile", desc="Kröne deinen Flexi mit Hörnern, Antennen oder einem Einhornhorn.", notes=[], new=set(), order=["antennae","dragon","reindeer","spiky","tusk","unicorn"]),
]

# Inhaltsverzeichnis (vollständig, inkl. der statischen Sektionen)
TOC = [
    ("01","base-animals","Basistiere"), ("02","heads","Köpfe"), ("03","eyes","Augen"),
    ("04","ears","Ohren"), ("05","hats","Hüte"), ("06","body-segments","Körpersegmente"),
    ("07","bottom-segs","Untersegmente"), ("08","flexi-legs","Flexi-Beine (Flügel)"),
    ("09","flexi-tails","Flexi-Schwänze"), ("10","legs","Beine"), ("11","tails","Schwänze"),
    ("12","accessories","Accessoires"), ("13","symbols","Symbole"), ("14","details","Details"),
    ("15","horns","Hörner"), ("16","colors","Farben ändern"), ("17","disable","Teile deaktivieren"),
]

# TOC v2.1: Wings und Side-Accessoires sind eigene Kategorien.
TOC = [
    ("01","base-animals","Basistiere"), ("02","heads","Köpfe"), ("03","eyes","Augen"),
    ("04","ears","Ohren"), ("05","hats","Hüte"), ("06","body-segments","Körpersegmente"),
    ("07","bottom-segs","Untersegmente"), ("08","flexi-legs","Flexi-Beine (Flügel)"),
    ("09","wings","Wings"), ("10","flexi-tails","Flexi-Schwänze"), ("11","legs","Beine"),
    ("12","tails","Schwänze"), ("13","accessories","Top-Accessoires"),
    ("14","side-accessories","Side-Accessoires"), ("15","symbols","Symbole"),
    ("16","details","Details"), ("17","horns","Hörner"), ("18","colors","Farben ändern"),
    ("19","disable","Teile deaktivieren"),
]

# ─────────────────────────────────────────────────────────────────────────
#  Abgleich Ordner <-> kuratierte Reihenfolge  (Drift-Erkennung)
# ─────────────────────────────────────────────────────────────────────────
# Der v2.1-Katalog ist kuratiert. Legacy-Dateien aus der alten PDF werden nicht
# automatisch in die neue Ausgabe aufgenommen.
CURATED_CATALOG = True

def reconcile(sec, report):
    folder = os.path.join(REPO_ROOT, "images", "parts", sec["folder"])
    if not os.path.isdir(folder):
        report.append(f"  [!] Ordner fehlt: images/parts/{sec['folder']} — Sektion '{sec['title']}' übersprungen")
        return []
    on_disk = sorted(f[:-4] for f in os.listdir(folder) if f.lower().endswith(".png"))
    disk_set = set(on_disk)
    known = sec["order"]
    known_set = set(known)

    kept    = [s for s in known if s in disk_set]          # bekannte, weiter vorhanden
    removed = [s for s in known if s not in disk_set]      # im Original entfernt
    added   = [] if CURATED_CATALOG else sorted(s for s in on_disk if s not in known_set)

    ordered = kept + added
    if removed:
        report.append(f"  [-] {sec['title']}: ENTFERNT im Original -> {', '.join(removed)}")
    if added:
        report.append(f"  [+] {sec['title']}: NEU im Original     -> {', '.join(added)}  (als NEU markiert)")
        sec["new"] = set(sec["new"]) | set(added)
    for s in ordered:
        if s not in LABELS:
            report.append(f"  [?] {sec['title']}: KEINE Übersetzung für '{s}' — bitte in LABELS ergänzen (Fallback: '{s}')")
    return ordered

def label_of(slug):
    return LABELS.get(slug, slug.replace("-", " ").title())

# ─────────────────────────────────────────────────────────────────────────
#  Liquid-Bausteine
# ─────────────────────────────────────────────────────────────────────────
def emit_card_section(sec, ordered):
    pairs = "|".join(f"{s},{label_of(s)}" for s in ordered)
    count = f"{len(ordered)} {sec['word']}"
    head = (f'      <div class="dp-pg-section-head"><h2>{sec["title"]}</h2>'
            f'<span class="dp-pg-count">{count}</span></div>')
    desc = f'\n      <p class="dp-pg-section-desc">{sec["desc"]}</p>' if sec["desc"] else ""
    notes = ""
    if sec["notes"]:
        items = "\n".join(f'        <span class="dp-pg-note">{n}</span>' for n in sec["notes"])
        notes = f'\n      <div class="dp-pg-notes">\n{items}\n      </div>'
    # NEU-Logik im for-loop
    new_check = ""
    if sec["new"]:
        conds = " or ".join(f"parts[0] == '{s}'" for s in sorted(sec["new"]))
        new_check = "{% if " + conds + " %} dp-pg-new{% endif %}"
    return f"""  <!-- ══════════════════ {sec['kat']} {sec['title'].upper()} ══════════════════ -->
  <section class="dp-pg-section" id="dp-pg-{sec['anchor']}">
    <div class="dp-pg-container">
      <div class="dp-pg-section-label">Kategorie {sec['kat']}</div>
{head}{desc}{notes}
      <div class="dp-pg-grid">
        {{% assign dp_items = '{pairs}' | split: '|' %}}
        {{% for item in dp_items %}}
          {{% assign parts = item | split: ',' %}}
          <div class="dp-pg-card{new_check}">
            <div class="dp-pg-card-img">
              <img src="{{{{ dp_pg_site_base }}}}/images/parts/{sec['folder']}/{{{{ parts[0] }}}}.png" alt="{{{{ parts[1] }}}}" width="530" height="530" loading="lazy">
            </div>
            <div class="dp-pg-card-label">{{{{ parts[1] }}}}</div>
          </div>
        {{% endfor %}}
      </div>
    </div>
  </section>
"""

def build():
    report = []
    body_sections = []
    for sec in SECTIONS:
        ordered = reconcile(sec, report)
        body_sections.append(emit_card_section(sec, ordered))
        if sec["anchor"] == "accessories":
            body_sections.append(SYMBOLS_BLOCK)   # 13 nach Accessoires einschieben
    body = "\n".join(body_sections)

    toc_rows = "\n".join(
        f'        <a href="#dp-pg-{anchor}"{" "*max(0,14-len(anchor))} class="dp-pg-toc-item">'
        f'<span class="dp-pg-toc-num">{num}</span>{label}</a>'
        for num, anchor, label in TOC
    )

    out = (HEAD
           .replace("__PDF_URL__", PDF_URL)
           .replace("__SITE_BASE__", SITE_BASE)
           + STYLE
           + WRAPPER_OPEN
           + HERO
           + TOC_OPEN + toc_rows + TOC_CLOSE
           + body
           + COLORS_BLOCK
           + DISABLE_BLOCK
           + CTA_BLOCK
           + WRAPPER_CLOSE)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(out)

    print("Drift-Report")
    print("============")
    print("\n".join(report) if report else "  Keine Abweichungen — Liquid deckt sich exakt mit den Bildordnern.")
    print()
    print(f"Geschrieben: {OUT_PATH}")
    print(f"Bild-Host:   {SITE_BASE}")

# ─────────────────────────────────────────────────────────────────────────
#  Statische Bausteine (Chrome) — 1:1 aus deiner Liquid übernommen
# ─────────────────────────────────────────────────────────────────────────
HEAD = """{% comment %}
  druckpunkt — Teile-Übersicht
  Template: templates/page.parts-guide.liquid

  ⚙ Generiert mit generate_parts_guide.py — Teile-Arrays nicht von Hand pflegen,
    sondern Generator neu laufen lassen (siehe SYNC-Hinweis im Skript-Kopf).

  Installation:
  1. Diese Datei nach templates/page.parts-guide.liquid kopieren
  2. Im Shopify-Admin eine neue Seite anlegen, Template "parts-guide" wählen
  3. dp_pg_site_base / dp_pg_pdf_url unten bei Bedarf anpassen
{% endcomment %}

{% assign dp_pg_site_base = "__SITE_BASE__" %}
{% assign dp_pg_pdf_url = "__PDF_URL__" %}

{% # theme-check-disable RemoteAsset %}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link
  href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;800&family=DM+Sans:wght@400;500&display=swap"
  rel="stylesheet"
>
{% # theme-check-enable RemoteAsset %}
"""

STYLE = """
<style>
  /* ── druckpunkt CI/CD Variablen ─────────────────────────────── */
  :root {
    --dp-pg-bg:       #1a1a2e;
    --dp-pg-bg2:      #22223a;
    --dp-pg-mid:      #2d2d44;
    --dp-pg-red:      #e94560;
    --dp-pg-red-dim:  rgba(233,69,96,0.10);
    --dp-pg-red-bdr:  rgba(233,69,96,0.30);
    --dp-pg-white:    #ffffff;
    --dp-pg-lgray:    #f5f5f7;
    --dp-pg-gray:     #8e8e9a;
    --dp-pg-gray2:    #5a5a6a;
    --dp-pg-border:   rgba(255,255,255,0.09);
  }

  .dp-pg-wrapper *,
  .dp-pg-wrapper *::before,
  .dp-pg-wrapper *::after { box-sizing: border-box; margin: 0; padding: 0; }

  .dp-pg-wrapper {
    background: var(--dp-pg-bg);
    color: var(--dp-pg-white);
    font-family: 'DM Sans', Helvetica Neue, Arial, sans-serif;
    font-size: 16px; line-height: 1.7;
    -webkit-font-smoothing: antialiased;
    width: 100vw; position: relative; left: 50%; right: 50%;
    margin-left: -50vw; margin-right: -50vw;
  }
  .dp-pg-wrapper a { color: inherit; text-decoration: none; }

  .dp-pg-btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 18px; border-radius: 6px;
    font-family: 'Outfit', sans-serif; font-weight: 700;
    font-size: 0.8125rem; letter-spacing: -0.2px;
    cursor: pointer; transition: background .15s, transform .12s;
    white-space: nowrap; line-height: 1;
  }
  .dp-pg-btn-primary { background: var(--dp-pg-red); color: #fff; border: none; }
  .dp-pg-btn-primary:hover { background: #c93252; }
  .dp-pg-btn-outline { background: transparent; color: var(--dp-pg-white); border: 1px solid var(--dp-pg-border); }
  .dp-pg-btn-outline:hover { background: var(--dp-pg-mid); }

  .dp-pg-hero {
    position: relative; background: var(--dp-pg-bg2);
    border-bottom: 1px solid var(--dp-pg-border);
    padding: 5rem 2rem 4rem; text-align: center; overflow: hidden;
  }
  .dp-pg-hero::before {
    content: ''; position: absolute; inset: 0;
    background: radial-gradient(ellipse 65% 55% at 50% 0%, rgba(233,69,96,0.07) 0%, transparent 68%);
    pointer-events: none;
  }
  .dp-pg-eyebrow {
    display: inline-block; font-family: 'Outfit', sans-serif;
    font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.16em;
    text-transform: uppercase; color: var(--dp-pg-red);
    border: 1px solid var(--dp-pg-red-bdr); background: var(--dp-pg-red-dim);
    padding: 4px 14px; border-radius: 3px; margin-bottom: 1.5rem;
  }
  .dp-pg-hero h1 {
    font-family: 'Outfit', sans-serif; font-weight: 800;
    font-size: clamp(2.4rem, 6vw, 4.2rem); letter-spacing: -3px;
    line-height: 1.05; margin-bottom: 1.25rem; color: var(--dp-pg-white);
  }
  .dp-pg-hero h1 em { font-style: normal; color: var(--dp-pg-red); }
  .dp-pg-hero-sub {
    font-size: 1.0625rem; color: var(--dp-pg-gray);
    max-width: 560px; margin: 0 auto 2.5rem; line-height: 1.6;
  }
  .dp-pg-hero-actions {
    display: flex; justify-content: center; gap: 0.875rem;
    flex-wrap: wrap; margin-bottom: 3rem;
  }
  .dp-pg-hero-actions .dp-pg-btn { font-size: 0.9rem; padding: 11px 26px; }
  .dp-pg-hero-img {
    max-width: 660px; width: 90%; border-radius: 14px;
    border: 1px solid var(--dp-pg-border); margin: 0 auto; display: block;
    box-shadow: 0 28px 56px rgba(0,0,0,0.45);
  }

  .dp-pg-container { max-width: 1120px; margin: 0 auto; padding: 0 2rem; }

  .dp-pg-section-label {
    font-family: 'Outfit', sans-serif; font-weight: 700;
    font-size: 0.6875rem; letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--dp-pg-red); margin-bottom: 1.125rem;
  }

  .dp-pg-toc-section { padding: 4rem 0; border-bottom: 1px solid var(--dp-pg-border); }
  .dp-pg-toc-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    border: 1px solid var(--dp-pg-border); border-radius: 10px; overflow: hidden;
  }
  .dp-pg-toc-item {
    display: flex; align-items: center; gap: 10px; padding: 13px 17px;
    border-right: 1px solid var(--dp-pg-border); border-bottom: 1px solid var(--dp-pg-border);
    font-size: 0.875rem; font-family: 'DM Sans', sans-serif;
    color: var(--dp-pg-lgray); transition: background .14s, color .14s;
  }
  .dp-pg-toc-item:hover { background: var(--dp-pg-mid); color: var(--dp-pg-red); }
  .dp-pg-toc-num {
    font-family: 'Outfit', sans-serif; font-weight: 700;
    font-size: 0.6875rem; color: var(--dp-pg-gray2); min-width: 20px;
  }

  .dp-pg-section { padding: 3.5rem 0 2rem; border-bottom: 1px solid var(--dp-pg-border); }
  .dp-pg-section:last-of-type { border-bottom: none; }
  .dp-pg-section-head {
    display: flex; align-items: baseline; gap: 0.75rem;
    margin-bottom: 0.625rem; padding-bottom: 0.875rem;
    border-bottom: 1px solid var(--dp-pg-border);
  }
  .dp-pg-section-head h2 {
    font-family: 'Outfit', sans-serif; font-weight: 700;
    font-size: 1.375rem; letter-spacing: -1px; color: var(--dp-pg-white);
  }
  .dp-pg-count {
    font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 0.75rem;
    color: var(--dp-pg-gray2); border: 1px solid var(--dp-pg-border);
    background: var(--dp-pg-mid); border-radius: 20px; padding: 2px 10px;
  }
  .dp-pg-section-desc {
    font-size: 0.9rem; color: var(--dp-pg-gray);
    margin: 0.75rem 0 1.75rem; max-width: 580px; line-height: 1.6;
  }
  .dp-pg-notes { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 1.25rem; }
  .dp-pg-note {
    font-size: 0.8125rem; color: var(--dp-pg-gray); background: var(--dp-pg-mid);
    border: 1px solid var(--dp-pg-border); border-radius: 4px; padding: 4px 12px;
  }

  .dp-pg-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 10px;
  }
  .dp-pg-card {
    background: var(--dp-pg-bg2); border: 1px solid var(--dp-pg-border);
    border-radius: 8px; overflow: hidden; position: relative;
    transition: border-color .15s, transform .15s;
  }
  .dp-pg-card:hover { border-color: var(--dp-pg-red-bdr); transform: translateY(-2px); }
  .dp-pg-card.dp-pg-new::before {
    content: 'NEU'; position: absolute; top: 7px; right: 7px;
    background: var(--dp-pg-red); color: #fff;
    font-family: 'Outfit', sans-serif; font-weight: 700;
    font-size: 0.5625rem; letter-spacing: 0.1em; padding: 2px 6px;
    border-radius: 3px; z-index: 2;
  }
  .dp-pg-card-img {
    background: var(--dp-pg-mid); aspect-ratio: 1;
    display: flex; align-items: center; justify-content: center; padding: 10px;
  }
  .dp-pg-card-img img { width: 100%; height: 100%; object-fit: contain; }
  .dp-pg-card-label {
    padding: 7px 8px; font-size: 0.8125rem; font-weight: 500;
    color: var(--dp-pg-gray); text-align: center; border-top: 1px solid var(--dp-pg-border);
  }

  .dp-pg-symbols { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem; margin-top: 1rem; }
  .dp-pg-symbol-group h3 {
    font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 0.75rem;
    color: var(--dp-pg-gray2); text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 0.625rem;
  }
  .dp-pg-symbol-group p { font-size: 1.0625rem; color: var(--dp-pg-white); letter-spacing: 0.14em; line-height: 2; }

  .dp-pg-tutorial { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; align-items: start; margin-top: 0.75rem; }
  .dp-pg-steps { display: flex; flex-direction: column; gap: 1.125rem; }
  .dp-pg-step { display: flex; gap: 0.875rem; align-items: flex-start; }
  .dp-pg-step-num {
    flex-shrink: 0; width: 26px; height: 26px; border-radius: 50%;
    background: var(--dp-pg-red-dim); border: 1px solid var(--dp-pg-red-bdr);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 0.75rem;
    color: var(--dp-pg-red); margin-top: 3px;
  }
  .dp-pg-step p { font-size: 0.9rem; color: var(--dp-pg-gray); line-height: 1.6; }
  .dp-pg-tutorial-img { width: 100%; border-radius: 8px; border: 1px solid var(--dp-pg-border); }

  .dp-pg-disable-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 7px; margin-top: 1rem;
  }
  .dp-pg-disable-item {
    font-size: 0.875rem; color: var(--dp-pg-gray); padding: 7px 12px;
    background: var(--dp-pg-bg2); border: 1px solid var(--dp-pg-border);
    border-radius: 6px; display: flex; align-items: center; gap: 8px;
  }
  .dp-pg-disable-item::before {
    content: ''; width: 5px; height: 5px; border-radius: 50%;
    background: var(--dp-pg-gray2); flex-shrink: 0;
  }

  .dp-pg-cta {
    margin: 4rem 0 2rem; background: var(--dp-pg-bg2);
    border: 1px solid var(--dp-pg-red-bdr); border-radius: 12px;
    padding: 3rem 2rem; text-align: center;
  }
  .dp-pg-cta h2 {
    font-family: 'Outfit', sans-serif; font-weight: 800;
    font-size: 1.75rem; letter-spacing: -1.5px; margin-bottom: 0.75rem;
  }
  .dp-pg-cta p { color: var(--dp-pg-gray); font-size: 0.9375rem; margin-bottom: 1.75rem; }

  [id].dp-pg-section { scroll-margin-top: 80px; }
  .dp-pg-toc-section { scroll-margin-top: 80px; }

  @media (max-width: 768px) {
    .dp-pg-grid { grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; }
    .dp-pg-tutorial { grid-template-columns: 1fr; }
    .dp-pg-symbols { grid-template-columns: 1fr 1fr; }
    .dp-pg-hero { padding: 3rem 1.25rem 2.5rem; }
    .dp-pg-hero-img { width: 100%; }
    .dp-pg-toc-grid { grid-template-columns: 1fr 1fr; }
  }
  @media (max-width: 480px) {
    .dp-pg-toc-grid { grid-template-columns: 1fr; }
    .dp-pg-symbols { grid-template-columns: 1fr; }
    .dp-pg-disable-grid { grid-template-columns: 1fr 1fr; }
  }
</style>
"""

WRAPPER_OPEN = '\n<div class="dp-pg-wrapper">\n\n'

HERO = """  <!-- ══════════════════ HERO ══════════════════ -->
  <section class="dp-pg-hero">
    <span class="dp-pg-eyebrow">Cute Flexi Maker · v2.1</span>
    <h1>Teile-<em>Übersicht</em></h1>
    <p class="dp-pg-hero-sub">
      Alle verfügbaren Teile für deinen individuellen Flexi. Starte mit einem Basistier
      und gestalte Kopf, Augen, Ohren, Beine, Schwanz und Accessoires ganz nach deinen Wünschen.
    </p>
    <div class="dp-pg-hero-actions">
      <a href="#dp-pg-toc" class="dp-pg-btn dp-pg-btn-primary">Übersicht durchsuchen</a>
      <a href="{{ dp_pg_pdf_url }}" class="dp-pg-btn dp-pg-btn-outline" download>↓ PDF herunterladen</a>
    </div>
    <img
      src="{{ dp_pg_site_base }}/images/hero.png"
      alt="Cute Flexi Maker Flexi-Figuren Übersicht"
      class="dp-pg-hero-img"
      width="1573" height="580"
      loading="eager"
    >
  </section>

"""

TOC_OPEN = """  <!-- ══════════════════ TOC ══════════════════ -->
  <section class="dp-pg-toc-section" id="dp-pg-toc">
    <div class="dp-pg-container">
      <div class="dp-pg-section-label">Inhaltsverzeichnis</div>
      <div class="dp-pg-toc-grid">
"""
TOC_CLOSE = """
      </div>
    </div>
  </section>

"""

SYMBOLS_BLOCK = """  <!-- ══════════════════ 15 SYMBOLE ══════════════════ -->
  <section class="dp-pg-section" id="dp-pg-symbols">
    <div class="dp-pg-container">
      <div class="dp-pg-section-label">Kategorie 15</div>
      <div class="dp-pg-section-head"><h2>Symbole</h2></div>
      <p class="dp-pg-section-desc">Buchstaben, Zahlen und Sonderzeichen für individuelle Beschriftungen.</p>
      <div class="dp-pg-symbols">
        <div class="dp-pg-symbol-group">
          <h3>Buchstaben</h3>
          <p>A B C D E F G H I J K L M N O P Q R S T U V W X Y Z<br>Ä Å Æ Ñ Ö Ø Ü</p>
        </div>
        <div class="dp-pg-symbol-group">
          <h3>Zahlen</h3>
          <p>0 1 2 3 4 5 6 7 8 9</p>
        </div>
        <div class="dp-pg-symbol-group">
          <h3>Sonderzeichen</h3>
          <p>&amp; @ ! + ? -</p>
        </div>
      </div>
    </div>
  </section>
"""

COLORS_BLOCK = """  <!-- ══════════════════ 18 FARBEN ÄNDERN ══════════════════ -->
  <section class="dp-pg-section" id="dp-pg-colors">
    <div class="dp-pg-container">
      <div class="dp-pg-section-label">Kategorie 18</div>
      <div class="dp-pg-section-head"><h2>Farben ändern</h2></div>
      <p class="dp-pg-section-desc">Cute Flexi Maker lässt dich die Farbe jedes Elements anpassen — so sieht deine Kreation genau so aus, wie du es dir vorstellst.</p>
      <div class="dp-pg-tutorial">
        <div class="dp-pg-steps">
          <div class="dp-pg-step"><div class="dp-pg-step-num">1</div><p>Die Hautfarbe ändert die Grundfarbe für den gesamten Flexi.</p></div>
          <div class="dp-pg-step"><div class="dp-pg-step-num">2</div><p>Um das Farbmenü zu öffnen, klicke auf den farbigen Kreis rechts neben dem Kategorienamen.</p></div>
          <div class="dp-pg-step"><div class="dp-pg-step-num">3</div><p>Bei Elementen mit mehreren Komponenten klicke auf den Dropdown-Pfeil, um alle Unterkomponenten zu sehen.</p></div>
          <div class="dp-pg-step"><div class="dp-pg-step-num">4</div><p>Du siehst nicht die perfekte Farbe? Klicke auf das Plus und wähle eine eigene Farbe!</p></div>
        </div>
        <img
          src="{{ dp_pg_site_base }}/images/page-08.png"
          alt="Farb-Picker Screenshot"
          class="dp-pg-tutorial-img"
          width="1632" height="2112"
          loading="lazy"
        >
      </div>
    </div>
  </section>
"""

DISABLE_BLOCK = """  <!-- ══════════════════ 19 TEILE DEAKTIVIEREN ══════════════════ -->
  <section class="dp-pg-section" id="dp-pg-disable">
    <div class="dp-pg-container">
      <div class="dp-pg-section-label">Kategorie 19</div>
      <div class="dp-pg-section-head"><h2>Teile deaktivieren</h2></div>
      <p class="dp-pg-section-desc">Bestimmte Elemente können deaktiviert werden, um die kleinsten Details zu verfeinern. Wenn eine Komponente deaktiviert werden kann, erscheint ein Schalter im Farbmenü.</p>
      <div class="dp-pg-disable-grid">
        <div class="dp-pg-disable-item">Apfelblatt (Apfel)</div>
        <div class="dp-pg-disable-item">Schnabelwachshaut (Papagei)</div>
        <div class="dp-pg-disable-item">Hasenohren Haarband</div>
        <div class="dp-pg-disable-item">Katzenohren innen</div>
        <div class="dp-pg-disable-item">Ei Punkte</div>
        <div class="dp-pg-disable-item">Ei Streifen</div>
        <div class="dp-pg-disable-item">Elefantenohren innen</div>
        <div class="dp-pg-disable-item">Augenglanz (Langes Auge)</div>
        <div class="dp-pg-disable-item">Blumenmitte</div>
        <div class="dp-pg-disable-item">Blumenblätter</div>
        <div class="dp-pg-disable-item">Hutkrempe (Cowboy)</div>
        <div class="dp-pg-disable-item">Hutkrempe (Detektiv)</div>
        <div class="dp-pg-disable-item">Hutstern (Cowboy)</div>
        <div class="dp-pg-disable-item">Mausohren innen</div>
        <div class="dp-pg-disable-item">Raptor-Krallen</div>
        <div class="dp-pg-disable-item">Stacheln (Dinoschwanz)</div>
        <div class="dp-pg-disable-item">Erdbeerblätter</div>
        <div class="dp-pg-disable-item">Erdbeerkerne</div>
        <div class="dp-pg-disable-item">T-Rex Zähne</div>
        <div class="dp-pg-disable-item">Flügelkrallen (Drachenflügel)</div>
      </div>
    </div>
  </section>
"""

CTA_BLOCK = """  <!-- ══════════════════ CTA ══════════════════ -->
  <div class="dp-pg-container">
    <div class="dp-pg-cta">
      <h2>Druckfertige Version herunterladen</h2>
      <p>Alle Teile auf 21 Seiten — jederzeit griffbereit, auch offline.</p>
      <a href="{{ dp_pg_pdf_url }}" class="dp-pg-btn dp-pg-btn-primary" style="font-size:1rem;padding:12px 28px" download>
        ↓ PDF herunterladen (21 Seiten)
      </a>
    </div>
  </div>
"""

WRAPPER_CLOSE = "\n</div><!-- /.dp-pg-wrapper -->\n"

if __name__ == "__main__":
    build()
