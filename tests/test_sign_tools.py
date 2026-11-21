# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""tools/sfd_splice.py, tools/mark_offsets.py and, where FontForge is installed, add_signs.py."""

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import mark_offsets  # noqa: E402
import sfd_splice  # noqa: E402

HEAD = "SplineFontDB: 3.2\nModificationTime: {t}\n{lookups}BeginChars: {n} {n}\n\n"


def sfd(t, lookups, glyphs):
    body = "\n".join(glyphs)
    return HEAD.format(t=t, lookups=lookups, n=len(glyphs)) + body + "EndChars\nEndSplineFont\n"


def record(name, *lines):
    return (
        f"StartChar: {name}\nEncoding: 1 1 1\n" + "".join(f"{ln}\n" for ln in lines) + "EndChar\n"
    )


ORIGINAL = sfd("100", "", [record("a", "Fore", " 1 2 m 1"), record("b", "Fore", " 3 4 m 1")])
# FontForge rewrote glyph a's outline while saving; the script added glyph c and a lookup.
SAVED = sfd(
    "200",
    'Lookup: 258 0 0 "new" { "new sub" } []\n',
    [
        record("a", "Fore", " 9 9 m 1", 'PairPos2: "new sub" c dx=0', 'PairPos2: "old sub" b dx=1'),
        record("b", "Fore", " 3 4 m 1"),
        record("c", "Fore", " 5 6 m 1"),
    ],
)


def test_splice_keeps_untouched_lines_and_adds_only_its_own():
    merged = sfd_splice.splice(ORIGINAL, SAVED, ["c"], {"new sub"})
    records = sfd_splice.records(merged)
    assert " 1 2 m 1" in records["a"] and " 9 9 m 1" not in records["a"]
    assert 'PairPos2: "new sub" c dx=0' in records["a"]
    assert '"old sub"' not in merged
    assert records["b"] == sfd_splice.records(ORIGINAL)["b"]
    assert records["c"] == sfd_splice.records(SAVED)["c"]
    assert 'Lookup: 258 0 0 "new"' in merged
    assert "ModificationTime: 100" in merged and "BeginChars: 3 3" in merged


def test_splice_refuses_a_glyph_the_original_has():
    with pytest.raises(ValueError):
        sfd_splice.splice(ORIGINAL, SAVED, ["b"], set())


def test_chain_contexts_name_the_glyphs_before_the_substitution():
    text = (
        'ChainSub2: coverage "rule" 0 0 0 1\n 1 1 0\n  Coverage: 11 backslash x\n'
        '  BCoverage: 5 I J S\n 1\n  SeqLookup: 0 "Single 19"\nEndFPST\n'
    )
    assert sfd_splice.chain_contexts(text) == [("Single 19", 0, ["I", "J", "S"])]


def test_sample_follows_a_contour_of_off_curve_points_only():
    square = [(100, 0, False), (100, 100, False), (0, 100, False), (0, 0, False)]
    points = mark_offsets.sample(square)
    assert all(math.dist(p, (50, 50)) <= 54 for p in points)
    assert points[0] == points[-1]


DOTS = [(-890.0, -280.0, 100.0), (-510.0, -280.0, 100.0)]
BODY = [(x, y) for x in range(0, 1201, 20) for y in (0, 1000)]


def test_nukta_centers_under_the_body_when_nothing_is_in_the_way():
    dx, dy = mark_offsets.nukta(BODY, 1200, BODY, DOTS)
    assert (dx, dy) == (0 + 600 - (1200 - 700), 0)


def test_nukta_moves_aside_from_a_tail_before_moving_down():
    # A tail just left of the nukta: it slides a little right rather than drop below the tail.
    tail = [(x, y) for x in range(220, 301, 20) for y in range(-340, 1, 20)]
    dx, dy = mark_offsets.nukta(BODY + tail, 1200, BODY, DOTS)
    assert dy == 0 and 100 < dx <= 200


def test_candrabindu_rises_over_a_tall_glyph():
    mark = (-980.0, 1430.0, -420.0, 1925.0)
    tall = [(x, 1500) for x in range(0, 1201, 20)]
    _, dy = mark_offsets.candrabindu(tall, 1200, BODY, mark)
    assert dy == 1500 + mark_offsets.GAP - 1430


def test_candrabindu_never_rises_past_the_ascent():
    mark = (-980.0, 1430.0, -420.0, 1925.0)
    tower = [(x, 3000) for x in range(0, 1201, 20)]
    _, dy = mark_offsets.candrabindu(tower, 1200, BODY, mark)
    assert mark[3] + dy == mark_offsets.CEILING


def test_subscript_moves_below_the_nukta():
    subscript = [(x, -45) for x in range(-1000, -399, 20)]
    assert mark_offsets.below_nukta(subscript, (-990, -380, -410, -180)) == -380 - 70 + 45


FONTFORGE = shutil.which("fontforge")


@pytest.mark.skipif(FONTFORGE is None, reason="FontForge is not installed")
def test_add_signs_refuses_to_add_a_sign_twice(tmp_path):
    source = tmp_path / "Gari.sfd"
    shutil.copy(ROOT / "Gari.sfd", source)
    before = source.read_bytes()
    run = subprocess.run(
        [
            FONTFORGE,
            "-lang=py",
            "-script",
            str(ROOT / "tools" / "add_signs.py"),
            str(source),
            str(ROOT / "sources" / "signs.json"),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert run.returncode != 0 and "already has a glyph" in run.stderr
    assert source.read_bytes() == before


@pytest.mark.skipif(FONTFORGE is None, reason="FontForge is not installed")
def test_draw_contours_raises_quadratics_exactly(tmp_path):
    script = tmp_path / "check.py"
    script.write_text(
        "import json, sys\n"
        f"sys.path.insert(0, {str(ROOT / 'tools')!r})\n"
        "import fontforge, add_signs\n"
        "f = fontforge.font(); g = f.createChar(-1, 'x')\n"
        "pen = g.glyphPen()\n"
        "add_signs.draw_contours(pen, [[[100, 0, 0], [100, 100, 0], [0, 100, 0], [0, 0, 0]],"
        " [[300, 0, 1], [400, 0, 1], [400, 100, 0], [300, 100, 1]]])\n"
        "pen = None\n"
        "print(json.dumps([len(g.foreground), g.boundingBox()]))\n"
    )
    run = subprocess.run(
        [FONTFORGE, "-lang=py", "-script", str(script)], capture_output=True, text=True, timeout=60
    )
    contours, bounds = json.loads(run.stdout.strip().splitlines()[-1])
    assert contours == 2
    # The off-curve-only square is a round contour inside it; the D shape starts at x 400.
    assert [round(v) for v in bounds] == [0, 0, 400, 100]


def test_sample_follows_on_curve_segments():
    square = [(0, 0, True), (100, 0, True), (100, 100, True), (0, 100, True)]
    assert mark_offsets.sample(square) == [(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]
