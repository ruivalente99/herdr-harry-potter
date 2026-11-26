#!/usr/bin/env python3
"""Build seven Wizarding World pixel-art location emblems and scenic backdrops (light/dark).

Usage: python3 tools/build-realm-backgrounds.py [--preview /tmp/hogwarts-realms.png]
PNG files are used by Herdr; matching SVG files are editable/exportable sources.
"""

import argparse
from html import escape
import json
from pathlib import Path
import random
import struct
import xml.etree.ElementTree as ET
import zlib

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "backgrounds/realms"
REALMS = {
    "great-hall": ("Great Hall", "#e0b34c"),
    "hogwarts-express": ("Hogwarts Express", "#c94242"),
    "gryffindor-tower": ("Gryffindor Tower", "#d45348"),
    "slytherin-dungeon": ("Slytherin Dungeon", "#52b878"),
    "quidditch-pitch": ("Quidditch Pitch", "#d9a841"),
    "diagon-alley": ("Diagon Alley", "#b88a56"),
    "astronomy-tower": ("Astronomy Tower", "#6e9bd6"),
}
W, H = 320, 180


def rgb(color):
    return tuple(bytes.fromhex(color.lstrip("#")))


def blend(a, b, amount):
    return "#" + "".join(f"{round(x * (1 - amount) + y * amount):02x}" for x, y in zip(rgb(a), rgb(b)))


def png(path, pixels, scale=1):
    height, width = len(pixels), len(pixels[0])
    rows = []
    for row in pixels:
        scan = b"\0" + b"".join(bytes(rgb(color)) * scale for color in row)
        rows.extend([scan] * scale)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">2I5B", width * scale, height * scale, 8, 2, 0, 0, 0)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                           + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b""))


class Scene:
    def __init__(self, dark, accent):
        side = "slytherin" if dark else "gryffindor"
        theme = json.loads((ROOT / "themes" / f"{side}.json").read_text())
        colors = theme["colors"]
        self.dark = dark
        self.colors = {
            "sky": theme["background"], "deep": colors["canvas"], "planet": colors["hover"],
            "horizon": blend(colors["hover"], theme["background"], 0.35),
            "stone": blend(colors["border"], theme["background"], 0.50 if dark else 0.55),
            "star": blend(colors["dim"], theme["background"], 0.35),
            "frame": colors["border"], "hull": blend(colors["input"], theme["background"], 0.72),
            "edge": colors["input"], "panel": colors["surface"], "glass": colors["selected"],
            "light": colors["muted"],
        }
        self.colors["accent"] = blend(accent, self.colors["sky"], 0.18 if dark else 0.45)
        self.colors["glow"] = blend(accent, self.colors["sky"], 0.42 if dark else 0.65)
        self.pixels = [[self.colors["sky"]] * W for _ in range(H)]

    def rect(self, x, y, width, height, color):
        color = self.colors.get(color, color)
        for yy in range(max(0, y), min(H, y + height)):
            self.pixels[yy][max(0, x):min(W, x + width)] = [color] * max(0, min(W, x + width) - max(0, x))

    def poly(self, points, color):
        for y in range(max(0, min(p[1] for p in points)), min(H, max(p[1] for p in points))):
            hits = []
            for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
                if min(y1, y2) <= y + 0.5 < max(y1, y2):
                    hits.append(x1 + (y + 0.5 - y1) * (x2 - x1) / (y2 - y1))
            hits.sort()
            for x1, x2 in zip(hits[::2], hits[1::2]):
                left, right = round(x1), round(x2)
                self.rect(left, y, right - left, 1, color)

    def line(self, x1, y1, x2, y2, width, color):
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        for step in range(steps + 1):
            x, y = round(x1 + (x2 - x1) * step / steps), round(y1 + (y2 - y1) * step / steps)
            self.rect(x - width // 2, y - width // 2, width, width, color)

    def disc(self, cx, cy, radius, color):
        for y in range(max(0, cy - radius), min(H, cy + radius + 1)):
            half = int(max(0, radius ** 2 - (y - cy) ** 2) ** 0.5)
            self.rect(cx - half, y, 2 * half + 1, 1, color)

    def ring(self, cx, cy, outer, inner, color):
        for y in range(max(0, cy - outer), min(H, cy + outer + 1)):
            for x in range(max(0, cx - outer), min(W, cx + outer + 1)):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if inner ** 2 <= d2 <= outer ** 2:
                    self.pixels[y][x] = self.colors.get(color, color)

    def window(self, points, rim=None):
        space = self.pixels
        self.pixels = [[self.colors["frame"]] * W for _ in range(H)]
        if rim:
            self.poly(rim, "hull")
        self.poly(points, "sky")
        for y, row in enumerate(self.pixels):
            for x, color in enumerate(row):
                if color == self.colors["sky"]:
                    row[x] = space[y][x]

    def svg(self, title):
        out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" '
               'width="640" height="360" shape-rendering="crispEdges">',
               f"  <title>{escape(title)} — pixel art</title>"]
        for y, row in enumerate(self.pixels):
            x = 0
            while x < W:
                end = x + 1
                while end < W and row[end] == row[x]:
                    end += 1
                out.append(f'<rect x="{x}" y="{y}" width="{end - x}" height="1" fill="{row[x]}"/>')
                x = end
        return "\n".join([*out, "</svg>", ""])


