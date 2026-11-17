# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
import pytest
from fontTools.ttLib import TTFont
from kannada import FONT

FAMILY_IDS = (1, 3, 4, 6, 16, 18, 21)
COPYRIGHT, LICENSE = 0, 13


@pytest.fixture(scope="module")
def names() -> dict[int, list[str]]:
    table = TTFont(FONT)["name"]
    out: dict[int, list[str]] = {}
    for record in table.names:
        out.setdefault(record.nameID, []).append(record.toUnicode())
    return out


def test_family_names_do_not_use_the_reserved_name(names):
    # OFL-1.1 condition 3: Navilu is a Reserved Font Name of the upstream font.
    used = [s for i in FAMILY_IDS for s in names.get(i, []) if "navilu" in s.lower()]
    assert not used


def test_license_keeps_the_upstream_reserved_font_name_notice(names):
    assert any("Reserved Font Name Navilu" in s for s in names[LICENSE])


def test_copyright_credits_the_upstream_authors(names):
    text = " ".join(names[COPYRIGHT])
    assert "Aravinda" in text and "Indian Institute of Science" in text
