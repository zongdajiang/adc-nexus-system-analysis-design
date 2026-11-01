param([string]$ShortcutDirectory)
$ErrorActionPreference='Stop'
$taskDesktop=[Environment]::GetFolderPath('Desktop')
$taskRoot=Split-Path -Parent $PSScriptRoot
$taskBootstrapDirectory=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'ADC-Nexus'
New-Item -ItemType Directory -Path $taskBootstrapDirectory -Force | Out-Null
$taskConfiguration=Join-Path $taskBootstrapDirectory 'config.json'
if(Test-Path -LiteralPath $taskConfiguration){
  $taskExistingConfiguration=Get-Content -LiteralPath $taskConfiguration -Raw -Encoding UTF8 | ConvertFrom-Json
  if($taskExistingConfiguration.project_root -ne $taskRoot){throw 'Another ADC Nexus project owns the desktop bootstrap configuration.'}
}
@{project_root=$taskRoot} | ConvertTo-Json | Set-Content -LiteralPath $taskConfiguration -Encoding UTF8
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'desktop-bootstrap.ps1') -Destination $taskBootstrapDirectory -Force
$taskBootstrap=Join-Path $taskBootstrapDirectory 'desktop-bootstrap.ps1'
$taskPowerShell=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
if(!(Test-Path -LiteralPath $taskPowerShell)){throw 'The built-in Windows PowerShell executable was not found.'}
$taskShell=New-Object -ComObject WScript.Shell
$taskLocations=@($taskDesktop)
$taskOrganized=Join-Path $taskDesktop 'ADC'
if(Test-Path -LiteralPath $taskOrganized -PathType Container){$taskLocations+=$taskOrganized}
if($ShortcutDirectory){
  if(!(Test-Path -LiteralPath $ShortcutDirectory -PathType Container)){throw 'The requested shortcut directory does not exist.'}
  $taskLocations=@([IO.Path]::GetFullPath($ShortcutDirectory))
} else {
  # Preserve the user's existing Desktop/ADC organization rather than create duplicates.
  $taskOwnedLocations=@($taskLocations | Where-Object {
    $taskCandidate=Join-Path $_ 'ADC Nexus - Start.lnk'
    (Test-Path -LiteralPath $taskCandidate) -and
      $taskShell.CreateShortcut($taskCandidate).Description -like 'ADC Nexus local server *'
  })
  $taskLocations=if($taskOwnedLocations.Count){$taskOwnedLocations}else{@($taskDesktop)}
}
foreach($taskLocation in $taskLocations){
foreach($taskAction in @('Start','Status','Stop')){
  $taskFile=Join-Path $taskLocation ('ADC Nexus - '+$taskAction+'.lnk')
  if(Test-Path -LiteralPath $taskFile){
    $taskExisting=$taskShell.CreateShortcut($taskFile)
    if($taskExisting.Description -notlike 'ADC Nexus local server *'){throw ('An unrelated shortcut already exists: '+$taskFile)}
  }
  $taskLink=$taskShell.CreateShortcut($taskFile)
  $taskLink.TargetPath=$taskPowerShell
  $taskLink.Arguments='-NoLogo -NoProfile -NoExit -File "'+$taskBootstrap+'" -Action '+$taskAction
  $taskLink.WorkingDirectory=$taskBootstrapDirectory
  $taskLink.WindowStyle=1
  $taskLink.Description='ADC Nexus local server '+$taskAction+'. Preserves existing local data.'
  $taskLink.IconLocation=(Join-Path $env:SystemRoot 'System32\shell32.dll')+',14'
  $taskLink.Save()
  $taskVerify=$taskShell.CreateShortcut($taskFile)
  if($taskVerify.WorkingDirectory -ne $taskBootstrapDirectory -or !$taskVerify.Arguments.Contains($taskBootstrap) -or !$taskVerify.Arguments.Contains('-NoExit') -or $taskVerify.TargetPath -ne $taskPowerShell){throw 'Shortcut verification failed'}
  Write-Host ('UPDATED '+$taskFile)
}
}
