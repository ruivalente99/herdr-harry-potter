#!/usr/bin/env python3
"""Spell Run's local Harry Potter pixel-art rooms, props, bitmap lettering and walking atlases.

Uses only the standard library. Character palettes come from the existing
32px Harry Potter cast; each atlas has idle / left stride / right stride, in four directions.
Run: python3 tools/build-spell-run-art.py [--preview docs/images/spell-run-decks.png]
"""
import argparse
from html import escape
from pathlib import Path
import json
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "mods/hogwarts-tabs/arcade"
CAST = ROOT / "mods/hogwarts-agents/sprites/hogwarts"
INK = "#11151f"


class Canvas:
    def __init__(self, width, height, title):
        self.width, self.height, self.title = width, height, title
        self.pixels = [[None] * width for _ in range(height)]

    def rect(self, x, y, width, height, color):
        for yy in range(max(0, y), min(self.height, y + height)):
            for xx in range(max(0, x), min(self.width, x + width)):
                self.pixels[yy][xx] = color

    def svg(self):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" width="{self.width}" height="{self.height}" shape-rendering="crispEdges">',
               f"<title>{escape(self.title)}</title>"]
        for y, row in enumerate(self.pixels):
            x = 0
            while x < self.width:
                color, end = row[x], x + 1
                while end < self.width and row[end] == color:
                    end += 1
                if color:
                    out.append(f'<rect x="{x}" y="{y}" width="{end - x}" height="1" fill="{color}"/>')
                x = end
        return "\n".join([*out, "</svg>", ""])

    def save(self, name):
        path = ART / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.svg())

    def png(self, path):
        raw = b"".join(b"\x00" + bytes(int((color or "#09131f")[index:index + 2], 16)
                        for color in line for index in (1, 3, 5)) for line in self.pixels)
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0))
                              + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


FONT = {
    "A": "010/101/111/101/101", "B": "110/101/110/101/110", "C": "011/100/100/100/011",
    "D": "110/101/101/101/110", "E": "111/100/110/100/111", "F": "111/100/110/100/100",
    "G": "011/100/101/101/011", "H": "101/101/111/101/101", "I": "111/010/010/010/111",
    "J": "001/001/001/101/010", "K": "101/101/110/101/101", "L": "100/100/100/100/111",
    "M": "10001/11011/10101/10001/10001", "N": "1001/1101/1011/1001/1001",
    "O": "010/101/101/101/010", "P": "110/101/110/100/100", "Q": "010/101/101/111/011",
    "R": "110/101/110/101/101", "S": "011/100/010/001/110", "T": "111/010/010/010/010",
    "U": "101/101/101/101/111", "V": "101/101/101/101/010", "W": "10001/10001/10101/10101/01010",
    "X": "101/101/010/101/101", "Y": "101/101/010/010/010", "Z": "111/001/010/100/111",
    " ": "00/00/00/00/00", "-": "000/000/111/000/000",
}


def lettering(text, name, color):
    width = sum(len(FONT[c].split('/')[0]) + 1 for c in text) - 1
    p = Canvas(width, 5, text)
    x = 0
    for char in text:
        glyph = FONT[char].split('/')
        for y, line in enumerate(glyph):
            for dx, dot in enumerate(line):
                if dot == "1":
                    p.rect(x + dx, y, 1, 1, color)
        x += len(glyph[0]) + 1
    p.save(f"{name}.svg")


