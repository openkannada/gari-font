# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Where Gari's nukta and candrabindu go after each glyph, worked out from the outlines.

Gari draws its marks in place, for a typical consonant. These offsets, applied by pair
positioning, move the 2 marks over or under the consonant that a glyph is built from, clear of
the glyph's own ink, and push a subscript down below a nukta. Points are in font units; a
glyph's points are relative to its own origin.
"""

from __future__ import annotations

Point = tuple[float, float]
Box = tuple[float, float, float, float]

GAP = 70  # ink-free space kept between a mark and its neighbor
MARGIN = 40  # how far either side of a mark the neighbor's ink is looked for
CEILING = 2150  # just under the font's ascent (2160), so nothing is clipped


def sample(points: list[tuple[float, float, bool]], steps: int = 6) -> list[Point]:
    """Points along a closed quadratic contour given as (x, y, on-curve)."""
    if not points:
        return []
    pts = list(points)
    if not any(on for *_, on in pts):
        (ax, ay, _), (bx, by, _) = pts[-1], pts[0]
        pts.insert(0, ((ax + bx) / 2, (ay + by) / 2, True))
    start = next(i for i, p in enumerate(pts) if p[2])
    pts = pts[start:] + pts[: start + 1]
    out, here, offs = [pts[0][:2]], pts[0][:2], []
    for x, y, on in pts[1:]:
        if not on:
            offs.append((x, y))
            continue
        ends = [
            ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(offs, offs[1:], strict=False)
        ]
        for control, end in zip(offs, [*ends, (x, y)], strict=bool(offs)):
            for k in range(1, steps + 1):
                t = k / steps
                out.append(
                    (
                        (1 - t) ** 2 * here[0] + 2 * (1 - t) * t * control[0] + t * t * end[0],
                        (1 - t) ** 2 * here[1] + 2 * (1 - t) * t * control[1] + t * t * end[1],
                    )
                )
            here = end
        if not offs:
            out.append((x, y))
            here = (x, y)
        offs = []
    return out


def box(points: list[Point]) -> Box:
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def middle(points: list[Point], low: float, high: float) -> float | None:
    """The middle of the ink between 2 heights, across."""
    xs = [x for x, y in points if low <= y <= high]
    return (min(xs) + max(xs)) / 2 if xs else None


def highest(points: list[Point], x0: float, x1: float) -> float | None:
    ys = [y for x, y in points if x0 <= x <= x1]
    return max(ys) if ys else None


Circle = tuple[float, float, float]


def circles(contours: list[list[Point]]) -> list[Circle]:
    """Each contour of a dotted mark as a circle: center and radius."""
    out = []
    for c in contours:
        x0, y0, x1, y1 = box(c)
        out.append(((x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) / 2))
    return out


def clear(dots: list[Circle], ink: list[Point], dx: float, dy: float) -> bool:
    """No ink within GAP of the dots once they move by (dx, dy)."""
    for cx, cy, r in dots:
        x, y, reach = cx + dx, cy + dy, (r + GAP) ** 2
        if any((px - x) ** 2 + (py - y) ** 2 < reach for px, py in ink):
            return False
    return True


SLIDE, DROP, STEP = 400, 600, 20  # how far the nukta may move sideways and down to find room


def nukta(
    glyph: list[Point], advance: float, consonant: list[Point], dots: list[Circle]
) -> tuple[int, int]:
    """Move the nukta under the consonant's body, then the least distance (sideways first)
    that keeps it clear of the glyph's ink."""
    center = middle(consonant, -60, 500)
    if center is None:
        return 0, 0
    x0 = min(cx - r for cx, _, r in dots)
    x1 = max(cx + r for cx, _, r in dots)
    base = center - (advance + (x0 + x1) / 2)
    near = [
        (px - advance, py)
        for px, py in glyph
        if py < 400 and advance + x0 + base - SLIDE - 300 <= px <= advance + x1 + base + SLIDE + 300
    ]
    for dx, dy in moves():
        if clear(dots, near, base + dx, dy):
            return round(base + dx), round(dy)
    return round(base), -DROP


def moves() -> list[tuple[int, int]]:
    """Candidate moves, cheapest first. Vowel signs hang off the right of the consonant, so
    moving left is cheaper than moving right, and sideways cheaper than down."""
    every = [(dx, -dy) for dx in range(-SLIDE, SLIDE + 1, STEP) for dy in range(0, DROP + 1, STEP)]
    return sorted(every, key=lambda m: (2 if m[0] > 0 else 1) * abs(m[0]) + 1.5 * abs(m[1]))


