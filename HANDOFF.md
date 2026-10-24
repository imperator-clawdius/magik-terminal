# HANDOFF — magik-terminal

**One-liner:** A free MIT visual theme + transparent wrapper that reskins OpenAI's Codex CLI with animated shader flames, a syntax theme, and optional pixel-art wallpaper on Windows Terminal and macOS Ghostty.
**Status:** live — ~90% to shippable (published releases; cosmetic polish + distribution remain)
**Monetization:** weak/indirect by design — a free brand/lead-gen funnel to b1scu1tk1d.com; no direct revenue

## What it is
A cosmetic terminal integration for the Codex CLI using the B1SCU1TK1D palette (ink black, cream, amber, turquoise). It installs a syntax theme, an ANSI palette, animated pixel-shader flames/frame/mark, and an optional pixel-art wallpaper, driven by a transparent `codex --magik` wrapper. It is not an OpenAI product and changes nothing about models, auth, or prompts.

## Who pays & why
No direct payer — the tool is free. The beneficiary is the B1SCU1TK1D brand (audience building, portfolio, funnel to the blog). Users are Codex CLI developers who want an aesthetic terminal; willingness to pay for the theme itself is ~0, so the asset's value is attention and brand reach.

## Stack
Python 3.11+ stdlib (`install.py`, `windows/cli.py`, `macos/cli.py`, `theme_settings.py`), PowerShell (`install.ps1`, `windows/launch.ps1`), HLSL pixel shader on Windows Terminal's experimental API (`windows/magik.hlsl`), GLSL port for Ghostty (`macos/magik.glsl`), a Node wallpaper tool (`tools/render-wallpaper.cjs`), ReportLab (dev-only, for the handoff PDF). Edits Codex `config.toml` + Windows Terminal `settings.json`. Multi-OS CI (Windows/Linux/macOS x64+arm).

## Architecture
`install.py` makes surgical, validated edits to Codex `config.toml` (`tui.theme`/`animations`) and Windows Terminal `settings.json` (one profile + color scheme), installs `themes/widowmaker.tmTheme` + the shader, writes `~/.local/bin` codex shims, and records byte-for-byte backups in `install-state.json` for clean uninstall. Runtime: the `codex --magik` wrapper (`windows/cli.py`, `macos/cli.py`) passes through to native Codex unless `--magik` opens the themed window; shaders render flames/frame/mark; `--wallpaper` toggle is persisted. macOS runs a separate isolated Ghostty instance. Key files first: `install.py`, `windows/cli.py`, `windows/magik.hlsl`, `macos/`, `themes/`.

## What works today
- Full Windows install/uninstall: surgical TOML/JSONC edits, backup/restore, PATH shims.
- Transparent `codex` passthrough plus `--magik`/`--yolo`/`--wallpaper`; `--no-daemon` elevation safety.
- HLSL + GLSL shaders with compile checks; separate macOS Ghostty instance.
- Wallpaper persistence, still mode, theme-only/Kitty palette; 500+ lines of tests; multi-OS CI.

## Gaps to ship (ranked)
1. Relies on Windows Terminal's EXPERIMENTAL pixel-shader API, which drivers/WT versions can reject (README documents the fallback). Fragile core.
2. Version-coupled to Codex (tested 0.159.3) and Windows Terminal 1.24 — upstream updates can break the wrapper/theme.
3. Distribution is manual GitHub-release ZIPs (no winget/brew/scoop); Retina/external-display and macOS GUI appearance are explicitly unverified.

## Run it
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
codex --magik
```
```sh
sh install-macos.sh                 # macOS (Ghostty)
python3 install.py --theme-only     # Kitty / palette-only
python -m unittest discover -s tests -v
```

## Risks / unknowns
- Experimental shader API + Codex/WT version drift means ongoing maintenance.
- Depends on the Codex CLI existing and behaving; trademark exposure is managed via the Apache-2.0 asset notice.
- Niche audience (Codex CLI users who also want terminal theming).

## Fastest path to revenue
1. Treat it as a brand funnel — drive installs to b1scu1tk1d.com (newsletter/commissions).
2. Sell custom theme packs / commissioned terminal branding to dev-tool companies.
3. Add sponsorship/donations and package for winget/brew to widen the funnel.
