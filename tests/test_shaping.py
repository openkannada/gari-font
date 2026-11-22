# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
import statistics

import pytest
import uharfbuzz as hb
from fontTools.ttLib import TTFont

from kannada import (
    CONSONANTS,
    FONT,
    RA,
    VIRAMA,
    ZWJ,
    ZWNJ,
    Shaper,
    clusters,
    three_consonant_clusters,
    without_script,
)

KSSA = "\u0c95\u0ccd\u0cb7"
LLLA = "\u0cde"


@pytest.fixture(scope="module")
def shaper() -> Shaper:
    return Shaper(FONT.read_bytes())


@pytest.fixture(scope="module")
def old_order() -> Shaper:
    return Shaper(without_script(FONT, "knd2"))


def test_font_has_new_order_script():
    scripts = {r.ScriptTag for r in TTFont(FONT)["GSUB"].table.ScriptList.ScriptRecord}
    assert "knd2" in scripts


def unjoined(shaper: Shaper, cluster: str) -> bool:
    return shaper.glyphs(cluster) == shaper.glyphs(
        cluster.replace(VIRAMA, VIRAMA + ZWNJ)
    ) or shaper.inserted_dotted_circle(cluster)


def test_every_consonant_pair_forms_a_conjunct(shaper):
    texts = [c for c in clusters() if not c.endswith(LLLA)]
    assert [c for c in texts if unjoined(shaper, c)] == []


@pytest.mark.xfail(strict=True, reason="the font has no subscript form of U+0CDE yet")
def test_every_consonant_takes_subscript_llla(shaper):
    texts = [c for c in clusters() if c.endswith(LLLA)]
    assert [c for c in texts if unjoined(shaper, c)] == []


def test_every_consonant_takes_the_arkavattu(shaper):
    texts = [RA + VIRAMA + c for c in CONSONANTS if c != RA]
    broken = [
        t
        for t in texts
        if shaper.glyphs(t) == shaper.glyphs(t, {"rphf": False}) or shaper.inserted_dotted_circle(t)
    ]
    assert broken == []


def joiner_variants(cluster: str) -> list[str]:
    return [cluster.replace(VIRAMA, VIRAMA + j, 1) for j in (ZWJ, ZWNJ)]


def test_new_order_shapes_like_old_order(shaper, old_order):
    # Old order never applies the font's KSSA ligature, so KSSA is checked on its own below.
    two, three = clusters(), three_consonant_clusters()
    final = [c + VIRAMA for c in two + three]
    joined = [v for c in two + [c + VIRAMA for c in two] for v in joiner_variants(c)]
    texts = [t for t in two + three + final + joined if KSSA not in t]
    differ = [t for t in texts if shaper.shape(t) != old_order.shape(t)]
    assert differ == []


def test_kssa_uses_its_ligature(shaper):
    assert len(shaper.glyphs(KSSA)) == 1


NEW_CHARACTERS = {
    0x0CDC: "ARCHAIC SHRII",
    0x0CDD: "NAKAARA POLLU",
    0x0CF3: "COMBINING ANUSVARA ABOVE RIGHT",
}
SIGNS = {
    0x0C80: "SPACING CANDRABINDU",
    0x0C81: "CANDRABINDU",
    0x0C84: "SIDDHAM",
    0x0CBC: "NUKTA",
    0x0CBD: "AVAGRAHA",
    0x0CE2: "VOWEL SIGN VOCALIC L",
    0x0CE3: "VOWEL SIGN VOCALIC LL",
    0x0CF1: "JIHVAMULIYA",
    0x0CF2: "UPADHMANIYA",
    0x0964: "DANDA",
    0x0965: "DOUBLE DANDA",
}
MARKS = {0x0C81, 0x0CBC, 0x0CE2, 0x0CE3}
GDEF_BASE, GDEF_MARK = 1, 3
NUKTA, CANDRABINDU = "\u0cbc", "\u0c81"


def hex_id(codepoint: int) -> str:
    return f"U+{codepoint:04X}"


@pytest.mark.parametrize("codepoint", sorted(NEW_CHARACTERS | SIGNS), ids=hex_id)
def test_new_character_has_a_glyph_with_ink(codepoint):
    font = TTFont(FONT)
    name = font.getBestCmap().get(codepoint)
    assert name is not None
    assert font["glyf"][name].numberOfContours > 0


@pytest.mark.parametrize(
    "text", ["\u0c85\u0cb5\u0ca8\u0cdd", "\u0c95\u0cf3", "\u0cdc\u0c97\u0ca3\u0cc7\u0cb6"]
)
def test_new_characters_shape_without_notdef(shaper, text):
    assert 0 not in shaper.glyphs(text)


def test_anusvara_above_right_joins_the_consonant_cluster(shaper):
    buf = hb.Buffer()
    buf.add_str("\u0c95\u0cf3")
    buf.guess_segment_properties()
    hb.shape(shaper.font, buf)
    assert {info.cluster for info in buf.glyph_infos} == {0}


@pytest.mark.parametrize("codepoint", [0x0CDC, 0x0CDD, *sorted(set(SIGNS) - MARKS)], ids=hex_id)
def test_new_letters_are_spaced_like_the_consonants(codepoint):
    font = TTFont(FONT)
    cmap, glyf, hmtx = font.getBestCmap(), font["glyf"], font["hmtx"]

    def right_bearing(name):
        return hmtx[name][0] - glyf[name].xMax

    consonants = [cmap[ord(c)] for c in CONSONANTS if ord(c) in cmap]
    median = statistics.median(right_bearing(n) for n in consonants)
    assert right_bearing(cmap[codepoint]) >= median / 2


