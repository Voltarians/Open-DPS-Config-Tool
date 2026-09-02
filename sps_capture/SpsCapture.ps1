#requires -Version 5.1
<#
.SYNOPSIS
Passively preserves files created or changed during an SPS2 session.
.DESCRIPTION
Watches selected Windows directories, copies stable changed files into a
timestamped evidence bundle, and records SHA-256 hashes. It does not modify,
proxy, inject into, or control SPS2, Techline Connect, or a vehicle.
#>
[CmdletBinding()]
param(
    [ValidateSet('Capture','Discover')][string]$Command = 'Capture',
    [string[]]$WatchPath,
    [string]$OutputRoot = (Join-Path ([Environment]::GetFolderPath('Desktop')) 'SPS-Captures'),
    [ValidateRange(1,300)][int]$PollSeconds = 2,
    [ValidateRange(0,300)][int]$PostStopSeconds = 10,
    [ValidateRange(1,30)][int]$StableChecks = 2,
    [string[]]$IncludePattern = @('*'),
    [string[]]$ExcludePattern = @('*.tmp','*.lock','~*'),
    [switch]$NoDefaultPaths
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-DefaultWatchPath {
    $found = [System.Collections.Generic.List[string]]::new()
    foreach ($parent in @($env:ProgramData,$env:LOCALAPPDATA,$env:APPDATA,$env:TEMP)) {
        if ([string]::IsNullOrWhiteSpace($parent)) { continue }
        foreach ($child in @('GM','General Motors','TechlineConnect','Techline Connect','SPS')) {
            $candidate = Join-Path $parent $child
            if (Test-Path -LiteralPath $candidate -PathType Container) {
                $found.Add((Resolve-Path -LiteralPath $candidate).Path)
            }
        }
    }
    @($found | Sort-Object -Unique)
}

function Test-PatternMatch([string]$Name) {
    $included = $false
    foreach ($pattern in $IncludePattern) {
        if ($Name -like $pattern) { $included = $true; break }
    }
    if (-not $included) { return $false }
    foreach ($pattern in $ExcludePattern) {
        if ($Name -like $pattern) { return $false }
    }
    return $true
}

function Get-FileKey([System.IO.FileInfo]$File) {
    '{0}|{1}' -f $File.Length,$File.LastWriteTimeUtc.Ticks
}

function Get-SafeRelativePath([string]$Path) {
    $full = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetPathRoot($full)
    $volume = $root.TrimEnd('\').Replace(':','')
    Join-Path $volume $full.Substring($root.Length).TrimStart('\')
}

function Get-CurrentInventory([string[]]$Roots) {
    $inventory = @{}
    foreach ($root in $Roots) {
        Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction SilentlyContinue |
            Where-Object { Test-PatternMatch $_.Name } | ForEach-Object {
                $inventory[$_.FullName] = [pscustomobject]@{
                    Path=$_.FullName; Length=$_.Length
                    LastWriteTimeUtc=$_.LastWriteTimeUtc.ToString('o')
                    Key=(Get-FileKey $_)
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
    $versionRelative=Join-Path '_versions' (Join-Path $relative ("$stamp-" + [System.IO.Path]::GetFileName($Source)))
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

$roots=@()
if (-not $NoDefaultPaths) { $roots += Get-DefaultWatchPath }
foreach ($path in @($WatchPath)) {
    if ([string]::IsNullOrWhiteSpace($path)) { continue }
    if (Test-Path -LiteralPath $path -PathType Container) { $roots += (Resolve-Path -LiteralPath $path).Path }
    else { Write-Warning "Watch path does not exist: $path" }
}
$roots=@($roots | Sort-Object -Unique)

if ($Command -eq 'Discover') {
    if ($roots.Count -eq 0) { Write-Host 'No candidate directories found. Supply -WatchPath.'; exit 2 }
    $roots; exit 0
}
if ($roots.Count -eq 0) { throw 'No watch paths available. Run Discover or supply -WatchPath.' }

$startedUtc=[DateTime]::UtcNow
$sessionName='SPS2-{0}' -f $startedUtc.ToString('yyyyMMdd-HHmmssZ')
$sessionRoot=Join-Path $OutputRoot $sessionName
$evidenceRoot=Join-Path $sessionRoot 'evidence'
$eventLog=Join-Path $sessionRoot 'events.jsonl'
$manifestPath=Join-Path $sessionRoot 'manifest.json'
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$baseline=Get-CurrentInventory $roots
@($baseline.Values | Sort-Object Path) | ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath (Join-Path $sessionRoot 'baseline.json') -Encoding UTF8
$seen=@{}; foreach ($entry in $baseline.GetEnumerator()) { $seen[$entry.Key]=$entry.Value.Key }
$capturedKeys=@{}; $captured=[System.Collections.Generic.List[object]]::new()

Write-Host "SPS Capture session: $sessionName"
Write-Host "Evidence folder: $sessionRoot"
$roots | ForEach-Object { Write-Host "Watching: $_" }
Write-Host 'Start SPS2. Press Ctrl+C after its download/programming workflow finishes.'
$stopRequested=$false
$cancelHandler=[ConsoleCancelEventHandler]{
    param($sender,$eventArgs)
    $eventArgs.Cancel=$true
    $script:stopRequested=$true
}
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

$captured | Export-Csv -LiteralPath (Join-Path $sessionRoot 'inventory.csv') -NoTypeInformation -Encoding UTF8
$manifest=[ordered]@{
    schema='opendps.sps-capture.v1'; session=$sessionName
    started_utc=$startedUtc.ToString('o'); stopped_utc=[DateTime]::UtcNow.ToString('o')
    computer=$env:COMPUTERNAME; user=$env:USERNAME; powershell=$PSVersionTable.PSVersion.ToString()
    watch_paths=$roots; poll_seconds=$PollSeconds; post_stop_seconds=$PostStopSeconds
    captured_file_versions=$captured.Count; files=@($captured)
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
$manifestHash=(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath (Join-Path $sessionRoot 'manifest.sha256') -Value "$manifestHash  manifest.json" -Encoding ASCII
Write-Host "Capture complete: $($captured.Count) file version(s) preserved."
Write-Host "Manifest: $manifestPath"
