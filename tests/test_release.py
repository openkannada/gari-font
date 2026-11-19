# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""The release steps after FontForge: file names, WOFF2, the web subset, the specimen and
the checksums. The build itself runs in the release workflow."""

import hashlib
import sys
from io import BytesIO
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont

from kannada import CONSONANTS, FONT, VIRAMA

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import check_release  # noqa: E402
import finish  # noqa: E402
import release  # noqa: E402
import specimen  # noqa: E402

SAMPLES = ["೜", "ಅವನೝ", "ಕೳ", "ಕ್ಷ್ಮ್ಯ", "ಸ್ತ್ರೀ", "ರ್ಕೈ", *(c + VIRAMA + "ರ" for c in CONSONANTS)]


def positions(data: bytes, text: str):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb.Font(hb.Face(data)), buf)
    return [
        (i.codepoint, p.x_advance, p.x_offset, p.y_offset)
        for i, p in zip(buf.glyph_infos, buf.glyph_positions, strict=True)
    ]


def sfnt(path: Path) -> bytes:
    font = TTFont(path)
    font.flavor = None
    data = BytesIO()
    font.save(data)
    return data.getvalue()


def test_fonts_are_placed_under_their_postscript_name(tmp_path):
    assert release.placed(FONT, tmp_path).name == "Gari-Regular.ttf"


def test_web_subset_keeps_kannada_and_shapes_like_the_font(tmp_path):
    web = release.web_subset(FONT, tmp_path)
    assert web.name == "Gari-Kannada.woff2"
    kannada = {cp for cp in TTFont(FONT).getBestCmap() if 0x0C80 <= cp <= 0x0CFF}
    assert kannada <= set(TTFont(web).getBestCmap())
    full, cut = FONT.read_bytes(), sfnt(web)  # HarfBuzz does not read WOFF2
    for text in SAMPLES:
        after = positions(cut, text)
        assert [g[1:] for g in positions(full, text)] == [g[1:] for g in after], text
        assert all(g[0] != 0 for g in after), text


def test_specimen_for_a_static_font(tmp_path):
    page = specimen.write(tmp_path, "Gari", "1.300", "Based on X.", FONT).read_text()
    assert "{{" not in page and 'class="static"' in page
    assert f'url("webfonts/{FONT.stem}.woff2")' in page
    for label in ("U+0CDC", "U+0CDD", "U+0CF3"):
        assert label in page
    assert "Not in this font" not in page


def test_specimen_names_the_characters_a_font_lacks():
    kept, note = specimen._covered("ಕೢ ಕ ಽ", {ord("ಕ"): "ka"})
    assert kept == "ಕ"
    assert note == "Not in this font: U+0CBD ಽ U+0CE2 ೢ"


def test_finish_leaves_the_post_table_of_a_cff_font(tmp_path):
    font = TTFont(FONT)
    font["post"].formatType = 3.0
    del font["glyf"]
    assert finish.finish(font)["post"].formatType == 3.0


def test_checksums_list_every_file(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    lines = release.checksums(tmp_path).read_text().splitlines()
    assert lines == [f"{hashlib.sha256(b'a').hexdigest()}  a.txt"]


def test_known_failures_match_by_check_code_and_file():
    known = {
        "opentype/hmtx_cff_num_glyphs": {"codes": ["x"], "files": ["*.otf"], "reason": "r"},
        "googlefonts/glyph_coverage": {"codes": ["missing-codepoints"], "reason": "r"},
    }
    assert check_release.is_known(("opentype/hmtx_cff_num_glyphs", "x", "Gari-Regular.otf"), known)
    assert not check_release.is_known(
        ("opentype/hmtx_cff_num_glyphs", "x", "Gari-Regular.ttf"), known
    )
    assert check_release.is_known(("googlefonts/glyph_coverage", "missing-codepoints", ""), known)
    assert not check_release.is_known(("googlefonts/glyph_coverage", "other", ""), known)
