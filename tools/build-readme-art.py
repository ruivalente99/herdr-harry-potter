#!/usr/bin/env python3
"""Build self-contained SVG illustrations and layout thumbnail from real theme and artwork assets.

Usage: python3 tools/build-readme-art.py
Writes docs/images/overview.svg, arena.svg, spell-run.svg and layouts/hogwarts.svg.
Python standard library only.
"""

import base64
from html import escape
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/images/overview.svg"
ARENA = ROOT / "docs/images/arena.svg"
SPELL_RUN = ROOT / "docs/images/spell-run.svg"
LAYOUT_SVG = ROOT / "layouts/hogwarts.svg"
DECK = ROOT / "mods/hogwarts-tabs/bomb-run-override.json"
SPELL_ART = "mods/hogwarts-tabs/arcade"
SPRITES = "mods/hogwarts-agents/sprites/hogwarts"
SYMBOLS = {}


def rect(x, y, w, h, fill, radius=0, stroke="none"):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def text(x, y, value, fill, size=14, weight=400, extra=""):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" {extra}>{escape(value)}</text>'


THEME = {"light": "gryffindor", "dark": "slytherin"}


def speech_bubble(side, x, y, w, h, pointer, quote, t):
    radius = 9
    outline = (f"M{x + radius} {y} H{pointer - 8} L{pointer} {y - 10} L{pointer + 8} {y} "
               f"H{x + w - radius} Q{x + w} {y} {x + w} {y + radius} "
               f"V{y + h - radius} Q{x + w} {y + h} {x + w - radius} {y + h} "
               f"H{x + radius} Q{x} {y + h} {x} {y + h - radius} "
               f"V{y + radius} Q{x} {y} {x + radius} {y} Z")
    return (f'<g id="speech-bubble-{side}"><path d="{outline}" fill="{t["popover"]}" '
            f'stroke="{t["border"]}" stroke-width="1.5" stroke-linejoin="round"/>'
            + text(x + w / 2, y + 21, quote, t["foreground"], 12, 500, 'text-anchor="middle"') + "</g>")


def artwork(path, x, y, w, h=None):
    if path not in SYMBOLS:
        source = (ROOT / path).read_text()
        viewbox = ET.fromstring(source).attrib["viewBox"]
        body = re.sub(r"<title>.*?</title>", "", source[source.index(">") + 1:source.rindex("</svg>")], flags=re.S)
        symbol = f"art-{len(SYMBOLS)}"
        SYMBOLS[path] = (symbol, f'<symbol id="{symbol}" viewBox="{viewbox}">{body}</symbol>')
    symbol = SYMBOLS[path][0]
    return f'<use href="#{symbol}" x="{x}" y="{y}" width="{w}" height="{h or w}" shape-rendering="crispEdges"/>'


def sprite(hero, x, y, size=48):
    return artwork(f"{SPRITES}/{hero}.svg", x, y, size)


