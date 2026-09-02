#requires -Version 5.1
<#
.SYNOPSIS
Passively preserves GDS2 diagnostic-session evidence on Windows.
.DESCRIPTION
Inventories selected GDS2, Techline, VCX, and J2534 data directories; copies
stable file versions; records process and J2534 registration snapshots; and
writes SHA-256 manifests. It does not inject into diagnostic software, intercept
J2534 calls, send vehicle messages, or decrypt traffic.
#>
[CmdletBinding()]
param(
    [ValidateSet('Capture','Discover')][string]$Command='Capture',
    [string[]]$WatchPath,
    [string[]]$CanCapturePath,
    [string]$OutputRoot=(Join-Path ([Environment]::GetFolderPath('Desktop')) 'GDS2-Captures'),
    [ValidateRange(1,300)][int]$PollSeconds=2,
    [ValidateRange(0,300)][int]$PostStopSeconds=10,
    [ValidateRange(1,30)][int]$StableChecks=2,
    [string[]]$IncludePattern=@('*'),
    [string[]]$ExcludePattern=@('*.tmp','*.lock','~*'),
    [switch]$NoDefaultPaths
)

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

function Get-DefaultWatchPath {
    $found=[System.Collections.Generic.List[string]]::new()
    $parents=@($env:ProgramData,$env:LOCALAPPDATA,$env:APPDATA,$env:ProgramFiles,${env:ProgramFiles(x86)})
    $children=@('GM','General Motors','GDS2','GDS 2','TechlineConnect','Techline Connect',
        'Bosch','Drew Technologies','DrewTech','VX Manager','AllScanner','VCX','J2534')
    foreach ($parent in $parents) {
        if ([string]::IsNullOrWhiteSpace($parent)) { continue }
        foreach ($child in $children) {
            $candidate=Join-Path $parent $child
            if (Test-Path -LiteralPath $candidate -PathType Container) {
                $found.Add((Resolve-Path -LiteralPath $candidate).Path)
            }
        }
    }
    @($found | Sort-Object -Unique)
}

function Test-PatternMatch([string]$Name) {
    $included=$false
    foreach ($pattern in $IncludePattern) { if ($Name -like $pattern) { $included=$true; break } }
    if (-not $included) { return $false }
    foreach ($pattern in $ExcludePattern) { if ($Name -like $pattern) { return $false } }
    return $true
}

function Get-FileKey([System.IO.FileInfo]$File) { '{0}|{1}' -f $File.Length,$File.LastWriteTimeUtc.Ticks }

