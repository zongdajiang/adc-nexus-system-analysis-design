param([string]$OutputDirectory)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$taskJar=Join-Path $taskRoot 'target\adc-nexus.jar'
if(!(Test-Path -LiteralPath $taskJar)){throw 'Build target/adc-nexus.jar before packaging.'}
if(!$OutputDirectory){$OutputDirectory=Join-Path (Split-Path -Parent $taskRoot) 'deliverables\ADC_Nexus_JDBC_1.5_20261102'}
$taskOutput=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $taskOutput){throw 'Output directory already exists; use a new directory to preserve the previous release.'}
$taskJarHash=(Get-FileHash -LiteralPath $taskJar -Algorithm SHA256).Hash.ToLowerInvariant()
foreach($taskName in @('acceptance-results.json','acceptance-postgres.json','auth-acceptance-sqlite.json','auth-acceptance-postgres.json','homepage-contract-tests.json','clinic-ui-tests.json','practice-ui-tests.json','ui-refinement-tests.json','setup-ui-tests.json','local-preservation-v1-5.json','browser-review-v1-5.json','documentation-release-check.json')){
  $taskProof=Get-Content -LiteralPath (Join-Path $taskRoot ('qa\'+$taskName)) -Raw -Encoding UTF8 | ConvertFrom-Json
  $taskExpected=if($taskProof.artifact){$taskProof.artifact.sha256}else{$taskProof.jar_sha256}
  if($taskExpected -ne $taskJarHash -or !$taskProof.passed){throw ('QA evidence does not match this JAR: '+$taskName)}
}
$taskStage=Join-Path $taskOutput 'source'
New-Item -ItemType Directory -Path $taskStage | Out-Null
foreach($taskFolder in @('src','docs')){Copy-Item -LiteralPath (Join-Path $taskRoot $taskFolder) -Destination $taskStage -Recurse}
New-Item -ItemType Directory -Path (Join-Path $taskStage 'tools'),(Join-Path $taskStage 'qa') | Out-Null
Get-ChildItem -LiteralPath (Join-Path $taskRoot 'tools') -File | Where-Object Extension -In '.ps1','.py','.mjs' | Copy-Item -Destination (Join-Path $taskStage 'tools')
Get-ChildItem -LiteralPath (Join-Path $taskRoot 'qa') -File | Where-Object Extension -In '.json','.md' | Copy-Item -Destination (Join-Path $taskStage 'qa')
foreach($taskFile in @('pom.xml','package.json','PRODUCT.md','README.md','Dockerfile','render.yaml','.gitignore','.dockerignore')){Copy-Item -LiteralPath (Join-Path $taskRoot $taskFile) -Destination $taskStage}
$taskWorkbench=Join-Path $taskRoot 'upgrade-workbench'
foreach($taskFile in Get-ChildItem -LiteralPath $taskWorkbench -File -Recurse){
  $taskRelative=[IO.Path]::GetRelativePath($taskRoot,$taskFile.FullName)
  if($taskRelative -match '(^|[\\/])raw([\\/]|$)'){continue}
  $taskDestination=Join-Path $taskStage $taskRelative
  New-Item -ItemType Directory -Path (Split-Path -Parent $taskDestination) -Force | Out-Null
  Copy-Item -LiteralPath $taskFile.FullName -Destination $taskDestination
}
New-Item -ItemType Directory -Path (Join-Path $taskStage '.impeccable') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $taskRoot '.impeccable/config.json') -Destination (Join-Path $taskStage '.impeccable/config.json')
$taskArchive=Join-Path $taskOutput 'ADC_Nexus_JDBC_1.5.0-rc1_Source.zip'
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($taskStage,$taskArchive,[IO.Compression.CompressionLevel]::Optimal,$false)
$taskZip=[IO.Compression.ZipFile]::OpenRead($taskArchive)
try {
  foreach($taskEntry in $taskZip.Entries){if($taskEntry.FullName -match '(^|/)(data|target|\.deps|\.git|__pycache__|raw)(/|$)|(^|/)\.env$|setup-credentials|local-server-state|本地角色测试账号'){throw 'A private/runtime file entered the source archive.'}}
} finally {$taskZip.Dispose()}
Copy-Item -LiteralPath $taskJar -Destination (Join-Path $taskOutput 'ADC_Nexus_JDBC_1.5.0-rc1.jar')
$taskReadme=Get-Content -LiteralPath (Join-Path $taskRoot 'docs\LOCAL_DELIVERY_V1_5.md') -Raw -Encoding UTF8
foreach($taskLink in @('PRACTICE_UPGRADE_V1_5.md','REVIEW_GUIDE.md','DEPLOYMENT.md')){
  $taskReadme=$taskReadme.Replace(']('+$taskLink+')','](source/docs/'+$taskLink+')')
  if(!(Test-Path -LiteralPath (Join-Path $taskStage ('docs\'+$taskLink)))){throw ('Missing packaged document: '+$taskLink)}
}
$taskReadme=$taskReadme.Replace('](../upgrade-workbench/','](source/upgrade-workbench/')
[IO.File]::WriteAllText((Join-Path $taskOutput 'README_交付说明.md'),$taskReadme,[Text.UTF8Encoding]::new($false))
$taskDocProof=Get-Content -LiteralPath (Join-Path $taskRoot 'qa/documentation-release-check.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskManifest=@{version='1.5.0-rc1';date='2026-11-02';implementation_baseline_date='2026-10-30';packaged_at_utc=[DateTimeOffset]::UtcNow.ToString('o');automated_checks=$taskDocProof.automated_checks;local_only=$true;live_delivery_verified=$false;runtime_data_included=$false;files=@()}
foreach($taskFile in Get-ChildItem -LiteralPath $taskOutput -File){$taskManifest.files+=@{name=$taskFile.Name;bytes=$taskFile.Length;sha256=(Get-FileHash -LiteralPath $taskFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}}
$taskManifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskOutput 'release-manifest.json') -Encoding UTF8
Write-Host ('PACKAGED '+$taskOutput)
Write-Host ('JAR SHA256 '+$taskJarHash)
Write-Host 'The source archive excludes local databases, passwords, sessions, logs and build caches.'
