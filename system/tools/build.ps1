param([switch]$Run)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
Push-Location $taskRoot
try {
  & node --check 'src/main/resources/web/app.js'
  if($LASTEXITCODE -ne 0){throw 'Browser JavaScript syntax check failed'}
  New-Item -ItemType Directory -Path '.deps','target\classes' -Force | Out-Null
  $taskPackages=@(
    @('org/xerial/sqlite-jdbc/3.53.4.0/sqlite-jdbc-3.53.4.0.jar','sqlite-jdbc.jar'),
    @('org/postgresql/postgresql/42.7.8/postgresql-42.7.8.jar','postgresql.jar'),
    @('com/zaxxer/HikariCP/7.1.0/HikariCP-7.1.0.jar','hikaricp.jar'),
    @('com/fasterxml/jackson/core/jackson-databind/2.20.2/jackson-databind-2.20.2.jar','jackson-databind.jar'),
    @('com/fasterxml/jackson/core/jackson-core/2.20.2/jackson-core-2.20.2.jar','jackson-core.jar'),
    @('com/fasterxml/jackson/core/jackson-annotations/2.20/jackson-annotations-2.20.jar','jackson-annotations.jar'),
    @('org/slf4j/slf4j-api/2.0.17/slf4j-api-2.0.17.jar','slf4j-api.jar'),
    @('org/slf4j/slf4j-simple/2.0.17/slf4j-simple-2.0.17.jar','slf4j-simple.jar')
  )
  foreach($taskPackage in $taskPackages){
    $taskTarget=Join-Path '.deps' $taskPackage[1]
    if(!(Test-Path -LiteralPath $taskTarget)) { Invoke-WebRequest -Uri ('https://repo.maven.apache.org/maven2/'+$taskPackage[0]) -OutFile $taskTarget }
  }
  $taskSources=Get-ChildItem -LiteralPath 'src\main\java' -Recurse -Filter '*.java' | ForEach-Object {[System.IO.Path]::GetRelativePath($taskRoot,$_.FullName)}
  & javac --release 21 -encoding UTF-8 -cp '.deps/*' -d 'target/classes' $taskSources
  if($LASTEXITCODE -ne 0){throw 'Java compilation failed'}
  Copy-Item -Path 'src/main/resources/*' -Destination 'target/classes' -Recurse -Force
  Write-Output 'Java JDBC build passed.'
  if($Run){ & java -cp 'target/classes;.deps/*' cn.adcnexus.Main }
} finally {Pop-Location}
