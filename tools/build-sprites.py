#!/usr/bin/env python3
"""Rebuild the fifteen 32×32 Harry Potter character sprites and spell effects. Standard library only.

Usage: python3 tools/build-sprites.py [--preview /tmp/hogwarts-sprites.png]
The optional contact sheet shows dark/light backgrounds and a 36px size check.
"""

import argparse
from html import escape
import json
from pathlib import Path
import struct
import zlib

SIZE = 32
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "mods/hogwarts-agents/sprites/hogwarts"
WEAPONS_DEST = DEST / "weapons"
INK = "#11151f"


class Sprite:
    def __init__(self, title, palette, width=SIZE, height=SIZE):
        self.title = title
        self.width = width
        self.height = height
        self.palette = {"K": INK, **palette}
        self.pixels = [[None] * width for _ in range(height)]

    def rect(self, x, y, w, h, color):
        assert color in self.palette, (self.title, color)
        assert 0 <= x < x + w <= self.width and 0 <= y < y + h <= self.height, (
            self.title, x, y, w, h, self.width, self.height
        )
        for row in self.pixels[y:y + h]:
            row[x:x + w] = [self.palette[color]] * w

    def stamp(self, x, y, rows):
        for dy, row in enumerate(rows):
            for dx, color in enumerate(row):
                if color != ".":
                    self.rect(x + dx, y + dy, 1, 1, color)

    def svg(self, display_w=36, display_h=36, mirror=False):
        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" '
            f'width="{display_w}" height="{display_h}" shape-rendering="crispEdges">',
            f"  <title>{escape(self.title)} — pixel art</title>",
        ]
        for y, row in enumerate(self.pixels):
            active = list(reversed(row)) if mirror else row
            x = 0
            while x < self.width:
                color = active[x]
                end = x + 1
                while end < self.width and active[end] == color:
                    end += 1
                if color:
                    lines.append(
                        f'  <rect x="{x}" y="{y}" width="{end - x}" '
                        f'height="1" fill="{color}"/>'
                    )
                x = end
        return "\n".join([*lines, "</svg>", ""])


BASE = {"F": "#efc09e", "s": "#c48c6a", "W": "#f8f6f0"}


def box(p, x, y, w, h, fill):
    p.rect(x, y, w, h, "K")
    p.rect(x + 1, y + 1, w - 2, h - 2, fill)


def body(title, palette, cape=False, head=True):
    p = Sprite(title, {**BASE, **palette})
    if cape:
        box(p, 6, 14, 20, 17, "C")
        p.rect(7, 15, 2, 15, "c")
        p.rect(23, 15, 2, 15, "c")
    box(p, 6, 16, 5, 10, "A")
    box(p, 21, 16, 5, 10, "A")
    p.rect(7, 17, 1, 7, "a")
    p.rect(7, 24, 3, 1, "F")
    p.rect(22, 24, 3, 1, "F")
    box(p, 10, 24, 6, 7, "L")
    box(p, 16, 24, 6, 7, "L")
    p.rect(11, 28, 4, 2, "B")
    p.rect(17, 28, 4, 2, "B")
    box(p, 9, 15, 14, 11, "A")
    p.rect(10, 16, 2, 8, "a")
    p.rect(10, 23, 12, 1, "T")
    if head:
        box(p, 10, 3, 12, 12, "F")
        p.rect(11, 4, 1, 9, "s")
        p.rect(13, 9, 2, 2, "K")
        p.rect(18, 9, 2, 2, "K")
        p.rect(13, 9, 1, 1, "W")
        p.rect(18, 9, 1, 1, "W")
        p.rect(15, 12, 3, 1, "s")
    return p


def hair(p, rows, x=10, y=2):
    p.stamp(x, y, rows)


