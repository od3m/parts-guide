"""
Detect the light-gray rounded part cards on a CFM Parts Guide page export.

The pages have a warm cream background (~#f5ecdc) and the cards are a
much lighter near-white grey (~#ececec). We threshold on those neutral
greys, then find connected components and keep the ones that look like
cards (large, roughly square, similar to each other in size).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from PIL import Image


# --- Tunables -----------------------------------------------------------------

MIN_CARD_AREA_FRACTION = 0.005   # fraction of page area
MAX_CARD_AREA_FRACTION = 0.05
MIN_ASPECT_RATIO = 0.65
MAX_ASPECT_RATIO = 1.6
PAD = 4                          # padding around detected card


@dataclass
class CardBox:
    x: int
    y: int
    w: int
    h: int

    def crop(self, img: Image.Image, pad: int = 0) -> Image.Image:
        left = max(0, self.x - pad)
        top = max(0, self.y - pad)
        right = min(img.width, self.x + self.w + pad)
        bottom = min(img.height, self.y + self.h + pad)
        return img.crop((left, top, right, bottom))


def _build_card_mask(arr: np.ndarray) -> np.ndarray:
    """Return a bool mask of pixels that look like card background (neutral light grey)."""
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    brightness = (r.astype(int) + g.astype(int) + b.astype(int)) // 3

    is_bright = brightness > 220
    is_not_white = brightness < 252               # exclude the very white shadowed edges
    # cream background has noticeably more red than blue; cards are neutral grey
    is_neutral = (r.astype(int) - b.astype(int)) < 6

    return is_bright & is_not_white & is_neutral


def _label_components(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """Simple two-pass connected components (4-connectivity) using union-find."""
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    parents: list[int] = [0]

    def find(x: int) -> int:
        while parents[x] != x:
            parents[x] = parents[parents[x]]
            x = parents[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parents[max(ra, rb)] = min(ra, rb)

    next_label = 1
    for y in range(h):
        row = mask[y]
        prev_label_row = labels[y - 1] if y > 0 else None
        for x in range(w):
            if not row[x]:
                continue
            left = labels[y, x - 1] if x > 0 else 0
            up = prev_label_row[x] if prev_label_row is not None else 0
            if left and up:
                labels[y, x] = min(left, up)
                union(left, up)
            elif left:
                labels[y, x] = left
            elif up:
                labels[y, x] = up
            else:
                labels[y, x] = next_label
                parents.append(next_label)
                next_label += 1

    # Flatten
    flat = np.zeros(next_label, dtype=np.int32)
    for i in range(1, next_label):
        flat[i] = find(i)
    labels = flat[labels]
    return labels, next_label


def _bounding_boxes(labels: np.ndarray) -> dict[int, tuple[int, int, int, int]]:
    """Return label -> (min_x, min_y, max_x, max_y)."""
    boxes: dict[int, list[int]] = {}
    h, w = labels.shape
    nz = labels.nonzero()
    if len(nz[0]) == 0:
        return {}
    for y, x in zip(nz[0].tolist(), nz[1].tolist()):
        lbl = int(labels[y, x])
        if lbl not in boxes:
            boxes[lbl] = [x, y, x, y]
        else:
            box = boxes[lbl]
            if x < box[0]:
                box[0] = x
            if y < box[1]:
                box[1] = y
            if x > box[2]:
                box[2] = x
            if y > box[3]:
                box[3] = y
    return {k: tuple(v) for k, v in boxes.items()}


def detect_cards(image_path: Path) -> list[CardBox]:
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)

    mask = _build_card_mask(arr)

    # Downscale to speed up the python CC implementation
    scale = 4
    small = mask[::scale, ::scale]

    labels, _ = _label_components(small)
    boxes_small = _bounding_boxes(labels)

    page_area = small.size
    min_area = page_area * MIN_CARD_AREA_FRACTION
    max_area = page_area * MAX_CARD_AREA_FRACTION

    cards: list[CardBox] = []
    for lbl, (x0, y0, x1, y1) in boxes_small.items():
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        area = bw * bh
        if area < min_area or area > max_area:
            continue
        aspect = bw / bh
        if not (MIN_ASPECT_RATIO <= aspect <= MAX_ASPECT_RATIO):
            continue
        # back to full resolution
        cards.append(
            CardBox(x=x0 * scale, y=y0 * scale, w=bw * scale, h=bh * scale)
        )

    # Sort: top-to-bottom, then left-to-right with row-clustering tolerance
    cards.sort(key=lambda c: (round(c.y / 80), c.x))
    return cards


def main() -> None:
    image_path = Path(sys.argv[1])
    cards = detect_cards(image_path)
    print(json.dumps([asdict(c) for c in cards], indent=2))
    print(f"\n{len(cards)} cards detected on {image_path.name}", file=sys.stderr)


if __name__ == "__main__":
    main()