def deck(spec):
    p = Canvas(208, 224, f"{spec['name']} — Hogwarts pixel-art zone")
    p.rect(0, 0, 208, 224, "#0d1016")
    p.rect(0, 0, 208, 30, "#242228")
    p.rect(0, 0, 208, 2, "#69625a")
    # Walkable stone/wood floor with subtle tiles.
    p.rect(0, 30, 208, 178, "#1e2024")
    for y in range(32, 208, 16):
        for x in range(0, 208, 16):
            p.rect(x, y, 16, 16, "#1d2c37" if (x + y) % 32 else "#202f39")
            p.rect(x + 1, y + 15, 14, 1, "#14161c")
            if (x * 3 + y) % 48 == 0:
                p.rect(x + 3, y + 3, 1, 1, "#454240")
    # Continuous outer castle walls follow collision border.
    for x, y, w, h in [(0, 30, 208, 18), (0, 192, 208, 16), (0, 48, 16, 144), (192, 48, 16, 144)]:
        p.rect(x, y, w, h, "#11131a")
        p.rect(x + 2, y + 2, max(1, w - 4), max(1, h - 4), "#344554")
    p.rect(16, 45, 176, 2, "#72919b")
    p.rect(16, 191, 176, 2, "#72919b")
    p.rect(13, 48, 2, 144, "#585654")
    p.rect(193, 48, 2, 144, "#585654")
    # Wall sconces & stone trim.
    for x in range(26, 188, 28):
        p.rect(x, 35, 12, 6, "#161820")
        p.rect(x + 4, 36, 4, 3, "#e8b44c")
        p.rect(x + 5, 36, 2, 1, "#fff2bd")
        p.rect(x, 197, 12, 3, "#1a1e26")
    for y in range(56, 186, 28):
        for x in (4, 198):
            p.rect(x, y, 6, 12, "#1c1f26")
            p.rect(x + 2, y + 3, 2, 4, "#e8b44c")
    # Lower arched doorway frame.
    p.rect(0, 208, 208, 16, "#171920")
    p.rect(68, 211, 72, 11, "#2f2c2a")
    p.rect(72, 214, 64, 6, "#0d1016")
    p.rect(101, 214, 6, 6, "#8c7650")

    zone = spec["id"]
    accent = spec["accent"]
    if zone == "greathall":
        # Great Hall: Gothic windows, house banners (crimson/green/blue/yellow) & floating candles!
        p.rect(10, 4, 188, 22, "#161522")
        for idx, x in enumerate(range(18, 186, 24)):
            p.rect(x, 6, 16, 18, "#3e3730")
            p.rect(x + 2, 8, 12, 14, "#101629")
            p.rect(x + 7, 12, 2, 8, "#f0e6cc")
            p.rect(x + 7, 9, 2, 3, "#ffd45e")
        # Four Hogwarts house carpet runners!
        for x, col in [(24, "#6e2629"), (178, "#235c3b")]:
            p.rect(x, 48, 6, 142, col)
    elif zone == "potions":
        # Potions Dungeon: vaulted stone alcoves with glowing green/violet potion bottles!
        p.rect(10, 4, 188, 22, "#101c18")
        for x in range(16, 192, 26):
            p.rect(x, 6, 20, 17, "#2d453a")
            p.rect(x + 2, 8, 16, 13, "#101e19")
            p.rect(x + 4, 13, 4, 6, "#4ee680")
            p.rect(x + 11, 11, 5, 8, "#a66bff")
            p.rect(x + 5, 11, 2, 2, "#c4ffd6")
            p.rect(x + 13, 9, 2, 2, "#e8d1ff")
        for y in (82, 146):
            p.rect(18, y, 172, 2, "#244738")
    elif zone == "library":
        # Restricted Section: towering bookshelves with colorful ancient spellbook spines!
        p.rect(10, 4, 188, 22, "#241914")
        colors = ["#a63232", "#2d6b47", "#2e548a", "#c99638", "#6e3b85"]
        for x in range(14, 190, 22):
            p.rect(x, 6, 18, 18, "#573d2c")
            p.rect(x + 2, 8, 14, 14, "#241812")
            for i in range(4):
                p.rect(x + 3 + i * 3, 9, 2, 5, colors[(x + i) % len(colors)])
                p.rect(x + 3 + i * 3, 16, 2, 5, colors[(x + i + 2) % len(colors)])
    elif zone == "greenhouse":
        # Herbology Greenhouse: Victorian glasshouse arches & lush hanging vines!
        p.rect(10, 4, 188, 22, "#19302a")
        for x in range(14, 192, 24):
            p.rect(x, 6, 20, 17, "#5e7d6c")
            p.rect(x + 2, 8, 16, 13, "#274d44")
            p.rect(x + 9, 8, 2, 13, "#5e7d6c")
            p.rect(x + 4, 9, 3, 6, "#5ec458")
            p.rect(x + 13, 11, 3, 7, "#80e075")
    elif zone == "quidditch":
        # Quidditch Pitch: bright blue sky + three iconic golden Quidditch goal hoops!
        p.rect(10, 4, 188, 22, "#1a3454")
        p.rect(14, 6, 180, 18, "#244c7a")
        for gx, gy in [(64, 9), (104, 6), (144, 9)]:
            p.rect(gx - 4, gy, 10, 9, "#f0c243")
            p.rect(gx - 2, gy + 2, 6, 5, "#244c7a")
            p.rect(gx, gy + 9, 2, 14 - gy + 9, "#b8902a")
        # Turf pitch lines.
        p.rect(103, 48, 2, 144, "#355e44")
        p.rect(16, 119, 176, 2, "#355e44")
    elif zone == "chamber":
        # Chamber of Secrets: carved stone serpent heads & shimmering green-teal water!
        p.rect(10, 4, 188, 22, "#112121")
        for x in (20, 62, 126, 168):
            p.rect(x, 6, 20, 18, "#3e5e5c")
            p.rect(x + 3, 9, 14, 12, "#183333")
            p.rect(x + 5, 11, 3, 2, "#52f0c0")
            p.rect(x + 12, 11, 3, 2, "#52f0c0")
            p.rect(x + 7, 16, 6, 2, "#2f5754")
        p.rect(92, 6, 24, 18, "#294545")
        p.rect(96, 10, 16, 10, "#122626")
        p.rect(100, 13, 8, 4, "#52d6b5")
    elif zone == "ministry":
        # Ministry Atrium: dark obsidian arches & glowing emerald Floo fireplaces!
        p.rect(10, 4, 188, 22, "#181626")
        for x in range(16, 192, 30):
            p.rect(x, 6, 24, 18, "#4c446e")
            p.rect(x + 3, 8, 18, 14, "#141121")
            p.rect(x + 6, 12, 12, 10, "#2aa85c")
            p.rect(x + 8, 14, 8, 6, "#8cffb4")
            p.rect(x + 2, 6, 20, 2, "#e8bd4c")
    elif zone == "forest":
        # Forbidden Forest: moonlit pine silhouettes & silver mist!
        p.rect(10, 4, 188, 22, "#101626")
        p.rect(164, 7, 12, 12, "#cddbff")
        p.rect(168, 7, 10, 10, "#101626")
        for x in range(14, 190, 16):
            p.rect(x + 4, 10, 4, 14, "#24304a")
            p.rect(x + 2, 14, 8, 10, "#1b263d")
            p.rect(x + 5, 18, 2, 6, "#141a2b")
    replacements = {
        "#1d2c37": spec["floor"], "#202f39": spec["floor"],
        "#344554": spec["wall"], "#72919b": accent,
    }
    p.pixels = [[replacements.get(color, color) for color in line] for line in p.pixels]
    p.save(f"deck-{zone}.svg")