def voldemort():
    # Lord Voldemort: pale bald serpent-like face, crimson eyes, flowing obsidian Death Eater robes.
    p = body("Lord Voldemort", {
        "F": "#dce3de", "s": "#aeb8b2", "A": "#212926", "a": "#141a18", "T": "#2f5940",
        "L": "#181f1d", "B": "#111614", "C": "#1b2420", "c": "#101614",
        "E": "#ff3848", "G": "#4ee680",
    }, cape=True, head=False)
    box(p, 10, 3, 12, 12, "F")
    p.rect(11, 4, 1, 10, "s")
    # Glowing crimson eyes & faint snake-slit nose.
    p.rect(12, 8, 3, 2, "K")
    p.rect(17, 8, 3, 2, "K")
    p.rect(13, 9, 2, 1, "E")
    p.rect(17, 9, 2, 1, "E")
    p.rect(15, 11, 1, 1, "s")
    p.rect(17, 11, 1, 1, "s")
    p.rect(14, 13, 4, 1, "s")
    # Emerald Death Eater lapel trim & dark magic glow at hands.
    p.rect(14, 16, 4, 7, "a")
    p.rect(13, 16, 1, 6, "T")
    p.rect(18, 16, 1, 6, "T")
    p.rect(7, 24, 3, 1, "G")
    p.rect(22, 24, 3, 1, "G")
    return p


def harry():
    # Harry Potter: messy black hair, lightning scar, round glasses, Gryffindor red/gold scarf, Hogwarts robe.
    p = body("Harry Potter", {
        "A": "#262a34", "a": "#171a22", "T": "#525866", "L": "#20242d", "B": "#181a20",
        "H": "#181a20", "h": "#323745", "R": "#b8242c", "G": "#f0c243",
    })
    # Messy dark hair with spiky fringe.
    hair(p, [
        ".K.KKKKKK.K.",
        ".KHHhHHHHHK.",
        "KHHHHHHHHHHK",
        "KHH..HH..HHK",
        "KH........HK",
    ])
    # Iconic lightning-bolt scar on forehead!
    p.stamp(13, 5, ["R.", "RR", ".R"])
    # Iconic round glasses!
    p.stamp(11, 8, ["KKKK..KKKK", "K..KKKK..K", "KKKK..KKKK"])
    p.rect(13, 9, 1, 1, "W")
    p.rect(19, 9, 1, 1, "W")
    # Gryffindor scarlet & gold striped scarf draped over Hogwarts robe.
    for idx, x in enumerate(range(10, 22, 2)):
        p.rect(x, 15, 2, 2, "R" if idx % 2 == 0 else "G")
    p.rect(18, 17, 2, 5, "R")
    p.rect(18, 18, 2, 1, "G")
    p.rect(18, 20, 2, 1, "G")
    return p


def hermione():
    # Hermione Granger: bushy chestnut wavy hair, Gryffindor scarf/tie, Hogwarts robes.
    p = body("Hermione Granger", {
        "F": "#f2c5a6", "s": "#c99272", "A": "#262a34", "a": "#171a22", "T": "#525866",
        "L": "#20242d", "B": "#181a20", "H": "#6e4226", "h": "#965e38",
        "R": "#b8242c", "G": "#f0c243", "S": "#d9d4c7",
    })
    # Bushy wavy chestnut hair framing face & shoulders.
    hair(p, [
        ".KKKKKKKKKK.",
        "KHHhHHHHhHHK",
        "KHHHHHHHHHHK",
        "KHH......HHK",
        "KHH......HHK",
    ])
    p.stamp(8, 5, ["KHK", "KHK", "KhK", "KHK", "KHK", "KHK", "KHK", "KK."])
    p.stamp(21, 5, ["KHK", "KHK", "KhK", "KHK", "KHK", "KHK", "KHK", ".KK"])
    # White collar + Gryffindor red/gold tie + gold emblem.
    p.rect(13, 15, 6, 3, "S")
    p.rect(15, 16, 2, 6, "R")
    p.rect(15, 18, 2, 1, "G")
    p.rect(15, 20, 2, 1, "G")
    p.rect(11, 17, 2, 2, "G")
    return p


def ron():
    # Ron Weasley: bright ginger hair, maroon Weasley sweater with gold 'R', Gryffindor trim.
    p = body("Ron Weasley", {
        "F": "#f4c9aa", "s": "#cf9574", "A": "#7d2229", "a": "#57151b", "T": "#4a382c",
        "L": "#2c313d", "B": "#2b211b", "H": "#d66024", "h": "#f0853e", "G": "#f2c94c",
    })
    hair(p, [
        "..KKKKKKKK..",
        ".KHHhHHHhHK.",
        "KHHHHHHHHHHK",
        "KHHH....HHHK",
        "KH........HK",
    ])
    # Iconic bright gold 'R' on his knitted maroon Weasley sweater!
    p.stamp(14, 17, [
        "GGG.",
        "G..G",
        "GGG.",
        "G.G.",
        "G..G",
    ])
    p.rect(11, 15, 10, 1, "G")
    return p


