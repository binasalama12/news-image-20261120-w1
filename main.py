#!/usr/bin/env python3
"""Atlas Fidelity — one-day front page, Friday 20 November 2026.

Written from scratch in this session: a 1600x1600 broadsheet that is
resized to 1024x1024 as entry.png. 48 stories, 7 regions, one hero row,
thirteen pictured panels, a dot-matrix world map with pins, a timeline
strip, a date-check box and a sources footer. All drawings are flat
PIL shapes made here; no photos, no external assets.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

W = H = 1600
MARGIN = 44
PAPER = (247, 243, 233)
INK = (26, 24, 20)
GREY = (96, 92, 84)
SOFT = (52, 50, 46)
ACCENT = (168, 32, 40)

DJV = "/usr/share/fonts/truetype/dejavu/"
LIB = "/usr/share/fonts/truetype/liberation/"


def sans(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(DJV + name, size)


def serif(size, bold=False, italic=False):
    if italic:
        name = "LiberationSerif-Italic.ttf"
    elif bold:
        name = "LiberationSerif-Bold.ttf"
    else:
        name = "LiberationSerif-Regular.ttf"
    try:
        return ImageFont.truetype(LIB + name, size)
    except OSError:
        return ImageFont.truetype(DJV + "DejaVuSerif-Bold.ttf", size)


def mono(size):
    return ImageFont.truetype(DJV + "DejaVuSansMono.ttf", size)


def wrap_lines(draw, text, font, max_width):
    """Split text into lines that fit max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, x, y, text, font, max_width, leading, fill, limit=None):
    lines = wrap_lines(draw, text, font, max_width)
    if limit is not None and len(lines) > limit:
        lines = lines[:limit]
        tail = lines[-1]
        while tail and draw.textlength(tail + "…", font=font) > max_width:
            tail = tail[:-1]
        lines[-1] = tail.rstrip() + "…"
    for i, line in enumerate(lines):
        draw.text((x, y + i * leading), line, font=font, fill=fill)
    return y + len(lines) * leading


def one_line(draw, text, font, max_width):
    if draw.textlength(text, font=font) <= max_width:
        return text
    clipped = text
    while clipped and draw.textlength(clipped + "…", font=font) > max_width:
        clipped = clipped[:-1]
    return clipped.rstrip() + "…"


def vgrad(draw, x, y, w, h, top, bottom, steps=16):
    for i in range(steps):
        t = i / steps
        col = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        draw.rectangle(
            [x, y + h * t, x + w, y + h * (t + 1.0 / steps) + 1], fill=col
        )


def speckled(width, height, base, seed=7, amp=7):
    """Paper sheet with a light random grain."""
    img = Image.new("RGB", (width, height), base)
    px = img.load()
    rng = random.Random(seed)
    for yy in range(height):
        for xx in range(width):
            if rng.random() < 0.30:
                n = rng.randint(-amp, amp)
                r, g, b = px[xx, yy]
                px[xx, yy] = (
                    max(0, min(255, r + n)),
                    max(0, min(255, g + n)),
                    max(0, min(255, b + n)),
                )
    return img


def disc(draw, cx, cy, r, colour):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour)


def skyline(draw, x, y, w, h, colour, seed, low=0.5):
    rng = random.Random(seed)
    bx = x + 2
    while bx < x + w - 8:
        bw = rng.randint(max(8, w // 26), max(12, w // 13))
        bh = h * (low - 0.3 + 0.55 * rng.random())
        draw.rectangle([bx, y + h - bh, bx + bw, y + h], fill=colour)
        bx += bw + rng.randint(1, 4)


def flag_us(draw, x, y, w, h):
    for i in range(5):
        fill = (178, 34, 52) if i % 2 == 0 else (240, 238, 232)
        draw.rectangle([x, y + h * i / 5, x + w, y + h * (i + 1) / 5], fill=fill)
    draw.rectangle([x, y, x + w * 0.45, y + h * 0.6], fill=(33, 71, 160))


def flag_cn(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
    draw.ellipse(
        [x + w * 0.10, y + h * 0.14, x + w * 0.30, y + h * 0.40],
        fill=(255, 222, 0),
    )


def flag_ru(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h / 3], fill=(240, 238, 232))
    draw.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(33, 71, 160))
    draw.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(200, 40, 40))


# ---------------------------------------------------------------------------
# Dot-matrix world map: coarse continent outlines in (lon, lat).
# ---------------------------------------------------------------------------

N_AMERICA = [
    (-168, 66), (-140, 70), (-120, 71), (-100, 69), (-90, 79), (-82, 70),
    (-78, 62), (-65, 50), (-55, 52), (-64, 44), (-70, 42), (-74, 39),
    (-76, 35), (-80, 31), (-81, 26), (-84, 22), (-87, 21), (-91, 19),
    (-96, 16), (-94, 17), (-87, 13), (-83, 9), (-86, 12), (-95, 16),
    (-101, 19), (-106, 22), (-111, 25), (-115, 30), (-121, 34),
    (-124, 41), (-125, 48), (-131, 55), (-150, 60), (-166, 60),
]
GREENLAND = [(-46, 60), (-32, 68), (-22, 70), (-19, 76), (-28, 82),
             (-48, 81), (-55, 73), (-53, 64)]
