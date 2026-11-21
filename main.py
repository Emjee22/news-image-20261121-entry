#!/usr/bin/env python3
"""news-image-20261121: one front page summing up Saturday 21 November 2026.

Draws a 1024x1024 newspaper front page with only the Python standard
library: a hand-defined 5x7 bitmap font, flat shapes, and a pure-Python
PNG encoder. No network, no external files, fully deterministic.
"""

import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (247, 242, 231)
INK = (22, 21, 19)
RED = (180, 35, 24)
NAVY = (27, 58, 92)
GREY = (120, 114, 102)
LIGHT = (232, 224, 208)
GOLD = (198, 142, 32)
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- font -----
# Hand-defined 5x7 bitmap glyphs. Each glyph is 7 rows of 5 bits.
# Only uppercase, digits and a few punctuation marks are needed: every
# word in the image is set in capitals, newspaper style.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "*": ("00000", "00100", "01110", "11111", "01110", "00100", "00000"),
}

CHAR_W = 6  # 5 glyph columns + 1 blank column
CHAR_H = 8  # 7 glyph rows + 1 blank row


def text_width(text, scale):
    return len(text) * CHAR_W * scale


def wrap_text(text, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    max_chars = max(1, max_w // (CHAR_W * scale))
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if len(trial) <= max_chars:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                # A single over-long word is hard-split.
                while len(word) > max_chars:
                    lines.append(word[:max_chars])
                    word = word[max_chars:]
                cur = word
        if cur:
            lines.append(cur)
    return lines


# -------------------------------------------------------------- canvas -----
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def _set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = color[0]
                self.px[i + 1] = color[1]
                self.px[i + 2] = color[2]

    def rect_outline(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.fill_rect(x - t // 2, y - t // 2, t, t, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self._set(xx, yy, color)

    def ring(self, cx, cy, r, color, t=2):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d2 <= r * r:
                    self._set(xx, yy, color)

    def poly(self, pts, color):
        """Even-odd scanline fill for a simple polygon (absolute coords)."""
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                xa = int(round(xs[i]))
                xb = int(round(xs[i + 1]))
                if xb >= xa:
                    self.fill_rect(xa, y, xb - xa + 1, 1, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
        miny, maxy = min(y0, y1, y2), max(y0, y1, y2)
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if den == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / den
                b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / den
                c = 1 - a - b
                if a >= 0 and b >= 0 and c >= 0:
                    self._set(xx, yy, color)

    def text(self, x, y, s, color, scale):
        for ch in s:
            glyph = FONT.get(ch, FONT["?"])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(
                            x + col * scale, y + row * scale, scale, scale, color
                        )
            x += CHAR_W * scale

    def text_centered(self, cx, y, s, color, scale):
        self.text(cx - text_width(s, scale) // 2, y, s, color, scale)

    def text_lines(self, x, y, lines, color, scale, lh=None):
        if lh is None:
            lh = CHAR_H * scale
        for line in lines:
            self.text(x, y, line, color, scale)
            y += lh
        return y


# ------------------------------------------------------------ png out ------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 6)  # fixed level: deterministic
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", comp)
    png += _chunk(b"IEND", b"")
    return png


# ------------------------------------------------------------ the news -----
# 31 verified stories from Saturday 21 November 2026. Region counts:
# EUROPE 8, AMERICAS 8, MIDDLE EAST 5, ASIA 4, AFRICA 2, WORLD 4 = 31.
REGIONS = [
    ("EUROPE", 8),
    ("AMERICAS", 8),
    ("MIDDLE EAST", 5),
    ("ASIA", 4),
    ("AFRICA", 2),
    ("WORLD", 4),
]

# (number, value, label) — six verified figures for the KPI band.
KPIS = [
    ("400+", "DRONES FIRED", "AT UKRAINE"),
    ("110", "MISSILES FIRED", "AT UKRAINE"),
    ("6.7", "PERU QUAKE", "MAGNITUDE"),
    ("-3.7%", "S&P 500 FALL", "AI SELL-OFF"),
    ("$2T", "ANTHROPIC", "MARKET DEBUT"),
    ("11,613", "EBOLA CASES", "IN DR CONGO"),
]

LEADS = [
    {
        "tag": "EUROPE - WAR",
        "head": "RUSSIA STRIKES KYIV - MISSILES LAND IN POLAND",
        "body": "400+ DRONES AND 110 MISSILES HIT UKRAINE. AT LEAST 8 KILLED IN KYIV. NATO: GRAVE VIOLATION.",
        "art": "missiles",
    },
    {
        "tag": "WORLD - CLIMATE",
        "head": "COP31 OVERTIME",
        "body": "THE UN CLIMATE SUMMIT IN ANTALYA RAN PAST ITS DEADLINE. NEARLY 200 NATIONS DEADLOCKED OVER FOSSIL FUELS.",
        "art": "globe",
    },
    {
        "tag": "AMERICAS - QUAKE",
        "head": "PERU QUAKE 6.7",
        "body": "A MAGNITUDE 6.7 QUAKE STRUCK CENTRAL PERU, FELT IN LIMA. NO IMMEDIATE CASUALTIES OR DAMAGE REPORTED.",
        "art": "quake",
    },
]

MEDIUM = [
    {
        "tag": "MIDDLE EAST",
        "head": "RIYADH: 3 MISSILES DOWNED",
        "body": "THREE HOUTHI MISSILES DOWNED ON THE WAY TO RIYADH. THIRD NIGHT OF ALERTS.",
    },
    {
        "tag": "AMERICAS",
        "head": "AI SELL-OFF HITS WALL ST",
        "body": "STOCKS FELL 3.7% IN AN AI AND CHIP SELL-OFF. S&P 500 IN CORRECTION.",
    },
]

# 15 small cards: (region, headline, summary). Region tallies with the
# leads, medium cards and one-liners give EUROPE 8, AMERICAS 8,
# MIDDLE EAST 5, ASIA 4, AFRICA 2, WORLD 4.
SMALL = [
    ("ASIA", "MYANMAR GUILTY OF GENOCIDE", "ICJ RULES AGAINST MYANMAR OVER THE ROHINGYA."),
    ("EUROPE", "TRUMP: DEFUND UKRAINE", "AFTER HIS PUTIN SUMMIT. HE ALSO WEIGHS STRIKES ON IRAN."),
    ("EUROPE", "UK AND EU SIGN BIG DEAL", "FOOD, CARBON, YOUTH MOBILITY. PM ANDY BURNHAM."),
    ("WORLD", "CANCER PILL BREAKTHROUGH", "DARAXONRASIB TRIAL: 1 IN 12 PANCREATIC CANCER PATIENTS."),
    ("EUROPE", "GEN Z PROTESTS SPREAD", "PROTESTS SPREAD ACROSS 25 EUROPEAN COUNTRIES."),
    ("ASIA", "MONGOLIA PRESIDENT OUT", "ELECTIONS WITHIN 4 MONTHS."),
    ("AMERICAS", "FBI DATABASE HACKED", "REPORTEDLY HACKED AS US OUTAGES CONTINUE."),
    ("AMERICAS", "ANTHROPIC AT $2 TRILLION", "OPENED TRADING ON WALL STREET AS A $2 TRILLION COMPANY."),
    ("WORLD", "BEPICOLOMBO AT MERCURY", "THE SPACECRAFT ARRIVES AT MERCURY."),
    ("MIDDLE EAST", "STRIKES KILL IN GAZA", "ISRAELI STRIKES KILL IN GAZA. WEST BANK VIOLENCE GOES ON."),
    ("MIDDLE EAST", "HOUTHIS BLAMED FOR ARMS PORTS", "YEMEN: HODEIDAH PORTS USED FOR ARMS SMUGGLING."),
    ("EUROPE", "SPAIN TO VOTE NOV 29", "CONSERVATIVES GAIN GROUND."),
    ("ASIA", "KOREA CHOLERA CASE", "SOUTH KOREA CONFIRMS ITS FIRST CASE IN A DECADE."),
    ("AFRICA", "EBOLA HITS 100 SCHOOLS", "DOZENS OF STUDENTS DIED IN EASTERN DR CONGO."),
    ("AMERICAS", "TRUMP: NO AI CENTRES ABROAD", "VOWS TO BAN US FIRMS BUILDING AI DATA CENTRES ABROAD."),
]

# 11 one-liners for the "ALSO ON SATURDAY" list.
ALSO = [
    "HAITI: SALVADORAN TROOPS LOSE SOLDIERS TO EXPLOSIVES.",
    "MAN CONVICTED OF STARTING THE DEADLY PALISADES FIRE IN LA.",
    "SYRIA CAPTURES EX-GENERAL ACCUSED OF THE 2014 MASSACRE.",
    "JAPAN CORE INFLATION RISES TO 2.2% IN OCTOBER.",
    "IRAN OPEN TO A JUST US DEAL, REJECTS MOVING URANIUM.",
    "EU APPROVES 1 BILLION EUROS IN DEFENCE AID FOR UKRAINE.",
    "NORDIC POLICE FLAG REVOLUT OVER RUSSIA-LINKED LAUNDERING.",
    "HIPPO FIONA DIES AT A US ZOO AFTER SWALLOWING A CAP.",
    "VATICAN MUSEUMS EXPLORE THE HISTORY OF POPEMOBILES.",
    "US OFFERS FIRST DEEP-SEA MINING LEASES, IGNORING VERDICT.",
    "WHO: 11,613 EBOLA CASES, 5,678 DEATHS IN DR CONGO.",
]


# ------------------------------------------------------------- drawing -----
def draw_header(c):
    c.fill_rect(0, 0, W, 8, RED)
    c.text_centered(W // 2, 16, "THE WORLD IN ONE DAY", RED, 3)
    c.hline(24, 46, W - 48, INK, 2)
    # The date is the biggest text on the page: it must read at 300 px.
    c.text_centered(W // 2, 56, "SATURDAY 21 NOVEMBER 2026", INK, 6)
    c.text_centered(
        W // 2, 112,
        "31 STORIES - 6 REGIONS - EVERY ONE DATED SATURDAY 21 NOVEMBER 2026",
        NAVY, 2,
    )
    c.hline(24, 136, W - 48, INK, 3)


def draw_region_tabs(c):
    y = 146
    tab_w = 160
    gap = 3
    x = 24
    for name, n in REGIONS:
        c.fill_rect(x, y, tab_w, 30, NAVY)
        c.text_centered(x + tab_w // 2, y + 7, "%s %d" % (name, n), WHITE, 2)
        x += tab_w + gap
    c.hline(24, y + 34, W - 48, INK, 2)


def draw_kpis(c):
    y = 188
    box_w = 160
    gap = 3
    x = 24
    for value, lab1, lab2 in KPIS:
        c.fill_rect(x, y, box_w, 68, LIGHT)
        c.rect_outline(x, y, box_w, 68, INK, 1)
        c.fill_rect(x, y, box_w, 4, RED)
        c.text_centered(x + box_w // 2, y + 10, value, RED, 4)
        c.text_centered(x + box_w // 2, y + 48, lab1, INK, 1)
        c.text_centered(x + box_w // 2, y + 58, lab2, INK, 1)
        x += box_w + gap


def draw_art_missiles(c, x, y, w, h):
    c.fill_rect(x, y, w, h, NAVY)
    # Night sky dots.
    for dx, dy in [(20, 12), (60, 26), (110, 10), (170, 22), (230, 12),
                   (280, 28), (40, 44), (150, 40), (250, 46)]:
        c.fill_rect(x + dx, y + dy, 3, 3, WHITE)
    # Ground and blast.
    c.fill_rect(x, y + h - 22, w, 22, INK)
    c.circle(x + w - 70, y + h - 26, 22, RED)
    c.circle(x + w - 70, y + h - 26, 12, GOLD)
    c.circle(x + w - 110, y + h - 24, 10, RED)
    # Rocket streaks.
    c.line(x + 30, y + h - 30, x + 90, y + 18, WHITE, 3)
    c.line(x + 70, y + h - 30, x + 130, y + 26, GOLD, 3)
    c.triangle(x + 86, y + 14, x + 98, y + 22, x + 82, y + 28, WHITE)


def draw_art_globe(c, x, y, w, h):
    c.fill_rect(x, y, w, h, LIGHT)
    cx, cy = x + w // 2 - 30, y + h // 2
    c.circle(cx, cy, 30, NAVY)
    c.circle(cx - 12, cy - 8, 9, PAPER)
    c.circle(cx + 10, cy + 6, 12, PAPER)
    c.circle(cx + 4, cy - 16, 6, PAPER)
    c.ring(cx, cy, 30, INK, 2)
    # Sun and heat rays over the globe.
    c.circle(x + w - 46, y + 26, 12, GOLD)
    for dx, dy in [(0, -18), (13, -13), (18, 0), (13, 13), (0, 18),
                   (-13, 13), (-18, 0), (-13, -13)]:
        c.line(x + w - 46, y + 26, x + w - 46 + dx, y + 26 + dy, GOLD, 2)
    c.text(x + 12, y + h - 18, "ANTALYA", INK, 1)


def draw_art_quake(c, x, y, w, h):
    c.fill_rect(x, y, w, h, LIGHT)
    # Seismograph zigzag.
    pts = [(0, 34), (30, 34), (45, 12), (60, 56), (75, 20), (90, 48),
           (105, 34), (140, 34), (155, 8), (170, 60), (185, 26),
           (200, 44), (215, 34), (260, 34), (275, 18), (290, 50),
           (304, 34)]
    for i in range(len(pts) - 1):
        c.line(x + pts[i][0], y + pts[i][1], x + pts[i + 1][0],
               y + pts[i + 1][1], RED, 3)
    # Cracked ground.
    c.fill_rect(x, y + h - 18, w, 18, INK)
    c.line(x + 60, y + h - 18, x + 80, y + h, PAPER, 2)
    c.line(x + 80, y + h, x + 70, y + h - 8, PAPER, 2)
    c.line(x + 200, y + h - 18, x + 215, y + h, PAPER, 2)
    c.text(x + 12, y + 8, "M 6.7", RED, 2)


def draw_leads(c):
    y = 264
    col_w = 320
    x = 24
    arts = (draw_art_missiles, draw_art_globe, draw_art_quake)
    for lead, art in zip(LEADS, arts):
        art(c, x, y, col_w, 64)
        ty = y + 72
        c.fill_rect(x, ty, text_width(lead["tag"], 1) + 12, 16, RED)
        c.text(x + 6, ty + 4, lead["tag"], WHITE, 1)
        hy = ty + 24
        head_lines = wrap_text(lead["head"], 3, col_w)
        c.text_lines(x, hy, head_lines, INK, 3, lh=26)
        by = hy + len(head_lines) * 26 + 6
        body_lines = wrap_text(lead["body"], 2, col_w)
        c.text_lines(x, by, body_lines, INK, 2, lh=15)
        c.vline(x + col_w + 4, y, 238, GREY, 1)
        x += col_w + 8


def draw_medium(c):
    y = 510
    card_w = 484
    x = 24
    for card in MEDIUM:
        c.fill_rect(x, y, card_w, 86, LIGHT)
        c.rect_outline(x, y, card_w, 86, INK, 1)
        c.fill_rect(x, y, 6, 86, RED)
        c.text(x + 16, y + 8, card["tag"], RED, 1)
        head_lines = wrap_text(card["head"], 3, card_w - 32)
        c.text_lines(x + 16, y + 24, head_lines, INK, 3, lh=26)
        by = y + 24 + len(head_lines) * 26 + 2
        body_lines = wrap_text(card["body"], 2, card_w - 32)
        c.text_lines(x + 16, by, body_lines, INK, 2, lh=15)
        x += card_w + 8


def draw_small_grid(c):
    y0 = 604
    col_w = 190
    gap_x = 6
    row_h = 78
    gap_y = 6
    for i, (region, head, body) in enumerate(SMALL):
        row, col = divmod(i, 5)
        x = 24 + col * (col_w + gap_x)
        y = y0 + row * (row_h + gap_y)
        c.fill_rect(x, y, col_w, row_h, WHITE)
        c.rect_outline(x, y, col_w, row_h, GREY, 1)
        c.fill_rect(x, y, col_w, 3, NAVY)
        c.text(x + 8, y + 8, region, RED, 1)
        # Small region icon: a dot in the card's top-right corner.
        c.circle(x + col_w - 14, y + 12, 4, NAVY)
        head_lines = wrap_text(head, 2, col_w - 16)[:2]
        c.text_lines(x + 8, y + 20, head_lines, INK, 2, lh=15)
        body_lines = wrap_text(body, 1, col_w - 16)[:2]
        c.text_lines(x + 8, y + 20 + len(head_lines) * 15 + 2,
                     body_lines, INK, 1, lh=9)


def draw_map(c, x, y, w, h):
    c.fill_rect(x, y, w, h, NAVY)
    c.text(x + 10, y + 8, "WHERE IT HAPPENED", WHITE, 2)
    # Simplified but recognisable continents: hand-plotted polygons on a
    # rough equirectangular grid (lon -180..180 -> x 0..460, lat 78..-55
    # -> y 24..117). Panel-local coords; each polygon is shifted by (x, y).
    def land(pts):
        c.poly([(x + px, y + py) for px, py in pts], PAPER)
    # North America: Alaska/Canada mass, Florida, tapering Mexico.
    land([(15, 32), (32, 29), (77, 30), (109, 33), (128, 37), (154, 40),
          (163, 45), (141, 49), (127, 60), (115, 64), (109, 68), (96, 65),
          (90, 61), (74, 53), (67, 44), (38, 37)])
    # Greenland.
    land([(160, 30), (173, 27), (192, 30), (199, 31), (179, 32)])
    # South America: wide north, tapering to Patagonia.
    land([(134, 62), (154, 63), (164, 66), (186, 74), (179, 83),
          (172, 88), (158, 95), (147, 100), (141, 105), (137, 93),
          (138, 79), (128, 69)])
    # Europe: Iberia west, Scandinavia bump north, Greece south-east.
    land([(218, 53), (219, 48), (230, 44), (243, 39), (254, 37),
          (263, 37), (269, 40), (267, 47), (256, 51), (246, 48),
          (234, 49), (228, 53)])
    # Africa: wide Sahel bulge, tapering to the Cape.
    land([(209, 68), (218, 58), (243, 53), (256, 56), (271, 57),
          (275, 59), (286, 71), (296, 72), (292, 79), (282, 89),
          (275, 96), (266, 102), (256, 103), (250, 97), (246, 91),
          (242, 83), (242, 76), (220, 75), (211, 71)])
    # Asia: Siberian north coast, Korea, China coast, India, Arabia.
    land([(269, 30), (307, 30), (358, 28), (410, 28), (448, 32),
          (458, 33), (435, 37), (410, 47), (403, 54), (393, 51),
          (387, 58), (371, 65), (365, 72), (356, 68), (348, 65),
          (346, 63), (333, 73), (329, 68), (324, 65), (307, 61),
          (301, 62), (288, 69), (280, 64), (275, 53), (269, 49),
          (266, 44), (266, 37)])
    # Japan.
    land([(416, 46), (422, 48), (420, 56), (414, 54)])
    # Australia.
    land([(375, 94), (387, 89), (399, 88), (412, 87), (418, 93),
          (423, 95), (426, 98), (423, 105), (410, 106), (395, 101),
          (377, 102), (375, 97)])
    # Red dots mark the day's places. Each label gets a dark backing
    # rectangle so white text reads on paper land and on navy sea alike.
    # (dot x, dot y, label, label x, label y); GAZA has a dot only.
    dots = [
        (136, 84, "PERU", 146, 81),
        (254, 42, "POLAND", 234, 28),
        (269, 43, "KYIV", 277, 39),
        (270, 52, "ANTALYA", 280, 50),
        (274, 57, None, 0, 0),
        (290, 61, "RIYADH", 298, 64),
        (249, 81, "CONGO", 257, 78),
        (393, 52, "SEOUL", 355, 48),
    ]
    for dx, dy, label, lx, ly in dots:
        c.circle(x + dx, y + dy, 5, RED)
        c.ring(x + dx, y + dy, 8, WHITE, 1)
        if label:
            c.fill_rect(x + lx, y + ly, text_width(label, 1) + 4, 9, INK)
            c.text(x + lx + 2, y + ly + 1, label, WHITE, 1)


def draw_bottom(c):
    y = 852
    h = 124
    draw_map(c, 24, y, 484, h)
    x = 516
    c.fill_rect(x, y, 484, h, LIGHT)
    c.rect_outline(x, y, 484, h, INK, 1)
    c.text(x + 10, y + 8, "ALSO ON SATURDAY", RED, 2)
    # Line pitch 9: 7 px glyph + 2 px clear gap, so no row touches the
    # next. 11 rows from y+24 end at y+120, inside the 124 px panel
    # (bottom border at y+123).
    ly = y + 24
    for item in ALSO:
        c.text(x + 10, ly, "* " + item, INK, 1)
        ly += 9
    c.hline(24, 984, W - 48, INK, 2)


def draw_footer(c):
    lines = wrap_text(
        "DATE CHECK - EVERY STORY HERE HAPPENED ON, OR WAS FIRST REPORTED "
        "ON, SATURDAY 21 NOVEMBER 2026, IN AT LEAST ONE TIME ZONE. "
        "SOURCES: AP, REUTERS, AFP, NYT, USGS, WHO.",
        1, W - 48,
    )
    c.text_lines(24, 992, lines, INK, 1, lh=10)


def draw():
    c = Canvas(W, H, PAPER)
    draw_header(c)
    draw_region_tabs(c)
    draw_kpis(c)
    draw_leads(c)
    draw_medium(c)
    draw_small_grid(c)
    draw_bottom(c)
    draw_footer(c)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = encode_png(draw())
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