def dumbledore():
    # Albus Dumbledore: tall starry purple hat, half-moon glasses, long silver beard, purple & gold robes.
    p = body("Albus Dumbledore", {
        "A": "#5b3b8c", "a": "#3d2563", "T": "#e8bc43", "L": "#472c70", "B": "#2b1c45",
        "C": "#4c3078", "c": "#301d4f", "H": "#e6eaef", "h": "#b3bcc7", "G": "#f5cd56",
    }, cape=True)
    # Tall embroidered purple wizard hat with gold stars.
    p.stamp(9, 0, [
        "....KKKKKK....",
        "...KAAAGAAK...",
        "..KAAAAAAAAK..",
        ".KAGAAAAAGAAK.",
        "KKKKKKKKKKKKKK",
        ".KGGGGGGGGGGK.",
    ])
    # Half-moon glasses & cascading long silver-white beard!
    p.rect(12, 9, 8, 1, "G")
    p.rect(13, 9, 2, 2, "K")
    p.rect(18, 9, 2, 2, "K")
    p.rect(13, 9, 1, 1, "W")
    p.rect(18, 9, 1, 1, "W")
    p.stamp(10, 11, [
        "HH........HH",
        "HHHHHsHHHHHH",
        ".HHhHHHHhHH.",
        "..HHHHHHHH..",
        "..HHhHHhHH..",
        "...HHHHHH...",
        "....HHHH....",
        ".....HH.....",
    ])
    # Gold robe trim.
    p.rect(10, 21, 2, 2, "G")
    p.rect(20, 21, 2, 2, "G")
    return p


def snape():
    # Severus Snape: pale face, sleek black curtain hair, billowing high-collared black robes.
    p = body("Severus Snape", {
        "F": "#ebd4c3", "s": "#bda28e", "A": "#242730", "a": "#14161c", "T": "#3b404f",
        "L": "#1b1d24", "B": "#111318", "C": "#1a1c24", "c": "#101217", "H": "#14161c", "S": "#99a3b3",
    }, cape=True)
    # Sleek center-parted shoulder-length black hair.
    hair(p, [
        "..KKKKKKKK..",
        ".KHHHHHHHHK.",
        "KHHHH..HHHHK",
        "KHH......HHK",
        "KHH......HHK",
    ])
    p.stamp(9, 6, ["KHK", "KHK", "KHK", "KHK", "KHK", "KHK", "KHK", "KK."])
    p.stamp(20, 6, ["KHK", "KHK", "KHK", "KHK", "KHK", "KHK", "KHK", ".KK"])
    # High black collar & vertical row of silver coat buttons.
    p.rect(11, 14, 10, 2, "a")
    for y in (16, 18, 20, 22):
        p.rect(15, y, 2, 1, "S")
    return p


def hagrid():
    # Rubeus Hagrid: giant wide silhouette, shaggy brown hair & massive beard, heavy brown moleskin coat.
    p = Sprite("Rubeus Hagrid", {
        **BASE, "A": "#5e3d28", "a": "#3d2618", "l": "#7d5438", "T": "#2b211a",
        "H": "#332218", "h": "#523828", "P": "#e884a8", "G": "#d4a64a",
    })
    # Wide giant torso & massive boots.
    box(p, 3, 10, 26, 16, "A")
    box(p, 9, 24, 6, 7, "T")
    box(p, 17, 24, 6, 7, "T")
    box(p, 10, 3, 12, 11, "F")
    p.rect(4, 11, 5, 3, "l")
    p.rect(23, 11, 5, 3, "l")
    # Shaggy dark brown hair & giant bushy beard!
    p.stamp(8, 1, [
        "..KKKKKKKKKKKK..",
        ".KHHhHHHHHHhHHK.",
        "KHHHHHHHHHHHHHHK",
        "KHHH........HHHK",
        "KHH..........HHK",
        "KHH..........HHK",
    ])
    p.rect(13, 8, 2, 2, "K")
    p.rect(17, 8, 2, 2, "K")
    p.rect(13, 8, 1, 1, "W")
    p.rect(17, 8, 1, 1, "W")
    p.stamp(9, 10, [
        "HH..........HH",
        "HHHHHHsHHHHHHH",
        "HHhHHHHHHHHhHH",
        ".HHHHHHHHHHHH.",
        "..HHhHHHHhHH..",
        "...HHHHHHHH...",
        "....HHHHHH....",
    ])
    # Wide leather belt with brass buckle & huge hands.
    p.rect(4, 21, 24, 2, "T")
    p.rect(14, 21, 4, 2, "G")
    p.rect(4, 22, 4, 3, "F")
    p.rect(24, 22, 4, 3, "F")
    return p