S_AMERICA = [
    (-79, 9), (-72, 12), (-63, 10), (-55, 6), (-50, 0), (-44, -3),
    (-35, -8), (-39, -18), (-46, -26), (-52, -33), (-58, -39), (-62, -41),
    (-65, -46), (-67, -51), (-68, -54), (-71, -54), (-73, -47), (-73, -37),
    (-71, -29), (-70, -19), (-75, -15), (-79, -8), (-81, -4), (-80, 1),
    (-77, 5),
]
EURASIA = [
    (-9, 37), (-9, 43), (-2, 44), (-9, 48), (-5, 50), (0, 51), (5, 53),
    (8, 56), (7, 58), (12, 56), (18, 56), (21, 60), (25, 60), (28, 63),
    (30, 66), (35, 65), (45, 67), (60, 69), (80, 70), (105, 71), (130, 71),
    (155, 71), (178, 69), (178, 65), (162, 61), (156, 55), (143, 54),
    (141, 50), (137, 46), (131, 43), (127, 40), (122, 38), (121, 34),
    (122, 30), (118, 27), (110, 24), (108, 19), (106, 14), (103, 7),
    (100, 9), (98, 14), (94, 17), (91, 22), (88, 22), (86, 20), (82, 16),
    (80, 13), (77, 8), (75, 13), (72, 19), (70, 22), (66, 25), (61, 25),
    (57, 26), (52, 27), (50, 29), (48, 30), (44, 29), (43, 33), (40, 36),
    (36, 36), (33, 36), (30, 36), (26, 38), (22, 37), (19, 40), (15, 38),
    (12, 39), (10, 37), (5, 37), (2, 37), (-2, 37),
]
AFRICA = [
    (-6, 35), (3, 37), (10, 37), (20, 32), (30, 31), (33, 30), (35, 28),
    (38, 23), (40, 19), (43, 12), (48, 11), (51, 11), (47, 4), (41, -4),
    (40, -14), (37, -21), (35, -27), (31, -29), (27, -34), (20, -35),
    (17, -32), (15, -26), (13, -19), (12, -13), (13, -8), (9, -3), (9, 3),
    (3, 6), (-4, 5), (-9, 5), (-14, 8), (-17, 13), (-17, 16), (-16, 21),
    (-15, 26), (-13, 29), (-10, 32),
]
AUSTRALIA = [
    (113, -22), (114, -29), (115, -34), (119, -35), (124, -33), (130, -32),
    (133, -32), (135, -35), (137, -35), (139, -37), (142, -38), (146, -38),
    (149, -37), (150, -36), (153, -31), (153, -26), (150, -22), (146, -19),
    (143, -15), (142, -11), (140, -13), (136, -12), (135, -15), (132, -11),
    (129, -13), (125, -14), (122, -17), (118, -20),
]
ISLANDS = [
    (-2.5, 53.5, 3.2, 3.0), (138, 37.5, 4.5, 3.2), (107, -6.5, 9.0, 2.6),
    (119, -2.0, 5.0, 3.2), (122, 13.5, 2.6, 3.6), (172, -41.5, 2.6, 2.2),
    (47, -19.0, 2.2, 4.2), (103, 1.5, 3.0, 2.0),
]
CONTINENTS = [N_AMERICA, GREENLAND, S_AMERICA, EURASIA, AFRICA, AUSTRALIA]


def _inside_poly(x, y, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside


def _is_land(lon, lat):
    for poly in CONTINENTS:
        if _inside_poly(lon, lat, poly):
            return True
    for cx, cy, rx, ry in ISLANDS:
        if ((lon - cx) / rx) ** 2 + ((lat - cy) / ry) ** 2 <= 1:
            return True
    return False


def draw_dot_map(draw, x, y, w, h, dot, land, sea=None, r=2):
    if sea:
        draw.rectangle([x, y, x + w, y + h], fill=sea)
    cols = int(w / (r * 2 + 2))
    rows = int(h / (r * 2 + 2))
    for i in range(cols):
        lon = -180 + 360 * (i + 0.5) / cols
        for j in range(rows):
            lat = 84 - 148 * (j + 0.5) / rows
            if _is_land(lon, lat):
                cx = x + (i + 0.5) * w / cols
                cy = y + (j + 0.5) * h / rows
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=land)
    return (x, y, w, h)


# ---------------------------------------------------------------------------
# Flat scene illustrations, one per story kind.
# ---------------------------------------------------------------------------

