# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""The nukta and the candrabindu with every consonant, vowel sign and common subscript."""

import pathops
import pytest
import uharfbuzz as hb
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from kannada import CONSONANTS, FONT, VIRAMA, Shaper

NUKTA, CANDRABINDU = "಼", "ಁ"
SIGNS = ["", *map(chr, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC1, 0x0CC2, 0x0CC3, 0x0CC6, 0x0CC7])]
SIGNS += list(map(chr, [0x0CC8, 0x0CCA, 0x0CCB, 0x0CCC]))
SUBSCRIPTS = [VIRAMA + c for c in "ರಲವಯ"]
ASCENT = 2160
TOUCH = 50  # square units of shared ink that count as a collision


@pytest.fixture(scope="module")
def font() -> TTFont:
    return TTFont(FONT)


@pytest.fixture(scope="module")
def shaper() -> Shaper:
    return Shaper(FONT.read_bytes())


def inked(font: TTFont, shaper: Shaper, text: str) -> list[tuple[str, pathops.Path]]:
    """Each output glyph's outline where HarfBuzz places it."""
    glyphs, order = font.getGlyphSet(), font.getGlyphOrder()
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(shaper.font, buf)
    out, x = [], 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions, strict=True):
        name, path = order[info.codepoint], pathops.Path()
        move = (1, 0, 0, 1, x + pos.x_offset, pos.y_offset)
        glyphs[name].draw(TransformPen(path.getPen(), move))
        out.append((name, path))
        x += pos.x_advance
    return out


def area(path: pathops.Path) -> float:
    pen = AreaPen()
    path.draw(pen)
    return abs(pen.value)


def collisions(font: TTFont, shaper: Shaper, text: str, mark: str) -> list[str]:
    name = font.getBestCmap()[ord(mark)]
    shaped = inked(font, shaper, text)
    out = []
    for i, (glyph, path) in enumerate(shaped):
        if glyph != name:
            continue
        if path.bounds[3] > ASCENT:
            out.append(f"{text}: above the ascent")
        for j, (other, ink) in enumerate(shaped):
            if j != i and area(pathops.op(path, ink, pathops.PathOp.INTERSECTION)) > TOUCH:
                out.append(f"{text}: {other}")
    return out


@pytest.mark.parametrize("consonant", CONSONANTS)
def test_nukta_clears_the_consonant_its_signs_and_subscripts(font, shaper, consonant):
    texts = [consonant + NUKTA + s for s in SIGNS + SUBSCRIPTS]
    assert [c for t in texts for c in collisions(font, shaper, t, NUKTA)] == []


@pytest.mark.parametrize("consonant", CONSONANTS)
def test_candrabindu_clears_the_consonant_and_its_signs(font, shaper, consonant):
    texts = [consonant + s + CANDRABINDU for s in SIGNS]
    assert [c for t in texts for c in collisions(font, shaper, t, CANDRABINDU)] == []


@pytest.mark.parametrize("consonant", CONSONANTS)
def test_vowel_signs_and_subscripts_form_through_the_nukta(font, shaper, consonant):
    nukta = font.getBestCmap()[ord(NUKTA)]
    order = font.getGlyphOrder()
    differ = []
    # A ra with a nukta is not a reph, so it keeps its own shape before a subscript.
    for sign in SIGNS + (SUBSCRIPTS if consonant != "\u0cb0" else []):
        with_nukta = [order[g] for g in shaper.glyphs(consonant + NUKTA + sign)]
        without = [order[g] for g in shaper.glyphs(consonant + sign)]
        if [g for g in with_nukta if g != nukta] != without:
            differ.append(sign)
    assert differ == []


@pytest.mark.parametrize("sign", [s for s in SIGNS if s])
def test_candrabindu_follows_the_consonant_glyph(font, shaper, sign):
    order = font.getGlyphOrder()
    names = [order[g] for g in shaper.glyphs("ಕ" + sign + CANDRABINDU)]
    assert names.index(font.getBestCmap()[ord(CANDRABINDU)]) == 1
