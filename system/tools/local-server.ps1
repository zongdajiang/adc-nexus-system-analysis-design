param(
  [ValidateSet('Start','Status','Stop')][string]$Action='Start',
  [switch]$NoBrowser,
  [switch]$KeepOpen
)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$taskJar=Join-Path $taskRoot 'target\adc-nexus.jar'
$taskData=Join-Path $taskRoot 'data'
$taskState=Join-Path $taskData 'local-server-state.json'
$taskUrl='http://localhost:8087'

function Get-LocalHealth {
  try {
    $taskHealth=Invoke-RestMethod -Uri 'http://127.0.0.1:8087/api/health' -TimeoutSec 3
    if($taskHealth.ok -and $taskHealth.data_access -eq 'JAVA_JDBC'){return $taskHealth}
  } catch {}
  return $null
}
function Get-OwnedProcess {
  if(!(Test-Path -LiteralPath $taskState)){return $null}
  try {
    $taskRecord=Get-Content -LiteralPath $taskState -Raw -Encoding UTF8 | ConvertFrom-Json
    $taskProcess=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$taskRecord.pid)
    $taskLive=Get-Process -Id ([int]$taskRecord.pid) -ErrorAction Stop
    if($taskProcess -and $taskRecord.jar -eq $taskJar -and $taskProcess.CommandLine.Contains('-jar target/adc-nexus.jar') -and
       $taskProcess.ExecutablePath -eq $taskRecord.java -and
       $taskLive.StartTime.ToUniversalTime().Ticks -eq ([datetime]$taskRecord.started_at).ToUniversalTime().Ticks){return $taskLive}
  } catch {}
  return $null
}
function Show-LocalStatus {
  $taskHealth=Get-LocalHealth
  if($taskHealth){
    Write-Host ('ONLINE  '+$taskUrl) -ForegroundColor Green
    Write-Host ('Version: '+$taskHealth.version+' | Database: '+$taskHealth.database)
    Write-Host ('Data: '+$taskData)
    return $true
  }
  Write-Host 'OFFLINE  No healthy ADC Nexus server on port 8087.' -ForegroundColor Yellow
  Write-Host 'Use the Start ADC Nexus desktop shortcut. Do not delete the data folder.'
  return $false
}

