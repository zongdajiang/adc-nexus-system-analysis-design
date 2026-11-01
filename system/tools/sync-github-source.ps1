param([Parameter(Mandatory=$true)][string]$DestinationSystemDirectory)
$ErrorActionPreference='Stop'
$taskSource=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$taskDestination=[IO.Path]::GetFullPath($DestinationSystemDirectory)
$taskRepository=Split-Path -Parent $taskDestination
if((Split-Path -Leaf $taskDestination) -ne 'system' -or !(Test-Path -LiteralPath (Join-Path $taskRepository '.git'))){throw 'Destination must be the system folder of an existing Git checkout.'}
$taskRemote=& git -C $taskRepository config --get remote.origin.url
if($taskRemote -notmatch '^https://github\.com/zongdajiang/adc-nexus-system-analysis-design(?:\.git)?$'){throw 'Destination is not the authorized ADC Nexus repository.'}
New-Item -ItemType Directory -Path $taskDestination -Force | Out-Null
$taskCount=0
foreach($taskFolder in @('src','docs','tools','qa','upgrade-workbench')){
  $taskFolderPath=Join-Path $taskSource $taskFolder
  foreach($taskFile in Get-ChildItem -LiteralPath $taskFolderPath -Recurse -File){
    $taskRelative=[IO.Path]::GetRelativePath($taskSource,$taskFile.FullName)
    if($taskRelative -match '(^|[\\/])(raw|__pycache__|browser)([\\/]|$)' -or $taskRelative -match '\.pyc$'){continue}
    if($taskFolder -eq 'qa' -and $taskFile.Extension -notin @('.json','.md')){continue}
    if($taskRelative -match 'setup-credentials|local-server-state|本地角色测试账号|(^|[\\/])\.env(?:$|\.)'){throw 'Private file refused.'}
    $taskTarget=[IO.Path]::GetFullPath((Join-Path $taskDestination $taskRelative))
    if(!$taskTarget.StartsWith($taskDestination+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Copy target escaped the system folder.'}
    New-Item -ItemType Directory -Path (Split-Path -Parent $taskTarget) -Force | Out-Null
    Copy-Item -LiteralPath $taskFile.FullName -Destination $taskTarget -Force
    $taskCount++
  }
}
foreach($taskFile in @('pom.xml','package.json','PRODUCT.md','README.md','Dockerfile','render.yaml','.gitignore','.dockerignore')){
  Copy-Item -LiteralPath (Join-Path $taskSource $taskFile) -Destination (Join-Path $taskDestination $taskFile) -Force
  $taskCount++
}
New-Item -ItemType Directory -Path (Join-Path $taskDestination '.impeccable') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $taskSource '.impeccable/config.json') -Destination (Join-Path $taskDestination '.impeccable/config.json') -Force
Write-Output ('Synced '+$taskCount+' source/document/QA files. No deletion, database, credentials, raw vendor documents or build cache copied.')
