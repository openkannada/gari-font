# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
import pytest
from fontTools.ttLib import TTFont

from kannada import FONT

FAMILY_IDS = (1, 2, 3, 4, 6, 16, 17, 18, 21, 22, 25)
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


def test_copyright_keeps_the_upstream_reserved_font_name_notice(names):
    # As in Navilu's font record, the Reserved Font Name follows both upstream holders.
    expected = "Indian Institute of Science, Bangalore; with Reserved Font Name Navilu"
    assert any(s.endswith(expected) for s in names[COPYRIGHT])


def test_license_record_is_the_short_ofl_statement(names):
    # The full text ships as OFL.txt; FontBakery and fontspector reject line breaks here.
    assert names[LICENSE] == [
        "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
        "This license is available with a FAQ at: https://openfontlicense.org"
    ]


def test_copyright_credits_the_upstream_authors_and_the_fork(names):
    text = " ".join(names[COPYRIGHT])
    assert "Aravinda" in text and "Indian Institute of Science" in text
    assert "Copyright 2026 The Open Kannada Authors" in text


def test_names_follow_the_family_and_style(names):
    assert names[1] == ["Gari"] and names[2] == ["Regular"]
    assert names[4] == ["Gari Regular"] and names[6] == ["Gari-Regular"]
    assert names[3] == ["1.300;NONE;Gari-Regular"]


def test_name_records_have_no_line_breaks(names):
    assert all("\n" not in s for texts in names.values() for s in texts)


def test_no_macintosh_name_records():
    assert {r.platformID for r in TTFont(FONT)["name"].names} == {3}
