# 既存の案件内SDKとツールだけを使い、QR単体Host評価FW（書込みなし）を再ビルドする。
param(
    [switch]$DiagnosticTx,
    [string]$Toolchain = "$env:LOCALAPPDATA/Arduino15/packages/rp2040/tools/pqt-gcc/4.1.0-1aec55e"
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$sourceDir = Join-Path $taskRoot 'firmware/usb_submcu_host_probe'
$buildName = if ($DiagnosticTx) { 'build_uart_gp0' } else { 'build' }
$txPin = if ($DiagnosticTx) { 0 } else { -1 }
$cmakeExe = Join-Path $taskRoot '.venv/Scripts/cmake.exe'
$cmakeArgs = @(
    '-S', $sourceDir, '-B', "$sourceDir/$buildName", '-G', 'Ninja',
    "-DPICO_SDK_PATH=$taskRoot/tools/usb_submcu/pico-sdk-2.2.0",
    "-DPICO_TOOLCHAIN_PATH=$Toolchain",
    "-Dpioasm_DIR=$taskRoot/tools/usb_submcu/sdk-tools-2.2.0/pioasm",
    "-Dpicotool_DIR=$taskRoot/tools/usb_submcu/picotool-2.2.0/picotool",
    "-DCMAKE_MAKE_PROGRAM=$taskRoot/.venv/Scripts/ninja.exe",
    '-DCMAKE_BUILD_TYPE=Release',
    "-DPROBE_UART_TX_PIN=$txPin"
)
& $cmakeExe @cmakeArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $cmakeExe --build "$sourceDir/$buildName" --parallel 8
exit $LASTEXITCODE
