# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Copy what a script added to a FontForge source into the original text, and nothing else.

FontForge rewrites some glyphs it did not touch when it saves a font, so a script that adds
glyphs or lookups takes from FontForge's output only the header (where lookups and mark classes
live), the records of the glyphs it added, and the lines of its own lookup subtables in the
other glyphs. Every other line of the original is kept as it is.
"""

from __future__ import annotations

import re

RECORD = re.compile(r"^StartChar: (\S+)\n.*?^EndChar\n", re.M | re.S)
LOOKUP_LINE = re.compile(r'^\w+2: "([^"]+)"')


def records(sfd_text: str) -> dict[str, str]:
    """Glyph name to its StartChar ... EndChar record."""
    return {m.group(1): m.group(0) for m in RECORD.finditer(sfd_text)}


def header(sfd_text: str) -> str:
    return sfd_text[: sfd_text.index("\nBeginChars: ") + 1]


def lookup_lines(record: str, subtables: set[str]) -> list[str]:
    """The record's substitution and positioning lines that belong to the given subtables."""
    out = []
    for line in record.splitlines(True):
        m = LOOKUP_LINE.match(line)
        if m and m.group(1) in subtables:
            out.append(line)
    return out


def splice(original: str, saved: str, added: list[str], subtables: set[str]) -> str:
    """The original source with the saved header (but the original ModificationTime), the saved
    records of the added glyphs, and the saved lines of the given subtables in other glyphs."""
    old, new = records(original), records(saved)
    if missing := [name for name in added if name not in new]:
        raise ValueError(f"the saved source has no record of {', '.join(missing)}")
    if present := [name for name in added if name in old]:
        raise ValueError(f"the original source already has {', '.join(present)}")
    keep = re.search(r"^ModificationTime: .*$", original, re.M).group(0)
    head = re.sub(r"^ModificationTime: .*$", keep, header(saved), count=1, flags=re.M)
    body = original[len(header(original)) :]
    for name, record in old.items():
        extra = [ln for ln in lookup_lines(new.get(name, ""), subtables) if ln not in record]
        if extra:
            body = body.replace(
                record, record.removesuffix("EndChar\n") + "".join(extra) + "EndChar\n", 1
            )
    count = re.search(r"^BeginChars: .*$", saved, re.M).group(0)
    body = re.sub(r"^BeginChars: .*$", count, body, count=1, flags=re.M)
    glyphs = "\n".join(new[name] for name in added)
    return head + body.replace("\nEndChars\n", f"\n\n{glyphs}EndChars\n", 1)


def chain_contexts(sfd_text: str) -> list[tuple[str, int, list[str]]]:
    """For each lookup a contextual substitution applies: (lookup name, the input position it
    applies at, the glyphs that may come just before that position)."""
    out = []
    for block in re.findall(r"^ChainSub2: coverage .*?^EndFPST$", sfd_text, re.M | re.S):
        inputs, backtrack = [], []
        for line in block.splitlines():
            line = line.strip()
            for key, into in (("Coverage: ", inputs), ("BCoverage: ", backtrack)):
                if line.startswith(key):
                    into.append(line[len(key) :].split(" ", 1)[1].split())
            if line.startswith("SeqLookup: "):
                position, name = line[len("SeqLookup: ") :].split(" ", 1)
                k = int(position)
                before = inputs[k - 1] if k else (backtrack[0] if backtrack else [])
                out.append((name.strip('"'), k, before))
    return out
