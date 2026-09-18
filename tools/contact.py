"""Contact sheets: a labelled grid of stills, set in Plex Mono on paper.

  python3 tools/contact.py OUT.png --title "styleframes · 16:9" --cols 4 --width 480 a.png b.png ...

Each label is the file's stem (or `label=path`). Needs Pillow.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PAPER = (244, 241, 234)
INK = (20, 20, 20)
DIM = (107, 102, 92)


def font(weight, size):
    return ImageFont.truetype(str(ROOT / f"public/fonts/IBMPlexMono-{weight}.ttf"), size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--title", default="")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--width", type=int, default=480)
    ap.add_argument("--gap", type=int, default=28)
    a = ap.parse_args()

    items = []
    for s in a.images:
        label, _, path = s.rpartition("=") if "=" in s else ("", "", s)
        im = Image.open(path).convert("RGB")
        h = round(im.height * a.width / im.width)
        items.append((label or Path(path).stem, im.resize((a.width, h), Image.LANCZOS)))

    cols = min(a.cols, len(items))
    rows = [items[i : i + cols] for i in range(0, len(items), cols)]
    lab = font("Medium", 15)
    head = font("SemiBold", 30)
    g = a.gap
    top = 96 if a.title else g
    row_h = [max(im.height for _, im in r) + 34 for r in rows]
    W = g + cols * (a.width + g)
    H = top + sum(row_h) + g * len(rows)
    sheet = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(sheet)
    if a.title:
        d.text((g, 34), a.title, font=head, fill=INK)
    y = top
    for r, rh in zip(rows, row_h):
        for c, (label, im) in enumerate(r):
            x = g + c * (a.width + g)
            d.rectangle([x + 6, y + 6, x + im.width + 6, y + im.height + 6], fill=INK)  # the hard shadow
            sheet.paste(im, (x, y))
            d.rectangle([x, y, x + im.width - 1, y + im.height - 1], outline=INK, width=2)
            d.text((x, y + im.height + 12), label, font=lab, fill=DIM)
        y += rh + g
    sheet.save(a.out)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