def window(side, x, realm, cards, duel, quote, speaker):
    palette = json.loads((ROOT / f"themes/{THEME[side]}.json").read_text())
    t = {**palette, **palette["colors"]}
    image = base64.b64encode((ROOT / f"backgrounds/realms/{THEME[side]}/{realm}.png").read_bytes()).decode()
    clip = f"window-{side}"
    out = [f'<g transform="translate({x} 148)">',
           f'<defs><clipPath id="{clip}">{rect(0, 0, 652, 500, "white", 14)}</clipPath></defs>',
           f'<g clip-path="url(#{clip})">',
           rect(0, 0, 652, 500, t["background"]),
           rect(0, 0, 652, 44, t["chrome"]), rect(0, 44, 210, 430, t["chrome"]),
           rect(210, 44, 1, 430, t["border"]), rect(0, 43, 652, 1, t["border"])]
    for i, color in enumerate([t["blocked"], t["working"], t["done"]]):
        out.append(f'<circle cx="{20 + i * 16}" cy="22" r="4" fill="{color}"/>')
    for label, px, w, on in [("Files", 448, 46, False), ("Changes", 500, 62, False), ("Spell Run", 568, 74, True)]:
        out += [rect(px, 11, w, 22, t["selected"] if on else t["chrome"], 6),
                text(px + w / 2, 26, label, t["foreground"] if on else t["muted"], 11, 600 if on else 400, 'text-anchor="middle"')]
    out += [text(84, 27, f"HERDR / {THEME[side].upper()} WORKSPACE", t["muted"], 12, 600),
            text(18, 77, "REALMS", t["dim"], 12, 600),
            rect(10, 91, 190, 51, t["selected"], 6),
            artwork("mods/hogwarts-systems/realms/gryffindor-tower.svg", 18, 101, 28),
            text(55, 111, "Hogwarts", t["foreground"], 15, 600),
            text(55, 131, "main · synced", t["dim"], 12),
            artwork("mods/hogwarts-systems/realms/hogwarts-express.svg", 18, 153, 28),
            text(55, 164, "Platform 9¾", t["muted"], 15),
            rect(0, 191, 210, 1, t["border"]), text(18, 215, "WIZARDS / 03", t["dim"], 12, 600)]
    for i, (hero, name, mood, role) in enumerate(cards):
        y = 228 + i * 79
        out += [rect(10, y, 190, 70, t["surface"], 7, t["border"]), sprite(hero, 16, y + 8),
                text(72, y + 24, name, t["foreground"], 13, 600),
                text(72, y + 43, mood, t[role], 11),
                rect(72, y + 54, 112, 3, t["border"], 1), rect(72, y + 54, 67 + i * 12, 3, t[role], 1)]
    out += [rect(222, 61, 416, 398, t["background"], 8, t["border"]),
            f'<image href="data:image/png;base64,{image}" x="223" y="100" width="414" height="358" preserveAspectRatio="xMidYMid slice" opacity="0.22"/>',
            text(238, 85, "hogwarts-castle", t["muted"], 13),
            rect(223, 98, 414, 1, t["border"]),
            text(238, 126, "CHARM / MISCHIEF MANAGED", t["accent"], 12, 600),
            text(238, 164, "$ herdr-app status", t["foreground"], 17, 600),
            text(238, 195, "layout   hogwarts", t["muted"], 14),
            text(238, 219, "wizards  3 casting spells", t["muted"], 14),
            text(238, 262, "Workspace ready.", t["done"], 18, 600),
            text(238, 285, "Owls dispatched. Wands at the ready.", t["dim"], 12),
            rect(238, 308, 384, 135, t["surface"], 6, t["border"]),
            text(250, 329, "DUELING CLUB / PRACTICE", t["accent"], 11, 600),
            sprite(duel[0], 318, 339), sprite(duel[1], 422, 339),
            artwork(f"{SPRITES}/weapons/{duel[2]}.svg", 351, 362, 50, 25),
            artwork(f"{SPRITES}/weapons/{duel[3]}.svg", 397, 362, 50, 25),
            speech_bubble(side, 246, 400, 368, 33, 342 if speaker == 0 else 446, quote, t),
            rect(0, 474, 652, 26, t["chrome"]),
            rect(0, 474, 652, 1, t["border"]),
            text(18, 491, "LOCAL / MAIN", t["dim"], 10, 600),
            text(622, 491, "3 CASTING SPELLS", t["working"], 10, 600, 'text-anchor="end"'),
            "</g>", rect(0.5, 0.5, 651, 499, "none", 14, t["border"]), "</g>"]
    return "\n".join(out)


def dark_theme():
    palette = json.loads((ROOT / "themes/slytherin.json").read_text())
    return {**palette, **palette["colors"]}


def page(width, height, title, desc, body):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" role="img" aria-labelledby="title description">',
        f'<title id="title">{escape(title)}</title>', f'<desc id="description">{escape(desc)}</desc>',
        "<defs>", *(markup for _, markup in SYMBOLS.values()), "</defs>", *body, "</svg>"]) + "\n"


