param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$Tectonic
)
$ErrorActionPreference='Stop'
$revisionBuildRoot=Split-Path -Parent $PSScriptRoot
function Invoke-RevisionCheck([string]$Script) {
    & $Python (Join-Path $PSScriptRoot $Script)
    if ($LASTEXITCODE -ne 0) { throw ('Failed: '+$Script) }
}
Push-Location $revisionBuildRoot
try {
    Invoke-RevisionCheck 'render_state_diagrams_v4.py'
    Invoke-RevisionCheck 'figure_registry.py'
    Push-Location 'report'
    try {
        & $Tectonic --only-cached --keep-logs --keep-intermediates main.tex
        if ($LASTEXITCODE -ne 0) { throw 'Report compilation failed' }
    } finally { Pop-Location }
    # This edition retains every native plate's page position. Do not redraw
    # accepted diagrams merely to rebuild the four state figures.
    Invoke-RevisionCheck 'verify-report.py'
    Invoke-RevisionCheck 'verify-diagram-layout.py'
    Copy-Item -LiteralPath 'report\main.pdf' -Destination '分析设计文档\ADC_Nexus_主文档.pdf' -Force
    & $Python (Join-Path $PSScriptRoot 'verify-release.py') --write-manifest
    if ($LASTEXITCODE -ne 0) { throw 'Release verification failed' }
} finally { Pop-Location }