def mcgonagall():
    # Prof. McGonagall: tall pointed black witch hat, spectacles, emerald tartan robes.
    p = body("Prof. McGonagall", {
        "F": "#f0c8ad", "s": "#c7997b", "A": "#1f6b47", "a": "#13472e", "T": "#e0b84c",
        "L": "#185236", "B": "#181a20", "C": "#1b2420", "c": "#101614",
        "H": "#252930", "h": "#8f98a6", "S": "#cfd6e0",
    }, cape=True)
    # Iconic tall pointed black witch hat!
    p.stamp(8, 0, [
        "......KKKK......",
        ".....KHHHHK.....",
        "....KHHHHHHK....",
        "...KHHHHHHHHK...",
        "..KHHAAAAAAHHK..",
        "KKKKKKKKKKKKKKKK",
    ])
    p.rect(10, 6, 2, 4, "h")
    p.rect(20, 6, 2, 4, "h")
    # Spectacles & tartan emerald trim.
    p.rect(12, 9, 8, 1, "S")
    p.rect(13, 9, 2, 2, "K")
    p.rect(18, 9, 2, 2, "K")
    p.rect(13, 9, 1, 1, "W")
    p.rect(18, 9, 1, 1, "W")
    p.rect(15, 16, 2, 2, "T")
    for y in (19, 21):
        p.rect(11, y, 10, 1, "a")
    return p


def sirius():
    # Sirius Black: wavy dark hair, goatee, charcoal Victorian coat & silver waistcoat.
    p = body("Sirius Black", {
        "A": "#323745", "a": "#1e222b", "T": "#6b543b", "L": "#252933", "B": "#181a20",
        "C": "#242833", "c": "#151820", "H": "#221d1b", "h": "#3d332f", "S": "#9ea8b8", "G": "#d9b452",
    }, cape=True)
    hair(p, [
        "..KKKKKKKK..",
        ".KHHhHHHhHK.",
        "KHHHHHHHHHHK",
        "KHH......HHK",
        "KHH......HHK",
    ])
    p.stamp(9, 6, ["KHK", "KHK", "KhK", "KHK", "KHK", "KK."])
    p.stamp(20, 6, ["KHK", "KHK", "KhK", "KHK", "KHK", ".KK"])
    # Scruffy dark goatee & waistcoat lapels.
    p.stamp(14, 12, ["HHHH", ".HH."])
    p.rect(13, 16, 6, 7, "S")
    p.rect(15, 16, 2, 7, "a")
    p.rect(15, 18, 2, 1, "G")
    return p


def draco():
    # Draco Malfoy: slicked-back platinum blonde hair, Slytherin emerald-and-silver scarf, Hogwarts robe.
    p = body("Draco Malfoy", {
        "F": "#f5d4bc", "s": "#cfa88e", "A": "#262a34", "a": "#171a22", "T": "#525866",
        "L": "#20242d", "B": "#181a20", "H": "#f2ecc9", "h": "#cfc69d",
        "G": "#228a4f", "S": "#d4dce3",
    })
    # Slicked-back pale platinum blonde hair.
    hair(p, [
        "..KKKKKKKK..",
        ".KHHhHHHHHK.",
        "KHHHHHHHHHHK",
        "KHHh....hHHK",
        "KH........HK",
    ])
    # Slytherin emerald & silver striped scarf!
    for idx, x in enumerate(range(10, 22, 2)):
        p.rect(x, 15, 2, 2, "G" if idx % 2 == 0 else "S")
    p.rect(18, 17, 2, 5, "G")
    p.rect(18, 18, 2, 1, "S")
    p.rect(18, 20, 2, 1, "S")
    return p


