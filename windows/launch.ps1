param(
    [string]$EncodedArguments,
    [string[]]$CodexArguments = @()
)
$ErrorActionPreference = 'Stop'
if ($EncodedArguments) {
    $json = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($EncodedArguments))
    # Windows PowerShell 5.1 emits the JSON array as one pipeline object.
    # Assign it first so string[] does not join multiple flags into one string.
    $decodedArguments = ConvertFrom-Json $json
    $CodexArguments = @($decodedArguments)
}
# Also cover direct launches from the Windows Terminal profile menu.
# A shared daemon can have different privileges from this PowerShell process.
$separator = [Array]::IndexOf($CodexArguments, '--')
$flags = @($CodexArguments)
if ($separator -eq 0) { $flags = @() }
elseif ($separator -gt 0) { $flags = @($CodexArguments[0..($separator - 1)]) }
if ('--no-daemon' -notin $flags -and -not ($flags | Where-Object { $_ -eq '--remote' -or $_ -like '--remote=*' })) {
    $CodexArguments = @('--no-daemon') + @($CodexArguments)
}
$runtime = Get-Content -LiteralPath "$PSScriptRoot\runtime.json" -Raw | ConvertFrom-Json
$native = @($runtime.native)
if (-not (Test-Path -LiteralPath $native[0])) { throw 'Codex runtime moved. Reinstall Magik Terminal for Codex (By W1d0wm4k3r) to refresh it.' }
$Host.UI.RawUI.WindowTitle = 'Magik Terminal for Codex (By W1d0wm4k3r)'
Write-Host ''
Write-Host '  +-- Magik Terminal for Codex (By W1d0wm4k3r) ------+' -ForegroundColor Yellow
Write-Host '  |  B1SCU1TK1D  //  AMBER FIRE. CYAN SIGNAL.         |' -ForegroundColor Cyan
Write-Host '  +-------------------------------------------------+' -ForegroundColor Yellow
Write-Host ''
$nativeArgs = @($native | Select-Object -Skip 1) + @($CodexArguments)
& $native[0] @nativeArgs
$global:LASTEXITCODE = $LASTEXITCODE
