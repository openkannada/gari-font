import pytest
from fontTools.ttLib import TTFont
from kannada import (
    CONSONANTS,
    FONT,
    RA,
    VIRAMA,
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


def test_new_order_draws_like_old_order(shaper, old_order):
    # Old order never applies the font's KSSA ligature, so KSSA is checked on its own below.
    texts = clusters() + three_consonant_clusters() + [c + VIRAMA for c in clusters()]
    differ = [t for t in texts if KSSA not in t and shaper.drawing(t) != old_order.drawing(t)]
    assert differ == []


def test_kssa_uses_its_ligature(shaper):
    assert len(shaper.glyphs(KSSA)) == 1