def luna():
    # Luna Lovegood: pale blonde hair, iconic pink & cyan Spectrespecs, Ravenclaw blue-bronze scarf.
    p = body("Luna Lovegood", {
        "F": "#f5d2ba", "s": "#cfa38a", "A": "#2a4475", "a": "#1c2f54", "T": "#b88246",
        "L": "#23355c", "B": "#4a3340", "H": "#f5e396", "h": "#d6be6b",
        "P": "#ff5ea8", "C": "#52e3ff", "U": "#2f5eb5", "O": "#c98b44",
    })
    hair(p, [
        "..KKKKKKKK..",
        ".KHHhHHHhHK.",
        "KHHHHHHHHHHK",
        "KHH......HHK",
        "KHH......HHK",
    ])
    p.stamp(8, 6, ["KHK", "KHK", "KhK", "KHK", "KHK", "KHK", "KHK", ".K."])
    p.stamp(21, 6, ["KHK", "KHK", "KhK", "KHK", "KHK", "KHK", "KHK", ".K."])
    # Iconic Spectrespecs (one pink lens, one cyan lens)!
    p.stamp(10, 8, [
        "KKKK..KKKK",
        "KPPKKKKCCK",
        "KPPK..KCCK",
        "KKKK..KKKK",
    ])
    # Ravenclaw blue & bronze striped scarf!
    for idx, x in enumerate(range(10, 22, 2)):
        p.rect(x, 15, 2, 2, "U" if idx % 2 == 0 else "O")
    p.rect(12, 17, 2, 5, "U")
    p.rect(12, 18, 2, 1, "O")
    p.rect(12, 20, 2, 1, "O")
    return p


def bellatrix():
    # Bellatrix Lestrange: towering wild tangled black curls, pale face, gothic plum-black corset dress.
    p = body("Bellatrix Lestrange", {
        "F": "#f0d4c7", "s": "#c4a395", "A": "#3b2238", "a": "#241322", "T": "#1a141c",
        "L": "#261624", "B": "#140c14", "C": "#241726", "c": "#140c17",
        "H": "#18161d", "h": "#3a3445", "P": "#b05ce6",
    }, cape=True)
    # Wild towering symmetric curly hair!
    p.stamp(8, 1, [
        "....KKK..KKK....",
        "..KKHHhKKhHHKK..",
        ".KHHHHHHHHHHHHK.",
        "KHHhHHHHHHHHhHHK",
        "KHHHH......HHHHK",
        "KHHH........HHHK",
        "KHH..........HHK",
        "KHK..........KHK",
        "KHK..........KHK",
        ".KK..........KK.",
    ])
    # Gothic corset lacing & dark magic violet glint.
    p.stamp(14, 16, ["P..P", ".PP.", "P..P", ".PP."])
    return p


def dobby():
    # Dobby: unmistakable huge pointy house-elf ears, big bright green eyes, tattered cream pillowcase & striped sock!
    p = Sprite("Dobby", {
        **BASE, "F": "#e8c4a6", "s": "#bf9678", "A": "#e8e0cf", "a": "#bfb59f",
        "E": "#48e66c", "R": "#d63e45", "G": "#f0c243",
    })
    # Huge pointy house-elf ears sticking far out on both sides!
    p.stamp(4, 7, [
        "KKK....",
        "KFFKK..",
        ".KsFFKK",
        "..KKssK",
        "....KKK",
    ])
    p.stamp(21, 7, [
        "....KKK",
        "..KKFFK",
        "KKFFsK.",
        "KssKK..",
        "KKK....",
    ])
    # Head with iconic large bright emerald-green eyes!
    box(p, 10, 4, 12, 12, "F")
    p.rect(11, 5, 1, 10, "s")
    p.rect(12, 8, 3, 3, "K")
    p.rect(17, 8, 3, 3, "K")
    p.rect(12, 9, 3, 2, "E")
    p.rect(17, 9, 3, 2, "E")
    p.rect(13, 9, 1, 1, "W")
    p.rect(18, 9, 1, 1, "W")
    p.rect(15, 12, 2, 1, "s")
    # Tattered cream pillowcase tunic & arms.
    box(p, 7, 17, 4, 8, "F")
    box(p, 21, 17, 4, 8, "F")
    box(p, 10, 15, 12, 11, "A")
    p.rect(11, 16, 2, 9, "a")
    p.rect(11, 24, 2, 1, "a")
    p.rect(18, 24, 3, 1, "a")
    # Bare foot on left, iconic bright striped FREE-ELF SOCK on right foot!
    box(p, 11, 25, 5, 6, "F")
    box(p, 16, 25, 5, 6, "R")
    p.rect(17, 27, 3, 1, "G")
    p.rect(17, 29, 3, 1, "G")
    return p