def paint_scene(draw, kind, x, y, w, h, seed=3):
    cx = x + w / 2
    cy = y + h / 2
    if kind == "storm":
        vgrad(draw, x, y, w, h, (24, 52, 66), (70, 110, 120))
        for i in range(3):
            r = h * (0.30 - i * 0.08)
            draw.arc(
                [cx - r, cy - r * 0.7 - h * 0.12, cx + r, cy + r * 0.7 - h * 0.12],
                start=20 + i * 40, end=300 + i * 30, fill=(220, 235, 240), width=5,
            )
        rng = random.Random(seed)
        for _ in range(26):
            sx = x + rng.random() * w
            sy = y + rng.random() * h * 0.7
            draw.line([sx, sy, sx - 5, sy + 12], fill=(170, 205, 220), width=2)
        for i in range(4):
            draw.arc(
                [x - w * 0.1 + i * w * 0.28, y + h * 0.78,
                 x + w * 0.25 + i * w * 0.28, y + h * 1.02],
                start=180, end=360, fill=(200, 225, 235), width=4,
            )
        draw.rectangle([x, y + h * 0.92, x + w, y + h], fill=(16, 40, 54))
    elif kind == "missile":
        vgrad(draw, x, y, w, h, (14, 18, 38), (52, 44, 66))
        skyline(draw, x, y + h * 0.30, w, h * 0.70, (10, 12, 24), seed, low=0.7)
        pts = [(x + w * 0.06, y + h * 0.16), (x + w * 0.34, y + h * 0.30),
               (x + w * 0.58, y + h * 0.52), (x + w * 0.76, y + h * 0.72)]
        draw.line(pts, fill=(255, 170, 60), width=4)
        sx, sy = pts[-1]
        for a in range(10):
            ang = math.radians(a * 36)
            draw.line([sx, sy, sx + math.cos(ang) * w * 0.07,
                       sy + math.sin(ang) * w * 0.07],
                      fill=(255, 120, 40), width=4)
        disc(draw, sx, sy, w * 0.03, (255, 90, 30))
        rng = random.Random(seed + 1)
        for _ in range(20):
            draw.point((x + rng.random() * w, y + rng.random() * h * 0.5),
                       fill=(220, 225, 245))
    elif kind == "summit":
        vgrad(draw, x, y, w, h, (70, 100, 150), (214, 196, 160))
        disc(draw, x + w * 0.84, y + h * 0.24, h * 0.11, (250, 214, 110))
        skyline(draw, x, y + h * 0.18, w, h * 0.82, (44, 56, 84), seed)
        for i, fn in enumerate((flag_us, flag_cn, flag_ru)):
            fx = x + w * (0.20 + 0.26 * i)
            draw.line([fx, y + h * 0.16, fx, y + h * 0.78],
                      fill=(235, 232, 225), width=3)
            fn(draw, fx + 2, y + h * 0.16, w * 0.15, h * 0.20)
        draw.rectangle([x, y + h * 0.86, x + w, y + h], fill=(30, 34, 48))
    elif kind == "bridge":
        vgrad(draw, x, y, w, h, (96, 120, 150), (170, 190, 205))
        draw.arc([x - w * 0.08, y + h * 0.22, x + w * 1.08, y + h * 1.05],
                 start=180, end=360, fill=(40, 44, 52), width=6)
        for i in range(5):
            fx = x + w * (0.12 + 0.19 * i)
            draw.line([fx, y + h * (0.55 - 0.10 * abs(i - 2)), fx, y + h * 0.86],
                      fill=(40, 44, 52), width=3)
        draw.rectangle([x, y + h * 0.86, x + w, y + h], fill=(38, 74, 110))
        sx, sy = x + w * 0.55, y + h * 0.34
        for a in range(8):
            ang = math.radians(a * 45)
            draw.line([sx, sy, sx + math.cos(ang) * w * 0.09,
                       sy + math.sin(ang) * w * 0.09],
                      fill=(255, 166, 0), width=4)
        disc(draw, sx, sy, w * 0.04, (255, 120, 40))
    elif kind == "apec":
        vgrad(draw, x, y, w, h, (60, 96, 140), (200, 210, 200))
        disc(draw, x + w * 0.16, y + h * 0.26, h * 0.12, (255, 226, 130))
        skyline(draw, x, y + h * 0.22, w, h * 0.78, (40, 58, 82), seed)
        for i, c in enumerate([(222, 41, 16), (33, 71, 160), (46, 140, 80),
                               (255, 200, 40), (150, 60, 160)]):
            fx = x + w * (0.14 + 0.17 * i)
            draw.line([fx, y + h * 0.30, fx, y + h * 0.66],
                      fill=(240, 238, 230), width=2)
            draw.polygon([(fx, y + h * 0.30), (fx + w * 0.10, y + h * 0.37),
                          (fx, y + h * 0.44)], fill=c)
    elif kind == "cop":
        vgrad(draw, x, y, w, h, (30, 80, 110), (90, 160, 140))
        disc(draw, cx, cy, h * 0.32, (64, 145, 200))
        draw.ellipse([cx - h * 0.16, cy - h * 0.20, cx + h * 0.05, cy - h * 0.02],
                     fill=(52, 168, 83))
        draw.ellipse([cx - h * 0.02, cy + h * 0.04, cx + h * 0.20, cy + h * 0.22],
                     fill=(52, 168, 83))
        draw.polygon([(cx + h * 0.08, cy - h * 0.30), (cx + h * 0.28, cy - h * 0.34),
                      (cx + h * 0.14, cy - h * 0.12)], fill=(52, 168, 83))
    elif kind == "court":
        vgrad(draw, x, y, w, h, (120, 116, 104), (196, 188, 168))
        for i in range(4):
            fx = x + w * (0.18 + 0.17 * i)
            draw.rectangle([fx, y + h * 0.32, fx + w * 0.07, y + h * 0.82],
                           fill=(238, 234, 224))
        draw.polygon([(x + w * 0.10, y + h * 0.30), (x + w * 0.90, y + h * 0.30),
                      (cx, y + h * 0.10)], fill=(238, 234, 224))
        draw.rectangle([x + w * 0.10, y + h * 0.82, x + w * 0.90, y + h * 0.88],
                       fill=(238, 234, 224))
        draw.line([x + w * 0.58, y + h * 0.62, x + w * 0.84, y + h * 0.40],
                  fill=(40, 36, 30), width=5)
        draw.rectangle([x + w * 0.80, y + h * 0.30, x + w * 0.94, y + h * 0.42],
                       fill=(40, 36, 30))
    elif kind == "chart":
        vgrad(draw, x, y, w, h, (250, 248, 244), (232, 226, 218))
        for i, bh in enumerate((0.30, 0.42, 0.36, 0.55, 0.48, 0.66, 0.60)):
            bx = x + w * (0.06 + 0.13 * i)
            draw.rectangle([bx, y + h * (1 - bh) - h * 0.08, bx + w * 0.08,
                            y + h * 0.92], fill=(190, 190, 186))
        pts = [(x + w * 0.06, y + h * 0.18), (x + w * 0.28, y + h * 0.30),
               (x + w * 0.44, y + h * 0.26), (x + w * 0.64, y + h * 0.52),
               (x + w * 0.90, y + h * 0.74)]
        draw.line(pts, fill=(178, 32, 40), width=6)
        draw.polygon([(x + w * 0.90, y + h * 0.74), (x + w * 0.78, y + h * 0.70),
                      (x + w * 0.86, y + h * 0.58)], fill=(178, 32, 40))
    elif kind == "game":
        vgrad(draw, x, y, w, h, (120, 40, 130), (255, 138, 76))
        disc(draw, cx, y + h * 0.52, h * 0.20, (255, 208, 110))
        skyline(draw, x, y + h * 0.10, w, h * 0.90, (18, 14, 36), seed)
        for px_ in (x + w * 0.13, x + w * 0.87):
            draw.line([px_, y + h, px_, y + h * 0.40], fill=(8, 24, 14), width=4)
            for a in range(6):
                ang = math.radians(195 + a * 26)
                draw.line([px_, y + h * 0.40,
                           px_ + math.cos(ang) * w * 0.075,
                           y + h * 0.40 + math.sin(ang) * w * 0.075],
                          fill=(8, 40, 20), width=3)
    elif kind == "voyager":
        draw.rectangle([x, y, x + w, y + h], fill=(8, 10, 26))
        rng = random.Random(seed + 7)
        for _ in range(40):
            draw.point((x + rng.random() * w, y + rng.random() * h),
                       fill=(225, 232, 250))
        draw.arc([x + w * 0.14, y + h * 0.20, x + w * 0.52, y + h * 0.80],
                 start=300, end=120, fill=(210, 214, 220), width=5)
        draw.line([x + w * 0.33, y + h * 0.50, x + w * 0.62, y + h * 0.24],
                  fill=(210, 214, 220), width=3)
        for rr in (0.10, 0.17, 0.24):
            draw.arc([x + w * (0.62 - rr), y + h * (0.24 - rr),
                      x + w * (0.62 + rr), y + h * (0.24 + rr)],
                     start=300, end=60, fill=(140, 200, 255), width=3)
    elif kind == "gavel":
        vgrad(draw, x, y, w, h, (104, 84, 60), (168, 148, 116))
        draw.line([x + w * 0.30, y + h * 0.66, x + w * 0.66, y + h * 0.30],
                  fill=(52, 38, 22), width=8)
        draw.rectangle([x + w * 0.58, y + h * 0.16, x + w * 0.80, y + h * 0.32],
                       fill=(52, 38, 22))
        draw.rectangle([x + w * 0.18, y + h * 0.78, x + w * 0.62, y + h * 0.86],
                       fill=(52, 38, 22))
    elif kind == "drought":
        vgrad(draw, x, y, w, h, (240, 200, 120), (214, 164, 96))
        disc(draw, x + w * 0.80, y + h * 0.24, h * 0.14, (255, 240, 170))
        draw.ellipse([x + w * 0.16, y + h * 0.52, x + w * 0.84, y + h * 0.94],
                     fill=(186, 138, 84))
        rng = random.Random(seed + 3)
        for _ in range(12):
            sx = x + w * (0.24 + rng.random() * 0.5)
            sy = y + h * (0.58 + rng.random() * 0.28)
            draw.line([sx, sy, sx + rng.randint(-30, 30), sy + rng.randint(4, 16)],
                      fill=(120, 86, 48), width=2)
    elif kind == "atom":
        vgrad(draw, x, y, w, h, (16, 22, 44), (36, 52, 88))
        disc(draw, cx, cy, h * 0.10, (255, 120, 90))
        for ang in (0, 60, 120):
            draw.arc([cx - w * 0.34, cy - h * 0.17, cx + w * 0.34, cy + h * 0.17],
                     start=ang, end=ang + 330, fill=(150, 200, 255), width=3)
        disc(draw, x + w * 0.22, y + h * 0.24, 4, (200, 230, 255))
        disc(draw, x + w * 0.78, y + h * 0.72, 4, (200, 230, 255))
    elif kind == "hands":
        vgrad(draw, x, y, w, h, (36, 66, 120), (90, 130, 170))
        flag_us(draw, x + w * 0.10, y + h * 0.20, w * 0.32, h * 0.30)
        draw.rectangle([x + w * 0.58, y + h * 0.20, x + w * 0.90, y + h * 0.50],
                       fill=(252, 209, 22))
        draw.rectangle([x + w * 0.58, y + h * 0.30, x + w * 0.90, y + h * 0.40],
                       fill=(0, 56, 147))
        draw.rectangle([x + w * 0.58, y + h * 0.40, x + w * 0.90, y + h * 0.50],
                       fill=(206, 17, 38))
        draw.arc([x + w * 0.36, y + h * 0.52, x + w * 0.64, y + h * 0.86],
                 start=0, end=180, fill=(240, 240, 235), width=4)
    elif kind == "ship":
        vgrad(draw, x, y, w, h, (70, 100, 128), (120, 150, 160))
        draw.polygon([(x, y + h * 0.26), (x + w * 0.30, y + h * 0.26),
                      (x + w * 0.22, y + h * 0.52), (x, y + h * 0.60)],
                     fill=(150, 120, 84))
        draw.polygon([(x + w, y + h * 0.30), (x + w * 0.72, y + h * 0.30),
                      (x + w * 0.80, y + h * 0.56), (x + w, y + h * 0.64)],
                     fill=(150, 120, 84))
        draw.rectangle([x, y + h * 0.60, x + w, y + h], fill=(36, 84, 124))
        draw.polygon([(x + w * 0.36, y + h * 0.62), (x + w * 0.68, y + h * 0.62),
                      (x + w * 0.62, y + h * 0.76), (x + w * 0.42, y + h * 0.76)],
                     fill=(28, 28, 28))
        draw.rectangle([x + w * 0.44, y + h * 0.48, x + w * 0.60, y + h * 0.62],
                       fill=(178, 44, 44))
    elif kind == "cricket":
        vgrad(draw, x, y, w, h, (52, 130, 66), (88, 166, 92))
        draw.rectangle([x + w * 0.42, y + h * 0.14, x + w * 0.58, y + h * 0.90],
                       fill=(216, 198, 150))
        for sx in (0.47, 0.53):
            for sy in (0.22, 0.78):
                draw.line([x + w * sx, y + h * sy, x + w * sx,
                           y + h * (sy + 0.08)], fill=(240, 240, 235), width=3)
        disc(draw, x + w * 0.68, y + h * 0.55, 6, (200, 30, 40))
        skyline(draw, x, y, w, h * 0.14, (30, 90, 44), seed)
    else:
        vgrad(draw, x, y, w, h, (90, 100, 120), (170, 178, 190))
        disc(draw, cx, cy, h * 0.16, (255, 220, 120))


