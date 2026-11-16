# Gari

Gari is a Kannada handwriting-style font. It is a modified version of Navilu by Aravinda VK, which is based on work by the Indian Institute of Science, Bangalore.

Navilu is licensed under the SIL Open Font License 1.1 with the Reserved Font Name "Navilu". The license does not allow a modified version to use that name, so this version is called Gari. Gari is under the same license; see `COPYING`.

## Changes from Navilu 1.2

See `ChangeLog`. In short:

- New-order Kannada shaping (`knd2`), which HarfBuzz and DirectWrite use when a font has it, alongside the old `knda` rules.

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