def hedwig():
    # Hedwig: snowy owl companion — crisp white feathers, dark flecks, golden owl eyes, orange talons.
    p = Sprite("Hedwig", {
        **BASE, "A": "#f5f7f8", "a": "#cfd8de", "d": "#525e69", "E": "#ffbf2e", "O": "#e69435",
    })
    # Round snowy owl head & oval feathered body with folded wings.
    box(p, 10, 4, 12, 10, "A")
    p.rect(11, 5, 2, 8, "a")
    # Large golden owl eyes & dark beak!
    p.rect(12, 7, 3, 3, "K")
    p.rect(17, 7, 3, 3, "K")
    p.rect(12, 8, 3, 2, "E")
    p.rect(17, 8, 3, 2, "E")
    p.rect(13, 8, 1, 1, "K")
    p.rect(18, 8, 1, 1, "K")
    p.rect(15, 10, 2, 2, "O")
    # Folded snowy wings (positioned so Spell Run gait flaps them!) & feathered chest.
    box(p, 6, 15, 5, 11, "A")
    box(p, 21, 15, 5, 11, "A")
    p.rect(7, 17, 2, 1, "d")
    p.rect(7, 20, 2, 1, "d")
    p.rect(23, 17, 2, 1, "d")
    p.rect(23, 20, 2, 1, "d")
    box(p, 10, 14, 12, 13, "A")
    p.rect(11, 15, 2, 11, "a")
    for x, y in [(14, 17), (18, 17), (16, 20), (13, 23), (18, 23)]:
        p.rect(x, y, 2, 1, "d")
    # Owl talons at y=27..30 so Spell Run walking gait steps cleanly!
    box(p, 11, 26, 4, 5, "O")
    box(p, 17, 26, 4, 5, "O")
    return p


def dementor():
    # Dementor: repeatable shadowy hooded wraith — tattered black cloak, icy void hood, skeletal hands.
    p = body("Dementor", {
        "F": "#9aa8b3", "s": "#6b7882", "A": "#1c202c", "a": "#10131c", "T": "#2f384a",
        "L": "#181c26", "B": "#2b3747", "C": "#151924", "c": "#0d1018", "E": "#68cce0",
    }, cape=True, head=False)
    # Deep shadowed wraith hood with faint chilling cyan glow inside void face.
    box(p, 8, 1, 16, 15, "C")
    p.rect(9, 2, 2, 13, "c")
    p.rect(21, 2, 2, 13, "c")
    box(p, 11, 5, 10, 10, "c")
    p.rect(14, 9, 4, 3, "a")
    p.rect(15, 10, 2, 1, "E")
    # Tattered shadowy shroud ribs & drifting cloak hem.
    for y in (17, 19, 21):
        p.rect(12, y, 8, 1, "T")
    p.rect(12, 28, 2, 2, "E")
    p.rect(18, 28, 2, 2, "E")
    return p


