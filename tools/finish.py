# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Finish a TTF that FontForge generated from Gari.sfd, in place.

    python3 tools/finish.py Gari.ttf

Drops FontForge's FFTM timestamp table and the Macintosh name records (whose license text
has line breaks), maps U+00A0 NO-BREAK SPACE to the space glyph, and, in a TrueType font,
writes the glyph names again so the post table holds no duplicates.
"""

from __future__ import annotations

import sys

from fontTools.ttLib import TTFont

SPACE, NO_BREAK_SPACE = 0x0020, 0x00A0
MACINTOSH = 1


def finish(font: TTFont) -> TTFont:
    if "FFTM" in font:
        del font["FFTM"]
    for table in font["cmap"].tables:
        if table.isUnicode() and SPACE in table.cmap:
            table.cmap.setdefault(NO_BREAK_SPACE, table.cmap[SPACE])
    font["name"].names = [r for r in font["name"].names if r.platformID != MACINTOSH]
    if "glyf" in font:
        post = font["post"]
        post.formatType = 2.0
        # Rebuilt from the glyph order, which fontTools dedupes.
        post.extraNames = []
        post.mapping = {}
    return font


def main(argv: list[str]) -> int:
    for path in argv:
        finish(TTFont(path)).save(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
