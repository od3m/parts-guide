from pathlib import Path
from io import BytesIO
from urllib.request import Request, urlopen
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

OUT = Path(__file__).resolve().parents[1] / "output" / "pdf" / "parts-guide-v2.1.pdf"
CACHE = Path(__file__).resolve().parents[1] / "tmp" / "pdf-images"
CACHE.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)

BASE = "https://www.printfarm.tools/cfm-parts-guide/parts/"
RELEASE = "https://www.printfarm.tools/cfm-parts-guide/releases/2026-08-03/parts/"
RELEASE_NAMES = {"axolotl", "narwal", "chibi", "party-hat", "sailor-hat", "traffic-cone", "pointed", "tiny-toes", "wavy-fin", "axolotl-gills", "spots", "tongue", "police-hat"}

DATA = [
    ("Basistiere", "base-animals", ["axolotl", "bee", "boar", "bulldog", "cat", "caterpillar", "dolphin", "dragon", "duck", "eagle", "elephant", "french-bulldog", "mouse", "narwal", "parrot", "pig", "pug", "snail", "t-rex"]),
    ("Köpfe", "heads", ["base", "bee", "bulldog", "chibi", "dolphin", "dragon", "duck", "elephant", "parrot", "pig", "round", "snail", "t-rex"]),
    ("Augen", "eyes", ["base", "big", "black", "color", "cute", "heart", "long", "reptile", "sleep", "smiley", "x"]),
    ("Ohren", "ears", ["big", "cat", "elephant", "folded", "mouse", "pig"]),
    ("Hüte", "hats", ["cowboy-hat", "crown", "detective-hat", "party-hat", "police-hat", "sailor-hat", "traffic-cone"]),
    ("Körpersegmente", "body-segments", ["base", "base-small", "flex", "fur"]),
    ("Untersegmente", "bottom-segments", ["bee", "flex", "mini-flex", "round", "snail"]),
    ("Flexi-Beine", "flexi-legs", ["angel", "bird", "dragon"]),
    ("Wings", "wings", ["angel-wings", "double", "feathers", "love-feathers", "standard"]),
    ("Flexi-Schwänze", "flexi-tails", ["dino", "dolphin", "dragon", "feathered", "pointed"]),
    ("Beine", "legs", ["bee", "bird-legs", "bird-wings", "caterpillar", "cute", "dino", "fins", "dragon", "duck", "elephant", "generic", "pig", "raptor", "small", "sploot", "tiny-toes"]),
    ("Schwänze", "tails", ["bird", "cat", "curly", "dino", "duck", "mouse", "round", "sting", "tufted"]),
    ("Top-Accessoires", "accessories", ["apple", "bird", "bow", "clover", "crest", "dragon-spikes", "egg", "fin", "flower", "heart", "lifebuoy", "paw", "shell", "spike", "spines", "sprout", "star", "strawberry", "wavy-fin"]),
    ("Side-Accessoires", "side-accessories", ["axolotl-gills", "dragon-spikes"]),
    ("Details", "details", ["angry-eyelids", "blaze", "cheeks", "eyebrows", "eyelashes", "furry-cheeks", "moustache", "piercing", "pois", "spots", "stripes", "tongue", "x-butt-mark"]),
    ("Hörner", "horns", ["antennae", "dragon", "reindeer", "spiky", "tusk", "unicorn"]),
]

NEW = {"axolotl", "narwal", "bulldog", "dolphin", "french-bulldog", "pug", "chibi", "big", "folded", "party-hat", "police-hat", "sailor-hat", "traffic-cone", "angel-wings", "double", "feathers", "love-feathers", "standard", "pointed", "bird-legs", "bird-wings", "fins", "sploot", "tiny-toes", "curly", "fin", "lifebuoy", "wavy-fin", "axolotl-gills", "blaze", "eyebrows", "piercing", "spots", "tongue", "x-butt-mark"}

def label(slug):
    return slug.replace(".locked", "").replace("-", " ").title()

def image_url(folder, slug):
    file_slug = "police-hat.locked" if slug == "police-hat" else slug
    root = RELEASE if slug in RELEASE_NAMES else BASE
    return f"{root}{folder}/{file_slug}.png"

def fetch_image(folder, slug):
    key = f"{folder}__{slug}.png"
    path = CACHE / key
    if not path.exists():
        try:
            req = Request(image_url(folder, slug), headers={"User-Agent": "druckpunkt-parts-guide/2.1"})
            path.write_bytes(urlopen(req, timeout=20).read())
        except Exception:
            return None
    return path

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#77788a"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 10 * mm, "druckpunkt. · Cute Flexi Maker Parts Guide v2.1")
    canvas.drawRightString(192 * mm, 10 * mm, f"Seite {doc.page}")
    canvas.restoreState()

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=31, leading=36, textColor=colors.white, spaceAfter=12))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontSize=13, leading=19, textColor=colors.HexColor("#d9d9e5")))
styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=22, leading=27, textColor=colors.HexColor("#1a1a2e"), spaceAfter=5))
styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=8.5, leading=11, alignment=1, textColor=colors.HexColor("#303047")))
styles.add(ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=10, leading=14, textColor=colors.HexColor("#3d3d4f")))

doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=14 * mm, leftMargin=14 * mm, topMargin=14 * mm, bottomMargin=16 * mm, title="Cute Flexi Maker Parts Guide v2.1")
story = []

cover = Table([[Paragraph("druckpunkt.", styles["CoverSub"])], [Spacer(1, 18 * mm)], [Paragraph("Cute Flexi Maker<br/>Parts Guide", styles["CoverTitle"])], [Paragraph("Vollständiger Teilekatalog · Version 2.1", styles["CoverSub"])], [Spacer(1, 10 * mm)], [Paragraph("Basistiere, Köpfe, Augen, Ohren, Hüte, Wings, Flexi-Teile, Beine, Schwänze, Accessoires, Details, Hörner und Symbole.", styles["CoverSub"])]] , colWidths=[170 * mm])
cover.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1a1a2e")), ("BOX", (0, 0), (-1, -1), 0, colors.HexColor("#1a1a2e")), ("LEFTPADDING", (0, 0), (-1, -1), 18 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 18 * mm), ("TOPPADDING", (0, 0), (-1, -1), 18 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 22 * mm)]))
story += [Spacer(1, 22 * mm), cover, PageBreak()]

story += [Paragraph("Inhalt", styles["SectionTitle"]), Paragraph("Alle in der aktuellen v2.1-Ausgabe enthaltenen Teile. Neue bzw. ergänzte Teile sind mit <b>NEU</b> markiert.", styles["Body"]), Spacer(1, 6 * mm)]
toc = [[f"{i:02d}", title, f"{len(slugs)} Teile"] for i, (title, _, slugs) in enumerate(DATA, 1)]
table = Table(toc, colWidths=[15 * mm, 115 * mm, 35 * mm])
table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f0f5")), ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#d4d4e0")), ("FONTNAME", (0, 0), (-1, -1), "Helvetica"), ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("ALIGN", (0, 0), (0, -1), "CENTER"), ("ALIGN", (-1, 0), (-1, -1), "RIGHT"), ("FONTSIZE", (0, 0), (-1, -1), 9), ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f7f7fa")])]))
story += [table, PageBreak()]

for title, folder, slugs in DATA:
    story += [Paragraph(title, styles["SectionTitle"]), Paragraph(f"{len(slugs)} Teile · Neue Ergänzungen sind mit NEU gekennzeichnet.", styles["Body"]), Spacer(1, 5 * mm)]
    rows = []
    for start in range(0, len(slugs), 5):
        row = []
        for slug in slugs[start:start + 5]:
            img_path = fetch_image(folder, slug)
            if img_path:
                img = Image(str(img_path), width=31 * mm, height=31 * mm, kind="proportional")
            else:
                img = Paragraph("Bild nicht verfügbar", styles["Small"])
            mark = " · NEU" if slug in NEW else ""
            row.append([img, Paragraph(f"{label(slug)}{mark}", styles["Small"])])
        while len(row) < 5:
            row.append("")
        rows.append(row)
    grid = Table(rows, colWidths=[35 * mm] * 5, rowHeights=[41 * mm] * len(rows))
    grid.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f0f7")), ("BOX", (0, 0), (-1, -1), .4, colors.HexColor("#d5d5e2")), ("INNERGRID", (0, 0), (-1, -1), .4, colors.HexColor("#d5d5e2")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm), ("TOPPADDING", (0, 0), (-1, -1), 2 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm)]))
    story += [grid, PageBreak()]

story += [Paragraph("Symbole", styles["SectionTitle"]), Paragraph("Buchstaben", styles["Heading2"]), Paragraph("A B C D E F G H I J K L M N O P Q R S T U V W X Y Z", styles["Body"]), Paragraph("Ä Å Æ Ñ Ö Ø Ü", styles["Body"]), Spacer(1, 4 * mm), Paragraph("Zahlen", styles["Heading2"]), Paragraph("0 1 2 3 4 5 6 7 8 9", styles["Body"]), Spacer(1, 4 * mm), Paragraph("Sonderzeichen", styles["Heading2"]), Paragraph("&amp; @ ! + ? -", styles["Body"]), PageBreak()]
story += [Paragraph("Farben ändern", styles["SectionTitle"]), Paragraph("Die Hautfarbe ändert die Grundfarbe des gesamten Flexis. Über den farbigen Kreis öffnest du die Farbauswahl; Unterkomponenten lassen sich über den Pfeil einblenden.", styles["Body"]), Spacer(1, 8 * mm), Paragraph("Teile deaktivieren", styles["SectionTitle"]), Paragraph("Einige Komponenten können im Farbmenü deaktiviert werden, darunter T-Rex-Zähne, Apfelblatt, Blütenblätter, Hutdetails, Drachenzähne und weitere Unterteile.", styles["Body"]), Spacer(1, 12 * mm), Paragraph("Referenz: printfarm.tools/cfm-parts-guide", styles["Small"])]

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
