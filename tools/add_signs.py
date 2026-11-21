# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Add the signs drawn in sources/signs.json to a FontForge source, as Gari's pen draws them.

Run with FontForge's Python: fontforge -lang=py -script tools/add_signs.py Gari.sfd

Each glyph in the JSON has 1 of 2 kinds of drawing:

- strokes: centerline skeletons as cubic segments, stroked with a round pen of the stem's
  width, with round caps and joins; a dot is a filled circle. The cubics were drawn as Hobby
  curves through hand-placed points; edit the cubics, or redraw a sign and replace its entry;
- contours: finished TrueType outlines (on-curve flag per point). The vocalic L signs are
  Gari's own ಌ and ೡ fitted to its subscript ಲ by `fontqa fix --compose-l` (openkannada/kannadi).

A glyph with an advance keeps it (marks are drawn left of their origin, over the base, as Gari
draws its marks); otherwise the advance is lsb + ink + rsb.

Shaping that comes with the signs:

- Unicode 15 makes jihvamuliya and upadhmaniya consonants with a stacker: the consonant after
  them (ka or kha, pa or pha) is written as a subscript. An abvs rule gives it Gari's own
  subscript form there.
- Gari's substitution rules skip the nukta, so a consonant with a nukta takes the same vowel
  sign and conjunct forms as without it.
- The candrabindu moves back past the vowel signs before it, to right after the consonant.
- Pair positioning (tools/mark_offsets.py) moves the nukta under the consonant's body and below
  descenders, pushes a subscript below a nukta, and moves the candrabindu over the consonant and
  above the vowel sign after it.

Only what this script adds goes into the source (tools/sfd_splice.py).
"""

import json
import sys
import tempfile
from pathlib import Path

import fontforge
import psMat

sys.path.insert(0, str(Path(__file__).parent))
import mark_offsets  # noqa: E402
from sfd_splice import chain_contexts, splice  # noqa: E402

KAPPA = 0.5523
CLASSES = {"base": "baseglyph", "mark": "mark"}
VIRAMA, NUKTA, CANDRABINDU = 0x0CCD, 0x0CBC, 0x0C81
CONSONANTS = {*range(0x0C95, 0x0CBA), 0x0CDE}
VOWEL_SIGNS = {*range(0x0CBE, 0x0CCD), 0x0CD5, 0x0CD6}
STACKERS = {0x0CF1: (0x0C95, 0x0C96), 0x0CF2: (0x0CAA, 0x0CAB)}
SCRIPTS = (("knda", ("dflt",)), ("knd2", ("dflt",)))
STACK_SINGLE = "Subscript after a stacker"
STACK_RULE = "'abvs' Subscript after jihvamuliya or upadhmaniya"
NUKTA_PLACE = "'blwm' Nukta under the consonant"
SUBSCRIPT_DROP = "'blwm' Subscript below the nukta"
NUKTA_DROP = "'blwm' Nukta below the vowel sign"
CANDRABINDU_PLACE = "'abvm' Candrabindu over the consonant"
CANDRABINDU_RISE = "'abvm' Candrabindu above the vowel sign"
CANDRABINDU_BACK = "Candrabindu after the consonant"
OTHER_MARKS = "Marks other than the nukta"


def draw_segments(pen, stroke):
    segments = stroke["segments"]
    pen.moveTo(tuple(segments[0][0]))
    for _, c1, c2, p in segments[:-1] if stroke["closed"] else segments:
        pen.curveTo(tuple(c1), tuple(c2), tuple(p))
    if stroke["closed"]:
        _, c1, c2, _ = segments[-1]
        pen.curveTo(tuple(c1), tuple(c2), tuple(segments[0][0]))
        pen.closePath()
    else:
        pen.endPath()


def draw_dot(pen, center, diameter):
    (x, y), r = center, diameter / 2
    k = r * KAPPA
    pen.moveTo((x + r, y))
    pen.curveTo((x + r, y + k), (x + k, y + r), (x, y + r))
    pen.curveTo((x - k, y + r), (x - r, y + k), (x - r, y))
    pen.curveTo((x - r, y - k), (x - k, y - r), (x, y - r))
    pen.curveTo((x + k, y - r), (x + r, y - k), (x + r, y))
    pen.closePath()


def toward(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def draw_contours(pen, contours):
    """TrueType contours (x, y, on-curve flag), each quadratic segment raised to a cubic."""
    for points in contours:
        points = [tuple(p) for p in points]
        if not any(on for *_, on in points):
            # A contour of off-curve points only starts at the midpoint of its last and first.
            points.insert(0, (*toward(points[-1], points[0], 0.5), 1))
        start = next(i for i, p in enumerate(points) if p[2])
        points = points[start:] + points[: start + 1]
        here = tuple(points[0][:2])
        pen.moveTo(here)
        offs = []
        for x, y, on in points[1:]:
            if not on:
                offs.append((x, y))
                continue
            if not offs:
                pen.lineTo((x, y))
            ends = [toward(a, b, 0.5) for a, b in zip(offs, offs[1:], strict=False)]
            for control, end in zip(offs, [*ends, (x, y)], strict=bool(offs)):
                pen.curveTo(toward(here, control, 2 / 3), toward(end, control, 2 / 3), end)
                here = end
            here, offs = (x, y), []
        pen.closePath()


def draw_strokes(work, strokes, stem):
    pen = work.glyphPen()
    for stroke in strokes:
        if "segments" in stroke:
            draw_segments(pen, stroke)
    pen = None
    if len(work.foreground):
        work.stroke("circular", stem, cap="round", join="round")
        work.removeOverlap()
    pen = work.glyphPen(replace=False)
    for stroke in strokes:
        if stroke.get("dot"):
            draw_dot(pen, stroke["center"], stroke["diameter"])
    pen = None


def outline(glyph, spec, stem):
    """Draw and clean up in a cubic scratch glyph, since the source's layers are quadratic."""
    scratch = fontforge.font()
    scratch.em = glyph.font.em
    work = scratch.createChar(-1, "work")
    if "contours" in spec:
        pen = work.glyphPen()
        draw_contours(pen, spec["contours"])
        pen = None
    else:
        draw_strokes(work, spec["strokes"], stem)
    work.removeOverlap()
    work.addExtrema()
    work.simplify(0.5, ("mergelines", "smoothcurves"))
    layer = work.foreground
    layer.is_quadratic = True
    glyph.foreground = layer
    scratch.close()