function Get-SafeRelativePath([string]$Path) {
    $full=[System.IO.Path]::GetFullPath($Path)
    $root=[System.IO.Path]::GetPathRoot($full)
    $volume=$root.TrimEnd('\').Replace(':','')
    Join-Path $volume $full.Substring($root.Length).TrimStart('\')
}

function Get-CurrentInventory([string[]]$Roots) {
    $inventory=@{}
    foreach ($root in $Roots) {
        Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction SilentlyContinue |
            Where-Object { Test-PatternMatch $_.Name } | ForEach-Object {
                $inventory[$_.FullName]=[pscustomobject]@{
                    Path=$_.FullName; Length=$_.Length
                    LastWriteTimeUtc=$_.LastWriteTimeUtc.ToString('o'); Key=(Get-FileKey $_)
                }
            }
    }
    $inventory
}

function Copy-StableEvidenceFile {
    param([string]$Source,[string]$EvidenceRoot,[hashtable]$CapturedKeys,
          [string]$EventLog,[string]$Reason)
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) { return $null }
    $stable=0; $previous=$null
    while ($stable -lt $StableChecks) {
        try { $file=Get-Item -LiteralPath $Source -Force; $key=Get-FileKey $file }
        catch { return $null }
        if ($key -eq $previous) { $stable++ } else { $stable=1; $previous=$key }
        if ($stable -lt $StableChecks) { Start-Sleep -Milliseconds 350 }
    }
    $captureKey="$Source|$previous"
    if ($CapturedKeys.ContainsKey($captureKey)) { return $null }
    $relative=Get-SafeRelativePath $Source
    $stamp=[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-fffffffZ')
    $versionRelative=Join-Path '_versions' (Join-Path $relative ("$stamp-"+[IO.Path]::GetFileName($Source)))
    $destination=Join-Path $EvidenceRoot $versionRelative
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    try {
        Copy-Item -LiteralPath $Source -Destination $destination -Force
        $copied=Get-Item -LiteralPath $destination
        $record=[ordered]@{
            captured_utc=[DateTime]::UtcNow.ToString('o'); reason=$Reason
            source_path=$Source; evidence_path=$versionRelative; size_bytes=$copied.Length
            source_last_write_utc=(Get-Item -LiteralPath $Source).LastWriteTimeUtc.ToString('o')
            sha256=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
        }
        Add-Content -LiteralPath $EventLog -Value ($record | ConvertTo-Json -Compress)
        $CapturedKeys[$captureKey]=$true
        [pscustomobject]$record
    } catch {
        $failure=[ordered]@{captured_utc=[DateTime]::UtcNow.ToString('o');reason='copy_error';source_path=$Source;error=$_.Exception.Message}
        Add-Content -LiteralPath $EventLog -Value ($failure | ConvertTo-Json -Compress)
        $null
    }
}

function Get-DiagnosticProcessSnapshot {
    $namePattern='gds|techline|tech2|mdi|vx|vcx|j2534|passthru|bosch|drew'
    try {
        Get-CimInstance Win32_Process -ErrorAction Stop |
            Where-Object { $_.Name -match $namePattern -or $_.ExecutablePath -match $namePattern } |
            Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CreationDate
    } catch {
        Get-Process -ErrorAction SilentlyContinue |
            Where-Object { $_.ProcessName -match $namePattern } |
            Select-Object Id,ProcessName,Path,StartTime
    }
}

function Get-OptionalProperty($Object,[string]$Name) {
    $property=$Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    $property.Value
}

function Get-J2534RegistrationSnapshot {
    $rows=[System.Collections.Generic.List[object]]::new()
    foreach ($root in @('HKLM:\SOFTWARE\PassThruSupport.04.04','HKLM:\SOFTWARE\WOW6432Node\PassThruSupport.04.04')) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        foreach ($key in Get-ChildItem -LiteralPath $root -ErrorAction SilentlyContinue) {
            $value=Get-ItemProperty -LiteralPath $key.PSPath -ErrorAction SilentlyContinue
            $rows.Add([pscustomobject]@{
                registry_path=$key.Name
                name=(Get-OptionalProperty $value 'Name')
                vendor=(Get-OptionalProperty $value 'Vendor')
                function_library=(Get-OptionalProperty $value 'FunctionLibrary')
                config_application=(Get-OptionalProperty $value 'ConfigApplication')
            })
        }
    }
    $rows
}

function Export-RelevantWindowsEvents([DateTime]$Start,[DateTime]$End,[string]$Path) {
    $pattern='GDS|Techline|Tech2|MDI|VCX|J2534|PassThru|Bosch|Drew'
    try {
        Get-WinEvent -FilterHashtable @{LogName='Application';StartTime=$Start;EndTime=$End} -ErrorAction Stop |
            Where-Object { $_.ProviderName -match $pattern -or $_.Message -match $pattern } |
            Select-Object TimeCreated,Id,LevelDisplayName,ProviderName,Message |
            ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $Path -Encoding UTF8
    } catch {
        @([ordered]@{error=$_.Exception.Message}) | ConvertTo-Json |
            Set-Content -LiteralPath $Path -Encoding UTF8
    }
}

$roots=@()
if (-not $NoDefaultPaths) { $roots+=Get-DefaultWatchPath }
foreach ($path in @($WatchPath)+@($CanCapturePath)) {
    if ([string]::IsNullOrWhiteSpace($path)) { continue }
    if (Test-Path -LiteralPath $path -PathType Container) { $roots+=(Resolve-Path -LiteralPath $path).Path }
    else { Write-Warning "Watch path does not exist: $path" }
}
$roots=@($roots | Sort-Object -Unique)

if ($Command -eq 'Discover') {
    if ($roots.Count -eq 0) { Write-Host 'No candidate directories found. Supply -WatchPath.'; exit 2 }
    $roots; exit 0
}
if ($roots.Count -eq 0) { throw 'No watch paths available. Run Discover or supply -WatchPath.' }

$startedUtc=[DateTime]::UtcNow
$sessionName='GDS2-{0}' -f $startedUtc.ToString('yyyyMMdd-HHmmssZ')
$sessionRoot=Join-Path $OutputRoot $sessionName
$evidenceRoot=Join-Path $sessionRoot 'evidence'
$eventLog=Join-Path $sessionRoot 'events.jsonl'
$manifestPath=Join-Path $sessionRoot 'manifest.json'
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$baseline=Get-CurrentInventory $roots
@($baseline.Values | Sort-Object Path) | ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath (Join-Path $sessionRoot 'baseline.json') -Encoding UTF8
@(Get-DiagnosticProcessSnapshot) | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $sessionRoot 'processes-start.json') -Encoding UTF8
@(Get-J2534RegistrationSnapshot) | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $sessionRoot 'j2534-registration.json') -Encoding UTF8