EMBLEM_INK = {
    "K": "#1a1e26", "W": "#f5efe0", "G": "#ebc043", "R": "#c93838",
    "E": "#3ca868", "B": "#4a7ec4", "S": "#b8c2cc", "s": "#6e7a85",
}

# 16x16 Wizarding World location emblems.
EMBLEMS = {
    # Great Hall: floating golden candle with flame & sparkle.
    "great-hall": [
        ".......KK.......",
        "......KGGK......",
        ".....KGGGGK.....",
        "......KGGK......",
        "......KKKK......",
        ".....KWWWWK.....",
        ".....KWWsWK.....",
        ".....KWWWWK.....",
        ".....KWWsWK.....",
        ".....KWWWWK.....",
        ".....KWWWWK.....",
        "....KKGGGGKK....",
        ".....KKKKKK.....",
        "................",
        "................",
        "................",
    ],
    # Hogwarts Express: iconic scarlet steam locomotive front!
    "hogwarts-express": [
        "......KKKK......",
        "......KssK......",
        ".....KRRRRK.....",
        "....KRRGGRRK....",
        "...KRRGGGGKRK...",
        "...KRRRRRRRRK...",
        "...KRKKGGKKRK...",
        "...KRRRRRRRRK...",
        "..KKRRGssGRRKK..",
        "..KSSRRRRRRSSK..",
        "..KKKKGGGGKKKK..",
        "...KssK..KssK...",
        "....KK....KK....",
        "................",
        "................",
        "................",
    ],
    # Gryffindor Tower: scarlet & gold shield crest.
    "gryffindor-tower": [
        "..KKKKKKKKKKKK..",
        ".KGGGGGGGGGGGGK.",
        ".KGRRRRRRRRRRGK.",
        ".KGRRGGGGGGGRGK.",
        ".KGRRGGRRGGRRGK.",
        ".KGRRGGGGGGGRGK.",
        ".KGRRRRGGGRRRGK.",
        ".KGRRRGGRGGRRGK.",
        "..KGRRRRRRRRGK..",
        "..KGRRGGGGGRGK..",
        "...KGRRRRRRGK...",
        "....KGRRRRGK....",
        ".....KGGGGK.....",
        "......KKKK......",
        "................",
        "................",
    ],
    # Slytherin Dungeon: emerald & silver serpent crest.
    "slytherin-dungeon": [
        "..KKKKKKKKKKKK..",
        ".KSSSSSSSSSSSSK.",
        ".KSEEEEEEEEEESK.",
        ".KSEESSSSSSEESK.",
        ".KSESSEEEEESESK.",
        ".KSEESSSSSSEESK.",
        ".KSEEEEEESSEESK.",
        ".KSEESSSSSSEESK.",
        "..KSEEEEEEEEESK.",
        "..KSESSSSSSSESK.",
        "...KSEEEEEESK...",
        "....KSEEEESK....",
        ".....KSSSSK.....",
        "......KKKK......",
        "................",
        "................",
    ],
    # Quidditch Pitch: winged Golden Snitch!
    "quidditch-pitch": [
        "................",
        "................",
        ".KKK........KKK.",
        "KSSSK..KK..KSSSK",
        ".KSSSKGWWGKSSSK.",
        "..KSSKGGGGKSSK..",
        "...KKGWWWWGKK...",
        ".....KGGGGK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Diagon Alley: crossed wands & golden galleon star!
    "diagon-alley": [
        ".......KK.......",
        "......KGGK......",
        ".KK..KGGGGK..KK.",
        "KssK..KGGK..KssK",
        ".KssK..KK..KssK.",
        "..KssK....KssK..",
        "...KssK..KssK...",
        "....KssKKssK....",
        ".....KssssK.....",
        "....KssKKssK....",
        "...KssK..KssK...",
        "..KGGK....KGGK..",
        ".KGGK......KGGK.",
        "..KK........KK..",
        "................",
        "................",
    ],
    # Astronomy Tower: golden crescent moon & stars!
    "astronomy-tower": [
        "......KKKK......",
        "....KKGGGGKK....",
        "...KGGGKKKKKK...",
        "..KGGGK.........",
        "..KGGK....KGK...",
        ".KGGGK...KGGGK..",
        ".KGGGK....KGK...",
        ".KGGGK..........",
        "..KGGK..........",
        "..KGGGK...KK....",
        "...KGGGKKKKGK...",
        "....KKGGGGKK....",
        "......KKKK......",
        "................",
        "................",
        "................",
    ],
}


def emblems():
    folder = ROOT / "mods/hogwarts-systems/realms"
    for realm, rows in EMBLEMS.items():
        assert len(rows) == 16 and all(len(row) == 16 for row in rows), realm
        rects = []
        for y, row in enumerate(rows):
            x = 0
            while x < 16:
                end = x + 1
                while end < 16 and row[end] == row[x]:
                    end += 1
                if row[x] != ".":
                    rects.append(f'<rect x="{x}" y="{y}" width="{end - x}" height="1" fill="{EMBLEM_INK[row[x]]}"/>')
                x = end
        (folder / f"{realm}.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="32" height="32" '
            f'shape-rendering="crispEdges"><title>{escape(REALMS[realm][0])}</title>{"".join(rects)}</svg>', encoding="utf-8")


def draw_hogwarts_silhouette(s, base_y=148):
    # Iconic Hogwarts castle towers silhouette across the Scottish loch!
    s.poly([(0, base_y), (42, 108), (94, 128), (154, 102), (218, 124), (274, 106), (320, 130), (320, 180), (0, 180)], "stone")
    for tx, tw, th in [(112, 10, 42), (126, 16, 62), (146, 12, 48), (162, 18, 56), (184, 10, 38)]:
        s.rect(tx, base_y - th, tw, th, "horizon")
        s.poly([(tx - 1, base_y - th), (tx + tw // 2, base_y - th - 14), (tx + tw + 1, base_y - th)], "horizon")
        s.rect(tx + tw // 2 - 1, base_y - th + 8, 2, 4, "glow")


def draw_vista(realm, dark):
    s = Scene(dark, REALMS[realm][1])
    rng = random.Random(901 + sum(ord(c) for c in realm))
    for _ in range(80):
        s.rect(rng.randrange(W), rng.randrange(135), 1, 1, "star")

    if realm == "great-hall":
        # Enchanted starry Great Hall ceiling with floating golden candles!
        for cx, cy in [(46, 36), (82, 52), (122, 32), (160, 48), (198, 34), (236, 50), (272, 38)]:
            s.rect(cx, cy, 3, 14, "horizon")
            s.rect(cx, cy - 4, 3, 3, "glow")
            s.rect(cx + 1, cy - 6, 1, 2, "accent")
        s.rect(0, 138, W, 42, "stone")
    elif realm == "hogwarts-express":
        # Scottish Highland hills & iconic Glenfinnan stone viaduct arches!
        s.poly([(0, 136), (52, 86), (118, 114), (186, 82), (254, 110), (320, 88), (320, 180), (0, 180)], "stone")
        s.rect(0, 118, W, 8, "horizon")
        for x in range(18, 310, 38):
            s.rect(x, 126, 8, 36, "horizon")
            s.disc(x + 23, 134, 11, "sky")
    elif realm == "gryffindor-tower":
        # View from Gryffindor Tower over Hogwarts spires & moon!
        s.disc(250, 52, 24, "planet")
        s.disc(258, 48, 21, "sky")
        draw_hogwarts_silhouette(s, 148)
    elif realm == "slytherin-dungeon":
        # Underwater Black Lake view with drifting light shafts & bubbles!
        for x in (48, 116, 192, 258):
            s.poly([(x, 0), (x + 26, 0), (x + 54, 160), (x + 18, 160)], "horizon")
        for bx, by, br in [(64, 96, 4), (128, 72, 6), (212, 108, 5), (264, 62, 4)]:
            s.ring(bx, by, br, br - 1, "glow")
    elif realm == "quidditch-pitch":
        # Open sky with the three iconic Quidditch goal hoops!
        for cx, cy, r in [(54, 126, 22), (110, 132, 24), (218, 128, 26), (274, 132, 22)]:
            s.disc(cx, cy, r, "horizon")
        for gx, gy in [(112, 74), (160, 56), (208, 74)]:
            s.rect(gx - 1, gy + 14, 3, 76, "stone")
            s.ring(gx, gy, 14, 11, "accent")
    elif realm == "diagon-alley":
        # Crooked Wizarding gables & Gringotts domed roof in the distance!
        for bx, bw, bh in [(18, 34, 64), (56, 30, 52), (92, 36, 70), (194, 32, 66), (232, 36, 54), (274, 30, 62)]:
            s.rect(bx, 152 - bh, bw, bh, "stone")
            s.poly([(bx - 2, 152 - bh), (bx + bw // 2, 134 - bh), (bx + bw + 2, 152 - bh)], "horizon")
            s.rect(bx + 8, 164 - bh, 6, 8, "glow")
            s.rect(bx + 18, 164 - bh, 6, 8, "glow")
        s.disc(160, 104, 24, "horizon")
        s.rect(136, 104, 48, 48, "horizon")
    else:
        # Astronomy Tower: full moon over Forbidden Forest & Black Lake reflection!
        s.disc(236, 56, 28, "planet")
        s.disc(245, 52, 25, "sky")
        for px in range(8, 316, 18):
            ph = 24 + (px * 13) % 28
            s.poly([(px, 144), (px + 9, 144 - ph), (px + 18, 144)], "stone")
        s.rect(0, 144, W, 36, "horizon")
        for ry in range(148, 174, 5):
            s.rect(220, ry, 28 - (ry - 148) // 2, 2, "glow")

    # Subtle emblem crest in upper right.
    emblem = ET.parse(ROOT / f"mods/hogwarts-systems/realms/{realm}.svg").getroot()
    for rect in emblem.findall("{http://www.w3.org/2000/svg}rect"):
        x, y, w, h = (int(rect.attrib[k]) for k in ["x", "y", "width", "height"])
        ink = blend(rect.attrib["fill"], s.colors["sky"], 0.68 if dark else 0.74)
        s.rect(218 + x * 4, 34 + y * 4, w * 4, h * 4, ink)
    return s


def draw(realm, dark=True):
    s = draw_vista(realm, dark)
    if realm == "great-hall":
        # Tall Gothic stone window mullions & warm stone sill.
        s.poly([(0, 0), (320, 0), (320, 18), (0, 18)], "frame")
        for x in [12, 106, 208, 302]:
            s.rect(x, 16, 8, 134, "frame")
            s.rect(x + 3, 18, 2, 130, "edge")
        s.rect(0, 148, 320, 32, "hull")
        s.line(0, 148, 320, 148, 2, "accent")
    elif realm == "hogwarts-express":
        # Wood-trimmed Express compartment window frame & plush bench sill.
        s.window([(24, 18), (296, 18), (296, 142), (24, 142)],
                 rim=[(16, 10), (304, 10), (304, 150), (16, 150)])
        s.rect(158, 14, 4, 132, "frame")
        s.rect(0, 150, 320, 30, "hull")
        s.line(0, 150, 320, 150, 2, "accent")
    elif realm == "gryffindor-tower":
        # Pointed Gothic tower arch & crimson-gold tapestry sill!
        s.window([(46, 20), (160, 6), (274, 20), (302, 64), (302, 148), (18, 148), (18, 64)])
        s.line(160, 8, 160, 148, 4, "frame")
        s.line(18, 86, 302, 86, 3, "frame")
        s.rect(0, 148, 320, 32, "hull")
        s.line(0, 148, 320, 148, 3, "accent")
    elif realm == "slytherin-dungeon":
        # Vaulted stone underwater dungeon arches!
        s.poly([(0, 0), (320, 0), (320, 24), (0, 24)], "hull")
        for x in [0, 96, 216, 308]:
            s.rect(x, 20, 12, 132, "frame")
            s.rect(x + 4, 24, 3, 124, "edge")
        s.rect(0, 148, 320, 32, "hull")
        s.line(0, 148, 320, 148, 2, "accent")
    elif realm == "quidditch-pitch":
        # Stadium wooden box awning & house-banner rail!
        s.rect(0, 0, 320, 16, "frame")
        for x in [22, 290]:
            s.rect(x, 16, 8, 134, "frame")
        s.rect(0, 148, 320, 32, "hull")
        s.line(0, 148, 320, 148, 3, "accent")
        for x in range(18, 306, 24):
            s.rect(x, 154, 14, 16, "panel")
            s.rect(x + 2, 156, 10, 2, "accent")
    elif realm == "diagon-alley":
        # Leaded-glass crooked shopfront window panes!
        s.window([(20, 16), (300, 16), (300, 146), (20, 146)])
        for x in [90, 160, 230]:
            s.rect(x, 16, 3, 130, "frame")
        s.rect(20, 80, 280, 3, "frame")
        s.rect(0, 146, 320, 34, "hull")
        s.line(0, 146, 320, 146, 2, "accent")
    else:
        # Astronomy Tower stone crenellations & brass telescope rail!
        s.rect(0, 0, 320, 12, "frame")
        for x in [16, 294]:
            s.rect(x, 12, 10, 136, "frame")
        s.rect(0, 146, 320, 34, "hull")
        for x in range(16, 304, 36):
            s.rect(x, 138, 18, 10, "frame")
        s.line(0, 148, 320, 148, 2, "accent")
    return s


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()
    emblems()
    DEST.mkdir(parents=True, exist_ok=True)
    scenes = []
    for realm, (title, _) in REALMS.items():
        for dark in [True, False]:
            scene = draw(realm, dark)
            target = DEST / ("slytherin" if dark else "gryffindor")
            target.mkdir(parents=True, exist_ok=True)
            (target / f"{realm}.svg").write_text(scene.svg(title), encoding="utf-8")
            png(target / f"{realm}.png", scene.pixels, scale=2)
            if dark:
                scenes.append(scene)
    if args.preview:
        background = Scene(True, REALMS["great-hall"][1]).colors["sky"]
        sheet = [[background] * (W * 2) for _ in range(H * 4)]
        for index, scene in enumerate(scenes):
            x, y = (index % 2) * W, (index // 2) * H
            for yy, row in enumerate(scene.pixels):
                sheet[y + yy][x:x + W] = row
        png(args.preview, sheet)
        print(f"Preview: {args.preview}")
    print(f"Built {len(REALMS) * 2} Wizarding realm backgrounds (PNG + SVG) in {DEST}")


if __name__ == "__main__":
    main()