def drop_close_points(glyph, within=2):
    """Remove points that rounding left within `within` units of the next on both axes,
    keeping on-curve points over off-curve ones."""
    layer = fontforge.layer()
    layer.is_quadratic = True
    for contour in glyph.foreground:
        points = list(contour)
        keep = []
        for i, p in enumerate(points):
            q = points[(i + 1) % len(points)]
            near = max(abs(p.x - q.x), abs(p.y - q.y)) <= within
            if near and (not p.on_curve or q.on_curve):
                continue
            keep.append(p)
        cleaned = fontforge.contour()
        cleaned.is_quadratic = True
        for p in keep:
            cleaned += p
        cleaned.closed = True
        layer += cleaned
    glyph.foreground = layer


def add(font, name, spec, stem):
    current = next((g for g in font.glyphs() if g.unicode == spec["unicode"]), None)
    if current is not None:
        sys.exit(f"U+{spec['unicode']:04X} already has a glyph, {current.glyphname}")
    if name in font:
        sys.exit(f"the source already has a glyph named {name}")
    glyph = font.createChar(spec["unicode"], name)
    outline(glyph, spec, stem)
    glyph.round()
    drop_close_points(glyph)
    glyph.correctDirection()
    if "advance" in spec:
        glyph.width = spec["advance"]
    else:
        xmin, _, xmax, _ = glyph.boundingBox()
        glyph.transform(psMat.translate(spec["lsb"] - xmin, 0))
        glyph.width = round(spec["lsb"] + (xmax - xmin) + spec["rsb"])
    glyph.glyphclass = CLASSES[spec["class"]]


def lookup_sources(font):
    """Glyph name to the glyph it is made from by a single substitution or, for a ligature,
    its first component."""
    source = {}
    for glyph in font.glyphs():
        for _, kind, *parts in glyph.getPosSub("*"):
            if kind == "Substitution":
                source.setdefault(parts[0], glyph.glyphname)
            elif kind == "Ligature":
                source.setdefault(glyph.glyphname, parts[0])
    return source


def made_from(name, source, wanted, depth=6):
    """The glyph in `wanted` that `name` is made from, or None."""
    for _ in range(depth):
        if name in wanted:
            return name
        if name not in source:
            return None
        name = source[name]
    return None


def subscripts(font):
    """Consonant glyph name to its below-base form, from the old-order blwf ligatures."""
    virama = next(g.glyphname for g in font.glyphs() if g.unicode == VIRAMA)
    out = {}
    for lookup in font.gsub_lookups:
        kind, _, features = font.getLookupInfo(lookup)
        if kind != "gsub_ligature" or not any(tag == "blwf" for tag, _ in features):
            continue
        tables = set(font.getLookupSubtables(lookup))
        for glyph in font.glyphs():
            for table, kind_, *parts in glyph.getPosSub("*"):
                if table in tables and kind_ == "Ligature" and parts[1:] == [virama]:
                    out.setdefault(parts[0], glyph.glyphname)
    return out