def build_arena():
    SYMBOLS.clear()
    t = dark_theme()
    image = base64.b64encode((ROOT / "backgrounds/realms/slytherin/great-hall.png").read_bytes()).decode()
    fronts = [("01 / DARK ARTS", "harry", "voldemort", "expelliarmus-right", "dark-curse-left", "Harry Potter", "Lord Voldemort"),
              ("02 / WAND DUEL", "hermione", "draco", "petrificus-right", "serpensortia-left", "Hermione", "Draco Malfoy"),
              ("03 / DARK ARTS", "dumbledore", "snape", "phoenix-fire-right", "sectumsempra-left", "Dumbledore", "Snape")]
    body = [rect(0, 0, 840, 470, t["background"], 16),
            text(28, 46, "Harry Potter · Dueling Club", t["foreground"], 22, 700, 'font-family="Trebuchet MS, Verdana, sans-serif"'),
            text(28, 70, "Illustrated Wizarding World duel · no real agent actions", t["muted"], 12),
            text(812, 46, "ILLUSTRATION", t["done"], 11, 600, 'text-anchor="end" letter-spacing="1"')]
    for i, preset in enumerate(["Golden Trio", "Hogwarts", "Order", "Allies", "Custom"]):
        x = 28 + i * 94
        body += [rect(x, 88, 86, 26, t["surface"], 6, t["accent"] if preset == "Hogwarts" else t["border"]),
                 text(x + 43, 105, preset, t["accent"] if preset == "Hogwarts" else t["foreground"], 11, 500, 'text-anchor="middle"')]
    for i, (label, a, b, wa, wb, na, nb) in enumerate(fronts):
        x = 28 + i * 266
        clip = f"front-{i}"
        body += [f'<defs><clipPath id="{clip}">{rect(x, 132, 250, 230, "white", 10)}</clipPath></defs>',
                 f'<g clip-path="url(#{clip})">', rect(x, 132, 250, 230, "#0d1211"),
                 f'<image href="data:image/png;base64,{image}" x="{x}" y="132" width="250" height="230" preserveAspectRatio="xMidYMid slice" opacity="0.35"/>',
                 "</g>", rect(x + 0.5, 132.5, 249, 229, "none", 10, t["border"]),
                 text(x + 125, 160, label, t["accent"], 12, 600, 'text-anchor="middle"'),
                 sprite(a, x + 34, 226, 64), sprite(b, x + 152, 226, 64),
                 artwork(f"{SPRITES}/weapons/{wa}.svg", x + 88, 250, 40, 20),
                 artwork(f"{SPRITES}/weapons/{wb}.svg", x + 122, 250, 40, 20),
                 rect(x + 20, 298, 210, 1, t["border"]),
                 text(x + 66, 324, na, t["foreground"], 13, 500, 'text-anchor="middle"'),
                 text(x + 184, 324, nb, t["foreground"], 13, 500, 'text-anchor="middle"')]
    body += [sprite("voldemort", 28, 388, 44), rect(84, 382, 728, 56, t["popover"], 10, t["border"]),
             text(102, 404, "Lord Voldemort · Club", t["accent"], 11, 600),
             text(102, 426, "The Boy Who Lived... come to debug.", t["foreground"], 14)]
    ARENA.write_text(page(840, 470, "Harry Potter Dueling Club — illustration",
                          "Illustrated Dueling Club with three Wizarding World fronts, using the project's pixel-art characters and spells. Not a screenshot.", body), encoding="utf-8")
    print(f"Built {ARENA.relative_to(ROOT)}")


def build_spell_run():
    SYMBOLS.clear()
    t = dark_theme()
    potions = json.loads(DECK.read_text())["decks"][1]
    scale, ox, oy = 2, 24, 124
    tile = lambda c, r: (ox + c * 16 * scale, oy + (32 + r * 16) * scale)
    body = [rect(0, 0, 464, 640, t["background"], 14),
            rect(12, 14, 34, 28, t["surface"], 6), text(29, 33, "02", t["blocked"], 13, 600, 'text-anchor="middle"'),
            text(56, 34, "Potions Dungeon", t["foreground"], 16, 600),
            text(440, 34, "ILLUSTRATION", t["muted"], 10, 600, 'text-anchor="end" letter-spacing="1"'),
            text(24, 92, "Points", t["muted"], 11), text(70, 92, "0240", t["foreground"], 14, 600),
            text(232, 92, "Rivals 3/4", t["foreground"], 12, 500, 'text-anchor="middle"'),
            text(440, 92, "00:42", t["muted"], 13, 500, 'text-anchor="end"'),
            artwork(f"{SPELL_ART}/deck-potions.svg", ox, oy, 208 * scale, 224 * scale)]
    for r, row in enumerate(potions["layout"]):
        for c, cell in enumerate(row):
            if cell == "#" and 0 < r < len(potions["layout"]) - 1 and 0 < c < len(row) - 1:
                body.append(artwork(f"{SPELL_ART}/rack.svg", *tile(c, r), 16 * scale))
    for c, r in [(2, 1), (9, 3), (6, 5), (10, 7), (3, 9), (7, 9)]:
        body.append(artwork(f"{SPELL_ART}/crate-0.svg", *tile(c, r), 16 * scale, 18 * scale))
    for c in range(3, 8):
        body.append(artwork(f"{SPELL_ART}/blast-h-1.svg", *tile(c, 5), 16 * scale))
    body.append(artwork(f"{SPELL_ART}/cauldron-1.svg", *tile(5, 3), 16 * scale))
    for hero, c, r in [("harry", 1, 1), ("hagrid", 11, 1), ("dementor", 8, 3), ("dobby", 1, 9), ("voldemort", 11, 9)]:
        x, y = tile(c, r)
        body.append(sprite(hero, x - 4, y - 10, 40))
    body += [sprite("harry", 22, 586, 36), text(68, 600, "Harry Potter", t["foreground"], 13, 600),
             text(68, 618, "Prefect · 310 / 600", t["muted"], 11),
             rect(24, 630, 416, 3, t["border"], 1), rect(24, 630, 217, 3, t["accent"], 1)]
    SPELL_RUN.write_text(page(464, 640, "Spell Run — illustration",
                              "Illustrated Spell Run room built from the game's own pixel art: the Potions Dungeon, potion barrels, an exploding cauldron, a spell burst and the Harry Potter cast. Not a screenshot.", body), encoding="utf-8")
    print(f"Built {SPELL_RUN.relative_to(ROOT)}")


