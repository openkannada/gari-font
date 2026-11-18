# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""OFL.txt keeps the layout of the SIL template, which license detectors such as GitHub's
match: the copyright block first, then the license statement and text."""

from pathlib import Path

OFL = (Path(__file__).parent.parent / "OFL.txt").read_text()


def test_starts_with_the_copyright_block():
    assert OFL.startswith("Copyright (C) 2026, The Open Kannada Authors.\n")


def test_keeps_every_copyright_holder_and_the_reserved_font_name():
    head = OFL.split("This Font Software is licensed")[0]
    for holder in ("The Open Kannada Authors", "Aravinda VK", "Indian Institute of Science"):
        assert holder in head
    assert head.rstrip().endswith("with Reserved Font Name Navilu.")


def test_states_the_license_with_its_current_address():
    assert (
        "This Font Software is licensed under the SIL Open Font License, Version 1.1.\n"
        "This license is copied below, and is also available with a FAQ at:\n"
        "https://openfontlicense.org\n"
    ) in OFL