# ---------------------------------------------------------------------------
# The day's stories.
# ---------------------------------------------------------------------------

DATE_LONG = "Friday 20 November 2026"

TIMELINE = [
    ("Overnight", "Crimean Bridge hit a third time"),
    ("~06:00 UTC", "APEC leaders meet in Shenzhen"),
    ("~10:00 UTC", "Trilateral declaration issued"),
    ("~12:00 UTC", "Akvan makes landfall in Odisha"),
    ("~14:00 UTC", "Houthi missile hits Riyadh KAFD"),
    ("Late", "Wall Street slides; Dow -1,084"),
]

HEROES = [
    {
        "region": "ASP", "kicker": "1 · ODISHA · STORM",
        "headline": "Akvan comes ashore on the Odisha coast",
        "dek": "Cyclone Akvan crossed the coast near Gopalpur at noon, "
               "winds 90-100 km/h gusting to 110. Three hundred thousand "
               "people are out of harm's way, 423 rescue teams deployed, "
               "red alerts in 11 districts.",
        "source": "IMD · The Hindu", "kind": "storm",
    },
    {
        "region": "MID", "kicker": "2 · RIYADH · ATTACK",
        "headline": "Houthi missile hits Riyadh's KAFD financial district",
        "dek": "A Houthi missile damaged a wealth-fund tower in the "
               "financial district, one of Riyadh's tallest. No casualties "
               "are reported, as air defences answered the strike.",
        "source": "Arab News · Reuters", "kind": "missile",
    },
    {
        "region": "ASP", "kicker": "3 · SHENZHEN · DIPLOMACY",
        "headline": "Trump, Xi and Putin issue a joint declaration",
        "dek": "No big peace deal from the trilateral's second day. Trump "
               "says the Iran war call waits until 2027, rates the summit "
               "'12 out of 10', and Putin may attend December's G20 in Miami.",
        "source": "Reuters · AP", "kind": "summit",
    },
]