def build_layout_thumbnail():
    def inner(hero):
        src = (ROOT / f"{SPRITES}/{hero}.svg").read_text(encoding="utf-8")
        return src[src.index(">") + 1:src.rindex("</svg>")].strip()

    light = json.loads((ROOT / "themes/gryffindor.json").read_text())
    dark = json.loads((ROOT / "themes/slytherin.json").read_text())
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400" viewBox="0 0 640 400" font-family="system-ui, -apple-system, sans-serif">',
        '<title>Harry Potter — Gryffindor and Slytherin</title>',
        '<desc>One layout, two coordinated Wizarding World palettes. Warm parchment &amp; scarlet; dungeon slate &amp; emerald.</desc>',
    ]
    for offset, title, hero, p in [(0, "Gryffindor", "harry", light), (320, "Slytherin", "voldemort", dark)]:
        c = p["colors"]
        out += [
            f'<g transform="translate({offset} 0)">',
            f'<rect width="320" height="400" fill="{c["canvas"]}"/>',
            f'<text x="20" y="30" fill="{c["accent"]}" font-size="17" font-weight="600">{title}</text>',
            f'<rect x="12" y="48" width="296" height="336" rx="8" fill="{p["background"]}" stroke="{c["border"]}"/>',
            f'<path d="M20 48H86V384H20Q12 384 12 376V56Q12 48 20 48Z" fill="{c["chrome"]}"/>',
            f'<rect x="86" y="48" width="222" height="26" fill="{c["chrome"]}"/>',
            f'<rect x="96" y="55" width="104" height="14" rx="4" fill="{c["selected"]}"/>',
            f'<rect x="22" y="66" width="48" height="4" fill="{c["muted"]}"/>',
            f'<rect x="18" y="90" width="62" height="24" rx="5" fill="{c["selected"]}"/>',
            f'<rect x="24" y="98" width="9" height="9" fill="{c["accent"]}"/>',
            f'<rect x="39" y="100" width="33" height="4" fill="{c["muted"]}"/>',
            f'<rect x="24" y="127" width="9" height="9" fill="{c["dim"]}"/>',
            f'<rect x="39" y="129" width="29" height="4" fill="{c["dim"]}"/>',
            f'<path d="M12 181H86" stroke="{c["border"]}"/>',
            f'<rect x="22" y="193" width="33" height="4" fill="{c["dim"]}"/>',
            f'<rect x="18" y="210" width="62" height="58" rx="5" fill="{c["surface"]}" stroke="{c["border"]}"/>',
            f'<g transform="translate(22 215) scale(.8)">\n  {inner(hero)}\n</g>',
            f'<rect x="51" y="221" width="23" height="3" fill="{c["muted"]}"/>',
            f'<rect x="51" y="229" width="17" height="3" fill="{c["dim"]}"/>',
            f'<rect x="24" y="252" width="48" height="3" fill="{c["done"]}"/>',
            f'<rect x="94" y="83" width="206" height="282" rx="6" fill="{p["background"]}" stroke="{c["input"]}"/>',
            f'<rect x="103" y="95" width="94" height="3" fill="{c["dim"]}"/>',
            f'<path d="M94 108H300" stroke="{c["border"]}"/>',
            f'<rect x="106" y="125" width="122" height="4" fill="{p["foreground"]}"/>',
            f'<rect x="106" y="141" width="174" height="3" fill="{c["dim"]}"/>',
            f'<rect x="106" y="154" width="157" height="3" fill="{c["dim"]}"/>',
            f'<rect x="106" y="175" width="65" height="4" fill="{c["accent"]}"/>',
            f'<rect x="106" y="192" width="161" height="3" fill="{c["muted"]}"/>',
            f'<rect x="106" y="205" width="136" height="3" fill="{c["dim"]}"/>',
            f'<rect x="106" y="234" width="10" height="10" rx="2" fill="{c["done"]}"/>',
            f'<rect x="123" y="237" width="112" height="4" fill="{c["muted"]}"/>',
            f'<rect x="106" y="264" width="172" height="48" rx="4" fill="{c["raised"]}"/>',
            f'<rect x="114" y="275" width="139" height="3" fill="{c["muted"]}"/>',
            f'<rect x="114" y="288" width="103" height="3" fill="{c["dim"]}"/>',
            f'<rect x="106" y="331" width="5" height="11" fill="{c["accent"]}"/>',
            f'<rect x="86" y="373" width="214" height="10" fill="{c["chrome"]}"/>',
            '</g>',
        ]
    out.append('</svg>\n')
    LAYOUT_SVG.write_text("\n".join(out), encoding="utf-8")
    print(f"Built {LAYOUT_SVG.relative_to(ROOT)}")