def zone_props():
    for kind in ("brazier", "rack", "bookshelf", "planter", "broomrack", "serpent", "floo", "stump"):
        p = Canvas(16, 16, kind)
        p.rect(1, 13, 14, 3, "#0a0e16")
        if kind == "brazier":
            # Great Hall golden fire brazier!
            p.rect(4, 10, 8, 4, "#594836")
            p.rect(3, 7, 10, 4, "#8c6d42")
            p.rect(4, 8, 8, 1, "#e8be4c")
            p.rect(4, 3, 8, 4, "#e0582b")
            p.rect(5, 2, 6, 4, "#f5be3b")
            p.rect(7, 3, 2, 2, "#fff5cc")
        elif kind == "rack":
            # Potions Dungeon iron cauldron & glowing potion rack.
            p.rect(2, 2, 12, 12, "#26332e")
            p.rect(3, 3, 10, 2, "#597366")
            p.rect(4, 6, 3, 5, "#4ee680")
            p.rect(9, 6, 3, 5, "#b06eff")
            p.rect(4, 11, 8, 2, "#465950")
        elif kind == "bookshelf":
            # Restricted Section enchanted bookcase.
            p.rect(1, 1, 14, 13, "#4f3626")
            p.rect(2, 2, 12, 11, "#291b12")
            for y in (3, 8):
                p.rect(3, y, 2, 4, "#b83535")
                p.rect(6, y, 2, 4, "#2e734c")
                p.rect(9, y, 2, 4, "#36629c")
                p.rect(12, y, 1, 4, "#e0b34c")
                p.rect(2, y + 4, 12, 1, "#6e4c36")
        elif kind == "planter":
            # Herbology Mandrake terracotta planter.
            p.rect(3, 8, 10, 6, "#8c4a32")
            p.rect(2, 7, 12, 2, "#b56343")
            p.rect(4, 3, 8, 5, "#368a3e")
            p.rect(5, 2, 6, 4, "#68d463")
            p.rect(7, 4, 2, 2, "#a8f59a")
        elif kind == "broomrack":
            # Quidditch Pitch wooden broomstick rack.
            p.rect(2, 3, 2, 11, "#6b472c")
            p.rect(12, 3, 2, 11, "#6b472c")
            p.rect(2, 5, 12, 2, "#94643f")
            p.rect(2, 10, 12, 2, "#94643f")
            for x in (5, 9):
                p.rect(x, 1, 2, 10, "#b88248")
                p.rect(x - 1, 10, 4, 4, "#e0b84c")
        elif kind == "serpent":
            # Chamber of Secrets carved stone serpent statue.
            p.rect(3, 1, 10, 13, "#3c5959")
            p.rect(4, 2, 8, 11, "#577d7d")
            p.rect(5, 4, 2, 2, "#52f0c0")
            p.rect(9, 4, 2, 2, "#52f0c0")
            p.rect(5, 8, 6, 2, "#243b3b")
            p.rect(2, 12, 12, 2, "#2b4242")
        elif kind == "floo":
            # Ministry Atrium emerald Floo fireplace.
            p.rect(1, 1, 14, 13, "#453e63")
            p.rect(2, 2, 12, 2, "#e8bd4c")
            p.rect(4, 5, 8, 8, "#161424")
            p.rect(5, 7, 6, 6, "#2eb860")
            p.rect(6, 9, 4, 4, "#9effba")
        else:
            # Forbidden Forest ancient moss-covered tree stump.
            p.rect(2, 4, 12, 10, "#42332c")
            p.rect(3, 3, 10, 3, "#695346")
            p.rect(4, 4, 8, 1, "#8c7260")
            p.rect(2, 6, 3, 4, "#3b7347")
            p.rect(10, 9, 3, 3, "#3b7347")
        p.save(f"{kind}.svg")


