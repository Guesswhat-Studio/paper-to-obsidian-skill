param(
    [string]$PythonVersion = "3.13",
    [switch]$InstallUv
)

$ErrorActionPreference = "Stop"
$SkillRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
# Keep durable state in the active workspace so it survives plugin-cache refreshes.
$Workspace = (Get-Location).Path
$VenvPath = Join-Path $Workspace ".paper-obsidian\.venv"
New-Item -ItemType Directory -Force -Path (Join-Path $Workspace ".paper-obsidian") | Out-Null

function Refresh-UvCommand {
    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidateDirs = @(
        (Join-Path $env:USERPROFILE ".local\bin"),
        (Join-Path $env:USERPROFILE ".cargo\bin")
    )
    foreach ($dir in $candidateDirs) {
        if ($dir -and (Test-Path -Path $dir) -and ($env:PATH -notlike "*$dir*")) {
            $env:PATH = "$dir;$env:PATH"
        }
    }

    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$uv = Refresh-UvCommand
if (-not $uv -and $InstallUv) {
    Write-Host "Installing uv with the official Astral installer"
    powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    $uv = Refresh-UvCommand
}

if (-not $uv) {
    throw "uv was not found. Re-run with -InstallUv to install uv, or install uv manually first."
}

& $uv python install $PythonVersion
& $uv venv $VenvPath --python $PythonVersion
$python = Join-Path $VenvPath "Scripts\python.exe"
& $uv pip install --python $python -r (Join-Path $SkillRoot "requirements.txt")
& $python (Join-Path $SkillRoot "scripts\setup_environment.py") --check-only --json-report (Join-Path $Workspace ".paper-obsidian\environment-check.json")

Write-Host "paper-to-obsidian-skill environment is ready: $VenvPath"