def build_weapons():
    """Build crisp 24×12 Harry Potter wand & spell effect SVGs (left + right pairs)."""
    WEAPONS_DEST.mkdir(parents=True, exist_ok=True)
    for old in WEAPONS_DEST.glob("*.svg"):
        old.unlink()

    def make(name, palette, rows):
        assert len(rows) == 12 and all(len(r) == 24 for r in rows), name
        for facing, mirror in (("right", False), ("left", True)):
            s = Sprite(f"{name} {facing}", palette, width=24, height=12)
            s.stamp(0, 0, rows)
            (WEAPONS_DEST / f"{name}-{facing}.svg").write_text(
                s.svg(display_w=48, display_h=24, mirror=mirror), encoding="utf-8"
            )

    def wand_beam(name, wood, core, glow):
        make(name, {"B": wood, "G": glow, "C": core, "W": "#ffffff"}, [
            "........................",
            "........................",
            ".............GG....GG...",
            "........GGGGGGGGGGGGG...",
            ".KKKKKKKGGCCCCCCCCCCGG..",
            "KBBBBBBBGWWWWWWWWWWWWCG.",
            "KBBBBBBBGWWWWWWWWWWWWCG.",
            ".KKKKKKKGGCCCCCCCCCCGG..",
            "........GGGGGGGGGGGGG...",
            "...............GG.......",
            "........................",
            "........................",
        ])

    # Iconic Harry Potter spells!
    wand_beam("expelliarmus", "#7a4a2b", "#ff5e66", "#d9202e")   # Harry: scarlet disarming jet
    wand_beam("petrificus",   "#8a5a36", "#78d9ff", "#388ee6")   # Hermione: azure-blue binding jet
    wand_beam("stupefy",      "#9c6438", "#ff9654", "#e0482b")   # Ron: crimson-amber stunner
    wand_beam("serpensortia", "#4f473e", "#78f0a4", "#229e52")   # Draco: emerald-silver jet
    wand_beam("transfigure",  "#5c4230", "#9effb4", "#2ea85d")   # McGonagall: emerald transfiguration
    wand_beam("patronus",     "#5c4d42", "#d9f4ff", "#78c8f0")   # Sirius: silver-blue Patronus mist

    # Voldemort's Avada Kedavra (jagged lethal emerald lightning from Elder Wand).
    make("dark-curse", {"B": "#cfc6b4", "G": "#1fb852", "L": "#6eff9c", "W": "#e6ffed"}, [
        "........................",
        "...........GG.....GG....",
        ".........GGLLGG.GGLLGG..",
        ".KKKKKKKGLLWWLLGLLWWLLG.",
        "KBBBBBBBGWWWWWWLWWWWWWLG",
        "KBBBBBBBGWWWWWWWWWWWWWLG",
        ".KKKKKKKGLLWWLLGLLWWLLG.",
        ".........GGLLGG.GGLLGG..",
        "...........GG.....GG....",
        "........................",
        "........................",
        "........................",
    ])

    # Dumbledore's Phoenix Flame (swirling golden-crimson phoenix fire).
    make("phoenix-fire", {"B": "#cfc6b4", "R": "#e0482b", "G": "#ffc842", "W": "#fff9d6"}, [
        "............RR..........",
        ".........RRGGGGRR.......",
        ".......RGWWWWWWGGRR.....",
        ".KKKKKKGWWGGGGWWGGGR....",
        "KBBBBBBGWWWWWWWWWWGGR...",
        "KBBBBBBGWWWWWWWWWWWGGR..",
        "KBBBBBBGWWWWWWWWWWGGR...",
        ".KKKKKKGWWGGGGWWGGGR....",
        ".......RGWWWWWWGGRR.....",
        ".........RRGGGGRR.......",
        "............RR..........",
        "........................",
    ])

    # Snape's Sectumsempra (razor silver-violet arcane slash).
    make("sectumsempra", {"B": "#2b2f3a", "V": "#9c66e6", "S": "#d4e0eb", "W": "#ffffff"}, [
        "........................",
        "........VVVVVVVV........",
        "......VVSSSSSSSSVV......",
        ".KKKKVSWWWWWWWWWWSSV....",
        "KBBBBVWWWWWWWWWWWWWSSV..",
        "KBBBBVSWWWWWWWWWWSSV....",
        ".KKKK..VVSSSSSSSSVV.....",
        ".........VVVVVVVV.......",
        "........................",
        "........................",
        "........................",
        "........................",
    ])

    # Hagrid's Pink Umbrella spark burst!
    make("umbrella-spark", {"P": "#e87aa2", "p": "#b84f76", "G": "#ffd154", "W": "#fff9db"}, [
        "..............GG........",
        "....KKKK....GGWWGG......",
        "...KPPPPK..GWWGGWWG.....",
        "..KPPPPPPKGWWWWWWWWG....",
        ".KPPppppPPKGGWWWWGG.....",
        "KPPPPPPPPPPKWWWWWWGG....",
        ".KPPppppPPKGGWWWWGG.....",
        "..KPPPPPPKGWWWWWWWWG....",
        "...KPPPPK..GWWGGWWG.....",
        "....KKKK....GGWWGG......",
        "..............GG........",
        "........................",
    ])

    # Luna's whimsical violet-cyan Spectrespecs charm.
    make("radish-charm", {"P": "#ff5ea8", "C": "#52e3ff", "W": "#ffffff"}, [
        "........................",
        "......PP.......CC.......",
        "....PPWWPP...CCWWCC.....",
        "...PWWWWWWPPCWWWWWWC....",
        "..PPWWPPWWCCWWCCWWCC....",
        "..PPWWWWWWWWWWWWWWCC....",
        "..PPWWPPWWCCWWCCWWCC....",
        "...PWWWWWWPPCWWWWWWC....",
        "....PPWWPP...CCWWCC.....",
        "......PP.......CC.......",
        "........................",
        "........................",
    ])

    # Bellatrix's jagged crimson-violet Crucio hex (dual-wielded!).
    make("crucio", {"R": "#d91c48", "V": "#b05ce6", "W": "#ffe0f0"}, [
        "........................",
        ".....VV........RR.......",
        "...VVWWVV....RRWWRR.....",
        "..VWWVVWWV..RWWVVWWR....",
        ".VWWRRRWWWVVWWWVVWWWR...",
        "VWWWWWWWWWWWWWWWWWWWWR..",
        "VWWWWWWWWWWWWWWWWWWWWR..",
        ".VWWRRRWWWVVWWWVVWWWR...",
        "..VWWVVWWV..RWWVVWWR....",
        "...VVWWVV....RRWWRR.....",
        ".....VV........RR.......",
        "........................",
    ])

    # Dobby's golden House-Elf Snap burst!
    make("elf-snap", {"G": "#f5be3b", "L": "#ffe77a", "W": "#ffffff"}, [
        "..........GG............",
        "........GGLLGG..........",
        ".....GGGLLWWLLGGG.......",
        "...GGLLLWWWWWWLLLGG.....",
        "..GLLWWWWWWWWWWWWLLG....",
        ".GLWWWWWWWWWWWWWWWWLG...",
        ".GLWWWWWWWWWWWWWWWWLG...",
        "..GLLWWWWWWWWWWWWLLG....",
        "...GGLLLWWWWWWLLLGG.....",
        ".....GGGLLWWLLGGG.......",
        "........GGLLGG..........",
        "..........GG............",
    ])

    # Dementor's icy Soul Chill wave.
    make("soul-chill", {"D": "#2e4659", "C": "#68cce0", "W": "#e0faff"}, [
        "........................",
        ".....DDDD....CCCC.......",
        "...DDCCCCDDDDWWWWCC.....",
        "..DCCWWWWCCCCWWWWWWC....",
        ".DCWWWWWWDDDDWWWWWWWC...",
        "DCWWWWWWWWWWWWWWWWWWWC..",
        "DCWWWWWWWWWWWWWWWWWWWC..",
        ".DCWWWWWWDDDDWWWWWWWC...",
        "..DCCWWWWCCCCWWWWWWC....",
        "...DDCCCCDDDDWWWWCC.....",
        ".....DDDD....CCCC.......",
        "........................",
    ])


