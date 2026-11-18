# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Font-wide fixes for release: installable, consistent vertical metrics, and a clean
binary after FontForge (tools/finish.py)."""

import pytest
from fontTools.ttLib import TTFont

from kannada import FONT


@pytest.fixture(scope="module")
def font() -> TTFont:
    return TTFont(FONT)


def test_installable_without_embedding_restrictions(font):
    assert font["OS/2"].fsType == 0
    assert font["OS/2"].achVendID == "NONE"


def test_vertical_metrics_agree_across_platforms(font):
    hhea, os2, head = font["hhea"], font["OS/2"], font["head"]
    assert (os2.sTypoAscender, os2.sTypoDescender) == (hhea.ascent, hhea.descent)
    assert os2.sTypoLineGap == hhea.lineGap == 0
    assert os2.fsSelection & (1 << 7), "USE_TYPO_METRICS"
    assert os2.usWinAscent >= head.yMax and os2.usWinDescent >= -head.yMin


def test_finished_binary(font):
    assert "FFTM" not in font
    cmap = font.getBestCmap()
    assert cmap[0x00A0] == cmap[0x0020]
    post = TTFont(FONT)["post"]
    assert len(post.extraNames) == len(set(post.extraNames))


def test_joiners_have_empty_zero_width_glyphs(font):
    cmap = font.getBestCmap()
    for joiner in (0x200C, 0x200D):
        name = cmap[joiner]
        assert font["hmtx"][name][0] == 0
        assert font["glyf"][name].numberOfContours == 0