def main():
    build_arena()
    build_spell_run()
    build_layout_thumbnail()
    SYMBOLS.clear()
    light = window("light", 48, "gryffindor-tower", [
        ("harry", "Harry Potter", "Casting spells", "working"),
        ("hermione", "Hermione", "Brewing potions", "working"),
        ("hedwig", "Hedwig", "Casting spells", "working"),
    ], ("harry", "draco", "expelliarmus-right", "serpensortia-left"), "My father will hear about this merge conflict!", 1)
    dark = window("dark", 740, "great-hall", [
        ("voldemort", "Lord Voldemort", "Casting spells", "working"),
        ("snape", "Severus Snape", "Deep enchantment", "working"),
        ("dobby", "Dobby", "Casting spells", "working"),
    ], ("dumbledore", "voldemort", "phoenix-fire-right", "dark-curse-left"), "The Boy Who Lived... come to debug.", 1)
    content = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="760" viewBox="0 0 1440 760" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" role="img" aria-labelledby="title description">',
        '<title id="title">Harry Potter for Herdr — one castle, two houses</title>',
        '<desc id="description">Illustrated Gryffindor and Slytherin workspaces using the project’s actual pixel-art Harry Potter characters, realm emblems, backdrops and theme colors. Not a screenshot.</desc>',
        "<defs>", *(markup for _, markup in SYMBOLS.values()), "</defs>",
        rect(0, 0, 1440, 760, "#101413", 20),
        text(48, 52, "YOUR AGENTS. THEIR SPELLS.", "#e0be70", 13, 600, 'letter-spacing="2"'),
        text(48, 109, "One castle. Two sides.", "#f2efe6", 40, 700, 'font-family="Trebuchet MS, Verdana, sans-serif"'),
        text(1392, 103, "HOGWARTS / HERDR", "#99a89e", 13, 500, 'text-anchor="end" letter-spacing="1"'),
        light, dark,
        rect(48, 675, 28, 3, "#c94242"), text(89, 682, "GRYFFINDOR", "#e8e3d8", 15, 600, 'letter-spacing="1"'),
        text(48, 708, "Warm parchment chrome. Gryffindor-scarlet accents.", "#b2aba0", 14),
        rect(740, 675, 28, 3, "#73cf9c"), text(781, 682, "SLYTHERIN", "#e8e3d8", 15, 600, 'letter-spacing="1"'),
        text(740, 708, "Dungeon slate panels. Slytherin-emerald accents.", "#99a89e", 14),
        text(720, 744, "ILLUSTRATED PREVIEW / ACTUAL PROJECT ARTWORK", "#8b968e", 10, 500, 'text-anchor="middle" letter-spacing="1"'),
        "</svg>",
    ]
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text("\n".join(content) + "\n", encoding="utf-8")
    print(f"Built {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
