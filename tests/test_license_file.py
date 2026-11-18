# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""OFL.txt keeps the layout of the SIL template, which license detectors such as GitHub's
match: copyright lines first, then the license statement and text."""

from pathlib import Path

OFL = (Path(__file__).parent.parent / "OFL.txt").read_text()


def test_starts_with_the_copyright_block():
    assert OFL.startswith("Copyright (C) 2026, The Open Kannada Authors.\n")


def test_copyright_block_keeps_the_upstream_reserved_font_name_scope():
    # Navilu's font record declared the Reserved Font Name after both upstream holders.
    head = OFL.split("\n\n")[0].splitlines()
    assert head == [
        "Copyright (C) 2026, The Open Kannada Authors.",
        "Copyright (C) 2011-2012, Aravinda VK <hallimanearavind@gmail.com> (http://aravindavk.in); "
        "Copyright (C) 2005-2010, Indian Institute of Science, Bangalore; "
        "with Reserved Font Name Navilu.",
    ]


def test_states_the_license_with_its_current_address():
    assert (
        "This Font Software is licensed under the SIL Open Font License, Version 1.1.\n"
        "This license is copied below, and is also available with a FAQ at:\n"
        "https://openfontlicense.org\n"
    ) in OFL
