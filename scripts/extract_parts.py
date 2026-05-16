"""
Merge each (RGB, L) pair emitted by `pdfimages -png` into a transparent PNG,
crop tight to the part, and save with a human-readable filename under
images/parts/<section>/<slug>.png. Also writes a JSON manifest the HTML
template can consume.

Run from the project root:

    python3 scripts/extract_parts.py

The raw input lives in raw-extracted/ (img-PPP-NNN.png where NNN odd = RGB,
NNN even = alpha mask).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "raw-extracted"
PARTS_DIR = ROOT / "images" / "parts"
MANIFEST_PATH = ROOT / "images" / "parts" / "manifest.json"


# Defined order on each page — matches reading order in the design.
# Each entry is (section_slug, display_title, [part_names])
PAGE_PARTS: dict[int, list[tuple[str, str, list[str]]]] = {
    2: [
        ("base-animals", "Base Animals",
         ["bee", "boar", "cat", "caterpillar", "duck",
          "dragon", "eagle", "elephant", "mouse", "parrot",
          "pig", "snail", "t-rex"]),
        ("heads", "Heads",
         ["base", "bee", "dragon", "duck", "elephant",
          "parrot", "pig", "round", "snail", "t-rex"]),
    ],
    3: [
        ("eyes", "Eyes",
         ["base", "big", "black", "color", "cute",
          "heart", "long", "reptile", "sleep", "smily", "x"]),
        ("ears", "Ears", ["cat", "elephant", "mouse", "pig"]),
        ("hats", "Hats", ["cowboy", "detective"]),
    ],
    4: [
        ("body-segments", "Body Segments",
         ["base", "base-small", "fur", "flex"]),
        ("bottom-segments", "Bottom Segments",
         ["bee", "flex", "mini-flex", "round", "snail"]),
        ("flexi-legs", "Flexi Legs (Wings)",
         ["angel", "bird", "dragon"]),
        ("flexi-tails", "Flexi Tails",
         ["feathered", "dragon", "dino"]),
    ],
    5: [
        ("legs", "Legs",
         ["bee", "bird", "cat", "caterpillar", "duck",
          "dino", "dragon", "elephant", "generic", "pig",
          "small", "raptor"]),
        ("tails", "Tails",
         ["bird", "cat", "duck", "tuffed", "mouse",
          "pig", "sting", "dino"]),
    ],
    6: [
        ("accessories", "Accessories",
         ["apple", "bird", "bow", "bunny-ears", "clover",
          "crest", "crown", "egg", "flower", "heart",
          "paw", "shell", "spike", "spines", "sprout",
          "star", "strawberry"]),
        ("symbols", "Symbols", ["alphabet"]),
    ],
}


@dataclass
class PartImage:
    """One named, processed part image."""
    section: str
    section_title: str
    name: str
    slug: str
    src: str
    page: int


@dataclass
class SectionManifest:
    slug: str
    title: str
    page: int
    parts: list[PartImage] = field(default_factory=list)


# ---------- pure helpers ----------------------------------------------------

def _page_files(page: int) -> list[Path]:
    """Return sorted list of raw PNGs for a given page (numbering is global)."""
    pattern = f"img-{page:03d}-*.png"
    return sorted(RAW_DIR.glob(pattern), key=lambda p: int(p.stem.split("-")[-1]))


def _pair_paths(page_files: list[Path], index: int) -> tuple[Path, Path]:
    """Return (rgb_path, mask_path) for a 1-based card index using ordered page files."""
    rgb_idx = (index - 1) * 2
    mask_idx = rgb_idx + 1
    return page_files[rgb_idx], page_files[mask_idx]


def _merge_with_alpha(rgb_path: Path, mask_path: Path) -> Image.Image:
    """Combine a color PNG and a single-channel mask into RGBA."""
    rgb = Image.open(rgb_path).convert("RGB")
    mask = Image.open(mask_path).convert("L")
    if mask.size != rgb.size:
        mask = mask.resize(rgb.size)
    rgba = rgb.convert("RGBA")
    rgba.putalpha(mask)
    return rgba


def _crop_to_content(img: Image.Image, padding: int = 8) -> Image.Image:
    """Trim to the bounding box of non-transparent pixels (with a little padding)."""
    bbox = img.getbbox()
    if not bbox:
        return img
    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(img.width, right + padding)
    bottom = min(img.height, bottom + padding)
    return img.crop((left, top, right, bottom))


def _save_optimized(img: Image.Image, dest: Path, max_size: int = 480) -> None:
    """Downsize for the web while keeping transparency, then save."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    img.save(dest, format="PNG", optimize=False, compress_level=6)


# ---------- main pipeline ---------------------------------------------------

def _iter_named_parts() -> Iterable[tuple[int, int, str, str, str]]:
    """Yield (page, raw_index, section_slug, section_title, part_name)."""
    for page, sections in PAGE_PARTS.items():
        raw_index = 1
        for section_slug, section_title, parts in sections:
            for part_name in parts:
                yield page, raw_index, section_slug, section_title, part_name
                raw_index += 1


def extract_all() -> list[SectionManifest]:
    sections_by_key: dict[tuple[int, str], SectionManifest] = {}
    files_by_page: dict[int, list[Path]] = {p: _page_files(p) for p in PAGE_PARTS}

    for page, raw_index, section_slug, section_title, part_name in _iter_named_parts():
        page_files = files_by_page.get(page, [])
        try:
            rgb_path, mask_path = _pair_paths(page_files, raw_index)
        except IndexError:
            print(f"  ! out of range for p{page}#{raw_index} ({part_name}) "
                  f"— only {len(page_files)} files on page")
            continue
        if not rgb_path.exists() or not mask_path.exists():
            print(f"  ! missing pair for p{page}#{raw_index} ({part_name})")
            continue

        slug = part_name.lower().replace(" ", "-").replace("/", "-")
        dest = PARTS_DIR / section_slug / f"{slug}.png"

        if not dest.exists():
            print(f"  ✓ p{page} {section_slug}/{slug}", flush=True)
            merged = _merge_with_alpha(rgb_path, mask_path)
            trimmed = _crop_to_content(merged)
            _save_optimized(trimmed, dest)

        key = (page, section_slug)
        if key not in sections_by_key:
            sections_by_key[key] = SectionManifest(
                slug=section_slug, title=section_title, page=page
            )
        sections_by_key[key].parts.append(
            PartImage(
                section=section_slug,
                section_title=section_title,
                name=part_name,
                slug=slug,
                src=str(dest.relative_to(ROOT)),
                page=page,
            )
        )

    return list(sections_by_key.values())


def write_manifest(sections: list[SectionManifest]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "slug": s.slug,
            "title": s.title,
            "page": s.page,
            "parts": [asdict(p) for p in s.parts],
        }
        for s in sections
    ]
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2))


def main() -> None:
    sections = extract_all()
    write_manifest(sections)

    print(f"\nExtracted {sum(len(s.parts) for s in sections)} part images "
          f"across {len(sections)} sections")
    for s in sections:
        print(f"  · {s.title:25s} ({s.page})  {len(s.parts)} parts")
    print(f"\nManifest → {MANIFEST_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
