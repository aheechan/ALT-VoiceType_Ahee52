param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    if (-not (Test-Path ".venv-build")) {
        python -m venv .venv-build
    }
    $python = Join-Path $root ".venv-build\Scripts\python.exe"
    & $python -m pip install --upgrade pip
    & $python -m pip install -e ".[ui,audio,asr-qwen,download]" "pyinstaller>=6.6"

    & $python -m PyInstaller --clean --noconfirm packaging\altvoice.spec

    if (-not $SkipInstaller) {
        $iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
        if ($null -eq $iscc) {
            Write-Warning "Inno Setup (ISCC.exe) not found; skipped installer."
        }
        else {
            & $iscc.Source packaging\installer.iss
        }
    }
}
finally {
    Pop-Location
}
