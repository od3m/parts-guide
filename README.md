# Cute Flexi Maker — Parts Guide (HTML edition)

Static HTML version of the **Cute Flexi Maker Parts Guide**. The current catalog is based on version **2.1** of the original Parts Guide and is designed for GitHub Pages as well as Shopify.

## Current status

- `index.html` contains the v2.1 catalog with the newer animals, heads, ears, hats, wings, flexi tails, legs, accessories and details.
- All v2.1 part images are mirrored locally below `images/parts/`; GitHub Pages no longer depends on the original image host.
- `index.html`, `page.parts-guide.liquid` and `generate_parts_guide.py` use the same curated v2.1 catalog, including the new animals, Flexi parts and accessories.
- `page.parts-guide.liquid` is the Shopify template version. Upload it as `templates/page.part-guide.liquid` and preview it in an unpublished theme before publishing.

## Source

- **Original Canva design:** https://www.canva.com/design/DAHJlJ4ogjQ/CtqKAKkoXrEFH0-BXr3lww/edit
- **PDF export v2.1:** [`parts-guide-v2.1.pdf`](parts-guide-v2.1.pdf) (21 pages, in this repo)

## Live preview

After deploying to GitHub Pages, the site will be reachable at:

```
https://<your-username>.github.io/<repo-name>/
```

## Project structure

```
cfm-parts-guide/
├── index.html                      # single-page HTML site
├── css/
│   └── styles.css                  # design tokens, layout, components, responsive
├── js/
│   └── main.js                     # active-nav highlight, back-to-top, image zoom
├── images/
│   ├── hero.png                    # cover band cropped from page 1
│   ├── cover-og.jpg                # OpenGraph preview image
│   ├── page-01.png … page-08.png   # high-res exports, one per page
│   └── parts/
│       ├── manifest.json           # machine-readable index of all parts
│       ├── base-animals/*.png      # 13 individual base animals (transparent)
│       ├── heads/*.png             # 10 individual heads
│       ├── eyes/*.png              # 11 eye styles
│       ├── ears/*.png              # 4 ear styles
│       ├── hats/*.png              # 2 hats
│       ├── body-segments/*.png     # 4 body segments
│       ├── bottom-segments/*.png   # 5 bottom segments
│       ├── flexi-legs/*.png        # 3 wings
│       ├── flexi-tails/*.png       # 3 flex tails
│       ├── legs/*.png              # 12 legs
│       ├── tails/*.png             # 8 tails
│       ├── accessories/*.png       # 17 accessories
│       └── symbols/*.png           # 1 alphabet preview
├── parts-guide.pdf                 # full PDF (8 pages, letter, "pro" quality)
├── raw-extracted/                  # 209 raw images from pdfimages (kept for debugging; can be deleted)
├── scripts/
│   ├── detect_cards.py             # exploratory; not used at runtime
│   └── extract_parts.py            # merges (RGB, alpha) pairs into named transparent PNGs
└── README.md
```

## What was rebuilt

- **HTML/CSS chrome** — sticky header, hero, table of contents, sections, CTA, footer, back-to-top button, zoom-on-click for figures — all hand-written semantic HTML.
- **Sections 1–16 (pages 2–9)** are real CSS grids of individual `<img>` cards. Each catalog part is its own transparent PNG, extracted from the PDF/source and renamed by part (`images/parts/<section>/<slug>.png`).
- **Symbols** section is a hybrid: the dice preview image plus the full A–Z, 0–9 and `& @ ! + ?` character set as real HTML text so it's selectable and searchable.
- **Details & Horns (page 7)** uses the original page composite. The PDF only has 11 unique rasters there because details (eyelids, cheeks, eyelashes, etc.) overlay on a shared base body — reconstructing each combo would need vector layout data we don't have.
- **Changing Colors / Disable Parts (page 8)** is fully rebuilt as HTML (numbered steps + two-column disable list) so text is selectable and searchable.

## How the part images were extracted

```sh
# 1. dump every raster image from the PDF
pdfimages -png -p parts-guide.pdf raw-extracted/img

# 2. merge each (color, alpha-mask) pair, crop and rename per the named order
python3 scripts/extract_parts.py
```

The script keeps a `manifest.json` you can use to drive further work — for example, swapping label rendering, adding tags, or generating filter UI.

## Local image assets

The v2.1 image set is already mirrored and used by both the static HTML and the generated Liquid template. To verify that every catalog entry has a local file:

```sh
python3 generate_parts_guide.py
```

The generator prints a drift report and writes `page.parts-guide.liquid`. Run `python3 -m http.server 8000` locally to check the browser for missing images.

## Deploying to GitHub Pages

1. Push the repository branch containing the updated `index.html`.
2. In **Settings → Pages**, set source to "Deploy from a branch" → the selected branch, folder `/ (root)`.
3. Wait a minute, then visit the URL shown on that page.

Custom domain? Add a `CNAME` file with your domain and configure DNS as per GitHub's docs.

## Shopify installation

The Shopify page `/pages/parts-guide` uses the template suffix `part-guide`. The matching file is therefore:

```text
templates/page.part-guide.liquid
```

Upload the Liquid file to a new unpublished theme, open that theme's preview, and test `/pages/parts-guide` there. The normal live-shop URL continues to render the published theme. Publish the test theme only after the preview is correct.

## Local preview

Any static server will do. From this folder:

```sh
python3 -m http.server 8000
# then open http://localhost:8000
```

## Performance notes

- All page images are PNG at ~2x letter size; total weight is ~12 MB. If you need a leaner load, run them through `pngquant` / `oxipng` or convert to WebP — a one-line shell loop will do.
- The PDF download is ~30 MB. Consider compressing with `gs` (Ghostscript) if size matters.

## License / credits

The original artwork, design and "Cute Flexi Maker" concept belong to their respective owners. This repository only contains the HTML/CSS wrapper and the exported page art that the design owner shared via Canva.