def add_stacked_subscripts(font):
    """The consonant after a stacker takes its subscript form. Returns the subtables added."""
    names = {g.unicode: g.glyphname for g in font.glyphs() if g.unicode != -1}
    below = subscripts(font)
    first = font.gsub_lookups[0]
    font.addLookup(STACK_SINGLE, "gsub_single", (), (), first)
    font.addLookupSubtable(STACK_SINGLE, f"{STACK_SINGLE} subtable")
    font.addLookup(
        STACK_RULE, "gsub_contextchain", ("ignore_marks",), (("abvs", SCRIPTS),), STACK_SINGLE
    )
    tables = {f"{STACK_SINGLE} subtable"}
    for stacker, consonants in STACKERS.items():
        followers = [names[c] for c in consonants]
        for name in followers:
            font[name].addPosSub(f"{STACK_SINGLE} subtable", below[name])
        table = f"{STACK_RULE} {stacker:04X}"
        font.addContextualSubtable(
            STACK_RULE,
            table,
            "coverage",
            f"[{names[stacker]}] | [{' '.join(followers)}] @<{STACK_SINGLE}> |",
        )
        tables.add(table)
    return tables


def candrabindu_after_consonant(font, passes=3):
    """Move the candrabindu back past up to `passes` marks. Each pass joins a mark and the
    candrabindu into a temporary glyph, then splits it into the candrabindu and the mark.
    Returns the temporary glyphs and the subtables added."""
    cb = next(g.glyphname for g in font.glyphs() if g.unicode == CANDRABINDU)
    marks = [
        g.glyphname
        for g in font.glyphs()
        if g.glyphclass == "mark" and g.unicode not in (CANDRABINDU, NUKTA)
    ]
    temporary = {}
    for mark in marks:
        glyph = font.createChar(-1, f"{mark}_{cb}.reorder")
        glyph.width = 0
        temporary[mark] = glyph.glyphname
    after, tables = font.gsub_lookups[-1], set()
    for n in range(1, passes + 1):
        join, split = f"{CANDRABINDU_BACK} join {n}", f"{CANDRABINDU_BACK} split {n}"
        font.addLookup(join, "gsub_ligature", (), (("psts", SCRIPTS),), after)
        font.addLookupSubtable(join, f"{join} subtable")
        font.addLookup(split, "gsub_multiple", (), (("psts", SCRIPTS),), join)
        font.addLookupSubtable(split, f"{split} subtable")
        for mark, temp in temporary.items():
            font[temp].addPosSub(f"{join} subtable", (mark, cb))
            font[temp].addPosSub(f"{split} subtable", (cb, mark))
        tables |= {f"{join} subtable", f"{split} subtable"}
        after = split
    return list(temporary.values()), tables


def skip_nukta(font):
    """Every substitution rule that sees marks sees all of them except the nukta."""
    nukta = next(g.glyphname for g in font.glyphs() if g.unicode == NUKTA)
    others = tuple(
        g.glyphname for g in font.glyphs() if g.glyphclass == "mark" and g.glyphname != nukta
    )
    font.markClasses = (*font.markClasses, (OTHER_MARKS, others))
    for lookup in font.gsub_lookups:
        if font.getLookupInfo(lookup)[1] == ():
            font.lookupSetFlags(lookup, (OTHER_MARKS,))


def contour_points(glyph):
    return [mark_offsets.sample([(p.x, p.y, p.on_curve) for p in c]) for c in glyph.foreground]


def points(glyph):
    return [p for contour in contour_points(glyph) for p in contour]


def context_before(font, sfd_text):
    """Glyph name to the glyphs that come just before it, for glyphs that a contextual rule
    substitutes."""
    out = {}
    for lookup, _, before in chain_contexts(sfd_text):
        if lookup not in font.gsub_lookups or font.getLookupInfo(lookup)[0] != "gsub_single":
            continue
        tables = set(font.getLookupSubtables(lookup))
        for glyph in font.glyphs():
            for table, kind, *parts in glyph.getPosSub("*"):
                if table in tables and kind == "Substitution":
                    out.setdefault(parts[0], set()).update(before)
    return out