# Each pictured story: region, kicker, headline, dek, source, scene kind,
# and (optional) map pin as fractions of the map box.
PICTURED = [
    ("EUR", "4 · KERCH STRAIT · WAR",
     "Crimean Bridge hit a third time this week; rail halted",
     "A Ukrainian naval drone strike disrupted rail traffic on the bridge. "
     "Rail partly resumes; Putin vows retaliation, and Kyiv was hit by drones.",
     "CLAIM · Kyiv", "bridge", 0.60, 0.26),
    ("ASP", "5 · SHENZHEN · SUMMIT", "APEC leaders meet in Shenzhen",
     "Leaders gather in China for the APEC summit. Xi urges APEC economies "
     "to back open trade and new technology.",
     "AP", "apec", 0.83, 0.43),
    ("EUR", "6 · ANTALYA · CLIMATE",
     "COP31's final day: fossil fuels cut from the text",
     "A revised draft strips out every fossil-fuel phase-out pledge. "
     "Delegates push back as the final plenary meets today.",
     "UNFCCC · AFP", "cop", 0.58, 0.32),
    ("EUR", "7 · THE HAGUE · LAW", "The world answers the genocide verdict",
     "Britain expels Myanmar's defence attache and seeks an urgent Security "
     "Council meeting. The Gambia hails a 'historic' verdict.",
     "AP · BBC", "court", 0.50, 0.21),
    ("AME", "8 · NEW YORK · MARKETS", "Anthropic's debut can't stop the slide",
     "The Dow fell 1,084 points, the S&P 2.02% and the Nasdaq 2.25%, as the "
     "AI selloff bit a day after Anthropic's record debut.",
     "Bloomberg", "chart", 0.28, 0.28),
    ("AME", "9 · VICE CITY · GAMES", "GTA VI passes The Odyssey's $1.84bn",
     "Launch-day sales top The Odyssey's $1.80bn global run, Sensor Tower "
     "estimates. Reviews land; Rockstar calls it the highest-rated game ever.",
     "Sensor Tower", "game", 0.27, 0.38),
    ("WLD", "10 · SPACE · SCIENCE",
     "NASA confirms Voyager 1's light-day milestone",
     "The probe is now a full light-day from Earth - 16 billion miles out, "
     "the farthest any human-made object has ever travelled.",
     "NASA · JPL", "voyager", None, None),
    ("ASP", "11 · SEOUL · LAW", "South Korea clears ex-PM Han",
     "The Supreme Court overturns former prime minister Han Duck-soo's "
     "conviction, in the case tied to the 2024 martial-law declaration.",
     "Korea Times", "gavel", 0.85, 0.31),
    ("OCE", "12 · SUVA · CLIMATE", "Fiji declares a national disaster over drought",
     "Fiji declares a national disaster over drought and water shortages. "
     "El Nino leaves water short across the islands.",
     "AFP", "drought", 0.91, 0.57),
    ("ASP", "13 · VIENNA · SECURITY",
     "North Korea expands uranium enrichment at Yongbyon",
     "The UN watchdog reports growth at the nuclear site, in its latest "
     "assessment of the Yongbyon complex.",
     "IAEA", "atom", 0.83, 0.33),
    ("AME", "14 · CARACAS · DIPLOMACY",
     "US and Venezuela restore military cooperation",
     "The two countries sign an agreement to work together again, restoring "
     "a military channel closed for years.",
     "Reuters", "hands", 0.30, 0.52),
    ("MID", "15 · HORMUZ · CONFLICT",
     "ADNOC vessel attacked in the Strait of Hormuz",
     "One crew member is missing after the strike on the ADNOC vessel in "
     "the strait.",
     "Reuters", "ship", 0.62, 0.45),
    ("OCE", "16 · WELLINGTON · CRICKET",
     "Day two at the Basin: Nicholls' 113 anchors New Zealand",
     "New Zealand build on Henry Nicholls' unbeaten 113 as India hunt early "
     "wickets, in the first Test at the Basin Reserve.",
     "AP", "cricket", 0.89, 0.64),
]

