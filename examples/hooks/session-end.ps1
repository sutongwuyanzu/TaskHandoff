$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
if (-not $env:HANDOFF_ROOT) { $env:HANDOFF_ROOT = (Get-Location).Path }
python "$RepoRoot\examples\hooks\session_end.py"
exit 0
