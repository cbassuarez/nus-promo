"""A glyph atlas in the terminal's face — IBM Plex Mono, packed the way a
renderer packs one: a grid of cells, white coverage on black. Stand-in for a
real dump from nus-render's atlas (see RESHOOT.md).  → public/internals/atlas.png"""
import os
from PIL import Image, ImageDraw, ImageFont

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
chars = [chr(c) for c in range(33, 127)] + list("─│┌┐└┘├┤┬┴┼━┃▀▄█░▒▓·•→←↑↓⌘⏎✓✗λ≠≤≥∞πΣΩ") + list("PS C:\\>~$#")
cols, cell = 16, 64
rows = (len(chars) + cols - 1) // cols
img = Image.new("L", (cols * cell, max(rows, cols) * cell), 0)
d = ImageDraw.Draw(img)
face = ImageFont.truetype(os.path.join(root, "public/fonts/IBMPlexMono-Regular.ttf"), 44)
for i, ch in enumerate(chars):
    x, y = (i % cols) * cell, (i // cols) * cell
    d.text((x + cell / 2, y + cell / 2), ch, fill=255, font=face, anchor="mm")
for i in range(cols + 1):  # the cell grid, faint
    d.line([(i * cell, 0), (i * cell, img.height)], fill=40)
    d.line([(0, i * cell), (img.width, i * cell)], fill=40)
img.convert("RGB").save(os.path.join(root, "public/internals/atlas.png"))
print("atlas.png", img.size, len(chars), "glyphs")