$taskMutex=$null
$taskLocked=$false
try {
  if($Action -eq 'Status'){ [void](Show-LocalStatus); return }
  $taskDigest=[BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($taskRoot))).Replace('-','').Substring(0,16)
  $taskMutex=New-Object Threading.Mutex($false,('Local\ADC_Nexus_'+$taskDigest))
  $taskLocked=$taskMutex.WaitOne(30000)
  if(!$taskLocked){throw 'Another launcher operation is still running. Check status shortly.'}
  if($Action -eq 'Stop'){
    $taskOwned=Get-OwnedProcess
    if(!$taskOwned){
      if(Get-LocalHealth){throw 'A server is running, but this launcher does not own it. Refusing to stop an unknown process.'}
      Write-Host 'Already stopped. Business data was not changed.'; return
    }
    Stop-Process -Id $taskOwned.Id
    $taskOwned.WaitForExit(10000) | Out-Null
    Write-Host 'Stopped the owned local server. Database and accounts are preserved.' -ForegroundColor Green
    return
  }
  if(Get-LocalHealth){
    if(!(Get-OwnedProcess)){throw 'A healthy ADC Nexus server exists but belongs to another launcher. Refusing to assume its data directory.'}
    [void](Show-LocalStatus)
    if(!$NoBrowser){Start-Process $taskUrl}
    return
  }
  $taskListener=Get-NetTCPConnection -LocalPort 8087 -State Listen -ErrorAction SilentlyContinue
  if($taskListener){throw 'Port 8087 is occupied by another process. No process was stopped; check the port owner first.'}
  if(!(Test-Path -LiteralPath $taskJar)){throw 'Application JAR is missing. Build the project with Maven first; do not delete or recreate data.'}
  $taskCandidates=@()
  if($env:JAVA_HOME){$taskCandidates+=Join-Path $env:JAVA_HOME 'bin\java.exe'}
  $taskCandidates+=Join-Path $env:USERPROFILE 'java\jdk-21.0.11+10\bin\java.exe'
  $taskCommand=Get-Command java.exe -ErrorAction SilentlyContinue
  if($taskCommand){$taskCandidates+=$taskCommand.Source}
  $taskJava=$taskCandidates | Where-Object {Test-Path -LiteralPath $_} | Select-Object -First 1
  if(!$taskJava){throw 'Java 21 or newer was not found. Install a trusted Java distribution or set JAVA_HOME.'}
  # Java reports its version on stderr. Windows PowerShell 5.1 turns redirected
  # native stderr into ErrorRecords; capture it without treating a valid version as a failure.
  $taskOldPreference=$ErrorActionPreference
  try {
    $ErrorActionPreference='Continue'
    $taskVersion=(& $taskJava -version 2>&1 | Out-String)
    $taskJavaExit=$LASTEXITCODE
  } finally {$ErrorActionPreference=$taskOldPreference}
  if($taskJavaExit -ne 0){throw 'The selected Java runtime could not report its version.'}
  if($taskVersion -notmatch 'version "([0-9]+)' -or [int]$Matches[1] -lt 21){throw 'The selected Java runtime must be version 21 or newer.'}
  $taskLogs=Join-Path $taskData 'logs'
  New-Item -ItemType Directory -Path $taskLogs -Force | Out-Null
  $taskStamp=Get-Date -Format 'yyyyMMdd-HHmmss-fff'
  $taskStdout=Join-Path $taskLogs ('local-'+$taskStamp+'.out.log')
  $taskStderr=Join-Path $taskLogs ('local-'+$taskStamp+'.err.log')
  $taskVariables=@{APP_ENV='LOCAL';PORT='8087';BIND_ADDRESS='127.0.0.1';DATA_DIR=$taskData;DEMO_MODE='true';DATABASE_URL=$null;ADC_TEST_NOW=$null;AUTH_TEST_DELIVERY_URL=$null}
  $taskPrevious=@{}
  foreach($taskKey in $taskVariables.Keys){$taskPrevious[$taskKey]=[Environment]::GetEnvironmentVariable($taskKey,'Process');[Environment]::SetEnvironmentVariable($taskKey,$taskVariables[$taskKey],'Process')}
  try {
    # Relative ASCII jar argument avoids Windows native argument-codepage damage to Chinese workspace paths.
    $taskChild=Start-Process -FilePath $taskJava -ArgumentList '-Dfile.encoding=UTF-8 -jar target/adc-nexus.jar' -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput $taskStdout -RedirectStandardError $taskStderr -PassThru
  } finally {foreach($taskKey in $taskPrevious.Keys){[Environment]::SetEnvironmentVariable($taskKey,$taskPrevious[$taskKey],'Process')}}
  $taskChild.Refresh()
  @{pid=$taskChild.Id;java=$taskJava;started_at=$taskChild.StartTime.ToUniversalTime().ToString('o');jar=$taskJar;stdout=$taskStdout;stderr=$taskStderr} | ConvertTo-Json | Set-Content -LiteralPath $taskState -Encoding UTF8
  for($taskAttempt=0;$taskAttempt -lt 40;$taskAttempt++){
    if(Get-LocalHealth){
      [void](Show-LocalStatus)
      Write-Host 'The server runs independently of this launcher window. Use the Stop shortcut to shut it down.'
      if(!$NoBrowser){Start-Process $taskUrl}
      return
    }
    $taskChild.Refresh()
    if($taskChild.HasExited){throw ('Server exited during startup. Inspect '+$taskStderr+' (never share credentials or complete medical text).')}
    Start-Sleep -Milliseconds 400
  }
  throw ('Startup timed out. The process was not killed. Check status and logs in '+$taskLogs)
} catch {
  Write-Host ('ERROR: '+$_.Exception.Message) -ForegroundColor Red
  exit 1
} finally {
  if($taskLocked){$taskMutex.ReleaseMutex()}
  if($taskMutex){$taskMutex.Dispose()}
  if($KeepOpen){[void](Read-Host 'Press Enter to finish')}
}