@pytest.mark.parametrize("codepoint", sorted(SIGNS), ids=hex_id)
def test_sign_has_its_glyph_class(codepoint):
    font = TTFont(FONT)
    classes = font["GDEF"].table.GlyphClassDef.classDefs
    expected = GDEF_MARK if codepoint in MARKS else GDEF_BASE
    assert classes.get(font.getBestCmap()[codepoint]) == expected


@pytest.mark.parametrize("codepoint", sorted(MARKS), ids=hex_id)
def test_mark_joins_the_consonant_cluster(shaper, codepoint):
    buf = hb.Buffer()
    buf.add_str("\u0c95" + chr(codepoint))
    buf.guess_segment_properties()
    hb.shape(shaper.font, buf)
    assert {info.cluster for info in buf.glyph_infos} == {0}
    assert not shaper.inserted_dotted_circle("\u0c95" + chr(codepoint))


@pytest.mark.parametrize(
    "text",
    [
        "\u0cb8\u0cbe\u0c80",  # ಸಾಀ
        "\u0cb9\u0cbe\u0c81",  # ಹಾಁ
        "\u0c84 \u0cb6\u0ccd\u0cb0\u0cc0",  # ಄ ಶ್ರೀ
        "\u0c9c\u0cbc\u0cae\u0cc0\u0ca8\u0cc1",  # ಜ಼ಮೀನು
        "\u0cab\u0cbc\u0cc8\u0cb2\u0ccd",  # ಫ಼ೈಲ್
        "\u0cb8\u0ccb\u0cbd\u0cb9\u0cae\u0ccd",  # ಸೋಽಹಮ್
        "\u0c95\u0ce2\u0caa\u0ccd\u0ca4",  # ಕೢಪ್ತ
        "\u0ca6\u0cc1\u0cf1\u0c96",  # ದುೱಖ
        "\u0c85\u0c82\u0ca4\u0cf2\u0caa\u0cc1\u0cb0",  # ಅಂತೲಪುರ
        "\u0cac\u0c82\u0ca6\u0ca8\u0cc1\u0964",  # ಬಂದನು।
        "\u0965\u0ce7\u0965",  # ॥೧॥
    ],
)
def test_signs_shape_in_words(shaper, text):
    assert 0 not in shaper.glyphs(text)
    assert not shaper.inserted_dotted_circle(text)


def ink_boxes(shaper: Shaper, text: str) -> list[tuple[float, float, float, float]]:
    """Each output glyph's ink box where HarfBuzz places it."""
    font = TTFont(FONT)
    glyf, order = font["glyf"], font.getGlyphOrder()
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(shaper.font, buf)
    boxes, x = [], 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions, strict=True):
        g = glyf[order[info.codepoint]]
        dx, dy = x + pos.x_offset, pos.y_offset
        boxes.append((dx + g.xMin, dy + g.yMin, dx + g.xMax, dy + g.yMax))
        x += pos.x_advance
    return boxes


@pytest.mark.parametrize("consonant", CONSONANTS)
def test_nukta_sits_under_the_consonant(shaper, consonant):
    base, nukta = ink_boxes(shaper, consonant + NUKTA)
    assert nukta[3] < 0
    assert base[0] <= (nukta[0] + nukta[2]) / 2 <= base[2]


@pytest.mark.parametrize("consonant", CONSONANTS)
def test_candrabindu_sits_over_the_consonant(shaper, consonant):
    base, candrabindu = ink_boxes(shaper, consonant + CANDRABINDU)
    assert candrabindu[1] > base[3]
    assert base[0] <= (candrabindu[0] + candrabindu[2]) / 2 <= base[2]


@pytest.mark.parametrize("codepoint", [0x0964, 0x0965], ids=hex_id)
def test_dandas_stand_on_the_baseline_as_tall_as_the_consonants(codepoint):
    font = TTFont(FONT)
    cmap, glyf = font.getBestCmap(), font["glyf"]
    tops = statistics.median(glyf[cmap[ord(c)]].yMax for c in CONSONANTS if ord(c) in cmap)
    danda = glyf[cmap[codepoint]]
    assert danda.yMin == 0
    assert 0.9 * tops <= danda.yMax <= 1.1 * tops


@pytest.mark.parametrize(
    ("stacker", "consonant"),
    [("ೱ", "ಕ"), ("ೱ", "ಖ"), ("ೲ", "ಪ"), ("ೲ", "ಫ")],
)
def test_consonant_after_a_stacker_is_a_subscript(shaper, old_order, stacker, consonant):
    subscript = shaper.glyphs("ಕ" + VIRAMA + consonant)[-1]
    for font in (shaper, old_order):
        assert font.glyphs(stacker + consonant)[-1] == subscript
        assert subscript in font.glyphs(stacker + consonant + "ು")


def test_other_consonants_stay_full_after_a_stacker(shaper):
    assert shaper.glyphs("ೱಗ")[-1] == shaper.glyphs("ಗ")[0]
    assert shaper.glyphs("ೲಕ")[-1] == shaper.glyphs("ಕ")[0]
