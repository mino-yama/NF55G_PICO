param([switch]$StopBuild)
$ErrorActionPreference = 'Stop'
$taskAllProcesses = @(Get-CimInstance Win32_Process)
$taskRoots = @($taskAllProcesses | Where-Object {
    $_.Name -eq 'python.exe' -and
    $_.CommandLine -like '*docs*Parent_Host_Integration_20261122_01*build_usb_lower_diagnostic.py*'
})
if (-not $taskRoots) { throw 'Own lower diagnostic build not found' }
$taskIds = @($taskRoots | Select-Object -ExpandProperty ProcessId)
do {
    $taskAdded = @($taskAllProcesses | Where-Object {
        $_.ParentProcessId -in $taskIds -and $_.ProcessId -notin $taskIds
    } | Select-Object -ExpandProperty ProcessId)
    $taskIds += $taskAdded
} while ($taskAdded.Count -gt 0)
$taskAllProcesses | Where-Object { $_.ProcessId -in $taskIds } |
    Select-Object ProcessId,ParentProcessId,Name,KernelModeTime,UserModeTime,CommandLine | Format-List
if ($StopBuild) {
    [array]::Reverse($taskIds)
    foreach ($taskBuildId in $taskIds) {
        Stop-Process -Id $taskBuildId -ErrorAction SilentlyContinue
        Write-Output ('STOPPED_OWN_BUILD_PID=' + $taskBuildId)
    }
}
