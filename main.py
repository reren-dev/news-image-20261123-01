# World News Front Page - 23 November 2026
# make.fun news-image-20261123 entry.
# Pure Python 3.13 stdlib only. No network, no clock, no randomness:
# every pixel is a deterministic function of the constants below.
# Writes /output/entry.png (via MAKEFUN_OUTPUT_DIR), 1024x1024, <= 1 MiB.
import os
import struct
import zlib
from binascii import crc32

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
NAVY = (11, 27, 51)
BLACK = (5, 7, 13)
INK = (16, 20, 28)
PAPER = (247, 243, 232)
PAPER_DIM = (232, 226, 210)
EMBER = (193, 39, 27)
ORANGE = (242, 106, 27)
YELLOW = (255, 194, 26)
PALE = (255, 243, 196)
SMOKE = (42, 47, 56)
WHITE = (255, 255, 255)
GREY = (120, 126, 138)
DARKGREY = (70, 76, 88)
SEA = (10, 22, 38)
SEALIGHT = (16, 38, 62)
GREEN = (27, 140, 74)
AMBER = (214, 138, 16)
BLUE = (36, 98, 178)
MAPLAND = (39, 65, 86)
MAPSEA = (8, 20, 38)
RED = (229, 72, 47)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 chars, '#' = on. Uppercase + digits + punctuation.
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".....", ".#..."),
    ',': (".....", ".....", ".....", ".....", "..#..", "..#..", ".#..."),
    ':': (".....", "..#..", ".....", "..#..", ".....", "..#..", "....."),
    ';': (".....", "..#..", ".....", "..#..", ".....", ".#...", "#...."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    '-': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    '/': ("....#", "...#.", "...#.", "..#..", "..#..", ".#...", "#...."),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    '&': (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    '%': ("#...#", "#..#.", "..#..", ".#...", "#..#.", "#...#", "....."),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '#': (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    '@': (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '*': (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    '_': (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    '\u2022': (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
    '\u00d7': (".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "....."),
}

CHAR_ADV = 6  # glyph width 5 + 1 gap, in font units


def text_width(s, scale):
    if not s:
        return 0
    return (len(s) * CHAR_ADV - 1) * scale


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)

    def _clip(self, x0, y0, x1, y1):
        x0 = max(0, min(self.w, x0))
        y0 = max(0, min(self.h, y0))
        x1 = max(0, min(self.w, x1))
        y1 = max(0, min(self.h, y1))
        return x0, y0, x1, y1

    def fill_rect(self, x0, y0, x1, y1, color):
        x0, y0, x1, y1 = self._clip(x0, y0, x1, y1)
        if x1 <= x0 or y1 <= y0:
            return
        r, g, b = color
        row = bytes((r, g, b)) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def blend_px(self, x, y, color, alpha):
        # alpha 0..255: overlay color over existing pixel
        if 0 <= x < self.w and 0 <= y < self.h and 0 < alpha < 256:
            i = (y * self.w + x) * 3
            a = alpha
            self.px[i] = (color[0] * a + self.px[i] * (255 - a)) // 255
            self.px[i + 1] = (color[1] * a + self.px[i + 1] * (255 - a)) // 255
            self.px[i + 2] = (color[2] * a + self.px[i + 2] * (255 - a)) // 255

    def blend_rect(self, x0, y0, x1, y1, color, alpha):
        x0, y0, x1, y1 = self._clip(x0, y0, x1, y1)
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.blend_px(x, y, color, alpha)

    def gradient_rect(self, x0, y0, x1, y1, stops):
        # stops: list of (pos 0..1, color); vertical gradient, per-row fill
        x0, y0, x1, y1 = self._clip(x0, y0, x1, y1)
        if y1 <= y0:
            return
        span = y1 - y0
        for y in range(y0, y1):
            t = (y - y0) / max(1, span - 1)
            c = _interp_stops(stops, t)
            self.fill_rect(x0, y, x1, y + 1, c)

    def ellipse(self, cx, cy, rx, ry, color, alpha=255):
        if rx <= 0 or ry <= 0:
            return
        for y in range(cy - ry, cy + ry + 1):
            dy = (y - cy) / ry
            rem = 1.0 - dy * dy
            if rem < 0:
                continue
            dx = int(rx * (rem ** 0.5))
            if alpha >= 255:
                self.fill_rect(cx - dx, y, cx + dx + 1, y + 1, color)
            else:
                for x in range(cx - dx, cx + dx + 1):
                    self.blend_px(x, y, color, alpha)

    def line(self, x0, y0, x1, y1, color, width=1):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        hw = width // 2
        for s in range(steps + 1):
            x = x0 + (x1 - x0) * s // steps
            y = y0 + (y1 - y0) * s // steps
            self.fill_rect(x - hw, y - hw, x + hw + 1, y + hw + 1, color)

    def polygon(self, pts, color):
        # scanline fill, even-odd
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0, y1 = max(0, min(ys)), min(self.h, max(ys))
        n = len(pts)
        for y in range(y0, y1):
            xs = []
            for i in range(n):
                x0, yy0 = pts[i]
                x1, yy1 = pts[(i + 1) % n]
                if yy0 == yy1:
                    continue
                if (yy0 <= y < yy1) or (yy1 <= y < yy0):
                    x = x0 + (y - yy0) * (x1 - x0) / (yy1 - yy0)
                    xs.append(x)
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[k]), y, int(xs[k + 1]) + 1, y + 1, color)

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            g = FONT.get(ch)
            if g is None:
                ch2 = ch.upper()
                g = FONT.get(ch2, FONT[' '])
            for ry, row in enumerate(g):
                for rx, bit in enumerate(row):
                    if bit == '#':
                        self.fill_rect(cx + rx * scale, y + ry * scale,
                                       cx + (rx + 1) * scale,
                                       y + (ry + 1) * scale, color)
            cx += CHAR_ADV * scale

    def text_stroke(self, x, y, s, scale, color, stroke_color, off=3):
        for dx, dy in ((-off, 0), (off, 0), (0, -off), (0, off),
                       (-off, -off), (off, -off), (-off, off), (off, off)):
            self.text(x + dx, y + dy, s, scale, stroke_color)
        self.text(x, y, s, scale, color)


def _interp_stops(stops, t):
    if t <= stops[0][0]:
        return stops[0][1]
    for i in range(1, len(stops)):
        if t <= stops[i][0]:
            t0, c0 = stops[i - 1]
            t1, c1 = stops[i]
            f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return tuple(int(c0[k] + (c1[k] - c0[k]) * f) for k in range(3))
    return stops[-1][1]


# ---------------------------------------------------------------- LCG (fixed seed, deterministic)
class LCG:
    def __init__(self, seed=1234567):
        self.s = seed

    def next(self):
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s

    def below(self, n):
        return self.next() % n

    def span(self, lo, hi):
        return lo + self.next() % (hi - lo + 1)


# ---------------------------------------------------------------- PNG encoder
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", zlib.compress(bytes(raw), 6)) +
            _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


# ---------------------------------------------------------------- content
HERO_BADGE = "CONFIRMED"
STRIPS = [
    # kicker, badge color, badge text, title, fact1, fact2
    ("MARKETS", GREEN, "CONFIRMED", "HUANG IS BACK",
     "NVDA +31% AS HUANG RETURNS", "NASDAQ +6.5% \u2022 S&P +4.7%"),
    ("EUROPE", GREEN, "CONFIRMED", "EU 22ND SANCTIONS",
     "60 BANKS OFF SWIFT", "VISA BAN ON EX-COMBATANTS"),
    ("TECH", GREEN, "CONFIRMED", "BARBADOS AI SUMMIT",
     "GUTERRES: ACT ON AI RISKS", "GLOBAL AI SAFETY FRAMEWORK"),
    ("MIDDLE EAST", GREEN, "CONFIRMED", "IRAN: US SANCTIONS",
     "US HITS 20+ SHADOW BANKS", "TEHRAN VOWS TO CONFRONT US"),
    ("UKRAINE", GREEN, "CONFIRMED", "DYMER: TOLL NOW 11",
     "RESCUE ENDS; BOY, 7, SAVED", "KYIV REGION DAY OF MOURNING"),
    ("DIPLOMACY", AMBER, "REPORTED", "NEW TALKS SOON",
     "KREMLIN: NEW ROUND SOON", "ZELENSKY: NEW STRIKES FEARED"),
]

# one-liners: (badge color, letter, text); C=CONFIRMED, R=REPORTED, O=OFFICIALS
ONELINERS = [
    (BLUE, "O", "SEOUL: FIRST WOMAN SPY CHIEF"),
    (BLUE, "O", "PRABOWO NAMES 2 VP CANDIDATES"),
    (BLUE, "O", "MODI GIVES NEPAL $1.63BN, IIT"),
    (GREEN, "C", "THAI COURT HALVES MP TERM"),
    (GREEN, "C", "BELGIUM FLIGHTS GROUNDED"),
    (GREEN, "C", "NIGERIA BOAT TOLL HITS 29"),
    (GREEN, "C", "GAZA: UNRWA WORKER KILLED"),
    (BLUE, "O", "ALBANIA DENIES LAUNCH ROLE"),
    (AMBER, "R", "KREMLIN VOWS MORE STRIKES"),
    (GREEN, "C", "BITCOIN BACK ABOVE $61K"),
    (AMBER, "R", "ISTANBUL MARCHES FOR PRESS"),
    (AMBER, "R", "FINLAND BACKS TANK TRAPS"),
    (BLUE, "O", "DNC SETS 12 DEBATES, 2028"),
    (BLUE, "O", "HASINA: JAIL IF SHE RETURNS"),
    (GREEN, "C", "CIKANDE: 24 DEAD, 34 MISSING"),
    (BLUE, "O", "UN URGES BENGHAZI PROBE"),
    (AMBER, "R", "SEOUL: EXAMS CHIEF QUITS"),
    (GREEN, "C", "BRAZIL CUTS 2027 GROWTH CALL"),
    (GREEN, "C", "AUSTRALIA: JOBLESS TO TOP 5%"),
    (AMBER, "R", "RUSSIA FIRES 153 DRONES"),
]

# map dots in panel coords (panel x 0..292, y 668..936; map area y 706..920)
MAP_LAND = [
    [(30, 730), (90, 720), (130, 728), (120, 760), (95, 790),
     (60, 800), (35, 770), (22, 745)],  # N America
    [(95, 810), (130, 805), (140, 850), (120, 900), (100, 870)],  # S America
    [(140, 725), (170, 718), (185, 730), (170, 748), (150, 745)],  # Europe
    [(140, 765), (168, 756), (192, 772), (196, 795), (178, 828),
     (158, 826), (142, 798)],  # Africa
    [(185, 720), (260, 715), (275, 745), (250, 790),
     (210, 780), (195, 750)],  # Asia
    [(250, 850), (275, 845), (280, 865), (255, 870)],  # Oceania
]
MAP_DOTS = [
    (165, 775), (172, 735), (152, 730), (55, 800), (205, 752),
    (252, 742), (235, 815), (218, 758), (232, 772), (172, 752),
    (115, 845), (268, 862),
]


def draw_masthead(cv):
    cv.fill_rect(0, 0, W, 76, NAVY)
    cv.text(16, 12, "MONDAY 23 NOVEMBER 2026", 4, YELLOW)
    s = "27 STORIES \u2022 6 CONTINENTS"
    cv.text(W - 16 - text_width(s, 2), 18, s, 2, WHITE)
    cv.text(16, 48, "THE WORLD IN ONE PICTURE", 3, WHITE)
    cv.fill_rect(0, 76, W, 80, ORANGE)


def _flame(cv, cx, base_y, size):
    # layered teardrop: red -> orange -> yellow -> pale core
    layers = [
        (EMBER, 46, 70), (ORANGE, 34, 52), (YELLOW, 22, 36), (PALE, 12, 20),
    ]
    for color, w, h in layers:
        k = size / 46.0
        cv.ellipse(cx, base_y - int(h * k * 0.45), int(w * k * 0.5),
                   int(h * k * 0.5), color)
    cv.ellipse(cx, base_y - int(62 * size / 46.0), int(7 * size / 46.0),
               int(12 * size / 46.0), PALE)


def draw_hero(cv):
    rng = LCG(20261123)
    # sky: black -> dark red -> orange horizon; sea: dark blue-black
    cv.gradient_rect(0, 80, W, 345, [
        (0.0, (5, 7, 13)), (0.45, (26, 10, 18)),
        (0.75, (122, 30, 14)), (0.95, (242, 106, 27)),
        (1.0, (242, 106, 27)),
    ])
    cv.gradient_rect(0, 345, W, 452, [
        (0.0, SEALIGHT), (0.35, SEA), (1.0, BLACK),
    ])
    # deterministic fine noise over sky+sea (anti-banding), +/-2
    for y in range(80, 452, 2):
        for x in range(0, W, 3):
            n = rng.below(5) - 2
            if n:
                i = (y * W + x) * 3
                cv.px[i] = max(0, min(255, cv.px[i] + n))
                cv.px[i + 1] = max(0, min(255, cv.px[i + 1] + n))
                cv.px[i + 2] = max(0, min(255, cv.px[i + 2] + n))
    # dark scrim behind the headline (top-left, over the darkest sky)
    cv.blend_rect(16, 96, 648, 244, BLACK, 175)
    # smoke plumes above the fires: rising, drifting left, fading
    for (px, py) in [(480, 240), (660, 232), (840, 226)]:
        for k, (dx, dy, sr, al) in enumerate(
                [(0, 0, 26, 200), (-22, -26, 34, 175),
                 (-48, -52, 42, 145), (-78, -78, 48, 110)]):
            cv.ellipse(px + dx, py + dy, sr, int(sr * 0.72), SMOKE, alpha=al)
            cv.ellipse(px + dx - 6, py + dy - 5, int(sr * 0.55),
                       int(sr * 0.4), (58, 64, 76), alpha=max(60, al - 40))
    # ship: listing corvette silhouette, bow to the right, larger
    hull = [(330, 302), (900, 276), (928, 290), (918, 336), (360, 352)]
    cv.polygon(hull, BLACK)
    cv.polygon([(560, 268), (700, 258), (706, 300), (566, 308)], BLACK)
    cv.polygon([(720, 262), (790, 258), (794, 296), (724, 300)], BLACK)
    cv.polygon([(800, 240), (836, 236), (840, 292), (804, 296)], BLACK)
    cv.line(620, 262, 606, 210, BLACK, 4)
    cv.line(606, 210, 640, 226, BLACK, 2)
    # bridge windows, lit
    for wx in (575, 598, 621, 644):
        cv.fill_rect(wx, 276, wx + 13, 285, YELLOW)
    # orange rim light along the hull top edge
    cv.line(330, 302, 900, 276, ORANGE, 2)
    cv.line(560, 268, 700, 258, ORANGE, 2)
    # fires on deck, with a glow halo at their base
    for (fx, fy, fsize) in [(480, 302, 64), (660, 296, 74), (840, 290, 58)]:
        cv.ellipse(fx, fy - 6, 62, 34, ORANGE, alpha=70)
        _flame(cv, fx, fy, fsize)
    # embers rising
    for _ in range(26):
        ex = 380 + rng.below(540)
        ey = 170 + rng.below(130)
        cv.ellipse(ex, ey, 2, 2, ORANGE if rng.below(2) else YELLOW)
    # fire reflection: a soft glow on the water, plus thin vertical streaks
    cv.ellipse(660, 382, 260, 14, ORANGE, alpha=26)
    for (fx, fw) in [(480, 90), (660, 110), (840, 70)]:
        for off in (-16, 0, 16):
            for k in range(4):
                yy = 352 + k * 17
                cv.blend_rect(fx + off - 2, yy, fx + off + 3,
                              yy + 12, ORANGE, 46 - k * 10)
    # thin pier silhouette at the waterline
    cv.fill_rect(60, 386, 960, 392, BLACK)
    # headline, white with black stroke
    cv.text_stroke(24, 108, "KYIV: WE SANK", 7, WHITE, BLACK, 3)
    cv.text_stroke(24, 166, "THE MERKURY", 7, WHITE, BLACK, 3)
    # badge, top right
    cv.fill_rect(868, 96, 1008, 126, GREEN)
    cv.text(868 + (140 - text_width("CONFIRMED", 2)) // 2, 106,
            "CONFIRMED", 2, WHITE)
    # caption bar
    cv.blend_rect(0, 400, W, 452, BLACK, 212)
    cv.text(24, 408, "ZELENSKY: 7 SEA DRONES SANK THE MERKURY", 3, YELLOW)
    cv.text(24, 434,
            "HELICOPTER DESTROYED \u2022 ANGARA HIT \u2022 SATELLITE: SHIP ON ITS SIDE",
            2, WHITE)


def draw_strips(cv):
    cv.fill_rect(0, 452, W, 664, PAPER)
    cell_w = [341, 341, 342]
    xs = [0, 341, 682]
    ys = [452, 558]
    for idx, st in enumerate(STRIPS):
        kicker, bcol, btext, title, f1, f2 = st
        cx = xs[idx % 3]
        cy = ys[idx // 3]
        cw = cell_w[idx % 3]
        cv.fill_rect(cx, cy, cx + cw, cy + 3, ORANGE)
        cv.text(cx + 12, cy + 12, kicker, 2, DARKGREY)
        bw = text_width(btext, 2) + 16
        cv.fill_rect(cx + cw - 12 - bw, cy + 10, cx + cw - 12, cy + 28, bcol)
        cv.text(cx + cw - 12 - bw + 8, cy + 14, btext, 2, WHITE)
        cv.text(cx + 12, cy + 36, title, 3, INK)
        cv.text(cx + 12, cy + 66, f1, 2, DARKGREY)
        cv.text(cx + 12, cy + 84, f2, 2, DARKGREY)
        if idx % 3:
            cv.fill_rect(cx, cy + 8, cx + 1, cy + 98, PAPER_DIM)
        if idx >= 3:
            cv.fill_rect(cx + 8, cy, cx + cw - 8, cy + 1, PAPER_DIM)
    cv.fill_rect(0, 664, W, 668, ORANGE)


def draw_bottom(cv):
    cv.fill_rect(0, 668, W, 936, PAPER)
    # --- world map panel (left) ---
    cv.fill_rect(0, 668, 292, 936, MAPSEA)
    cv.text(12, 680, "WHERE IT HAPPENED", 2, YELLOW)
    for poly in MAP_LAND:
        cv.polygon(poly, MAPLAND)
    for (dx, dy) in MAP_DOTS:
        cv.ellipse(dx, dy, 6, 6, WHITE)
        cv.ellipse(dx, dy, 4, 4, RED)
    # --- one-liner list (right) ---
    cv.text(300, 680, "ALSO ON 23 NOVEMBER", 3, INK)
    cv.text(300, 702,
            "GREEN CONFIRMED \u2022 AMBER REPORTED \u2022 BLUE OFFICIALS",
            2, DARKGREY)
    cols = [(300, 660), (668, 1020)]
    for ci, (x0, x1) in enumerate(cols):
        for ri in range(10):
            item = ONELINERS[ci * 10 + ri]
            bcol, letter, text = item
            y = 724 + ri * 22
            cv.fill_rect(x0, y + 1, x0 + 10, y + 11, bcol)
            cv.text(x0 + 2, y + 2, letter, 1, WHITE)
            cv.text(x0 + 14, y, text, 2, INK)


def draw_footer(cv):
    cv.fill_rect(0, 936, W, H, NAVY)
    cv.text(16, 942, "DATE CHECK - LEFT OUT ON PURPOSE:", 2, YELLOW)
    cv.text(16, 958,
            "COP31 COLLAPSE (22 NOV) \u2022 BAHRAIN ATTACK (21 NOV) \u2022 "
            "GAZA TRUCK STRIKE (21 NOV)", 2, WHITE)
    cv.text(16, 974,
            "KRYVYI RIH (20 NOV) \u2022 DRC EBOLA POST (22 NOV) \u2022 "
            "BEPI COLOMBO (22 NOV)", 2, WHITE)
    cv.text(16, 990,
            "SOURCES: AP \u2022 REUTERS \u2022 AFP \u2022 CNN \u2022 UN NEWS "
            "\u2022 EC \u2022 US TREASURY", 2, GREY)
    cv.text(16, 1006,
            "BBC \u2022 NEMA \u2022 TBS \u2022 PTI \u2022 BLOOMBERG \u2022 "
            "KOREA JOONGANG DAILY \u2022 ANTARA", 2, GREY)


def build():
    cv = Canvas(W, H)
    draw_masthead(cv)
    draw_hero(cv)
    draw_strips(cv)
    draw_bottom(cv)
    draw_footer(cv)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    cv = build()
    size = write_png(cv, path)
    return path, size


if __name__ == "__main__":
    p, n = main()
    print(p, n)
