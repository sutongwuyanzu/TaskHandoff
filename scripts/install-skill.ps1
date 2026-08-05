# Install TaskHandoff as a Claude Code / agent skill (Windows).
# Usage:
#   .\scripts\install-skill.ps1
#   .\scripts\install-skill.ps1 -Target "$env:USERPROFILE\.claude\skills\task-handoff"

param(
    [string]$Target = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (-not $Target) {
    $Target = Join-Path $env:USERPROFILE ".claude\skills\task-handoff"
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null

$items = @(
    "SKILL.md",
    "templates",
    "scripts",
    "taskhandoff",
    "references",
    "pyproject.toml",
    "README.md"
)

foreach ($name in $items) {
    $src = Join-Path $Root $name
    if (-not (Test-Path $src)) { continue }
    $dest = Join-Path $Target $name
    if (Test-Path $src -PathType Container) {
        if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
        Copy-Item -Recurse -Force $src $dest
    } else {
        Copy-Item -Force $src $dest
    }
}

Write-Host "Installed skill to: $Target"
Write-Host "Then: pip install -e `"$Root`""
Write-Host "Or in a project: handoff init --root ."
