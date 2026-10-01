param(
    [string]$EncodedArguments,
    [string[]]$CodexArguments = @()
)
$ErrorActionPreference = 'Stop'
if ($EncodedArguments) {
    $json = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($EncodedArguments))
    $CodexArguments = @(ConvertFrom-Json $json)
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