def pickups():
    glyphs = {
        "range": ("#f2bd66", [(7, 3, 2, 10), (3, 7, 10, 2), (5, 4, 6, 1), (5, 11, 6, 1)]),
        "nova": ("#ef9678", [(6, 3, 4, 10), (3, 6, 10, 4), (4, 4, 2, 2), (10, 10, 2, 2), (4, 10, 2, 2), (10, 4, 2, 2)]),
        "echo": ("#c2b0ef", [(3, 4, 6, 2), (3, 4, 2, 6), (3, 8, 6, 2), (7, 6, 6, 2), (11, 6, 2, 6), (7, 10, 6, 2)]),
        "rack": ("#9ccc8e", [(3, 4, 10, 2), (3, 7, 10, 2), (3, 10, 10, 2), (4, 3, 2, 10)]),
        "line": ("#78ced1", [(3, 6, 2, 4), (6, 6, 2, 4), (9, 6, 2, 4), (11, 4, 2, 8)]),
        "speed": ("#8fbaf2", [(3, 3, 2, 3), (5, 5, 2, 3), (3, 8, 2, 4), (8, 3, 2, 3), (10, 5, 2, 3), (8, 8, 2, 4)]),
    }
    for name, (color, marks) in glyphs.items():
        p = Canvas(16, 16, f"{name} charm")
        p.rect(2, 0, 12, 16, "#0b1420")
        p.rect(0, 2, 16, 12, "#0b1420")
        p.rect(2, 1, 12, 14, color)
        p.rect(1, 2, 14, 12, color)
        p.rect(3, 3, 10, 10, "#1c2a38")
        for x, y, w, h in marks:
            p.rect(x, y, w, h, color)
        p.rect(7, 7, 2, 2, "#f4efd6")
        p.save(f"buff-{name}.svg")


