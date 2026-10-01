"""Build the human/agent handoff PDF. Development dependency: reportlab."""
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/magik-terminal-hermes-handoff.pdf'
TITLE = 'Magik Terminal for Codex (By W1d0wm4k3r)'
REPO = 'https://github.com/imperator-clawdius/magik-terminal'
VERSION = 'v0.3.0'
INK, AMBER, CYAN = [colors.HexColor(v) for v in ('#07070a', '#f0b34a', '#3be0c8')]
styles = getSampleStyleSheet()
styles.add(ParagraphStyle('Body', fontName='Helvetica', fontSize=10, leading=14,
                          textColor=INK, spaceAfter=8))
styles.add(ParagraphStyle('SmallBody', parent=styles['Body'], fontSize=8.5, leading=11.5))
styles.add(ParagraphStyle('CodeBody', fontName='Courier', fontSize=8.2, leading=11.5,
                          backColor=colors.HexColor('#f2efe6'), borderPadding=8,
                          spaceBefore=5, spaceAfter=12, splitLongWords=True))
styles.add(ParagraphStyle('Section', fontName='Helvetica-Bold', fontSize=22,
                          leading=27, textColor=INK, spaceAfter=15))
styles.add(ParagraphStyle('Subsection', fontName='Helvetica-Bold', fontSize=12,
                          leading=16, spaceBefore=8, spaceAfter=6))
styles.add(ParagraphStyle('CoverTitle', fontName='Helvetica-Bold', fontSize=34,
                          leading=38, spaceAfter=12))
styles.add(ParagraphStyle('Caption', parent=styles['SmallBody'], alignment=TA_CENTER,
                          textColor=colors.HexColor('#555360')))
story = []


def p(text, style='Body'):
    story.append(Paragraph(text, styles[style]))


def code(text):
    p(escape(text).replace('\n', '<br/>'), 'CodeBody')


def sub(text):
    p(escape(text), 'Subsection')


def page(title):
    if story:
        story.append(PageBreak())
    p(escape(title), 'Section')


def table(rows, widths):
    data = [[Paragraph(escape(str(cell)).replace('\n', '<br/>'), styles['SmallBody'])
             for cell in row] for row in rows]
    item = Table(data, colWidths=widths, hAlign='LEFT', repeatRows=1)
    item.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AMBER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f4f0')]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('LINEBELOW', (0, 0), (-1, 0), 1, INK),
    ]))
    story.append(item)
    story.append(Spacer(1, 10))


def link(label, url):
    return f'<a href="{escape(url, {chr(34): "&quot;"})}" color="#08685d">{escape(label)}</a>'


