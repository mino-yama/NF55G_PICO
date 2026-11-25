$ErrorActionPreference = 'Stop'
if (-not $PSScriptRoot) { throw 'Run this script by its full path.' }
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$tool = Join-Path $repo 'tools/usb_submcu/picotool-2.2.0/picotool/picotool.exe'
$uf2 = Join-Path $PSScriptRoot 'candidate_20261125_090518_376/usb_submcu_external_meter_relay.uf2'
$serial = 'BFCF2EDB84B0B37F'
$expectedHash = 'AC9C7A6A43E5FCFAFF280717F387E3CF5A4299316FD795EF96DE077489936422'
if ((Get-FileHash -LiteralPath $uf2 -Algorithm SHA256).Hash -ne $expectedHash) {
    throw 'Candidate UF2 hash mismatch.'
}
$out = Join-Path $PSScriptRoot ('flash_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path $out | Out-Null

function Invoke-Picotool {
    param([string]$Step, [string[]]$ToolArgs)
    $stdout = Join-Path $out "$Step.stdout.log"
    $stderr = Join-Path $out "$Step.stderr.log"
    $argumentLine = ($ToolArgs | ForEach-Object { '"' + $_ + '"' }) -join ' '
    Write-Host "Running $Step. Logs: $out"
    $process = Start-Process -FilePath $tool -ArgumentList $argumentLine -NoNewWindow -Wait -PassThru `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if ($process.ExitCode -ne 0) { throw "picotool $Step failed (exit=$($process.ExitCode)). See $stdout and $stderr" }
    Get-Content -Raw -LiteralPath $stdout
}

function Assert-HostInfo {
    param([string]$Info, [string]$Version)
    if ($Info -notmatch '(?im)^\s*chipid:\s*0xBFCF2EDB84B0B37F\s*$' -or
        $Info -notmatch '(?im)^\s*boot type:\s*bootsel\s*$' -or
        $Info -notmatch '(?im)^\s*flash size:\s*2048K\s*$' -or
        $Info -notmatch ('(?im)^\s*version:\s*' + [regex]::Escape($Version) + '\s*$')) {
        throw "Unexpected device or firmware. Expected $serial, BOOTSEL, 2048K and $Version. See $out"
    }
}

$before = Invoke-Picotool -Step '01_before' -ToolArgs @('info', '-a', '--ser', $serial)
Assert-HostInfo -Info $before -Version 'meter-host-relay-20261123.2'
$backup = Join-Path $out 'flash_before.bin'
$null = Invoke-Picotool -Step '02_backup' -ToolArgs @('save', '-a', '-v', $backup, '--ser', $serial)
$size = (Get-Item -LiteralPath $backup).Length
if ($size -ne 2MB) { throw "Unexpected flash backup size: $size" }
[ordered]@{ chipid = $serial; bytes = $size; sha256 = (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'backup_manifest.json') -Encoding utf8

$null = Invoke-Picotool -Step '03_load' -ToolArgs @('load', '-v', $uf2, '--ser', $serial)
$null = Invoke-Picotool -Step '04_verify' -ToolArgs @('verify', $uf2, '--ser', $serial)
$after = Invoke-Picotool -Step '05_after' -ToolArgs @('info', '-a', '--ser', $serial)
Assert-HostInfo -Info $after -Version 'meter-host-relay-20261125.1'
Write-Output "Flash verified: $serial meter-host-relay-20261125.1. BOOTSEL retained. Logs: $out"
