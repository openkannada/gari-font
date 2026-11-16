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


@pytest.mark.parametrize("codepoint", sorted(NEW_CHARACTERS))
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


@pytest.mark.parametrize("codepoint", [0x0CDC, 0x0CDD])
def test_new_letters_are_spaced_like_the_consonants(codepoint):
    font = TTFont(FONT)
    cmap, glyf, hmtx = font.getBestCmap(), font["glyf"], font["hmtx"]

    def right_bearing(name):
        return hmtx[name][0] - glyf[name].xMax

    consonants = [cmap[ord(c)] for c in CONSONANTS if ord(c) in cmap]
    median = statistics.median(right_bearing(n) for n in consonants)
    assert right_bearing(cmap[codepoint]) >= median / 2
