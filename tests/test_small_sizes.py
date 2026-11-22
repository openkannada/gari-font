# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""The siddham's spiral stays 1 open channel at 12 and 16 px, at any horizontal pixel phase.

FreeType renders without hinting; a pixel at half coverage or more is ink. An open spiral has
no counter, so its opening is closed with a ring hugging the outer edge (1.5 pixels thick at
12 px, reaching 30 units into the ink): the white channel is then 1 counter, which must not
fill in or pinch into pieces.
"""

import math
from io import BytesIO

import freetype
import pathops
import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from kannada import FONT

SIDDHAM = 0x0C84
UPM = 2048


def ellipse(cx, cy, rx, ry, n=72):
    path = pathops.Path()
    pts = [
        (cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n))
        for k in range(n)
    ]
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    path.close()
    return path


def probe() -> pathops.Path:
    font = TTFont(FONT)
    ink = pathops.Path()
    font.getGlyphSet()[font.getBestCmap()[SIDDHAM]].draw(ink.getPen())
    x0, y0, x1, y1 = ink.bounds
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    ring = pathops.op(
        ellipse(cx, cy, rx + 260, ry + 260),
        ellipse(cx, cy, rx - 30, ry - 30),
        pathops.PathOp.DIFFERENCE,
    )
    return pathops.op(ink, ring, pathops.PathOp.UNION)


def counters(path: pathops.Path, px: int, shift: float) -> int:
    pen = TTGlyphPen(None)
    path.draw(
        TransformPen(Cu2QuPen(pen, max_err=0.5, reverse_direction=True), (1, 0, 0, 1, shift, 0))
    )
    glyph = pen.glyph()
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder([".notdef", "g"])
    fb.setupCharacterMap({})
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph(), "g": glyph})
    fb.setupHorizontalMetrics({".notdef": (0, 0), "g": (UPM, glyph.xMin)})
    fb.setupHorizontalHeader(ascent=UPM, descent=-UPM // 2)
    fb.setupNameTable({"familyName": "Probe", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    data = BytesIO()
    fb.save(data)
    face = freetype.Face(BytesIO(data.getvalue()))
    face.set_pixel_sizes(0, px)
    face.load_glyph(1, freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_RENDER)
    bm = face.glyph.bitmap
    rows, width, pitch, buffer = bm.rows, bm.width, bm.pitch, bm.buffer
    ink = [[buffer[r * pitch + c] >= 128 for c in range(width)] for r in range(rows)]
    # White regions that do not reach the bitmap's edge are counters.
    seen, found = set(), 0
    for r in range(rows):
        for c in range(width):
            if ink[r][c] or (r, c) in seen:
                continue
            stack, edge = [(r, c)], False
            seen.add((r, c))
            while stack:
                y, x = stack.pop()
                edge |= y in (0, rows - 1) or x in (0, width - 1)
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if (
                        0 <= ny < rows
                        and 0 <= nx < width
                        and not ink[ny][nx]
                        and (ny, nx) not in seen
                    ):
                        seen.add((ny, nx))
                        stack.append((ny, nx))
            found += not edge
    return found


@pytest.mark.parametrize("px", [12, 16])
def test_siddham_channel_stays_open(px):
    path = probe()
    assert counters(path, 200, 0) == 1
    found = [counters(path, px, k / 8 * UPM / px) for k in range(8)]
    assert found == [1] * 8
