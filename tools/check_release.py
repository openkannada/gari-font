# SPDX-FileCopyrightText: 2026 The Open Kannada Authors
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Check the Gari release files: fontspector, shaperglot and this repository's tests.

    uv run python tools/check_release.py --fontspector path/to/fontspector

fontspector runs the Google Fonts profile on the release TTF. A FAIL, ERROR or FATAL fails
this script unless release/known-fails.toml lists the check with a reason; a listed check
that now passes is reported, so the list can shrink. Reports go to dist/checks/.
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

ROOT = Path(__file__).parent.parent
KNOWN = ROOT / "release" / "known-fails.toml"
BAD = {"FAIL", "ERROR", "FATAL"}
SHAPERGLOT = "uvx --from shaperglot==1.2.2 shaperglot"


def failing_checks(report: dict) -> dict[str, list[str]]:
    """check id -> the files (or "family") it failed on."""
    out: dict[str, list[str]] = {}
    for path, sections in report["results"].items():
        for checks in sections.values():
            for check in checks:
                if check["worst_status"] in BAD:
                    out.setdefault(check["check_id"], []).append(Path(path).name or "family")
    return out


def fontspector(binary: Path, fonts: list[Path], out: Path) -> dict[str, list[str]]:
    report = out / "fontspector.json"
    command = [str(binary), "--profile", "googlefonts", "--skip-network", "--json", str(report)]
    command += ["--ghmarkdown", str(out / "fontspector.md"), *map(str, fonts)]
    subprocess.run(command, check=False)
    return failing_checks(json.loads(report.read_text()))


def shaperglot(command: str, font: Path, out: Path, allowed: set[str]) -> bool:
    """True when shaperglot finds nothing missing for kn_Knda beyond the allowed characters."""
    result = subprocess.run(
        [*shlex.split(command), "check", str(font), "kn_Knda"],
        capture_output=True,
        text=True,
        check=False,
    )
    (out / "shaperglot.txt").write_text(result.stdout + result.stderr)
    if "100.0%" in result.stdout:
        return True
    missing = {
        ch
        for line in result.stdout.splitlines()
        if "missing from the font:" in line
        for ch in line.split(":", 1)[1].strip()
        if not ch.isspace()
    }
    print(f"shaperglot: missing {' '.join(f'U+{ord(c):04X}' for c in sorted(missing))}")
    return bool(missing) and missing <= allowed


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
    parser.add_argument("--shaperglot", default=SHAPERGLOT, help="command that runs shaperglot")
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    args = parser.parse_args(argv)

    font = next((args.dist / "Gari" / "ttf").glob("*.ttf"))
    out = args.dist / "checks" / "Gari"
    out.mkdir(parents=True, exist_ok=True)

    known = tomllib.loads(KNOWN.read_text())
    allowed = {chr(int(cp.removeprefix("U+"), 16)) for cp in known.pop("shaperglot_missing", {})}
    failed = fontspector(args.fontspector, [font], out)
    new = sorted(set(failed) - set(known))
    for check in sorted(failed):
        print(f"fontspector {check}: {'known' if check in known else 'NEW'}")
    for check in sorted(set(known) - set(failed)):
        print(f"fontspector {check}: listed in known-fails.toml but passes now")
    glot = shaperglot(args.shaperglot, font, out, allowed)
    print(f"shaperglot kn_Knda: {'pass' if glot else 'FAIL'}")
    passed = tests(font)
    print(f"tests on {font.name}: {'pass' if passed else 'FAIL'}")
    return 0 if not new and glot and passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
