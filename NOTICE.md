# Notices

Gari is a modified version of Navilu. These authors made the work it is built on:

| Work | Authors | License | Used here |
|---|---|---|---|
| Navilu 1.2 | Aravinda VK, 2011-2012 ([aravindavk/Navilu](https://github.com/aravindavk/Navilu)) | OFL-1.1, with the Reserved Font Name "Navilu" | `Gari.sfd`, `Gari.ttf`, `generate.pe`, `Makefile`, `fedora_makefile`, `tools/release` and `ChangeLog` derive from it |
| The glyphs Navilu was drawn from | Indian Institute of Science, Bangalore, 2005-2010 | OFL-1.1, through Navilu | The outlines in `Gari.sfd` |

The signs added after Gari 1.300 (ಀ ಁ ಄ ಼ ಽ ೢ ೣ ೱ ೲ । ॥) took their structure, size and position from Noto Sans Kannada 2.006 (The Noto Project Authors) and Tiro Kannada 1.65 (The Indigo Project Authors), both OFL-1.1. No outlines were copied: each sign is a skeleton stroked with Gari's own pen.

Because Navilu reserves its name, this modified version may not be called Navilu. It is called Gari.

## What is licensed how

| Files | License |
|---|---|
| The font: `Gari.sfd`, `Gari.ttf`, `sources/signs.json`, `generate.pe`, the Makefiles and `tools/release` (upstream's shell script for tarballs, separate from `tools/release.py`) | OFL-1.1, see [OFL.txt](OFL.txt) |
| Scripts, tests and configuration written for this fork: `tools/add_knd2.py`, `tools/add_signs.py`, `tools/finish.py`, `tools/release.py`, `tools/check_release.py`, `tools/specimen.py`, `specimen/template.html`, `release/`, `font-health/`, `tests/`, `pyproject.toml`, `uv.lock`, `.github/workflows/` | MIT OR Apache-2.0, copyright The Open Kannada Authors, see [LICENSES](LICENSES) |
| Documents written for this fork: `README.md`, `FONTLOG.txt`, `NOTICE.md`, `CONTRIBUTING.md`, `drafts/`, `specimen/signs-proof.png` | CC BY 4.0, copyright The Open Kannada Authors, see [LICENSES/CC-BY-4.0.txt](LICENSES/CC-BY-4.0.txt) |
| `specimen/sample-kn.json`: Kannada sample text from [googlefonts/lang](https://github.com/googlefonts/lang) (`kn_Knda.textproto`, from the Kannada translation of the Universal Declaration of Human Rights), with 4 typos fixed | Apache-2.0, as googlefonts/lang |
