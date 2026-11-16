"""Add new-order Kannada shaping (knd2) to a FontForge source that only has knda.

Run with FontForge's Python: fontforge -lang=py -script tools/add_knd2.py Gari.sfd

Every lookup registered for knda is also registered for knd2, except the below-base
ligatures. Old-order shapers hand blwf a consonant then a virama; new-order shapers hand
it a virama then a consonant. Each blwf ligature lookup gets a knd2 twin with the
components swapped, placed right after it so lookup order is kept.

A cluster that ends in a virama (ಸ್ಟ್) also differs. Old-order shapers move that virama
next to the base, where the font's contextual rules expect it; new-order shapers leave it
after the subscript. For knd2 the base gets its virama form when a subscript and a virama
follow, and a pair adjustment draws the virama and the subscript where old order draws them.
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


def swapped_twin(font, lookup, virama):
    kind, flags, features = font.getLookupInfo(lookup)
    twin = f"{lookup} knd2"
    font.addLookup(
        twin, kind, flags, tuple((t, (("knd2", ("dflt",)),)) for t, _ in features), lookup
    )
    for subtable in font.getLookupSubtables(lookup):
        twin_sub = f"{subtable} knd2"
        font.addLookupSubtable(twin, twin_sub)
        for glyph in font.glyphs():
            for _, kind_, *components in glyph.getPosSub(subtable):
                if kind_ == "Ligature" and len(components) == 2 and components[1] == virama:
                    glyph.addPosSub(twin_sub, (virama, components[0]))
    return twin


def ligature_outputs(font, lookup):
    subtables = set(font.getLookupSubtables(lookup))
    return [
        g.glyphname
        for g in font.glyphs()
        if any(p[0] in subtables and p[1] == "Ligature" for p in g.getPosSub("*"))
    ]


def single_sources(font, lookup):
    subtables = set(font.getLookupSubtables(lookup))
    return [
        g.glyphname
        for g in font.glyphs()
        if any(p[0] in subtables and p[1] == "Substitution" for p in g.getPosSub("*"))
    ]


def final_virama_rules(font, subscripts, virama, base_form, after):
    """Give knd2 the old-order look for base + subscript + virama."""
    knd2 = (("knd2", ("dflt",)),)
    bases = " ".join(single_sources(font, base_form))
    subs = " ".join(subscripts)
    context = "knd2 final virama base"
    font.addLookup(context, "gsub_contextchain", (), (("psts", knd2),), after)
    font.addContextualSubtable(
        context,
        f"{context} subtable",
        "coverage",
        f"| [{bases}] @<{base_form}> | [{subs}] [{virama}]",
    )
    swap = "knd2 final virama position"
    font.addLookup(swap, "gpos_pair", (), (("dist", knd2),))
    font.addLookupSubtable(swap, f"{swap} subtable")
    virama_advance = font[virama].width
    for name in subscripts:
        font[name].addPosSub(
            f"{swap} subtable", virama, virama_advance, 0, 0, 0, -font[name].width, 0, 0, 0
        )


def main(path, base_form, after):
    font = fontforge.open(path)
    if any(
        script == "knd2"
        for lookup in font.gsub_lookups
        for _, scripts in font.getLookupInfo(lookup)[2]
        for script, _ in scripts
    ):
        sys.exit(f"{path} already has knd2 lookups")
    virama = next(g.glyphname for g in font.glyphs() if g.unicode == VIRAMA)
    subscripts = []
    for lookup in list(font.gsub_lookups) + list(font.gpos_lookups):
        info = font.getLookupInfo(lookup)
        if is_blwf_ligature(info):
            font.lookupSetFeatureList(lookup, knda_only(info[2]))
            swapped_twin(font, lookup, virama)
            subscripts += ligature_outputs(font, lookup)
        elif info[2]:
            font.lookupSetFeatureList(lookup, with_knd2(info[2]))
    final_virama_rules(font, sorted(set(subscripts)), virama, base_form, after)
    font.save(path)


if __name__ == "__main__":
    # Lookup 17 maps each base to the form that takes a virama; psts lookup 4 applies it.
    main(
        sys.argv[1],
        "Single Substitution lookup 17",
        "'psts' Post Base Substitutions in Kannada lookup 4",
    )
