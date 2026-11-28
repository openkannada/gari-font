# Gari

Gari is a free, handwriting-style Kannada font, built on Navilu by Aravinda VK. It adds the new-order Kannada shaping (`knd2`) that HarfBuzz and DirectWrite use, the engines behind browsers, LibreOffice and Windows, and the newest Unicode letters. Version 1.300 shapes 2,035 of the 2,146 Kannada test strings in [font-health-action](https://github.com/openkannada/font-health-action) correctly.

Navilu, which is based on work by the Indian Institute of Science, Bangalore, is licensed under the SIL Open Font License 1.1 with the Reserved Font Name "Navilu". The license does not allow a modified version to use that name, so this version is called Gari.

## Quick start

Download [Gari-1.300.zip](https://github.com/openkannada/gari-font/releases/download/v1.300/Gari-1.300.zip). It holds TTF, OTF and WOFF2 files and a Kannada-only web font for websites:

```css
@font-face { font-family: "Gari"; src: url("web/Gari-Kannada.woff2") format("woff2"); }
:lang(kn) { font-family: "Gari", sans-serif; }
```

See it beside Neha Sans and Neha Serif at [openkannada.org/fonts](https://openkannada.org/fonts/).

## Results

Measured on `Gari.ttf` 1.300 with [font-health-action](https://github.com/openkannada/font-health-action) and Shaperglot. [font-health/baseline.json](font-health/baseline.json) lists every known failure.

| Check | Result |
|---|---|
| Kannada shaping strings that shape correctly | 2,035 of 2,146 |
| Clusters with no conjunct | 35, all ending in ೞ |
| Strings with a missing glyph | 76, mostly ೢ and ೣ |
| Marks that touch another glyph, for a person to judge | 8 |
| Shaperglot `kn_Knda` | 20%: only the code point check fails, on the missing nukta and avagraha; every shaping check passes |

## Changes from Navilu 1.2

See `ChangeLog`. In short:

- New-order Kannada shaping (`knd2`), which HarfBuzz and DirectWrite use when a font has it, alongside the old `knda` rules.
- U+0CDC ARCHAIC SHRII, U+0CDD NAKAARA POLLU and U+0CF3 COMBINING ANUSVARA ABOVE RIGHT.

## Install

Copy `Gari.ttf` to your fonts folder (`~/.fonts` on Linux, then run `fc-cache`), or open it and choose Install on macOS or Windows.

## Build

Build `Gari.ttf` from `Gari.sfd` with FontForge, then finish it with `tools/finish.py`, which needs fontTools (`uv run` provides it):

    uv run make

`make fedora` writes source and binary tarballs to `/tmp`; the source tarball includes `tools/finish.py`.

## Test

Run the shaping tests against the built font (needs [uv](https://docs.astral.sh/uv/)):

    uv run pytest

Set `FONT=path/to/font.ttf` to test another build.

CI also runs [font-health-action](https://github.com/openkannada/font-health-action) on `Gari.ttf`: 2,146 Kannada shaping strings and Shaperglot's `kn_Knda` checks. [font-health/baseline.json](font-health/baseline.json) lists the failures Gari has today (35 clusters ending in ೞ with no conjunct, 76 strings with a missing glyph, mostly ೢ and ೣ), so the check fails only on new ones. Shaperglot passes with the nukta and avagraha allowed to be missing, as in `release/known-fails.toml`. The job checks the committed `Gari.ttf`, so rebuild it with the source change. Shrink the baseline as gaps are fixed.

## Release

    uv sync --group release
    uv run python tools/release.py
    uv run python tools/check_release.py --fontspector path/to/fontspector

`tools/release.py` builds the TTF from `Gari.sfd` as `make` does (`generate.pe`, then `tools/finish.py`) and an OTF with FontForge, both in `build/release/` so the committed `Gari.ttf` is left alone, and writes `dist/Gari/` and `dist/Gari-1.300.zip` with a `.sha256` file. The folder holds the TTF and OTF, WOFF2 for the web, `web/Gari-Kannada.woff2` cut to Kannada for websites, a 1-page `specimen.html`, `OFL.txt`, `FONTLOG.txt` and `SHA256SUMS`.

`tools/check_release.py` runs fontspector with the Google Fonts profile, Shaperglot for `kn_Knda`, and the tests on the release font. `release/known-fails.toml` lists what fails for reasons outside the release, with the reason: Gari has no Latin letters, and it has no nukta (U+0CBC) or avagraha (U+0CBD) yet, so Shaperglot scores `kn_Knda` at 20%: its mandatory codepoint check fails on those 2 characters and every other check passes. The `Release build` workflow does all of this and keeps the zip, its checksum and the reports as artifacts. It sets `SOURCE_DATE_EPOCH` to the time of the commit under test, so a build with the same FontForge version gives the same bytes. Different FontForge versions order 2 GSUB feature records differently, which changes no shaping.

## Related

- [Neha Sans and Neha Serif](https://github.com/openkannada/neha-fonts): text fonts for Kannada, built from Noto.
- [font-health-action](https://github.com/openkannada/font-health-action): the Kannada shaping tests Gari runs on every commit.
- [kannadi](https://github.com/openkannada/kannadi): converts old Nudi and Baraha documents to Unicode, so they can be set in fonts like this one.
- [Navilu](https://github.com/aravindavk/navilu): the upstream font by Aravinda VK.

## License

The font is under the SIL Open Font License 1.1; see [OFL.txt](OFL.txt). Gari adds no Reserved Font Name of its own. The scripts and tests written for this fork are under MIT OR Apache-2.0. [NOTICE.md](NOTICE.md) credits the upstream authors and lists which files are under which license. [CONTRIBUTING.md](CONTRIBUTING.md) explains the sign-off.

Part of [Open Kannada](https://github.com/openkannada), free and open-source tools that make Kannada work properly on computers.
