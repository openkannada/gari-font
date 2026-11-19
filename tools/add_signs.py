# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Add the signs drawn in sources/signs.json to a FontForge source, as Gari's pen draws them.

Run with FontForge's Python: fontforge -lang=py -script tools/add_signs.py Gari.sfd

Each glyph in the JSON has 1 of 2 kinds of drawing:

- strokes: centerline skeletons as cubic segments (Hobby curves through hand-placed points),
  stroked with a round pen of the stem's width, with round caps and joins; a dot is a filled
  circle;
- contours: finished TrueType outlines (on-curve flag per point). The vocalic L signs are
  Gari's own ಌ and ೡ fitted to its subscript ಲ by `fontqa fix --compose-l` (openkannada/kannadi).

A glyph with an advance keeps it (marks are drawn left of their origin, over the base, since
Gari positions marks in their outlines); otherwise the advance is lsb + ink + rsb.

Unicode 15 makes jihvamuliya and upadhmaniya consonants with a stacker: the consonant after
them (ka or kha after jihvamuliya, pa or pha after upadhmaniya) is written as a subscript. An
abvs rule, for knda and knd2, gives those consonants Gari's own subscript forms there.

FontForge rewrites some existing glyphs when it saves a font, so only what this script adds is
copied from its output into the source: the lookups, the new glyphs and the consonants' new
substitution lines. Every other line of the source is kept as it is.
"""

import json
import re
import sys
import tempfile
from pathlib import Path

import fontforge
import psMat

KAPPA = 0.5523
CLASSES = {"base": "baseglyph", "mark": "mark"}
VIRAMA = 0x0CCD
STACKERS = {0x0CF1: (0x0C95, 0x0C96), 0x0CF2: (0x0CAA, 0x0CAB)}
STACK_SINGLE = "Subscript after a stacker"
STACK_RULE = "'abvs' Subscript after jihvamuliya or upadhmaniya"


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
            # Between 2 off-curve points lies an implied on-curve point at their midpoint.
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


def drop_coincident_points(glyph, within=2):
    """Remove points that rounding left within a unit or 2 of the next, keeping on-curve ones."""
    layer = fontforge.layer()
    layer.is_quadratic = True
    for contour in glyph.foreground:
        points = list(contour)
        keep = []
        for i, p in enumerate(points):
            q = points[(i + 1) % len(points)]
            near = abs(p.x - q.x) + abs(p.y - q.y) < within
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
    if current is not None and len(current.foreground):
        sys.exit(f"U+{spec['unicode']:04X} already has a glyph with ink, {current.glyphname}")
    glyph = font.createChar(spec["unicode"], name)
    glyph.clear()
    outline(glyph, spec, stem)
    glyph.round()
    drop_coincident_points(glyph)
    glyph.correctDirection()
    if "advance" in spec:
        glyph.width = spec["advance"]
    else:
        xmin, _, xmax, _ = glyph.boundingBox()
        glyph.transform(psMat.translate(spec["lsb"] - xmin, 0))
        glyph.width = round(spec["lsb"] + (xmax - xmin) + spec["rsb"])
    glyph.glyphclass = CLASSES[spec["class"]]


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
    """The consonant after a stacker takes its subscript form. Returns the glyphs it changes."""
    names = {g.unicode: g.glyphname for g in font.glyphs() if g.unicode != -1}
    below = subscripts(font)
    scripts = (("knda", ("dflt",)), ("knd2", ("dflt",)))
    first = font.gsub_lookups[0]
    font.addLookup(STACK_SINGLE, "gsub_single", (), (), first)
    font.addLookupSubtable(STACK_SINGLE, f"{STACK_SINGLE} subtable")
    font.addLookup(
        STACK_RULE, "gsub_contextchain", ("ignore_marks",), (("abvs", scripts),), STACK_SINGLE
    )
    touched = []
    for stacker, consonants in STACKERS.items():
        followers = [names[c] for c in consonants]
        for name in followers:
            font[name].addPosSub(f"{STACK_SINGLE} subtable", below[name])
            touched.append(name)
        font.addContextualSubtable(
            STACK_RULE,
            f"{STACK_RULE} {stacker:04X}",
            "coverage",
            f"[{names[stacker]}] | [{' '.join(followers)}] @<{STACK_SINGLE}> |",
        )
    return touched


def records(sfd_text):
    """Glyph name to its StartChar ... EndChar record."""
    return {
        m.group(1): m.group(0)
        for m in re.finditer(r"^StartChar: (\S+)\n.*?^EndChar\n", sfd_text, re.M | re.S)
    }


def header(sfd_text):
    return sfd_text[: sfd_text.index("\nBeginChars: ") + 1]


def splice(original, saved, added, touched):
    """The original source with the saved one's header, its records of the added glyphs, and
    the substitution lines it gave the touched glyphs."""
    old, new = records(original), records(saved)
    keep = re.search(r"^ModificationTime: .*$", original, re.M).group(0)
    head = re.sub(r"^ModificationTime: .*$", keep, header(saved), count=1, flags=re.M)
    body = original[len(header(original)) :]
    for name in touched:
        lines = [ln for ln in new[name].splitlines(True) if ln.startswith("Substitution2: ")]
        extra = "".join(ln for ln in lines if ln not in old[name])
        record = old[name].removesuffix("EndChar\n") + extra + "EndChar\n"
        body = body.replace(old[name], record, 1)
    count = re.search(r"^BeginChars: .*$", saved, re.M).group(0)
    body = re.sub(r"^BeginChars: .*$", count, body, count=1, flags=re.M)
    glyphs = "\n".join(new[name] for name in added)
    return head + body.replace("\nEndChars\n", f"\n\n{glyphs}EndChars\n", 1)


def main(path, source):
    data = json.loads(Path(source).read_text())
    font = fontforge.open(path)
    for name, spec in data["glyphs"].items():
        add(font, name, spec, data["stem"])
    touched = add_stacked_subscripts(font)
    with tempfile.TemporaryDirectory() as tmp:
        saved = Path(tmp) / "out.sfd"
        font.save(str(saved))
        merged = splice(Path(path).read_text(), saved.read_text(), list(data["glyphs"]), touched)
    Path(path).write_text(merged)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "sources/signs.json")
