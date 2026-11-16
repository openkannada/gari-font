"""Kannada test strings and a HarfBuzz wrapper shared by the tests."""

import io
import os
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont

VIRAMA = "\u0ccd"
ZWNJ = "\u200c"
ZWJ = "\u200d"
RA = "\u0cb0"
DOTTED_CIRCLE = 0x25CC
CONSONANTS = tuple(chr(cp) for cp in [*range(0x0C95, 0x0CBA), 0x0CDE] if cp not in (0x0CA9, 0x0CB4))

FONT = Path(os.environ.get("FONT", Path(__file__).parent.parent / "Gari.ttf"))


class Shaper:
    """Shapes text with 1 font and reports glyph ids and positions."""

    def __init__(self, data: bytes):
        self.font = hb.Font(hb.Face(data))
        self.dotted_circle = self.font.get_nominal_glyph(DOTTED_CIRCLE)

    def shape(self, text: str, features: dict | None = None) -> list[tuple[int, int, int, int]]:
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        buf.flags = hb.BufferFlags.REMOVE_DEFAULT_IGNORABLES
        hb.shape(self.font, buf, features or {})
        return [
            (i.codepoint, p.x_offset, p.y_offset, p.x_advance)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions, strict=True)
        ]

    def glyphs(self, text: str, features: dict | None = None) -> list[int]:
        return [g for g, *_ in self.shape(text, features)]

    def inserted_dotted_circle(self, text: str) -> bool:
        return self.dotted_circle is not None and self.dotted_circle in self.glyphs(text)


def without_script(path: Path, tag: str) -> bytes:
    """The font with 1 script removed from GSUB and GPOS, so HarfBuzz falls back to the other."""
    font = TTFont(path)
    for table in ("GSUB", "GPOS"):
        if table not in font:
            continue
        scripts = font[table].table.ScriptList
        scripts.ScriptRecord = [r for r in scripts.ScriptRecord if r.ScriptTag != tag]
        scripts.ScriptCount = len(scripts.ScriptRecord)
    out = io.BytesIO()
    font.save(out)
    return out.getvalue()


def clusters() -> list[str]:
    return [a + VIRAMA + b for a in CONSONANTS for b in CONSONANTS]


def three_consonant_clusters() -> list[str]:
    return [a + VIRAMA + b for a in CONSONANTS for b in clusters()]