def props():
    # Destructible enchanted potion barrel/crate.
    for phase in (0, 1):
        p = Canvas(16, 18, "Enchanted potion barrel")
        p.rect(2, 15, 12, 3, "#0b1018")
        p.rect(4, 2, 8, 14, "#0b1018")
        p.rect(3, 4, 10, 10, "#0b1018")
        p.rect(4, 3, 8, 12, "#6e492e")
        p.rect(5, 3, 6, 11, "#8c603e")
        p.rect(6, 4, 2, 9, "#b38056")
        for y in (5, 11):
            p.rect(4, y, 8, 2, "#4a525c")
        # Glowing magical rune seal in center!
        p.rect(6, 7, 4, 4, "#9d5cff" if phase else "#52d6b5")
        p.rect(7, 8, 2, 2, "#f0d9ff" if phase else "#d4fff5")
        p.save(f"crate-{phase}.svg")
    # Exploding Cauldron (3 bubbling fuse phases)!
    for phase in (0, 1, 2):
        p = Canvas(16, 16, "Bubbling exploding cauldron")
        p.rect(3, 13, 10, 2, "#0b1018")
        p.rect(3, 5, 10, 8, "#10141c")
        p.rect(2, 7, 12, 4, "#10141c")
        p.rect(4, 6, 8, 6, "#363d4a")
        p.rect(3, 7, 10, 4, "#292f3a")
        p.rect(5, 7, 2, 3, "#5a6578")
        p.rect(3, 5, 10, 2, "#4e5869")
        # Bubbling magical brew on top!
        brew = ["#b05ce6", "#ff8538", "#fff0a6"][phase]
        spark = ["#e6b8ff", "#ffd154", "#ffffff"][phase]
        p.rect(4, 4, 8, 2, brew)
        p.rect(6, 2 + (phase % 2), 4, 2, spark)
        p.rect(5 + phase * 2, 1, 2, 1, spark)
        p.save(f"cauldron-{phase}.svg")
    # Magical golden-crimson spell burst!
    for phase in range(3):
        p = Canvas(16, 16, "Spell burst")
        for x in range(16):
            spread = [3, 4, 5, 4][(x + phase) % 4]
            p.rect(x, 8 - spread, 1, spread * 2, "#c63848")
            p.rect(x, 9 - spread, 1, spread * 2 - 2, "#f59c42")
            p.rect(x, 7 + (x + phase) % 2, 1, 2, "#fff0a6")
        p.save(f"blast-h-{phase}.svg")
        p.pixels = [list(line) for line in zip(*p.pixels)]
        p.save(f"blast-v-{phase}.svg")
    # Ground shadow & Echo warning.
    p = Canvas(16, 16, "Ground shadow")
    p.rect(4, 12, 8, 3, "#0a101a")
    p.rect(2, 13, 12, 1, "#0a101a")
    p.save("shadow.svg")
    p = Canvas(16, 16, "Echo spell warning — not a pickup")
    for x, y, w, h in [(0, 0, 5, 2), (0, 0, 2, 5), (11, 0, 5, 2), (14, 0, 2, 5),
                        (0, 14, 5, 2), (0, 11, 2, 5), (11, 14, 5, 2), (14, 11, 2, 5)]:
        p.rect(x, y, w, h, "#ef9678")
    for x, y, w, h in [(5, 4, 6, 2), (9, 6, 2, 2), (5, 8, 6, 1), (5, 9, 2, 2), (5, 11, 6, 1)]:
        p.rect(x, y, w, h, "#f2bd66")
    p.save("echo-beacon.svg")


