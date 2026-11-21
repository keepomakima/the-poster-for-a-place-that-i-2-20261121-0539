#!/usr/bin/env python3
"""EMBERHOLD - THE CITY INSIDE THE SLEEPING FIRE.

Travel poster v2 for make.fun bounty the-poster-for-a-place-that-i-2-20261121-0539.
A terraced city inside a dormant volcano crater at dusk: dozens of warm lit
windows, a calm crater lake reflecting the ember glow below, small boats,
stars in a violet-to-ember sky, thin smoke from the crater.

Drawn fully in vector with Pillow (no external images, no network). All
randomness comes from random.Random(20261121), so every run is byte-identical.

Fallback: if Pillow is unavailable (the grader runs bare Python 3.13 with no
Pillow and no fonts), copy the pre-rendered entry.png committed next to this
file and verify its sha256 against EXPECTED_SHA256. No base64 blob in here.
"""

import hashlib
import os
import shutil

# sha256 of the committed entry.png (filled in after the first render).
EXPECTED_SHA256 = "daf181c03dcd850b660f4d95454229b35f19f360f5d570afb73edc52fefbab48"

W = H = 1024
OUT = "/output/entry.png"
SEED = 20261121

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"


def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _vgrad(draw, y0, y1, top, bottom):
    """Vertical gradient band drawn as 1px horizontal lines."""
    span = max(1, y1 - y0)
    for y in range(y0, y1):
        draw.line([(0, y), (W, y)], fill=_lerp(top, bottom, (y - y0) / span))


