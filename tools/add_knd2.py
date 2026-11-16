"""Add new-order Kannada shaping (knd2) to a FontForge source that only has knda.

Run with FontForge's Python: fontforge -lang=py -script tools/add_knd2.py Gari.sfd

Every lookup registered for knda is also registered for knd2, except the below-base
ligatures. Old-order shapers hand blwf a consonant then a virama; new-order shapers hand
it a virama then a consonant. Each blwf ligature lookup gets a knd2 twin with the
components swapped, placed right after it so lookup order is kept.

A cluster that ends in a virama (ಸ್ಟ್, ಕ್ಸ್ಟ್) also differs. Old-order shapers move that
virama next to the base, where the font's contextual rules expect it; new-order shapers leave
it after the subscripts. For knd2, 2 passes of GSUB lookups move it back in front of up to 2
subscripts before any presentation lookup runs, so the knda rules then apply unchanged.
"""

import sys

import fontforge

VIRAMA = 0x0CCD


def with_knd2(features):
    out = []
    for tag, scripts in features:
        names = [s for s, _ in scripts]
        if "knda" in names and "knd2" not in names:
            langs = dict(scripts)["knda"]
            scripts = (*scripts, ("knd2", langs))
        out.append((tag, scripts))
    return tuple(out)


def knda_only(features):
    return tuple((tag, tuple(s for s in scripts if s[0] == "knda")) for tag, scripts in features)


def is_blwf_ligature(info):
    kind, _, features = info
    return kind == "gsub_ligature" and any(tag == "blwf" for tag, _ in features)


def knda_langs(font):
    """The language systems the font registers under knda."""
    for lookup in font.gsub_lookups:
        for _, scripts in font.getLookupInfo(lookup)[2]:
            if "knda" in dict(scripts):
                return dict(scripts)["knda"]
    raise ValueError("the font has no knda lookups")


def swapped_twin(font, lookup, virama, langs):
    kind, flags, features = font.getLookupInfo(lookup)
    twin = f"{lookup} knd2"
    font.addLookup(twin, kind, flags, tuple((t, (("knd2", langs),)) for t, _ in features), lookup)
    for subtable in font.getLookupSubtables(lookup):
        twin_sub = f"{subtable} knd2"
        font.addLookupSubtable(twin, twin_sub)
        for glyph in font.glyphs():
            for _, kind_, *components in glyph.getPosSub(subtable):
                if kind_ == "Ligature" and len(components) == 2 and components[1] == virama:
                    glyph.addPosSub(twin_sub, (virama, components[0]))


def outputs(font, lookup, kind):
    """Glyphs that a lookup's subtables produce with entries of this kind."""
    subtables = set(font.getLookupSubtables(lookup))
    return [
        g.glyphname
        for g in font.glyphs()
        if any(p[0] in subtables and p[1] == kind for p in g.getPosSub("*"))
    ]


def final_virama_reorder(font, subscripts, virama, langs, after):
    """Move a final virama in front of up to 2 subscripts, where old-order shaping puts it.

    Each pass joins subscript + virama into a temporary glyph, then splits it into virama +
    subscript, so the virama moves back 1 subscript per pass.
    """
    knd2 = (("knd2", langs),)
    temporary = {s: font.createChar(-1, f"{s}_{virama}.knd2") for s in subscripts}
    for glyph in temporary.values():
        glyph.width = 0
    for n in (1, 2):
        join, split = f"knd2 final virama join {n}", f"knd2 final virama split {n}"
        font.addLookup(join, "gsub_ligature", (), (("psts", knd2),), after)
        font.addLookupSubtable(join, f"{join} subtable")
        font.addLookup(split, "gsub_multiple", (), (("psts", knd2),), join)
        font.addLookupSubtable(split, f"{split} subtable")
        for s, glyph in temporary.items():
            glyph.addPosSub(f"{join} subtable", (s, virama))
            glyph.addPosSub(f"{split} subtable", (virama, s))
        after = split


def main(path, after):
    font = fontforge.open(path)
    if any(
        script == "knd2"
        for lookup in font.gsub_lookups
        for _, scripts in font.getLookupInfo(lookup)[2]
        for script, _ in scripts
    ):
        sys.exit(f"{path} already has knd2 lookups")
    virama = next(g.glyphname for g in font.glyphs() if g.unicode == VIRAMA)
    langs = knda_langs(font)
    subscripts = []
    for lookup in list(font.gsub_lookups) + list(font.gpos_lookups):
        info = font.getLookupInfo(lookup)
        if is_blwf_ligature(info):
            font.lookupSetFeatureList(lookup, knda_only(info[2]))
            swapped_twin(font, lookup, virama, langs)
            subscripts += outputs(font, lookup, "Ligature")
        elif info[2]:
            font.lookupSetFeatureList(lookup, with_knd2(info[2]))
    final_virama_reorder(font, sorted(set(subscripts)), virama, langs, after)
    font.save(path)


if __name__ == "__main__":
    # The reordering must run before every presentation lookup, so it follows the reph lookup.
    main(sys.argv[1], "'rphf' Reph Form in Kannada lookup 0")
