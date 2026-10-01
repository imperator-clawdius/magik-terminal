param([switch]$NoMotion, [switch]$Uninstall, [switch]$DefaultProfile)
$ErrorActionPreference = 'Stop'
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'Python 3.11+ is required: https://www.python.org/downloads/' }
$options = @()
if ($NoMotion) { $options += '--no-motion' }
if ($Uninstall) { $options += '--uninstall' }
if ($DefaultProfile) { $options += '--default-profile' }
& $python.Source "$PSScriptRoot\install.py" @options
if ($LASTEXITCODE -ne 0) { throw "Magik installer exited with code $LASTEXITCODE" }
