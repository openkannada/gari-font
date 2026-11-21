# Gari

Gari is a Kannada handwriting-style font. It is a modified version of Navilu by Aravinda VK, which is based on work by the Indian Institute of Science, Bangalore.

Navilu is licensed under the SIL Open Font License 1.1 with the Reserved Font Name "Navilu". The license does not allow a modified version to use that name, so this version is called Gari.

## Changes from Navilu 1.2

See `ChangeLog`. In short:

- New-order Kannada shaping (`knd2`), which HarfBuzz and DirectWrite use when a font has it, alongside the old `knda` rules.
- U+0CDC ARCHAIC SHRII, U+0CDD NAKAARA POLLU and U+0CF3 COMBINING ANUSVARA ABOVE RIGHT.
- The rest of the Kannada block and the dandas: ಀ ಁ ಄ ಼ ಽ ೢ ೣ ೱ ೲ । ॥, drawn in Gari's own stroke.

## Install

Copy `Gari.ttf` to your fonts folder (`~/.fonts` on Linux, then run `fc-cache`), or open it and choose Install on macOS or Windows.

## Build

Build `Gari.ttf` from `Gari.sfd` with FontForge, then finish it with `tools/finish.py`, which needs fontTools (`uv run` provides it):

    uv run make

`make fedora` writes source and binary tarballs to `/tmp`; the source tarball includes `tools/finish.py`.

`sources/signs.json` holds the skeletons of the signs added after 1.300, and `tools/add_signs.py` strokes them with Gari's round pen and adds them to `Gari.sfd` (`fontforge -lang=py -script tools/add_signs.py Gari.sfd`). It also adds the shaping the signs need (its docstring lists it), with `tools/mark_offsets.py` working out where the nukta and candrabindu go and `tools/sfd_splice.py` copying only the additions into the source. It refuses a character that already has a glyph, so edit a sign in `Gari.sfd` itself once it is there.

## Test

Run the shaping tests against the built font (needs [uv](https://docs.astral.sh/uv/)):

    uv run pytest

Set `FONT=path/to/font.ttf` to test another build.

CI also runs [font-health-action](https://github.com/openkannada/font-health-action) on `Gari.ttf`: 2,146 Kannada shaping strings and Shaperglot's `kn_Knda` checks. [font-health/baseline.json](font-health/baseline.json) lists the failures Gari has today (35 clusters ending in ೞ with no conjunct), so the check fails only on new ones. Shaperglot reports full `kn_Knda` support. The job checks the committed `Gari.ttf`, so rebuild it with the source change. Shrink the baseline as gaps are fixed.

## Release

    uv sync --group release
    uv run python tools/release.py
    uv run python tools/check_release.py --fontspector path/to/fontspector

`tools/release.py` builds the TTF from `Gari.sfd` as `make` does (`generate.pe`, then `tools/finish.py`) and an OTF with FontForge, both in `build/release/` so the committed `Gari.ttf` is left alone, and writes `dist/Gari/` and `dist/Gari-1.300.zip` with a `.sha256` file. The folder holds the TTF and OTF, WOFF2 for the web, `web/Gari-Kannada.woff2` cut to Kannada for websites, a 1-page `specimen.html`, `OFL.txt`, `FONTLOG.txt` and `SHA256SUMS`.

`tools/check_release.py` runs fontspector with the Google Fonts profile, Shaperglot for `kn_Knda`, and the tests on the release font. `release/known-fails.toml` lists what fails for reasons outside the release, with the reason: Gari has no Latin letters. Shaperglot reports full `kn_Knda` support. The `Release build` workflow does all of this and keeps the zip, its checksum and the reports as artifacts. It sets `SOURCE_DATE_EPOCH` to the time of the commit under test, so a build with the same FontForge version gives the same bytes. Different FontForge versions order 2 GSUB feature records differently, which changes no shaping.

## License

The font is under the SIL Open Font License 1.1; see [OFL.txt](OFL.txt). Gari adds no Reserved Font Name of its own. The scripts and tests written for this fork are under MIT OR Apache-2.0. [NOTICE.md](NOTICE.md) credits the upstream authors and lists which files are under which license. [CONTRIBUTING.md](CONTRIBUTING.md) explains the sign-off.

Part of [Open Kannada](https://github.com/openkannada), free and open-source tools that make Kannada work properly on computers.