BRIEFS = [
    ("EUR", "BRUSSELS", "EU-UK summit opens"),
    ("ASP", "NEW DELHI", "Modi meets William and Kate"),
    ("ASP", "DHAKA", "Fire at the Yunus home; arson feared"),
    ("ASP", "MUMBAI", "Sensex +1.21%, Nifty +1.14% on the day"),
    ("ASP", "TOKYO", "Hayabusa2 gives up landing; mission rewritten"),
    ("EUR", "BERLIN", "Coalition of the Willing meets in Berlin"),
    ("EUR", "BERLIN", "Merz hosts Qatar's emir in Berlin"),
    ("ASP", "NEW DELHI", "Pakistan minister leads delegation to Delhi for SCO"),
    ("ASP", "MANILA", "Philippines-Chile trade deal signed"),
    ("ASP", "MANILA", "Musk plans Philippines projects"),
    ("ASP", "HONG KONG", "India beats Malaysia, Asian Hockey Trophy opens"),
    ("ASP", "IPOH", "Harimau Shakti exercise opens in Ipoh"),
    ("ASP", "NEW DELHI", "India's electronics exports jump 44%"),
    ("ASP", "NEW DELHI", "ICMR completes 100 tech transfers"),
    ("ASP", "NEW DELHI", "India unveils its first bird-flu vaccine"),
    ("WLD", "GENEVA", "World Children's Day marked worldwide"),
    ("EUR", "EUROPE", "Youth anti-war protests across Europe"),
    ("EUR", "BRUSSELS", "EU delays its methane rules by 24 months"),
    ("EUR", "COLOGNE", "Bayern Munich beat Koln 3-0"),
    ("WLD", "U17 CUP", "Argentina 0-2 Australia at the U17 Cup"),
    ("AME", "WASHINGTON", "Jobless claims come in at 203,000"),
    ("EUR", "STRASBOURG", "NATO's assembly opens its 72nd session"),
    ("ASP", "HANOI", "Azerbaijan's Aliyev visits Vietnam"),
    ("MID", "MARKETS", "Crude futures fall over 3%"),
    ("AFR", "KHARTOUM", "Sudan army: two-year El Obeid siege broken"),
    ("AFR", "MOGADISHU", "Somalia gives UAE ambassador 72 hours to leave"),
    ("AME", "SAN SALVADOR", "Migrant boat capsizes off El Salvador; dozens missing"),
    ("AME", "PORT-AU-PRINCE", "Haiti approves Salvadoran troop deal vs gangs"),
    ("WLD", "ARABIAN SEA", "Amur falcons cross the Arabian Sea"),
    ("AME", "NEW YORK", "Al-Saadi appears in a New York court over a UK plot"),
    ("EUR", "KYIV", "Witkoff and Kushner brief Zelenskyy"),
    ("ASP", "BEIJING", "Xi urges APEC to back open trade, new tech"),
]

