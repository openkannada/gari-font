# Gari

Gari is a Kannada handwriting-style font. It is a modified version of Navilu by Aravinda VK, which is based on work by the Indian Institute of Science, Bangalore.

Navilu is licensed under the SIL Open Font License 1.1 with the Reserved Font Name "Navilu". The license does not allow a modified version to use that name, so this version is called Gari.

## Changes from Navilu 1.2

See `ChangeLog`. In short:

- New-order Kannada shaping (`knd2`), which HarfBuzz and DirectWrite use when a font has it, alongside the old `knda` rules.
- U+0CDC ARCHAIC SHRII, U+0CDD NAKAARA POLLU and U+0CF3 COMBINING ANUSVARA ABOVE RIGHT.

## Install

Copy `Gari.ttf` to your fonts folder (`~/.fonts` on Linux, then run `fc-cache`), or open it and choose Install on macOS or Windows.

## Build

Build `Gari.ttf` from `Gari.sfd` with FontForge:

    make

`make fedora` writes source and binary tarballs to `/tmp`.

## Test

Run the shaping tests against the built font (needs [uv](https://docs.astral.sh/uv/)):

    uv run pytest

Set `FONT=path/to/font.ttf` to test another build.

## Release

    uv sync --group release
    uv run python tools/release.py
    uv run python tools/check_release.py --fontspector path/to/fontspector

`tools/release.py` builds `Gari.ttf` from `Gari.sfd` with `make`, generates an OTF with FontForge, and writes `dist/Gari/` and `dist/Gari-1.300.zip` with a `.sha256` file. The folder holds the TTF and OTF, WOFF2 for the web, `web/Gari-Kannada.woff2` cut to Kannada for websites, a 1-page `specimen.html`, `OFL.txt`, `FONTLOG.txt` and `SHA256SUMS`.

`tools/check_release.py` runs fontspector with the Google Fonts profile, Shaperglot for `kn_Knda`, and the tests on the release font. `release/known-fails.toml` lists what fails for reasons outside the release, with the reason: Gari has no Latin letters, and it has no nukta (U+0CBC) or avagraha (U+0CBD) yet. The `Release build` workflow does all of this and keeps the zip, its checksum and the reports as artifacts. It sets `SOURCE_DATE_EPOCH` to the last commit's time, so a build with the same FontForge version gives the same bytes. Different FontForge versions order 2 GSUB feature records differently, which changes no shaping.

## License

The font is under the SIL Open Font License 1.1; see [OFL.txt](OFL.txt). Gari adds no Reserved Font Name of its own. The scripts and tests written for this fork are under MIT OR Apache-2.0. [NOTICE.md](NOTICE.md) credits the upstream authors and lists which files are under which license. [CONTRIBUTING.md](CONTRIBUTING.md) explains the sign-off.

Part of [Open Kannada](https://github.com/openkannada), free and open-source tools that make Kannada work properly on computers.