def write_preview(sprites, path):
    backgrounds = [
        json.loads((ROOT / "themes" / f"{side}.json").read_text())["background"]
        for side in ["slytherin", "gryffindor"]
    ]
    width, height, cell = len(sprites) * 144, 424, 144
    rgb = lambda color: bytes.fromhex(color.lstrip("#"))
    rows = []
    for y in range(height):
        bg = backgrounds[y // (height // 2)]
        row = bytearray(rgb(bg) * width)
        local_y = y % (height // 2)
        for index, sprite in enumerate(sprites):
            for scale, top in [(4, 8), (1.125, 160)]:
                size = round(SIZE * scale)
                if not top <= local_y < top + size:
                    continue
                sy = int((local_y - top) / scale)
                left = index * cell + (cell - size) // 2
                for dx in range(size):
                    color = sprite.pixels[sy][int(dx / scale)]
                    if color:
                        row[(left + dx) * 3:(left + dx + 1) * 3] = rgb(color)
        rows.append(b"\0" + row)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
    Path(path).write_bytes(png + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()
    drawings = {
        "voldemort": voldemort, "harry": harry, "hermione": hermione, "ron": ron,
        "dumbledore": dumbledore, "snape": snape, "hagrid": hagrid, "mcgonagall": mcgonagall,
        "sirius": sirius, "draco": draco, "luna": luna, "bellatrix": bellatrix,
        "dobby": dobby, "hedwig": hedwig, "dementor": dementor,
    }
    DEST.mkdir(parents=True, exist_ok=True)
    for old in DEST.glob("*.svg"):
        old.unlink()
    characters = {name: draw() for name, draw in drawings.items()}
    for name, sprite in characters.items():
        (DEST / f"{name}.svg").write_text(sprite.svg(), encoding="utf-8")
    build_weapons()
    print(f"Built {len(characters)} Harry Potter character sprites and spell effects in {DEST}")
    if args.preview:
        write_preview(list(characters.values()), args.preview)
        print(f"Preview: {args.preview}")


if __name__ == "__main__":
    main()
