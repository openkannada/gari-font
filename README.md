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

## License

The font is under the SIL Open Font License 1.1; see [OFL.txt](OFL.txt). Gari adds no Reserved Font Name of its own. The scripts and tests written for this fork are under MIT OR Apache-2.0. [NOTICE.md](NOTICE.md) credits the upstream authors and lists which files are under which license. [CONTRIBUTING.md](CONTRIBUTING.md) explains the sign-off.

Part of [Open Kannada](https://github.com/openkannada), free and open-source tools that make Kannada work properly on computers.