$seen=@{}; foreach ($entry in $baseline.GetEnumerator()) { $seen[$entry.Key]=$entry.Value.Key }
$capturedKeys=@{}; $captured=[Collections.Generic.List[object]]::new()
Write-Host "GDS2 Capture session: $sessionName"
$roots | ForEach-Object { Write-Host "Watching: $_" }
Write-Host 'Start GDS2. Press Ctrl+C after the diagnostic session and log exports finish.'
$stopRequested=$false
$cancelHandler=[ConsoleCancelEventHandler]{param($sender,$eventArgs);$eventArgs.Cancel=$true;$script:stopRequested=$true}
[Console]::add_CancelKeyPress($cancelHandler)

do {
    $current=Get-CurrentInventory $roots
    foreach ($entry in $current.GetEnumerator()) {
        $reason=$null
        if (-not $seen.ContainsKey($entry.Key)) { $reason='created' }
        elseif ($seen[$entry.Key] -ne $entry.Value.Key) { $reason='modified' }
        if ($reason) {
            $record=Copy-StableEvidenceFile -Source $entry.Key -EvidenceRoot $evidenceRoot -CapturedKeys $capturedKeys -EventLog $eventLog -Reason $reason
            if ($record) { $captured.Add($record) }
        }
        $seen[$entry.Key]=$entry.Value.Key
    }
    if (-not $stopRequested) { Start-Sleep -Seconds $PollSeconds }
} while (-not $stopRequested)
[Console]::remove_CancelKeyPress($cancelHandler)

if ($PostStopSeconds -gt 0) {
    Write-Host "Final collection window: $PostStopSeconds seconds"
    $deadline=[DateTime]::UtcNow.AddSeconds($PostStopSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        $current=Get-CurrentInventory $roots
        foreach ($entry in $current.GetEnumerator()) {
            if (-not $seen.ContainsKey($entry.Key) -or $seen[$entry.Key] -ne $entry.Value.Key) {
                $record=Copy-StableEvidenceFile -Source $entry.Key -EvidenceRoot $evidenceRoot -CapturedKeys $capturedKeys -EventLog $eventLog -Reason 'final_scan'
                if ($record) { $captured.Add($record) }
                $seen[$entry.Key]=$entry.Value.Key
            }
        }
        Start-Sleep -Seconds 1
    }
}

$stoppedUtc=[DateTime]::UtcNow
@(Get-DiagnosticProcessSnapshot) | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $sessionRoot 'processes-stop.json') -Encoding UTF8
Export-RelevantWindowsEvents -Start $startedUtc.ToLocalTime() -End $stoppedUtc.ToLocalTime() `
    -Path (Join-Path $sessionRoot 'windows-application-events.json')
$captured | Export-Csv -LiteralPath (Join-Path $sessionRoot 'inventory.csv') -NoTypeInformation -Encoding UTF8
$manifest=[ordered]@{
    schema='opendps.gds2-capture.v1'; session=$sessionName
    started_utc=$startedUtc.ToString('o'); stopped_utc=$stoppedUtc.ToString('o')
    computer=$env:COMPUTERNAME; user=$env:USERNAME; powershell=$PSVersionTable.PSVersion.ToString()
    watch_paths=$roots; can_capture_paths=@($CanCapturePath); poll_seconds=$PollSeconds
    post_stop_seconds=$PostStopSeconds; captured_file_versions=$captured.Count; files=@($captured)
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
$hash=(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath (Join-Path $sessionRoot 'manifest.sha256') -Value "$hash  manifest.json" -Encoding ASCII
Write-Host "Capture complete: $($captured.Count) file version(s) preserved."
Write-Host "Evidence folder: $sessionRoot"
