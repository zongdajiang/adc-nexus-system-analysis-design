param(
  [ValidateSet('Start','Status','Stop')][string]$Action='Start',
  [switch]$NoBrowser
)
$ErrorActionPreference='Stop'
$taskTranscript=$false
$taskLog=$null
try {
  $Host.UI.RawUI.WindowTitle='ADC Nexus - '+$Action
  Write-Host ('ADC Nexus | '+$Action) -ForegroundColor Cyan
  Write-Host '------------------------------------------------------------'
  $taskLogFolder=Join-Path $PSScriptRoot 'logs'
  New-Item -ItemType Directory -Path $taskLogFolder -Force | Out-Null
  $taskLog=Join-Path $taskLogFolder ('launcher-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')+'-'+$Action+'.log')
  try {Start-Transcript -LiteralPath $taskLog -Force | Out-Null; $taskTranscript=$true} catch {Write-Host ('Log unavailable: '+$_.Exception.Message) -ForegroundColor Yellow}
  $taskConfiguration=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  $taskScript=Join-Path $taskConfiguration.project_root 'tools\local-server.ps1'
  if(!(Test-Path -LiteralPath $taskScript)){throw 'ADC Nexus project was moved. Re-run tools/install-shortcuts.ps1 from its new location.'}
  Write-Host ('Project: '+$taskConfiguration.project_root)
  Write-Host ('Action:  '+$Action)
  $global:LASTEXITCODE=0
  & $taskScript -Action $Action -NoBrowser:$NoBrowser
  if($LASTEXITCODE -ne 0){throw 'The operation failed. Read the ERROR message above and keep the log for diagnosis.'}
} catch {
  Write-Host ('ERROR: '+$_.Exception.Message) -ForegroundColor Red
  $global:LASTEXITCODE=1
} finally {
  Write-Host ''
  Write-Host '------------------------------------------------------------'
  Write-Host 'Read the result above. Close this window with X when finished.'
  Write-Host 'Closing this result window does not stop a running Java server.'
  Write-Host 'Use the Stop shortcut only when you want to stop the website.'
  if($taskTranscript){Write-Host ('Launcher log: '+$taskLog); Stop-Transcript | Out-Null}
  # The desktop shortcut uses -NoExit, so success and early script errors stay visible.
}
