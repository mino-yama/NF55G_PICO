# Stop only the verified build root and its current descendants.
$ErrorActionPreference = 'Stop'
$taskAllProcesses = @(Get-CimInstance Win32_Process)
$taskRootProcess = $taskAllProcesses | Where-Object {
    $_.ProcessId -eq 27676 -and $_.Name -eq 'cmake.exe' -and
    $_.CommandLine -like '*usb_submcu_external_meter*'
}
if (-not $taskRootProcess) { throw 'Expected build root no longer exists' }
$taskIds = @(27676)
do {
    $taskAdded = @($taskAllProcesses | Where-Object {
        $_.ParentProcessId -in $taskIds -and $_.ProcessId -notin $taskIds
    } | Select-Object -ExpandProperty ProcessId)
    $taskIds += $taskAdded
} while ($taskAdded.Count -gt 0)
[array]::Reverse($taskIds)
foreach ($taskBuildId in $taskIds) {
    Stop-Process -Id $taskBuildId -ErrorAction SilentlyContinue
    Write-Output ('STOPPED_BUILD_PID=' + $taskBuildId)
}