REGION_NAMES = {"EUR": "EUROPE", "AME": "THE AMERICAS", "ASP": "ASIA-PACIFIC",
                "MID": "MIDEAST", "AFR": "AFRICA", "OCE": "OCEANIA",
                "WLD": "WORLD"}
REGION_ORDER = ["EUR", "AME", "ASP", "MID", "AFR", "OCE", "WLD"]
REGION_COLOURS = {"EUR": (38, 84, 150), "AME": (46, 140, 80),
                  "ASP": (178, 44, 44), "MID": (196, 132, 36),
                  "AFR": (122, 82, 160), "OCE": (36, 148, 168),
                  "WLD": (96, 96, 96)}

DATE_CHECK = (
    "Left out - they broke before Friday: the ICJ genocide ruling on Myanmar "
    "itself (Thursday 19 Nov) - Friday's news is the world's answer to it - "
    "Denmark's Greenland-US pact (19 Nov) - Anthropic's $81.34bn IPO (19 Nov); "
    "its first trading day was Thursday - Germany's electricity-tax cut "
    "(18 Nov) - the Crimean Bridge span collapse (17-18 Nov). "
    "Not yet: the trilateral's first meeting was 19 Nov; the joint "
    "declaration is Friday's."
)

FOOTER_ONE = ("Every story here happened, or was first reported, on Friday "
              "20 November 2026, in some time zone. Disputed claims are "
              "attributed, not stated as fact.")
FOOTER_TWO = ("Sources: Reuters - AP - AFP - BBC - Bloomberg - IMD - NASA - "
              "IAEA - The Hindu - Arab News - Sensor Tower. Original "
              "drawings, drawn for this page.")


# ---------------------------------------------------------------------------
# Panel and section renderers.
# ---------------------------------------------------------------------------

def region_counts():
    counts = {}
    for story in HEROES:
        counts[story["region"]] = counts.get(story["region"], 0) + 1
    for story in PICTURED:
        counts[story[0]] = counts.get(story[0], 0) + 1
    for brief in BRIEFS:
        counts[brief[0]] = counts.get(brief[0], 0) + 1
    return counts


def paint_region_strip(draw, x, y, w, h, counts):
    regs = [r for r in REGION_ORDER if counts.get(r)]
    total = sum(counts[r] for r in regs)
    cx = x
    for reg in regs:
        seg = w * counts[reg] / total
        draw.rectangle([cx, y, cx + seg, y + h], fill=REGION_COLOURS[reg])
        label = "%s %d" % (REGION_NAMES[reg], counts[reg])
        font = sans(21, bold=True)
        if draw.textlength(label, font=font) <= seg - 10:
            draw.text((cx + seg / 2, y + h / 2), label, font=font,
                      anchor="mm", fill=(255, 255, 255))
        cx += seg


def paint_panel(draw, x, y, w, region, kicker, headline, dek, source, kind,
                scene_h, seed, head_size=27, dek_size=18, dek_lines=3):
    paint_scene(draw, kind, x, y, w, scene_h, seed)
    yy = y + scene_h + 8
    draw.rectangle([x, yy + 2, x + 10, yy + 20], fill=REGION_COLOURS[region])
    draw.text((x + 16, yy), kicker, font=sans(19, bold=True), fill=INK)
    if source:
        src = source.upper()
        used = draw.textlength(kicker, font=sans(19, bold=True)) + 22
        if used + draw.textlength(src, font=sans(16, bold=True)) + 8 <= w:
            draw.text((x + w, yy), src, font=sans(16, bold=True),
                      anchor="ra", fill=GREY)
    yy += 26
    yy = draw_wrapped(draw, x, yy, headline, serif(head_size, bold=True), w,
                      int(head_size * 1.12), INK, limit=2)
    yy += 2
    draw_wrapped(draw, x, yy, dek, serif(dek_size), w, int(dek_size * 1.18),
                 SOFT, limit=dek_lines)


def paint_timeline(draw, x, y, w):
    draw.rectangle([x, y, x + 128, y + 54], fill=ACCENT)
    draw.text((x + 64, y + 15), "THE DAY", font=sans(20, bold=True),
              anchor="ma", fill=(255, 255, 255))
    draw.text((x + 64, y + 37), "IN UTC", font=sans(20, bold=True),
              anchor="ma", fill=(255, 255, 255))
    seg = (w - 140) // 6
    for i, (when, what) in enumerate(TIMELINE):
        sx = x + 140 + i * seg
        draw.text((sx, y + 2), when, font=sans(19, bold=True), fill=ACCENT)
        draw_wrapped(draw, sx, y + 26, what, sans(17), seg - 8, 20, INK,
                     limit=2)


