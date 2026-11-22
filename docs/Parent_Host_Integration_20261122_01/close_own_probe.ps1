# 今回の接続診断だけを終了する。Pico上のRAM runtimeは停止しない。
$taskProbeProcesses = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'python.exe' -and
    $_.CommandLine -like '*mpremote*reset_hello_probe.py*'
}
foreach ($taskProbeProcess in $taskProbeProcesses) {
    Stop-Process -Id $taskProbeProcess.ProcessId -ErrorAction SilentlyContinue
    Write-Output ('CLOSED_PROBE_PID=' + $taskProbeProcess.ProcessId)
}
