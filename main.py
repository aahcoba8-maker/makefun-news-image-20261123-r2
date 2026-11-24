#!/usr/bin/env python3
"""Front page of one day: 23 November 2026.

Draws a newspaper-style summary of the day's world news as a single
1024x1024 PNG and writes it to $MAKEFUN_OUTPUT_DIR/entry.png (falling
back to this script's directory when the variable is not set).

Layout discipline: one dominant lead story, three secondary stories in
a strict three-column grid, generous whitespace, a three-colour palette
(ink, red, market green) on paper. Pure PIL drawing, fully deterministic:
two runs produce identical bytes.
"""

import os
import sys

W = 1024
H = 1024
MARGIN = 46

PAPER = (248, 244, 233)
INK = (18, 20, 24)
RED = (163, 22, 33)
GREEN = (10, 110, 52)
GREY = (86, 90, 98)
PANEL = (255, 253, 247)
HAIRLINE = (196, 188, 168)

SERIF_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
)
SANS_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
)
SANS_BOLD_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
)


def load_font(ImageFont, candidates, size):
    """First readable font file wins; Pillow's sized default is the net."""
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


class Page:
    """Thin wrapper over an ImageDraw with the page's fonts loaded."""

    def __init__(self, draw, ImageFont):
        self.d = draw
        self.serif = lambda s: load_font(ImageFont, SERIF_CANDIDATES, s)
        self.sans = lambda s: load_font(ImageFont, SANS_CANDIDATES, s)
        self.sans_bold = lambda s: load_font(ImageFont, SANS_BOLD_CANDIDATES, s)

    def width(self, text, font):
        return self.d.textlength(text, font=font)

    def centered(self, text, y, font, fill):
        x = (W - self.width(text, font)) / 2
        self.d.text((x, y), text, font=font, fill=fill)
        return x

    def wrap(self, text, font, max_width):
        """Greedy word wrap measured with the real font metrics."""
        lines, current = [], ""
        for word in text.split():
            trial = word if not current else current + " " + word
            if self.width(trial, font) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def block(self, text, x, y, font, fill, max_width, leading):
        for line in self.wrap(text, font, max_width):
            self.d.text((x, y), line, font=font, fill=fill)
            y += leading
        return y

    def rule(self, y, weight=2, fill=INK, x0=MARGIN, x1=W - MARGIN):
        self.d.rectangle([x0, y, x1, y + weight - 1], fill=fill)


def masthead(p):
    """Nameplate plus a dateline band that names the day, unmissably."""
    p.rule(30, 2)
    p.rule(36, 6)
    p.centered("THE WORLD TODAY", 52, p.serif(56), INK)
    p.rule(128, 2)
    band = p.sans_bold(25)
    p.d.text((MARGIN, 140), "MONDAY", font=band, fill=INK)
    p.centered("23 NOVEMBER 2026", 140, p.serif(29), RED)
    right = "ONE IMAGE"
    p.d.text((W - MARGIN - p.width(right, band), 140), right, font=band, fill=INK)
    p.rule(178, 2)


def market_chart(p, x, y, w, h):
    """Steep green rebound line: the shape of the day's market story."""
    p.d.rectangle([x, y, x + w, y + h], fill=PANEL, outline=HAIRLINE, width=2)
    for i in range(1, 4):
        gy = y + h * i / 4
        p.d.line([x + 10, gy, x + w - 10, gy], fill=HAIRLINE, width=1)
    pts = [
        (0.04, 0.78), (0.16, 0.72), (0.28, 0.80), (0.38, 0.68),
        (0.48, 0.72), (0.58, 0.52), (0.70, 0.40), (0.82, 0.24),
        (0.96, 0.10),
    ]
    xy = [(x + fx * w, y + fy * h) for fx, fy in pts]
    p.d.line(xy, fill=GREEN, width=6, joint="curve")
    for px, py in xy[::3] + xy[-1:]:
        p.d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=GREEN)
    p.d.text((x + 14, y + 10), "NVIDIA  +31%", font=p.sans_bold(26), fill=GREEN)
    nas = "NASDAQ  +6.5%"
    nas_font = p.sans_bold(20)
    p.d.text((x + w - 14 - p.width(nas, nas_font), y + h - 34),
             nas, font=nas_font, fill=GREY)


def lead_story(p):
    """The dominant story: Nvidia reinstates Jensen Huang; markets soar."""
    y = 194
    p.d.text((MARGIN, y), "MARKETS  —  THE DAY'S BIGGEST STORY",
             font=p.sans_bold(23), fill=RED)
    y += 38
    head = p.serif(78)
    p.d.text((MARGIN, y), "HUANG IS BACK:", font=head, fill=INK)
    p.d.text((MARGIN, y + 92), "NVIDIA LEAPS 31%", font=head, fill=INK)
    y += 196
    deck = ("Nvidia reinstates the chief executive it lost only 11 days ago. "
            "The S&P 500 jumps 4.8% as Wall Street stages one of its biggest "
            "rebound days on record.")
    p.block(deck, MARGIN, y, p.sans(26), (40, 42, 48), 520, 36)
    market_chart(p, 606, y - 6, 372, 150)
    return y + 160


