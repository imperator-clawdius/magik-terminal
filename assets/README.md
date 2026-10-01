# B1SCU1TK1D pixel landscape

The original artwork is the background of https://b1scu1tk1d.com, supplied by
the site's owner for inclusion in this theme. The SVG is copied from
https://b1scu1tk1d.com/landscape.svg and is included under this project's MIT license.

Original SVG SHA-256 (LF line endings):
`0f01ee48069c7b024e52a5256ede084912e998a15a4ed6cc3a4ed071d8a71a7c`

The PNG is a 1600 × 900 rasterization of the SVG, retaining the original pixel
shapes and colors. `tools/render-wallpaper.cjs` reproduces it with Playwright.
There is no runtime download or image-generation dependency.

Windows Terminal blends the image at 10% opacity over the theme's ink background.
This keeps the theme's normal text palette above a 4.5:1 contrast ratio even
against a hypothetical white wallpaper pixel. Codex controls some dimmed UI
text and selection colors separately; those are not covered by that palette check.

## Codex blossom mark

`codex-mark.svg` and its transparent PNG reproduce the braille-dot layout from
OpenAI Codex's `onboarding_settled_logo` snapshot. The source snapshot is included
as `codex-mark-source.snap`; upstream is
https://github.com/openai/codex/blob/main/codex-rs/tui/src/snapshots/codex_tui__empty_state_animation__tests__onboarding_settled_logo.snap.
This asset is derived from OpenAI's Apache-2.0-licensed Codex source; the upstream
license is included as `CODEX-LICENSE.txt`. OpenAI's marks remain its own.
The community theme is not an official OpenAI product.

The shader displays the mark at 25% of its original default-font dimensions,
centered in the bottom-right quarter, and masks it behind text. Native welcome
animations are disabled in the Codex TUI settings to avoid a duplicate centered
mark. The theme's own flames continue to animate unless still mode is selected.