def chrome(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(INK)
    canvas.rect(0, 756, 612, 36, fill=1, stroke=0)
    canvas.setFillColor(CYAN)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(44, 770, 'MAGIK TERMINAL / HERMES AGENT HANDOFF')
    canvas.setFillColor(AMBER)
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(568, 770, VERSION + ' / 01 OCT 2026')
    canvas.setStrokeColor(AMBER)
    canvas.line(44, 40, 568, 40)
    canvas.setFillColor(colors.HexColor('#555360'))
    canvas.setFont('Helvetica', 8)
    canvas.drawString(44, 27, 'Magik Terminal for Codex (By W1d0wm4k3r)')
    canvas.drawRightString(568, 27, str(doc.page))
    canvas.restoreState()


p('Magik Terminal<br/>for Codex', 'CoverTitle')
p('(By W1d0wm4k3r)', 'Section')
p('Implementation record &amp; Hermes agent handoff', 'Subsection')
p('Release v0.3.0 · 1 October 2026 · Prepared from the implemented source, local installation, and validation results.')
p('A portable foundation for continuing the work: what was built, where it lives, how it launches, how it persists, and how to change it without losing the user\'s settings.')
image_path = ROOT / 'docs/wallpaper-on.png'
iw, ih = ImageReader(str(image_path)).getSize()
story.append(Image(str(image_path), width=524, height=524 * ih / iw))
p('Actual Windows Terminal capture. Original blog wallpaper, digital flames, rounded prompt, and quarter-size Codex mark.', 'Caption')
p(link('Source repository', REPO) + ' · ' + link('Tagged release', REPO + '/releases/tag/' + VERSION)
  + ' · ' + link('Blog and download', 'https://b1scu1tk1d.com/#magik-terminal'))
p('<b>Reading map:</b> 2 changes &amp; palette; 3 architecture; 4 command routing; 5 graphics; '
  '6 persistent state; 7 operations; 8 verification &amp; publishing; 9 Hermes operating brief; 10 provenance &amp; limits; 11 Mac architecture; 12 Mac verification and acceptance.', 'SmallBody')
p('This PDF transfers implementation knowledge and an actionable workflow. It does not install or register a Hermes skill, configure Hermes, or assert that Hermes has read it.', 'SmallBody')

page('2 / What was implemented')
table([
    ['Request', 'Implemented result'],
    ['Identity', TITLE + '. Updated profile/tab, launcher banner, installer messages, theme metadata, README, blog, local preference instructions, and branded desktop shortcut.'],
    ['Launch', 'codex --magik; opt-in codex --magik --yolo. Native Codex remains the underlying process.'],
    ['Palette and framing', 'B1SCU1TK1D colors; animated side flames, cyber corner brackets, subtle circuit grid, matching ANSI and syntax colors.'],
    ['Closer frame / softer panels', 'Horizontal Terminal padding reduced from 56 to 24 logical pixels on each side (32 pixels, about 1/3 inch at 96 DPI). Shader rounds eligible prompt-panel corners with a 10-pixel radius.'],
    ['Codex symbol', 'Persistent lower-right background mark, 25% of the original default-font width and height. Small-window scaling and prompt clearance.'],
    ['Wallpaper', 'Original blog pixel landscape bundled offline as SVG and PNG. Saved on/off/status controls; 10% opacity for readable text.'],
    ['Distribution', 'Public source, ZIP releases, SHA-256 checksums, setup/uninstall guide, real screenshots, and blog preview toggle. This release adds this PDF and its rebuild script.'],
], [123, 401])
sub('The design contract')
table([['Role', 'Color', 'Use'], ['Ink', '#07070a', 'Primary background'],
       ['Panel', '#0d0d12', 'Theme panel / ANSI black'], ['Cream', '#f2efe6', 'Main foreground'],
       ['Muted', '#8b8896', 'Comments and secondary text'], ['Amber', '#f0b34a', 'Warm accents, keywords, left flames'],
       ['Turquoise', '#3be0c8', 'Strings, links, right flames']], [90, 95, 339])
p('palette.json is the project palette. It also contains complementary blue, rose, green, and magenta for syntax and distinguishable diffs. Do not force every Codex UI color into these six values; some surfaces remain native Codex controls.', 'SmallBody')

page('3 / Architecture and source map')
code('Shell command\n  -> ~/.local/bin/codex.ps1 or codex.cmd\n  -> installed cli.py + runtime.json\n  -> native Codex directly OR Windows Terminal profile\n  -> launch.ps1 -> native Codex\n\nVisual composition\n  Codex syntax theme + Terminal ANSI palette\n  + optional Terminal background image\n  + HLSL frame/flames/rounded panels/Codex mark')
table([
    ['Source path', 'Responsibility'],
    ['install.py / install.ps1', 'Standard-library Python installer and PowerShell entry point. Discovery, validated config edits, file journal, PATH shims, profile installation, rollback/uninstall.'],
    ['theme_settings.py', 'Canonical TITLE and profile GUID; JSONC reader; wallpaper command parsing and persisted updates. Copied beside the installed cli.py.'],
    ['windows/cli.py', 'Argument routing, --magik and --widowmaker alias, explicit --yolo translation, noninteractive passthrough, child lifecycle.'],
    ['windows/launch.ps1', 'Decode forwarded argument array, read native runtime, display branded banner, invoke the original Codex entry point.'],
    ['windows/magik.hlsl', 'Windows Terminal compositor shader. t0 terminal surface; t1 Codex mark texture; time/scale/resolution uniforms.'],
    ['palette.json / themes/', 'Brand colors; tmTheme syntax definitions; exported Windows Terminal scheme; standalone Kitty palette.'],
    ['assets/ / docs/', 'Offline wallpaper and logo source/rendered assets, attribution/licenses, real screenshots, README illustration, this PDF.'],
    ['tests/ / tools/ / .github/', '32 unit/integration tests, real Windows shader compiler check, asset renderer, PDF builder, Windows/Linux validation workflow.'],
], [158, 366])
p('Repository folder: Projects/magik-terminal under the owner\'s home. Blog repository: Projects/b1scu1tk1d. The theme is an integration around Codex and Windows Terminal, not a fork of Codex or a model behavior modification.', 'SmallBody')

page('4 / Launch contract and arguments')
table([
    ['Command / context', 'Behavior'],
    ['codex --magik', 'From an interactive ordinary shell: open a themed tab in Terminal window 0, using the stable profile GUID and current working directory.'],
    ['codex --magik --yolo', 'Same visual launch, plus --dangerously-bypass-approvals-and-sandbox forwarded explicitly to native Codex.'],
    ['Already in the themed profile', 'WT_PROFILE_ID matches the GUID: run native Codex in that tab; do not nest a new tab.'],
    ['Plain codex / batch / redirected I/O', 'Pass through to native Codex. Preserve argument arrays, streams, and exit status. --version and --help do not create a window.'],
    ['--wallpaper on / off / status', 'With --magik or --widowmaker: a settings-only command, exits without creating a model session. Do not combine with a prompt or --yolo.'],
    ['--widowmaker', 'Compatibility alias for --magik, including explicit --yolo.'],
    ['-- argument separator', 'Theme flag parsing stops here so literal prompt flags can be passed through.'],
], [184, 340])
sub('Why renaming cannot break the launcher')
p('The profile identity is <b>{89a85927-87d9-4b07-922a-3fc6a9f2dc61}</b>. Routing uses that GUID, not the display name. The install directory remains magik-terminal. The internal syntax theme ID remains widowmaker; both checked-in tmTheme files carry the new display title.')
sub('How argument forwarding works')
p('cli.py builds an argument list without a shell. For a new themed tab, it serializes the forwarded list as UTF-8 JSON, Base64-encodes it, and passes it to launch.ps1 as EncodedArguments. PowerShell decodes the array and invokes the native executable with array splatting. runtime.json stores native argv, such as Node plus the installed Codex JavaScript entry point.')
p('The wrapper waits for its child and tolerates Ctrl+C while the child handles the shared console event. Child exit codes propagate. YOLO is never turned on by a theme default, wallpaper command, or rename.')
code('codex --magik\ncodex --magik --yolo\ncodex --magik resume --last\ncodex --magik --wallpaper on\ncodex --magik --wallpaper off\ncodex --magik --wallpaper status')

page('5 / Graphics and readability')
sub('Compositor, not model-generated decoration')
p('Windows Terminal supplies the terminal surface to shaderTexture at t0 and the transparent Codex mark to codexMark at t1. The shader works in logical pixels using Resolution / max(Scale, 1). The final color adds decoration through a background mask based on distance from ink. This is a color heuristic, not a semantic understanding of text or panels.')
table([
    ['Feature', 'Current implementation'],
    ['Mark dimensions', 'originalMarkSize = 304; markScale = 0.25; resulting nominal size = 76 logical pixels. Further bounded by 20% of the smaller viewport dimension. This is 25% width/height, not 25% area.'],
    ['Mark position', 'Center starts at (0.75 * width, 0.75 * height). Vertical center is capped to reserve 112 logical pixels for composer/footer plus 12 pixels clearance. Hide if it no longer fits wholly below the viewport midpoint.'],
    ['Mark appearance', 'Transparent dot-pattern asset from the native settled welcome logo, tinted subtly by the shader and masked behind foreground content. Independent of wallpaper choice.'],
    ['Frame / flames', 'Corner rails at 7 logical pixels; brackets extend to 49. Side flames use 3-pixel quantization and noise inside roughly 48-pixel gutters; subtle 24-pixel circuit rows.'],
    ['Rounded panels', 'Detect dark, nearly neutral panel pixels near side edges; sample vertical neighbors up to 10 pixels and composite a rounded boundary. No changes to Codex input handling.'],
    ['Still mode', '-NoMotion prepends #define W1_STILL 1; flame time becomes zero. The shader still supplies frozen flames, frame, rounding, and logo.'],
], [134, 390])
sub('Wallpaper and native welcome logo')
p('The original 160 x 90 pixel landscape SVG is rasterized to a 1600 x 900 PNG. Terminal uses uniformToFill, center alignment, and backgroundImageOpacity = 0.10. Fresh installs default off; upgrades read the saved preference. The palette contrast test checks at least 4.5:1 for normal text even against a hypothetical white wallpaper pixel; cream exceeds 13:1. Native dimmed text and selection colors are outside that guarantee.')
p('The full installer writes tui.animations = false to suppress the large native centered welcome mark. This also freezes native shimmer/spinner motion. Theme flames animate independently. Existing Codex sessions must be reopened to lose the old mark. A per-launch -c override was rejected during development because it triggered embedded-mode warnings; keep this cosmetic setting in persistent config.')

page('6 / Persistent state and upgrade behavior')
table([
    ['Installed location', 'Stored state / purpose'],
    ['$CODEX_HOME/config.toml', 'Validated TOML edit: [tui] theme = "widowmaker"; animations = false for full installs. Unrelated parsed settings must remain equal. Default CODEX_HOME is ~/.codex.'],
    ['$CODEX_HOME/themes/', 'widowmaker.tmTheme contains the current branded syntax palette. Internal ID is intentionally stable.'],
    ['$CODEX_HOME/magik-terminal/', 'cli.py, launch.ps1, theme_settings.py, runtime.json, private install-state.json, content-addressed magik-<hash>.hlsl, and installed assets.'],
    ['Windows Terminal settings.json', 'Owned profile GUID, title, matching scheme, shader paths, Cascadia Mono 12, padding 24,8,24,8, background properties. Default profile changes only with -DefaultProfile.'],
    ['~/.local/bin/', 'codex.ps1 and codex.cmd shims. User PATH gets this directory only if absent. Native Codex and PowerShell startup profiles are not edited.'],
    ['Owner-only preferences', '~/.codex/AGENTS.md names the theme and records the palette and wallpaper preservation rule. Desktop shortcuts use the same GUID; local shortcut changes are not part of the distributed installer/uninstall journal.'],
], [177, 347])
sub('Backups, wallpaper writes, and uninstall')
p('install-state.json stores original file bytes in Base64 plus installed SHA-256 hashes. Repeat installs retain the original backup. Failed file writes attempt rollback. Wallpaper updates change the owned profile and runtime preference, update journal hashes, and roll back on an OSError. A file changed after installation is marked user_modified; uninstall retains it and the backup instead of silently restoring over the edit.')
p('Uninstall restores exact original bytes for unchanged managed files, removes newly created managed files, and removes the user PATH entry only if the installer added it. Partial uninstall returns code 2 and lists retained files. <b>Never publish install-state.json:</b> it can contain unrelated private configuration backups. runtime.json contains machine-specific paths and also stays out of release archives.')
sub('Upgrade boundaries a successor must understand')
p('JSONC comments/formatting are normalized although unrelated settings are preserved semantically. The owned profile is rebuilt, so manual customizations inside that profile may be reset. Wallpaper preference persists; still mode currently must be requested again with -NoMotion. Old color schemes are retained to avoid breaking other profiles that may reference them. File/registry changes are not a fully transactional system and are not protected against concurrent edits.')

page('7 / Install, operate, recover')
p('Baseline verified environment: Windows Terminal 1.24.11911.0, Codex CLI 0.159.3, PowerShell 5.1+, Python 3.11+. Use an installed, signed-in Codex with /theme support. Theme code is free; Codex access is separate.')
sub('Install or upgrade from the extracted package')
code('powershell -NoProfile -ExecutionPolicy Bypass -File .\\install.ps1\n\n# Optional defaults / visual mode:\n.\\install.ps1 -DefaultProfile\n.\\install.ps1 -Wallpaper on\n.\\install.ps1 -NoMotion -Wallpaper on\n\n# Remove using the private local installation journal:\n.\\install.ps1 -Uninstall')
p('The execution-policy bypass is process-local. Open a new shell after PATH changes. Use codex.cmd if the PowerShell policy blocks the .ps1 shim. A machine-wide Codex PATH entry can precede the user shim; diagnose with Get-Command codex -All and where.exe codex. Invoke ~/.local/bin/codex.cmd explicitly when necessary.')
sub('Custom installs and other terminals')
code('python install.py --terminal-settings PATH\npython install.py --codex-executable PATH_TO_REAL_CODEX_EXE\npython install.py --theme-only')
p('Theme-only mode installs syntax colors without changing native animation settings. Kitty users can include themes/kitty.conf in their own configuration. HLSL effects and the Windows launcher are Windows Terminal features. For the full separate Mac instance, use install-macos.sh and the Ghostty GLSL implementation described on pages 11-12. Kitty receives palette-only support.')
table([
    ['Symptom', 'Diagnosis / recovery'],
    ['Flag rejected', 'Check command resolution and PATH; the native Codex executable does not implement --magik. Reinstall shims if missing.'],
    ['Native runtime moved', 'Reinstall to refresh runtime.json; use --codex-executable for a custom real executable. Do not point it back to the theme shim.'],
    ['Old central logo or old title', 'Reopen Codex/the themed tab. Confirm the GUID-owned profile and tui.animations setting.'],
    ['Shader rejected by GPU/Terminal', 'Remove experimental.pixelShaderPath and experimental.pixelShaderImagePath from the owned profile for palette/wallpaper-only fallback. -NoMotion still uses the GPU shader.'],
    ['Partial uninstall', 'Read reported paths and original backups. Merge the required recovery deliberately; do not overwrite later user settings blindly.'],
], [135, 389])

page('8 / Verification and publishing')
sub('Checks performed on the foundation')
p('The 32-test suite covers argument preservation and Unicode quoting, plain/batch passthrough, themed launch routing, explicit YOLO, alias and -- boundary, in-profile reuse, TOML preservation, JSONC strings, repeat installs, rollback, uninstall, saved wallpaper state, settings-only subprocess behavior, and palette contrast. It also exercises a mocked full installation and upgrade. Real Windows compilation validates both animated and still ps_4_0 shader variants.')
code('python -m unittest discover -s tests -v\npython tools/check-shader.py\n\n# Smoke checks; these exit without starting a chat:\ncodex --magik --version\ncodex --magik --yolo --version\ncodex --magik --wallpaper status')
p('Actual Terminal windows were inspected for logo placement, prompt clearance, softened corners, flame rails, and wallpaper on/off. Theme CI runs on Windows, Ubuntu, and macOS. Windows compiles HLSL; Ubuntu compiles GLSL; Apple Silicon and Intel macOS validate Ghostty configuration and execute isolated native sessions. A GUI smoke check opens separate Ghostty windows and verifies normal and explicit YOLO argument paths with a harmless sentinel. No claim is made that every GPU, scaling factor, or future Codex UI layout has been tested. The local graphical workstation is Windows; Mac visual acceptance remains a recipient check.')
sub('Blog integration')
p('The separate b1scu1tk1d repository uses Next.js static export. src/components/magik-download.tsx owns the branded download card and an accessible aria-pressed wallpaper preview button. The two public/widowmaker-wallpaper-*.png files are actual terminal screenshots; those filenames remain stable. The preview button only swaps preview images, never the visitor\'s terminal settings. The #magik-terminal anchor remains stable.')
code('npm run build\nnpm run lint')
p('Local and live browser checks cover desktop and 390-pixel mobile rendering, no horizontal overflow, both toggle states, image loading, and download target. Existing unrelated img optimization warnings remain in the blog; builds and lint have no errors.')
sub('Release sequence for the successor')
p('1. Inspect diffs and private-file exclusions. Run the checks above after relevant changes. 2. Commit source and push; wait for CI. 3. Build the PDF and a git archive ZIP from the release commit. 4. Publish an immutable version tag with magik-terminal.zip, the compatibility filename w1d0wm4k3r-cli-theme.zip, SHA256SUMS.txt, and this PDF. The two Windows/compatibility ZIP files must be identical. Publish magik-terminal-macos.zip separately with its own SHA-256. 5. Deploy the blog only after assets exist. 6. Download the public assets, compare hashes, and check the live page.')
p('Main-branch pushes in the blog repository trigger .github/workflows/deploy.yml and GitHub Pages. Source screenshots must contain only the intended terminal view, not overlapping personal windows. Neither private install state nor runtime.json belongs in an archive.', 'SmallBody')

page('9 / Hermes assimilation brief')
p('Give Hermes this PDF plus the source repository at the matching release tag. The following brief can be copied into its task instructions. It describes a workflow, not a Hermes-specific API or assumed skill-file format.')
sub('Mission and invariants')
p('<b>Maintain Magik Terminal for Codex (By W1d0wm4k3r).</b> Read the repository README, this handoff, and the relevant implementation before editing. Preserve codex --magik and explicit codex --magik --yolo. Keep the stable profile GUID, saved wallpaper preference, original native Codex entry point, syntax theme ID, install paths, and existing download links compatible.')
p('Use the B1SCU1TK1D palette for this project. Keep text readable, flames near the edges, panels soft, and the small Codex mark in the lower-right quarter with prompt clearance. Do not insert decorative ANSI/frame text into ordinary assistant chat responses. Terminal rendering supplies the visual identity.')
sub('First working session')
p('1. Confirm OS, installed Codex and Terminal versions, source checkout/tag, git status, command resolution, and the current profile GUID. Read runtime/state metadata locally without logging backups or credentials.\n<br/>2. Establish the current wallpaper and motion choice. Inspect the relevant config fields, not a wholesale dump of private files.\n<br/>3. Run the baseline tests; on Windows compile both shader variants. Read only the files relevant to the requested change.\n<br/>4. Implement the smallest coherent change. Exercise an isolated temporary install before touching real settings for installer changes.\n<br/>5. Inspect a real terminal at normal and smaller sizes with wallpaper both on and off; return to the user\'s saved choice.\n<br/>6. Update docs and screenshots when visible behavior changes. Summarize changed files, evidence, limits, and any remaining work.')
sub('Choose the correct extension point')
table([
    ['Need', 'Start here'],
    ['New visual effect / logo placement', 'windows/magik.hlsl, assets, tools/check-shader.py'],
    ['Palette or syntax changes', 'palette.json, install.theme_bytes(), install.scheme(), exported themes'],
    ['New launch flag', 'windows/cli.py; keep argument lists, -- boundary, batch behavior, and explicit YOLO'],
    ['Persisted preference', 'theme_settings.py plus installer runtime/state handling and rollback tests'],
    ['Distribution / documentation', 'README, this builder, tagged release assets, blog component and deployment'],
], [191, 333])
p('Do not rewrite native Codex, change authentication/model selection, loosen permissions by default, silently overwrite later user settings, or claim new cross-platform support without implementation and verification. Publication authority belongs to the current user/session; this handoff is not blanket authorization for future external actions.', 'SmallBody')

page('10 / Provenance, limits, and next steps')
sub('Canonical sources')
p(link('Theme source and tagged releases', REPO) + '<br/>' +
  link('Source at v0.3.0', REPO + '/tree/v0.3.0') + '<br/>' +
  link('Blog source', 'https://github.com/imperator-clawdius/b1scu1tk1d') + '<br/>' +
  link('Original blog landscape SVG', 'https://b1scu1tk1d.com/landscape.svg') + '<br/>' +
  link('Upstream Codex settled-logo snapshot', 'https://github.com/openai/codex/blob/main/codex-rs/tui/src/snapshots/codex_tui__empty_state_animation__tests__onboarding_settled_logo.snap') + '<br/>' +
  link('Windows Terminal shader API reference', 'https://learn.microsoft.com/en-us/windows/terminal/customize-settings/profile-appearance#pixel-shader-effects'))
p('The upstream logo link uses a moving branch. The shipped assets/codex-mark-source.snap records the exact source used. The SVG/PNG recreate its braille-dot layout. The original landscape SVG SHA-256 with LF line endings is:', 'SmallBody')
code('0f01ee48069c7b024e52a5256ede084912e998a15a4ed6cc3a4ed071d8a71a7c')
sub('Asset and document rebuilds')
code('# Development dependencies only; runtime remains stdlib Python.\n# Asset renderer expects Playwright (or PLAYWRIGHT_MODULE).\nnode tools/render-wallpaper.cjs\n\n# PDF builder expects ReportLab.\npython tools/build-handoff.py')
p('tools/render-wallpaper.cjs rasterizes the repository SVG assets. tools/build-handoff.py is the editable source of this document. The PDF contains selectable text and links for agent ingestion; if a Hermes setup cannot read PDFs, provide this builder and README alongside it. No Hermes installation was discovered or modified as part of this delivery.')
sub('Known engineering limits / candidate follow-up work')
p('The panel/text mask is heuristic; unusual background colors, selections, or new Codex layouts can reduce decoration visibility or change rounding. The logo baseline is the observed default-font size, not a dynamically measured native logo. Very short windows intentionally hide it. Experimental shader APIs can vary by Terminal/GPU version.')
p('Argument classification currently scans forwarded tokens for a known batch command set. A literal token matching a command name can affect routing; use care when extending parsing. The native npm entry location may change after upstream upgrades. A future improvement could add more precise argument parsing, registry/file transaction boundaries, concurrent-write protection, preserved still-mode preference, and configurable per-profile overrides. These are potential improvements, not implemented features.')
sub('Licensing and release history')
p('Theme code and owner-supplied blog artwork: MIT. Codex-derived logo asset: Apache-2.0 with assets/CODEX-LICENSE.txt and attribution. OpenAI marks remain OpenAI\'s; this is an independent community project. v0.1.0 established Magik Terminal; v0.2.0 added the wallpaper controls and persistent small mark under a temporary W1d0wm4k3r title; v0.3.0 restores the final Magik Terminal for Codex (By W1d0wm4k3r) identity, adds the separate macOS implementation, and supplies this handoff.')

page('11 / Separate macOS implementation')
p('The macOS package uses Ghostty with a native GLSL shader. It is a separate application instance and configuration, sharing the visual design, original assets, brand, and launcher contract with Windows. It is not a Windows emulator or a promise that built-in macOS Terminal supports these effects.')
table([
    ['Mac source', 'Purpose'],
    ['install-macos.sh', 'Portable shell entry point: resolves the extracted source directory and runs Python 3.11+ installer.'],
    ['macos/install.py', 'Finds Ghostty.app and native Codex. Reuses validated TOML, theme generation, journal and uninstall primitives. Installs a POSIX shim plus backed-up zsh/bash PATH blocks.'],
    ['macos/cli.py', 'Uses shared flag parser. Interactive themed launches use /usr/bin/open -na Ghostty.app with config-default-files=false and the dedicated config file. Native/batch calls exec directly.'],
    ['macos/session.py', 'Runs inside Ghostty. Decodes the Base64 JSON argument list, sets CODEX_HOME and MAGIK_PROFILE, restores captured PATH for Node/npm, and execs native Codex.'],
    ['macos/settings.py', 'Generates Ghostty config: Menlo 12, matching palette, 24/8 padding, shader, wallpaper opacity, isolated command, and window-save-state=never.'],
    ['macos/magik.glsl', 'Generated from the Windows shader by tools/build-macos-shader.py. Uses mainImage, iChannel0, iTime, iResolution, and iCurrentCursor. Logo is embedded as bit-packed dot rows.'],
], [164, 360])
sub('Isolation and persistence')
p('Runtime lives in $CODEX_HOME/magik-terminal-macos, separate from the Windows installation directory. Ghostty\'s ordinary config is not read or changed. New instances do not restore previous Ghostty windows. Existing themed sessions are recognized by MAGIK_PROFILE. Like Windows, the persistent Codex syntax/animation settings affect Codex generally; model, account, and tool settings remain untouched.')
p('The executable shim is ~/.local/bin/codex. The installer adds a managed PATH block to ~/.zshrc and ~/.bash_profile, preserving other text and journaling originals. --no-shell-hook opts out. Python and native Codex paths are recorded at installation; reinstall if their locations change. Wallpaper and motion choices both persist across Mac upgrades. Wallpaper toggles save the next-launch config; reopen Magik to apply.')
p('Ghostty exposes only one input texture, so the small logo cannot use Windows\' extra sampler. The generated shader embeds the source SVG\'s dot coordinates as row masks instead. Retina/font scaling follows cursor-cell height because the custom shader interface has no Windows-style Scale uniform. This approximation requires visual acceptance on the target display.', 'SmallBody')

page('12 / Mac setup and acceptance')
p('Requirements: macOS supported by the chosen Ghostty build; Ghostty 1.2+ (a current release is recommended); Python 3.11+; installed, signed-in Codex with theme support. Use native dependencies for Apple Silicon or Intel. The theme package itself ships Python, shell, GLSL, and assets, not a platform-specific executable.')
code('sh install-macos.sh\n# Then open a new shell:\ncodex --magik\ncodex --magik --yolo\n\ncodex --magik --wallpaper on\ncodex --magik --wallpaper off\ncodex --magik --wallpaper status\n\nsh install-macos.sh --no-motion\nsh install-macos.sh --motion\nsh install-macos.sh --uninstall')
sub('What is verified automatically')
p('The Mac tests exercise separate-instance command construction, quoted paths, lossless explicit YOLO forwarding, in-profile reuse, batch behavior, an isolated full install, wallpaper toggles, upgrade persistence, and exact shell-file recovery. POSIX runners execute the installed shim with an inert native sentinel and verify its exit code. The GLSL shader is compiled in animated and still variants; it also compiled in Chromium WebGL2 during development.')
p('tools/smoke-macos.py runs on the macOS CI runner against a temporary HOME and a harmless sentinel instead of Codex. With --config-only, it validates Ghostty config, runs session.py directly, checks child argv/profile markers, toggles wallpaper, and uninstalls. This passed on Apple Silicon and Intel. Without that flag it opens real Ghostty windows and verifies the sentinel arguments. This GUI check passed on the Intel runner. A system TextEdit probe distinguishes an unavailable hosted desktop from a Magik-specific failure, and any skip is reported explicitly. It makes no model request and requires no account credentials. This confirms configuration, native-session behavior, and GUI startup on the tested runner; it is not a visual review of every display. CI verifies the official app signature and clears first-open quarantine metadata only on that disposable test dependency. User installers leave Mac security settings alone; users should open Ghostty once to complete its normal first-open prompt.')
sub('Recipient visual acceptance')
p('Open both launch modes on the recipient Mac. Confirm amber/turquoise flames, cyber frame, cream text, subtle landscape, small lower-right mark, and prompt clearance. Check wallpaper off and on, smaller windows, Retina and external displays, still mode, and restart persistence. Confirm ordinary Ghostty stays unchanged. If shader rendering fails, remove custom-shader from the dedicated ghostty.conf for palette/wallpaper fallback and inspect Ghostty render logs.')
p('The current config validator runs after installation and reports errors with the saved backup location; it does not automatically uninstall after a Ghostty validation failure. Preserve the journal and run the explicit uninstall or correct the config. Code and tests are the source of truth for future refinements.', 'SmallBody')
p(link('Ghostty configuration and custom-shader reference', 'https://ghostty.org/docs/config/reference') + '<br/>' +
  link('Ghostty downloads', 'https://ghostty.org/download') + '<br/>' +
  link('Mac package', REPO + '/releases/latest/download/magik-terminal-macos.zip'))

doc = SimpleDocTemplate(str(OUTPUT), pagesize=(612, 792), rightMargin=44,
                        leftMargin=44, topMargin=55, bottomMargin=54,
                        title=TITLE + ' - Hermes Agent Handoff',
                        author='W1d0wm4k3r / B1SCU1TK1D',
                        subject='Implementation, operations, and extension guide for Magik Terminal')
doc.build(story, onFirstPage=chrome, onLaterPages=chrome)
print(OUTPUT)