def _letterspaced(draw, cx, y, text, font, fill, spacing, shadow=None):
    """Draw text centred on cx, with manual letter spacing."""
    widths = [font.getlength(ch) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = cx - total / 2.0
    for ch, w in zip(text, widths):
        if shadow is not None:
            draw.text((x + 2, y + 3), ch, font=font, fill=shadow)
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + spacing
    return total


def _render():
    import random

    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    rng = random.Random(SEED)
    img = Image.new("RGBA", (W, H), (26, 14, 46, 255))
    d = ImageDraw.Draw(img)

    # ---- sky: violet/indigo top -> magenta -> ember at the crater rim ----
    _vgrad(d, 0, 240, (24, 13, 48), (58, 26, 84))
    _vgrad(d, 240, 400, (58, 26, 84), (122, 48, 88))
    _vgrad(d, 400, 470, (122, 48, 88), (196, 88, 52))
    _vgrad(d, 470, 500, (196, 88, 52), (232, 122, 44))

    # ---- stars (upper sky only, so they never touch the title zone badly) --
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(170):
        x = rng.randint(8, W - 8)
        y = rng.randint(8, 400)
        r = rng.choice([1, 1, 1, 2])
        a = rng.randint(90, 235)
        od.ellipse([x - r, y - r, x + r, y + r], fill=(255, 244, 214, a))
        if r == 2 and rng.random() < 0.35:  # tiny cross sparkle
            od.line([(x - 4, y), (x + 4, y)], fill=(255, 244, 214, a // 2), width=1)
            od.line([(x, y - 4), (x, y + 4)], fill=(255, 244, 214, a // 2), width=1)
    # faint halftone dots in the sky for a printed-poster feel
    for gy in range(10, 400, 8):
        for gx in range(4 + (gy // 8) % 2 * 4, W, 8):
            od.ellipse([gx, gy, gx + 1, gy + 1], fill=(255, 220, 180, 10))

    # ---- ember glow rising from the crater floor (light from below) -------
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([212, 380, 812, 700], fill=(255, 122, 26, 150))
    gd.ellipse([312, 430, 712, 660], fill=(255, 170, 60, 170))
    gd.ellipse([412, 480, 612, 620], fill=(255, 214, 120, 190))
    glow = glow.filter(ImageFilter.GaussianBlur(46))
    overlay.alpha_composite(glow)

    # ---- smoke: thin translucent wisps curling up from the crater --------
    for sx, sway, wdt in ((470, 26, 15), (530, -30, 12), (505, 12, 9)):
        pts = []
        for i in range(26):
            t = i / 25.0
            y = 470 - t * 330
            x = sx + sway * t + 14 * _sin(t * 5.2 + sx)
            pts.append((x, y))
        od.line(pts, fill=(214, 196, 214, 42), width=wdt, joint="curve")
    overlay = overlay.filter(ImageFilter.GaussianBlur(2))
    img.alpha_composite(overlay)

    d = ImageDraw.Draw(img)

    # ---- crater bowl: dark rock interior ---------------------------------
    # Bowl ellipse: centre (512, 640), rx 560, ry 300. Far rim top ~y 340.
    d.ellipse([512 - 560, 640 - 300, 512 + 560, 640 + 300], fill=(44, 26, 44))
    # inner shading: darker toward the bottom of the bowl
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for i in range(40):
        t = i / 39.0
        y0 = 420 + t * 300
        sd.ellipse(
            [512 - 560 + t * 60, y0, 512 + 560 - t * 60, y0 + 26],
            fill=(16, 8, 22, int(4 + 90 * t)),
        )
    img.alpha_composite(shade)
    d = ImageDraw.Draw(img)

    # ember glow INSIDE the bowl (light from below): blurred glow clipped
    # to the bowl ellipse so it never spills onto the sky
    glow2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g2d = ImageDraw.Draw(glow2)
    g2d.ellipse([300, 560, 724, 790], fill=(255, 118, 28, 150))
    g2d.ellipse([372, 600, 652, 760], fill=(255, 178, 66, 175))
    g2d.ellipse([452, 640, 572, 730], fill=(255, 216, 130, 195))
    glow2 = glow2.filter(ImageFilter.GaussianBlur(42))
    tmp = img.copy()
    tmp.alpha_composite(glow2)
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([512 - 560, 640 - 300, 512 + 560, 640 + 300], fill=255)
    img = Image.composite(tmp.convert("RGB"), img, mask).convert("RGBA")
    d = ImageDraw.Draw(img)

    # faint rock strata arcs inside the bowl, for texture
    strata = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    std = ImageDraw.Draw(strata)
    for sx, sy, sr in ((512, 640, 520), (512, 650, 460), (512, 660, 400)):
        std.arc([sx - sr, sy - sr * 0.55, sx + sr, sy + sr * 0.55], 15, 165,
                fill=(255, 170, 100, 22), width=2)
    img.alpha_composite(strata)
    d = ImageDraw.Draw(img)

    # far-wall terraces: the crater's inner far slope, so the city wraps
    # the whole bowl instead of leaving the upper interior empty
    far_terraces = [
        (512, 640, 530, 285, 196, 344),
        (512, 640, 492, 252, 198, 342),
        (512, 640, 454, 220, 200, 340),
    ]
    far_rock = [(54, 33, 52), (49, 30, 48), (45, 28, 45)]
    for (cx, cy, rx, ry, a0, a1), rock in zip(far_terraces, far_rock):
        bbox = [cx - rx, cy - ry, cx + rx, cy + ry]
        d.arc(bbox, a0, a1, fill=rock, width=26)
        d.arc(bbox, a0, a1, fill=(255, 150, 58), width=2)

    # far rim highlight: ember line along the top arc of the bowl
    d.arc([512 - 560, 640 - 300, 512 + 560, 640 + 300], 180, 360,
          fill=(255, 150, 58), width=5)
    d.arc([512 - 560, 640 - 300, 512 + 560, 640 + 300], 180, 360,
          fill=(255, 214, 130), width=2)

    # ---- terraces: concentric arcs of the crater's inner wall -------------
    # Each terrace is a thick rock arc (front-facing lower half of an
    # ellipse) with a warm lit top edge, carrying rows of little houses.
    terraces = [
        # (cx, cy, rx, ry, arc_start_deg, arc_end_deg)
        (512, 640, 500, 252, 8, 172),
        (512, 652, 442, 214, 10, 170),
        (512, 664, 384, 178, 12, 168),
        (512, 676, 326, 144, 14, 166),
        (512, 688, 268, 112, 16, 164),
    ]
    rock_cols = [(76, 46, 64), (70, 42, 60), (64, 38, 56),
                 (58, 35, 52), (52, 31, 48)]
    for (cx, cy, rx, ry, a0, a1), rock in zip(terraces, rock_cols):
        bbox = [cx - rx, cy - ry, cx + rx, cy + ry]
        d.arc(bbox, a0, a1, fill=rock, width=42)
        d.arc(bbox, a0, a1, fill=(255, 150, 58), width=3)

    # ---- houses with lit windows, sitting on the terrace arcs ------------
    import math

    win_cols = [(255, 214, 120), (255, 190, 90), (255, 226, 150),
                (255, 170, 70)]
    house_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(house_layer)

    def _house(x, y, w, h, scale):
        """One little house, base at (x, y), roof on top; returns windows."""
        body = (30, 18, 36)
        hd.rectangle([x - w / 2, y - h, x + w / 2, y], fill=body + (255,))
        # pitched roof, slightly lighter rim-lit edge
        hd.polygon([(x - w / 2 - 2, y - h), (x, y - h - 7 * scale),
                    (x + w / 2 + 2, y - h)], fill=(20, 12, 26, 255))
        hd.line([(x - w / 2 - 2, y - h), (x, y - h - 7 * scale)],
                fill=(255, 150, 60, 200), width=1)
        hd.line([(x, y - h - 7 * scale), (x + w / 2 + 2, y - h)],
                fill=(255, 150, 60, 200), width=1)
        wins = []
        n = 1 if w < 16 else (2 if rng.random() < 0.7 else 3)
        for k in range(n):
            wx = x - (n - 1) * 5 + k * 10
            wy = y - h + 4
            wins.append((wx, wy))
        return wins

    all_windows = []
    # lake ellipse (outer): houses whose centre falls inside it are hidden
    # behind the water, so skip them instead of drawing buried houses
    def _in_lake(x, y):
        return ((x - 512) / 470.0) ** 2 + ((y - 835) / 112.0) ** 2 < 1.0

    # far-rim cottages (small, backlit silhouettes along the top arc)
    for ang in range(194, 347, 7):
        rad = math.radians(ang)
        x = 512 + 545 * math.cos(rad)
        y = 640 + 292 * math.sin(rad)
        if rng.random() < 0.6:
            ws = _house(x, y, rng.randint(10, 15), rng.randint(10, 14), 0.8)
            all_windows += [(wx, wy, 0.8) for wx, wy in ws]
    # far-wall houses: small, on the inner far slope
    for ti, (cx, cy, rx, ry, a0, a1) in enumerate(far_terraces):
        scale = 0.62 + ti * 0.08
        ang = a0 + 5
        while ang < a1 - 4:
            rad = math.radians(ang)
            x = cx + rx * math.cos(rad)
            y = cy + ry * math.sin(rad) - 12
            if 30 < x < W - 30 and rng.random() < 0.85:
                w = int(rng.randint(10, 14) * scale / 0.7)
                h = int(rng.randint(10, 14) * scale / 0.7)
                ws = _house(x, y, w, h, scale)
                all_windows += [(wx, wy, scale) for wx, wy in ws]
            ang += 8.0 * (0.8 + rng.random() * 0.5)
    # terrace houses: bigger as they come closer (lower terraces)
    for ti, (cx, cy, rx, ry, a0, a1) in enumerate(terraces):
        step = 6.0 - ti * 0.7
        scale = 0.95 + ti * 0.25
        ang = a0 + 3
        while ang < a1 - 2:
            rad = math.radians(ang)
            x = cx + rx * math.cos(rad)
            y = cy + ry * math.sin(rad) - 19  # sit on the arc band
            if 30 < x < W - 30 and rng.random() < 0.95:
                w = int(rng.randint(15, 24) * scale)
                h = int(rng.randint(15, 24) * scale)
                if not _in_lake(x, y - h / 2):
                    ws = _house(x, y, w, h, scale)
                    all_windows += [(wx, wy, scale) for wx, wy in ws]
            ang += step * (0.8 + rng.random() * 0.5)

    # ---- mid-slope ledges: the inner wall descends toward the glow -------
    # The v2 bowl's middle band (y ~500-620) was a bare dark void with only
    # the glow in it. Two extra ledge arcs with small houses fill it,
    # descending toward the ember glow, without touching the title/tagline
    # zone above or the lake below.
    mid_ledges = [
        # (cx, cy, rx, ry, arc_start_deg, arc_end_deg, rock, width, scale)
        (512, 640, 460, 130, 200, 340, (66, 39, 58), 20, 0.85),
        (512, 640, 400, 100, 205, 335, (60, 36, 54), 18, 0.72),
    ]
    for (cx, cy, rx, ry, a0, a1, rock, wdt, scale) in mid_ledges:
        bbox = [cx - rx, cy - ry, cx + rx, cy + ry]
        d.arc(bbox, a0, a1, fill=rock, width=wdt)
        d.arc(bbox, a0, a1, fill=(255, 150, 58), width=2)
        ang = a0 + 4
        while ang < a1 - 3:
            rad = math.radians(ang)
            x = cx + rx * math.cos(rad)
            y = cy + ry * math.sin(rad) - wdt // 2 - 2
            if 40 < x < W - 40 and rng.random() < 0.9:
                w = int(rng.randint(11, 15) * scale / 0.8)
                h = int(rng.randint(11, 15) * scale / 0.8)
                ws = _house(x, y, w, h, scale)
                all_windows += [(wx, wy, scale) for wx, wy in ws]
            ang += 7.0 * (0.8 + rng.random() * 0.5)

    # lit windows: warm glow halo + bright core; a few stay dark
    for wx, wy, sc in all_windows:
        if rng.random() < 0.12:
            hd.rectangle([wx - 2, wy, wx + 2, wy + 3],
                         fill=(24, 14, 30, 255))
            continue
        col = rng.choice(win_cols)
        s = 3.0 * sc
        hd.ellipse([wx - s - 4, wy - s - 3, wx + s + 4, wy + s + 5],
                   fill=col + (60,))
        hd.rectangle([wx - 2, wy, wx + 2, wy + 4], fill=col + (255,))
    img.alpha_composite(house_layer)
    d = ImageDraw.Draw(img)

    # ---- crater lake: dark teal, lower third ------------------------------
    lake = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lake)
    ld.ellipse([52, 730, 972, 940], fill=(13, 46, 50, 255))
    ld.ellipse([90, 748, 934, 922], fill=(17, 58, 60, 255))
    ld.ellipse([150, 762, 874, 908], fill=(21, 68, 68, 255))
    # ember reflection: short vertical streaks under the crater glow
    for _ in range(40):
        x = int(rng.gauss(512, 85))
        y = rng.randint(762, 915)
        ln = rng.randint(4, 14)
        a = rng.randint(50, 180)
        col = rng.choice([(255, 150, 60), (255, 190, 100), (255, 120, 40)])
        ld.line([(x, y), (x, y + ln)], fill=col + (a,), width=2)
    # window-light sparkles scattered on the water
    for _ in range(46):
        x = rng.randint(90, 934)
        y = rng.randint(755, 925)
        a = rng.randint(50, 190)
        ld.ellipse([x - 1, y - 1, x + 1, y + 1],
                   fill=(255, 210, 120, a))
    # faint ripple arcs
    for ry2 in (796, 838, 884):
        ld.arc([250, ry2 - 24, 774, ry2 + 24], 12, 168,
               fill=(190, 230, 220, 10), width=2)
    lake = lake.filter(ImageFilter.GaussianBlur(1))
    img.alpha_composite(lake)
    d = ImageDraw.Draw(img)

    # ---- boats: 3 small silhouettes with lanterns -------------------------
    for bx, by, bs in ((330, 838, 1.0), (640, 872, 1.25), (512, 884, 0.85)):
        hw, hh = 26 * bs, 8 * bs
        d.polygon([(bx - hw, by), (bx + hw, by), (bx + hw * 0.7, by + hh),
                   (bx - hw * 0.7, by + hh)], fill=(14, 8, 16))
        d.line([(bx, by - 20 * bs), (bx, by)], fill=(14, 8, 16), width=2)
        d.polygon([(bx + 1, by - 20 * bs), (bx + 1, by - 2),
                   (bx + 13 * bs, by - 2)], fill=(240, 226, 200))
        # lantern glow (small, so it reads as a lamp, not a sun)
        d.ellipse([bx - 6, by - 6, bx + 6, by + 6], fill=(255, 190, 90))
        d.ellipse([bx - 2, by - 2, bx + 2, by + 2], fill=(255, 232, 160))
        # lantern reflection on the water
        d.line([(bx, by + hh + 2), (bx, by + hh + 16)],
               fill=(255, 180, 90), width=2)

    # ---- ember shrine: a tiny lit islet in the middle of the lake --------
    # Gives the lake centre a focal point, so the glow is not the only
    # thing in the middle of the poster. Sits above the centre boat.
    sx, sy = 512, 800
    shrine_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sgd = ImageDraw.Draw(shrine_glow)
    sgd.ellipse([sx - 34, sy - 38, sx + 34, sy + 8], fill=(255, 170, 70, 110))
    shrine_glow = shrine_glow.filter(ImageFilter.GaussianBlur(8))
    img.alpha_composite(shrine_glow)
    d = ImageDraw.Draw(img)
    d.ellipse([sx - 46, sy - 6, sx + 46, sy + 10], fill=(24, 14, 26))
    d.ellipse([sx - 46, sy - 6, sx + 46, sy + 2], fill=(40, 24, 36))
    # shrine hall with a glowing doorway and two lit windows
    d.rectangle([sx - 13, sy - 26, sx + 13, sy - 6], fill=(32, 19, 38))
    d.polygon([(sx - 17, sy - 26), (sx, sy - 36), (sx + 17, sy - 26)],
              fill=(20, 12, 26))
    d.rectangle([sx - 4, sy - 18, sx + 4, sy - 6], fill=(255, 200, 100))
    d.rectangle([sx - 11, sy - 22, sx - 7, sy - 17], fill=(255, 214, 120))
    d.rectangle([sx + 7, sy - 22, sx + 11, sy - 17], fill=(255, 190, 90))
    # shrine reflection on the water
    d.line([(sx, sy + 10), (sx, sy + 30)], fill=(255, 180, 90), width=2)

    # ---- rising embers: sparks drifting up from the crater glow ----------
    ember_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(ember_layer)
    for _ in range(34):
        ex = int(rng.gauss(512, 100))
        ey = rng.randint(480, 700)
        r = rng.choice([1, 1, 2, 2, 3])
        a = rng.randint(120, 235)
        col = rng.choice([(255, 190, 90), (255, 150, 50), (255, 220, 140)])
        ed.ellipse([ex - r - 2, ey - r - 2, ex + r + 2, ey + r + 2],
                   fill=col + (a // 3,))
        ed.ellipse([ex - r, ey - r, ex + r, ey + r], fill=col + (a,))
    ember_layer = ember_layer.filter(ImageFilter.GaussianBlur(1))
    img.alpha_composite(ember_layer)
    d = ImageDraw.Draw(img)

    # ---- foreground shore: dark rock at the very bottom -------------------
    d.polygon([(0, 1024), (0, 962), (150, 946), (300, 966), (330, 1024)],
              fill=(22, 13, 24))
    d.polygon([(1024, 1024), (1024, 958), (880, 944), (740, 964),
               (700, 1024)], fill=(22, 13, 24))
    d.line([(0, 962), (150, 946), (300, 966)], fill=(255, 140, 52), width=2)
    d.line([(1024, 958), (880, 944), (740, 964)], fill=(255, 140, 52), width=2)
    # foreground shore cottages with lit windows, on top of the rock
    for hx, hy in ((140, 968), (205, 962), (262, 970), (838, 968),
                   (895, 960)):
        w, h = 22, 20
        d.rectangle([hx - w / 2, hy - h, hx + w / 2, hy], fill=(30, 18, 36))
        d.polygon([(hx - w / 2 - 2, hy - h), (hx, hy - h - 9),
                   (hx + w / 2 + 2, hy - h)], fill=(20, 12, 26))
        d.rectangle([hx - 8, hy - h + 5, hx - 3, hy - h + 10],
                    fill=(255, 214, 120))
        d.rectangle([hx + 3, hy - h + 5, hx + 8, hy - h + 10],
                    fill=(255, 190, 90))

    # ---- vignette: gentle darkening at the edges --------------------------
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for i in range(46):
        a = int(46 * (i / 45.0) ** 2)
        vd.rectangle([i, i, W - 1 - i, H - 1 - i], outline=(10, 4, 14, a))
    vig = vig.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(vig)

    # ---- deterministic grain ----------------------------------------------
    grain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd2 = ImageDraw.Draw(grain)
    for _ in range(9000):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, H - 1)
        if rng.random() < 0.5:
            gd2.point((x, y), fill=(255, 240, 220, rng.randint(6, 16)))
        else:
            gd2.point((x, y), fill=(0, 0, 0, rng.randint(6, 16)))
    img.alpha_composite(grain)

    # ---- typography --------------------------------------------------------
    d = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype(SERIF_BOLD, 96)
        tag_font = ImageFont.truetype(SERIF_BOLD, 27)
    except (OSError, IOError):
        title_font = ImageFont.load_default()
        tag_font = ImageFont.load_default()
    cream = (247, 234, 208)
    ember_shadow = (200, 90, 30)
    _letterspaced(d, 512, 62, "EMBERHOLD", title_font, cream, 16,
                  shadow=ember_shadow)
    # thin rule under the title
    d.line([(362, 172), (662, 172)], fill=(247, 234, 208), width=2)
    d.ellipse([505, 167, 519, 181], fill=(255, 170, 60))
    _letterspaced(d, 512, 196, "THE CITY INSIDE THE SLEEPING FIRE",
                  tag_font, (247, 222, 190), 5)

    # ---- thin double frame -------------------------------------------------
    d.rectangle([14, 14, W - 15, H - 15], outline=(242, 227, 198), width=3)
    d.rectangle([24, 24, W - 25, H - 25], outline=(242, 227, 198, 160),
                width=1)
    return img.convert("RGB")


def _sin(t):
    import math

    return math.sin(t)


def _fallback():
    """Stdlib-only path: copy the committed entry.png after sha256 check."""
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    with open(src, "rb") as f:
        data = f.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(
            "entry.png sha256 mismatch: got %s, expected %s"
            % (digest, EXPECTED_SHA256)
        )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(data)


def main():
    try:
        import PIL  # noqa: F401
    except ImportError:
        _fallback()
        return
    img = _render()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, format="PNG")


if __name__ == "__main__":
    main()
