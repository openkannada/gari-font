# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Check the Gari release files: names, fontspector, Shaperglot and the tests.

    uv run python tools/check_release.py --fontspector path/to/fontspector

- No font in the release (TTF, OTF, WOFF2) may be named Navilu, the upstream Reserved Font
  Name, in a name record or a CFF name field.
- fontspector runs the Google Fonts profile on the TTF and the OTF. A FAIL, ERROR or FATAL
  fails this script unless release/known-fails.toml lists its check and failure code with a
  reason; a listed failure that no longer occurs is reported, so the list can shrink.
- Shaperglot checks kn_Knda through tools/shaperglot_gate.py; only the characters listed under
  [shaperglot] in known-fails.toml may be missing.
- The tests run on the release TTF.

Reports go to dist/checks/Gari/.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tomllib
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).parent.parent
KNOWN = ROOT / "release" / "known-fails.toml"
BAD = {"FAIL", "ERROR", "FATAL"}
SHAPERGLOT_PYTHON = "uvx --from shaperglot==1.2.2 python"
RESERVED = "navilu"
# Name IDs that name the font: family, style, unique, full, PostScript and their variants.
NAME_IDS = {1, 2, 3, 4, 6, 16, 17, 21, 22, 25}


def reserved_name_left(path: Path) -> list[str]:
    font = TTFont(path)
    found = [
        f"name {r.nameID}"
        for r in font["name"].names
        if r.nameID in NAME_IDS and RESERVED in r.toUnicode().lower()
    ]
    if "CFF " in font:
        cff = font["CFF "].cff
        top = cff.topDictIndex[0]
        fields = {"FontName": " ".join(cff.fontNames)}
        fields |= {k: str(getattr(top, k, "")) for k in ("FullName", "FamilyName")}
        found += [f"CFF {k}" for k, v in fields.items() if RESERVED in v.lower()]
    return found


def failures(report: dict) -> set[tuple[str, str]]:
    """(check id, failure code) for every FAIL, ERROR or FATAL in a fontspector report."""
    return {
        (check["check_id"], sub.get("code") or "")
        for sections in report["results"].values()
        for checks in sections.values()
        for check in checks
        for sub in check["subresults"]
        if sub["severity"] in BAD
    }


def fontspector(binary: Path, fonts: list[Path], out: Path) -> set[tuple[str, str]]:
    report = out / "fontspector.json"
    report.unlink(missing_ok=True)
    command = [str(binary), "--profile", "googlefonts", "--skip-network", "--json", str(report)]
    command += ["--ghmarkdown", str(out / "fontspector.md"), *map(str, fonts)]
    subprocess.run(command, check=False)
    if not report.exists():
        raise SystemExit("fontspector wrote no report")
    return failures(json.loads(report.read_text()))


def shaperglot(python: str, font: Path, out: Path, allowed: list[str]) -> bool:
    gate = ROOT / "tools" / "shaperglot_gate.py"
    result = subprocess.run(
        [*shlex.split(python), str(gate), str(font), *allowed],
        capture_output=True,
        text=True,
        check=False,
    )
    (out / "shaperglot.txt").write_text(result.stdout + result.stderr)
    print(result.stdout.strip())
    return result.returncode == 0


def tests(font: Path) -> bool:
    """Run this repository's tests on the release font."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests"],
        cwd=ROOT,
        env={**os.environ, "FONT": str(font)},
        check=False,
    )
    return result.returncode == 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fontspector", type=Path, required=True)
    parser.add_argument(
        "--shaperglot-python", default=SHAPERGLOT_PYTHON, help="a Python that has Shaperglot"
    )
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    args = parser.parse_args(argv)

    folder = args.dist / "Gari"
    ttf = next((folder / "ttf").glob("*.ttf"))
    otfs = sorted((folder / "otf").glob("*.otf"))
    out = args.dist / "checks" / "Gari"
    out.mkdir(parents=True, exist_ok=True)

    every_font = sorted(p for p in folder.rglob("*") if p.suffix in {".ttf", ".otf", ".woff2"})
    named = {p.name: left for p in every_font if (left := reserved_name_left(p))}
    print(f"names: {named or f'no font in the {len(every_font)} is named Navilu'}")

    known_file = tomllib.loads(KNOWN.read_text())
    allowed = sorted(known_file.pop("shaperglot", {}).get("missing", []))
    known = {(check, code) for check, entry in known_file.items() for code in entry["codes"]}
    found = fontspector(args.fontspector, [ttf, *otfs], out)
    for check, code in sorted(found):
        print(f"fontspector {check} ({code}): {'known' if (check, code) in known else 'NEW'}")
    for check, code in sorted(known - found):
        print(f"fontspector {check} ({code}): listed in known-fails.toml but passes now")
    glot = shaperglot(args.shaperglot_python, ttf, out, allowed)
    passed = tests(ttf)
    print(f"tests on {ttf.name}: {'pass' if passed else 'FAIL'}")
    return 0 if not named and found <= known and glot and passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
