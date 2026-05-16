"""
Extract individual "Details" and "Horns" part cards from the Canva PNG
exports in scripts/_canva/.

The PDF-based pipeline in extract_parts.py uses `pdfimages` to pull each
part out as its own pre-isolated raster + alpha mask. The pages for details
and horns are composite rasters in the PDF, so `pdfimages` returns one big
blob instead of per-card images — we have to detect cards from the page
ourselves.

Captions ("ANGRY EYELIDS", "MOUSTACHE", …) now live *below* each card, the
same way page 6 / accessories does it. That means we don't have to repaint
anything inside the card — just crop the rounded rectangle and key the
surrounding page white to transparent.

Approach (pure-PIL — numpy isn't available in this env):
  1. Build a "non-white" mask from the page.
  2. Histogram non-white pixels per row → split into card rows. Caption
     text rows are short and drop out via the min-height filter.
  3. Within each card row, histogram per column → individual card x-spans.
  4. Crop each card with a small margin, then flood-fill the surrounding
     page white to transparency so the rounded corners come through.

Run from project root:
    python3 scripts/extract_page7_from_canva.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
CANVA_DIR = ROOT / "scripts" / "_canva"
PARTS_DIR = ROOT / "images" / "parts"


# Each source page maps to a section and a top-to-bottom, left-to-right
# list of part names. Rows are inferred from the layout — the only thing
# we hard-code is the *order* within each row.
PAGES: list[tuple[Path, str, list[list[str]]]] = [
    (
        CANVA_DIR / "page-07-hires.png",
        "details",
        [
            ["angry-eyelids", "cheeks", "scales-top", "scales-side", "eyelashes"],
            ["furry-cheeks", "moustache", "pois", "stripes"],
        ],
    ),
    (
        CANVA_DIR / "page-08-hires.png",
        "horns",
        [
            ["antennae", "dragon", "tusk", "reindeer", "spiky"],
            ["unicorn"],
        ],
    ),
]


# ---------- mask construction ------------------------------------------------

def _non_white(r: int, g: int, b: int) -> int:
    return 1 if (r < 240 or g < 240 or b < 240) else 0


def build_mask(img: Image.Image) -> Image.Image:
    rgb = img.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    mask = Image.new("1", (w, h), 0)
    mpx = mask.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if _non_white(r, g, b):
                mpx[x, y] = 1
    return mask


# ---------- row/column histograms -------------------------------------------

def _row_counts(mask: Image.Image) -> list[int]:
    w, h = mask.size
    mpx = mask.load()
    counts = [0] * h
    for y in range(h):
        c = 0
        for x in range(w):
            c += mpx[x, y]
        counts[y] = c
    return counts


def _col_counts_in_band(mask: Image.Image, y0: int, y1: int) -> list[int]:
    w, _ = mask.size
    mpx = mask.load()
    counts = [0] * w
    for x in range(w):
        c = 0
        for y in range(y0, y1):
            c += mpx[x, y]
        counts[x] = c
    return counts


def _runs(values: list[int], threshold: int, min_len: int) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    i, n = 0, len(values)
    while i < n:
        if values[i] >= threshold:
            j = i
            while j < n and values[j] >= threshold:
                j += 1
            if j - i >= min_len:
                runs.append((i, j))
            i = j
        else:
            i += 1
    return runs


def find_card_rows(mask: Image.Image) -> list[tuple[int, int]]:
    """Card-only rows. Caption text rows are short and get filtered out below."""
    w, _ = mask.size
    counts = _row_counts(mask)
    # Card rows cover ≥12% of page width; tall enough text headers can sneak in.
    thr = int(w * 0.12)
    return _runs(counts, threshold=thr, min_len=80)


def find_cards_in_row(mask: Image.Image, y0: int, y1: int) -> list[tuple[int, int]]:
    counts = _col_counts_in_band(mask, y0, y1)
    band_h = y1 - y0
    thr = max(int(band_h * 0.20), 8)
    return _runs(counts, threshold=thr, min_len=30)


# ---------- background keying -----------------------------------------------

def _looks_like_strict_bg(r: int, g: int, b: int) -> bool:
    """Pixels we can safely flood-fill *anywhere* in the crop — including
    alongside the card body — without risking eating into figure shading.

    Just page white. The Canva render is essentially anti-alias-free between
    page white and the card body (white → r=222 cool body in one step), so
    we don't need a cool-AA rule. Adding one bites into the lower-right of
    the card body where its natural gradient brightens to ~r=234, leaving a
    "brushed" band visible on angry-eyelids, cheeks, eyelashes, etc.
    """
    return r >= 248 and g >= 248 and b >= 248


def _looks_like_shadow_bg(r: int, g: int, b: int) -> bool:
    """Pixels we flood-fill in addition to page white — the soft drop shadow
    that the source draws under and alongside each card.

    Restricted to *neutral* grey (``abs(r-g) ≤ 3, abs(g-b) ≤ 3``). The old
    rule also caught faintly cool pixels (``b - r ≤ 10``), but those pixels
    are mostly the rounded-card-edge AA — alpha-keying them turns the
    cool-tinted edge into low-alpha black, which on a dark page background
    looks like blue/grey streaks *inside* the light card. Leaving the
    cool-tinted AA opaque keeps the edge looking clean on any background;
    the neutral grey side-shadow still gets keyed out because it has
    r ≈ g ≈ b on the page.
    """
    return r >= 190 and r < 248 and abs(r - g) <= 3 and abs(g - b) <= 3


def _looks_like_bg(r: int, g: int, b: int) -> bool:
    """Anything outside the card body — page white plus the drop-shadow.

    Shadow rules apply *anywhere* in the crop now (not just below
    body_bottom): adjacent cards on the page cast grey shadow to the
    left/right of the current card that would otherwise survive as a
    visible grey band alongside the body. The shadow rules require
    `abs(r-g) ≤ 3`, so the cool-tinted card body (g - r ≥ 3) and any
    figure shading on top of it can't match — flood-fill can't tunnel
    through the card body into the figure.
    """
    if _looks_like_strict_bg(r, g, b):
        return True
    if _looks_like_shadow_bg(r, g, b):
        return True
    return False


def _bg_to_rgba(r: int, g: int, b: int) -> tuple[int, int, int, int]:
    """Turn a bg pixel composited on white into a (0, 0, 0, α) shadow pixel.

    Using a pure-black foreground keeps the saved PNG looking right on *any*
    background. Solving algebraically for the true premultiplied foreground
    of a low-alpha cool-tinted edge pixel (e.g., (240, 245, 250)) gives a
    surprising raw RGB like (0, 85, 170): mathematically correct when
    re-composited on white, but rendered on a dark backdrop (e.g., the
    site's zoom modal) the cool tint becomes a visible blue/grey streak
    *inside* the rounded card edge. ``α = 255 − min(r, g, b)`` keeps the
    edge fully covered (no holes through the body) and matches the way
    apple.png / spike.png store their drop shadow.
    """
    return (0, 0, 0, 0)


def key_card_bg_to_transparent(img: Image.Image) -> Image.Image:
    """Flood-fill the background in from the crop border so the card's rounded
    corners and drop shadow get alpha-graded transparency."""
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    visited = [[False] * w for _ in range(h)]

    stack: list[tuple[int, int]] = []
    for x in range(w):
        for y in (0, h - 1):
            r, g, b, _ = px[x, y]
            if _looks_like_bg(r, g, b):
                stack.append((x, y))
                visited[y][x] = True
    for y in range(h):
        for x in (0, w - 1):
            r, g, b, _ = px[x, y]
            if _looks_like_bg(r, g, b):
                stack.append((x, y))
                visited[y][x] = True

    while stack:
        x, y = stack.pop()
        r, g, b, _ = px[x, y]
        px[x, y] = _bg_to_rgba(r, g, b)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if nx < 0 or ny < 0 or nx >= w or ny >= h:
                continue
            if visited[ny][nx]:
                continue
            rr, gg, bb, _ = px[nx, ny]
            if _looks_like_bg(rr, gg, bb):
                visited[ny][nx] = True
                stack.append((nx, ny))
    return rgba


# ---------- crop & save ------------------------------------------------------

# Outside the detected mask span so flood-fill has page-white pixels to
# start from. The mask detection hugs the card silhouette tightly.
SIDE_MARGIN_PX = 8
TOP_MARGIN_PX = 8
# Below the card-body bottom to include the rounded-edge AA *and* the full
# soft drop shadow the source draws below each card. The shadow gets
# converted into alpha-graded transparency (see _bg_to_rgba) so the cards
# match the floating-on-paper look of the accessories. 45 sits just under
# the 48-px minimum gap between card_body_bottom and caption text across
# all rows, so the caption never gets pulled in; smaller values chop the
# shadow off before alpha fades to ~0 and the hard edge reads as a
# second card outline below the figure.
BOTTOM_EDGE_PAD_PX = 45


def _is_card_body(r: int, g: int, b: int) -> bool:
    """Card body = cool-tinted rounded rectangle behind the figure."""
    return r >= 210 and g >= 218 and b >= 230 and b - r >= 8 and g - r >= 3


def find_card_body_bottom(page: Image.Image, y0: int, y1: int, x0: int, x1: int) -> int:
    """Highest y at which the card body still appears anywhere across [x0, x1].

    Probing a single column under-reports the bottom in two different ways:
    near the card's left/right edge the rounded corner curves up and we stop
    too high; at the center the figure occupies the middle of the card and
    breaks the streak even higher. So we scan from the bottom upward and
    return the first y that has *any* card-body pixel — that's the card's
    rounded bottom edge at its lowest point.
    """
    px = page.load()
    for y in range(y1 - 1, y0 - 1, -1):
        for x in range(x0, x1, 4):
            r, g, b = px[x, y]
            if _is_card_body(r, g, b):
                return y
    return y0


def crop_card(page: Image.Image, x0: int, x1: int, y0: int,
              card_bottom_y: int,
              prev_x1: int | None = None,
              next_x0: int | None = None) -> Image.Image:
    # Side margins normally sit at SIDE_MARGIN_PX, but adjacent cards on the
    # row are only ~5 px apart, so an 8-px margin would pull the next card's
    # body in. Cap each side at the midpoint of the gap to the neighbour.
    if prev_x1 is None:
        left = max(0, x0 - SIDE_MARGIN_PX)
    else:
        left = max(prev_x1 + (x0 - prev_x1) // 2, x0 - SIDE_MARGIN_PX)
    if next_x0 is None:
        right = min(page.width, x1 + SIDE_MARGIN_PX)
    else:
        right = min(x1 + (next_x0 - x1) // 2, x1 + SIDE_MARGIN_PX)
    top = max(0, y0 - TOP_MARGIN_PX)
    # Going `card_bottom_y + 45` is just under the 48-px gap to the caption
    # text below each card across all rows, so the caption never enters the
    # crop and the alpha-graded shadow fades to near-zero before being cut.
    bottom = min(page.height, card_bottom_y + BOTTOM_EDGE_PAD_PX)
    return page.crop((left, top, right, bottom))


def save_part(img: Image.Image, dest: Path, max_size: int = 600) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    out = img
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    out.thumbnail((max_size, max_size), Image.LANCZOS)
    out.save(dest, "PNG", optimize=False, compress_level=6)


# ---------- orchestration ----------------------------------------------------

def process_page(source: Path, section: str, row_names: list[list[str]]) -> None:
    if not source.exists():
        print(f"missing {source}", file=sys.stderr)
        return
    print(f"reading {source.relative_to(ROOT)}", file=sys.stderr)
    page = Image.open(source).convert("RGB")
    mask = build_mask(page)
    rows = find_card_rows(mask)
    # Drop caption-text-only rows — they're short relative to a card row.
    real_rows = [r for r in rows if (r[1] - r[0]) > 200]
    print(f"  detected {len(rows)} non-white rows, {len(real_rows)} card rows", file=sys.stderr)

    if len(real_rows) != len(row_names):
        print(
            f"  ! got {len(real_rows)} card rows, expected {len(row_names)}; "
            f"pairing by index anyway",
            file=sys.stderr,
        )

    for names, (y0, y1) in zip(row_names, real_rows):
        spans = find_cards_in_row(mask, y0, y1)
        print(
            f"  row y={y0}..{y1}  detected={len(spans)}  expected={len(names)}",
            file=sys.stderr,
        )
        if not spans:
            continue
        # Card geometry is uniform per row, so scan the first card's full
        # width once and use that as the bottom for every card in the row.
        x0_first, x1_first = spans[0]
        card_bottom_y = find_card_body_bottom(page, y0, y1, x0_first, x1_first)
        print(f"    card_bottom_y={card_bottom_y}", file=sys.stderr)
        for i, (name, (x0, x1)) in enumerate(zip(names, spans)):
            prev_x1 = spans[i - 1][1] if i > 0 else None
            next_x0 = spans[i + 1][0] if i + 1 < len(spans) else None
            cropped = crop_card(page, x0, x1, y0, card_bottom_y,
                                prev_x1=prev_x1, next_x0=next_x0)
            keyed = key_card_bg_to_transparent(cropped)
            dest = PARTS_DIR / section / f"{name}.png"
            save_part(keyed, dest)
            print(f"    ✓ {dest.relative_to(ROOT)}", file=sys.stderr)


def main() -> None:
    for source, section, row_names in PAGES:
        process_page(source, section, row_names)


if __name__ == "__main__":
    main()