def add_mark_positions(font, sfd_text):
    """Pair positioning for the nukta and the candrabindu. Returns the subtables added."""
    by_code = {g.unicode: g for g in font.glyphs() if g.unicode != -1}
    nukta, candrabindu = by_code[NUKTA], by_code[CANDRABINDU]
    dots = mark_offsets.circles(contour_points(nukta))
    cb_box = mark_offsets.box(points(candrabindu))
    source = lookup_sources(font)
    consonants = {by_code[c].glyphname for c in CONSONANTS if c in by_code}
    signs = {by_code[c].glyphname for c in VOWEL_SIGNS if c in by_code}
    below = set(subscripts(font).values())
    below |= {n for n in source if made_from(n, source, below)}
    ink = {g.glyphname: points(g) for g in font.glyphs()}

    tables = {}
    for name, feature, flags in (
        (NUKTA_PLACE, "blwm", ()),
        (SUBSCRIPT_DROP, "blwm", ()),
        (NUKTA_DROP, "blwm", ()),
        (CANDRABINDU_PLACE, "abvm", (OTHER_MARKS,)),
        (CANDRABINDU_RISE, "abvm", ()),
    ):
        font.addLookup(name, "gpos_pair", flags, ((feature, SCRIPTS),))
        tables[name] = f"{name} subtable"
        font.addLookupSubtable(name, tables[name])

    x0, y0, x1, y1 = mark_offsets.box(points(nukta))
    reach = [x0, y0, x1, y1]
    marks = (nukta.glyphname, candrabindu.glyphname)
    places, placed = [(0, 0)], {}
    before = context_before(font, sfd_text)
    for glyph in font.glyphs():
        name = glyph.glyphname
        made = made_from(name, source, consonants)
        if name in marks or name in below or made is None or not ink[name]:
            continue
        dx, dy = mark_offsets.nukta(ink[name], glyph.width, ink[made], dots)
        placed[name] = (dx, dy, [(x - glyph.width, y) for x, y in ink[name]])
        if dx or dy:
            glyph.addPosSub(tables[NUKTA_PLACE], nukta.glyphname, 0, 0, 0, 0, dx, dy, 0, 0)
        if name in consonants:
            # A subscript or vowel sign glyph follows a nukta on the bare consonant only.
            reach = [min(reach[0], x0 + dx), min(reach[1], y0 + dy), max(reach[2], x1 + dx), y1]
            places.append((dx, dy))
    for glyph in font.glyphs():
        name = glyph.glyphname
        if name in marks or not ink[name]:
            continue
        if name in below:
            dy = mark_offsets.below_nukta(ink[name], tuple(reach))
            if dy:
                nukta.addPosSub(tables[SUBSCRIPT_DROP], name, 0, 0, 0, 0, 0, dy, 0, 0)
        elif made_from(name, source, signs):
            cases = [placed[p] for p in sorted(before.get(name, ())) if p in placed]
            if cases:
                dx, dy = mark_offsets.after_consonants(ink[name], dots, cases)
            else:
                dx, dy = 0, mark_offsets.under_sign(ink[name], dots, places)
            if dx or dy:
                nukta.addPosSub(tables[NUKTA_DROP], name, dx, dy, 0, 0, 0, 0, 0, 0)

    for glyph in font.glyphs():
        name = glyph.glyphname
        made = made_from(name, source, consonants)
        if name in marks or not ink[name]:
            continue
        if glyph.glyphclass == "mark":
            dy = mark_offsets.above_sign(ink[name], cb_box)
            if dy:
                candrabindu.addPosSub(tables[CANDRABINDU_RISE], name, 0, dy, 0, 0, 0, 0, 0, 0)
            continue
        dx, dy = mark_offsets.candrabindu(ink[name], glyph.width, ink[made or name], cb_box)
        if dx or dy:
            glyph.addPosSub(
                tables[CANDRABINDU_PLACE], candrabindu.glyphname, 0, 0, 0, 0, dx, dy, 0, 0
            )
    return set(tables.values())


def main(path, source):
    data = json.loads(Path(source).read_text())
    font = fontforge.open(path)
    for name, spec in data["glyphs"].items():
        add(font, name, spec, data["stem"])
    tables = add_stacked_subscripts(font)
    temporary, reorder = candrabindu_after_consonant(font)
    skip_nukta(font)
    tables |= reorder | add_mark_positions(font, Path(path).read_text())
    added = [*data["glyphs"], *temporary]
    with tempfile.TemporaryDirectory() as tmp:
        saved = Path(tmp) / "out.sfd"
        font.save(str(saved))
        merged = splice(Path(path).read_text(), saved.read_text(), added, tables)
    Path(path).write_text(merged)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "sources/signs.json")
