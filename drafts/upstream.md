# Notes for aravindavk/Navilu

Gari is a renamed fork, so its changes cannot go back as one pull request under the Navilu name. To offer them upstream, the useful parts are:

- `tools/add_knd2.py`, which adds new-order (`knd2`) shaping to `Navilu.sfd` without touching the `knda` rules. Run on upstream `Navilu.sfd`, it gives a font in which every 2- and 3-consonant cluster, with or without a final virama, shapes under `knd2` exactly as under `knda`.
- The 3 drafted glyphs for U+0CDC, U+0CDD and U+0CF3, from kannadi `tools/glyphdraft`.

Draft issue text:

> Title: Add new-order (knd2) shaping and 3 new characters
>
> Navilu has only old-order `knda` rules, and no glyphs for U+0CDC, U+0CDD and U+0CF3. I have a script that adds `knd2` rules to `Navilu.sfd` (tested to shape every 2- and 3-consonant cluster the same as `knda` in HarfBuzz) and drafts of the 3 characters matched to Navilu's stems. Would you like them as a pull request?
