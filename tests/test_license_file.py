# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""OFL.txt keeps the layout of the SIL template, which license detectors such as GitHub's
match: 1 copyright line per holder first, then the license statement and text."""

from pathlib import Path

OFL = (Path(__file__).parent.parent / "OFL.txt").read_text()


def test_starts_with_the_copyright_block():
    assert OFL.startswith("Copyright (C) 2026, The Open Kannada Authors.\n")


def test_copyright_block_is_1_line_per_holder_with_the_reserved_name_on_navilu():
    head = OFL.split("\n\n")[0].splitlines()
    assert [line.split(",")[1].strip().split(" <")[0] for line in head] == [
        "The Open Kannada Authors.",
        "Aravinda VK",
        "Indian Institute of Science",
    ]
    assert all(line.startswith("Copyright (C) ") for line in head)
    assert head[1].endswith("(http://aravindavk.in), with Reserved Font Name Navilu.")


def test_states_the_license_with_its_current_address():
    assert (
        "This Font Software is licensed under the SIL Open Font License, Version 1.1.\n"
        "This license is copied below, and is also available with a FAQ at:\n"
        "https://openfontlicense.org\n"
    ) in OFL