def after_consonants(
    sign: list[Point], dots: list[Circle], cases: list[tuple[int, int, list[Point]]]
) -> tuple[int, int]:
    """The least further move of the nukta that keeps it clear of both a vowel sign and each
    consonant the sign follows. Each case is the nukta's place under a consonant and that
    consonant's ink, both relative to the consonant's end."""
    near = [(x, y) for x, y in sign if y < 400]
    for mx, my in moves():
        if all(
            clear(dots, near + [p for p in ink if p[1] < 400], dx + mx, dy + my)
            for dx, dy, ink in cases
        ):
            return mx, my
    return 0, -DROP


def under_sign(sign: list[Point], dots: list[Circle], places: list[tuple[int, int]]) -> int:
    """How far the nukta drops (0 or negative) to clear a vowel sign drawn after it, from every
    place the nukta takes under a consonant."""
    near = [(x, y) for x, y in sign if y < 400]
    for drop in range(0, DROP + 1, STEP):
        if all(clear(dots, near, dx, dy - drop) for dx, dy in places):
            return -drop
    return -DROP


def below_nukta(subscript: list[Point], mark: Box) -> int:
    """How far down a subscript that follows the nukta moves to clear it (0 or negative). mark
    is the box the nukta can occupy, once moved."""
    x0, bottom, x1, _ = mark
    top = highest(subscript, x0, x1)
    return round(min(0.0, (bottom - GAP) - top)) if top is not None else 0


def candrabindu(
    glyph: list[Point], advance: float, consonant: list[Point], mark: Box
) -> tuple[int, int]:
    """Move the candrabindu, which shaping puts right after the consonant, over the consonant's
    body and above the glyph's ink."""
    x0, bottom, x1, top = mark
    center = middle(consonant, 500, 3000)
    dx = 0.0 if center is None else center - (advance + (x0 + x1) / 2)
    half = (x1 - x0) / 2 + MARGIN
    middle_x = advance + dx + (x0 + x1) / 2
    peak = highest(glyph, middle_x - half, middle_x + half)
    rise = max(0.0, peak + GAP - bottom) if peak is not None else 0.0
    return round(dx), round(min(rise, CEILING - top))


def above_sign(sign: list[Point], mark: Box) -> int:
    """How far the candrabindu rises to clear a vowel sign drawn after it (0 or positive)."""
    x0, bottom, x1, top = mark
    reach = 200  # the candrabindu moves sideways with its consonant; look a little wider
    peak = highest(sign, x0 - reach, x1 + reach)
    rise = max(0.0, peak + GAP - bottom) if peak is not None else 0.0
    return round(min(rise, CEILING - top))


def _distance_ok(moving: list[Point], fixed: list[Point], dx: float, dy: float) -> bool:
    reach = GAP * GAP
    for mx, my in moving:
        x, y = mx + dx, my + dy
        if any((fx - x) ** 2 + (fy - y) ** 2 < reach for fx, fy in fixed):
            return False
    return True


def _near(points: list[Point], other: list[Point], margin: float) -> list[Point]:
    """The points of `points` within `margin` of the other set's box."""
    if not points or not other:
        return []
    x0, y0, x1, y1 = box(other)
    return [
        (x, y)
        for x, y in points
        if x0 - margin <= x <= x1 + margin and y0 - margin <= y <= y1 + margin
    ]


def drop_clear(moving: list[Point], fixed: list[Point], limit: int = 900, step: int = 10) -> int:
    """How far `moving` drops (0 or negative) to stay GAP clear of `fixed`."""
    for d in range(0, limit + 1, step):
        a = _near(moving, fixed, GAP + d)
        b = _near(fixed, [(x, y - d) for x, y in moving], GAP)
        if _distance_ok(a, b, 0, -d):
            return -d
    return -limit


def slide_clear(moving: list[Point], fixed: list[Point], limit: int = 900, step: int = 10) -> int:
    """How far `moving` slides right (0 or positive) to stay GAP clear of `fixed`."""
    for d in range(0, limit + 1, step):
        a = _near(moving, fixed, GAP + d)
        b = _near(fixed, [(x + d, y) for x, y in moving], GAP)
        if _distance_ok(a, b, d, 0):
            return d
    return limit


def subscript_drop(subscript: list[Point], dots: list[Circle], place: tuple[int, int]) -> int:
    """How far a subscript after the nukta drops (0 or negative) to clear the nukta where it
    sits under this consonant."""
    dx, dy = place
    near = [(x, y) for x, y in subscript if y > -1200]
    for d in range(0, 901, 10):
        if clear(dots, [(x, y - d) for x, y in near], dx, dy):
            return -d
    return -900