def actors():
    actor_dir = ART / "actors"
    if actor_dir.exists():
        for old in actor_dir.glob("*.svg"):
            old.unlink()
    rects = re.compile(r'<rect x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)" fill="(#[0-9a-f]{6})"/>')
    for path in sorted(CAST.glob("*.svg")):
        src = Canvas(32, 32, path.stem)
        for x, y, w, h, color in rects.findall(path.read_text()):
            src.rect(int(x), int(y), int(w), int(h), color)
        if not any(any(row) for row in src.pixels):
            continue
        for facing in ("down", "up", "left", "right"):
            atlas = Canvas(96, 32, f"{path.stem} — {facing}: idle, left stride, right stride")
            rear = src.pixels[7][10] or src.pixels[5][12] or "#3e5061"
            for phase in range(3):
                for y, line in enumerate(src.pixels):
                    for x, color in enumerate(line):
                        if color is None:
                            continue
                        xx, yy = x, y
                        if phase and y >= 27 and 10 <= x <= 21:
                            leading = (x < 16) == (phase == 1)
                            yy = y - (1 if leading else 0)
                            xx += (-1 if x < 16 else 1) if leading else 0
                        if phase and 20 <= y <= 25 and (x < 11 or x > 20):
                            yy += (1 if x < 16 else -1) * (1 if phase == 1 else -1)
                        if facing == "up":
                            if 8 <= y <= 16 and 9 <= x <= 22 and color != INK:
                                color = rear
                            elif 10 <= y <= 15 and 10 <= x <= 21:
                                color = rear
                        if facing in ("left", "right"):
                            xx = 16 + round((xx - 16) * 0.8)
                            if y < 18:
                                xx += 1
                        if facing == "left":
                            xx = 31 - xx
                        if 0 <= xx < 32 and 0 <= yy < 32:
                            atlas.rect(phase * 32 + xx, yy, 1, 1, color)
            atlas.save(f"actors/{path.stem}-{facing}.svg")


def overview(specs, destination):
    sheet = Canvas(896, 524, "Spell Run Hogwarts room architecture")
    sheet.rect(0, 0, sheet.width, sheet.height, "#0d1016")
    rects = re.compile(r'<rect x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)" fill="(#[0-9a-f]{6})"')
    def paste(name, x, y):
        for sx, sy, width, height, color in rects.findall((ART / name).read_text()):
            sheet.rect(x + int(sx), y + int(sy), int(width), int(height), color)
    for index, spec in enumerate(specs):
        left, top = 8 + index % 4 * 224, 12 + index // 4 * 260
        cursor = left
        for char in spec["name"].upper():
            if char not in FONT:
                continue
            glyph = FONT[char].split("/")
            for y, line in enumerate(glyph):
                for x, dot in enumerate(line):
                    if dot == "1":
                        sheet.rect(cursor + x * 2, top + y * 2, 2, 2, spec["accent"])
            cursor += (len(glyph[0]) + 1) * 2
        paste(f"deck-{spec['id']}.svg", left, top + 18)
        for y, line in enumerate(spec["layout"]):
            for x, kind in enumerate(line):
                if kind == "#" and 0 < x < 12 and 0 < y < 10:
                    paste(f"{spec['prop']}.svg", left + x * 16, top + 18 + (y + 2) * 16)
    sheet.png(destination)


def main(preview=None):
    ART.mkdir(parents=True, exist_ok=True)
    specs = json.loads((ROOT / "mods/hogwarts-tabs/bomb-run-override.json").read_text())["decks"]
    for spec in specs:
        deck(spec)
    props()
    zone_props()
    pickups()
    actors()
    for text, name, color in [
        ("SPELL RUN", "title", "#f0d99e"), ("CLEAR THE HALL", "mission", "#93c7b5"),
        ("ROOM SECURED", "victory", "#a8e0a5"), ("HEXED OUT", "defeat", "#ed948c"),
        ("ON STANDBY", "paused", "#f0d99e"),
    ]:
        lettering(text, name, color)
    if preview:
        overview(specs, preview)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ART, help="Destination for generated SVGs")
    parser.add_argument("--preview", type=Path, help="Optional eight-zone architecture PNG")
    args = parser.parse_args()
    ART = args.output
    main(args.preview)