def icon_ship(p, x, y):
    p.d.polygon([(x + 4, y + 22), (x + 56, y + 22), (x + 48, y + 34), (x + 12, y + 34)], fill=INK)
    p.d.rectangle([x + 24, y + 10, x + 38, y + 22], fill=INK)
    p.d.line([x + 31, y, x + 31, y + 10], fill=INK, width=3)
    for i in range(3):
        sx = x + 2 + i * 20
        p.d.arc([sx, y + 36, sx + 16, y + 46], 0, 180, fill=RED, width=3)


def icon_tanker(p, x, y):
    p.d.polygon([(x + 2, y + 24), (x + 58, y + 24), (x + 50, y + 36), (x + 10, y + 36)], fill=INK)
    p.d.rectangle([x + 8, y + 16, x + 44, y + 24], fill=INK)
    p.d.rectangle([x + 46, y + 10, x + 52, y + 24], fill=INK)
    p.d.polygon([(x + 27, y), (x + 33, y + 8), (x + 27, y + 14), (x + 21, y + 8)], fill=RED)


def icon_globe(p, x, y):
    p.d.ellipse([x + 6, y, x + 54, y + 44], outline=INK, width=3)
    p.d.line([x + 6, y + 22, x + 54, y + 22], fill=INK, width=2)
    p.d.arc([x + 20, y + 2, x + 40, y + 42], 90, 270, fill=INK, width=2)
    p.d.arc([x + 20, y + 2, x + 40, y + 42], 270, 90, fill=INK, width=2)
    p.d.line([x + 44, y + 6, x + 52, y - 2], fill=RED, width=3)


COLUMNS = (
    {
        "icon": icon_ship,
        "kicker": "UKRAINE — LIBYA",
        "headline": "UKRAINE SINKS RUSSIAN WARSHIP",
        "body": ("Naval drones destroy the corvette Merkury in Benghazi "
                 "port, Libya. A Russian strike on Dymer, near Kyiv, "
                 "kills at least 11."),
    },
    {
        "icon": icon_tanker,
        "kicker": "MIDDLE EAST",
        "headline": "IRAN VOWS TO BREAK HORMUZ BLOCKADE",
        "body": ("Tankers attacked in the Strait of Hormuz as Tehran "
                 "vows to defy the US blockade. US sanctions hit Iran's "
                 "shadow banks."),
    },
    {
        "icon": icon_globe,
        "kicker": "CLIMATE — TURKEY",
        "headline": "COP31 ENDS WITH NO DEAL AT ALL",
        "body": ("The longest UN climate summit in history closes in "
                 "Turkey without an agreement, split to the end over "
                 "fossil fuels and money."),
    },
)


def columns(p, top):
    col_w = (W - 2 * MARGIN - 2 * 24) // 3
    for i, col in enumerate(COLUMNS):
        x = MARGIN + i * (col_w + 24)
        if i:
            p.d.line([x - 12, top, x - 12, top + 268], fill=HAIRLINE, width=2)
        col["icon"](p, x, top)
        p.d.text((x, top + 52), col["kicker"], font=p.sans_bold(19), fill=RED)
        y = p.block(col["headline"], x, top + 80, p.serif(26), INK, col_w, 31)
        p.block(col["body"], x, y + 8, p.sans(18), (40, 42, 48), col_w, 24)


def footer(p):
    p.rule(918, 2)
    brief = ("IN BRIEF   Democrats win the largest US House majority since "
             "1992  ·  Cartel leader 'Chapo Isidro' captured in Sinaloa  ·  "
             "India pledges €1.4bn to rebuild flood-hit Nepal")
    p.block(brief, MARGIN, 930, p.sans(18), (40, 42, 48), W - 2 * MARGIN, 25)
    src = "Sources: Reuters · Just Security · Nexus Europa · One Turn — reports of 23 November 2026"
    p.centered(src, 988, p.sans(15), GREY)


def render():
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (W, H), PAPER)
    p = Page(ImageDraw.Draw(img), ImageFont)
    masthead(p)
    bottom = lead_story(p)
    p.rule(bottom + 14, 5)
    columns(p, bottom + 40)
    footer(p)
    return img


def fallback_png(path):
    """Stdlib-only emergency image: valid PNG, paper with an ink block."""
    import struct
    import zlib

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    raw = b""
    for yy in range(256):
        row = bytearray(b"\x00")
        for xx in range(256):
            row += bytes(PAPER if 24 <= xx < 232 and 24 <= yy < 232 else INK)
        raw += bytes(row)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", 256, 256, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw))
           + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.dirname(
        os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    try:
        render().save(target, format="PNG")
    except Exception:
        fallback_png(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