def paint_bottom(draw, y):
    draw.text((MARGIN, y), "WHERE IT HAPPENED", font=sans(22, bold=True),
              fill=ACCENT)
    draw.text((500, y),
              "ALSO ON FRIDAY 20 NOVEMBER - %d MORE STORIES" % len(BRIEFS),
              font=sans(22, bold=True), fill=ACCENT)
    box = draw_dot_map(draw, MARGIN, y + 32, 440, 240, 4, (120, 130, 140),
                       sea=(16, 32, 52), r=2)
    bx, by, bw, bh = box
    for story in PICTURED:
        fx, fy = story[6], story[7]
        if fx is None:
            continue
        px = bx + fx * bw
        py = by + fy * bh
        num = story[1].split(" ")[0]
        draw.ellipse([px - 13, py - 13, px + 13, py + 13], fill=(200, 40, 40))
        draw.text((px, py), num, font=sans(17, bold=True), anchor="mm",
                  fill=(255, 255, 255))
    x0, y0 = 500, y + 34
    colw = (W - MARGIN - x0 - 32) // 3
    per = (len(BRIEFS) + 2) // 3
    for ci in range(3):
        for ri, brief in enumerate(BRIEFS[ci * per:(ci + 1) * per]):
            n = 17 + ci * per + ri
            bx2, by2 = x0 + ci * (colw + 16), y0 + ri * 22
            draw.ellipse([bx2, by2 + 5, bx2 + 8, by2 + 13],
                         fill=REGION_COLOURS[brief[0]])
            txt = "%d %s - %s" % (n, brief[1], brief[2])
            draw.text((bx2 + 14, by2),
                      one_line(draw, txt, sans(16), colw - 14),
                      font=sans(16), fill=INK)


def paint_date_check(draw, x, y, w):
    draw.rectangle([x, y, x + w, y + 86], outline=ACCENT, width=3)
    draw.rectangle([x, y, x + 168, y + 86], fill=ACCENT)
    draw.text((x + 84, y + 43), "DATE CHECK", font=sans(24, bold=True),
              anchor="mm", fill=(255, 255, 255))
    draw_wrapped(draw, x + 184, y + 10, DATE_CHECK, serif(20), w - 200, 24,
                 INK, limit=3)
    return y + 86


def paint_footer(draw, x, y, w):
    draw.text((x, y), FOOTER_ONE, font=serif(20, italic=True), fill=SOFT)
    draw.text((x, y + 26), FOOTER_TWO, font=sans(18), fill=GREY)


# ---------------------------------------------------------------------------
# Full page.
# ---------------------------------------------------------------------------

def build_page():
    img = speckled(W, H, PAPER, seed=7)
    draw = ImageDraw.Draw(img)
    counts = region_counts()
    total = len(HEROES) + len(PICTURED) + len(BRIEFS)

    draw.text((MARGIN, 24), "ONE DAY OF WORLD NEWS, ONE PICTURE",
              font=sans(22, bold=True), fill=ACCENT)
    draw.text((W - MARGIN, 24),
              "%d STORIES - 7 REGIONS - EVERY ONE FROM THIS FRIDAY" % total,
              font=sans(22, bold=True), anchor="ra", fill=INK)
    draw.line([MARGIN, 56, W - MARGIN, 56], fill=INK, width=3)
    draw.text((MARGIN, 64), DATE_LONG, font=serif(102, bold=True), fill=INK)

    paint_timeline(draw, MARGIN, 186, W - 88)
    paint_region_strip(draw, MARGIN, 252, W - 88, 34, counts)

    hero_w = (W - 88 - 24) // 3
    for i, hero in enumerate(HEROES):
        hx = MARGIN + i * (hero_w + 12)
        paint_panel(draw, hx, 300, hero_w, hero["region"], hero["kicker"],
                    hero["headline"], hero["dek"], hero["source"],
                    hero["kind"], 126, 3 + i, head_size=27, dek_size=18,
                    dek_lines=3)

    draw.line([MARGIN, 590, W - MARGIN, 590], fill=INK, width=2)
    rows = [(PICTURED[:5], 5), (PICTURED[5:9], 4), (PICTURED[9:], 4)]
    yy = 596
    for row, n in rows:
        pw = (W - 88 - (n - 1) * 12) // n
        for i, story in enumerate(row):
            paint_panel(draw, MARGIN + i * (pw + 12), yy, pw, story[0],
                        story[1], story[2], story[3], story[4], story[5],
                        62, 10 + i, head_size=21, dek_size=16, dek_lines=2)
        yy += 182

    paint_bottom(draw, 1150)
    paint_date_check(draw, MARGIN, 1428, W - 88)
    paint_footer(draw, MARGIN, 1528, W - 88)
    return img


def main():
    page = build_page()
    page = page.resize((1024, 1024), Image.LANCZOS)
    page.save("entry.png")


if __name__ == "__main__":
    main()
