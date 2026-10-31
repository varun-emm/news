# Builds the app icon: a periodic-table style "Ne" tile, the symbol in Fraunces (the masthead serif), labels in Inter.
# usage: python3 tools/icon.py inter-600.ttf fraunces-800.ttf out_dir
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
f600, f800, out = TTFont(sys.argv[1]), TTFont(sys.argv[2]), sys.argv[3]
ACCENT, INK, MUTED, BG = "#ff5a36", "#f5f5f7", "#a1a1aa", "#0b0b0f"

def text(font, s, size, x, y, fill, anchor="start", track=0):
    # glyph outlines as one SVG path, positioned by the baseline; track is extra spacing in em
    gs, cmap, upm = font.getGlyphSet(), font.getBestCmap(), font["head"].unitsPerEm
    hmtx, parts, adv = font["hmtx"], [], 0
    for ch in s:
        g = cmap[ord(ch)]; pen = SVGPathPen(gs); gs[g].draw(pen)
        parts.append((adv, pen.getCommands())); adv += hmtx[g][0] + track * upm
    adv -= track * upm
    k = size / upm; x0 = x - (adv * k if anchor == "end" else adv * k / 2 if anchor == "middle" else 0)
    return "".join(f'<path transform="translate({x0 + a * k:.2f},{y}) scale({k:.5f},{-k:.5f})" d="{d}"/>' for a, d in parts if d).join([f'<g fill="{fill}">', "</g>"])

def tile(rounded=True, detail=True):
    r = 22 if rounded else 0
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">',
         f'<defs><radialGradient id="glow" cx="50%" cy="55%" r="60%"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".22"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient></defs>',
         f'<rect width="100" height="100" rx="{r}" fill="{BG}"/>',
         f'<rect width="100" height="100" rx="{r}" fill="url(#glow)"/>']
    if detail:
        s.append(f'<rect x="9" y="9" width="82" height="82" rx="{max(r - 9, 6)}" fill="none" stroke="{ACCENT}" stroke-opacity=".55" stroke-width="1.6"/>')
        s.append(text(f600, "10", 12, 17, 28, ACCENT))
        s.append(text(f600, "20.18", 8.5, 83, 27, MUTED, "end"))
        s.append(text(f800, "Ne", 44, 50, 68, INK, "middle", -0.02))
        s.append(text(f600, "NEWS", 9, 50, 83, MUTED, "middle", 0.18))
    else:  # tiny sizes: just the symbol, as big as it goes
        s.append(text(f800, "Ne", 60, 50, 72, INK, "middle", -0.03))
    return "".join(s) + "</svg>"

open(f"{out}/favicon.svg", "w").write(tile())
open(f"{out}/icon-full.svg", "w").write(tile(rounded=False))
open(f"{out}/icon-small.svg", "w").write(tile(detail=False))
print("ok")
